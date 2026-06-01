from __future__ import annotations

from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Finding
from eqa_framework.shared.verifiable import Verifiable


class LayerViolationsAnalyzer(Verifiable):
    """Detecta violaciones de arquitectura en capas IEC 62304 via análisis de includes."""

    @property
    def name(self) -> str:
        return "layer_violations"

    @property
    def estimated_seconds(self) -> int:
        return 20

    def run(self, context: ExecutionContext) -> list[Finding]:
        raise NotImplementedError
