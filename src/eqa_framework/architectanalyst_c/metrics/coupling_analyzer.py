from __future__ import annotations

from dataclasses import dataclass

from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Finding
from eqa_framework.shared.verifiable import Verifiable


@dataclass
class ModuleMetrics:
    """Métricas de acoplamiento de Robert C. Martin por módulo."""

    module: str
    ca: int = 0  # Afferent coupling — cuántos módulos dependen de este
    ce: int = 0  # Efferent coupling — de cuántos módulos depende este
    instability: float = 0.0  # I = Ce / (Ca + Ce)
    abstractness: float = 0.0  # A = interfaces / total_types
    distance: float = 0.0  # D = |A + I - 1|


class CouplingAnalyzer(Verifiable):
    """Calcula métricas Ca, Ce, I, A, D por módulo según modelo de Martin."""

    @property
    def name(self) -> str:
        return "coupling"

    @property
    def estimated_seconds(self) -> int:
        return 60

    def run(self, context: ExecutionContext) -> list[Finding]:
        raise NotImplementedError

    def compute_metrics(self, context: ExecutionContext) -> list[ModuleMetrics]:
        raise NotImplementedError
