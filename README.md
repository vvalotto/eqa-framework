# eqa-framework

**Framework de Control de Calidad Automatizado para C Embebido**

[![CI](https://github.com/vvalotto/eqa-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/vvalotto/eqa-framework/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/eqa-framework.svg)](https://pypi.org/project/eqa-framework/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Framework Python de código abierto que orquesta herramientas de análisis estático (cppcheck, flawfinder, lizard) sobre proyectos C embebidos, verificando cumplimiento de MISRA-C 2012 e IEC 62304.

## Agentes

| Agente | Cuándo usarlo | Tiempo estimado | Comportamiento ante fallos | Estado |
|--------|---------------|-----------------|---------------------------|--------|
| `codeguard-c` | Pre-commit | < 15 s | Solo advierte, nunca bloquea | ✅ v0.1.0 |
| `designreviewer-c` | PR review | 2–10 min | Bloquea si hay hallazgos CRITICAL | 🚧 v0.2.0 |
| `architectanalyst-c` | Fin de sprint | 5–30 min | Solo informa, guarda histórico en SQLite | 🔜 v0.3.0 |

## Instalación

```bash
pip install eqa-framework
```

### Dependencias de sistema requeridas

```bash
# cppcheck (obligatorio)
brew install cppcheck        # macOS
sudo apt install cppcheck    # Linux

# flawfinder y lizard
pip install flawfinder lizard
```

## Uso rápido

```bash
codeguard-c src/
designreviewer-c src/ --format json
architectanalyst-c src/ --sprint-id sprint-01
```

## Configuración

Los agentes se configuran en `pyproject.toml` del proyecto C que se analiza:

```toml
[tool.codeguard-c]
max_cyclomatic_complexity = 10
max_function_lines        = 50

[tool.designreviewer-c]
max_fan_out    = 12
max_parameters = 6

[tool.architectanalyst-c.layers]
platform    = []
hal         = ["platform"]
application = ["hal"]
```

Ver [`examples/configs/pyproject.toml.example`](examples/configs/pyproject.toml.example) para la referencia completa de todas las opciones.

## Documentación técnica

- [`docs/agentes/codeguard-c.md`](docs/agentes/codeguard-c.md) — referencia técnica de checks y configuración
- [`docs/guias/uso-codeguard-c.md`](docs/guias/uso-codeguard-c.md) — guía de usuario paso a paso
- [`examples/configs/pyproject.toml.example`](examples/configs/pyproject.toml.example) — todas las opciones de configuración

## Contribuir

Ver [CLAUDE.md](CLAUDE.md) para instrucciones de entorno, convenciones y arquitectura interna.

## Licencia

MIT — Ver [LICENSE](LICENSE)
