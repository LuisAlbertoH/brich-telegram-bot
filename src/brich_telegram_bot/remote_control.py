from __future__ import annotations

from typing import Any

from .config import AppConfig
from .security import (
    build_keyboard_ctl_command,
    normalize_combo,
    normalize_macro_name,
    normalize_simple_key,
    sanitize_text_input,
)
from .ssh_client import RaspberrySSHClient, SSHExecutionError


class RemoteControlError(RuntimeError):
    """Raised when a remote control operation fails."""


class RemoteKeyboardController:
    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def send_text(self, text: str) -> str:
        safe_text = sanitize_text_input(text)
        command = build_keyboard_ctl_command(self._require_project_path(), ["text", safe_text])
        self._run_checked(command)
        return safe_text

    def send_key(self, key: str) -> str:
        safe_key = normalize_simple_key(key)
        command = build_keyboard_ctl_command(self._require_project_path(), ["key", safe_key])
        self._run_checked(command)
        return safe_key

    def send_combo(self, combo: str) -> str:
        safe_combo = normalize_combo(combo)
        command = build_keyboard_ctl_command(self._require_project_path(), ["combo", safe_combo])
        self._run_checked(command)
        return safe_combo

    def run_macro(self, macro_name: str) -> str:
        safe_macro_name = normalize_macro_name(macro_name)
        command = build_keyboard_ctl_command(self._require_project_path(), ["macro", safe_macro_name])
        self._run_checked(command)
        return safe_macro_name

    def list_macros(self) -> list[str]:
        script_project_path = self._require_project_path()
        attempts = [
            build_keyboard_ctl_command(script_project_path, ["macro", "--list"]),
            build_keyboard_ctl_command(script_project_path, ["macro", "list"]),
        ]
        with RaspberrySSHClient(self._config) as ssh_client:
            for command in attempts:
                try:
                    result = ssh_client.run_raw(command, allow_nonzero=True)
                except SSHExecutionError:
                    continue
                if result.exit_status != 0:
                    continue
                parsed = self._parse_macro_list(result.stdout)
                if parsed:
                    return parsed
        return []

    def status_snapshot(self) -> dict[str, Any]:
        with RaspberrySSHClient(self._config) as ssh_client:
            service_status = ssh_client.get_service_status()
            ble_status = ssh_client.get_ble_status()
        return {
            "service": service_status,
            "ble": ble_status,
        }

    def _run_checked(self, command: str) -> None:
        try:
            with RaspberrySSHClient(self._config) as ssh_client:
                ssh_client.run_raw(command)
        except (SSHExecutionError, ValueError) as exc:
            raise RemoteControlError(str(exc)) from exc

    def _parse_macro_list(self, stdout: str) -> list[str]:
        macros = []
        for line in stdout.splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue
            try:
                macros.append(normalize_macro_name(cleaned))
            except ValueError:
                continue
        unique_sorted = sorted(set(macros))
        return unique_sorted

    def _require_project_path(self) -> str:
        if not self._config.rpi_project_path:
            raise RemoteControlError("RPI_PROJECT_PATH no configurado")
        return self._config.rpi_project_path

