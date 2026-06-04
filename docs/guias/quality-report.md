# Perfil de Calidad — Guía de uso del flag --report

## Qué es el perfil de calidad

El flag `--report` genera un documento Markdown con un resumen visual del estado del proyecto para el agente que se está ejecutando. A diferencia del output normal (tabla Rich o JSON), el perfil de calidad está pensado para ser archivado, compartido o incluido en revisiones de sprint.

El perfil no reemplaza al output normal del agente — se produce adicionalmente, después del análisis.

---

## Uso básico

### Generar el perfil en stdout

```bash
codeguard-c src/ --report
designreviewer-c src/ --report
architectanalyst-c src/ --sprint-id sprint-05 --report
```

El análisis normal se muestra en la terminal; el Markdown se imprime a continuación en stdout.

### Guardar el perfil en un archivo

```bash
codeguard-c src/ --report calidad-codeguard.md
designreviewer-c src/ --report calidad-design.md
architectanalyst-c src/ --sprint-id sprint-05 --report calidad-arch.md
```

El análisis normal se muestra en la terminal. El archivo se crea (o sobreescribe) silenciosamente; aparece un mensaje de confirmación en stderr:

```
Reporte guardado en calidad-codeguard.md
```

### Combinar con --format json

```bash
codeguard-c src/ --format json > findings.json --report calidad.md
```

El JSON va a stdout (redirigido a `findings.json`); el Markdown al archivo. Los dos outputs son completamente independientes.

---

## Interpretar el perfil

### Tabla de dimensiones

```markdown
## Perfil

| Dimensión | Estado |
|-----------|--------|
| Complejidad | ✅ OK |
| Seguridad | ⚠️ ADVERTENCIA |
| MISRA | ❌ CRÍTICO |
```

Cada agente tiene sus propias dimensiones:

| Agente | Dimensiones |
|--------|-------------|
| `codeguard-c` | Complejidad, Seguridad, MISRA |
| `designreviewer-c` | Dependencias, Capas |
| `architectanalyst-c` | Inestabilidad, Distancia |

Los estados posibles:

| Estado | Icono | Significado |
|--------|-------|-------------|
| OK | ✅ | No hay findings en esta dimensión |
| ADVERTENCIA | ⚠️ | Hay findings de severidad WARNING |
| CRÍTICO | ❌ | Hay findings de severidad CRITICAL o ERROR |

### Sección de hallazgos

Aparece solo si al menos una dimensión tiene hallazgos. Muestra hasta 5 findings representativos por dimensión.

```markdown
## Principales hallazgos

**❌ CRÍTICO — MISRA**
- src/hal/hal_uart.c:28 — misra violation
- src/app/app_logic.c:10 — misra violation

**⚠️ ADVERTENCIA — Seguridad**
- src/sensor.c:6 — gets: Does not check for buffer over…
```

Para `architectanalyst-c`, los findings muestran el nombre del módulo y la métrica que superó el umbral, en lugar de una ruta de archivo.

### Resumen

Una línea de texto que describe el estado general:

- "Sin observaciones. El código cumple con todos los umbrales configurados." — sin hallazgos
- "Hay advertencias que merecen atención." — solo WARNING
- "Se detectaron violaciones críticas. Revisar antes de continuar." — hay CRITICAL

Para `architectanalyst-c`, el resumen puede incluir una nota adicional de tendencia histórica: qué módulos empeoraron su distancia D respecto al sprint anterior y cuántos módulos nuevos aparecieron en el sprint actual.

---

## Casos de uso habituales

### Archivar el estado de calidad al cierre de sprint

```bash
architectanalyst-c src/ --sprint-id sprint-05 \
  --report reports/sprint-05-quality.md
```

### Generar los tres perfiles en un paso de CI

```bash
mkdir -p reports
codeguard-c src/ --report reports/codeguard.md
designreviewer-c src/ --report reports/design.md
architectanalyst-c src/ --sprint-id "$SPRINT_ID" --report reports/arch.md
```

### Subir los perfiles como artefacto en GitHub Actions

```yaml
- name: Generar perfiles de calidad
  run: |
    mkdir -p reports
    codeguard-c src/ --report reports/codeguard.md
    designreviewer-c src/ --report reports/design.md
    architectanalyst-c src/ \
      --sprint-id ${{ github.run_number }} \
      --report reports/arch.md

- name: Upload quality profiles
  uses: actions/upload-artifact@v4
  with:
    name: quality-profiles
    path: reports/
```

### Ver el perfil sin guardar archivo (revisión rápida)

```bash
codeguard-c src/ --report | grep -A 30 "## Perfil"
```

### Redirigir el análisis y capturar solo el perfil

```bash
# El análisis va a /dev/null; el perfil al archivo
codeguard-c src/ --report calidad.md > /dev/null
```

El mensaje "Reporte guardado en..." va a stderr y seguirá siendo visible.

---

## Preguntas frecuentes

**¿El flag --report afecta el exit code del agente?**
No. El exit code sigue siendo el mismo independientemente de si se usa `--report` o no: `codeguard-c` siempre retorna 0; `designreviewer-c` retorna 1 si hay CRITICAL; `architectanalyst-c` siempre retorna 0.

**¿El archivo de reporte se sobreescribe si ya existe?**
Sí. `write_report` sobreescribe sin verificar si el archivo existe. Para conservar versiones anteriores, incluir la fecha o el sprint_id en el nombre del archivo:

```bash
codeguard-c src/ --report "reports/codeguard-$(date +%Y-%m-%d).md"
architectanalyst-c src/ --sprint-id sprint-05 --report reports/arch-sprint-05.md
```

**¿El perfil de calidad muestra todos los findings?**
No. Se muestran hasta 5 findings por dimensión. Para el listado completo usar `--format json` o el output texto normal del agente.

**¿Puedo usar --report con un archivo específico en lugar de un directorio?**
Sí. `--report` funciona igual sin importar si el argumento `path` del agente es un directorio o un archivo:

```bash
codeguard-c src/hal/hal_uart.c --report calidad-uart.md
```

**¿El perfil incluye la información de tendencias de ArchitectAnalyst-C?**
Sí, pero solo en el texto del resumen. Las columnas de tendencia (↑ ↓ =) del output Rich no se reproducen en el Markdown — el perfil muestra el estado absoluto de cada dimensión, no la evolución individual de cada módulo.
