from __future__ import annotations

import sys
import time
from pathlib import Path

from eqa_framework.codeguard_c.checks.complexity_check import ComplexityCheck
from eqa_framework.codeguard_c.checks.misra_check import MisraCheck
from eqa_framework.codeguard_c.checks.security_check import SecurityCheck
from eqa_framework.codeguard_c.config import CodeGuardConfig
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Report

BUDGET_SECONDS: int = 15

_CHECK_LABEL: dict[str, str] = {
    "misra": "cppcheck (MISRA-C)",
    "security": "flawfinder (seguridad)",
    "complexity": "lizard (complejidad)",
}


class CodeGuardOrchestrator:
    """Coordina los checks de CodeGuard-C respetando el presupuesto de 15 s."""

    def __init__(self, config: CodeGuardConfig) -> None:
        self._config = config
        self._checks = [MisraCheck(config), SecurityCheck(config), ComplexityCheck(config)]

    def run(
        self, project_root: Path, target_files: list[Path], progress: bool = True
    ) -> tuple[Report, float]:
        context = ExecutionContext(project_root=project_root, target_files=target_files)
        report = Report(agent="codeguard-c")
        t0 = time.perf_counter()
        for check in self._checks:
            if progress:
                label = _CHECK_LABEL.get(check.name, check.name)
                print(f"→ {label}...", file=sys.stderr)
            for finding in check.run(context):
                report.add(finding)
        elapsed = time.perf_counter() - t0
        return report, elapsed
