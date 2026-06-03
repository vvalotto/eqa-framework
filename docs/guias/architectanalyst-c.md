# ArchitectAnalyst-C — Guía de usuario

## Instalación

```bash
pip install eqa-framework
```

ArchitectAnalyst-C no requiere herramientas de sistema adicionales — el análisis es puramente Python.

Verificar que está disponible:

```bash
architectanalyst-c --help
```

---

## Uso básico

Analizar todos los archivos `.c` y `.h` de un directorio al cierre del sprint:

```bash
architectanalyst-c src/ --sprint-id sprint-03
```

Sin `--sprint-id`, el snapshot se guarda con sprint_id vacío. Se recomienda siempre pasarlo para tener tendencias significativas.

Output JSON para integración con otras herramientas:

```bash
architectanalyst-c src/ --sprint-id sprint-03 --format json
```

Apuntar a una configuración en una ubicación no estándar:

```bash
architectanalyst-c src/ --sprint-id sprint-03 --config /path/to/pyproject.toml
```

---

## Interpretar el output

### Modo texto

```
 Module        Ca    Ce      I       A       D
 app_logic      2     0   0.00  =  0.00  =  1.00  =
 hal_uart       1     1   0.50  ↓  0.00  =  0.50  ↓
 main           0     2   1.00  ↑  0.00  =  0.00  =
 sensor         0     0   0.00  =  0.00  =  1.00  =

  CRITICAL  [ARC003]  app_logic: distance 1.00 in Zone of Pain/Uselessness (> 0.5)
  CRITICAL  [ARC003]  sensor: distance 1.00 in Zone of Pain/Uselessness (> 0.5)
  WARNING   [ARC001]  main: instability 1.00 exceeds limit 0.8

2 CRITICAL · 1 WARNING  (0.3s)
```

**Columnas de la tabla:**

| Columna | Descripción |
|---------|-------------|
| Module | Nombre del módulo (stem del archivo) |
| Ca | Afferent Coupling — módulos que dependen de este |
| Ce | Efferent Coupling — módulos de los que depende este |
| I | Instabilidad = Ce / (Ca + Ce). 0 = estable, 1 = inestable |
| A | Abstractness — proporción de tipos opacos/abstractos en el header |
| D | Distance a la Main Sequence = \|A + I - 1\|. 0 = ideal |

**Símbolos de tendencia** (columnas angostas junto a I, A, D):

| Símbolo | Significado |
|---------|-------------|
| `↓` (verde) | Mejoró respecto al sprint anterior |
| `↑` (rojo) | Empeoró |
| `=` (gris) | Sin cambio significativo |
| *(vacío)* | Primera ejecución |

Para I y D, bajar es mejorar. Para A, subir es mejorar.

### Modo JSON

```bash
architectanalyst-c src/ --sprint-id sprint-03 --format json | jq .
```

La salida tiene dos claves:

```json
{
  "metrics": [
    {
      "module": "app_logic",
      "ca": 2,
      "ce": 0,
      "instability": 0.0,
      "abstractness": 0.0,
      "distance": 1.0
    }
  ],
  "findings": [
    {
      "file": "/path/to/app_logic.h",
      "severity": "CRITICAL",
      "rule": "ARC003",
      "message": "app_logic: distance 1.00 in Zone of Pain/Uselessness (> 0.5)"
    }
  ]
}
```

---

## Interpretar los findings

### ARC003 — Zone of Pain o Uselessness (CRITICAL)

El módulo tiene D > 0.5. En proyectos C embebidos, la causa más frecuente es la **Zone of Pain**: el módulo es muy usado (Ca alto) pero no tiene abstracción (A ≈ 0). Ejemplos típicos: estructuras de datos globales, módulos de configuración estática, headers con #defines usados por toda la aplicación.

**Acciones posibles:**
- Introducir un header de interfaz con typedefs opacos para ocultar la implementación
- Separar las constantes en un header de bajo nivel que no genere Ca hacia el módulo
- Evaluar si el módulo realmente necesita abstracción o si su estabilidad es aceptable dado el diseño

### ARC002 — Distancia en zona de advertencia (WARNING)

D está entre `max_distance_warning` y `max_distance_critical`. Es una señal temprana, no urgente.

### ARC001 — Instabilidad excesiva (WARNING)

I > `max_instability` (default 0.8). El módulo depende de muchos otros y pocos dependen de él. En la capa de integración o en el `main.c` esto es esperado; en módulos del medio de la arquitectura puede indicar un diseño frágil.

---

## Configuración

Agregar la sección `[tool.architectanalyst-c]` al `pyproject.toml` del proyecto C analizado:

