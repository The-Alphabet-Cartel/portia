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
SweepHandler for portia-bot. Runs a periodic background task that reconciles
tracked temp channels with actual server state. Cleans up orphaned channels
(e.g. from a restart where events were missed) and prunes stale tracking
entries for channels that no longer exist.
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-02-23
BOT: portia-bot
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/PapaBearDoes/bragi
============================================================================
"""

import asyncio
import traceback
from typing import Any

import fluxer


class SweepHandler:
    """Periodic reconciliation of tracked temp channels.

    Started as a background task from main.py's on_ready event.
    """

    def __init__(
        self,
        bot: fluxer.Bot,
        config_manager: Any,
        logging_manager: Any,
        channel_tracker: Any,
    ) -> None:
        self._bot = bot
        self._config = config_manager
        self._log = logging_manager.get_logger("sweep")
        self._tracker = channel_tracker
        self._task: asyncio.Task | None = None

    def _sweep_interval(self) -> int:
        return self._config.get_int("voice", "sweep_interval", 300)

    def _empty_timeout(self) -> int:
        return self._config.get_int("voice", "empty_timeout", 60)

    def start(self) -> None:
        """Begin the periodic sweep loop."""
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._sweep_loop())
        self._log.info(
            f"Sweep task started (interval: {self._sweep_interval()}s)"
        )

    def stop(self) -> None:
        """Stop the periodic sweep loop."""
        if self._task and not self._task.done():
            self._task.cancel()
            self._log.info("Sweep task stopped")

    async def _sweep_loop(self) -> None:
        """Run reconciliation on a fixed interval."""
        while True:
            try:
                await asyncio.sleep(self._sweep_interval())
                await self.run_sweep()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log.error(
                    f"Sweep loop error: {e}\n{traceback.format_exc()}"
                )
                # Continue the loop after errors
                await asyncio.sleep(30)

    async def run_sweep(self) -> None:
        """Single reconciliation pass over all tracked channels."""
        tracked = self._tracker.get_all()
        if not tracked:
            self._log.debug("Sweep: no tracked channels")
            return

        self._log.debug(f"Sweep: checking {len(tracked)} tracked channel(s)")
        stale_ids: list[str] = []
        empty_ids: list[str] = []

        for channel_id_str, entry in tracked.items():
            channel_id = int(channel_id_str)
            try:
                guild = await self._bot.fetch_guild(entry["guild_id"])
                channel = await guild.fetch_channel(channel_id)

                # Check if empty
                members = getattr(channel, "members", None)
                voice_states = getattr(channel, "voice_states", None)
                member_count = 0
                if members is not None:
                    member_count = len(members)
                elif voice_states is not None:
                    member_count = len(voice_states)

                if member_count == 0:
                    empty_ids.append(channel_id_str)

            except fluxer.HTTPException as e:
                if "404" in str(e) or "Unknown Channel" in str(e):
                    stale_ids.append(channel_id_str)
                else:
                    self._log.warning(
                        f"Sweep: error checking channel {channel_id}: {e}"
                    )
            except Exception as e:
                self._log.warning(
                    f"Sweep: unexpected error for {channel_id}: {e}"
                )

        # Prune stale entries (channel no longer exists on server)
        for channel_id_str in stale_ids:
            self._tracker.untrack(int(channel_id_str))
            self._log.info(
                f"Sweep: pruned stale tracking entry for {channel_id_str}"
            )

        # Delete empty tracked channels
        for channel_id_str in empty_ids:
            channel_id = int(channel_id_str)
            entry = tracked.get(channel_id_str)
            if not entry:
                continue
            try:
                guild = await self._bot.fetch_guild(entry["guild_id"])
                channel = await guild.fetch_channel(channel_id)
                await channel.delete(reason="Portia sweep: temp VC empty")
                self._tracker.untrack(channel_id)
                self._log.success(  # type: ignore[attr-defined]
                    f"Sweep: deleted empty temp VC {channel_id} "
                    f"(was: {entry['owner_name']}'s VC)"
                )
            except fluxer.HTTPException as e:
                if "404" in str(e) or "Unknown Channel" in str(e):
                    self._tracker.untrack(channel_id)
                else:
                    self._log.error(
                        f"Sweep: failed to delete {channel_id}: {e}"
                    )

        summary_parts = []
        if stale_ids:
            summary_parts.append(f"{len(stale_ids)} stale pruned")
        if empty_ids:
            summary_parts.append(f"{len(empty_ids)} empty deleted")
        if summary_parts:
            self._log.info(f"Sweep complete: {', '.join(summary_parts)}")
        else:
            self._log.debug("Sweep complete: all tracked channels active")

    async def run_startup_reconciliation(self) -> None:
        """Run once at startup to clean up any orphans from before restart."""
        tracked = self._tracker.get_all()
        if not tracked:
            self._log.info("Startup reconciliation: no tracked channels")
            return
        self._log.info(
            f"Startup reconciliation: checking {len(tracked)} channel(s)"
        )
        await self.run_sweep()
