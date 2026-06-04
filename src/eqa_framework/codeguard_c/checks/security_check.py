from __future__ import annotations

import csv
import fnmatch
import subprocess
from io import StringIO
from pathlib import Path

from eqa_framework.codeguard_c.config import CodeGuardConfig
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Finding, Severity
from eqa_framework.shared.verifiable import Verifiable

_MIN_WARNING_LEVEL = 2
_MIN_ERROR_LEVEL = 4


def _is_excluded(path: Path, patterns: list[str]) -> bool:
    name = path.name
    parts = path.parts
    for pattern in patterns:
        stripped = pattern.rstrip("/")
        if pattern.endswith("/"):
            if stripped in parts:
                return True
        elif fnmatch.fnmatch(name, pattern):
            return True
    return False


def _run_flawfinder(files: list[Path]) -> str:
    result = subprocess.run(
        ["flawfinder", "--dataonly", "--csv", *[str(f) for f in files]],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout


def _level_to_severity(level: int) -> Severity | None:
    if level >= _MIN_ERROR_LEVEL:
        return Severity.ERROR
    if level >= _MIN_WARNING_LEVEL:
        return Severity.WARNING
    return None


class SecurityCheck(Verifiable):
    """Detecta funciones C inseguras (gets, strcpy, sprintf) via flawfinder."""

    def __init__(self, config: CodeGuardConfig) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return "security"

    @property
    def estimated_seconds(self) -> int:
        return 3

    def run(self, context: ExecutionContext) -> list[Finding]:
        files = [
            f for f in context.target_files if not _is_excluded(f, self._config.exclude_patterns)
        ]
        if not files:
            return []

        output = _run_flawfinder(files)
        return self._parse(output)

    def _parse(self, flawfinder_csv: str) -> list[Finding]:
        findings: list[Finding] = []
        reader = csv.DictReader(StringIO(flawfinder_csv))
        for row in reader:
            try:
                if not row.get("Level"):
                    continue
                level = int(row["Level"])
                severity = _level_to_severity(level)
                if severity is None:
                    continue
                findings.append(
                    Finding(
                        severity=severity,
                        rule=row["RuleId"],
                        message=f"{row['Name']}: {row['Warning']}",
                        file=Path(row["File"]),
                        line=int(row["Line"]),
                        tool="flawfinder",
                    )
                )
            except (KeyError, ValueError):
                continue

        return findings
