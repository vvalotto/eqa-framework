from __future__ import annotations

from pathlib import Path

import click

from eqa_framework.architectanalyst_c.config import ArchitectAnalystConfig
from eqa_framework.architectanalyst_c.orchestrator import ArchitectAnalystOrchestrator


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--sprint-id", default="", help="Identificador del sprint para el snapshot histórico."
)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None)
def main(path: Path, sprint_id: str, fmt: str, config_path: Path | None) -> None:
    """ArchitectAnalyst-C — análisis arquitectónico de fin de sprint."""
    project_root = config_path.parent if config_path else path if path.is_dir() else path.parent
    config = ArchitectAnalystConfig.from_project(project_root)
    orchestrator = ArchitectAnalystOrchestrator(config)

    orchestrator.run(project_root, sprint_id)

    # ArchitectAnalyst-C nunca bloquea — solo informa
    raise SystemExit(0)
