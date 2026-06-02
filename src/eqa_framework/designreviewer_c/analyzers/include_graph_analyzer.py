from __future__ import annotations

import fnmatch
import re
from collections import defaultdict
from pathlib import Path

from eqa_framework.designreviewer_c.config import DesignReviewerConfig
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Finding, Severity
from eqa_framework.shared.verifiable import Verifiable

_INCLUDE_RE = re.compile(r'#\s*include\s+"([^"]+)"')
_RULE_CYCLE = "INC001"
_RULE_FANOUT = "INC002"

_WHITE = 0
_GRAY = 1
_BLACK = 2


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
    """Return all local (quoted) include strings from a C/H file."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return _INCLUDE_RE.findall(content)


def _resolve_include(include: str, source_file: Path, known_files: frozenset[Path]) -> Path | None:
    candidate = (source_file.parent / include).resolve()
    return candidate if candidate in known_files else None


def _detect_cycles(graph: dict[Path, list[Path]]) -> list[tuple[Path, ...]]:
    """Return deduplicated cycles found via DFS coloring."""
    color: defaultdict[Path, int] = defaultdict(lambda: _WHITE)
    seen: set[frozenset[Path]] = set()
    cycles: list[tuple[Path, ...]] = []

    def dfs(node: Path, stack: list[Path]) -> None:
        color[node] = _GRAY
        stack.append(node)
        for neighbor in graph.get(node, []):
            if color[neighbor] == _GRAY:
                idx = stack.index(neighbor)
                cycle = tuple(stack[idx:])
                key = frozenset(cycle)
                if key not in seen:
                    seen.add(key)
                    cycles.append(cycle)
            elif color[neighbor] == _WHITE:
                dfs(neighbor, stack)
        stack.pop()
        color[node] = _BLACK

    for node in graph:
        if color[node] == _WHITE:
            dfs(node, [])

    return cycles


class IncludeGraphAnalyzer(Verifiable):
    """Detecta dependencias circulares entre headers y fan-out excesivo."""

    def __init__(self, config: DesignReviewerConfig) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return "include_graph"

    @property
    def estimated_seconds(self) -> int:
        return 15

    def run(self, context: ExecutionContext) -> list[Finding]:
        files = [
            f.resolve()
            for f in context.target_files
            if not _is_excluded(f, self._config.exclude_patterns)
        ]
        if not files:
            return []

        known_files: frozenset[Path] = frozenset(files)
        raw_includes: dict[Path, list[str]] = {f: _parse_local_includes(f) for f in files}

        # Resolved graph for cycle detection (only edges to files in our scan set)
        graph: dict[Path, list[Path]] = {}
        for file, includes in raw_includes.items():
            graph[file] = [
                resolved
                for inc in includes
                if (resolved := _resolve_include(inc, file, known_files)) is not None
            ]

        findings: list[Finding] = []

        for cycle in _detect_cycles(graph):
            names = " → ".join(p.name for p in (*cycle, cycle[0]))
            findings.append(
                Finding(
                    severity=Severity.CRITICAL,
                    rule=_RULE_CYCLE,
                    message=f"circular dependency: {names}",
                    file=cycle[0],
                    line=0,
                    tool="include_graph",
                )
            )

        for file, includes in raw_includes.items():
            fan_out = len(set(includes))
            if fan_out > self._config.max_fan_out:
                findings.append(
                    Finding(
                        severity=Severity.CRITICAL,
                        rule=_RULE_FANOUT,
                        message=(
                            f"{file.name}: fan-out {fan_out} "
                            f"exceeds limit {self._config.max_fan_out}"
                        ),
                        file=file,
                        line=0,
                        tool="include_graph",
                    )
                )

        return findings
