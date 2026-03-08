from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from brich_telegram_bot.config import load_config
from brich_telegram_bot.security import normalize_combo, normalize_simple_key, sanitize_text_input


def main() -> int:
    print("[smoke] importing modules: OK")

    os.environ.setdefault("TELEGRAM_BOT_TOKEN", "smoke-token")
    os.environ.setdefault("SETUP_PASSWORD", "smoke-password")
    os.environ.setdefault("LOG_LEVEL", "INFO")

    config = load_config()
    print(f"[smoke] config loaded from: {config.env_file}")

    assert normalize_simple_key("enter") == "ENTER"
    assert normalize_combo("ctrl+shift+t") == "CTRL+SHIFT+T"
    assert sanitize_text_input("hello") == "hello"
    print("[smoke] security validators: OK")

    print("[smoke] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
