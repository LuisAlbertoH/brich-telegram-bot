from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from dotenv import dotenv_values, load_dotenv

VALID_LOG_LEVELS = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
VALID_AUTH_MODES = {"password", "key"}

ENV_KEYS_IN_ORDER = [
    "TELEGRAM_BOT_TOKEN",
    "AUTHORIZED_CHAT_ID",
    "SETUP_PASSWORD",
    "RPI_HOST",
    "RPI_PORT",
    "RPI_USER",
    "RPI_AUTH_MODE",
    "RPI_PASSWORD",
    "RPI_SSH_KEY_PATH",
    "RPI_PROJECT_PATH",
    "SSH_TIMEOUT_SEC",
    "LOG_LEVEL",
]


class ConfigError(ValueError):
    """Raised when environment configuration is invalid."""


@dataclass(slots=True)
class AppConfig:
    telegram_bot_token: str
    authorized_chat_id: int | None
    setup_password: str
    rpi_host: str | None
    rpi_port: int
    rpi_user: str | None
    rpi_auth_mode: str
    rpi_password: str | None
    rpi_ssh_key_path: str | None
    rpi_project_path: str | None
    ssh_timeout_sec: int
    log_level: str
    env_file: Path

    @property
    def has_authorized_chat(self) -> bool:
        return self.authorized_chat_id is not None

    @property
    def remote_ready(self) -> bool:
        base_ready = bool(self.rpi_host and self.rpi_user and self.rpi_project_path)
        if not base_ready:
            return False
        if self.rpi_auth_mode == "password":
            return bool(self.rpi_password)
        if self.rpi_auth_mode == "key":
            return bool(self.rpi_ssh_key_path)
        return False

    @property
    def setup_ready(self) -> bool:
        return bool(self.setup_password)

    @property
    def fully_configured(self) -> bool:
        return self.has_authorized_chat and self.setup_ready and self.remote_ready

    @property
    def env_file_exists(self) -> bool:
        return self.env_file.exists()

    def redacted_summary(self) -> str:
        auth_secret = "set" if (
            (self.rpi_auth_mode == "password" and self.rpi_password)
            or (self.rpi_auth_mode == "key" and self.rpi_ssh_key_path)
        ) else "missing"
        return (
            f"AUTHORIZED_CHAT_ID={self.authorized_chat_id}\n"
            f"RPI_HOST={self.rpi_host}\n"
            f"RPI_PORT={self.rpi_port}\n"
            f"RPI_USER={self.rpi_user}\n"
            f"RPI_AUTH_MODE={self.rpi_auth_mode}\n"
            f"RPI_AUTH_SECRET={auth_secret}\n"
            f"RPI_PROJECT_PATH={self.rpi_project_path}\n"
            f"SSH_TIMEOUT_SEC={self.ssh_timeout_sec}\n"
            f"LOG_LEVEL={self.log_level}\n"
            f"ENV_FILE={self.env_file}"
        )


def get_default_env_file() -> Path:
    package_file = Path(__file__).resolve()
    project_root = package_file.parents[2]
    env_override = os.getenv("BRICH_BOT_ENV_FILE")
    if env_override:
        return Path(env_override).expanduser().resolve()
    return project_root / ".env"


def _parse_int(raw: str | None, key: str, default: int, minimum: int, maximum: int) -> int:
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{key} debe ser entero, recibido: {raw!r}") from exc
    if value < minimum or value > maximum:
        raise ConfigError(f"{key} fuera de rango [{minimum}, {maximum}]: {value}")
    return value


def _parse_authorized_chat_id(raw: str | None) -> int | None:
    if raw is None or raw.strip() == "":
        return None
    try:
        return int(raw.strip())
    except ValueError as exc:
        raise ConfigError("AUTHORIZED_CHAT_ID debe ser entero") from exc


