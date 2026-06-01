from __future__ import annotations

from pathlib import Path

import click

from eqa_framework.codeguard_c.config import CodeGuardConfig
from eqa_framework.codeguard_c.orchestrator import CodeGuardOrchestrator


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None)
def main(path: Path, fmt: str, config_path: Path | None) -> None:
    """CodeGuard-C — análisis rápido pre-commit para C embebido."""
    project_root = config_path.parent if config_path else path if path.is_dir() else path.parent
    config = CodeGuardConfig.from_project(project_root)
    orchestrator = CodeGuardOrchestrator(config)

    target_files = list(path.rglob("*.[ch]")) if path.is_dir() else [path]
    orchestrator.run(project_root, target_files)

    # CodeGuard-C nunca bloquea el commit
    raise SystemExit(0)
