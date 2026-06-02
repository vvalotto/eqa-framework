from __future__ import annotations

from pathlib import Path

import pytest

from eqa_framework.designreviewer_c.analyzers.include_graph_analyzer import (
    IncludeGraphAnalyzer,
    _detect_cycles,
    _is_excluded,
)
from eqa_framework.designreviewer_c.config import DesignReviewerConfig
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Severity

_A = Path("/project/a.h")
_B = Path("/project/b.h")
_C = Path("/project/c.h")


# ---------------------------------------------------------------------------
# _detect_cycles
# ---------------------------------------------------------------------------


class TestDetectCycles:
    def test_simple_cycle_a_b_a(self) -> None:
        graph: dict[Path, list[Path]] = {_A: [_B], _B: [_A]}
        cycles = _detect_cycles(graph)
        assert len(cycles) == 1
        assert set(cycles[0]) == {_A, _B}

    def test_longer_cycle_a_b_c_a(self) -> None:
        graph: dict[Path, list[Path]] = {_A: [_B], _B: [_C], _C: [_A]}
        cycles = _detect_cycles(graph)
        assert len(cycles) == 1
        assert set(cycles[0]) == {_A, _B, _C}

    def test_no_cycle_in_dag(self) -> None:
        graph: dict[Path, list[Path]] = {_A: [_B, _C], _B: [_C], _C: []}
        assert _detect_cycles(graph) == []

    def test_self_loop(self) -> None:
        graph: dict[Path, list[Path]] = {_A: [_A]}
        cycles = _detect_cycles(graph)
        assert len(cycles) == 1
        assert _A in cycles[0]

    def test_empty_graph(self) -> None:
        assert _detect_cycles({}) == []

    def test_duplicate_cycle_reported_once(self) -> None:
        # A→B→A can be detected from both A and B — should appear only once
        graph: dict[Path, list[Path]] = {_A: [_B], _B: [_A]}
        assert len(_detect_cycles(graph)) == 1

    def test_disconnected_graph_no_cycle(self) -> None:
        d = Path("/project/d.h")
        graph: dict[Path, list[Path]] = {_A: [_B], _B: [], _C: [d], d: []}
        assert _detect_cycles(graph) == []


# ---------------------------------------------------------------------------
# _is_excluded
# ---------------------------------------------------------------------------


class TestIsExcluded:
    def test_directory_pattern(self) -> None:
        assert _is_excluded(Path("/project/build/module.h"), ["build/"])

    def test_directory_pattern_no_match(self) -> None:
        assert not _is_excluded(Path("/project/src/module.h"), ["build/"])

    def test_glob_pattern(self) -> None:
        assert _is_excluded(Path("/project/src/mock_uart.h"), ["mock_*.h"])

    def test_no_patterns(self) -> None:
        assert not _is_excluded(Path("/project/src/uart.h"), [])


# ---------------------------------------------------------------------------
# IncludeGraphAnalyzer.run()
# ---------------------------------------------------------------------------


@pytest.fixture()
def default_config() -> DesignReviewerConfig:
    return DesignReviewerConfig(max_fan_out=12)


def _ctx(tmp_path: Path, files: list[Path]) -> ExecutionContext:
    return ExecutionContext(project_root=tmp_path, target_files=files)


