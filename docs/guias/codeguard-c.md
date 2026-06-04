# CodeGuard-C — Guía de usuario

## Instalación

```bash
pip install eqa-framework
```

Requiere las siguientes herramientas del sistema:

```bash
# macOS
brew install cppcheck

# Ubuntu / Debian
apt-get install cppcheck

# flawfinder y lizard se instalan junto con el paquete Python
```

Verificar que todo está disponible:

```bash
cppcheck --version     # Cppcheck 2.x
flawfinder --version   # Flawfinder 2.x
lizard --version       # 1.x
codeguard-c --help
```

---

## Uso básico

Analizar todos los archivos `.c` y `.h` de un directorio:

```bash
codeguard-c src/
```

Analizar un archivo específico:

```bash
codeguard-c src/hal/hal_uart.c
```

Output JSON para integración con CI u otras herramientas:

```bash
codeguard-c src/ --format json
```

Apuntar a una configuración en una ubicación no estándar:

```bash
codeguard-c src/ --config /path/to/pyproject.toml
```

Generar un perfil de calidad en Markdown:

```bash
# Imprimir el perfil en stdout
codeguard-c src/ --report

# Guardar el perfil en un archivo
codeguard-c src/ --report calidad.md
```

---

## Interpretar el output

### Modo texto

```
 File                    Line  Sev       Rule               Message
 src/hal/hal_uart.c        28  CRITICAL  misra-c2012-11.9   misra violation
 src/sensor.c               6  ERROR     FF1014             gets: Does not check for buffer overflows
 src/app/app_logic.c        8  WARNING   CCN001             app_process_sensors: cyclomatic complexity 15 exceeds limit 10
 src/app/app_logic.c        8  WARNING   LOC001             app_process_sensors: function length 52 lines exceeds limit 50

4 CRITICAL · 1 ERROR · 2 WARNING  (3.2s)
```

Cada columna:

- **File**: ruta al archivo con el problema
- **Line**: línea donde se detectó
- **Sev**: severidad — CRITICAL / ERROR / WARNING / INFO
- **Rule**: identificador de la regla o check
  - `misra-c2012-X.Y` — violación MISRA C:2012 regla X.Y
  - `FF####` — finding de flawfinder (ej. `FF1014` = `gets`)
  - `CCN001` — complejidad ciclomática superada
  - `LOC001` — longitud de función superada
  - identificadores de cppcheck (`nullPointer`, `uninitvar`, etc.)
- **Message**: descripción del problema

La última línea muestra el resumen de conteos y el tiempo total de análisis. Si el análisis supera los 15 segundos, aparece una advertencia adicional (el análisis continúa igual).

### Modo JSON

```bash
codeguard-c src/ --format json | jq .
```

Cada elemento del array tiene:

```json
{
  "file": "src/sensor.c",
  "line": 6,
  "severity": "ERROR",
  "rule": "FF1014",
  "message": "gets: Does not check for buffer overflows (CWE-120, CWE-20).",
  "tool": "flawfinder"
}
```

El campo `tool` indica qué herramienta generó el finding: `cppcheck`, `flawfinder` o `lizard`.

---

## Configuración

CodeGuard-C lee su configuración de `[tool.codeguard-c]` en el `pyproject.toml` del proyecto. Si no existe `pyproject.toml`, busca `.embedded-qa.toml` en la misma ubicación. Si no hay ninguno, usa los valores por defecto.

### Opciones disponibles

```toml
[tool.codeguard-c]
max_cyclomatic_complexity = 10    # CCN máximo por función (default: 10)
max_function_lines        = 50    # Líneas máximas por función (default: 50)
exclude_patterns          = [     # Patrones de archivos/dirs a ignorar
    "build/",
    "third_party/",
    "*.pb.c",
]

[tool.codeguard-c.checks]
misra_mandatory = true    # Violaciones MISRA Mandatory → CRITICAL (default: true)
misra_required  = true    # Violaciones MISRA Required  → WARNING  (default: true)
misra_advisory  = false   # Violaciones MISRA Advisory  → INFO     (default: false)
security        = true    # Funciones inseguras via flawfinder      (default: true)
complexity      = true    # CC y LOC via lizard                     (default: true)
```

### Patrones de exclusión

Los patrones en `exclude_patterns` se evalúan contra cada archivo individualmente:

