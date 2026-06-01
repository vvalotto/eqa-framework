from __future__ import annotations

from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Finding
from eqa_framework.shared.verifiable import Verifiable


class MisraCheck(Verifiable):
    """Verifica violaciones MISRA-C 2012 via cppcheck + addon misra."""

    @property
    def name(self) -> str:
        return "misra"

    @property
    def estimated_seconds(self) -> int:
        return 8

    def run(self, context: ExecutionContext) -> list[Finding]:
        raise NotImplementedError
