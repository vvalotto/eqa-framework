from __future__ import annotations

import abc

from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Finding


class Verifiable(abc.ABC):
    """Clase base para cada verificación individual de los agentes."""

    @property
    @abc.abstractmethod
    def name(self) -> str: ...

    @property
    @abc.abstractmethod
    def estimated_seconds(self) -> int: ...

    @abc.abstractmethod
    def run(self, context: ExecutionContext) -> list[Finding]: ...
