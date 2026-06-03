from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text

from eqa_framework.codeguard_c.config import CodeGuardConfig
from eqa_framework.codeguard_c.orchestrator import BUDGET_SECONDS, CodeGuardOrchestrator
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
        table.add_column("Rule", no_wrap=True, width=24)
        table.add_column("Message", no_wrap=True, overflow="ellipsis")

        for f in sorted(report.findings, key=lambda x: (x.severity.value, str(x.file), x.line)):
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

    if elapsed > BUDGET_SECONDS:
        _console.print(
            f"[yellow]⚠ Analysis took {elapsed:.1f}s (budget: {BUDGET_SECONDS}s)[/yellow]"
        )


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


def _build_quality_report(report: Report, target_path: str, file_count: int) -> QualityReport:
    def _dim(name: str, tools: list[str]) -> DimensionStatus:
        matching = [f for f in report.findings if f.tool in tools]
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

    complexity_dim = _dim("Complejidad", ["lizard"])
    security_dim = _dim("Seguridad", ["flawfinder"])
    misra_dim = _dim("MISRA", ["cppcheck"])

    dims = [complexity_dim, security_dim, misra_dim]
    any_critical = any(d.status == "critical" for d in dims)
    any_warning = any(d.status == "warning" for d in dims)

    if any_critical:
        summary = "Se detectaron violaciones críticas. Revisar antes de continuar."
    elif any_warning:
        summary = "Hay advertencias que merecen atención."
    else:
        summary = "Sin observaciones. El código cumple con todos los umbrales configurados."

    return QualityReport(
        agent_name="CodeGuard-C",
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
    """CodeGuard-C — análisis rápido pre-commit para C embebido."""
    project_root = config_path.parent if config_path else path if path.is_dir() else path.parent
    config = CodeGuardConfig.from_project(project_root)
    orchestrator = CodeGuardOrchestrator(config)

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

    raise SystemExit(0)
