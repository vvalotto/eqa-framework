from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ExecutionContext:
    """Contexto de ejecución pasado a cada Verifiable."""

    project_root: Path
    target_files: list[Path] = field(default_factory=list)
    sprint_id: str = ""


def load_toml_section(project_root: Path, section: str) -> dict[str, Any]:
    """Lee [tool.<section>] desde pyproject.toml o .embedded-qa.toml."""
    raise NotImplementedError
