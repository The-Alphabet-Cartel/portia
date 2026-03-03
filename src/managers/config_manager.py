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
ConfigManager for portia-bot. Loads configuration from JSON defaults, then
overrides with .env values, then overrides sensitive values from Docker
Secrets. Implements the three-layer config stack (Rule #4 / Rule #7).
----------------------------------------------------------------------------
FILE VERSION: v1.1.0
LAST MODIFIED: 2026-03-02
BOT: portia-bot
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/PapaBearDoes/bragi
============================================================================
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("portia-bot.config_manager")


class ConfigManager:
    def __init__(self, config_path: str = "/app/src/config/portia_config.json") -> None:
        self._config: dict[str, Any] = {}
        self._config_path = config_path
        self._load_json(config_path)
        self._apply_env_overrides()
        self._apply_secret_overrides()

    # -------------------------------------------------------------------------
    # Layer 1: JSON defaults
    # -------------------------------------------------------------------------
    def _load_json(self, config_path: str) -> None:
        path = Path(config_path)
        if not path.exists():
            log.warning(
                f"⚠️ Config file not found at {config_path} — using empty defaults"
            )
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
            log.debug(f"🔍 Loaded config from {config_path}")
        except (json.JSONDecodeError, OSError) as e:
            log.error(f"❌ Failed to load config JSON: {e} — using empty defaults")

    # -------------------------------------------------------------------------
    # Layer 2: .env overrides (non-sensitive)
    # -------------------------------------------------------------------------
    def _apply_env_overrides(self) -> None:
        env_map = {
            "LOG_LEVEL": ("logging", "level"),
            "LOG_FORMAT": ("logging", "format"),
            "PORTIA_LOG_FILE": ("logging", "file"),
            "LOG_CONSOLE": ("logging", "console"),
            "COMMAND_PREFIX": ("bot", "command_prefix"),
            "PORTIA_GUILD_ID": ("bot", "guild_id"),
            "PORTIA_LOBBY_CHANNEL_ID": ("voice", "lobby_channel_id"),
            "PORTIA_CATEGORY_ID": ("voice", "category_id"),
            "PORTIA_EMPTY_TIMEOUT": ("voice", "empty_timeout"),
            "PORTIA_CHANNEL_NAME_FORMAT": ("voice", "channel_name_format"),
            "PORTIA_SWEEP_INTERVAL": ("voice", "sweep_interval"),
        }
        for env_key, (section, key) in env_map.items():
            value = os.environ.get(env_key)
            if value is not None:
                self._config.setdefault(section, {})[key] = value
                log.debug(f"🔍 Applied env override: {env_key}")

    # -------------------------------------------------------------------------
    # Layer 3: Docker Secret overrides (sensitive)
    # -------------------------------------------------------------------------
    def _apply_secret_overrides(self) -> None:
        token_file = os.environ.get("TOKEN_FILE", "/run/secrets/portia_token")
        token = self._read_secret_file(token_file)
        if token:
            self._config.setdefault("bot", {})["token"] = token
            log.debug("🔍 Bot token loaded from Docker Secret")
        else:
            log.error("❌ Bot token not found — bot will fail to connect")

    def _read_secret_file(self, path: str) -> Optional[str]:
        secret_path = Path(path)
        if not secret_path.exists():
            log.warning(f"⚠️ Secret file not found: {path}")
            return None
        try:
            return secret_path.read_text(encoding="utf-8").strip()
        except OSError as e:
            log.error(f"❌ Could not read secret {path}: {e}")
            return None

    # -------------------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------------------
    def reload(self) -> None:
        """Re-read JSON config from disk and re-apply env/secret overrides.

        Called by the ConfigWatcher on file change (Rule #13 hot-reload).
        """
        self._config = {}
        self._load_json(self._config_path)
        self._apply_env_overrides()
        self._apply_secret_overrides()
        log.info("Configuration reloaded from disk")

    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        return self._config.get(section, {}).get(key, fallback)

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        value = self.get(section, key, fallback)
        try:
            return int(value)
        except (TypeError, ValueError):
            log.warning(
                f"⚠️ [{section}.{key}] expected int, got {value!r} — using {fallback}"
            )
            return fallback

    def get_bool(self, section: str, key: str, fallback: bool = True) -> bool:
        value = self.get(section, key, fallback)
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("true", "1", "yes")

    def get_token(self) -> str:
        return self.get("bot", "token", "")


def create_config_manager(
    config_path: str = "/app/src/config/portia_config.json",
) -> ConfigManager:
    """Factory function — MANDATORY. Never call ConfigManager directly."""
    return ConfigManager(config_path=config_path)


__all__ = ["ConfigManager", "create_config_manager"]
