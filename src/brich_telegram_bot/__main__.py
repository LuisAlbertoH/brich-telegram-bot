from __future__ import annotations

import logging
import sys

from .config import ConfigError, load_config
from .logging_utils import configure_logging
from .telegram_bot import BrichTelegramBot


def main() -> None:
    try:
        bootstrap_config = load_config()
    except ConfigError as exc:
        print(f"Error de configuracion: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    configure_logging(bootstrap_config.log_level)
    logger = logging.getLogger(__name__)
    logger.info("configuration_loaded", extra={"env_file": str(bootstrap_config.env_file)})

    bot = BrichTelegramBot(bootstrap_config)
    bot.run()


if __name__ == "__main__":
    main()
