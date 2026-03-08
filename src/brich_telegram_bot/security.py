from __future__ import annotations

import re
import shlex
import unicodedata

from .constants import KEYBOARD_KEYS, MAX_TEXT_LENGTH

MODIFIERS = {"CTRL", "SHIFT", "ALT", "GUI"}
ALLOWED_SIMPLE_KEYS = set(KEYBOARD_KEYS)
ALLOWED_COMBO_SPECIAL = ALLOWED_SIMPLE_KEYS | {"DELETE", "HOME", "END", "PGUP", "PGDOWN"}
MACRO_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
PROJECT_PATH_PATTERN = re.compile(r"^/[A-Za-z0-9._/\-]+$")
KEY_TOKEN_PATTERN = re.compile(r"^[A-Z0-9_]{1,32}$")


def sanitize_text_input(text: str) -> str:
    cleaned = unicodedata.normalize("NFC", text)
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    cleaned = "".join(
        char
        for char in cleaned
        if char in {"\n", "\t"} or ord(char) >= 32
    )
    if not cleaned.strip():
        raise ValueError("El texto no puede ser vacio")
    if len(cleaned) > MAX_TEXT_LENGTH:
        raise ValueError(f"El texto excede {MAX_TEXT_LENGTH} caracteres")
    return cleaned


def normalize_simple_key(key: str) -> str:
    normalized = key.strip().upper()
    if normalized in ALLOWED_SIMPLE_KEYS:
        return normalized
    if not KEY_TOKEN_PATTERN.fullmatch(normalized):
        raise ValueError(f"Tecla invalida: {key}")
    return normalized


def normalize_combo(combo: str) -> str:
    parts = [part.strip().upper() for part in combo.split("+") if part.strip()]
    if len(parts) < 2:
        raise ValueError("Combo invalido. Formato esperado: CTRL+ALT+T")

    modifiers = parts[:-1]
    key = parts[-1]

    if len(set(modifiers)) != len(modifiers):
        raise ValueError("Combo invalido. Modificadores duplicados")
    if not modifiers or any(modifier not in MODIFIERS for modifier in modifiers):
        raise ValueError("Modificadores invalidos. Usa CTRL, SHIFT, ALT, GUI")
    if not _is_valid_combo_key(key):
        raise ValueError("Tecla final invalida para combo")

    return "+".join([*modifiers, key])


def normalize_macro_name(name: str) -> str:
    normalized = name.strip()
    if not MACRO_PATTERN.fullmatch(normalized):
        raise ValueError("Nombre de macro invalido")
    return normalized


def validate_project_path(path_value: str) -> str:
    normalized = path_value.strip()
    if not PROJECT_PATH_PATTERN.fullmatch(normalized):
        raise ValueError("RPI_PROJECT_PATH invalido")
    return normalized.rstrip("/")


def quote_remote_command(args: list[str]) -> str:
    if not args:
        raise ValueError("No hay comando para ejecutar")
    return " ".join(shlex.quote(arg) for arg in args)


def build_keyboard_ctl_command(project_path: str, args: list[str]) -> str:
    safe_project_path = validate_project_path(project_path)
    script_path = f"{safe_project_path}/keyboard_ctl.py"
    return quote_remote_command(["python3", script_path, *args])


def _is_valid_combo_key(key: str) -> bool:
    if key in ALLOWED_COMBO_SPECIAL:
        return True
    if len(key) == 1 and re.fullmatch(r"[A-Z0-9]", key):
        return True
    if KEY_TOKEN_PATTERN.fullmatch(key):
        return True
    return False
