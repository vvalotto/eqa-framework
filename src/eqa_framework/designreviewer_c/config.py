from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from eqa_framework.shared.config import load_toml_section


@dataclass
class DesignReviewerConfig:
    max_fan_out: int = 12
    max_function_lines: int = 80
    max_parameters: int = 6
    max_nesting_depth: int = 4
    max_cc_critical: int = 15
    exclude_patterns: list[str] = field(
        default_factory=lambda: ["build/", "third_party/", "test/mocks/"]
    )
    layers: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def from_project(cls, project_root: Path) -> DesignReviewerConfig:
        data = load_toml_section(project_root, "designreviewer-c")
        layers_raw: dict[str, list[str]] = {k: list(v) for k, v in data.get("layers", {}).items()}
        return cls(
            max_fan_out=int(data.get("max_fan_out", 12)),
            max_function_lines=int(data.get("max_function_lines", 80)),
            max_parameters=int(data.get("max_parameters", 6)),
            max_nesting_depth=int(data.get("max_nesting_depth", 4)),
            max_cc_critical=int(data.get("max_cc_critical", 15)),
            exclude_patterns=list(
                data.get("exclude_patterns", ["build/", "third_party/", "test/mocks/"])
            ),
            layers=layers_raw,
        )
