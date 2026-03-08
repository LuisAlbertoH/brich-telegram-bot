from __future__ import annotations

import pytest

from brich_telegram_bot.security import (
    build_keyboard_ctl_command,
    normalize_combo,
    normalize_macro_name,
    normalize_simple_key,
    sanitize_text_input,
    validate_project_path,
)


def test_normalize_simple_key_accepts_valid_key() -> None:
    assert normalize_simple_key("enter") == "ENTER"


def test_normalize_simple_key_rejects_invalid_key() -> None:
    with pytest.raises(ValueError):
        normalize_simple_key("DROP TABLE")


def test_normalize_combo_accepts_valid_combo() -> None:
    assert normalize_combo("ctrl+alt+t") == "CTRL+ALT+T"


def test_normalize_combo_rejects_invalid_modifier() -> None:
    with pytest.raises(ValueError):
        normalize_combo("WIN+ALT+T")


def test_normalize_macro_name_rejects_injection() -> None:
    with pytest.raises(ValueError):
        normalize_macro_name("open_terminal; rm -rf /")


def test_sanitize_text_limits_size() -> None:
    long_text = "a" * 501
    with pytest.raises(ValueError):
        sanitize_text_input(long_text)


def test_validate_project_path_accepts_expected_format() -> None:
    assert validate_project_path("/home/pi/brich") == "/home/pi/brich"


def test_build_keyboard_ctl_command_quotes_arguments() -> None:
    command = build_keyboard_ctl_command("/home/pi/brich", ["text", "hello world"])
    assert "'hello world'" in command