def load_config(env_file: Path | None = None) -> AppConfig:
    final_env_file = env_file or get_default_env_file()
    if final_env_file.exists():
        load_dotenv(final_env_file, override=True)

    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        raise ConfigError(
            "TELEGRAM_BOT_TOKEN es obligatorio para iniciar el bot. "
            "Define la variable en entorno o en .env."
        )

    authorized_chat_id = _parse_authorized_chat_id(os.getenv("AUTHORIZED_CHAT_ID"))
    setup_password = (os.getenv("SETUP_PASSWORD") or "").strip()

    rpi_host = _normalize_optional(os.getenv("RPI_HOST"))
    rpi_port = _parse_int(os.getenv("RPI_PORT"), "RPI_PORT", 22, 1, 65535)
    rpi_user = _normalize_optional(os.getenv("RPI_USER"))
    rpi_auth_mode = (os.getenv("RPI_AUTH_MODE") or "password").strip().lower()
    if rpi_auth_mode not in VALID_AUTH_MODES:
        raise ConfigError("RPI_AUTH_MODE debe ser 'password' o 'key'")
    rpi_password = _normalize_optional(os.getenv("RPI_PASSWORD"))
    rpi_ssh_key_path = _normalize_optional(os.getenv("RPI_SSH_KEY_PATH"))
    rpi_project_path = _normalize_optional(os.getenv("RPI_PROJECT_PATH"))

    ssh_timeout_sec = _parse_int(os.getenv("SSH_TIMEOUT_SEC"), "SSH_TIMEOUT_SEC", 10, 1, 120)

    log_level = (os.getenv("LOG_LEVEL") or "INFO").strip().upper()
    if log_level not in VALID_LOG_LEVELS:
        raise ConfigError(f"LOG_LEVEL invalido: {log_level}")

    if rpi_host and not is_valid_host(rpi_host):
        raise ConfigError("RPI_HOST invalido. Usa IP o hostname simple")
    if rpi_project_path and not is_valid_project_path(rpi_project_path):
        raise ConfigError("RPI_PROJECT_PATH invalido")

    if rpi_auth_mode == "password" and rpi_password is not None and len(rpi_password) < 1:
        raise ConfigError("RPI_PASSWORD no puede ser vacio")
    if rpi_auth_mode == "key" and rpi_ssh_key_path is not None and len(rpi_ssh_key_path) < 1:
        raise ConfigError("RPI_SSH_KEY_PATH no puede ser vacio")

    return AppConfig(
        telegram_bot_token=token,
        authorized_chat_id=authorized_chat_id,
        setup_password=setup_password,
        rpi_host=rpi_host,
        rpi_port=rpi_port,
        rpi_user=rpi_user,
        rpi_auth_mode=rpi_auth_mode,
        rpi_password=rpi_password,
        rpi_ssh_key_path=rpi_ssh_key_path,
        rpi_project_path=rpi_project_path,
        ssh_timeout_sec=ssh_timeout_sec,
        log_level=log_level,
        env_file=final_env_file,
    )


def _normalize_optional(raw: str | None) -> str | None:
    if raw is None:
        return None
    stripped = raw.strip()
    return stripped if stripped else None


def is_valid_host(host: str) -> bool:
    host_pattern = re.compile(r"^[A-Za-z0-9.-]{1,253}$")
    return bool(host_pattern.fullmatch(host))


def is_valid_project_path(path_value: str) -> bool:
    path_pattern = re.compile(r"^/[A-Za-z0-9._/\-]+$")
    return bool(path_pattern.fullmatch(path_value))


def write_env_file(values: Mapping[str, Any], env_file: Path) -> None:
    current_values = {}
    if env_file.exists():
        current_values = {k: v for k, v in dotenv_values(env_file).items() if v is not None}

    merged: dict[str, str] = {}
    merged.update({k: str(v) for k, v in current_values.items()})

    for key, value in values.items():
        if value is None:
            merged[key] = ""
        else:
            merged[key] = str(value)

    lines: list[str] = []
    for key in ENV_KEYS_IN_ORDER:
        if key in merged:
            lines.append(f"{key}={_serialize_env_value(merged[key])}")

    extra_keys = sorted(set(merged.keys()) - set(ENV_KEYS_IN_ORDER))
    for key in extra_keys:
        lines.append(f"{key}={_serialize_env_value(merged[key])}")

    env_file.parent.mkdir(parents=True, exist_ok=True)
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _serialize_env_value(value: str) -> str:
    if value == "":
        return ""
    if re.fullmatch(r"[A-Za-z0-9_./:\-]+", value):
        return value
    if any(char in value for char in [' ', '"', "'", "#", "$", "`"]):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value
