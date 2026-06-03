from __future__ import annotations

from pathlib import Path

from eqa_framework.codeguard_c.agent import _build_quality_report
from eqa_framework.shared.reporting import Finding, Report, Severity


def _report(*findings: Finding) -> Report:
    r = Report(agent="codeguard-c")
    for f in findings:
        r.add(f)
    return r


def _finding(severity: Severity, tool: str, msg: str = "msg") -> Finding:
    return Finding(severity=severity, rule="R", message=msg, file=Path("f.c"), line=1, tool=tool)


class TestBuildQualityReportNoFindings:
    def test_all_dimensions_ok(self) -> None:
        qr = _build_quality_report(_report(), "src/", 5)
        assert all(d.status == "ok" for d in qr.dimensions)

    def test_summary_sin_observaciones(self) -> None:
        qr = _build_quality_report(_report(), "src/", 5)
        assert "Sin observaciones" in qr.summary

    def test_three_dimensions_present(self) -> None:
        qr = _build_quality_report(_report(), "src/", 5)
        names = [d.name for d in qr.dimensions]
        assert "Complejidad" in names
        assert "Seguridad" in names
        assert "MISRA" in names

    def test_metadata(self) -> None:
        qr = _build_quality_report(_report(), "src/my_project/", 42)
        assert qr.agent_name == "CodeGuard-C"
        assert qr.target_path == "src/my_project/"
        assert qr.file_count == 42


class TestBuildQualityReportComplexity:
    def test_warning_finding_sets_warning_status(self) -> None:
        r = _report(_finding(Severity.WARNING, "lizard", "CC > 10"))
        qr = _build_quality_report(r, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Complejidad")
        assert dim.status == "warning"

    def test_critical_finding_sets_critical_status(self) -> None:
        r = _report(_finding(Severity.CRITICAL, "lizard", "CC > 20"))
        qr = _build_quality_report(r, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Complejidad")
        assert dim.status == "critical"

    def test_finding_text_in_findings(self) -> None:
        r = _report(_finding(Severity.WARNING, "lizard", "function too complex"))
        qr = _build_quality_report(r, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Complejidad")
        assert any("function too complex" in f for f in dim.findings)

    def test_max_5_findings(self) -> None:
        findings = [_finding(Severity.WARNING, "lizard", f"fn{i}") for i in range(10)]
        r = _report(*findings)
        qr = _build_quality_report(r, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Complejidad")
        assert len(dim.findings) <= 5


class TestBuildQualityReportSecurity:
    def test_flawfinder_critical_sets_critical(self) -> None:
        r = _report(_finding(Severity.CRITICAL, "flawfinder", "dangerous call"))
        qr = _build_quality_report(r, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Seguridad")
        assert dim.status == "critical"

    def test_flawfinder_warning_sets_warning(self) -> None:
        r = _report(_finding(Severity.WARNING, "flawfinder", "risky call"))
        qr = _build_quality_report(r, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Seguridad")
        assert dim.status == "warning"

    def test_lizard_finding_does_not_affect_security(self) -> None:
        r = _report(_finding(Severity.CRITICAL, "lizard", "cc high"))
        qr = _build_quality_report(r, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Seguridad")
        assert dim.status == "ok"


class TestBuildQualityReportMisra:
    def test_cppcheck_critical_sets_critical(self) -> None:
        r = _report(_finding(Severity.CRITICAL, "cppcheck", "misra violation"))
        qr = _build_quality_report(r, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "MISRA")
        assert dim.status == "critical"

    def test_cppcheck_warning_sets_warning(self) -> None:
        r = _report(_finding(Severity.WARNING, "cppcheck", "advisory rule"))
        qr = _build_quality_report(r, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "MISRA")
        assert dim.status == "warning"


class TestBuildQualityReportSummary:
    def test_critical_in_summary_when_critical(self) -> None:
        r = _report(_finding(Severity.CRITICAL, "cppcheck"))
        qr = _build_quality_report(r, "src/", 1)
        assert "críticas" in qr.summary.lower() or "crítico" in qr.summary.lower()

    def test_advertencias_in_summary_when_warning_only(self) -> None:
        r = _report(_finding(Severity.WARNING, "lizard"))
        qr = _build_quality_report(r, "src/", 1)
        assert "advertencia" in qr.summary.lower()
