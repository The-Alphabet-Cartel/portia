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
ChannelTrackerManager for portia-bot. Maintains a persistent JSON record of
temporary voice channels created by Portia. Survives container restarts via
the /app/data volume mount. Only channels tracked here will ever be deleted
by Portia — she never touches channels she did not create.
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-02-23
BOT: portia-bot
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/PapaBearDoes/bragi
============================================================================
"""

import json
import time
from pathlib import Path
from typing import Any, Optional

DATA_FILE = "/app/data/temp_channels.json"


class ChannelTrackerManager:
    """Tracks temporary voice channels Portia has created.

    Data structure on disk:
    {
        "channel_id_str": {
            "owner_id": int,
            "owner_name": str,
            "created_at": float (unix timestamp),
            "guild_id": int
        }
    }
    """

    def __init__(self, config_manager: Any, logging_manager: Any) -> None:
        self._config = config_manager
        self._log = logging_manager.get_logger("channel_tracker")
        self._data_file = Path(DATA_FILE)
        self._channels: dict[str, dict[str, Any]] = {}
        self._load()

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------
    def _load(self) -> None:
        if not self._data_file.exists():
            self._log.info("No existing channel tracking data — starting fresh")
            return
        try:
            with open(self._data_file, "r", encoding="utf-8") as f:
                self._channels = json.load(f)
            count = len(self._channels)
            self._log.success(  # type: ignore[attr-defined]
                f"Loaded {count} tracked channel(s) from disk"
            )
        except (json.JSONDecodeError, OSError) as e:
            self._log.error(f"Failed to load channel data: {e} — starting fresh")
            self._channels = {}

    def _save(self) -> None:
        try:
            self._data_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(self._channels, f, indent=2)
        except OSError as e:
            self._log.error(f"Failed to save channel data: {e}")

    # -------------------------------------------------------------------------
    # Channel operations
    # -------------------------------------------------------------------------
    def track(self, channel_id: int, owner_id: int, owner_name: str, guild_id: int) -> None:
        """Record a newly created temporary channel."""
        self._channels[str(channel_id)] = {
            "owner_id": owner_id,
            "owner_name": owner_name,
            "created_at": time.time(),
            "guild_id": guild_id,
        }
        self._save()
        self._log.debug(f"Tracking new temp channel {channel_id} for {owner_name}")

    def untrack(self, channel_id: int) -> Optional[dict[str, Any]]:
        """Remove a channel from tracking. Returns the entry if it existed."""
        entry = self._channels.pop(str(channel_id), None)
        if entry:
            self._save()
            self._log.debug(f"Untracked channel {channel_id}")
        return entry

    def is_tracked(self, channel_id: int) -> bool:
        """Check if a channel was created by Portia."""
        return str(channel_id) in self._channels

    def get_all(self) -> dict[str, dict[str, Any]]:
        """Return a copy of all tracked channels."""
        return dict(self._channels)

    def count(self) -> int:
        """Return the number of currently tracked channels."""
        return len(self._channels)


def create_channel_tracker_manager(
    config_manager: Any,
    logging_manager: Any,
) -> ChannelTrackerManager:
    """Factory function — MANDATORY. Never call ChannelTrackerManager directly."""
    return ChannelTrackerManager(
        config_manager=config_manager,
        logging_manager=logging_manager,
    )


__all__ = ["ChannelTrackerManager", "create_channel_tracker_manager"]
