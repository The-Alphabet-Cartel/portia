"""
============================================================================
Bragi: Bot Infrastructure for The Alphabet Cartel
The Alphabet Cartel - https://discord.gg/alphabetcartel | alphabetcartel.net
============================================================================

MISSION - NEVER TO BE VIOLATED:
    Welcome  → Greet and orient new members to our chosen family
    Moderate → Support staff with tools that keep our space safe
    Support  → Connect members to resources, information, and each other
    Sustain  → Run reliably so our community always has what it needs

============================================================================
LoggingConfigManager for portia-bot. Provides colorized, leveled console and
file logging with a custom SUCCESS level (25). Rule #9 compliant.
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-02-23
BOT: portia-bot
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/PapaBearDoes/bragi
============================================================================
"""

import logging
import sys
from typing import Optional

SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")

NOISY_LIBRARIES = [
    "websockets", "websockets.client", "websockets.server",
    "httpx", "httpcore", "asyncio", "urllib3",
    "aiohttp", "aiohttp.access",
]


class _ColorFormatter(logging.Formatter):
    COLORS = {
        "CRITICAL": "\033[1;91m",
        "ERROR":    "\033[91m",
        "WARNING":  "\033[93m",
        "INFO":     "\033[96m",
        "DEBUG":    "\033[90m",
        "SUCCESS":  "\033[92m",
        "RESET":    "\033[0m",
    }
    SYMBOLS = {
        "CRITICAL": "🚨",
        "ERROR":    "❌",
        "WARNING":  "⚠️",
        "INFO":     "ℹ️",
        "DEBUG":    "🔍",
        "SUCCESS":  "✅",
    }

    def format(self, record: logging.LogRecord) -> str:
        level = record.levelname
        color = self.COLORS.get(level, self.COLORS["RESET"])
        symbol = self.SYMBOLS.get(level, "")
        reset = self.COLORS["RESET"]
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        return (
            f"{color}[{timestamp}] {level:<8} | "
            f"{record.name:<30} | {symbol} {record.getMessage()}{reset}"
        )


class LoggingConfigManager:

    def __init__(
        self,
        log_level: str = "INFO",
        log_format: str = "human",
        log_file: Optional[str] = None,
        console_enabled: bool = True,
        app_name: str = "portia-bot",
    ) -> None:
        self.app_name = app_name
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.log_format = log_format
        self.log_file = log_file
        self.console_enabled = console_enabled
        self._configure_root()
        self._silence_noisy_libraries()

    def _configure_root(self) -> None:
        root = logging.getLogger()
        root.setLevel(self.log_level)
        root.handlers.clear()

        if self.console_enabled:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(self.log_level)
            use_color = self.log_format == "human" and sys.stdout.isatty()
            if use_color or self.log_format == "human":
                handler.setFormatter(_ColorFormatter())
            else:
                handler.setFormatter(logging.Formatter(
                    "[%(asctime)s] %(levelname)-8s | %(name)-30s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                ))
            root.addHandler(handler)

        if self.log_file:
            file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(logging.Formatter(
                "[%(asctime)s] %(levelname)-8s | %(name)-30s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ))
            root.addHandler(file_handler)

    def _silence_noisy_libraries(self) -> None:
        for lib in NOISY_LIBRARIES:
            logging.getLogger(lib).setLevel(logging.WARNING)

    def get_logger(self, name: str) -> logging.Logger:
        logger = logging.getLogger(f"{self.app_name}.{name}")
        logger.success = lambda msg, *args, **kwargs: logger.log(  # type: ignore[attr-defined]
            SUCCESS_LEVEL, msg, *args, **kwargs
        )
        return logger


def create_logging_config_manager(
    log_level: str = "INFO",
    log_format: str = "human",
    log_file: Optional[str] = None,
    console_enabled: bool = True,
    app_name: str = "portia-bot",
) -> LoggingConfigManager:
    """Factory function — MANDATORY. Never call LoggingConfigManager directly."""
    return LoggingConfigManager(
        log_level=log_level,
        log_format=log_format,
        log_file=log_file,
        console_enabled=console_enabled,
        app_name=app_name,
    )


__all__ = ["LoggingConfigManager", "create_logging_config_manager", "SUCCESS_LEVEL"]
