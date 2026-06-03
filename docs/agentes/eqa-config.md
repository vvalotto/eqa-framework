# eqa-config — Documentación técnica

## Qué hace

`eqa-config` es una TUI (Terminal User Interface) que permite al desarrollador editar su configuración personal de los agentes eqa sin tocar el `pyproject.toml` del proyecto. Los valores personales se guardan en `~/.config/eqa/config.toml` y tienen precedencia sobre los valores del proyecto en todas las ejecuciones de los agentes.

El objetivo es que cada desarrollador pueda ajustar umbrales a su estilo de trabajo (por ejemplo, bajar `max_cyclomatic_complexity` para ser más estricto consigo mismo) sin afectar la configuración compartida del equipo.

---

## Arquitectura interna

```
eqa-config
      │
      ▼
  app.py  (Textual App)
      │  carga PersonalConfig (~/.config/eqa/config.toml)
      │  carga config de proyecto (pyproject.toml, apply_personal=False)
      │
      ├── DataTable  ← tabla de 14 keys editables de los tres agentes
      ├── EditScreen ← modal de edición con validación de tipo (ModalScreen)
      └── QuitScreen ← modal de confirmación al salir con cambios sin guardar
```

```
config_editor/
├── __init__.py
├── app.py            ← EqaConfigApp (Textual), EditScreen, QuitScreen, _SCHEMA
└── personal_config.py ← PersonalConfig: load/set/delete/save
```

---

## Schema de keys editables

| Agente | Clave | Tipo | Default |
|--------|-------|------|---------|
| `codeguard-c` | `max_cyclomatic_complexity` | int | 10 |
| `codeguard-c` | `max_function_lines` | int | 50 |
| `codeguard-c` | `misra_mandatory` | bool | True |
| `codeguard-c` | `misra_required` | bool | True |
| `codeguard-c` | `misra_advisory` | bool | False |
| `designreviewer-c` | `max_fan_out` | int | 12 |
| `designreviewer-c` | `max_function_lines` | int | 80 |
| `designreviewer-c` | `max_parameters` | int | 6 |
| `designreviewer-c` | `max_nesting_depth` | int | 4 |
| `designreviewer-c` | `max_cc_critical` | int | 15 |
| `architectanalyst-c` | `max_instability` | float | 0.8 |
| `architectanalyst-c` | `max_distance_warning` | float | 0.3 |
| `architectanalyst-c` | `max_distance_critical` | float | 0.5 |
| `architectanalyst-c` | `db_path` | str | `.quality_control/embedded_architecture.db` |

---

## PersonalConfig

Módulo `config_editor/personal_config.py`. Gestiona `~/.config/eqa/config.toml`.

### API

```python
class PersonalConfig:
    def __init__(self, config_path: Path = ~/.config/eqa/config.toml) -> None
    def load(self) -> dict[str, dict[str, Any]]   # retorna vacío si no existe
    def set(self, agent: str, key: str, value: Any) -> None
    def delete(self, agent: str, key: str) -> None  # noop si no existe
    def save(self) -> None                           # crea directorio si falta
```

### Formato del archivo

```toml
[codeguard-c]
max_cyclomatic_complexity = 8

[architectanalyst-c]
max_instability = 0.6
```

Las secciones espejean `[tool.<agente>]` de `pyproject.toml`, pero sin el prefijo `tool.`.

---

## Precedencia de configuración

El merge se aplica en `shared/config.load_toml_section()` con `apply_personal=True` (defecto):

```
defaults del dataclass
    ↓ sobreescrito por
[tool.<agente>] en pyproject.toml del proyecto
    ↓ sobreescrito por
[<agente>] en ~/.config/eqa/config.toml
```

El merge es **clave a clave**: tener un valor personal para `max_instability` no anula el resto de keys del agente.

`load_toml_section()` acepta `personal_config_path: Path | None` para inyectar una ruta alternativa (útil en tests).

---

## Validación de tipos en la TUI

La función `_parse(raw: str, type_: type) -> Any` valida el valor ingresado antes de guardarlo:

| Tipo | Valores válidos | Error |
|------|----------------|-------|
| `int` | cualquier entero | `ValueError` si no parsea |
| `float` | cualquier flotante | `ValueError` si no parsea |
| `bool` | `true/false`, `1/0`, `yes/no` | `ValueError` para cualquier otro valor |
| `str` | cualquier texto | nunca falla |

---

## Bindings de teclado

| Tecla | Acción |
|-------|--------|
| `↑` / `↓` | Navegar filas |
| `E` / `Enter` | Editar valor personal de la fila seleccionada |
| `D` | Borrar valor personal (reset a proyecto/default) |
| `S` | Guardar a `~/.config/eqa/config.toml` |
| `Q` | Salir (confirma si hay cambios sin guardar) |
| `Esc` | Cancelar edición (en modal) |

---

## Consideraciones técnicas

- `push_screen_wait` de Textual requiere ser llamado desde un worker; `action_edit_row` y `action_request_quit` están decorados con `@work` (de `textual`).
- Tras editar o borrar, el cursor se restaura en la fila original mediante `DataTable.move_cursor(row=n)`.
- Las clases `EditScreen(ModalScreen[str | None])`, `QuitScreen(ModalScreen[bool])` y `EqaConfigApp(App[None])` requieren el override mypy `disallow_subclassing_any = false` porque Textual no expone tipos genéricos que mypy strict pueda resolver.
