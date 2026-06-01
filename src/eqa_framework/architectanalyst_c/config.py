from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from eqa_framework.shared.config import load_toml_section


@dataclass
class ArchitectAnalystConfig:
    max_instability: float = 0.8
    max_distance_warning: float = 0.3
    max_distance_critical: float = 0.5
    db_path: Path = Path(".quality_control/embedded_architecture.db")
    exclude_patterns: list[str] = field(default_factory=lambda: ["build/", "third_party/"])
    layers: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def from_project(cls, project_root: Path) -> ArchitectAnalystConfig:
        data = load_toml_section(project_root, "architectanalyst-c")
        return cls(
            max_instability=float(data.get("max_instability", 0.8)),
            max_distance_warning=float(data.get("max_distance_warning", 0.3)),
            max_distance_critical=float(data.get("max_distance_critical", 0.5)),
            db_path=Path(str(data.get("db_path", ".quality_control/embedded_architecture.db"))),
            exclude_patterns=list(data.get("exclude_patterns", ["build/", "third_party/"])),
            layers=dict(data.get("layers", {})),
        )
