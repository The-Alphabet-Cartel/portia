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
----------------------------------------------------------------------------
FILE VERSION: v1.2.0
LAST MODIFIED: 2026-02-24
BOT: portia-bot
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/PapaBearDoes/bragi
============================================================================
"""

import asyncio
import traceback
from typing import Any, Optional

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
    # Voice state update handler
    # -------------------------------------------------------------------------
    async def handle_voice_state_update(self, payload: dict) -> None:
        """Called by the main.py dispatcher on every voice state change.

        Payload is a raw dict from fluxer-py's gateway. We handle:
        1. User JOINS the lobby channel → create temp VC and move them
        2. User LEAVES a tracked temp channel → start cleanup timer if empty
        3. User JOINS a tracked temp channel → cancel any pending cleanup
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

        # Scenario 1: User joined the lobby
        if channel_id and channel_id == lobby_id:
            await self._handle_lobby_join(
                guild_id=guild_id,
                user_id=user_id,
                username=username,
            )
        # Scenario 2: User disconnected (channel_id is null)
        # We don't know WHICH channel they left from this payload alone.
        # The sweep handler will catch orphaned empty channels.
        # But we can check all tracked channels on disconnect events.
        if channel_id is None:
            await self._check_all_tracked_channels()

        # Scenario 3: User joined a tracked temp channel → cancel cleanup
        if channel_id:
            channel_id_int = int(channel_id)
            if self._tracker.is_tracked(channel_id_int):
                self._cancel_cleanup_timer(channel_id_int)

    async def _check_all_tracked_channels(self) -> None:
        """After a disconnect, check all tracked channels for emptiness."""
        tracked = self._tracker.get_all()
        for channel_id_str in list(tracked.keys()):
            channel_id_int = int(channel_id_str)
            await self._handle_temp_channel_leave(channel_id_int)
    # -------------------------------------------------------------------------
    # Lobby join → create temp channel and move user
    # -------------------------------------------------------------------------
    async def _handle_lobby_join(
        self, guild_id: str, user_id: str, username: str
    ) -> None:
        """Create a temporary VC for the user and move them into it."""
        channel_name = self._channel_name_format().replace("{username}", username)
        self._log.info(f"Creating temp VC '{channel_name}' for {username}")

        try:
            guild = await self._bot.fetch_guild(int(guild_id))

            # --- Channel creation (API discovery) ---
            # Try guild.create_voice_channel() first (discord.py pattern).
            # If that doesn't exist, try variations and log what's available.
            create_kwargs: dict[str, Any] = {"name": channel_name}
            category_id = self._category_id()
            if category_id:
                create_kwargs["category"] = int(category_id)

            new_channel = None
            new_channel_id = None
            # Attempt 1: guild.create_voice_channel()
            if hasattr(guild, "create_voice_channel"):
                self._log.debug("Using guild.create_voice_channel()")
                new_channel = await guild.create_voice_channel(**create_kwargs)
            # Attempt 2: guild.create_channel() with type parameter
            elif hasattr(guild, "create_channel"):
                self._log.debug("Using guild.create_channel() with type=voice")
                new_channel = await guild.create_channel(
                    type="voice", **create_kwargs
                )
            else:
                # Log available guild methods for discovery
                guild_methods = [
                    a for a in dir(guild)
                    if not a.startswith("_") and "create" in a.lower()
                ]
                all_methods = [a for a in dir(guild) if not a.startswith("_")]
                self._log.error(
                    f"Cannot find channel creation method on guild.\n"
                    f"  Create-like methods: {guild_methods}\n"
                    f"  All public attrs: {all_methods}"
                )
                return

            if new_channel is None:
                self._log.error("Channel creation returned None")
                return
            # Extract channel ID — might be object or dict
            if isinstance(new_channel, dict):
                new_channel_id = int(new_channel.get("id", 0))
            else:
                new_channel_id = int(getattr(new_channel, "id", 0))

            if not new_channel_id:
                self._log.error(
                    f"Could not extract ID from new channel: "
                    f"type={type(new_channel).__name__}, "
                    f"value={new_channel!r:.300}"
                )
                return

            self._log.success(  # type: ignore[attr-defined]
                f"Created temp VC '{channel_name}' (ID: {new_channel_id})"
            )

            # Track the channel
            self._tracker.track(
                new_channel_id, int(user_id), username, int(guild_id)
            )
            # --- Move user to the new channel (API discovery) ---
            # Try multiple patterns for moving a user between voice channels
            member = await guild.fetch_member(int(user_id))
            moved = False

            # Attempt 1: member.move_to(channel)
            if hasattr(member, "move_to"):
                self._log.debug("Using member.move_to()")
                await member.move_to(new_channel)
                moved = True
            # Attempt 2: member.edit(voice_channel=channel)
            elif hasattr(member, "edit"):
                self._log.debug("Using member.edit(voice_channel=...)")
                await member.edit(voice_channel=new_channel)
                moved = True
            # Attempt 3: guild.move_member(member, channel)
            elif hasattr(guild, "move_member"):
                self._log.debug("Using guild.move_member()")
                await guild.move_member(member, new_channel)
                moved = True
            else:
                member_methods = [
                    a for a in dir(member)
                    if not a.startswith("_")
                    and ("move" in a.lower() or "edit" in a.lower() or "voice" in a.lower())
                ]
                all_member_methods = [a for a in dir(member) if not a.startswith("_")]
                self._log.error(
                    f"Cannot find move method.\n"
                    f"  Member move/edit/voice methods: {member_methods}\n"
                    f"  All member attrs: {all_member_methods}"
                )
            if moved:
                self._log.info(f"Moved {username} into '{channel_name}'")

        except AttributeError as e:
            self._log.error(
                f"API shape mismatch during channel creation/move: {e}\n"
                f"{traceback.format_exc()}"
            )
        except fluxer.Forbidden:
            self._log.error(
                "Missing permissions to create voice channel or move member"
            )
        except fluxer.HTTPException as e:
            self._log.error(f"Fluxer API error during lobby join: {e}")
        except Exception as e:
            self._log.error(
                f"Unexpected error during lobby join: {e}\n"
                f"{traceback.format_exc()}"
            )
    # -------------------------------------------------------------------------
    # Temp channel leave → schedule cleanup if empty
    # -------------------------------------------------------------------------
    async def _handle_temp_channel_leave(self, channel_id: int) -> None:
        """Check if a tracked temp channel is now empty, schedule deletion."""
        timeout = self._empty_timeout()

        entry = self._tracker.get_all().get(str(channel_id))
        if not entry:
            return

        try:
            guild = await self._bot.fetch_guild(entry["guild_id"])

            # Try to fetch the channel
            channel = None
            if hasattr(guild, "fetch_channel"):
                channel = await guild.fetch_channel(channel_id)
            else:
                self._log.debug(
                    f"guild has no fetch_channel — "
                    f"guild attrs: {[a for a in dir(guild) if not a.startswith('_')]}"
                )

            if channel is None:
                # Can't verify — let sweep handle it
                return
            # Determine member count — try multiple attributes
            member_count = 0
            if isinstance(channel, dict):
                # Raw dict response
                members = channel.get("members", channel.get("voice_states", []))
                member_count = len(members) if members else 0
            else:
                members = getattr(channel, "members", None)
                voice_states = getattr(channel, "voice_states", None)
                if members is not None:
                    member_count = len(members)
                elif voice_states is not None:
                    member_count = len(voice_states)
                else:
                    self._log.debug(
                        f"Channel {channel_id} — cannot determine members, "
                        f"type={type(channel).__name__}, "
                        f"attrs={[a for a in dir(channel) if not a.startswith('_')]}"
                    )
                    # Assume empty — worst case, sweep catches it
                    member_count = 0

            if member_count > 0:
                self._log.debug(
                    f"Channel {channel_id} still has {member_count} member(s)"
                )
                return

            # Channel is empty — start cleanup timer
            self._start_cleanup_timer(channel_id, timeout)
        except fluxer.HTTPException as e:
            if "404" in str(e) or "Unknown Channel" in str(e):
                self._log.info(f"Channel {channel_id} already gone — untracking")
                self._tracker.untrack(channel_id)
            else:
                self._log.error(f"Error checking channel {channel_id}: {e}")
        except Exception as e:
            self._log.error(
                f"Unexpected error checking channel {channel_id}: {e}\n"
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

        try:
            guild = await self._bot.fetch_guild(entry["guild_id"])
            channel = await guild.fetch_channel(channel_id)

            if hasattr(channel, "delete"):
                await channel.delete(reason="Portia: temp VC empty — cleaning up")
            else:
                self._log.error(
                    f"Channel object has no delete method — "
                    f"type={type(channel).__name__}, "
                    f"attrs={[a for a in dir(channel) if not a.startswith('_')]}"
                )
                return
            self._tracker.untrack(channel_id)
            self._cleanup_timers.pop(channel_id, None)
            self._log.success(  # type: ignore[attr-defined]
                f"Deleted empty temp VC {channel_id} "
                f"(was: {entry['owner_name']}'s VC)"
            )

        except fluxer.HTTPException as e:
            if "404" in str(e) or "Unknown Channel" in str(e):
                self._log.info(f"Channel {channel_id} already gone — untracking")
                self._tracker.untrack(channel_id)
                self._cleanup_timers.pop(channel_id, None)
            else:
                self._log.error(f"Failed to delete channel {channel_id}: {e}")
        except Exception as e:
            self._log.error(
                f"Unexpected error deleting channel {channel_id}: {e}\n"
                f"{traceback.format_exc()}"
            )