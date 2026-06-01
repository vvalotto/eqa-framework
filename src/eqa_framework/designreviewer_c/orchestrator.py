from __future__ import annotations

from pathlib import Path

from eqa_framework.designreviewer_c.analyzers.include_graph_analyzer import IncludeGraphAnalyzer
from eqa_framework.designreviewer_c.analyzers.layer_violations_analyzer import (
    LayerViolationsAnalyzer,
)
from eqa_framework.designreviewer_c.config import DesignReviewerConfig
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Report


class DesignReviewerOrchestrator:
    """Coordina los analyzers de DesignReviewer-C. Retorna exit code 1 si hay CRITICAL."""

    def __init__(self, config: DesignReviewerConfig) -> None:
        self._config = config
        self._analyzers = [IncludeGraphAnalyzer(), LayerViolationsAnalyzer()]

    def run(self, project_root: Path, target_files: list[Path]) -> Report:
        context = ExecutionContext(project_root=project_root, target_files=target_files)
        report = Report(agent="designreviewer-c")
        for analyzer in self._analyzers:
            for finding in analyzer.run(context):
                report.add(finding)
        return report

    def exit_code(self, report: Report) -> int:
        return 1 if report.has_critical() else 0
