from __future__ import annotations

from pathlib import Path

from eqa_framework.architectanalyst_c.config import ArchitectAnalystConfig
from eqa_framework.architectanalyst_c.metrics.coupling_analyzer import CouplingAnalyzer
from eqa_framework.architectanalyst_c.snapshot_store import SnapshotStore
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Report


class ArchitectAnalystOrchestrator:
    """Coordina el análisis arquitectónico completo y persiste el snapshot en SQLite."""

    def __init__(self, config: ArchitectAnalystConfig) -> None:
        self._config = config
        self._analyzers = [CouplingAnalyzer()]
        self._store = SnapshotStore(config.db_path)

    def run(self, project_root: Path, sprint_id: str) -> Report:
        target_files = list(project_root.rglob("*.[ch]"))
        context = ExecutionContext(
            project_root=project_root,
            target_files=target_files,
            sprint_id=sprint_id,
        )
        report = Report(agent="architectanalyst-c")
        for analyzer in self._analyzers:
            for finding in analyzer.run(context):
                report.add(finding)
        return report
