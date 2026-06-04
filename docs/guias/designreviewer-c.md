# DesignReviewer-C — Guía de usuario

## Instalación

```bash
pip install eqa-framework
```

DesignReviewer-C no requiere herramientas de sistema adicionales — el análisis es puramente Python.

Verificar que está disponible:

```bash
designreviewer-c --help
```

---

## Uso básico

Analizar todos los archivos `.c` y `.h` de un directorio:

```bash
designreviewer-c src/
```

Analizar un archivo específico:

```bash
designreviewer-c src/hal/hal_uart.c
```

Output JSON para integración con CI u otras herramientas:

```bash
designreviewer-c src/ --format json
```

Apuntar a una configuración en una ubicación no estándar:

```bash
designreviewer-c src/ --config /path/to/pyproject.toml
```

Generar un perfil de calidad en Markdown:

```bash
# Imprimir el perfil en stdout
designreviewer-c src/ --report

# Guardar el perfil en un archivo
designreviewer-c src/ --report calidad.md
```

---

## Interpretar el output

### Modo texto

```
 File                        Line  Sev       Rule    Message
 /src/hal/hal_uart.c            0  CRITICAL  LAY001  hal_uart.c: layer 'hal' must not include from layer 'app' (hal_uart.c → app_logic.h)
 /src/drivers/i2c.h             0  CRITICAL  INC001  circular dependency: i2c.h → spi.h → i2c.h

2 CRITICAL  (0.1s)
```

Cada columna:

- **File**: ruta al archivo con el problema
- **Line**: línea del finding (0 indica que aplica al archivo completo, no a una línea específica)
- **Sev**: severidad — CRITICAL
- **Rule**: identificador de la regla
  - `INC001` — dependencia circular entre headers
  - `INC002` — fan-out de módulo por encima del umbral
  - `LAY001` — violación de jerarquía de capas
- **Message**: descripción del problema con el detalle del ciclo o la violación

La última línea muestra el resumen de conteos y el tiempo de análisis. El agente retorna exit code 1 si hay al menos un finding CRITICAL.

### Modo JSON

```bash
designreviewer-c src/ --format json | jq .
```

Cada elemento del array tiene:

```json
{
  "file": "/src/hal/hal_uart.c",
  "line": 0,
  "severity": "CRITICAL",
  "rule": "LAY001",
  "message": "hal_uart.c: layer 'hal' must not include from layer 'app' (hal_uart.c → app_logic.h)",
  "tool": "layer_violations"
}
```

El campo `tool` indica qué analyzer generó el finding: `include_graph` o `layer_violations`.

---

## Configuración

DesignReviewer-C lee su configuración de `[tool.designreviewer-c]` en el `pyproject.toml` del proyecto. Busca el archivo comenzando desde el path dado y caminando hacia los directorios padre, por lo que puede invocar el agente con un subdirectorio (`src/`) y la configuración se leerá igualmente desde la raíz del proyecto.

### Opciones disponibles

```toml
[tool.designreviewer-c]
max_fan_out        = 12    # Cantidad máxima de includes locales distintos por módulo (default: 12)
exclude_patterns   = [     # Patrones de archivos/dirs a ignorar
    "build/",
    "third_party/",
    "test/mocks/",
]

[tool.designreviewer-c.layers]
# Jerarquía de capas: cada capa lista las capas de las que puede depender.
# Un include que viola esta jerarquía genera LAY001 CRITICAL.
platform = []
hal      = ["platform"]
app      = ["hal", "platform"]
```

### Definir la jerarquía de capas

La sección `[tool.designreviewer-c.layers]` define las capas del proyecto y sus dependencias permitidas. Cada clave es un nombre de capa que debe coincidir con un directorio en la estructura del proyecto. El valor es la lista de capas de las que esa capa puede depender.

```toml
[tool.designreviewer-c.layers]
# Arquitectura típica IEC 62304 para dispositivos médicos
platform = []                    # Drivers de bajo nivel, sin dependencias
bsp      = ["platform"]          # Board Support Package
hal      = ["bsp", "platform"]   # Hardware Abstraction Layer
services = ["hal", "platform"]   # Servicios del sistema
app      = ["services", "hal", "platform"]  # Lógica de aplicación
```

