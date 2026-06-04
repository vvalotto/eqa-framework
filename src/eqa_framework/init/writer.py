from __future__ import annotations

from pathlib import Path

_SECTION_MARKERS = (
    "[tool.codeguard-c]",
    "[tool.designreviewer-c]",
    "[tool.architectanalyst-c]",
)


def _derive_layers(ordered: list[str]) -> dict[str, list[str]]:
    """Dada la lista ordenada de menor a mayor nivel, cada capa puede depender de todas las anteriores."""
    return {layer: ordered[:i] for i, layer in enumerate(ordered)}


def generate_toml(layers: list[str]) -> str:
    """Genera el bloque TOML con las tres secciones de eqa-framework."""
    lines: list[str] = []

    lines += [
        "[tool.codeguard-c]",
        "max_cyclomatic_complexity = 10   # WARNING si CCN supera este valor",
        "max_function_lines        = 50   # WARNING si la función supera este número de líneas",
        'exclude_patterns          = ["build/", "third_party/"]',
        "",
        "[tool.codeguard-c.checks]",
        "misra_mandatory = true",
        "misra_required  = true",
        "misra_advisory  = false",
        "security        = true",
        "complexity      = true",
        "",
    ]

    lines += [
        "[tool.designreviewer-c]",
        "max_fan_out      = 12   # WARNING si un módulo incluye más headers locales distintos",
        'exclude_patterns = ["build/", "third_party/"]',
        "",
    ]

    if layers:
        derived = _derive_layers(layers)
        lines.append("[tool.designreviewer-c.layers]")
        max_len = max(len(k) for k in derived)
        for layer, deps in derived.items():
            padding = " " * (max_len - len(layer))
            deps_str = str(deps).replace("'", '"')
            lines.append(f"{layer}{padding} = {deps_str}")
    else:
        lines += [
            "[tool.designreviewer-c.layers]",
            '# TODO: definir capas — ej: platform = []  /  hal = ["platform"]  /  app = ["hal", "platform"]',
        ]

    lines += [
        "",
        "[tool.architectanalyst-c]",
        "max_instability       = 0.8   # WARNING si I = Ce/(Ca+Ce) supera este umbral",
        "max_distance_warning  = 0.3   # WARNING si D = |A+I-1| supera este umbral",
        "max_distance_critical = 0.5   # CRITICAL si D supera este umbral (Zone of Pain/Uselessness)",
        'db_path               = ".quality_control/architecture.db"',
        'exclude_patterns      = ["build/", "third_party/"]',
        "",
    ]

    return "\n".join(lines)


class ConfigWriter:
    def write(self, path: Path, toml_block: str) -> list[str]:
        """Escribe las secciones de eqa-framework en pyproject.toml.

        Si el archivo no existe, lo crea. Si existe, appendea solo las secciones ausentes.
        Retorna la lista de marcadores de sección efectivamente escritos.
        """
        target = path / "pyproject.toml"

        existing_content = target.read_text(encoding="utf-8") if target.exists() else ""
        missing = [m for m in _SECTION_MARKERS if m not in existing_content]

        if not missing:
            return []

        block_to_write = _filter_sections(toml_block, missing)

        separator = "\n" if existing_content and not existing_content.endswith("\n\n") else ""
        if existing_content and not existing_content.endswith("\n"):
            separator = "\n\n"
        elif (
            existing_content
            and existing_content.endswith("\n")
            and not existing_content.endswith("\n\n")
        ):
            separator = "\n"

        target.write_text(existing_content + separator + block_to_write, encoding="utf-8")
        return missing


def _filter_sections(toml_block: str, keep_markers: list[str]) -> str:
    """Retorna solo las secciones del bloque cuyos marcadores están en keep_markers."""
    if set(keep_markers) == set(_SECTION_MARKERS):
        return toml_block

    lines = toml_block.splitlines(keepends=True)
    result: list[str] = []
    current_active = False

    for line in lines:
        stripped = line.strip()
        if stripped in _SECTION_MARKERS:
            current_active = stripped in keep_markers
        if current_active:
            result.append(line)

    return "".join(result)
