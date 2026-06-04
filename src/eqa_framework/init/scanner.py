from __future__ import annotations

from pathlib import Path

_NOISE: frozenset[str] = frozenset(
    {
        "build",
        "third_party",
        "test",
        "tests",
        "mocks",
        "generated",
        "out",
        "dist",
        ".git",
    }
)


class DirectoryScanner:
    def scan(self, path: Path, src_dir: str | None = None) -> list[str]:
        """Retorna nombres de subdirectorios candidatos a capa, ordenados.

        Si src_dir es None, busca primero en path/src/. Si no existe, usa path directamente.
        Si src_dir está explícito, usa path/src_dir.
        Filtra directorios de ruido y los que empiezan con punto.
        """
        if src_dir is not None:
            base = path / src_dir
        else:
            src_candidate = path / "src"
            base = src_candidate if src_candidate.is_dir() else path

        if not base.is_dir():
            return []

        return sorted(
            d.name
            for d in base.iterdir()
            if d.is_dir() and d.name not in _NOISE and not d.name.startswith(".")
        )
