from __future__ import annotations

import json
import shutil
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text

from eqa_framework.architectanalyst_c.config import ArchitectAnalystConfig
from eqa_framework.architectanalyst_c.metrics.coupling_analyzer import ModuleMetrics
from eqa_framework.architectanalyst_c.orchestrator import ArchitectAnalystOrchestrator
from eqa_framework.architectanalyst_c.snapshot_store import Snapshot
from eqa_framework.shared.reporting import Report, Severity

_SEVERITY_STYLE: dict[Severity, str] = {
    Severity.CRITICAL: "bold red",
    Severity.ERROR: "red",
    Severity.WARNING: "yellow",
    Severity.INFO: "cyan",
}

_THRESHOLD = 0.05  # minimum delta to show ↑/↓ instead of =

_console = Console(width=max(120, shutil.get_terminal_size((120, 24)).columns))


def _trend(current: float, previous: float | None, lower_is_better: bool = True) -> str:
    if previous is None:
        return ""
    delta = current - previous
    if abs(delta) < _THRESHOLD:
        return "="
    if lower_is_better:
        return "↑" if delta > 0 else "↓"
    return "↓" if delta > 0 else "↑"


def _trend_style(symbol: str) -> str:
    return "green" if symbol == "↓" else "red" if symbol == "↑" else "dim"


def _render_text(
    metrics: list[ModuleMetrics],
    previous: Snapshot | None,
    report: Report,
    elapsed: float,
) -> None:
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    table.add_column("Module", no_wrap=True)
    table.add_column("Ca", justify="right", width=4)
    table.add_column("Ce", justify="right", width=4)
    table.add_column("I", justify="right", width=5)
    table.add_column(" ", width=2)  # I trend
    table.add_column("A", justify="right", width=5)
    table.add_column(" ", width=2)  # A trend
    table.add_column("D", justify="right", width=5)
    table.add_column(" ", width=2)  # D trend

    for m in metrics:
        prev_m = previous.modules.get(m.module) if previous else None
        i_sym = _trend(m.instability, prev_m.instability if prev_m else None)
        a_sym = _trend(
            m.abstractness, prev_m.abstractness if prev_m else None, lower_is_better=False
        )
        d_sym = _trend(m.distance, prev_m.distance if prev_m else None)

        table.add_row(
            m.module,
            str(m.ca),
            str(m.ce),
            f"{m.instability:.2f}",
            Text(i_sym, style=_trend_style(i_sym)),
            f"{m.abstractness:.2f}",
            Text(a_sym, style=_trend_style(a_sym)),
            f"{m.distance:.2f}",
            Text(d_sym, style=_trend_style(d_sym)),
        )

    _console.print(table)

    if report.findings:
        _console.print()
        for f in sorted(report.findings, key=lambda x: (x.severity.value, str(x.file))):
            style = _SEVERITY_STYLE.get(f.severity, "")
            _console.print(f"  [{style}]{f.severity.value}[/{style}]  [{f.rule}]  {f.message}")

    counts = " · ".join(
        f"[{_SEVERITY_STYLE[sev]}]{report.count(sev)} {sev.value}[/{_SEVERITY_STYLE[sev]}]"
        for sev in Severity
        if report.count(sev) > 0
    )
    summary = counts if counts else "[green]No findings[/green]"
    _console.print(f"\n{summary}  [dim]({elapsed:.1f}s)[/dim]")


def _render_json(metrics: list[ModuleMetrics], report: Report) -> None:
    data = {
        "metrics": [
            {
                "module": m.module,
                "ca": m.ca,
                "ce": m.ce,
                "instability": round(m.instability, 4),
                "abstractness": round(m.abstractness, 4),
                "distance": round(m.distance, 4),
            }
            for m in metrics
        ],
        "findings": [
            {
                "file": str(f.file),
                "severity": f.severity.value,
                "rule": f.rule,
                "message": f.message,
            }
            for f in report.findings
        ],
    }
    click.echo(json.dumps(data, indent=2))


def _find_project_root(start: Path) -> Path:
    current = start if start.is_dir() else start.parent
    for directory in [current, *current.parents]:
        if (directory / "pyproject.toml").exists() or (directory / ".embedded-qa.toml").exists():
            return directory
    return current


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--sprint-id", default="", help="Identificador del sprint para el snapshot histórico."
)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None)
def main(path: Path, sprint_id: str, fmt: str, config_path: Path | None) -> None:
    """ArchitectAnalyst-C — análisis arquitectónico de fin de sprint."""
    project_root = config_path.parent if config_path else _find_project_root(path)
    config = ArchitectAnalystConfig.from_project(project_root)
    orchestrator = ArchitectAnalystOrchestrator(config)

    target_files = list(path.rglob("*.[ch]")) if path.is_dir() else [path]
    report, metrics, previous, elapsed = orchestrator.run(project_root, target_files, sprint_id)

    if fmt == "json":
        _render_json(metrics, report)
    else:
        _render_text(metrics, previous, report, elapsed)

    # ArchitectAnalyst-C nunca bloquea — solo informa
    raise SystemExit(0)
