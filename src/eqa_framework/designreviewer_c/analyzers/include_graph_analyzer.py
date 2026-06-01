from __future__ import annotations

from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Finding
from eqa_framework.shared.verifiable import Verifiable


class IncludeGraphAnalyzer(Verifiable):
    """Detecta dependencias circulares entre headers y fan-out excesivo."""

    @property
    def name(self) -> str:
        return "include_graph"

    @property
    def estimated_seconds(self) -> int:
        return 15

    def run(self, context: ExecutionContext) -> list[Finding]:
        raise NotImplementedError
