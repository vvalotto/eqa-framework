from __future__ import annotations

from pathlib import Path

import pytest

from eqa_framework.architectanalyst_c.config import ArchitectAnalystConfig
from eqa_framework.architectanalyst_c.metrics.coupling_analyzer import (
    CouplingAnalyzer,
    _compute_abstractness,
)
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Severity


def _make_config(
    max_instability: float = 0.8,
    max_distance_warning: float = 0.3,
    max_distance_critical: float = 0.5,
) -> ArchitectAnalystConfig:
    return ArchitectAnalystConfig(
        max_instability=max_instability,
        max_distance_warning=max_distance_warning,
        max_distance_critical=max_distance_critical,
    )


def _context(files: list[Path]) -> ExecutionContext:
    return ExecutionContext(
        project_root=files[0].parent if files else Path("."), target_files=files
    )


# ---------------------------------------------------------------------------
# _compute_abstractness
# ---------------------------------------------------------------------------


def test_abstractness_opaque_ptr(tmp_path: Path) -> None:
    h = tmp_path / "driver.h"
    h.write_text("typedef struct Driver * Driver_t;\n")
    assert _compute_abstractness(h) == pytest.approx(1.0)


def test_abstractness_forward_decl(tmp_path: Path) -> None:
    h = tmp_path / "handle.h"
    h.write_text("struct Handle;\ntypedef struct Handle * Handle_t;\n")
    # 2 abstract (1 forward + 1 opaque ptr), 2 total (1 typedef + 1 forward)
    # Wait: typedef counts, forward decl via _FORWARD_DECL_RE
    # total = typedef(1) + struct body(0) + enum body(0) = 1
    # abstract = opaque_ptr(1) + forward(1) = 2 → capped at 1.0
    assert _compute_abstractness(h) == pytest.approx(1.0)


def test_abstractness_concrete_struct(tmp_path: Path) -> None:
    h = tmp_path / "data.h"
    h.write_text("typedef struct { int x; int y; } Point_t;\n")
    # total = typedef(1) + struct_body(1) = 2, abstract = 0 → A = 0.0
    assert _compute_abstractness(h) == pytest.approx(0.0)


def test_abstractness_empty_header(tmp_path: Path) -> None:
    h = tmp_path / "empty.h"
    h.write_text("#ifndef EMPTY_H\n#define EMPTY_H\n#endif\n")
    assert _compute_abstractness(h) == pytest.approx(0.0)


def test_abstractness_missing_file(tmp_path: Path) -> None:
    assert _compute_abstractness(tmp_path / "nonexistent.h") == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# CouplingAnalyzer.compute_metrics — fixed dependency graphs
# ---------------------------------------------------------------------------


def test_single_module_no_deps(tmp_path: Path) -> None:
    h = tmp_path / "standalone.h"
    h.write_text("#ifndef S_H\n#define S_H\nvoid foo(void);\n#endif\n")
    analyzer = CouplingAnalyzer(_make_config())
    metrics = analyzer.compute_metrics(_context([h]))
    assert len(metrics) == 1
    m = metrics[0]
    assert m.module == "standalone"
    assert m.ca == 0
    assert m.ce == 0
    assert m.instability == pytest.approx(0.0)
    assert m.distance == pytest.approx(1.0)  # A=0, I=0 → Zone of Pain


def test_two_module_linear_dep(tmp_path: Path) -> None:
    """
    a.h  ←  b.c   (b depends on a)
    """
    a_h = tmp_path / "a.h"
    a_h.write_text("void a(void);\n")
    b_c = tmp_path / "b.c"
    b_c.write_text('#include "a.h"\nvoid b(void) {}\n')

    analyzer = CouplingAnalyzer(_make_config())
    metrics = {m.module: m for m in analyzer.compute_metrics(_context([a_h, b_c]))}

    assert metrics["a"].ca == 1
    assert metrics["a"].ce == 0
    assert metrics["a"].instability == pytest.approx(0.0)

    assert metrics["b"].ca == 0
    assert metrics["b"].ce == 1
    assert metrics["b"].instability == pytest.approx(1.0)


def test_ca_ce_triangle(tmp_path: Path) -> None:
    """
    a ← b, a ← c, b ← c  (c depends on both a and b; b depends on a)
    """
    a_h = tmp_path / "a.h"
    a_h.write_text("void a(void);\n")
    b_h = tmp_path / "b.h"
    b_h.write_text('#include "a.h"\nvoid b(void);\n')
    c_c = tmp_path / "c.c"
    c_c.write_text('#include "a.h"\n#include "b.h"\nvoid c(void) {}\n')

    analyzer = CouplingAnalyzer(_make_config())
    metrics = {m.module: m for m in analyzer.compute_metrics(_context([a_h, b_h, c_c]))}

    assert metrics["a"].ca == 2  # b and c
    assert metrics["a"].ce == 0
    assert metrics["b"].ca == 1  # c
    assert metrics["b"].ce == 1  # a
    assert metrics["b"].instability == pytest.approx(0.5)
    assert metrics["c"].ca == 0
    assert metrics["c"].ce == 2  # a and b
    assert metrics["c"].instability == pytest.approx(1.0)


