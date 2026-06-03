from __future__ import annotations

import json
import shutil
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text

from eqa_framework.designreviewer_c.config import DesignReviewerConfig
from eqa_framework.designreviewer_c.orchestrator import DesignReviewerOrchestrator
from eqa_framework.shared.report import (
    DimensionStatus,
    QualityReport,
    StatusLiteral,
    render_markdown,
    write_report,
)
from eqa_framework.shared.reporting import Report, Severity

_SEVERITY_STYLE: dict[Severity, str] = {
    Severity.CRITICAL: "bold red",
    Severity.ERROR: "red",
    Severity.WARNING: "yellow",
    Severity.INFO: "cyan",
}

_console = Console(width=max(120, shutil.get_terminal_size((120, 24)).columns))


def _render_text(report: Report, elapsed: float) -> None:
    if report.findings:
        table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
        table.add_column("File", style="dim", no_wrap=True)
        table.add_column("Line", justify="right", style="dim", width=5)
        table.add_column("Sev", no_wrap=True, width=8)
        table.add_column("Rule", no_wrap=True, width=8)
        table.add_column("Message", no_wrap=True, overflow="ellipsis")

        for f in sorted(report.findings, key=lambda x: (str(x.file), x.severity.value, x.line)):
            style = _SEVERITY_STYLE.get(f.severity, "")
            msg = f.message if len(f.message) <= 80 else f.message[:79] + "…"
            table.add_row(
                str(f.file),
                str(f.line),
                Text(f.severity.value, style=style),
                f.rule,
                msg,
            )

        _console.print(table)

    counts = " · ".join(
        f"[{_SEVERITY_STYLE[sev]}]{report.count(sev)} {sev.value}[/{_SEVERITY_STYLE[sev]}]"
        for sev in Severity
        if report.count(sev) > 0
    )
    summary = counts if counts else "[green]No findings[/green]"
    _console.print(f"\n{summary}  [dim]({elapsed:.1f}s)[/dim]")


def _render_json(report: Report) -> None:
    data = [
        {
            "file": str(f.file),
            "line": f.line,
            "severity": f.severity.value,
            "rule": f.rule,
            "message": f.message,
            "tool": f.tool,
        }
        for f in report.findings
    ]
    click.echo(json.dumps(data, indent=2))


def _find_project_root(start: Path) -> Path:
    """Walk up from start until a pyproject.toml or .embedded-qa.toml is found."""
    current = start if start.is_dir() else start.parent
    for directory in [current, *current.parents]:
        if (directory / "pyproject.toml").exists() or (directory / ".embedded-qa.toml").exists():
            return directory
    return current


def _build_quality_report(report: Report, target_path: str, file_count: int) -> QualityReport:
    from datetime import date

    def _dim(name: str, rules: list[str]) -> DimensionStatus:
        matching = [f for f in report.findings if f.rule in rules]
        critical = [f for f in matching if f.severity == Severity.CRITICAL]
        warnings = [f for f in matching if f.severity == Severity.WARNING]
        status: StatusLiteral
        if critical:
            status = "critical"
            top = critical[:5]
        elif warnings:
            status = "warning"
            top = warnings[:5]
        else:
            return DimensionStatus(name, "ok")
        findings_str = [f"{f.file}:{f.line} — {f.message[:60]}" for f in top]
        return DimensionStatus(name, status, findings_str)

    deps_dim = _dim("Dependencias", ["INC001", "INC002"])
    layers_dim = _dim("Capas", ["LAY001"])
    dims = [deps_dim, layers_dim]

    any_critical = any(d.status == "critical" for d in dims)
    any_warning = any(d.status == "warning" for d in dims)
    if any_critical:
        summary = "Se detectaron violaciones críticas de diseño. Revisar antes de continuar."
    elif any_warning:
        summary = "Hay advertencias de diseño que merecen atención."
    else:
        summary = "Sin observaciones. El diseño cumple con los criterios configurados."

    return QualityReport(
        agent_name="DesignReviewer-C",
        target_path=target_path,
        file_count=file_count,
        date=str(date.today()),
        dimensions=dims,
        summary=summary,
    )


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None)
@click.option(
    "--report",
    "report_output",
    is_flag=False,
    flag_value="-",
    default=None,
    help="Genera perfil de calidad en Markdown. Sin argumento: stdout. Con argumento: archivo.",
)
def main(path: Path, fmt: str, config_path: Path | None, report_output: str | None) -> None:
    """DesignReviewer-C — análisis de diseño para PR review."""
    project_root = config_path.parent if config_path else _find_project_root(path)
    config = DesignReviewerConfig.from_project(project_root)
    orchestrator = DesignReviewerOrchestrator(config)

    target_files = list(path.rglob("*.[ch]")) if path.is_dir() else [path]
    report, elapsed = orchestrator.run(project_root, target_files)

    if fmt == "json":
        _render_json(report)
    else:
        _render_text(report, elapsed)

    if report_output is not None:
        output = None if report_output == "-" else report_output
        qr = _build_quality_report(report, str(path), len(target_files))
        write_report(render_markdown(qr), output)

    raise SystemExit(orchestrator.exit_code(report))