- Patrones terminados en `/` excluyen directorios: `"build/"` excluye cualquier archivo cuya ruta contenga el segmento `build`.
- Patrones con wildcard usan glob sobre el nombre del archivo: `"*.pb.c"` excluye `proto_generated.pb.c`.

```toml
exclude_patterns = [
    "build/",           # directorio de build
    "third_party/",     # dependencias externas
    "*.pb.c",           # archivos generados por protobuf
    "test/mocks/",      # mocks de test
]
```

### Ajustar umbrales según certificación

Para proyectos con certificación funcional los umbrales suelen ser más estrictos:

```toml
# IEC 62304 Clase B / ISO 26262 ASIL-B
[tool.codeguard-c]
max_cyclomatic_complexity = 6
max_function_lines        = 40

# IEC 62304 Clase C / ISO 26262 ASIL-C/D
[tool.codeguard-c]
max_cyclomatic_complexity = 4
max_function_lines        = 30
```

---

## Integración en CI

### GitHub Actions

```yaml
- name: CodeGuard-C
  run: |
    pip install eqa-framework
    codeguard-c src/ --format json > codeguard_report.json
    cat codeguard_report.json

- name: Upload CodeGuard report
  uses: actions/upload-artifact@v4
  with:
    name: codeguard-report
    path: codeguard_report.json
```

Para bloquear el pipeline si hay findings CRITICAL o ERROR:

```yaml
- name: CodeGuard-C (fail on critical)
  run: |
    codeguard-c src/ --format json > report.json
    CRITICALS=$(jq '[.[] | select(.severity == "CRITICAL" or .severity == "ERROR")] | length' report.json)
    if [ "$CRITICALS" -gt 0 ]; then
      echo "❌ $CRITICALS CRITICAL/ERROR findings"
      codeguard-c src/
      exit 1
    fi
```

### Pre-commit hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: codeguard-c
        name: CodeGuard-C
        entry: codeguard-c
        args: [src/]
        language: python
        pass_filenames: false
        always_run: true
```

---

## Casos de uso habituales

### Verificar un módulo antes de un PR

```bash
codeguard-c src/drivers/
```

### Filtrar solo errores críticos para un informe ejecutivo

```bash
codeguard-c src/ --format json | \
  jq '[.[] | select(.severity == "CRITICAL" or .severity == "ERROR")]'
```

### Contar findings por severidad

```bash
codeguard-c src/ --format json | \
  jq 'group_by(.severity) | map({severity: .[0].severity, count: length})'
```

### Ver solo findings de una herramienta

```bash
codeguard-c src/ --format json | jq '[.[] | select(.tool == "flawfinder")]'
```

### Analizar un archivo nuevo antes de commitear

```bash
codeguard-c src/drivers/new_driver.c
```

---

## Preguntas frecuentes

**¿Por qué el agente siempre retorna exit code 0?**
CodeGuard-C es una herramienta de visibilidad, no un gate de bloqueo. La decisión de bloquear el pipeline corresponde al proceso de CI del proyecto, no a la herramienta de análisis. Esto permite adoptar el agente de forma incremental sin bloquear el flujo de trabajo existente.

**¿Por qué los mensajes MISRA dicen "use --rule-texts to get proper output"?**
El texto completo de las reglas MISRA C:2012 es un documento de pago. cppcheck puede usar ese archivo con `--rule-texts=<file>` para mostrar el texto real de cada regla. Sin él, muestra ese mensaje genérico. El `Rule` que aparece en el output (`misra-c2012-8.4`) es suficiente para consultar la regla en la documentación de MISRA o en las referencias públicas.

**¿El agente necesita compilar el código?**
No. Todas las herramientas (cppcheck, flawfinder, lizard) analizan el texto fuente. No requieren toolchain, headers del SDK, ni script de build. Esto permite integrarlo en CI sin replicar el entorno de build completo.

**¿Cómo suprimo un finding específico que es un falso positivo?**
Para cppcheck se puede usar un comentario en línea:
```c
//cppcheck-suppress nullPointer
ptr = get_hardware_address();
```
Para flawfinder no hay mecanismo de supresión por línea — la alternativa es agregar el archivo a `exclude_patterns` si el directorio completo es conocidamente seguro (ej. `third_party/`).

**¿Qué pasa si el análisis tarda más de 15 segundos?**
El agente imprime una advertencia pero completa el análisis. El presupuesto de 15 segundos es orientativo para uso como hook pre-commit. En CI el tiempo no es un problema.
