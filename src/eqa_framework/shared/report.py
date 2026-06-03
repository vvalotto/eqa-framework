from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

StatusLiteral = Literal["ok", "warning", "critical"]

_ICON: dict[StatusLiteral, str] = {
    "ok": "✅",
    "warning": "⚠️",
    "critical": "❌",
}

_LABEL: dict[StatusLiteral, str] = {
    "ok": "OK",
    "warning": "ADVERTENCIA",
    "critical": "CRÍTICO",
}


@dataclass
class DimensionStatus:
    name: str
    status: StatusLiteral
    findings: list[str] = field(default_factory=list)


@dataclass
class QualityReport:
    agent_name: str
    target_path: str
    file_count: int
    date: str
    dimensions: list[DimensionStatus]
    summary: str


def write_report(markdown: str, output: str | None) -> None:
    """Escribe el Markdown a un archivo o a stdout.

    Si output es None imprime a stdout. Si es una ruta, escribe el archivo
    y confirma en stderr para no contaminar stdout.
    """
    if output is None:
        sys.stdout.write(markdown)
    else:
        path = Path(output)
        path.write_text(markdown, encoding="utf-8")
        sys.stderr.write(f"Reporte guardado en {path}\n")


def render_markdown(report: QualityReport) -> str:
    lines: list[str] = []

    lines.append(f"# {report.agent_name} — Perfil de Calidad")
    lines.append("")
    lines.append(
        f"**Proyecto:** `{report.target_path}` · " f"{report.file_count} archivos · {report.date}"
    )
    lines.append("")

    lines.append("## Perfil")
    lines.append("")
    lines.append("| Dimensión | Estado |")
    lines.append("|-----------|--------|")
    for dim in report.dimensions:
        icon = _ICON[dim.status]
        label = _LABEL[dim.status]
        lines.append(f"| {dim.name} | {icon} {label} |")
    lines.append("")

    dims_with_findings = [d for d in report.dimensions if d.findings]
    if dims_with_findings:
        lines.append("## Principales hallazgos")
        lines.append("")
        for dim in dims_with_findings:
            icon = _ICON[dim.status]
            label = _LABEL[dim.status]
            lines.append(f"**{icon} {label} — {dim.name}**")
            for finding in dim.findings:
                lines.append(f"- {finding}")
            lines.append("")

    lines.append("## Resumen")
    lines.append("")
    lines.append(report.summary)
    lines.append("")

    return "\n".join(lines)
