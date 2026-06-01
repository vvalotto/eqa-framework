from __future__ import annotations

from pathlib import Path

import click

from eqa_framework.designreviewer_c.config import DesignReviewerConfig
from eqa_framework.designreviewer_c.orchestrator import DesignReviewerOrchestrator


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None)
def main(path: Path, fmt: str, config_path: Path | None) -> None:
    """DesignReviewer-C — análisis de diseño para PR review."""
    project_root = config_path.parent if config_path else path if path.is_dir() else path.parent
    config = DesignReviewerConfig.from_project(project_root)
    orchestrator = DesignReviewerOrchestrator(config)

    target_files = list(path.rglob("*.[ch]")) if path.is_dir() else [path]
    report = orchestrator.run(project_root, target_files)

    raise SystemExit(orchestrator.exit_code(report))
