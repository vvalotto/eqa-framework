from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from eqa_framework.architectanalyst_c.metrics.coupling_analyzer import ModuleMetrics

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS snapshots (
    id          INTEGER PRIMARY KEY,
    sprint_id   TEXT NOT NULL,
    timestamp   TEXT NOT NULL,
    module      TEXT NOT NULL,
    ca          INTEGER,
    ce          INTEGER,
    instability REAL,
    abstractness REAL,
    distance    REAL
)
"""

_INSERT = (
    "INSERT INTO snapshots "
    "(sprint_id, timestamp, module, ca, ce, instability, abstractness, distance) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
)


@dataclass
class Snapshot:
    sprint_id: str
    timestamp: str
    modules: dict[str, ModuleMetrics]


def _row_to_metrics(row: tuple[str, int, int, float, float, float]) -> ModuleMetrics:
    module, ca, ce, instability, abstractness, distance = row
    m = ModuleMetrics(module=module, file=Path(module))
    m.ca = ca or 0
    m.ce = ce or 0
    m.instability = instability or 0.0
    m.abstractness = abstractness or 0.0
    m.distance = distance or 0.0
    return m


class SnapshotStore:
    """Persiste snapshots de métricas arquitectónicas en SQLite entre sprints."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        # In-memory DBs are ephemeral per-connection; keep one alive for the lifetime of the store.
        self._mem_conn: sqlite3.Connection | None = None

    def _connect(self) -> sqlite3.Connection:
        if str(self._db_path) == ":memory:":
            if self._mem_conn is None:
                self._mem_conn = sqlite3.connect(":memory:")
                self._mem_conn.execute(_CREATE_TABLE)
                self._mem_conn.commit()
            return self._mem_conn
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        conn.execute(_CREATE_TABLE)
        conn.commit()
        return conn

    def save(self, snapshot: Snapshot) -> None:
        rows = [
            (
                snapshot.sprint_id,
                snapshot.timestamp,
                name,
                m.ca,
                m.ce,
                m.instability,
                m.abstractness,
                m.distance,
            )
            for name, m in snapshot.modules.items()
        ]
        with self._connect() as conn:
            conn.executemany(_INSERT, rows)

    def load_last(self, sprint_id: str) -> Snapshot | None:
        """Returns the most recent snapshot that is not from sprint_id."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT sprint_id, timestamp FROM snapshots "
                "WHERE sprint_id != ? ORDER BY timestamp DESC LIMIT 1",
                (sprint_id,),
            ).fetchone()
            if not row:
                return None
            prev_sprint_id, prev_timestamp = row
            module_rows = conn.execute(
                "SELECT module, ca, ce, instability, abstractness, distance "
                "FROM snapshots WHERE sprint_id = ? AND timestamp = ?",
                (prev_sprint_id, prev_timestamp),
            ).fetchall()

        modules = {r[0]: _row_to_metrics(r) for r in module_rows}
        return Snapshot(sprint_id=prev_sprint_id, timestamp=prev_timestamp, modules=modules)

    def load_history(self) -> list[Snapshot]:
        with self._connect() as conn:
            runs = conn.execute(
                "SELECT DISTINCT sprint_id, timestamp FROM snapshots ORDER BY timestamp"
            ).fetchall()
            snapshots: list[Snapshot] = []
            for sprint_id, timestamp in runs:
                module_rows = conn.execute(
                    "SELECT module, ca, ce, instability, abstractness, distance "
                    "FROM snapshots WHERE sprint_id = ? AND timestamp = ?",
                    (sprint_id, timestamp),
                ).fetchall()
                modules = {r[0]: _row_to_metrics(r) for r in module_rows}
                snapshots.append(
                    Snapshot(sprint_id=sprint_id, timestamp=timestamp, modules=modules)
                )
        return snapshots
