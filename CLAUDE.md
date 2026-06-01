# CLAUDE.md — eqa-framework

Guía para desarrolladores y para Claude Code. El README cubre instalación y uso; este archivo cubre el internals.

---

## Arquitectura

Tres agentes CLI independientes que comparten el paquete `shared/`:

```
src/eqa_framework/
├── shared/           ← clases base, config, reporting (reutilizadas por los tres agentes)
├── codeguard_c/      ← CLI: codeguard-c    | orquesta cppcheck + flawfinder + lizard
├── designreviewer_c/ ← CLI: designreviewer-c | analiza dependencias e includes
└── architectanalyst_c/ ← CLI: architectanalyst-c | métricas de acoplamiento, histórico SQLite
```

Cada agente tiene la misma estructura interna:

```
<agente>/
├── agent.py        ← entry point Click (función main())
├── orchestrator.py ← coordina los checks/analyzers
├── config.py       ← lee sección [tool.<agente>] de pyproject.toml
└── checks/ o analyzers/ o metrics/
    └── *.py        ← implementación de cada verificación
```

Las herramientas externas (cppcheck, flawfinder, lizard) se invocan como subprocesos desde los checks.

---

## Entorno de desarrollo

**Prerequisitos del sistema:**

```bash
brew install cppcheck          # macOS — obligatorio para codeguard-c
# pip install flawfinder lizard  ← ya incluidos en pip install -e ".[dev]"
```

**Setup del proyecto:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

**Verificar que todo funciona:**

```bash
cppcheck --version             # Cppcheck 2.x
codeguard-c --help
pytest
pre-commit run --all-files
```

---

## Comandos habituales

```bash
pytest                                          # correr tests
pytest tests/unit/codeguard_c/ -v              # tests de un agente
pytest --cov=src/eqa_framework --cov-report=term-missing  # con cobertura

black src/ tests/                               # formatear
ruff check src/ tests/                          # lint
mypy src/                                       # tipos
pre-commit run --all-files                      # todos los checks juntos
```

---

## Convenciones

**Código:**
- Line length: 100 caracteres (black + ruff configurados)
- Python 3.11+ — usar `X | Y` en vez de `Optional[X]`, `list[X]` en vez de `List[X]`
- mypy en modo `strict` — todas las funciones con tipos explícitos
- Sin comentarios que expliquen qué hace el código; solo comentarios que expliquen el por qué

**Commits (español, Conventional Commits):**
- `feat:` nueva funcionalidad
- `fix:` corrección de bug
- `test:` agregar o corregir tests
- `refactor:` refactor sin cambio de comportamiento
- `docs:` solo documentación
- `chore:` tooling, CI, dependencias
- `ci:` cambios en GitHub Actions

**Branches:**
- `main` — producción, protegida (PRs requeridos, CI debe pasar)
- `feat/<nombre>` — features nuevas
- `fix/<nombre>` — bugfixes

---

## Tests

Estructura espejada a `src/`:

```
tests/
├── conftest.py
├── unit/
│   ├── codeguard_c/
│   ├── designreviewer_c/
│   └── architectanalyst_c/
├── integration/     ← tests que invocan las herramientas C reales
└── e2e/             ← tests sobre el proyecto de ejemplo en examples/sample_c_project/
```

Los tests de integración y e2e requieren cppcheck instalado en el sistema.

---

## CI/CD

- **CI** (`.github/workflows/ci.yml`): lint (black, ruff, mypy) + pytest en Python 3.11 y 3.12
- **Release** (`.github/workflows/release.yml`): tag `v*.*.*` publica a PyPI via `PYPI_API_TOKEN`
- **Branch protection** en `main`: PRs requeridos, los tres jobs de CI deben pasar

---

## Archivos de referencia

- `examples/configs/pyproject.toml.example` — todas las opciones de configuración de los tres agentes
- `examples/sample_c_project/` — proyecto C de ejemplo para demos y tests e2e
- `docs/specs/` — plan del proyecto y plan de entorno original
