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

# lizard --csv columns (0-indexed)
_COL_CCN = 1
_COL_LENGTH = 4
_COL_FILE = 6
_COL_FUNC_NAME = 7
_COL_START_LINE = 9


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


def _run_lizard(files: list[Path]) -> str:
    result = subprocess.run(
        ["lizard", "--csv", *[str(f) for f in files]],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout


class ComplexityCheck(Verifiable):
    """Verifica complejidad ciclomática y longitud de funciones via lizard."""

    def __init__(self, config: CodeGuardConfig) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return "complexity"

    @property
    def estimated_seconds(self) -> int:
        return 3

    def run(self, context: ExecutionContext) -> list[Finding]:
        files = [
            f for f in context.target_files if not _is_excluded(f, self._config.exclude_patterns)
        ]
        if not files:
            return []

        output = _run_lizard(files)
        return self._parse(output)

    def _parse(self, lizard_csv: str) -> list[Finding]:
        findings: list[Finding] = []
        reader = csv.reader(StringIO(lizard_csv))
        for row in reader:
            if len(row) < 10:
                continue
            try:
                ccn = int(row[_COL_CCN])
                length = int(row[_COL_LENGTH])
                file_path = Path(row[_COL_FILE])
                func_name = row[_COL_FUNC_NAME]
                start_line = int(row[_COL_START_LINE])
            except (ValueError, IndexError):
                continue

            if ccn > self._config.max_cyclomatic_complexity:
                findings.append(
                    Finding(
                        severity=Severity.WARNING,
                        rule="CCN001",
                        message=(
                            f"{func_name}: cyclomatic complexity {ccn} "
                            f"exceeds limit {self._config.max_cyclomatic_complexity}"
                        ),
                        file=file_path,
                        line=start_line,
                        tool="lizard",
                    )
                )

            if length > self._config.max_function_lines:
                findings.append(
                    Finding(
                        severity=Severity.WARNING,
                        rule="LOC001",
                        message=(
                            f"{func_name}: function length {length} lines "
                            f"exceeds limit {self._config.max_function_lines}"
                        ),
                        file=file_path,
                        line=start_line,
                        tool="lizard",
                    )
                )

        return findings
