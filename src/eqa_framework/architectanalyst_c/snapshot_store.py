from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Snapshot:
    sprint_id: str
    timestamp: str
    metrics: dict[str, float]


class SnapshotStore:
    """Persiste snapshots de métricas arquitectónicas en SQLite entre sprints."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def save(self, snapshot: Snapshot) -> None:
        raise NotImplementedError

    def load_last(self, sprint_id: str) -> Snapshot | None:
        raise NotImplementedError

    def load_history(self) -> list[Snapshot]:
        raise NotImplementedError