Un archivo en `src/hal/uart.c` pertenece a la capa `hal`. Si ese archivo incluye un header de `src/app/`, el agente genera un finding CRITICAL porque `app` no está en las dependencias permitidas de `hal`.

Los archivos que no pertenecen a ninguna capa definida (ej. `main.c` en la raíz) son ignorados por el análisis de capas.

### Ajustar el umbral de fan-out

```toml
# Proyecto pequeño con arquitectura estricta
[tool.designreviewer-c]
max_fan_out = 5

# Proyecto con módulos de integración que conectan muchos subsistemas
[tool.designreviewer-c]
max_fan_out = 15
```

---

## Integración en CI

### GitHub Actions — gate de bloqueo en PR

```yaml
- name: DesignReviewer-C
  run: |
    pip install eqa-framework
    designreviewer-c src/
  # El agente retorna exit code 1 si hay CRITICAL → el step falla automáticamente
```

### GitHub Actions — con reporte de artefacto

```yaml
- name: DesignReviewer-C
  run: designreviewer-c src/ --format json > designreviewer_report.json || true

- name: Upload DesignReviewer report
  uses: actions/upload-artifact@v4
  with:
    name: designreviewer-report
    path: designreviewer_report.json

- name: Fail if CRITICAL findings
  run: |
    CRITICALS=$(jq '[.[] | select(.severity == "CRITICAL")] | length' designreviewer_report.json)
    if [ "$CRITICALS" -gt 0 ]; then
      echo "❌ $CRITICALS CRITICAL findings"
      designreviewer-c src/
      exit 1
    fi
```

### Uso como check de PR review

DesignReviewer-C está pensado para correr durante la revisión de pull requests, no como hook pre-commit. El análisis tarda típicamente 1–10 segundos según el tamaño del proyecto — aceptable en CI pero lento para un hook local que corre en cada commit.

---

## Casos de uso habituales

### Verificar que un PR no introduce violaciones de capa

```bash
designreviewer-c src/
echo "Exit code: $?"
```

### Ver solo las violaciones de capa

```bash
designreviewer-c src/ --format json | \
  jq '[.[] | select(.rule == "LAY001")]'
```

### Ver solo las dependencias circulares

```bash
designreviewer-c src/ --format json | \
  jq '[.[] | select(.rule == "INC001")]'
```

### Contar módulos con fan-out excesivo

```bash
designreviewer-c src/ --format json | \
  jq '[.[] | select(.rule == "INC002")] | length'
```

### Analizar un módulo específico antes de hacer PR

```bash
designreviewer-c src/hal/
```

---

## Preguntas frecuentes

**¿Por qué el agente retorna exit code 1?**
DesignReviewer-C actúa como gate de bloqueo para PR review. A diferencia de CodeGuard-C (que es orientativo), los findings de DesignReviewer-C representan violaciones de arquitectura que deben corregirse antes de integrar el código. El exit code 1 permite usar el agente directamente en un paso de CI sin lógica adicional.

**¿Qué pasa si no tengo `[tool.designreviewer-c.layers]` en mi pyproject.toml?**
El análisis de violaciones de capa (LAY001) se omite completamente cuando no hay capas configuradas. El análisis de ciclos (INC001) y fan-out (INC002) funciona igualmente.

**¿Por qué el agente no detecta la violación aunque veo el `#include` problemático?**
Las causas más comunes son: (1) el archivo incluido no es un include local con comillas — el agente ignora `#include <file.h>`; (2) el directorio del archivo no coincide con ningún nombre de capa definido en la configuración; (3) el archivo está en `exclude_patterns`.

**¿El agente puede analizar proyectos con múltiples pyproject.toml (monorepo)?**
El agente usa el primer `pyproject.toml` que encuentra caminando hacia arriba desde el path dado. En un monorepo, pasar el path de un subproyecto encontrará su propio `pyproject.toml` antes de llegar al raíz. Si se necesita usar una configuración específica, usar `--config /path/to/pyproject.toml`.

**¿Cómo excluir un módulo de integración que legítimamente tiene muchos includes?**
Agregar el directorio del módulo a `exclude_patterns`:
```toml
[tool.designreviewer-c]
exclude_patterns = ["build/", "src/integration/"]
```