class TestIncludeGraphAnalyzerRun:
    def test_clean_project_no_findings(
        self, tmp_path: Path, default_config: DesignReviewerConfig
    ) -> None:
        a = tmp_path / "a.h"
        b = tmp_path / "b.h"
        a.write_text('#include "b.h"\n')
        b.write_text("")
        findings = IncludeGraphAnalyzer(default_config).run(_ctx(tmp_path, [a, b]))
        assert findings == []

    def test_detects_simple_cycle(
        self, tmp_path: Path, default_config: DesignReviewerConfig
    ) -> None:
        a = tmp_path / "a.h"
        b = tmp_path / "b.h"
        a.write_text('#include "b.h"\n')
        b.write_text('#include "a.h"\n')
        findings = IncludeGraphAnalyzer(default_config).run(_ctx(tmp_path, [a, b]))
        cycle_findings = [f for f in findings if f.rule == "INC001"]
        assert len(cycle_findings) == 1
        assert cycle_findings[0].severity == Severity.CRITICAL
        assert "a.h" in cycle_findings[0].message
        assert "b.h" in cycle_findings[0].message

    def test_detects_three_node_cycle(
        self, tmp_path: Path, default_config: DesignReviewerConfig
    ) -> None:
        a = tmp_path / "a.h"
        b = tmp_path / "b.h"
        c = tmp_path / "c.h"
        a.write_text('#include "b.h"\n')
        b.write_text('#include "c.h"\n')
        c.write_text('#include "a.h"\n')
        findings = IncludeGraphAnalyzer(default_config).run(_ctx(tmp_path, [a, b, c]))
        cycle_findings = [f for f in findings if f.rule == "INC001"]
        assert len(cycle_findings) == 1
        assert cycle_findings[0].severity == Severity.CRITICAL

    def test_detects_fan_out_violation(self, tmp_path: Path) -> None:
        config = DesignReviewerConfig(max_fan_out=2)
        heavy = tmp_path / "heavy.c"
        deps = [tmp_path / f"dep{i}.h" for i in range(3)]
        for d in deps:
            d.write_text("")
        heavy.write_text("".join(f'#include "{d.name}"\n' for d in deps))
        findings = IncludeGraphAnalyzer(config).run(_ctx(tmp_path, [heavy, *deps]))
        fanout_findings = [f for f in findings if f.rule == "INC002"]
        assert len(fanout_findings) == 1
        assert fanout_findings[0].severity == Severity.CRITICAL
        assert "heavy.c" in fanout_findings[0].message
        assert "3" in fanout_findings[0].message

    def test_no_fan_out_finding_at_threshold(self, tmp_path: Path) -> None:
        config = DesignReviewerConfig(max_fan_out=2)
        f = tmp_path / "f.c"
        a = tmp_path / "a.h"
        b = tmp_path / "b.h"
        a.write_text("")
        b.write_text("")
        f.write_text('#include "a.h"\n#include "b.h"\n')
        findings = IncludeGraphAnalyzer(config).run(_ctx(tmp_path, [f, a, b]))
        assert not any(fi.rule == "INC002" for fi in findings)

    def test_system_includes_not_counted_for_fan_out(self, tmp_path: Path) -> None:
        config = DesignReviewerConfig(max_fan_out=1)
        f = tmp_path / "f.c"
        local = tmp_path / "local.h"
        local.write_text("")
        # <stdio.h> and <stdint.h> are angle-bracket includes — must not count
        f.write_text('#include <stdio.h>\n#include <stdint.h>\n#include "local.h"\n')
        findings = IncludeGraphAnalyzer(config).run(_ctx(tmp_path, [f, local]))
        assert not any(fi.rule == "INC002" for fi in findings)

    def test_tool_field_is_include_graph(
        self, tmp_path: Path, default_config: DesignReviewerConfig
    ) -> None:
        a = tmp_path / "a.h"
        b = tmp_path / "b.h"
        a.write_text('#include "b.h"\n')
        b.write_text('#include "a.h"\n')
        findings = IncludeGraphAnalyzer(default_config).run(_ctx(tmp_path, [a, b]))
        assert all(f.tool == "include_graph" for f in findings)

    def test_excluded_files_skipped(self, tmp_path: Path) -> None:
        config = DesignReviewerConfig(max_fan_out=12, exclude_patterns=["build/"])
        build = tmp_path / "build"
        build.mkdir()
        a = build / "a.h"
        b = build / "b.h"
        a.write_text('#include "b.h"\n')
        b.write_text('#include "a.h"\n')
        findings = IncludeGraphAnalyzer(config).run(_ctx(tmp_path, [a, b]))
        assert findings == []

    def test_empty_target_files_returns_empty(
        self, tmp_path: Path, default_config: DesignReviewerConfig
    ) -> None:
        ctx = ExecutionContext(project_root=tmp_path, target_files=[])
        assert IncludeGraphAnalyzer(default_config).run(ctx) == []

    def test_unresolvable_include_not_in_cycle_detection(
        self, tmp_path: Path, default_config: DesignReviewerConfig
    ) -> None:
        # a.h includes missing.h which is not in target_files — no false cycle
        a = tmp_path / "a.h"
        a.write_text('#include "missing.h"\n')
        findings = IncludeGraphAnalyzer(default_config).run(_ctx(tmp_path, [a]))
        assert not any(f.rule == "INC001" for f in findings)
