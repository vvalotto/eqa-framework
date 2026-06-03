from __future__ import annotations

from pathlib import Path

from eqa_framework.designreviewer_c.agent import _build_quality_report
from eqa_framework.shared.reporting import Finding, Report, Severity


def _report(*findings: Finding) -> Report:
    r = Report(agent="designreviewer-c")
    for f in findings:
        r.add(f)
    return r


def _finding(severity: Severity, rule: str, msg: str = "msg") -> Finding:
    return Finding(severity=severity, rule=rule, message=msg, file=Path("f.h"), line=1, tool="t")


class TestBuildQualityReportNoFindings:
    def test_all_dimensions_ok(self) -> None:
        qr = _build_quality_report(_report(), "src/", 5)
        assert all(d.status == "ok" for d in qr.dimensions)

    def test_summary_sin_observaciones(self) -> None:
        qr = _build_quality_report(_report(), "src/", 5)
        assert "Sin observaciones" in qr.summary

    def test_two_dimensions_present(self) -> None:
        qr = _build_quality_report(_report(), "src/", 5)
        names = [d.name for d in qr.dimensions]
        assert "Dependencias" in names
        assert "Capas" in names

    def test_metadata(self) -> None:
        qr = _build_quality_report(_report(), "src/my_project/", 10)
        assert qr.agent_name == "DesignReviewer-C"
        assert qr.target_path == "src/my_project/"
        assert qr.file_count == 10


class TestBuildQualityReportDependencies:
    def test_inc001_critical_sets_critical(self) -> None:
        r = _report(_finding(Severity.CRITICAL, "INC001", "circular include"))
        qr = _build_quality_report(r, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Dependencias")
        assert dim.status == "critical"

    def test_inc002_warning_sets_warning(self) -> None:
        r = _report(_finding(Severity.WARNING, "INC002", "fan-out exceeded"))
        qr = _build_quality_report(r, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Dependencias")
        assert dim.status == "warning"

    def test_lay001_does_not_affect_dependencies(self) -> None:
        r = _report(_finding(Severity.CRITICAL, "LAY001", "layer violation"))
        qr = _build_quality_report(r, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Dependencias")
        assert dim.status == "ok"

    def test_finding_text_included(self) -> None:
        r = _report(_finding(Severity.CRITICAL, "INC001", "hal → app cycle"))
        qr = _build_quality_report(r, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Dependencias")
        assert any("hal → app cycle" in f for f in dim.findings)

    def test_max_5_findings(self) -> None:
        findings = [_finding(Severity.WARNING, "INC002", f"module{i}") for i in range(10)]
        r = _report(*findings)
        qr = _build_quality_report(r, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Dependencias")
        assert len(dim.findings) <= 5


class TestBuildQualityReportLayers:
    def test_lay001_critical_sets_critical(self) -> None:
        r = _report(_finding(Severity.CRITICAL, "LAY001", "HAL depends on APP"))
        qr = _build_quality_report(r, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Capas")
        assert dim.status == "critical"

    def test_lay001_warning_sets_warning(self) -> None:
        r = _report(_finding(Severity.WARNING, "LAY001", "borderline violation"))
        qr = _build_quality_report(r, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Capas")
        assert dim.status == "warning"

    def test_inc001_does_not_affect_layers(self) -> None:
        r = _report(_finding(Severity.CRITICAL, "INC001", "cycle"))
        qr = _build_quality_report(r, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Capas")
        assert dim.status == "ok"


class TestBuildQualityReportSummary:
    def test_critical_summary(self) -> None:
        r = _report(_finding(Severity.CRITICAL, "LAY001"))
        qr = _build_quality_report(r, "src/", 1)
        assert "críticas" in qr.summary.lower() or "crítico" in qr.summary.lower()

    def test_warning_summary(self) -> None:
        r = _report(_finding(Severity.WARNING, "INC002"))
        qr = _build_quality_report(r, "src/", 1)
        assert "advertencia" in qr.summary.lower()
