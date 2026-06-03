from __future__ import annotations

from pathlib import Path

from eqa_framework.architectanalyst_c.metrics.coupling_analyzer import ModuleMetrics
from eqa_framework.architectanalyst_c.snapshot_store import Snapshot, SnapshotStore


def _store() -> SnapshotStore:
    return SnapshotStore(Path(":memory:"))


def _metrics(module: str, ca: int = 0, ce: int = 0) -> ModuleMetrics:
    m = ModuleMetrics(module=module, file=Path(module))
    m.ca = ca
    m.ce = ce
    total = ca + ce
    m.instability = ce / total if total > 0 else 0.0
    m.abstractness = 0.0
    m.distance = abs(m.abstractness + m.instability - 1.0)
    return m


def _snapshot(sprint_id: str, timestamp: str, **modules: ModuleMetrics) -> Snapshot:
    return Snapshot(sprint_id=sprint_id, timestamp=timestamp, modules=dict(modules))


# ---------------------------------------------------------------------------
# save + load_last
# ---------------------------------------------------------------------------


def test_load_last_empty_store() -> None:
    store = _store()
    assert store.load_last("sprint-01") is None


def test_save_and_load_last(tmp_path: Path) -> None:
    store = _store()
    snap = _snapshot("sprint-01", "2026-01-01T10:00:00", a=_metrics("a", ca=2))
    store.save(snap)

    result = store.load_last("sprint-02")
    assert result is not None
    assert result.sprint_id == "sprint-01"
    assert "a" in result.modules
    assert result.modules["a"].ca == 2


def test_load_last_excludes_current_sprint() -> None:
    store = _store()
    store.save(_snapshot("sprint-01", "2026-01-01T10:00:00", a=_metrics("a")))
    store.save(_snapshot("sprint-02", "2026-01-02T10:00:00", a=_metrics("a")))

    result = store.load_last("sprint-02")
    assert result is not None
    assert result.sprint_id == "sprint-01"


def test_load_last_returns_most_recent_previous() -> None:
    store = _store()
    store.save(_snapshot("sprint-01", "2026-01-01T10:00:00", a=_metrics("a")))
    store.save(_snapshot("sprint-02", "2026-01-02T10:00:00", a=_metrics("a")))
    store.save(_snapshot("sprint-03", "2026-01-03T10:00:00", a=_metrics("a")))

    result = store.load_last("sprint-03")
    assert result is not None
    assert result.sprint_id == "sprint-02"


def test_load_last_no_previous_for_first_sprint() -> None:
    store = _store()
    store.save(_snapshot("sprint-01", "2026-01-01T10:00:00", a=_metrics("a")))
    assert store.load_last("sprint-01") is None


def test_metrics_roundtrip(tmp_path: Path) -> None:
    store = _store()
    m = _metrics("hal_uart", ca=1, ce=1)
    m.abstractness = 0.5
    m.distance = abs(m.abstractness + m.instability - 1.0)  # |0.5+0.5-1| = 0.0
    store.save(_snapshot("sprint-01", "2026-01-01T10:00:00", hal_uart=m))

    result = store.load_last("sprint-02")
    assert result is not None
    r = result.modules["hal_uart"]
    assert r.ca == 1
    assert r.ce == 1
    assert abs(r.instability - 0.5) < 1e-6
    assert abs(r.abstractness - 0.5) < 1e-6
    assert abs(r.distance - 0.0) < 1e-6


# ---------------------------------------------------------------------------
# load_history
# ---------------------------------------------------------------------------


def test_load_history_empty() -> None:
    assert _store().load_history() == []


def test_load_history_multiple_sprints() -> None:
    store = _store()
    store.save(_snapshot("sprint-01", "2026-01-01T10:00:00", a=_metrics("a")))
    store.save(_snapshot("sprint-02", "2026-01-02T10:00:00", a=_metrics("a")))

    history = store.load_history()
    assert len(history) == 2
    assert history[0].sprint_id == "sprint-01"
    assert history[1].sprint_id == "sprint-02"


def test_load_history_preserves_all_modules() -> None:
    store = _store()
    store.save(
        _snapshot(
            "sprint-01",
            "2026-01-01T10:00:00",
            a=_metrics("a", ca=2),
            b=_metrics("b", ce=1),
        )
    )
    history = store.load_history()
    assert len(history) == 1
    assert set(history[0].modules.keys()) == {"a", "b"}


# ---------------------------------------------------------------------------
# Persistence — creates parent directory
# ---------------------------------------------------------------------------


def test_creates_parent_directory(tmp_path: Path) -> None:
    db_path = tmp_path / "subdir" / "nested" / "metrics.db"
    store = SnapshotStore(db_path)
    store.save(_snapshot("sprint-01", "2026-01-01T10:00:00", a=_metrics("a")))
    assert db_path.exists()
