from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from eqa_framework.codeguard_c.checks.complexity_check import ComplexityCheck, _is_excluded
from eqa_framework.codeguard_c.config import CodeGuardConfig
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Severity

# Real lizard --csv output for two functions:
#   simple_func: CCN=1, length=3
#   complex_func: CCN=7, length=17
_LIZARD_CSV = """\
3,1,12,1,3,"simple_func@1-3@/src/module.c","/src/module.c","simple_func","simple_func( int x)",1,3
17,7,97,3,17,"complex_func@5-21@/src/module.c","/src/module.c","complex_func","complex_func( int a , int b , int c)",5,21
"""

_DEFAULT_CONFIG = CodeGuardConfig()  # max_cc=10, max_loc=50


@pytest.fixture()
def ctx(tmp_path: Path) -> ExecutionContext:
    f = tmp_path / "module.c"
    f.touch()
    return ExecutionContext(project_root=tmp_path, target_files=[f])


class TestComplexityCheckParse:
    def _check(self, config: CodeGuardConfig = _DEFAULT_CONFIG) -> ComplexityCheck:
        return ComplexityCheck(config)

    def test_no_findings_within_limits(self, ctx: ExecutionContext) -> None:
        with patch(
            "eqa_framework.codeguard_c.checks.complexity_check._run_lizard",
            return_value=_LIZARD_CSV,
        ):
            findings = self._check().run(ctx)
        assert findings == []

    def test_cc_finding_when_threshold_exceeded(self, ctx: ExecutionContext) -> None:
        config = CodeGuardConfig(max_cyclomatic_complexity=5)
        with patch(
            "eqa_framework.codeguard_c.checks.complexity_check._run_lizard",
            return_value=_LIZARD_CSV,
        ):
            findings = self._check(config).run(ctx)
        cc_findings = [f for f in findings if f.rule == "CCN001"]
        assert len(cc_findings) == 1
        assert cc_findings[0].severity == Severity.WARNING
        assert "complex_func" in cc_findings[0].message
        assert "7" in cc_findings[0].message
        assert cc_findings[0].line == 5

    def test_loc_finding_when_threshold_exceeded(self, ctx: ExecutionContext) -> None:
        config = CodeGuardConfig(max_function_lines=10)
        with patch(
            "eqa_framework.codeguard_c.checks.complexity_check._run_lizard",
            return_value=_LIZARD_CSV,
        ):
            findings = self._check(config).run(ctx)
        loc_findings = [f for f in findings if f.rule == "LOC001"]
        assert len(loc_findings) == 1
        assert "complex_func" in loc_findings[0].message
        assert "17" in loc_findings[0].message

    def test_both_findings_on_same_function(self, ctx: ExecutionContext) -> None:
        config = CodeGuardConfig(max_cyclomatic_complexity=5, max_function_lines=10)
        with patch(
            "eqa_framework.codeguard_c.checks.complexity_check._run_lizard",
            return_value=_LIZARD_CSV,
        ):
            findings = self._check(config).run(ctx)
        assert len(findings) == 2
        assert {f.rule for f in findings} == {"CCN001", "LOC001"}

    def test_all_functions_flagged_when_low_thresholds(self, ctx: ExecutionContext) -> None:
        config = CodeGuardConfig(max_cyclomatic_complexity=0, max_function_lines=0)
        with patch(
            "eqa_framework.codeguard_c.checks.complexity_check._run_lizard",
            return_value=_LIZARD_CSV,
        ):
            findings = self._check(config).run(ctx)
        assert len(findings) == 4  # 2 funcs × 2 rules

    def test_empty_output_returns_no_findings(self, ctx: ExecutionContext) -> None:
        with patch(
            "eqa_framework.codeguard_c.checks.complexity_check._run_lizard",
            return_value="",
        ):
            findings = self._check().run(ctx)
        assert findings == []

    def test_tool_field_is_lizard(self, ctx: ExecutionContext) -> None:
        config = CodeGuardConfig(max_cyclomatic_complexity=5)
        with patch(
            "eqa_framework.codeguard_c.checks.complexity_check._run_lizard",
            return_value=_LIZARD_CSV,
        ):
            findings = self._check(config).run(ctx)
        assert all(f.tool == "lizard" for f in findings)


class TestExcludePatterns:
    def test_directory_pattern_excludes_file_in_that_dir(self) -> None:
        assert _is_excluded(Path("/project/build/module.c"), ["build/"])

    def test_directory_pattern_does_not_exclude_unrelated(self) -> None:
        assert not _is_excluded(Path("/project/src/module.c"), ["build/"])

    def test_glob_pattern_excludes_matching_file(self) -> None:
        assert _is_excluded(Path("/project/src/proto.pb.c"), ["*.pb.c"])

    def test_glob_pattern_does_not_exclude_non_matching(self) -> None:
        assert not _is_excluded(Path("/project/src/module.c"), ["*.pb.c"])

    def test_multiple_patterns(self) -> None:
        assert _is_excluded(Path("/project/third_party/lib.c"), ["build/", "third_party/"])

    def test_no_patterns_excludes_nothing(self) -> None:
        assert not _is_excluded(Path("/project/src/module.c"), [])


class TestExcludePatternsIntegration:
    def test_excluded_files_not_passed_to_lizard(self, tmp_path: Path) -> None:
        keep = tmp_path / "src" / "module.c"
        keep.parent.mkdir()
        keep.touch()
        exclude = tmp_path / "build" / "generated.c"
        exclude.parent.mkdir()
        exclude.touch()

        ctx = ExecutionContext(
            project_root=tmp_path,
            target_files=[keep, exclude],
        )
        config = CodeGuardConfig(exclude_patterns=["build/"])

        with patch(
            "eqa_framework.codeguard_c.checks.complexity_check._run_lizard",
            return_value="",
        ) as mock_lizard:
            ComplexityCheck(config).run(ctx)

        called_files = mock_lizard.call_args[0][0]
        assert keep in called_files
        assert exclude not in called_files

    def test_all_files_excluded_skips_lizard(self, tmp_path: Path) -> None:
        f = tmp_path / "build" / "gen.c"
        f.parent.mkdir()
        f.touch()
        ctx = ExecutionContext(project_root=tmp_path, target_files=[f])
        config = CodeGuardConfig(exclude_patterns=["build/"])

        with patch("eqa_framework.codeguard_c.checks.complexity_check._run_lizard") as mock_lizard:
            findings = ComplexityCheck(config).run(ctx)

        mock_lizard.assert_not_called()
        assert findings == []
