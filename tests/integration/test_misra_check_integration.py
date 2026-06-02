from __future__ import annotations

from pathlib import Path

import pytest

from eqa_framework.codeguard_c.checks.misra_check import MisraCheck
from eqa_framework.codeguard_c.config import CodeGuardConfig
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Severity

pytestmark = pytest.mark.integration

# Violates misra-c2012-11.9 (Mandatory: NULL macro) and produces
# nullPointer + uninitvar from cppcheck's own analysis
_MISRA_C = """\
#include <stdio.h>

int main()
{
    int x;
    int *p = 0;
    printf("%d", x);
    printf("%d", *p);
    return 0;
}
"""

# static linkage avoids misra-c2012-8.4 (external linkage without prior prototype)
_CLEAN_C = """\
static int add(int a, int b)
{
    return a + b;
}
"""


@pytest.fixture()
def misra_file(tmp_path: Path) -> Path:
    f = tmp_path / "defects.c"
    f.write_text(_MISRA_C, encoding="utf-8")
    return f


@pytest.fixture()
def clean_file(tmp_path: Path) -> Path:
    f = tmp_path / "clean.c"
    f.write_text(_CLEAN_C, encoding="utf-8")
    return f


def test_detects_null_pointer_as_error(misra_file: Path) -> None:
    ctx = ExecutionContext(project_root=misra_file.parent, target_files=[misra_file])
    findings = MisraCheck(CodeGuardConfig()).run(ctx)
    errors = [f for f in findings if f.rule == "nullPointer"]
    assert len(errors) == 1
    assert errors[0].severity == Severity.ERROR
    assert errors[0].file == misra_file


def test_detects_uninitvar_as_error(misra_file: Path) -> None:
    ctx = ExecutionContext(project_root=misra_file.parent, target_files=[misra_file])
    findings = MisraCheck(CodeGuardConfig()).run(ctx)
    errors = [f for f in findings if f.rule == "uninitvar"]
    assert len(errors) == 1
    assert errors[0].severity == Severity.ERROR


def test_misra_mandatory_violation_is_critical(misra_file: Path) -> None:
    ctx = ExecutionContext(project_root=misra_file.parent, target_files=[misra_file])
    findings = MisraCheck(CodeGuardConfig()).run(ctx)
    critical = [f for f in findings if f.severity == Severity.CRITICAL]
    assert len(critical) >= 1


def test_clean_file_produces_no_errors(clean_file: Path) -> None:
    ctx = ExecutionContext(project_root=clean_file.parent, target_files=[clean_file])
    findings = MisraCheck(CodeGuardConfig()).run(ctx)
    errors = [f for f in findings if f.severity in (Severity.CRITICAL, Severity.ERROR)]
    assert errors == []


def test_excluded_file_produces_no_findings(misra_file: Path) -> None:
    config = CodeGuardConfig(exclude_patterns=["defects.c"])
    ctx = ExecutionContext(project_root=misra_file.parent, target_files=[misra_file])
    assert MisraCheck(config).run(ctx) == []
