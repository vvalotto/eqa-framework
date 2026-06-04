from __future__ import annotations

import click
from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from eqa_framework import __version__

_console = Console()


def _commands_table() -> Table:
    table = Table(box=None, padding=(0, 2, 0, 0), show_header=False)
    table.add_column("cmd", style="bold cyan", no_wrap=True)
    table.add_column("when", style="dim", no_wrap=True)
    table.add_column("desc")

    rows = [
        ("codeguard-c", "pre-commit", "Análisis de MISRA-C, seguridad y complejidad"),
        ("designreviewer-c", "PR review", "Dependencias circulares y violaciones de capa"),
        (
            "architectanalyst-c",
            "fin de sprint",
            "Métricas de acoplamiento y tendencias arquitectónicas",
        ),
        ("eqa-config", "cuando quieras", "Editor TUI de umbrales personales"),
        ("eqa-init", "al incorporar el proyecto", "Bootstrap de pyproject.toml con TUI de capas"),
    ]
    for cmd, when, desc in rows:
        table.add_row(cmd, Text(f"[{when}]", style="dim"), desc)

    return table


def _usage_table() -> Table:
    table = Table(box=None, padding=(0, 2, 0, 0), show_header=False)
    table.add_column("example", style="green", no_wrap=True)
    table.add_column("desc", style="dim")

    rows = [
        ("eqa-init .", "Inicializar configuración (una vez)"),
        ("codeguard-c src/", "Analizar código antes de commitear"),
        ("designreviewer-c src/", "Verificar diseño al abrir un PR"),
        ("architectanalyst-c src/ --sprint-id s01", "Snapshot de arquitectura al cerrar el sprint"),
        ("codeguard-c src/ --report calidad.md", "Generar perfil de calidad en Markdown"),
        ("eqa-init --guide", "Mostrar la guía completa de instalación"),
    ]
    for example, desc in rows:
        table.add_row(example, desc)

    return table


@click.command()
def main() -> None:
    """eqa-framework — Control de Calidad Automatizado para C Embebido."""
    _console.print()
    _console.print(
        Panel(
            Text.assemble(
                ("eqa-framework ", "bold white"),
                (f"v{__version__}", "dim"),
                (" — Control de Calidad Automatizado para C Embebido", "white"),
            ),
            border_style="cyan",
            expand=False,
        )
    )

    _console.print(Padding("[bold]Comandos disponibles:[/bold]", (1, 0, 0, 0)))
    _console.print(_commands_table())

    _console.print(Padding("[bold]Uso rápido:[/bold]", (1, 0, 0, 0)))
    _console.print(_usage_table())

    _console.print(
        Padding(
            "[dim]Documentación: https://github.com/vvalotto/eqa-framework[/dim]",
            (1, 0, 1, 0),
        )
    )
