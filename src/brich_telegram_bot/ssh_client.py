from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import paramiko

from .config import AppConfig
from .constants import BLE_STATUS_FILE, SERVICE_NAME
from .security import quote_remote_command

logger = logging.getLogger(__name__)


class SSHExecutionError(RuntimeError):
    """Raised when an SSH command fails or a connection cannot be established."""


@dataclass(slots=True)
class SSHResult:
    command: str
    exit_status: int
    stdout: str
    stderr: str
    duration_ms: int


class RaspberrySSHClient:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._client: paramiko.SSHClient | None = None

    def __enter__(self) -> "RaspberrySSHClient":
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def connect(self) -> None:
        if not self._config.remote_ready:
            raise SSHExecutionError("Configuracion remota incompleta para SSH")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs: dict[str, Any] = {
            "hostname": self._config.rpi_host,
            "port": self._config.rpi_port,
            "username": self._config.rpi_user,
            "timeout": self._config.ssh_timeout_sec,
            "auth_timeout": self._config.ssh_timeout_sec,
            "banner_timeout": self._config.ssh_timeout_sec,
        }

        if self._config.rpi_auth_mode == "password":
            connect_kwargs["password"] = self._config.rpi_password
            connect_kwargs["look_for_keys"] = False
            connect_kwargs["allow_agent"] = False
        else:
            connect_kwargs["key_filename"] = str(Path(self._config.rpi_ssh_key_path or "").expanduser())
            connect_kwargs["look_for_keys"] = False
            connect_kwargs["allow_agent"] = False

        try:
            client.connect(**connect_kwargs)
        except Exception as exc:
            raise SSHExecutionError(f"No se pudo conectar por SSH: {exc}") from exc

        self._client = client

    def close(self) -> None:
        if self._client:
            self._client.close()
        self._client = None

    def run_argv(self, argv: Sequence[str], allow_nonzero: bool = False) -> SSHResult:
        command = quote_remote_command(list(argv))
        return self.run_raw(command, allow_nonzero=allow_nonzero)

    def run_raw(self, command: str, allow_nonzero: bool = False) -> SSHResult:
        if not self._client:
            raise SSHExecutionError("Cliente SSH no conectado")

        start = time.monotonic()
        try:
            stdin, stdout, stderr = self._client.exec_command(command, timeout=self._config.ssh_timeout_sec)
            del stdin
            out_text = stdout.read().decode("utf-8", errors="replace").strip()
            err_text = stderr.read().decode("utf-8", errors="replace").strip()
            exit_code = stdout.channel.recv_exit_status()
        except Exception as exc:
            raise SSHExecutionError(f"Fallo ejecutando comando remoto: {exc}") from exc

        duration_ms = int((time.monotonic() - start) * 1000)
        result = SSHResult(
            command=command,
            exit_status=exit_code,
            stdout=out_text,
            stderr=err_text,
            duration_ms=duration_ms,
        )

        logger.info(
            "ssh_command_finished",
            extra={
                "command": command,
                "exit_status": exit_code,
                "duration_ms": duration_ms,
            },
        )

        if not allow_nonzero and exit_code != 0:
            raise SSHExecutionError(
                f"Comando remoto fallo (exit={exit_code}): {err_text or out_text or command}"
            )
        return result

    def get_service_status(self) -> dict[str, str]:
        active = self.run_argv(["systemctl", "is-active", SERVICE_NAME], allow_nonzero=True)
        enabled = self.run_argv(["systemctl", "is-enabled", SERVICE_NAME], allow_nonzero=True)
        return {
            "active": active.stdout or active.stderr or f"exit={active.exit_status}",
            "enabled": enabled.stdout or enabled.stderr or f"exit={enabled.exit_status}",
        }

    def control_service(self, action: str) -> None:
        safe_action = action.strip().lower()
        if safe_action not in {"restart", "start", "stop"}:
            raise SSHExecutionError(f"Accion de servicio invalida: {action}")

        args = ["systemctl", safe_action, SERVICE_NAME]
        result = self.run_argv(args, allow_nonzero=True)
        if result.exit_status == 0:
            return

        sudo_result = self.run_argv(["sudo", "-n", *args], allow_nonzero=True)
        if sudo_result.exit_status != 0:
            detail = sudo_result.stderr or sudo_result.stdout or result.stderr or result.stdout
            raise SSHExecutionError(
                f"No se pudo ejecutar '{safe_action}' en {SERVICE_NAME}: {detail or 'sin detalle'}"
            )

    def get_service_events(self, limit: int = 40) -> list[str]:
        safe_limit = max(1, min(limit, 200))
        args = [
            "journalctl",
            "-u",
            SERVICE_NAME,
            "--no-pager",
            "--output",
            "short-iso",
            "-n",
            str(safe_limit),
        ]
        result = self.run_argv(args, allow_nonzero=True)
        if result.exit_status != 0:
            sudo_result = self.run_argv(["sudo", "-n", *args], allow_nonzero=True)
            if sudo_result.exit_status != 0:
                detail = sudo_result.stderr or sudo_result.stdout or result.stderr or result.stdout
                raise SSHExecutionError(
                    f"No se pudieron leer eventos de servicio: {detail or 'sin detalle'}"
                )
            text = sudo_result.stdout
        else:
            text = result.stdout

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return lines

    def get_ble_status(self) -> dict[str, Any]:
        cmd = f"if [ -f {BLE_STATUS_FILE} ]; then cat {BLE_STATUS_FILE}; else echo '{{}}'; fi"
        result = self.run_raw(cmd, allow_nonzero=True)
        if not result.stdout:
            return {}
        try:
            payload = json.loads(result.stdout)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            return {"raw": result.stdout}
        return {"raw": result.stdout}
