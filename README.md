# eqa-framework

**Framework de Control de Calidad Automatizado para C Embebido**

[![CI](https://github.com/vvalotto/eqa-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/vvalotto/eqa-framework/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Framework Python de código abierto que orquesta herramientas de análisis estático (cppcheck, flawfinder, lizard) sobre proyectos C embebidos, verificando cumplimiento de MISRA-C 2012 e IEC 62304.

## Agentes

| Agente | Cuándo usarlo | Tiempo estimado | Comportamiento ante fallos | Estado |
|--------|---------------|-----------------|---------------------------|--------|
| `codeguard-c` | Pre-commit | < 15 s | Solo advierte, nunca bloquea | ✅ v0.1.0 |
| `designreviewer-c` | PR review | < 10 s | Bloquea si hay hallazgos CRITICAL | ✅ v0.2.0 |
| `architectanalyst-c` | Fin de sprint | 5–30 min | Solo informa, guarda histórico en SQLite | ✅ v0.3.0 |

## Editor de configuración personal

`eqa-config` es una TUI que permite a cada desarrollador sobreescribir umbrales de los agentes a nivel personal, sin tocar el `pyproject.toml` del proyecto.

```bash
eqa-config
```

Los valores se guardan en `~/.config/eqa/config.toml` y tienen precedencia sobre la configuración del proyecto.

## Instalación

```bash
pip install eqa-framework
```

### Dependencias de sistema requeridas

```bash
# cppcheck (obligatorio para codeguard-c)
brew install cppcheck        # macOS
sudo apt install cppcheck    # Linux

# flawfinder y lizard (incluidos en pip install eqa-framework)
```

## Uso rápido

```bash
codeguard-c src/
designreviewer-c src/ --format json
architectanalyst-c src/ --sprint-id sprint-01
eqa-config
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

[tool.architectanalyst-c]
max_instability       = 0.8
max_distance_critical = 0.5
db_path               = ".quality_control/architecture.db"
```

Ver [`examples/configs/pyproject.toml.example`](examples/configs/pyproject.toml.example) para la referencia completa de todas las opciones.

## Documentación técnica

**Agentes de análisis:**
- [`docs/agentes/codeguard-c.md`](docs/agentes/codeguard-c.md) — referencia técnica de CodeGuard-C
- [`docs/guias/codeguard-c.md`](docs/guias/codeguard-c.md) — guía de usuario de CodeGuard-C
- [`docs/agentes/designreviewer-c.md`](docs/agentes/designreviewer-c.md) — referencia técnica de DesignReviewer-C
- [`docs/guias/designreviewer-c.md`](docs/guias/designreviewer-c.md) — guía de usuario de DesignReviewer-C
- [`docs/agentes/architectanalyst-c.md`](docs/agentes/architectanalyst-c.md) — referencia técnica de ArchitectAnalyst-C
- [`docs/guias/architectanalyst-c.md`](docs/guias/architectanalyst-c.md) — guía de usuario de ArchitectAnalyst-C

**Editor de configuración:**
- [`docs/agentes/eqa-config.md`](docs/agentes/eqa-config.md) — referencia técnica de eqa-config
- [`docs/guias/eqa-config.md`](docs/guias/eqa-config.md) — guía de usuario de eqa-config

**Referencia:**
- [`examples/configs/pyproject.toml.example`](examples/configs/pyproject.toml.example) — todas las opciones de configuración

## Contribuir

Ver [CLAUDE.md](CLAUDE.md) para instrucciones de entorno, convenciones y arquitectura interna.

## Licencia

MIT — Ver [LICENSE](LICENSE)
