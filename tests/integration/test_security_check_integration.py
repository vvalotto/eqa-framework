from __future__ import annotations

from pathlib import Path

import pytest

from eqa_framework.codeguard_c.checks.security_check import SecurityCheck
from eqa_framework.codeguard_c.config import CodeGuardConfig
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Severity

pytestmark = pytest.mark.integration

_INSECURE_C = """\
#include <stdio.h>
#include <string.h>

void insecure_func(char *input) {
    char buf[64];
    gets(buf);
    strcpy(buf, input);
    sprintf(buf, input);
}
"""

_SAFE_C = """\
#include <stdio.h>
#include <string.h>

void safe_func(const char *input, size_t len) {
    char buf[64];
    snprintf(buf, sizeof(buf), "%s", input);
}
"""


@pytest.fixture()
def insecure_file(tmp_path: Path) -> Path:
    f = tmp_path / "insecure.c"
    f.write_text(_INSECURE_C, encoding="utf-8")
    return f


@pytest.fixture()
def safe_file(tmp_path: Path) -> Path:
    f = tmp_path / "safe.c"
    f.write_text(_SAFE_C, encoding="utf-8")
    return f


def test_detects_gets_as_error(insecure_file: Path) -> None:
    ctx = ExecutionContext(project_root=insecure_file.parent, target_files=[insecure_file])
    findings = SecurityCheck(CodeGuardConfig()).run(ctx)
    gets_findings = [f for f in findings if "gets" in f.message]
    assert len(gets_findings) == 1
    assert gets_findings[0].severity == Severity.ERROR
    assert gets_findings[0].file == insecure_file


def test_detects_strcpy_as_error(insecure_file: Path) -> None:
    ctx = ExecutionContext(project_root=insecure_file.parent, target_files=[insecure_file])
    findings = SecurityCheck(CodeGuardConfig()).run(ctx)
    strcpy_findings = [f for f in findings if "strcpy" in f.message]
    assert len(strcpy_findings) == 1
    assert strcpy_findings[0].severity == Severity.ERROR


def test_detects_sprintf_as_error(insecure_file: Path) -> None:
    ctx = ExecutionContext(project_root=insecure_file.parent, target_files=[insecure_file])
    findings = SecurityCheck(CodeGuardConfig()).run(ctx)
    sprintf_findings = [f for f in findings if "sprintf" in f.message]
    assert len(sprintf_findings) == 1
    assert sprintf_findings[0].severity == Severity.ERROR


def test_safe_code_produces_no_errors(safe_file: Path) -> None:
    ctx = ExecutionContext(project_root=safe_file.parent, target_files=[safe_file])
    findings = SecurityCheck(CodeGuardConfig()).run(ctx)
    errors = [f for f in findings if f.severity == Severity.ERROR]
    assert errors == []


def test_excluded_file_produces_no_findings(insecure_file: Path) -> None:
    config = CodeGuardConfig(exclude_patterns=["insecure.c"])
    ctx = ExecutionContext(project_root=insecure_file.parent, target_files=[insecure_file])
    findings = SecurityCheck(config).run(ctx)
    assert findings == []