```toml
[tool.architectanalyst-c]
max_instability       = 0.8    # WARNING si I > umbral (default: 0.8)
max_distance_warning  = 0.3    # WARNING si D > umbral (default: 0.3)
max_distance_critical = 0.5    # CRITICAL si D > umbral (default: 0.5)
db_path               = ".quality_control/architecture.db"  # ruta del SQLite
exclude_patterns      = ["build/", "third_party/"]
```

El agente busca `pyproject.toml` comenzando desde el path dado y caminando hacia los directorios padre. Si el archivo no existe, usa los valores por defecto.

### Ajustar umbrales

Para proyectos con arquitectura estricta (certificación IEC 62304):

```toml
[tool.architectanalyst-c]
max_instability       = 0.7
max_distance_warning  = 0.2
max_distance_critical = 0.4
```

Para proyectos en fase inicial donde la arquitectura todavía está tomando forma:

```toml
[tool.architectanalyst-c]
max_instability       = 0.9
max_distance_warning  = 0.4
max_distance_critical = 0.7
```

### Ubicación de la base de datos

Por defecto el archivo SQLite se crea en `.quality_control/embedded_architecture.db` relativo a la raíz del proyecto. Se recomienda agregar este archivo a `.gitignore` o al repositorio según la política del equipo:

```bash
# .gitignore — ignorar la DB (recomendado si se recalcula en CI)
.quality_control/

# Alternativa: versionar la DB para tener histórico en el repo
# (no agregar a .gitignore)
```

---

## Workflow típico de fin de sprint

```bash
# 1. Al cierre del sprint, analizar el proyecto
architectanalyst-c src/ --sprint-id sprint-05

# 2. Ver evolución en JSON para procesar con otras herramientas
architectanalyst-c src/ --sprint-id sprint-05 --format json > sprint-05-arch.json

# 3. Ver módulos en Zone of Pain (D > 0.5)
architectanalyst-c src/ --sprint-id sprint-05 --format json | \
  jq '.findings[] | select(.rule == "ARC003")'

# 4. Ver evolución de instabilidad de un módulo específico
architectanalyst-c src/ --sprint-id sprint-05 --format json | \
  jq '.metrics[] | select(.module == "hal_uart")'
```

---

## Integración en CI

ArchitectAnalyst-C siempre retorna exit code 0, por lo que no puede usarse como gate bloqueante. El uso típico en CI es guardar el snapshot y publicar el reporte como artefacto:

```yaml
- name: ArchitectAnalyst-C
  run: |
    pip install eqa-framework
    architectanalyst-c src/ --sprint-id ${{ github.run_number }} --format json \
      > architectanalyst_report.json

- name: Upload architecture report
  uses: actions/upload-artifact@v4
  with:
    name: architecture-report
    path: architectanalyst_report.json
```

Para detectar regresiones en CI, procesar el JSON manualmente:

```yaml
- name: Check for new Zone of Pain modules
  run: |
    CRITICALS=$(jq '.findings | map(select(.rule == "ARC003")) | length' architectanalyst_report.json)
    echo "Módulos en Zone of Pain: $CRITICALS"
    if [ "$CRITICALS" -gt 5 ]; then
      echo "⚠️ Demasiados módulos en Zone of Pain"
      exit 1
    fi
```

---

## Preguntas frecuentes

**¿Por qué todos mis módulos tienen A = 0.0?**
En C embebido es normal. La abstracción mediante typedefs opacos y forward declarations no es una práctica universal. Un valor A = 0 no es un error — significa que el módulo es concreto. El finding ARC003 se dispara cuando esa concreción se combina con alta estabilidad (Ca alto, Ce bajo), lo que resulta en D alto.

**¿Por qué `main` tiene siempre I = 1.0?**
`main.c` típicamente incluye headers de toda la aplicación (Ca = 0, Ce alto), resultando en I = 1.0. Esto es esperado y correcto para el punto de entrada. Si genera ARC001, ajustar `max_instability = 1.0` o agregar `main.c` a `exclude_patterns`.

**¿El historial se acumula indefinidamente?**
Sí. La base de datos SQLite crece con cada sprint. Para proyectos de larga duración se puede rotar la DB o limpiarla manualmente. Actualmente no hay comando de limpieza incorporado.

**¿Cómo forzar una comparación con un sprint específico?**
No es posible directamente. `load_last` siempre usa el sprint más reciente distinto del actual. Para comparar contra un sprint específico, usar `--format json` en los dos sprints y comparar los JSONs manualmente o con un script.

**¿Qué pasa si dos módulos tienen el mismo nombre en directorios distintos?**
Se tratan como un único módulo — el archivo representativo será el último procesado. Esto puede producir métricas incorrectas. Se recomienda que todos los archivos `.h` y `.c` tengan nombres únicos en el proyecto.
