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

Uses direct HTTP calls to the Fluxer API consistent with VoiceLobbyHandler.
----------------------------------------------------------------------------
FILE VERSION: v1.1.0
LAST MODIFIED: 2026-02-25
BOT: portia-bot
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/PapaBearDoes/bragi
============================================================================
"""

import asyncio
import traceback
from typing import Any, Optional

import httpx
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
        self._http: Optional[httpx.AsyncClient] = None

        # Resolve API base URL from bot
        api_url = getattr(bot, "api_url", "https://api.fluxer.app/v1")
        if isinstance(api_url, str) and api_url.endswith("/"):
            api_url = api_url.rstrip("/")
        self._api_url = api_url

    def set_token(self, token: str) -> None:
        """Set the bot token for authenticated HTTP requests."""
        self._http = httpx.AsyncClient(
            base_url=self._api_url,
            headers={
                "Authorization": f"Bot {token}",
                "Content-Type": "application/json",
            },
            timeout=15.0,
        )
        self._log.debug("Sweep HTTP client initialised")

    def _sweep_interval(self) -> int:
        return self._config.get_int("voice", "sweep_interval", 300)

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

        if not self._http:
            self._log.warning("Sweep: HTTP client not initialised")
            return

        self._log.debug(f"Sweep: checking {len(tracked)} tracked channel(s)")
        stale_ids: list[str] = []
        empty_ids: list[str] = []

        for channel_id_str, entry in tracked.items():
            try:
                resp = await self._http.get(f"/channels/{channel_id_str}")

                if resp.status_code == 404:
                    stale_ids.append(channel_id_str)
                    continue

                if resp.status_code >= 400:
                    self._log.warning(
                        f"Sweep: error fetching channel {channel_id_str}: "
                        f"{resp.status_code}"
                    )
                    continue

                channel_data = resp.json()

                # Check if empty
                member_count = 0
                voice_states = channel_data.get("voice_states", [])
                if voice_states:
                    member_count = len(voice_states)
                else:
                    members = channel_data.get("members", [])
                    if members:
                        member_count = len(members)

                if member_count == 0:
                    empty_ids.append(channel_id_str)

            except httpx.HTTPError as e:
                self._log.warning(
                    f"Sweep: HTTP error for {channel_id_str}: {e}"
                )
            except Exception as e:
                self._log.warning(
                    f"Sweep: unexpected error for {channel_id_str}: {e}"
                )

        # Prune stale entries (channel no longer exists on server)
        for channel_id_str in stale_ids:
            self._tracker.untrack(int(channel_id_str))
            self._log.info(
                f"Sweep: pruned stale tracking entry for {channel_id_str}"
            )

        # Delete empty tracked channels
        for channel_id_str in empty_ids:
            entry = tracked.get(channel_id_str)
            if not entry:
                continue
            try:
                resp = await self._http.delete(f"/channels/{channel_id_str}")

                if resp.status_code == 404 or resp.status_code < 400:
                    self._tracker.untrack(int(channel_id_str))
                    if resp.status_code < 400:
                        self._log.success(  # type: ignore[attr-defined]
                            f"Sweep: deleted empty temp VC {channel_id_str} "
                            f"(was: {entry['owner_name']}'s VC)"
                        )
                    else:
                        self._log.info(
                            f"Sweep: channel {channel_id_str} already gone"
                        )
                else:
                    self._log.error(
                        f"Sweep: failed to delete {channel_id_str}: "
                        f"{resp.status_code}"
                    )
            except httpx.HTTPError as e:
                self._log.error(
                    f"Sweep: HTTP error deleting {channel_id_str}: {e}"
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
