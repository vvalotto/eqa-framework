from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from eqa_framework.designreviewer_c.config import DesignReviewerConfig
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Finding, Severity
from eqa_framework.shared.verifiable import Verifiable

_INCLUDE_RE = re.compile(r'#\s*include\s+"([^"]+)"')
_RULE_LAYER = "LAY001"


def _is_excluded(path: Path, patterns: list[str]) -> bool:
    parts = path.parts
    for pattern in patterns:
        stripped = pattern.rstrip("/")
        if pattern.endswith("/"):
            if stripped in parts:
                return True
        elif fnmatch.fnmatch(path.name, pattern):
            return True
    return False


def _parse_local_includes(file_path: Path) -> list[str]:
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return _INCLUDE_RE.findall(content)


def _file_layer(file: Path, project_root: Path, layers: dict[str, list[str]]) -> str | None:
    """Return the layer name for a file by matching path components against layer names."""
    try:
        parts = file.resolve().relative_to(project_root.resolve()).parts
    except ValueError:
        parts = file.resolve().parts
    for part in parts:
        if part in layers:
            return part
    return None


class LayerViolationsAnalyzer(Verifiable):
    """Detecta violaciones de arquitectura en capas IEC 62304 via análisis de includes."""

    def __init__(self, config: DesignReviewerConfig) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return "layer_violations"

    @property
    def estimated_seconds(self) -> int:
        return 20

    def run(self, context: ExecutionContext) -> list[Finding]:
        if not self._config.layers:
            return []

        files = [
            f.resolve()
            for f in context.target_files
            if not _is_excluded(f, self._config.exclude_patterns)
        ]
        if not files:
            return []

        project_root = context.project_root.resolve()
        layers = self._config.layers
        findings: list[Finding] = []

        for file in files:
            source_layer = _file_layer(file, project_root, layers)
            if source_layer is None:
                continue

            allowed = layers.get(source_layer, [])

            for include in _parse_local_includes(file):
                target_path = (file.parent / include).resolve()
                target_layer = _file_layer(target_path, project_root, layers)
                if target_layer is None or target_layer == source_layer:
                    continue
                if target_layer not in allowed:
                    findings.append(
                        Finding(
                            severity=Severity.CRITICAL,
                            rule=_RULE_LAYER,
                            message=(
                                f"{file.name}: layer '{source_layer}' must not include "
                                f"from layer '{target_layer}' "
                                f"({file.name} → {target_path.name})"
                            ),
                            file=file,
                            line=0,
                            tool="layer_violations",
                        )
                    )

        return findings
