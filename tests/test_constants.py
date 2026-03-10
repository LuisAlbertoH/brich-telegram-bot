from __future__ import annotations

from brich_telegram_bot.constants import (
    BUTTON_ALIASES,
    CAMERA_MENU_ROWS,
    MAIN_MENU_ROWS,
    NAVIGATION_MENU_ROWS,
    STATUS_MENU_ROWS,
)


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
        "Una sola vez tras navegar",
        "Auto tras navegar: ON",
        "Auto tras navegar: OFF",
    ]:
        assert expected in flattened


def test_camera_menu_contains_resolution_options() -> None:
    flattened = [BUTTON_ALIASES.get(item, item) for row in CAMERA_MENU_ROWS for item in row]
    for expected in [
        "RES 640x480",
        "RES 1280x720",
        "RES 1920x1080",
        "RES DEFAULT",
    ]:
        assert expected in flattened


def test_status_menu_contains_service_controls() -> None:
    flattened = [BUTTON_ALIASES.get(item, item) for row in STATUS_MENU_ROWS for item in row]
    for expected in [
        "Estado ahora",
        "Eventos BLE",
        "Eventos servicio",
        "Reiniciar servicio",
        "Iniciar servicio",
        "Detener servicio",
    ]:
        assert expected in flattened
