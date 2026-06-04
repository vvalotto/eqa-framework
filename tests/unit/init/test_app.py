from __future__ import annotations

from eqa_framework.init.app import _clean_layer_name, _is_valid_layer_name


class TestCleanLayerName:
    def test_strips_whitespace(self) -> None:
        assert _clean_layer_name("  hal  ") == "hal"

    def test_lowercases(self) -> None:
        assert _clean_layer_name("HAL") == "hal"

    def test_empty_string(self) -> None:
        assert _clean_layer_name("") == ""

    def test_already_clean(self) -> None:
        assert _clean_layer_name("platform") == "platform"


class TestIsValidLayerName:
    def test_valid_name(self) -> None:
        assert _is_valid_layer_name("hal") is True

    def test_empty_is_invalid(self) -> None:
        assert _is_valid_layer_name("") is False

    def test_whitespace_only_is_invalid(self) -> None:
        assert _is_valid_layer_name("   ") is False

    def test_name_with_spaces_is_invalid(self) -> None:
        assert _is_valid_layer_name("hal layer") is False

    def test_name_with_underscores_is_valid(self) -> None:
        assert _is_valid_layer_name("hal_uart") is True

    def test_name_with_hyphens_is_valid(self) -> None:
        assert _is_valid_layer_name("hal-core") is True
