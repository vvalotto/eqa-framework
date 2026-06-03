from __future__ import annotations

import pytest

from eqa_framework.shared.report import DimensionStatus, QualityReport, render_markdown


@pytest.fixture()
def full_report() -> QualityReport:
    return QualityReport(
        agent_name="CodeGuard-C",
        target_path="src/my_project/",
        file_count=42,
        date="2026-06-03",
        dimensions=[
            DimensionStatus("Complejidad", "warning", ["2 funciones con CC > 10"]),
            DimensionStatus("Seguridad", "ok", []),
            DimensionStatus("MISRA", "critical", ["3 funciones violan reglas obligatorias"]),
        ],
        summary="Seguridad bajo control. Revisar MISRA y complejidad.",
    )


@pytest.fixture()
def clean_report() -> QualityReport:
    return QualityReport(
        agent_name="DesignReviewer-C",
        target_path="src/",
        file_count=10,
        date="2026-06-03",
        dimensions=[
            DimensionStatus("Includes", "ok", []),
            DimensionStatus("Capas", "ok", []),
        ],
        summary="Sin hallazgos. Arquitectura correcta.",
    )


class TestRenderMarkdownHeader:
    def test_title_contains_agent_name(self, full_report: QualityReport) -> None:
        md = render_markdown(full_report)
        assert "# CodeGuard-C — Perfil de Calidad" in md

    def test_header_contains_path(self, full_report: QualityReport) -> None:
        md = render_markdown(full_report)
        assert "`src/my_project/`" in md

    def test_header_contains_file_count(self, full_report: QualityReport) -> None:
        md = render_markdown(full_report)
        assert "42 archivos" in md

    def test_header_contains_date(self, full_report: QualityReport) -> None:
        md = render_markdown(full_report)
        assert "2026-06-03" in md


class TestRenderMarkdownProfile:
    def test_profile_table_has_all_dimensions(self, full_report: QualityReport) -> None:
        md = render_markdown(full_report)
        assert "| Complejidad |" in md
        assert "| Seguridad |" in md
        assert "| MISRA |" in md

    def test_ok_icon(self, full_report: QualityReport) -> None:
        md = render_markdown(full_report)
        assert "✅ OK" in md

    def test_warning_icon(self, full_report: QualityReport) -> None:
        md = render_markdown(full_report)
        assert "⚠️ ADVERTENCIA" in md

    def test_critical_icon(self, full_report: QualityReport) -> None:
        md = render_markdown(full_report)
        assert "❌ CRÍTICO" in md


class TestRenderMarkdownFindings:
    def test_findings_section_present_when_there_are_findings(
        self, full_report: QualityReport
    ) -> None:
        md = render_markdown(full_report)
        assert "## Principales hallazgos" in md

    def test_findings_section_absent_when_all_ok(self, clean_report: QualityReport) -> None:
        md = render_markdown(clean_report)
        assert "## Principales hallazgos" not in md

    def test_only_dimensions_with_findings_appear_in_section(
        self, full_report: QualityReport
    ) -> None:
        md = render_markdown(full_report)
        # Seguridad tiene status ok y sin findings — no debe aparecer como encabezado en hallazgos
        lines = md.splitlines()
        findings_start = next(
            i for i, line in enumerate(lines) if line == "## Principales hallazgos"
        )
        summary_start = next(i for i, line in enumerate(lines) if line == "## Resumen")
        findings_lines = lines[findings_start:summary_start]
        # Solo los encabezados de dimensión tienen el patrón "**... — NombreDimension**"
        assert not any("— Seguridad" in line for line in findings_lines)

    def test_finding_text_included(self, full_report: QualityReport) -> None:
        md = render_markdown(full_report)
        assert "2 funciones con CC > 10" in md
        assert "3 funciones violan reglas obligatorias" in md

    def test_multiple_findings_per_dimension(self) -> None:
        report = QualityReport(
            agent_name="Agent",
            target_path="src/",
            file_count=5,
            date="2026-06-03",
            dimensions=[
                DimensionStatus("Dim", "critical", ["hallazgo A", "hallazgo B", "hallazgo C"]),
            ],
            summary="Resumen.",
        )
        md = render_markdown(report)
        assert "- hallazgo A" in md
        assert "- hallazgo B" in md
        assert "- hallazgo C" in md


class TestRenderMarkdownSummary:
    def test_summary_section_present(self, full_report: QualityReport) -> None:
        md = render_markdown(full_report)
        assert "## Resumen" in md

    def test_summary_text_included(self, full_report: QualityReport) -> None:
        md = render_markdown(full_report)
        assert "Seguridad bajo control. Revisar MISRA y complejidad." in md


class TestRenderMarkdownReproducible:
    def test_same_input_same_output(self, full_report: QualityReport) -> None:
        assert render_markdown(full_report) == render_markdown(full_report)

    def test_ends_with_newline(self, full_report: QualityReport) -> None:
        md = render_markdown(full_report)
        assert md.endswith("\n")
