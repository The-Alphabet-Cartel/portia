"""
============================================================================
Bragi: Bot Infrastructure for The Alphabet Cartel
The Alphabet Cartel - https://fluxer.gg/yGJfJH5C | alphabetcartel.net
============================================================================

MISSION - NEVER TO BE VIOLATED:
    Welcome  → Greet and orient new members to our chosen family
    Moderate → Support staff with tools that keep our space safe
    Support  → Connect members to resources, information, and each other
    Sustain  → Run reliably so our community always has what it needs

============================================================================
Config watcher for portia-bot. Monitors the config directory for file
changes and triggers reload callbacks without restarting the container.
Uses polling via os.stat (no external dependencies required).
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-03-02
BOT: portia-bot
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/The-Alphabet-Cartel/portia
============================================================================
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Callable, Coroutine

log = logging.getLogger("portia-bot.config_watcher")


class ConfigWatcher:
    """Polls config files for changes and fires async callbacks on modification.

    Watches all *.json files in a directory. When a file's mtime changes,
    the registered callback is invoked with the filename that changed.
    Designed to run as a background asyncio task.
    """

    def __init__(
        self,
        config_dir: str = "/app/src/config",
        poll_interval: float = 5.0,
    ) -> None:
        self._config_dir = Path(config_dir)
        self._poll_interval = poll_interval
        self._running = False
        self._mtimes: dict[str, float] = {}
        self._callbacks: list[Callable[[str], Coroutine[Any, Any, None]]] = []

        # Snapshot initial mtimes
        self._snapshot_mtimes()

    def _snapshot_mtimes(self) -> None:
        """Record current mtime for all JSON files in the config directory."""
        if not self._config_dir.exists():
            log.warning(f"Config directory not found: {self._config_dir}")
            return
        for filepath in self._config_dir.glob("*.json"):
            try:
                self._mtimes[str(filepath)] = os.stat(filepath).st_mtime
            except OSError:
                pass

    def on_change(
        self, callback: Callable[[str], Coroutine[Any, Any, None]]
    ) -> None:
        """Register an async callback to fire when a config file changes.

        The callback receives the filename (not full path) of the changed file.
        """
        self._callbacks.append(callback)

    async def start(self) -> None:
        """Start the polling loop as a background task."""
        if self._running:
            return
        self._running = True
        log.info(
            f"Config watcher started — polling {self._config_dir} "
            f"every {self._poll_interval}s"
        )
        asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        """Stop the polling loop."""
        self._running = False
        log.info("Config watcher stopped")

    async def _poll_loop(self) -> None:
        """Main polling loop — checks mtimes and fires callbacks on changes."""
        while self._running:
            await asyncio.sleep(self._poll_interval)
            try:
                await self._check_for_changes()
            except Exception as e:
                log.error(f"Config watcher error: {e}")

    async def _check_for_changes(self) -> None:
        """Compare current mtimes against snapshot and fire callbacks."""
        if not self._config_dir.exists():
            return

        for filepath in self._config_dir.glob("*.json"):
            str_path = str(filepath)
            try:
                current_mtime = os.stat(filepath).st_mtime
            except OSError:
                continue

            previous_mtime = self._mtimes.get(str_path)

            if previous_mtime is None or current_mtime != previous_mtime:
                self._mtimes[str_path] = current_mtime

                # Skip initial snapshot (no previous mtime)
                if previous_mtime is None:
                    continue

                filename = filepath.name
                log.info(f"Config file changed: {filename}")

                for callback in self._callbacks:
                    try:
                        await callback(filename)
                    except Exception as e:
                        log.error(f"Callback error for {filename}: {e}")


def create_config_watcher(
    config_dir: str = "/app/src/config",
    poll_interval: float = 5.0,
) -> ConfigWatcher:
    """Factory function — MANDATORY. Never call ConfigWatcher directly."""
    return ConfigWatcher(config_dir=config_dir, poll_interval=poll_interval)


__all__ = ["ConfigWatcher", "create_config_watcher"]
