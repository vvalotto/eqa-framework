# Perfil de Calidad — Documentación del sistema de reportes

## Qué hace

El sistema de reportes genera un perfil Markdown con el estado del proyecto según el agente que lo produce. Es una capa de presentación transversal a los tres agentes — `codeguard-c`, `designreviewer-c` y `architectanalyst-c` — que sintetiza los findings en dimensiones de calidad con tres estados posibles: OK, ADVERTENCIA y CRÍTICO.

El reporte se activa con el flag `--report` en cualquiera de los tres agentes. No modifica el comportamiento ni el output normal del agente: es un output adicional, independiente de `--format`, que puede ir a stdout o a un archivo.

---

## Arquitectura

```
agent.py
    │  ejecuta análisis normal (texto o JSON → stdout)
    │
    └──▶ _build_quality_report(report, ...)
              │  agrupa findings por dimensión
              ▼
         QualityReport
              │
              ▼
         render_markdown(qr) → str
              │
              ▼
         write_report(markdown, output)
              │
              ├──▶ output=None  → sys.stdout.write()
              └──▶ output=path  → path.write_text() + confirmación en stderr
```

El módulo `shared/report.py` contiene las clases y funciones compartidas. Cada agente implementa su propia función `_build_quality_report` interna que mapea sus findings a dimensiones semánticas.

---

## El modelo de datos

### DimensionStatus

```python
@dataclass
class DimensionStatus:
    name: str
    status: StatusLiteral          # "ok" | "warning" | "critical"
    findings: list[str]            # hasta 5 findings representativos; vacío si ok
```

Representa una dimensión de calidad con su estado y los principales hallazgos. Si `status == "ok"`, `findings` es una lista vacía.

### QualityReport

```python
@dataclass
class QualityReport:
    agent_name: str
    target_path: str
    file_count: int
    date: str                      # fecha ISO del análisis
    dimensions: list[DimensionStatus]
    summary: str
```

### StatusLiteral

`"ok"` → ✅ OK · `"warning"` → ⚠️ ADVERTENCIA · `"critical"` → ❌ CRÍTICO

El criterio para determinar el status de una dimensión es uniforme en los tres agentes: si hay algún finding de severidad CRITICAL (o ERROR en el caso de flawfinder), el status es `"critical"`; si solo hay WARNING, es `"warning"`; si no hay findings, es `"ok"`.

---

## Dimensiones por agente

Cada agente define sus propias dimensiones mapeando findings a grupos semánticos.

### CodeGuard-C

| Dimensión | Filtro | Criterio de status |
|-----------|--------|--------------------|
| Complejidad | `f.tool == "lizard"` | `critical` si hay CRITICAL; `warning` si hay WARNING |
| Seguridad | `f.tool == "flawfinder"` | `critical` si hay ERROR/CRITICAL; `warning` si hay WARNING |
| MISRA | `f.tool == "cppcheck"` | `critical` si hay CRITICAL (Mandatory); `warning` si hay WARNING (Required) |

Los findings representativos de cada dimensión tienen el formato `{file}:{line} — {message[:60]}`.

### DesignReviewer-C

| Dimensión | Filtro | Criterio de status |
|-----------|--------|--------------------|
| Dependencias | `f.rule in ["INC001", "INC002"]` | `critical` si hay CRITICAL |
| Capas | `f.rule == "LAY001"` | `critical` si hay CRITICAL |

Los findings representativos tienen el mismo formato `{file}:{line} — {message[:60]}`.

### ArchitectAnalyst-C

| Dimensión | Filtro | Criterio de status |
|-----------|--------|--------------------|
| Inestabilidad | `f.rule == "ARC001"` | `warning` si I excede el umbral |
| Distancia | `f.rule in ["ARC002", "ARC003"]` | `critical` si hay ARC003; `warning` si solo ARC002 |

Los findings representativos muestran el mensaje truncado a 80 caracteres.

El resumen de ArchitectAnalyst-C incluye una nota de tendencia histórica cuando hay snapshot previo: lista los módulos cuya distancia D empeoró más de 0.05 respecto al sprint anterior, y la cantidad de módulos nuevos que aparecieron en el sprint actual.

---

## Estructura del Markdown generado

`render_markdown(report)` produce un string con la siguiente estructura fija:

```markdown
# <agent_name> — Perfil de Calidad

**Proyecto:** `<target_path>` · N archivos · YYYY-MM-DD

## Perfil

| Dimensión | Estado |
|-----------|--------|
| Complejidad | ✅ OK |
| Seguridad | ⚠️ ADVERTENCIA |
| MISRA | ❌ CRÍTICO |

## Principales hallazgos

**❌ CRÍTICO — MISRA**
- src/hal/uart.c:28 — misra violation
- src/app/app_logic.c:10 — misra violation

**⚠️ ADVERTENCIA — Seguridad**
- src/sensor.c:6 — gets: Does not check for buffer over…

## Resumen

Se detectaron violaciones críticas. Revisar antes de continuar.
```

La sección "Principales hallazgos" solo aparece si al menos una dimensión tiene findings. Se muestran hasta 5 findings por dimensión, ordenados según el criterio de cada agente (por severidad o por el orden en que se producen).

---

## Comportamiento del flag `--report`

El flag tiene semántica dual: sin argumento actúa como flag booleano (imprime a stdout); con argumento actúa como opción con valor (escribe a archivo).

Esto se implementa con `is_flag=False, flag_value="-"` en Click:
- Sin argumento → Click asigna `"-"` → `write_report` recibe `output=None` → escribe a stdout.
- Con ruta de archivo → Click usa esa cadena → `write_report` escribe el archivo y confirma en stderr.
- Sin pasar el flag → Click asigna `None` → no se genera reporte.

El mensaje de confirmación ("Reporte guardado en ...") va a stderr para no contaminar stdout cuando el output de análisis también va a stdout.

---

## Funciones públicas de shared/report.py

```python
def render_markdown(report: QualityReport) -> str: ...
```
Convierte un `QualityReport` en un string Markdown. No tiene efectos secundarios.

```python
def write_report(markdown: str, output: str | None) -> None: ...
```
Escribe el Markdown. Si `output` es `None`, escribe a stdout. Si es una ruta, escribe el archivo en UTF-8 y emite la confirmación en stderr.

---

## Limitaciones conocidas

**Hasta 5 findings por dimensión:** en proyectos con muchos hallazgos, los menos prioritarios no aparecen en el perfil. El output completo está disponible en el modo texto o JSON del agente.

**Labels en español no configurables:** los textos OK, ADVERTENCIA, CRÍTICO y los resúmenes están en español sin opción de cambiar el idioma.

**Fecha sin hora ni zona horaria:** dos análisis en el mismo día producen la misma fecha en el reporte.
