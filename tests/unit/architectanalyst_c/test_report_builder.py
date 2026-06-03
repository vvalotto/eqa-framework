from __future__ import annotations

from pathlib import Path

from eqa_framework.architectanalyst_c.agent import _build_quality_report
from eqa_framework.architectanalyst_c.metrics.coupling_analyzer import ModuleMetrics
from eqa_framework.architectanalyst_c.snapshot_store import Snapshot
from eqa_framework.shared.reporting import Finding, Report, Severity


def _report(*findings: Finding) -> Report:
    r = Report(agent="architectanalyst-c")
    for f in findings:
        r.add(f)
    return r


def _finding(severity: Severity, rule: str, msg: str = "msg") -> Finding:
    return Finding(severity=severity, rule=rule, message=msg, file=Path("m.h"), line=0, tool="t")


def _module(name: str, instability: float = 0.5, distance: float = 0.2) -> ModuleMetrics:
    return ModuleMetrics(
        module=name,
        file=Path(f"{name}.h"),
        ca=1,
        ce=1,
        instability=instability,
        abstractness=0.0,
        distance=distance,
    )


def _snapshot(modules: dict[str, ModuleMetrics]) -> Snapshot:
    return Snapshot(sprint_id="prev", timestamp="2026-01-01", modules=modules)


class TestBuildQualityReportNoFindings:
    def test_all_dimensions_ok(self) -> None:
        qr = _build_quality_report(_report(), [], None, "src/", 5)
        assert all(d.status == "ok" for d in qr.dimensions)

    def test_summary_sin_observaciones(self) -> None:
        qr = _build_quality_report(_report(), [], None, "src/", 5)
        assert "Sin observaciones" in qr.summary

    def test_two_dimensions_present(self) -> None:
        qr = _build_quality_report(_report(), [], None, "src/", 5)
        names = [d.name for d in qr.dimensions]
        assert "Inestabilidad" in names
        assert "Distancia" in names

    def test_metadata(self) -> None:
        qr = _build_quality_report(_report(), [], None, "src/project/", 8)
        assert qr.agent_name == "ArchitectAnalyst-C"
        assert qr.target_path == "src/project/"
        assert qr.file_count == 8


class TestBuildQualityReportInstability:
    def test_arc001_critical_sets_critical(self) -> None:
        r = _report(_finding(Severity.CRITICAL, "ARC001", "instability 0.95 > 0.8"))
        qr = _build_quality_report(r, [], None, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Inestabilidad")
        assert dim.status == "critical"

    def test_arc001_warning_sets_warning(self) -> None:
        r = _report(_finding(Severity.WARNING, "ARC001", "instability near limit"))
        qr = _build_quality_report(r, [], None, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Inestabilidad")
        assert dim.status == "warning"

    def test_arc002_does_not_affect_instability(self) -> None:
        r = _report(_finding(Severity.CRITICAL, "ARC002", "distance warning"))
        qr = _build_quality_report(r, [], None, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Inestabilidad")
        assert dim.status == "ok"


class TestBuildQualityReportDistance:
    def test_arc003_critical_sets_critical(self) -> None:
        r = _report(_finding(Severity.CRITICAL, "ARC003", "zone of pain"))
        qr = _build_quality_report(r, [], None, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Distancia")
        assert dim.status == "critical"

    def test_arc002_warning_sets_warning(self) -> None:
        r = _report(_finding(Severity.WARNING, "ARC002", "distance warning"))
        qr = _build_quality_report(r, [], None, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Distancia")
        assert dim.status == "warning"

    def test_finding_text_included(self) -> None:
        r = _report(_finding(Severity.CRITICAL, "ARC003", "hal_uart in zone of pain"))
        qr = _build_quality_report(r, [], None, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Distancia")
        assert any("hal_uart" in f for f in dim.findings)

    def test_max_5_findings(self) -> None:
        findings = [_finding(Severity.CRITICAL, "ARC003", f"mod{i}") for i in range(10)]
        r = _report(*findings)
        qr = _build_quality_report(r, [], None, "src/", 1)
        dim = next(d for d in qr.dimensions if d.name == "Distancia")
        assert len(dim.findings) <= 5


class TestBuildQualityReportTrend:
    def test_no_trend_note_without_previous(self) -> None:
        metrics = [_module("hal_uart", distance=0.8)]
        qr = _build_quality_report(_report(), metrics, None, "src/", 1)
        assert "↑" not in qr.summary
        assert "empeoró" not in qr.summary

    def test_trend_note_when_distance_worsened(self) -> None:
        metrics = [_module("hal_uart", distance=0.8)]
        prev = _snapshot({"hal_uart": _module("hal_uart", distance=0.3)})
        qr = _build_quality_report(_report(), metrics, prev, "src/", 1)
        assert "empeoró" in qr.summary or "hal_uart" in qr.summary

    def test_no_trend_note_when_distance_stable(self) -> None:
        metrics = [_module("hal_uart", distance=0.3)]
        prev = _snapshot({"hal_uart": _module("hal_uart", distance=0.3)})
        qr = _build_quality_report(_report(), metrics, prev, "src/", 1)
        assert "empeoró" not in qr.summary

    def test_new_modules_noted(self) -> None:
        metrics = [_module("new_module", distance=0.2)]
        prev = _snapshot({"old_module": _module("old_module", distance=0.2)})
        qr = _build_quality_report(_report(), metrics, prev, "src/", 1)
        assert "nuevo" in qr.summary


class TestBuildQualityReportSummary:
    def test_critical_summary(self) -> None:
        r = _report(_finding(Severity.CRITICAL, "ARC003"))
        qr = _build_quality_report(r, [], None, "src/", 1)
        assert "crítica" in qr.summary.lower() or "crítico" in qr.summary.lower()

    def test_warning_summary(self) -> None:
        r = _report(_finding(Severity.WARNING, "ARC001"))
        qr = _build_quality_report(r, [], None, "src/", 1)
        assert "atención" in qr.summary.lower()
