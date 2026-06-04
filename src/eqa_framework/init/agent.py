from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown

from eqa_framework.init.scanner import DirectoryScanner
from eqa_framework.init.writer import ConfigWriter, generate_toml

_SECTION_LABELS = {
    "[tool.codeguard-c]": "codeguard-c",
    "[tool.designreviewer-c]": "designreviewer-c",
    "[tool.architectanalyst-c]": "architectanalyst-c",
}


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--src-dir", default=None, help="Subdirectorio de fuentes a escanear para capas.")
@click.option(
    "--no-interactive",
    is_flag=True,
    default=False,
    help="Escribe defaults sin lanzar la TUI. La sección de capas queda pendiente de edición manual.",
)
@click.option(
    "--guide",
    is_flag=True,
    default=False,
    help="Muestra la guía de instalación y quick start.",
)
def main(path: Path, src_dir: str | None, no_interactive: bool, guide: bool) -> None:
    """eqa-init — inicializa la configuración de eqa-framework en un proyecto C."""
    if guide:
        content = (
            files("eqa_framework.init").joinpath("getting-started.md").read_text(encoding="utf-8")
        )
        Console().print(Markdown(content))
        raise SystemExit(0)
    scanner = DirectoryScanner()
    candidates = scanner.scan(path, src_dir)

    if candidates:
        click.echo(f"Subdirectorios detectados como posibles capas: {', '.join(candidates)}")
    else:
        click.echo("No se detectaron subdirectorios candidatos a capa.")

    layers: list[str] = []

    if not no_interactive:
        from eqa_framework.init.app import LayerWizardApp

        result = LayerWizardApp(candidates).run()
        if result is None:
            click.echo("Cancelado. No se escribió ningún archivo.")
            raise SystemExit(0)
        layers = result
    else:
        layers = []

    toml_block = generate_toml(layers)
    writer = ConfigWriter()
    written = writer.write(path, toml_block)

    target = path / "pyproject.toml"

    if not written:
        click.echo(f"Sin cambios: todas las secciones de eqa-framework ya estaban en {target}.")
        raise SystemExit(0)

    written_labels = [_SECTION_LABELS.get(m, m) for m in written]
    click.echo(f"Secciones escritas en {target}: {', '.join(written_labels)}")

    if no_interactive or not layers:
        click.echo(
            "  → Editar [tool.designreviewer-c.layers] en pyproject.toml para definir las capas."
        )

    raise SystemExit(0)
