# sample_c_project

Proyecto C embebido de ejemplo para demos y tests e2e de eqa-framework.
Contiene violaciones intencionales de cada tipo para verificar que los agentes
las detecten correctamente.

## Estructura

```
sample_c_project/
├── pyproject.toml       ← configuración de los tres agentes
└── src/
    ├── sensor.c         ← gets(), strcpy(), nullPointer, uninitvar
    ├── main.c           ← gets(), función con CC > 10
    ├── hal/
    │   ├── hal_uart.h   ← header con include guard correcto
    │   └── hal_uart.c   ← viola capas: incluye app/app_logic.h desde HAL
    └── app/
        ├── app_logic.h  ← sin include guard (MISRA 4.10)
        └── app_logic.c  ← función con CC > 10 y > 50 líneas (7 parámetros)
```

## Violaciones por agente

### codeguard-c

| Archivo | Violación | Herramienta | Severidad esperada |
|---|---|---|---|
| sensor.c | `gets()` | flawfinder | ERROR |
| sensor.c | `strcpy()` | flawfinder | ERROR |
| sensor.c | `nullPointer` | cppcheck | ERROR |
| sensor.c | `uninitvar` | cppcheck | ERROR |
| main.c | `gets()` | flawfinder | ERROR |
| main.c | `classify_reading` CC > 10 | lizard | WARNING |
| app/app_logic.c | `app_process_sensors` CC > 10 | lizard | WARNING |
| hal/hal_uart.c | `sprintf` sin bounds | flawfinder | ERROR |
| *.c | violaciones MISRA (NULL literal, etc.) | cppcheck+misra | CRITICAL/WARNING |

### designreviewer-c

| Archivo | Violación |
|---|---|
| hal/hal_uart.c | incluye `app/app_logic.h` — HAL no debe depender de APP |
| app/app_logic.h | sin include guard |
| app/app_logic.c | función con 7 parámetros (límite: 6) |

## Uso

```bash
# Instalar eqa-framework
pip install eqa-framework

# Analizar con codeguard-c
codeguard-c examples/sample_c_project/src/

# Output JSON (para CI)
codeguard-c examples/sample_c_project/src/ --format json
```
