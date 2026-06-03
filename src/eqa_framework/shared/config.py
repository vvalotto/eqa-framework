from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from eqa_framework.config_editor.personal_config import PersonalConfig


@dataclass
class ExecutionContext:
    """Contexto de ejecución pasado a cada Verifiable."""

    project_root: Path
    target_files: list[Path] = field(default_factory=list)
    sprint_id: str = ""


def load_toml_section(
    project_root: Path,
    section: str,
    apply_personal: bool = True,
    personal_config_path: Path | None = None,
) -> dict[str, Any]:
    """Lee [tool.<section>] desde pyproject.toml o .embedded-qa.toml.

    Si apply_personal=True, fusiona con ~/.config/eqa/config.toml donde la
    config personal gana clave a clave. personal_config_path permite inyectar
    una ruta alternativa (útil en tests).
    """
    project_config: dict[str, Any] = {}
    for filename in ("pyproject.toml", ".embedded-qa.toml"):
        config_file = project_root / filename
        if not config_file.exists():
            continue
        data = tomllib.loads(config_file.read_text(encoding="utf-8"))
        tool: dict[str, Any] = data.get("tool", {})
        project_config = tool.get(section, {})
        break

    if not apply_personal:
        return project_config

    personal = PersonalConfig(personal_config_path) if personal_config_path else PersonalConfig()
    personal.load()
    personal_section: dict[str, Any] = personal._data.get(section, {})

    return {**project_config, **personal_section}
