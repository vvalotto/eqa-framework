from __future__ import annotations

from typing import Any

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, Input, Label, Static


def _clean_layer_name(raw: str) -> str:
    """Normaliza el nombre de una capa: strip y minúsculas."""
    return raw.strip().lower()


def _is_valid_layer_name(name: str) -> bool:
    """Retorna True si el nombre es un identificador no vacío sin espacios."""
    cleaned = _clean_layer_name(name)
    return bool(cleaned) and " " not in cleaned


# ---------------------------------------------------------------------------
# Modal de nombre de capa
# ---------------------------------------------------------------------------


class AddLayerScreen(ModalScreen[str | None]):
    CSS = """
    AddLayerScreen {
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

    def compose(self) -> ComposeResult:
        with Static(id="dialog"):
            yield Label("Nombre de la nueva capa (ej: drivers):", id="prompt")
            yield Input(placeholder="nombre", id="input")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        name = _clean_layer_name(event.value)
        self.dismiss(name if _is_valid_layer_name(name) else None)

    def on_key(self, event: Any) -> None:
        if event.key == "escape":
            self.dismiss(None)


# ---------------------------------------------------------------------------
# App principal
# ---------------------------------------------------------------------------


class LayerWizardApp(App[list[str] | None]):
    """TUI para definir la jerarquía de capas de un proyecto C embebido."""

    TITLE = "eqa-init — Jerarquía de capas"
    BINDINGS = [
        Binding("a", "add_layer", "Agregar", show=True),
        Binding("x", "delete_layer", "Eliminar", show=True),
        Binding("shift+up", "move_up", "Subir", show=True),
        Binding("shift+down", "move_down", "Bajar", show=True),
        Binding("enter", "confirm", "Confirmar", show=True),
        Binding("q,escape", "cancel", "Cancelar", show=True),
    ]

    def __init__(self, candidates: list[str]) -> None:
        super().__init__()
        self._layers: list[str] = list(candidates)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            "Ordenar de menor a mayor nivel. [shift+↑↓] mover · [A] agregar · [X] eliminar · [Enter] confirmar · [Q] cancelar",
            id="hint",
        )
        yield DataTable(id="table", cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("#", "Capa")
        self._refresh_table()

    def _refresh_table(self, restore_row: int = 0) -> None:
        table = self.query_one(DataTable)
        table.clear()
        for i, layer in enumerate(self._layers, start=1):
            table.add_row(str(i), layer)
        if self._layers:
            table.move_cursor(row=min(restore_row, len(self._layers) - 1))

    @work
    async def action_add_layer(self) -> None:
        result = await self.push_screen_wait(AddLayerScreen())
        if result is None:
            return
        if result in self._layers:
            self.notify(f"La capa '{result}' ya existe", severity="warning")
            return
        self._layers.append(result)
        self._refresh_table(restore_row=len(self._layers) - 1)

    def action_delete_layer(self) -> None:
        table = self.query_one(DataTable)
        row = table.cursor_row
        if 0 <= row < len(self._layers):
            removed = self._layers.pop(row)
            self.notify(f"Capa '{removed}' eliminada")
            self._refresh_table(restore_row=max(0, row - 1))

    def action_move_up(self) -> None:
        table = self.query_one(DataTable)
        row = table.cursor_row
        if row > 0:
            self._layers[row], self._layers[row - 1] = self._layers[row - 1], self._layers[row]
            self._refresh_table(restore_row=row - 1)

    def action_move_down(self) -> None:
        table = self.query_one(DataTable)
        row = table.cursor_row
        if row < len(self._layers) - 1:
            self._layers[row], self._layers[row + 1] = self._layers[row + 1], self._layers[row]
            self._refresh_table(restore_row=row + 1)

    def action_confirm(self) -> None:
        self.exit(list(self._layers))

    @work
    async def action_cancel(self) -> None:
        self.exit(None)
