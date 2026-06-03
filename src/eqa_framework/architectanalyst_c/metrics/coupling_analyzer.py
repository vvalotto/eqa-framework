from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path

from eqa_framework.architectanalyst_c.config import ArchitectAnalystConfig
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Finding, Severity
from eqa_framework.shared.verifiable import Verifiable

_INCLUDE_RE = re.compile(r'#\s*include\s+"([^"]+)"')

# Abstractness — opaque pointer typedefs and forward struct declarations count as abstract
_OPAQUE_PTR_RE = re.compile(r"\btypedef\s+struct\s+\w+\s*\*\s*\w+\s*;")
_FORWARD_DECL_RE = re.compile(r"^\s*struct\s+\w+\s*;", re.MULTILINE)

# Total types — typedefs, struct bodies, enum bodies (with or without tag name)
_TYPEDEF_RE = re.compile(r"\btypedef\b")
_STRUCT_BODY_RE = re.compile(r"\bstruct\s+(?:\w+\s*)?\{")
_ENUM_BODY_RE = re.compile(r"\benum\s+(?:\w+\s*)?\{")

_RULE_HIGH_INSTABILITY = "ARC001"
_RULE_DISTANCE_WARN = "ARC002"
_RULE_DISTANCE_CRIT = "ARC003"


@dataclass
class ModuleMetrics:
    """Métricas de acoplamiento de Robert C. Martin por módulo."""

    module: str
    file: Path
    ca: int = 0
    ce: int = 0
    instability: float = 0.0
    abstractness: float = 0.0
    distance: float = 0.0


def _is_excluded(path: Path, patterns: list[str]) -> bool:
    parts = path.parts
    for pattern in patterns:
        if pattern.endswith("/"):
            if pattern.rstrip("/") in parts:
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


def _compute_abstractness(header: Path) -> float:
    try:
        content = header.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0.0
    total = (
        len(_TYPEDEF_RE.findall(content))
        + len(_STRUCT_BODY_RE.findall(content))
        + len(_ENUM_BODY_RE.findall(content))
    )
    if total == 0:
        return 0.0
    abstract = len(_OPAQUE_PTR_RE.findall(content)) + len(_FORWARD_DECL_RE.findall(content))
    return min(1.0, abstract / total)


class CouplingAnalyzer(Verifiable):
    """Calcula métricas Ca, Ce, I, A, D por módulo según modelo de Martin."""

    def __init__(self, config: ArchitectAnalystConfig) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return "coupling"

    @property
    def estimated_seconds(self) -> int:
        return 60

    def compute_metrics(self, context: ExecutionContext) -> list[ModuleMetrics]:
        files = [
            f.resolve()
            for f in context.target_files
            if not _is_excluded(f, self._config.exclude_patterns)
        ]
        if not files:
            return []

        # Prefer .h over .c as representative file for each module (for abstractness)
        stem_to_file: dict[str, Path] = {}
        for f in files:
            stem = f.stem
            if stem not in stem_to_file or f.suffix == ".h":
                stem_to_file[stem] = f

        all_stems = set(stem_to_file.keys())

        # Build efferent deps: which modules does each module include?
        module_deps: dict[str, set[str]] = {s: set() for s in all_stems}
        for f in files:
            stem = f.stem
            for inc in _parse_local_includes(f):
                dep_stem = Path(inc).stem
                if dep_stem in all_stems and dep_stem != stem:
                    module_deps[stem].add(dep_stem)

        metrics: dict[str, ModuleMetrics] = {
            stem: ModuleMetrics(module=stem, file=stem_to_file[stem]) for stem in all_stems
        }

        for stem, deps in module_deps.items():
            metrics[stem].ce = len(deps)

        for _stem, deps in module_deps.items():
            for dep in deps:
                metrics[dep].ca += 1

        for stem, m in metrics.items():
            total_coupling = m.ca + m.ce
            m.instability = m.ce / total_coupling if total_coupling > 0 else 0.0
            rep = stem_to_file[stem]
            m.abstractness = _compute_abstractness(rep) if rep.suffix == ".h" else 0.0
            m.distance = abs(m.abstractness + m.instability - 1.0)

        return sorted(metrics.values(), key=lambda x: x.module)

    def run(self, context: ExecutionContext) -> list[Finding]:
        findings: list[Finding] = []
        for m in self.compute_metrics(context):
            if m.instability > self._config.max_instability:
                findings.append(
                    Finding(
                        severity=Severity.WARNING,
                        rule=_RULE_HIGH_INSTABILITY,
                        message=(
                            f"{m.module}: instability {m.instability:.2f}"
                            f" exceeds limit {self._config.max_instability}"
                        ),
                        file=m.file,
                        tool="coupling",
                    )
                )
            if m.distance > self._config.max_distance_critical:
                findings.append(
                    Finding(
                        severity=Severity.CRITICAL,
                        rule=_RULE_DISTANCE_CRIT,
                        message=(
                            f"{m.module}: distance {m.distance:.2f}"
                            f" in Zone of Pain/Uselessness (> {self._config.max_distance_critical})"
                        ),
                        file=m.file,
                        tool="coupling",
                    )
                )
            elif m.distance > self._config.max_distance_warning:
                findings.append(
                    Finding(
                        severity=Severity.WARNING,
                        rule=_RULE_DISTANCE_WARN,
                        message=(
                            f"{m.module}: distance {m.distance:.2f}"
                            f" approaching Zone of Pain/Uselessness"
                            f" (> {self._config.max_distance_warning})"
                        ),
                        file=m.file,
                        tool="coupling",
                    )
                )
        return findings