def test_self_include_ignored(tmp_path: Path) -> None:
    """Including a file with the same stem should not count as a dependency."""
    h = tmp_path / "mod.h"
    h.write_text("void mod(void);\n")
    c = tmp_path / "mod.c"
    c.write_text('#include "mod.h"\nvoid mod(void) {}\n')

    analyzer = CouplingAnalyzer(_make_config())
    metrics = analyzer.compute_metrics(_context([h, c]))
    assert len(metrics) == 1
    m = metrics[0]
    assert m.ca == 0
    assert m.ce == 0


def test_instability_and_distance_formulas(tmp_path: Path) -> None:
    a_h = tmp_path / "a.h"
    a_h.write_text("void a(void);\n")
    b_c = tmp_path / "b.c"
    b_c.write_text('#include "a.h"\nvoid b(void) {}\n')
    c_c = tmp_path / "c.c"
    c_c.write_text('#include "a.h"\nvoid c(void) {}\n')

    analyzer = CouplingAnalyzer(_make_config())
    metrics = {m.module: m for m in analyzer.compute_metrics(_context([a_h, b_c, c_c]))}

    # a: Ca=2, Ce=0 → I=0, A=0 → D=1.0
    assert metrics["a"].instability == pytest.approx(0.0)
    assert metrics["a"].distance == pytest.approx(1.0)
    # b: Ca=0, Ce=1 → I=1, A=0 → D=0.0
    assert metrics["b"].instability == pytest.approx(1.0)
    assert metrics["b"].distance == pytest.approx(0.0)


def test_excluded_files_ignored(tmp_path: Path) -> None:
    build = tmp_path / "build"
    build.mkdir()
    a_h = tmp_path / "a.h"
    a_h.write_text("void a(void);\n")
    b_c = build / "b.c"
    b_c.write_text('#include "../a.h"\nvoid b(void) {}\n')

    config = _make_config()
    config.exclude_patterns = ["build/"]
    analyzer = CouplingAnalyzer(config)
    metrics = analyzer.compute_metrics(_context([a_h, b_c]))

    # b.c is excluded; only a.h remains
    assert len(metrics) == 1
    assert metrics[0].module == "a"


# ---------------------------------------------------------------------------
# CouplingAnalyzer.run — findings generation
# ---------------------------------------------------------------------------


def test_finding_high_instability(tmp_path: Path) -> None:
    a_h = tmp_path / "a.h"
    a_h.write_text("void a(void);\n")
    b_c = tmp_path / "b.c"
    b_c.write_text('#include "a.h"\nvoid b(void) {}\n')

    config = _make_config(max_instability=0.5)
    findings = CouplingAnalyzer(config).run(_context([a_h, b_c]))

    instability_findings = [f for f in findings if f.rule == "ARC001"]
    assert len(instability_findings) == 1
    assert instability_findings[0].severity == Severity.WARNING
    assert "b" in instability_findings[0].message


def test_finding_distance_critical(tmp_path: Path) -> None:
    # standalone module: Ca=0, Ce=0, I=0, A=0 → D=1.0 > 0.5
    h = tmp_path / "lone.h"
    h.write_text("void lone(void);\n")

    findings = CouplingAnalyzer(_make_config()).run(_context([h]))

    dist_findings = [f for f in findings if f.rule == "ARC003"]
    assert len(dist_findings) == 1
    assert dist_findings[0].severity == Severity.CRITICAL


def test_finding_distance_warning(tmp_path: Path) -> None:
    """
    b has Ce=1, Ca=1 → I=0.5, A=0 → D=0.5 (== critical threshold, not > 0.5).
    With max_distance_warning=0.3 and max_distance_critical=0.6, should be WARNING.
    """
    a_h = tmp_path / "a.h"
    a_h.write_text("void a(void);\n")
    b_h = tmp_path / "b.h"
    b_h.write_text('#include "a.h"\nvoid b(void);\n')
    c_c = tmp_path / "c.c"
    c_c.write_text('#include "b.h"\nvoid c(void) {}\n')

    config = _make_config(max_distance_warning=0.3, max_distance_critical=0.6)
    findings = CouplingAnalyzer(config).run(_context([a_h, b_h, c_c]))

    b_dist = [f for f in findings if f.rule == "ARC002" and "b" in f.message]
    assert len(b_dist) == 1
    assert b_dist[0].severity == Severity.WARNING


def test_no_findings_for_ideal_module(tmp_path: Path) -> None:
    """
    A module that only depends on others (I=1.0, D=0.0) should not trigger
    distance findings, though it may trigger instability if above threshold.
    """
    a_h = tmp_path / "a.h"
    a_h.write_text("void a(void);\n")
    b_c = tmp_path / "b.c"
    b_c.write_text('#include "a.h"\nvoid b(void) {}\n')

    # b: I=1.0, A=0, D=0.0 → no distance finding
    findings = CouplingAnalyzer(_make_config()).run(_context([a_h, b_c]))
    dist_b = [f for f in findings if "b" in f.message and f.rule in ("ARC002", "ARC003")]
    assert len(dist_b) == 0
