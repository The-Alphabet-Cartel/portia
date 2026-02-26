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
VoiceLobbyHandler for portia-bot. Handles voice state update events to
create temporary voice channels when users join the lobby, and schedules
cleanup when temporary channels become empty.

fluxer-py sends on_voice_state_update as a single raw dict with:
  - channel_id: str or null (null = user disconnected)
  - guild_id: str
  - user_id: str
  - member.user.username: str
  - member.user.global_name: str

Channel creation uses direct HTTP calls to the Fluxer API because
fluxer-py's Guild object does not expose a create_voice_channel method.
Member moves use fluxer-py's member.edit() with guild_id kwarg.
Emptiness detection uses in-memory occupancy tracking from gateway events
because fetch_channel does not return voice state / member data.
----------------------------------------------------------------------------
FILE VERSION: v1.7.0
LAST MODIFIED: 2026-02-25
BOT: portia-bot
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/PapaBearDoes/bragi
============================================================================
"""

import asyncio
import time
import traceback
from typing import Any, Optional

import httpx
import fluxer


class VoiceLobbyHandler:
    """Creates temporary voice channels and manages their lifecycle.

    This handler is called from the single on_voice_state_update dispatcher
    in main.py. It does NOT register its own events (fluxer-py limitation).
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
        self._log = logging_manager.get_logger("voice_lobby")
        self._tracker = channel_tracker

        # Timers for empty-channel cleanup: {channel_id_int: asyncio.Task}
        self._cleanup_timers: dict[int, asyncio.Task] = {}

        # Track who is in each temp channel: {channel_id_int: set of user_id strings}
        self._channel_occupants: dict[int, set[str]] = {}

        # Dedup guard: {user_id: timestamp} — prevents double-fire
        self._recent_lobby_joins: dict[str, float] = {}
        self._dedup_window = 5.0  # seconds

        # HTTP client for direct API calls (channel creation)
        self._http: Optional[httpx.AsyncClient] = None

        # Resolve API base URL — bot.api_url may be None before connection
        self._api_url = getattr(bot, "api_url", None) or "https://api.fluxer.app/v1"
        if self._api_url.endswith("/"):
            self._api_url = self._api_url.rstrip("/")

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
        self._log.debug("HTTP client initialised with bot token")

    # -------------------------------------------------------------------------
    # Config helpers
    # -------------------------------------------------------------------------
    def _lobby_channel_id(self) -> str:
        return str(self._config.get("voice", "lobby_channel_id", ""))

    def _category_id(self) -> Optional[str]:
        raw = self._config.get("voice", "category_id", "")
        return str(raw) if raw else None

    def _empty_timeout(self) -> int:
        return self._config.get_int("voice", "empty_timeout", 60)

    def _channel_name_format(self) -> str:
        return self._config.get("voice", "channel_name_format", "{username}'s VC")

    # -------------------------------------------------------------------------
    # Payload helpers — extract fields from the raw dict
    # -------------------------------------------------------------------------
    def _get_channel_id(self, payload: dict) -> Optional[str]:
        """Get channel_id from payload. Returns None if user disconnected."""
        cid = payload.get("channel_id")
        return str(cid) if cid else None

    def _get_guild_id(self, payload: dict) -> str:
        return str(payload.get("guild_id", ""))

    def _get_user_id(self, payload: dict) -> str:
        return str(payload.get("user_id", ""))

    def _get_username(self, payload: dict) -> str:
        """Extract display name from payload, preferring global_name."""
        member = payload.get("member", {})
        user = member.get("user", {})
        return user.get("global_name") or user.get("username") or "unknown"

    # -------------------------------------------------------------------------
    # Dedup guard
    # -------------------------------------------------------------------------
    def _is_duplicate_lobby_join(self, user_id: str) -> bool:
        """Prevent double-fire of lobby join events."""
        now = time.monotonic()
        last = self._recent_lobby_joins.get(user_id, 0.0)
        if now - last < self._dedup_window:
            self._log.debug(f"Dedup: ignoring duplicate lobby join for {user_id}")
            return True
        self._recent_lobby_joins[user_id] = now
        return False

    # -------------------------------------------------------------------------
    # Voice state update handler
    # -------------------------------------------------------------------------
    async def handle_voice_state_update(self, payload: dict) -> None:
        """Called by the main.py dispatcher on every voice state change.

        Payload is a raw dict from fluxer-py's gateway. We handle:
        1. Update in-memory occupancy tracking for all tracked channels
        2. If user left a tracked channel and it's now empty → start timer
        3. If user joined a tracked channel → cancel any pending timer
        4. If user joined the lobby → create temp VC and move them
        """
        channel_id = self._get_channel_id(payload)
        guild_id = self._get_guild_id(payload)
        user_id = self._get_user_id(payload)
        username = self._get_username(payload)
        lobby_id = self._lobby_channel_id()

        self._log.debug(
            f"Voice update: user={username} ({user_id}) "
            f"channel={channel_id or 'disconnected'}"
        )

        # -----------------------------------------------------------------
        # Step 1: Update occupancy tracking
        # -----------------------------------------------------------------

        # Remove user from whatever tracked channel they were previously in
        previous_channel: Optional[int] = None
        for ch_id, occupants in self._channel_occupants.items():
            if user_id in occupants:
                previous_channel = ch_id
                occupants.discard(user_id)
                break

        # Determine the current channel as int (if any)
        current_channel_int: Optional[int] = None
        if channel_id:
            current_channel_int = int(channel_id)

        # Add user to the channel they just joined (if it's tracked)
        if current_channel_int and self._tracker.is_tracked(current_channel_int):
            self._channel_occupants.setdefault(current_channel_int, set()).add(user_id)
            self._cancel_cleanup_timer(current_channel_int)
            self._log.debug(
                f"Channel {current_channel_int} occupants: "
                f"{len(self._channel_occupants[current_channel_int])}"
            )

        # -----------------------------------------------------------------
        # Step 2: Check if user left a tracked channel that is now empty
        # -----------------------------------------------------------------
        if previous_channel and previous_channel != current_channel_int:
            occupants = self._channel_occupants.get(previous_channel, set())
            if len(occupants) == 0:
                timeout = self._empty_timeout()
                self._start_cleanup_timer(previous_channel, timeout)
            else:
                self._log.debug(
                    f"Channel {previous_channel} still has "
                    f"{len(occupants)} occupant(s)"
                )

        # -----------------------------------------------------------------
        # Step 3: User joined the lobby → create temp VC and move them
        # -----------------------------------------------------------------
        if channel_id and channel_id == lobby_id:
            if not self._is_duplicate_lobby_join(user_id):
                await self._handle_lobby_join(
                    guild_id=guild_id,
                    user_id=user_id,
                    username=username,
                )

    # -------------------------------------------------------------------------
    # Lobby join → create temp channel and move user
    # -------------------------------------------------------------------------
    async def _handle_lobby_join(
        self, guild_id: str, user_id: str, username: str
    ) -> None:
        """Create a temporary VC for the user and move them into it."""
        if not self._http:
            self._log.error("HTTP client not initialised — call set_token() first")
            return

        channel_name = self._channel_name_format().replace("{username}", username)
        self._log.info(f"Creating temp VC '{channel_name}' for {username}")

        try:
            # --- Create voice channel via REST API ---
            # Channel type 2 = voice (Discord-compatible convention)
            create_payload: dict[str, Any] = {
                "name": channel_name,
                "type": 2,
            }
            category_id = self._category_id()
            if category_id:
                create_payload["parent_id"] = category_id

            resp = await self._http.post(
                f"/guilds/{guild_id}/channels",
                json=create_payload,
            )

            if resp.status_code >= 400:
                self._log.error(
                    f"Channel creation failed: {resp.status_code} {resp.text}"
                )
                return

            channel_data = resp.json()
            new_channel_id = int(channel_data.get("id", 0))

            if not new_channel_id:
                self._log.error(
                    f"Channel creation returned no ID: {channel_data}"
                )
                return

            self._log.success(  # type: ignore[attr-defined]
                f"Created temp VC '{channel_name}' (ID: {new_channel_id})"
            )

            # Track the channel
            self._tracker.track(
                new_channel_id, int(user_id), username, int(guild_id)
            )

            # Seed occupancy — user will be moved here momentarily
            self._channel_occupants.setdefault(new_channel_id, set()).add(user_id)

            # --- Move user via fluxer-py member.edit() ---
            guild = await self._bot.fetch_guild(int(guild_id))
            member = await guild.fetch_member(int(user_id))

            moved = False
            if hasattr(member, "edit"):
                try:
                    await member.edit(
                        guild_id=int(guild_id),
                        channel_id=int(new_channel_id),
                    )
                    moved = True
                except Exception as e1:
                    self._log.debug(f"member.edit(channel_id=int) failed: {e1}")
                    try:
                        await member.edit(
                            guild_id=int(guild_id),
                            channel_id=str(new_channel_id),
                        )
                        moved = True
                    except Exception as e2:
                        self._log.debug(
                            f"member.edit(channel_id=str) failed: {e2}"
                        )

            if moved:
                self._log.info(f"Moved {username} into '{channel_name}'")
            else:
                self._log.error(
                    f"Failed to move {username}. "
                    f"Channel '{channel_name}' ({new_channel_id}) created "
                    f"but user not moved."
                )

        except httpx.HTTPError as e:
            self._log.error(f"HTTP error during lobby join: {e}")
        except Exception as e:
            self._log.error(
                f"Unexpected error during lobby join: {e}\n"
                f"{traceback.format_exc()}"
            )

    # -------------------------------------------------------------------------
    # Cleanup timer management
    # -------------------------------------------------------------------------
    def _start_cleanup_timer(self, channel_id: int, timeout: int) -> None:
        """Start an async timer to delete an empty temp channel."""
        self._cancel_cleanup_timer(channel_id)
        self._log.info(
            f"Channel {channel_id} is empty — scheduling deletion in {timeout}s"
        )
        task = asyncio.create_task(self._cleanup_after_delay(channel_id, timeout))
        self._cleanup_timers[channel_id] = task

    def _cancel_cleanup_timer(self, channel_id: int) -> None:
        """Cancel a pending cleanup timer (user rejoined)."""
        task = self._cleanup_timers.pop(channel_id, None)
        if task and not task.done():
            task.cancel()
            self._log.debug(f"Cancelled cleanup timer for channel {channel_id}")

    async def _cleanup_after_delay(self, channel_id: int, timeout: int) -> None:
        """Wait, then delete the channel if still empty."""
        try:
            await asyncio.sleep(timeout)

            # Double-check occupancy before deleting
            occupants = self._channel_occupants.get(channel_id, set())
            if len(occupants) > 0:
                self._log.debug(
                    f"Channel {channel_id} no longer empty "
                    f"({len(occupants)} occupants) — skipping delete"
                )
                return

            await self._delete_temp_channel(channel_id)
        except asyncio.CancelledError:
            pass  # Timer was cancelled because someone joined
        except Exception as e:
            self._log.error(
                f"Cleanup task error for {channel_id}: {e}\n"
                f"{traceback.format_exc()}"
            )

    async def _delete_temp_channel(self, channel_id: int) -> None:
        """Delete a tracked temporary voice channel."""
        entry = self._tracker.get_all().get(str(channel_id))
        if not entry:
            return

        if not self._http:
            return

        try:
            resp = await self._http.delete(f"/channels/{channel_id}")

            if resp.status_code == 404:
                self._log.info(f"Channel {channel_id} already gone — untracking")
            elif resp.status_code >= 400:
                self._log.error(
                    f"Failed to delete channel {channel_id}: "
                    f"{resp.status_code} {resp.text}"
                )
                return
            else:
                self._log.success(  # type: ignore[attr-defined]
                    f"Deleted empty temp VC {channel_id} "
                    f"(was: {entry['owner_name']}'s VC)"
                )

            self._tracker.untrack(channel_id)
            self._cleanup_timers.pop(channel_id, None)
            self._channel_occupants.pop(channel_id, None)

        except httpx.HTTPError as e:
            self._log.error(f"HTTP error deleting channel {channel_id}: {e}")
        except Exception as e:
            self._log.error(
                f"Unexpected error deleting channel {channel_id}: {e}\n"
                f"{traceback.format_exc()}"
            )
