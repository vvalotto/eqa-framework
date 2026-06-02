from __future__ import annotations

from pathlib import Path

from eqa_framework.codeguard_c.checks.complexity_check import ComplexityCheck
from eqa_framework.codeguard_c.checks.misra_check import MisraCheck
from eqa_framework.codeguard_c.checks.security_check import SecurityCheck
from eqa_framework.codeguard_c.config import CodeGuardConfig
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Report


class CodeGuardOrchestrator:
    """Coordina los checks de CodeGuard-C respetando el presupuesto de 15 s."""

    def __init__(self, config: CodeGuardConfig) -> None:
        self._config = config
        self._checks = [MisraCheck(), SecurityCheck(), ComplexityCheck(config)]

    def run(self, project_root: Path, target_files: list[Path]) -> Report:
        context = ExecutionContext(project_root=project_root, target_files=target_files)
        report = Report(agent="codeguard-c")
        for check in self._checks:
            for finding in check.run(context):
                report.add(finding)
        return report
