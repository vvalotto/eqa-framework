from __future__ import annotations

from pathlib import Path

from eqa_framework.designreviewer_c.analyzers.layer_violations_analyzer import (
    LayerViolationsAnalyzer,
    _file_layer,
)
from eqa_framework.designreviewer_c.config import DesignReviewerConfig
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Severity

# IEC 62304-inspired layer hierarchy used across all tests:
#   platform: no dependencies
#   hal: may depend on platform
#   app: may depend on hal and platform
_LAYERS = {
    "platform": [],
    "hal": ["platform"],
    "app": ["hal", "platform"],
}


def _config(**kwargs: object) -> DesignReviewerConfig:
    return DesignReviewerConfig(layers=_LAYERS, exclude_patterns=[], **kwargs)  # type: ignore[arg-type]


def _ctx(project_root: Path, files: list[Path]) -> ExecutionContext:
    return ExecutionContext(project_root=project_root, target_files=files)


# ---------------------------------------------------------------------------
# _file_layer
# ---------------------------------------------------------------------------


class TestFileLayer:
    def test_detects_hal_layer(self, tmp_path: Path) -> None:
        f = tmp_path / "hal" / "uart.c"
        assert _file_layer(f, tmp_path, _LAYERS) == "hal"

    def test_detects_app_layer(self, tmp_path: Path) -> None:
        f = tmp_path / "src" / "app" / "logic.c"
        assert _file_layer(f, tmp_path, _LAYERS) == "app"

    def test_returns_none_for_unknown_layer(self, tmp_path: Path) -> None:
        f = tmp_path / "src" / "main.c"
        assert _file_layer(f, tmp_path, _LAYERS) is None

    def test_returns_none_for_empty_layers(self, tmp_path: Path) -> None:
        f = tmp_path / "hal" / "uart.c"
        assert _file_layer(f, tmp_path, {}) is None


# ---------------------------------------------------------------------------
# LayerViolationsAnalyzer.run()
# ---------------------------------------------------------------------------


class TestLayerViolationsAnalyzerRun:
    def test_detects_hal_including_app(self, tmp_path: Path) -> None:
        hal_dir = tmp_path / "hal"
        app_dir = tmp_path / "app"
        hal_dir.mkdir()
        app_dir.mkdir()

        app_h = app_dir / "logic.h"
        app_h.write_text("")
        hal_c = hal_dir / "uart.c"
        hal_c.write_text('#include "../app/logic.h"\n')

        findings = LayerViolationsAnalyzer(_config()).run(_ctx(tmp_path, [hal_c, app_h]))

        assert len(findings) == 1
        assert findings[0].severity == Severity.CRITICAL
        assert findings[0].rule == "LAY001"
        assert "hal" in findings[0].message
        assert "app" in findings[0].message

    def test_no_finding_for_allowed_include(self, tmp_path: Path) -> None:
        # app → hal is allowed
        app_dir = tmp_path / "app"
        hal_dir = tmp_path / "hal"
        app_dir.mkdir()
        hal_dir.mkdir()

        hal_h = hal_dir / "uart.h"
        hal_h.write_text("")
        app_c = app_dir / "logic.c"
        app_c.write_text('#include "../hal/uart.h"\n')

        findings = LayerViolationsAnalyzer(_config()).run(_ctx(tmp_path, [app_c, hal_h]))
        assert findings == []

    def test_no_finding_for_same_layer_include(self, tmp_path: Path) -> None:
        hal_dir = tmp_path / "hal"
        hal_dir.mkdir()

        hal_h = hal_dir / "spi.h"
        hal_h.write_text("")
        hal_c = hal_dir / "uart.c"
        hal_c.write_text('#include "spi.h"\n')

        findings = LayerViolationsAnalyzer(_config()).run(_ctx(tmp_path, [hal_c, hal_h]))
        assert findings == []

    def test_no_finding_when_layers_empty(self, tmp_path: Path) -> None:
        config = DesignReviewerConfig(layers={}, exclude_patterns=[])
        hal_dir = tmp_path / "hal"
        hal_dir.mkdir()
        app_dir = tmp_path / "app"
        app_dir.mkdir()

        app_h = app_dir / "logic.h"
        app_h.write_text("")
        hal_c = hal_dir / "uart.c"
        hal_c.write_text('#include "../app/logic.h"\n')

        findings = LayerViolationsAnalyzer(config).run(_ctx(tmp_path, [hal_c, app_h]))
        assert findings == []

    def test_no_finding_for_file_outside_any_layer(self, tmp_path: Path) -> None:
        # main.c is not in any layer — should be skipped
        hal_dir = tmp_path / "hal"
        hal_dir.mkdir()

        hal_h = hal_dir / "uart.h"
        hal_h.write_text("")
        main_c = tmp_path / "main.c"
        main_c.write_text('#include "hal/uart.h"\n')

        findings = LayerViolationsAnalyzer(_config()).run(_ctx(tmp_path, [main_c, hal_h]))
        assert findings == []

    def test_platform_cannot_include_hal(self, tmp_path: Path) -> None:
        platform_dir = tmp_path / "platform"
        hal_dir = tmp_path / "hal"
        platform_dir.mkdir()
        hal_dir.mkdir()

        hal_h = hal_dir / "uart.h"
        hal_h.write_text("")
        plat_c = platform_dir / "clock.c"
        plat_c.write_text('#include "../hal/uart.h"\n')

        findings = LayerViolationsAnalyzer(_config()).run(_ctx(tmp_path, [plat_c, hal_h]))
        assert len(findings) == 1
        assert "platform" in findings[0].message
        assert "hal" in findings[0].message

    def test_excluded_files_skipped(self, tmp_path: Path) -> None:
        config = DesignReviewerConfig(layers=_LAYERS, exclude_patterns=["build/"])
        build_hal = tmp_path / "build" / "hal"
        build_hal.mkdir(parents=True)
        app_dir = tmp_path / "app"
        app_dir.mkdir()

        app_h = app_dir / "logic.h"
        app_h.write_text("")
        hal_c = build_hal / "uart.c"
        hal_c.write_text('#include "../../app/logic.h"\n')

        findings = LayerViolationsAnalyzer(config).run(_ctx(tmp_path, [hal_c, app_h]))
        assert findings == []

    def test_empty_target_files_returns_empty(self, tmp_path: Path) -> None:
        ctx = ExecutionContext(project_root=tmp_path, target_files=[])
        assert LayerViolationsAnalyzer(_config()).run(ctx) == []

    def test_tool_field_is_layer_violations(self, tmp_path: Path) -> None:
        hal_dir = tmp_path / "hal"
        app_dir = tmp_path / "app"
        hal_dir.mkdir()
        app_dir.mkdir()

        app_h = app_dir / "logic.h"
        app_h.write_text("")
        hal_c = hal_dir / "uart.c"
        hal_c.write_text('#include "../app/logic.h"\n')

        findings = LayerViolationsAnalyzer(_config()).run(_ctx(tmp_path, [hal_c, app_h]))
        assert all(f.tool == "layer_violations" for f in findings)

    def test_system_includes_ignored(self, tmp_path: Path) -> None:
        # <stdio.h> angle-bracket includes must not trigger layer check
        hal_dir = tmp_path / "hal"
        hal_dir.mkdir()
        hal_c = hal_dir / "uart.c"
        hal_c.write_text("#include <stdio.h>\n#include <stdint.h>\n")

        findings = LayerViolationsAnalyzer(_config()).run(_ctx(tmp_path, [hal_c]))
        assert findings == []
