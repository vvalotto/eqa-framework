# Plan de Creación de Entorno — eqa-framework

**Proyecto:** `eqa-framework`  
**Descripción:** Framework de Control de Calidad Automatizado para C Embebido  
**Visibilidad:** Público  
**Fecha:** Mayo 2026

---

## Índice

1. [Prerequisitos](#1-prerequisitos)
2. [Crear repositorio en GitHub](#2-crear-repositorio-en-github)
3. [Estructura del proyecto](#3-estructura-del-proyecto)
4. [Configuración de pyproject.toml](#4-configuración-de-pyprojecttoml)
5. [Entorno virtual y dependencias](#5-entorno-virtual-y-dependencias)
6. [Pre-commit hooks](#6-pre-commit-hooks)
7. [GitHub Actions — Pipeline CI](#7-github-actions--pipeline-ci)
8. [Branch protection](#8-branch-protection)
9. [Issue templates](#9-issue-templates)
10. [Primer commit y push](#10-primer-commit-y-push)

---

## 1. Prerequisitos

Verificar que las siguientes herramientas están instaladas en el entorno de desarrollo antes de comenzar:

```bash
# Python 3.11 o superior
python3 --version          # esperado: Python 3.11.x o mayor

# Git
git --version              # esperado: git 2.x

# GitHub CLI (para crear el repo desde terminal)
gh --version               # esperado: gh version 2.x

# Herramientas de análisis C (obligatorias para los agentes)
cppcheck --version         # esperado: Cppcheck 2.6 o mayor
flawfinder --version       # esperado: Flawfinder 2.x
lizard --version            # pip install lizard

# Opcional pero recomendado
complexity --version       # GNU complexity (apt install complexity / brew install complexity)
```

### Instalación de herramientas de análisis

```bash
# cppcheck (Linux)
sudo apt install cppcheck

# cppcheck (macOS)
brew install cppcheck

# flawfinder y lizard via pip
pip install flawfinder lizard

# GitHub CLI (Linux)
sudo apt install gh

# GitHub CLI (macOS)
brew install gh

# Autenticarse en GitHub CLI
gh auth login
```

---

## 2. Crear repositorio en GitHub

### 2.1 Crear el repo público con GitHub CLI

```bash
gh repo create eqa-framework \
  --public \
  --description "Framework de Control de Calidad Automatizado para C Embebido (MISRA-C / IEC 62304)" \
  --license MIT \
  --gitignore Python \
  --clone
```

Esto crea el repositorio en GitHub, agrega `.gitignore` para Python y `LICENSE` MIT, y clona localmente.

```bash
# Ingresar al directorio
cd eqa-framework
```

### 2.2 Configurar identidad de Git (si no está global)

```bash
git config user.name  "Victor Valotto"
git config user.email "vvalotto@gmail.com"
```

### 2.3 Configurar rama principal

```bash
# Asegurarse de estar en main
git branch -M main
```

---

## 3. Estructura del proyecto

Crear la estructura de carpetas completa:

```bash
mkdir -p src/eqa_framework/{shared,codeguard_c/{checks},designreviewer_c/{analyzers},architectanalyst_c/{metrics}}
mkdir -p tests/{unit/{codeguard_c,designreviewer_c,architectanalyst_c},integration,e2e}
mkdir -p docs/{guias,teoria,agentes}
mkdir -p examples/{configs,sample_c_project/src}
mkdir -p .github/{workflows,ISSUE_TEMPLATE}
```

La estructura resultante:

```
eqa-framework/
├── src/
│   └── eqa_framework/
│       ├── __init__.py
│       ├── shared/
│       │   ├── __init__.py
│       │   ├── verifiable.py       ← clase base (adaptada de software_limpio)
│       │   ├── config.py           ← QualityConfig compartida
│       │   └── reporting.py        ← generación de reportes
│       ├── codeguard_c/
│       │   ├── __init__.py
│       │   ├── agent.py            ← CLI entry point: codeguard-c
│       │   ├── orchestrator.py
│       │   ├── config.py
│       │   └── checks/
│       │       ├── __init__.py
│       │       ├── misra_check.py
│       │       ├── security_check.py
│       │       └── complexity_check.py
│       ├── designreviewer_c/
│       │   ├── __init__.py
│       │   ├── agent.py            ← CLI entry point: designreviewer-c
│       │   ├── orchestrator.py
│       │   ├── config.py
│       │   └── analyzers/
│       │       ├── __init__.py
│       │       ├── include_graph_analyzer.py
│       │       └── layer_violations_analyzer.py
│       └── architectanalyst_c/
│           ├── __init__.py
│           ├── agent.py            ← CLI entry point: architectanalyst-c
│           ├── orchestrator.py
│           ├── config.py
│           ├── snapshot_store.py
│           └── metrics/
│               ├── __init__.py
│               └── coupling_analyzer.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/
├── examples/
│   ├── configs/
│   │   └── pyproject.toml.example  ← referencia de configuración completa
│   └── sample_c_project/           ← proyecto C de ejemplo para demos
│       └── src/
├── .github/
│   ├── workflows/
│   └── ISSUE_TEMPLATE/
├── .gitignore
├── .pre-commit-config.yaml
├── pyproject.toml
├── README.md
└── LICENSE
```

### Crear los `__init__.py` vacíos

```bash
find src tests -type d | while read d; do touch "$d/__init__.py"; done
```

---

## 4. Configuración de pyproject.toml

Crear `pyproject.toml` en la raíz del proyecto:

```toml
[build-system]
requires      = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name        = "eqa-framework"
version     = "0.1.0"
description = "Framework de Control de Calidad Automatizado para C Embebido"
readme      = "README.md"
license     = "MIT"
requires-python = ">=3.11"
authors     = [{name = "Victor Valotto", email = "vvalotto@gmail.com"}]
keywords    = ["embedded", "quality", "misra", "iec62304", "cppcheck", "static-analysis", "c"]
classifiers = [
    "Development Status :: 2 - Pre-Alpha",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Quality Assurance",
    "Topic :: Software Development :: Embedded Systems",
]

dependencies = [
    "click>=8.1.7",
    "rich>=13.7.0",
    "pyyaml>=6.0.1",
    "tomli>=2.0.0; python_version < '3.11'",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
    "isort>=5.12.0",
    "pre-commit>=3.5.0",
]

[project.scripts]
codeguard-c        = "eqa_framework.codeguard_c.agent:main"
designreviewer-c   = "eqa_framework.designreviewer_c.agent:main"
architectanalyst-c = "eqa_framework.architectanalyst_c.agent:main"

[tool.setuptools.packages.find]
where = ["src"]

# ── Configuración de herramientas ─────────────────────────────────────────────

[tool.black]
line-length    = 100
target-version = ["py311"]

[tool.isort]
profile    = "black"
line_length = 100

[tool.ruff]
line-length = 100
select      = ["E", "F", "W", "I", "N", "B", "C4"]
ignore      = ["E501"]

[tool.mypy]
python_version        = "3.11"
strict                = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths    = ["tests"]
addopts      = "-v --tb=short"

[tool.coverage.run]
source = ["src/eqa_framework"]

# ── Configuración de los agentes (defaults explícitos) ────────────────────────

[tool.codeguard-c]
max_cyclomatic_complexity = 10
max_function_lines        = 50
min_dead_code_confidence  = 60
exclude_patterns          = ["build/", "third_party/", "*.pb.c"]

[tool.codeguard-c.checks]
misra_mandatory = true
misra_required  = true
misra_advisory  = false
security        = true
complexity      = true
uninitialized   = true
null_pointer    = true
buffer_overflow = true

[tool.codeguard-c.ai]
enabled    = false
max_tokens = 500

[tool.designreviewer-c]
max_fan_out        = 12
max_function_lines = 80
max_parameters     = 6
max_nesting_depth  = 4
max_cc_critical    = 15
exclude_patterns   = ["build/", "third_party/", "test/mocks/"]

[tool.designreviewer-c.checks]
circular_includes   = true
layer_violations    = true
global_variables    = true
include_guards      = true
non_portable_types  = true
dangerous_casts     = true

[tool.designreviewer-c.ai]
enabled    = false
max_tokens = 800

[tool.architectanalyst-c]
max_instability       = 0.8
max_distance_warning  = 0.3
max_distance_critical = 0.5
db_path               = ".quality_control/embedded_architecture.db"
exclude_patterns      = ["build/", "third_party/", "__pycache__"]

[tool.architectanalyst-c.checks]
coupling          = true
instability       = true
distance          = true
dependency_cycles = true
layer_violations  = true
misra_coverage    = true

[tool.architectanalyst-c.layers]
# Definir la arquitectura en capas del proyecto C analizado
# platform      = []
# hal           = ["platform"]
# bsp           = ["hal", "platform"]
# drivers       = ["hal", "bsp"]
# application   = ["drivers", "hal"]

[tool.architectanalyst-c.ai]
enabled    = false
max_tokens = 1500
```

---

## 5. Entorno virtual y dependencias

```bash
# Crear entorno virtual
python3 -m venv .venv

# Activar (Linux/macOS)
source .venv/bin/activate

# Instalar el proyecto en modo desarrollo con dependencias de dev
pip install -e ".[dev]"

# Verificar que los CLI están disponibles
codeguard-c --help
designreviewer-c --help
architectanalyst-c --help
```

Agregar `.venv/` al `.gitignore` (ya incluido en el template de Python de GitHub).

---

## 6. Pre-commit hooks

### 6.1 Crear `.pre-commit-config.yaml`

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files
        args: ["--maxkb=500"]

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-PyYAML]
        args: [--ignore-missing-imports]
```

### 6.2 Instalar los hooks

```bash
pre-commit install
pre-commit run --all-files   # verificar que todo pasa en verde
```

---

## 7. GitHub Actions — Pipeline CI

### 7.1 Workflow principal: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  quality:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: black
        run: black --check src/ tests/

      - name: ruff
        run: ruff check src/ tests/

      - name: mypy
        run: mypy src/

  test:
    name: Tests
    runs-on: ubuntu-latest
    needs: quality
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install system tools
        run: |
          sudo apt-get update
          sudo apt-get install -y cppcheck
          pip install flawfinder lizard

      - name: Install project
        run: pip install -e ".[dev]"

      - name: Run tests
        run: pytest --cov=src/eqa_framework --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### 7.2 Workflow de release: `.github/workflows/release.yml`

```yaml
name: Release

on:
  push:
    tags:
      - "v*.*.*"

jobs:
  publish:
    name: Publish to PyPI
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Build package
        run: |
          pip install build
          python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

---

## 8. Branch protection

Configurar desde **GitHub → Settings → Branches → Add rule** para la rama `main`:

| Regla                                              | Valor        |
|----------------------------------------------------|--------------|
| Require a pull request before merging              | ✅ activado  |
| Required approvals                                 | 1            |
| Require status checks to pass (CI: quality + test) | ✅ activado  |
| Require branches to be up to date before merging  | ✅ activado  |
| Do not allow bypassing the above settings          | ✅ activado  |

### Con GitHub CLI

```bash
gh api repos/vvalotto/eqa-framework/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["quality","test"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null
```

---

## 9. Issue templates

### 9.1 Bug report: `.github/ISSUE_TEMPLATE/bug_report.md`

```markdown
---
name: Bug report
about: Reportar un error en eqa-framework
title: '[BUG] '
labels: bug
assignees: vvalotto
---

## Descripción del bug
<!-- Descripción clara y concisa del problema -->

## Pasos para reproducir
1. Correr `...`
2. Ver error

## Comportamiento esperado
<!-- Qué debería ocurrir -->

## Comportamiento actual
<!-- Qué ocurre en realidad -->

## Entorno
- OS: [e.g. Ubuntu 22.04]
- Python: [e.g. 3.11.4]
- eqa-framework version: [e.g. 0.1.0]
- cppcheck version: [e.g. 2.9]

## Logs / output
```
pegar output aquí
```
```

### 9.2 Feature request: `.github/ISSUE_TEMPLATE/feature_request.md`

```markdown
---
name: Feature request
about: Proponer una nueva funcionalidad o mejora
title: '[FEAT] '
labels: enhancement
assignees: vvalotto
---

## Problema o necesidad
<!-- Qué problema resuelve esta feature? -->

## Solución propuesta
<!-- Descripción clara de lo que querés que pase -->

## Alternativas consideradas
<!-- Otras soluciones que consideraste -->

## Contexto adicional
<!-- Estándar relacionado (MISRA-C, IEC 62304), agente afectado, etc. -->
```

### 9.3 Nuevo check/métrica: `.github/ISSUE_TEMPLATE/new_check.md`

```markdown
---
name: Nueva métrica o check
about: Proponer una nueva verificación para alguno de los agentes
title: '[CHECK] '
labels: enhancement, new-check
assignees: vvalotto
---

## Agente objetivo
- [ ] CodeGuard-C
- [ ] DesignReviewer-C
- [ ] ArchitectAnalyst-C

## Métrica / check propuesto
<!-- Nombre y descripción de la verificación -->

## Herramienta que lo detecta
<!-- cppcheck, flawfinder, lizard, análisis propio, etc. -->

## Severidad sugerida
- [ ] CRITICAL
- [ ] ERROR
- [ ] WARNING
- [ ] INFO

## Estándar relacionado
<!-- MISRA-C regla, IEC 62304 cláusula, etc. -->

## Umbral propuesto
<!-- Valor numérico o condición que dispara la alerta -->
```

---

## 10. Primer commit y push

```bash
# Verificar estado
git status

# Agregar todos los archivos
git add .

# Primer commit
git commit -m "chore: initial project setup

- Estructura de proyecto con tres agentes (codeguard-c, designreviewer-c, architectanalyst-c)
- pyproject.toml con configuración completa de agentes, MISRA-C e IEC 62304
- Pre-commit hooks: black, isort, ruff, mypy
- GitHub Actions CI: lint + tests en Python 3.11 y 3.12
- Issue templates: bug report, feature request, nuevo check
- Branch protection configurada en main"

# Push a main
git push -u origin main
```

### Verificar que el pipeline pasa

```bash
# Seguir el estado del workflow desde terminal
gh run watch
```

---

## Resumen de comandos (secuencia completa)

```bash
# 1. Crear repo
gh repo create eqa-framework --public --description "Framework de Control de Calidad Automatizado para C Embebido" --license MIT --gitignore Python --clone
cd eqa-framework

# 2. Estructura
mkdir -p src/eqa_framework/{shared,codeguard_c/checks,designreviewer_c/analyzers,architectanalyst_c/metrics}
mkdir -p tests/{unit/{codeguard_c,designreviewer_c,architectanalyst_c},integration,e2e}
mkdir -p docs .github/{workflows,ISSUE_TEMPLATE} examples/configs
find src tests -type d | while read d; do touch "$d/__init__.py"; done

# 3. Crear pyproject.toml, .pre-commit-config.yaml, workflows y templates
# (copiar contenido de las secciones anteriores)

# 4. Entorno virtual
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 5. Pre-commit
pre-commit install
pre-commit run --all-files

# 6. Primer commit
git add . && git commit -m "chore: initial project setup"
git push -u origin main

# 7. Branch protection
gh api repos/vvalotto/eqa-framework/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["quality","test"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null
```

---

*eqa-framework — Plan de Entorno v1.0 | Facultad de Ingeniería UNER | Mayo 2026*
