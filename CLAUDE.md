# CLAUDE.md — eqa-framework

Guía para desarrolladores y para Claude Code. El README cubre instalación y uso; este archivo cubre el internals.

---

## Estado actual

| Componente | Milestone | Estado |
|------------|-----------|--------|
| `codeguard-c` | v0.1.0 | ✅ Implementado |
| `designreviewer-c` | v0.2.0 | ✅ Implementado (issues #7–#9 cerrados) |
| `architectanalyst-c` | v0.3.0 | ✅ Implementado (issues #10–#12 cerrados) |
| `eqa-config` (TUI) | v0.4.0 | ✅ Implementado (issues #31–#35 cerrados) |
| Reportes Markdown (`--report`) | v0.5.0 | ✅ Implementado (issues #36–#40 cerrados) |
| `eqa-init` (bootstrap config) | v0.6.0 | ✅ Implementado (issues #51–#55 cerrados) |

324 tests en total (unit + integration + e2e). `shared/` completamente funcional.

---

## Arquitectura

Tres agentes CLI + dos herramientas de soporte, todos comparten el paquete `shared/`:

```
src/eqa_framework/
├── shared/           ← clases base, config con merge personal, reporting
├── codeguard_c/      ← CLI: codeguard-c    | orquesta cppcheck + flawfinder + lizard
├── designreviewer_c/ ← CLI: designreviewer-c | analiza dependencias e includes
├── architectanalyst_c/ ← CLI: architectanalyst-c | métricas de acoplamiento, histórico SQLite
├── config_editor/    ← CLI: eqa-config     | TUI Textual para config personal
└── init/             ← CLI: eqa-init       | bootstrap pyproject.toml con TUI de capas
```

Cada agente CLI tiene la misma estructura interna:

```
<agente>/
├── agent.py        ← entry point Click (función main())
├── orchestrator.py ← coordina los checks/analyzers
├── config.py       ← lee sección [tool.<agente>] de pyproject.toml
└── checks/ o analyzers/ o metrics/
    └── *.py        ← implementación de cada verificación
```

El módulo `config_editor/` tiene estructura propia:

```
config_editor/
├── __init__.py
├── personal_config.py  ← PersonalConfig: load/set/delete/save (~/.config/eqa/config.toml)
└── app.py              ← EqaConfigApp (Textual), EditScreen, QuitScreen, _SCHEMA
```

Las herramientas externas (cppcheck, flawfinder, lizard) se invocan como subprocesos desde los checks.

---

## Precedencia de configuración

`shared/config.load_toml_section()` fusiona tres capas:

```
defaults del dataclass de cada agente
    ↓ sobreescrito por
[tool.<agente>] en pyproject.toml del proyecto
    ↓ sobreescrito por
[<agente>] en ~/.config/eqa/config.toml  ← config personal
```

El merge es clave a clave (`apply_personal=True` por defecto). Los tests que verifican solo la carga de config de proyecto usan `apply_personal=False`.

---

## Entorno de desarrollo

**Prerequisitos del sistema:**

```bash
brew install cppcheck          # macOS — obligatorio para codeguard-c
```

**Setup del proyecto:**

```bash
# Con uv (recomendado — sincroniza el venv existente):
uv pip install -e ".[dev]"

# O con pip directamente:
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

**Verificar que todo funciona:**

```bash
cppcheck --version             # Cppcheck 2.x
codeguard-c --help
eqa-config --help
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
- `docs/<nombre>` — documentación
- `test/<nombre>` — tests

---

## Tests

Estructura espejada a `src/`:

```
tests/
├── conftest.py
├── unit/
│   ├── codeguard_c/
│   ├── designreviewer_c/
│   ├── architectanalyst_c/
│   ├── config_editor/       ← test_personal_config.py, test_merge_config.py, test_app.py
│   └── shared/
├── integration/             ← tests que invocan las herramientas C reales + config merge
└── e2e/                     ← tests sobre el proyecto de ejemplo en examples/sample_c_project/
```

Los tests de integración y e2e requieren cppcheck instalado en el sistema.

---

## CI/CD

- **CI** (`.github/workflows/ci.yml`): lint (black, ruff, mypy) + pytest en Python 3.11 y 3.12
- **Releases**: tags `v*.*.*` + GitHub Release creado manualmente con `gh release create`
- **Branch protection** en `main`: PRs requeridos, los tres jobs de CI deben pasar

---

## Archivos de referencia

- `examples/configs/pyproject.toml.example` — todas las opciones de configuración de los tres agentes
- `examples/sample_c_project/` — proyecto C de ejemplo con violaciones controladas para los tres agentes
- `docs/agentes/codeguard-c.md` — referencia técnica de CodeGuard-C (checks, salidas, configuración)
- `docs/guias/codeguard-c.md` — guía de usuario de CodeGuard-C
- `docs/agentes/designreviewer-c.md` — referencia técnica de DesignReviewer-C (INC001, INC002, LAY001)
- `docs/guias/designreviewer-c.md` — guía de usuario de DesignReviewer-C
- `docs/agentes/architectanalyst-c.md` — referencia técnica de ArchitectAnalyst-C (ARC001, ARC002, ARC003)
- `docs/guias/architectanalyst-c.md` — guía de usuario de ArchitectAnalyst-C
- `docs/agentes/eqa-config.md` — referencia técnica de eqa-config (TUI, PersonalConfig, precedencia)
- `docs/guias/eqa-config.md` — guía de usuario de eqa-config
- `docs/agentes/quality-report.md` — referencia técnica del sistema de reportes Markdown (QualityReport, DimensionStatus, render_markdown, dimensiones por agente)
- `docs/guias/quality-report.md` — guía de uso del flag `--report` en los tres agentes
- `docs/agentes/eqa-init.md` — referencia técnica de eqa-init (DirectoryScanner, ConfigWriter, LayerWizardApp, defaults generados)
- `docs/guias/eqa-init.md` — guía de usuario de eqa-init (TUI de capas, --no-interactive, casos de uso)
- `docs/specs/` — plan del proyecto y plan de entorno original
