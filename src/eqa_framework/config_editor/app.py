from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, Input, Label, Static

from eqa_framework.config_editor.personal_config import PersonalConfig
from eqa_framework.shared.config import load_toml_section

# ---------------------------------------------------------------------------
# Schema: keys editables por agente
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class KeySpec:
    agent: str
    key: str
    type_: type[Any]
    default: Any


_SCHEMA: list[KeySpec] = [
    KeySpec("codeguard-c", "max_cyclomatic_complexity", int, 10),
    KeySpec("codeguard-c", "max_function_lines", int, 50),
    KeySpec("codeguard-c", "misra_mandatory", bool, True),
    KeySpec("codeguard-c", "misra_required", bool, True),
    KeySpec("codeguard-c", "misra_advisory", bool, False),
    KeySpec("designreviewer-c", "max_fan_out", int, 12),
    KeySpec("designreviewer-c", "max_function_lines", int, 80),
    KeySpec("designreviewer-c", "max_parameters", int, 6),
    KeySpec("designreviewer-c", "max_nesting_depth", int, 4),
    KeySpec("designreviewer-c", "max_cc_critical", int, 15),
    KeySpec("architectanalyst-c", "max_instability", float, 0.8),
    KeySpec("architectanalyst-c", "max_distance_warning", float, 0.3),
    KeySpec("architectanalyst-c", "max_distance_critical", float, 0.5),
    KeySpec("architectanalyst-c", "db_path", str, ".quality_control/embedded_architecture.db"),
]


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _parse(raw: str, type_: type[Any]) -> Any:
    if type_ is bool:
        if raw.lower() in ("true", "1", "yes"):
            return True
        if raw.lower() in ("false", "0", "no"):
            return False
        raise ValueError(f"valor booleano inválido: {raw!r}")
    return type_(raw)


# ---------------------------------------------------------------------------
# Modal de edición
# ---------------------------------------------------------------------------


class EditScreen(ModalScreen[str | None]):
    CSS = """
    EditScreen {
        align: center middle;
    }
    #dialog {
        width: 60;
        height: 9;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    #prompt { margin-bottom: 1; }
    """

    def __init__(self, prompt: str, current: str) -> None:
        super().__init__()
        self._prompt = prompt
        self._current = current

    def compose(self) -> ComposeResult:
        with Static(id="dialog"):
            yield Label(self._prompt, id="prompt")
            yield Input(value=self._current, id="input")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def on_key(self, event: Any) -> None:
        if event.key == "escape":
            self.dismiss(None)


# ---------------------------------------------------------------------------
# Modal de confirmación de salida
# ---------------------------------------------------------------------------


class QuitScreen(ModalScreen[bool]):
    CSS = """
    QuitScreen {
        align: center middle;
    }
    #dialog {
        width: 50;
        height: 7;
        border: thick $warning;
        background: $surface;
        padding: 1 2;
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        with Static(id="dialog"):
            yield Label("Hay cambios sin guardar. ¿Salir de todos modos? (S/N)")

    def on_key(self, event: Any) -> None:
        if event.key in ("s", "y"):
            self.dismiss(True)
        elif event.key in ("n", "escape"):
            self.dismiss(False)


# ---------------------------------------------------------------------------
# App principal
# ---------------------------------------------------------------------------


class EqaConfigApp(App[None]):
    TITLE = "eqa-config — Editor de configuración personal"
    BINDINGS = [
        Binding("e,enter", "edit_row", "Editar", show=True),
        Binding("d", "delete_row", "Borrar personal", show=True),
        Binding("s", "save", "Guardar", show=True),
        Binding("q", "request_quit", "Salir", show=True),
    ]

    def __init__(
        self,
        project_root: Path | None = None,
        personal_config_path: Path | None = None,
    ) -> None:
        super().__init__()
        self._project_root = project_root or Path.cwd()
        self._personal = (
            PersonalConfig(personal_config_path) if personal_config_path else PersonalConfig()
        )
        self._personal.load()
        self._project: dict[str, dict[str, Any]] = {}
        self._dirty = False

        for agent in ("codeguard-c", "designreviewer-c", "architectanalyst-c"):
            self._project[agent] = load_toml_section(
                self._project_root,
                agent,
                apply_personal=False,
            )

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="table", cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Agente", "Clave", "Default", "Proyecto", "Personal", "Efectivo")
        self._refresh_table()

    def _refresh_table(self, restore_row: int = 0) -> None:
        table = self.query_one(DataTable)
        table.clear()
        for spec in _SCHEMA:
            default_val = spec.default
            project_val = self._project.get(spec.agent, {}).get(spec.key)
            personal_val = self._personal._data.get(spec.agent, {}).get(spec.key)

            effective = (
                personal_val
                if personal_val is not None
                else (project_val if project_val is not None else default_val)
            )

            row = (
                spec.agent,
                spec.key,
                _fmt(default_val),
                _fmt(project_val) if project_val is not None else "—",
                _fmt(personal_val) if personal_val is not None else "—",
                _fmt(effective),
            )
            table.add_row(*row, key=f"{spec.agent}::{spec.key}")
        table.move_cursor(row=restore_row)

    def _current_spec(self) -> KeySpec | None:
        table = self.query_one(DataTable)
        if table.cursor_row < 0 or table.cursor_row >= len(_SCHEMA):
            return None
        spec: KeySpec = _SCHEMA[table.cursor_row]
        return spec

    @work
    async def action_edit_row(self) -> None:
        table = self.query_one(DataTable)
        current_row = table.cursor_row
        spec = self._current_spec()
        if spec is None:
            return
        personal_val = self._personal._data.get(spec.agent, {}).get(spec.key)
        current_str = _fmt(personal_val) if personal_val is not None else ""
        prompt = f"[{spec.agent}] {spec.key} ({spec.type_.__name__}) — Enter para confirmar, Esc para cancelar"

        result = await self.push_screen_wait(EditScreen(prompt, current_str))
        if result is None:
            return
        try:
            parsed = _parse(result, spec.type_)
        except (ValueError, TypeError):
            self.notify(f"Valor inválido para tipo {spec.type_.__name__!r}", severity="error")
            return
        self._personal.set(spec.agent, spec.key, parsed)
        self._dirty = True
        self._refresh_table(restore_row=current_row)

    def action_delete_row(self) -> None:
        table = self.query_one(DataTable)
        current_row = table.cursor_row
        spec = self._current_spec()
        if spec is None:
            return
        self._personal.delete(spec.agent, spec.key)
        self._dirty = True
        self._refresh_table(restore_row=current_row)
        self.notify(f"{spec.key} eliminado de config personal")

    def action_save(self) -> None:
        self._personal.save()
        self._dirty = False
        self.notify("Guardado en ~/.config/eqa/config.toml")

    @work
    async def action_request_quit(self) -> None:
        if self._dirty:
            confirmed = await self.push_screen_wait(QuitScreen())
            if not confirmed:
                return
        self.exit()


def main() -> None:
    EqaConfigApp().run()


if __name__ == "__main__":
    main()
