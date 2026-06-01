# eqa-framework

**Framework de Control de Calidad Automatizado para C Embebido**

[![CI](https://github.com/vvalotto/eqa-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/vvalotto/eqa-framework/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Framework Python de código abierto que orquesta herramientas de análisis estático (cppcheck, flawfinder, lizard) sobre proyectos C embebidos, verificando cumplimiento de MISRA-C 2012 e IEC 62304.

## Agentes

| Agente | Cuándo | Tiempo | Comportamiento |
|--------|--------|--------|----------------|
| `codeguard-c` | Pre-commit | < 15s | Solo advierte, nunca bloquea |
| `designreviewer-c` | PR review | 2–10 min | Bloquea si hay CRITICAL |
| `architectanalyst-c` | Fin de sprint | 5–30 min | Solo informa, histórico SQLite |

## Instalación

```bash
pip install eqa-framework
```

### Dependencias de sistema

```bash
# cppcheck (obligatorio)
sudo apt install cppcheck        # Linux
brew install cppcheck            # macOS

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

En `pyproject.toml` o `.embedded-qa.toml`:

```toml
[tool.codeguard-c]
max_cyclomatic_complexity = 10
max_function_lines        = 50

[tool.architectanalyst-c.layers]
platform    = []
hal         = ["platform"]
application = ["hal"]
```

## Desarrollo

```bash
git clone https://github.com/vvalotto/eqa-framework.git
cd eqa-framework
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Licencia

MIT — Ver [LICENSE](LICENSE)
