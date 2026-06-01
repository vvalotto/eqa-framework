from __future__ import annotations

from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Finding
from eqa_framework.shared.verifiable import Verifiable


class ComplexityCheck(Verifiable):
    """Verifica complejidad ciclomática y longitud de funciones via lizard."""

    @property
    def name(self) -> str:
        return "complexity"

    @property
    def estimated_seconds(self) -> int:
        return 3

    def run(self, context: ExecutionContext) -> list[Finding]:
        raise NotImplementedError
