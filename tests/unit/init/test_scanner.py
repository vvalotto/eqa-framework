from __future__ import annotations

from pathlib import Path

from eqa_framework.init.scanner import DirectoryScanner


def _make_dirs(base: Path, names: list[str]) -> None:
    for name in names:
        (base / name).mkdir(parents=True, exist_ok=True)


class TestScan:
    def test_returns_sorted_candidates(self, tmp_path: Path) -> None:
        _make_dirs(tmp_path, ["app", "hal", "platform"])
        result = DirectoryScanner().scan(tmp_path)
        assert result == ["app", "hal", "platform"]

    def test_filters_noise_directories(self, tmp_path: Path) -> None:
        _make_dirs(
            tmp_path,
            ["hal", "build", "third_party", "test", "tests", "mocks", "generated", "out", "dist"],
        )
        result = DirectoryScanner().scan(tmp_path)
        assert result == ["hal"]

    def test_filters_dot_directories(self, tmp_path: Path) -> None:
        _make_dirs(tmp_path, ["hal", ".git", ".venv"])
        result = DirectoryScanner().scan(tmp_path)
        assert result == ["hal"]

    def test_empty_dir_returns_empty_list(self, tmp_path: Path) -> None:
        result = DirectoryScanner().scan(tmp_path)
        assert result == []

    def test_ignores_files(self, tmp_path: Path) -> None:
        _make_dirs(tmp_path, ["hal"])
        (tmp_path / "main.c").write_text("")
        result = DirectoryScanner().scan(tmp_path)
        assert result == ["hal"]

    def test_uses_src_subdir_when_exists(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        _make_dirs(src, ["hal", "app"])
        _make_dirs(tmp_path, ["docs"])  # directorio en raíz — no debe aparecer
        result = DirectoryScanner().scan(tmp_path)
        assert result == ["app", "hal"]

    def test_falls_back_to_path_when_no_src(self, tmp_path: Path) -> None:
        _make_dirs(tmp_path, ["hal", "platform"])
        result = DirectoryScanner().scan(tmp_path)
        assert result == ["hal", "platform"]

    def test_explicit_src_dir_overrides_inference(self, tmp_path: Path) -> None:
        firmware = tmp_path / "firmware"
        _make_dirs(firmware, ["drivers", "hal"])
        src = tmp_path / "src"
        _make_dirs(src, ["app"])  # no debe usarse
        result = DirectoryScanner().scan(tmp_path, src_dir="firmware")
        assert result == ["drivers", "hal"]

    def test_explicit_src_dir_nonexistent_returns_empty(self, tmp_path: Path) -> None:
        result = DirectoryScanner().scan(tmp_path, src_dir="nonexistent")
        assert result == []
