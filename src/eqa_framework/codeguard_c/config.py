from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from eqa_framework.shared.config import load_toml_section


@dataclass
class CodeGuardConfig:
    max_cyclomatic_complexity: int = 10
    max_function_lines: int = 50
    exclude_patterns: list[str] = field(
        default_factory=lambda: ["build/", "third_party/", "*.pb.c"]
    )
    misra_mandatory: bool = True
    misra_required: bool = True
    misra_advisory: bool = False

    @classmethod
    def from_project(cls, project_root: Path) -> CodeGuardConfig:
        data = load_toml_section(project_root, "codeguard-c")
        return cls(
            max_cyclomatic_complexity=int(data.get("max_cyclomatic_complexity", 10)),
            max_function_lines=int(data.get("max_function_lines", 50)),
            exclude_patterns=list(
                data.get("exclude_patterns", ["build/", "third_party/", "*.pb.c"])
            ),
            misra_mandatory=bool(data.get("misra_mandatory", True)),
            misra_required=bool(data.get("misra_required", True)),
            misra_advisory=bool(data.get("misra_advisory", False)),
        )
