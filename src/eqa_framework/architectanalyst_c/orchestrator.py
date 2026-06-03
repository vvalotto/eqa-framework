from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from eqa_framework.architectanalyst_c.config import ArchitectAnalystConfig
from eqa_framework.architectanalyst_c.metrics.coupling_analyzer import (
    CouplingAnalyzer,
    ModuleMetrics,
)
from eqa_framework.architectanalyst_c.snapshot_store import Snapshot, SnapshotStore
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Report


class ArchitectAnalystOrchestrator:
    """Coordina el análisis arquitectónico completo y persiste el snapshot en SQLite."""

    def __init__(self, config: ArchitectAnalystConfig) -> None:
        self._config = config
        self._analyzer = CouplingAnalyzer(config)
        self._store = SnapshotStore(config.db_path)

    def run(
        self, project_root: Path, target_files: list[Path], sprint_id: str
    ) -> tuple[Report, list[ModuleMetrics], Snapshot | None, float]:
        context = ExecutionContext(
            project_root=project_root, target_files=target_files, sprint_id=sprint_id
        )
        t0 = time.perf_counter()

        previous = self._store.load_last(sprint_id)
        metrics = self._analyzer.compute_metrics(context)

        report = Report(agent="architectanalyst-c")
        for finding in self._analyzer.run(context):
            report.add(finding)

        timestamp = datetime.now(timezone.utc).isoformat()
        snapshot = Snapshot(
            sprint_id=sprint_id,
            timestamp=timestamp,
            modules={m.module: m for m in metrics},
        )
        self._store.save(snapshot)

        elapsed = time.perf_counter() - t0
        return report, metrics, previous, elapsed
