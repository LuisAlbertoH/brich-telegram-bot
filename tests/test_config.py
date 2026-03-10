from __future__ import annotations

from pathlib import Path

import pytest

from brich_telegram_bot.config import ConfigError, load_config, write_env_file


@pytest.fixture()
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    keys = [
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
        "CAMERA_DEVICE_INDEX",
        "CAMERA_FRAME_WIDTH",
        "CAMERA_FRAME_HEIGHT",
        "CAMERA_WARMUP_FRAMES",
        "CAMERA_TIMEOUT_SEC",
        "LOCAL_RECIPES_PATH",
        "LOG_LEVEL",
        "BRICH_BOT_ENV_FILE",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def test_load_config_requires_telegram_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_env: None) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")
    monkeypatch.setenv("BRICH_BOT_ENV_FILE", str(env_file))
    with pytest.raises(ConfigError):
        load_config()


def test_write_and_load_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_env: None) -> None:
    env_file = tmp_path / ".env"
    write_env_file(
        {
            "TELEGRAM_BOT_TOKEN": "123:abc",
            "AUTHORIZED_CHAT_ID": "12345",
            "SETUP_PASSWORD": "testpass",
            "RPI_HOST": "192.168.1.20",
            "RPI_PORT": "22",
            "RPI_USER": "pi",
            "RPI_AUTH_MODE": "password",
            "RPI_PASSWORD": "secret",
            "RPI_SSH_KEY_PATH": "",
            "RPI_PROJECT_PATH": "/home/pi/brich",
            "SSH_TIMEOUT_SEC": "10",
            "CAMERA_DEVICE_INDEX": "0",
            "CAMERA_FRAME_WIDTH": "1280",
            "CAMERA_FRAME_HEIGHT": "720",
            "CAMERA_WARMUP_FRAMES": "8",
            "CAMERA_TIMEOUT_SEC": "6",
            "LOCAL_RECIPES_PATH": "automation_recipes.json",
            "LOG_LEVEL": "INFO",
        },
        env_file=env_file,
    )
    monkeypatch.setenv("BRICH_BOT_ENV_FILE", str(env_file))
    config = load_config()
    assert config.telegram_bot_token == "123:abc"
    assert config.authorized_chat_id == 12345
    assert config.remote_ready is True
    assert config.fully_configured is True
    assert config.camera_device_index == 0
    assert config.camera_frame_width == 1280
    assert config.camera_frame_height == 720
    assert config.camera_warmup_frames == 8
    assert config.camera_timeout_sec == 6
    assert config.local_recipes_path.name == "automation_recipes.json"
