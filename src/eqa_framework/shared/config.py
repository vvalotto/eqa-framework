from __future__ import annotations

import tomllib
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
    for filename in ("pyproject.toml", ".embedded-qa.toml"):
        config_file = project_root / filename
        if not config_file.exists():
            continue
        data = tomllib.loads(config_file.read_text(encoding="utf-8"))
        tool: dict[str, Any] = data.get("tool", {})
        section_data: dict[str, Any] = tool.get(section, {})
        return section_data
    return {}
