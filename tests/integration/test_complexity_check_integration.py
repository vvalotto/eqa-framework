from __future__ import annotations

from pathlib import Path

import pytest

from eqa_framework.codeguard_c.checks.complexity_check import ComplexityCheck
from eqa_framework.codeguard_c.config import CodeGuardConfig
from eqa_framework.shared.config import ExecutionContext

pytestmark = pytest.mark.integration

# A function with CCN=7 and 17 physical lines (verified against lizard output)
_COMPLEX_C = """\
int complex_func(int a, int b, int c) {
    if (a > 0) {
        if (b > 0) {
            if (c > 0) { return 1; }
            else if (c < -5) { return 2; }
            else { return 3; }
        } else if (b < -10) {
            return 4;
        } else {
            return 5;
        }
    } else if (a < -10) {
        return 6;
    } else {
        return 7;
    }
}
"""

_SIMPLE_C = """\
int add(int a, int b) {
    return a + b;
}
"""


@pytest.fixture()
def c_file(tmp_path: Path) -> Path:
    f = tmp_path / "module.c"
    f.write_text(_COMPLEX_C, encoding="utf-8")
    return f


@pytest.fixture()
def simple_c_file(tmp_path: Path) -> Path:
    f = tmp_path / "simple.c"
    f.write_text(_SIMPLE_C, encoding="utf-8")
    return f


def test_detects_high_cc(c_file: Path) -> None:
    config = CodeGuardConfig(max_cyclomatic_complexity=5)
    ctx = ExecutionContext(project_root=c_file.parent, target_files=[c_file])
    findings = ComplexityCheck(config).run(ctx)
    cc = [f for f in findings if f.rule == "CCN001"]
    assert len(cc) == 1
    assert "complex_func" in cc[0].message
    assert cc[0].file == c_file


def test_detects_long_function(c_file: Path) -> None:
    config = CodeGuardConfig(max_function_lines=10)
    ctx = ExecutionContext(project_root=c_file.parent, target_files=[c_file])
    findings = ComplexityCheck(config).run(ctx)
    loc = [f for f in findings if f.rule == "LOC001"]
    assert len(loc) == 1
    assert "complex_func" in loc[0].message


def test_no_findings_for_simple_function(simple_c_file: Path) -> None:
    config = CodeGuardConfig(max_cyclomatic_complexity=10, max_function_lines=50)
    ctx = ExecutionContext(project_root=simple_c_file.parent, target_files=[simple_c_file])
    findings = ComplexityCheck(config).run(ctx)
    assert findings == []


def test_excluded_file_produces_no_findings(c_file: Path) -> None:
    config = CodeGuardConfig(max_cyclomatic_complexity=5, exclude_patterns=["module.c"])
    ctx = ExecutionContext(project_root=c_file.parent, target_files=[c_file])
    findings = ComplexityCheck(config).run(ctx)
    assert findings == []
