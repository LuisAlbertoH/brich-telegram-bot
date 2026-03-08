from __future__ import annotations

from brich_telegram_bot.constants import BUTTON_ALIASES, MAIN_MENU_ROWS, NAVIGATION_MENU_ROWS


def test_main_menu_includes_navegar() -> None:
    flattened = [BUTTON_ALIASES.get(item, item) for row in MAIN_MENU_ROWS for item in row]
    assert "NAVEGAR" in flattened
    assert "Camara" in flattened


def test_navigation_menu_contains_core_shortcuts() -> None:
    flattened = [BUTTON_ALIASES.get(item, item) for row in NAVIGATION_MENU_ROWS for item in row]
    for expected in [
        "UP",
        "DOWN",
        "ALT+TAB",
        "WIN+TAB",
        "PGUP",
        "PGDOWN",
        "Tomar foto",
        "Auto tras navegar: ON",
        "Auto tras navegar: OFF",
    ]:
        assert expected in flattened
