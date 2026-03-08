from __future__ import annotations

MAIN_MENU_ROWS: list[list[str]] = [
    ["Texto", "Teclas"],
    ["Combos", "Macros"],
    ["Estado", "Ajustes"],
]

SETUP_CONFIRM_ROWS: list[list[str]] = [
    ["Guardar", "Cancelar"],
]

SETUP_RESET_CONFIRM_ROWS: list[list[str]] = [
    ["SI", "NO"],
]

AUTH_MODE_ROWS: list[list[str]] = [
    ["password", "key"],
]

LOG_LEVEL_ROWS: list[list[str]] = [
    ["DEBUG", "INFO", "WARNING", "ERROR"],
]

KEYBOARD_KEYS: list[str] = [
    "UP",
    "DOWN",
    "LEFT",
    "RIGHT",
    "ENTER",
    "TAB",
    "ESC",
    "BACKSPACE",
    "SPACE",
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "F6",
    "F7",
    "F8",
    "F9",
    "F10",
    "F11",
    "F12",
]

KEY_MENU_ROWS: list[list[str]] = [
    ["UP", "DOWN", "LEFT", "RIGHT"],
    ["ENTER", "TAB", "ESC", "BACKSPACE", "SPACE"],
    ["F1", "F2", "F3", "F4", "F5", "F6"],
    ["F7", "F8", "F9", "F10", "F11", "F12"],
    ["Cancelar"],
]

MACRO_MENU_FOOTER: list[list[str]] = [["Listar macros", "Cancelar"]]

SERVICE_NAME = "brich-keyboard.service"
BLE_STATUS_FILE = "/tmp/brich_keyboard_status.json"

MAX_TEXT_LENGTH = 500

