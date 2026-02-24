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
----------------------------------------------------------------------------
FILE VERSION: v1.1.0
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

        # Timers for empty-channel cleanup: {channel_id: asyncio.Task}
        self._cleanup_timers: dict[int, asyncio.Task] = {}

    # -------------------------------------------------------------------------
    # Config helpers
    # -------------------------------------------------------------------------
    def _lobby_channel_id(self) -> int:
        raw = self._config.get("voice", "lobby_channel_id", "")
        try:
            return int(raw)
        except (TypeError, ValueError):
            return 0

    def _category_id(self) -> Optional[int]:
        raw = self._config.get("voice", "category_id", "")
        if not raw:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    def _empty_timeout(self) -> int:
        return self._config.get_int("voice", "empty_timeout", 60)

    def _channel_name_format(self) -> str:
        return self._config.get("voice", "channel_name_format", "{username}'s VC")

    # -------------------------------------------------------------------------
    # Voice state update handler
    # -------------------------------------------------------------------------
    async def handle_voice_state_update(self, *args, **kwargs) -> None:
        """Called by the main.py dispatcher on every voice state change.

        DISCOVERY MODE: Accepts *args/**kwargs to discover the actual
        fluxer-py event signature. Will be tightened once confirmed.
        """
        self._log.debug(
            f"handle_voice_state_update called with {len(args)} args, {len(kwargs)} kwargs"
        )

        # Discovery: try to identify the common patterns
        # Pattern A (discord.py style): (member, before, after)
        # Pattern B (single object):    (voice_state,)
        # Pattern C (two objects):      (before, after)

        if len(args) == 3:
            member, before, after = args
        elif len(args) == 2:
            before, after = args
            member = None
        elif len(args) == 1:
            # Single voice state object — inspect it
            state = args[0]
            self._log.info(
                f"Single arg received — type: {type(state).__name__}, "
                f"attrs: {[a for a in dir(state) if not a.startswith('_')]}"
            )
            return
        else:
            self._log.warning(f"Unexpected arg count: {len(args)}")
            return
        self._log.debug(
            f"Voice state update: member={getattr(member, 'id', member)} "
            f"before={getattr(before, 'channel', before)} "
            f"after={getattr(after, 'channel', after)}"
        )

        # Determine channel IDs safely
        before_channel_id = self._safe_channel_id(before)
        after_channel_id = self._safe_channel_id(after)

        # Scenario 1: User joined the lobby
        lobby_id = self._lobby_channel_id()
        if lobby_id and after_channel_id == lobby_id:
            await self._handle_lobby_join(member, after)

        # Scenario 2: User left a tracked temp channel
        if before_channel_id and self._tracker.is_tracked(before_channel_id):
            await self._handle_temp_channel_leave(before_channel_id)

        # If someone joins a tracked temp channel, cancel any pending cleanup
        if after_channel_id and self._tracker.is_tracked(after_channel_id):
            self._cancel_cleanup_timer(after_channel_id)

    def _safe_channel_id(self, voice_state: Any) -> Optional[int]:
        """Extract channel ID from a voice state object, handling unknowns."""
        if voice_state is None:
            return None
        channel = getattr(voice_state, "channel", None)
        if channel is None:
            return None
        channel_id = getattr(channel, "id", None)
        if channel_id is not None:
            return int(channel_id)
        # Maybe voice_state itself is the channel or has channel_id directly
        channel_id = getattr(voice_state, "channel_id", None)
        if channel_id is not None:
            return int(channel_id)
        return None

    # -------------------------------------------------------------------------
    # Lobby join → create temp channel and move user
    # -------------------------------------------------------------------------
    async def _handle_lobby_join(self, member: Any, voice_state: Any) -> None:
        """Create a temporary VC for the user and move them into it."""
        user_name = getattr(member, "name", str(getattr(member, "id", "unknown")))
        user_id = getattr(member, "id", 0)
        guild_id = self._resolve_guild_id(voice_state)

        if not guild_id:
            self._log.error("Cannot determine guild ID from voice state — skipping")
            return

        channel_name = self._channel_name_format().replace("{username}", user_name)
        self._log.info(f"Creating temp VC '{channel_name}' for {user_name}")

        try:
            guild = await self._bot.fetch_guild(guild_id)

            # Build create kwargs — category if configured
            create_kwargs: dict[str, Any] = {"name": channel_name}
            category_id = self._category_id()
            if category_id:
                create_kwargs["category"] = category_id

            # Attempt channel creation — exact API shape TBD
            new_channel = await guild.create_voice_channel(**create_kwargs)
            new_channel_id = new_channel.id

            self._log.success(  # type: ignore[attr-defined]
                f"Created temp VC '{channel_name}' (ID: {new_channel_id})"
            )

            # Track the channel
            self._tracker.track(new_channel_id, user_id, user_name, guild_id)

            # Move the user into the new channel
            await member.move_to(new_channel)
            self._log.info(f"Moved {user_name} into '{channel_name}'")

        except AttributeError as e:
            # Likely an API shape mismatch — log full details for discovery
            self._log.error(
                f"API shape mismatch during channel creation: {e}\n"
                f"member type: {type(member)}\n"
                f"member attrs: {dir(member)}\n"
                f"voice_state type: {type(voice_state)}\n"
                f"voice_state attrs: {dir(voice_state)}\n"
                f"{traceback.format_exc()}"
            )
        except fluxer.Forbidden:
            self._log.error(
                f"Missing permissions to create voice channel or move member"
            )
        except fluxer.HTTPException as e:
            self._log.error(f"Fluxer API error during lobby join: {e}")
        except Exception as e:
            self._log.error(
                f"Unexpected error during lobby join: {e}\n"
                f"{traceback.format_exc()}"
            )

    def _resolve_guild_id(self, voice_state: Any) -> Optional[int]:
        """Try to extract guild_id from the voice state or its channel."""
        for attr_path in ["channel.guild_id", "guild_id"]:
            obj = voice_state
            for part in attr_path.split("."):
                obj = getattr(obj, part, None)
                if obj is None:
                    break
            if obj is not None:
                try:
                    return int(obj)
                except (TypeError, ValueError):
                    pass
        # Fallback to configured guild ID
        raw = self._config.get("bot", "guild_id", "")
        if raw:
            try:
                return int(raw)
            except (TypeError, ValueError):
                pass
        return None

    # -------------------------------------------------------------------------
    # Temp channel leave → schedule cleanup if empty
    # -------------------------------------------------------------------------
    async def _handle_temp_channel_leave(self, channel_id: int) -> None:
        """Check if a tracked temp channel is now empty, schedule deletion."""
        timeout = self._empty_timeout()
        self._log.debug(
            f"User left tracked channel {channel_id} — "
            f"will check emptiness and schedule {timeout}s cleanup"
        )

        # Check if channel is empty by fetching it
        try:
            entry = self._tracker.get_all().get(str(channel_id))
            if not entry:
                return
            guild = await self._bot.fetch_guild(entry["guild_id"])
            channel = await guild.fetch_channel(channel_id)

            # Attempt to get member count — API shape TBD
            members = getattr(channel, "members", None)
            voice_states = getattr(channel, "voice_states", None)
            member_count = 0

            if members is not None:
                member_count = len(members)
            elif voice_states is not None:
                member_count = len(voice_states)
            else:
                # Fallback: log what we have for discovery
                self._log.debug(
                    f"Channel {channel_id} attrs: {dir(channel)} — "
                    f"cannot determine member count, assuming empty"
                )

            if member_count > 0:
                self._log.debug(f"Channel {channel_id} still has {member_count} member(s)")
                return

            # Channel is empty — start cleanup timer
            self._start_cleanup_timer(channel_id, timeout)

        except fluxer.HTTPException as e:
            # Channel may already be deleted externally
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
        # Cancel existing timer if any
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
            await channel.delete(reason="Portia: temp VC empty — cleaning up")
            self._tracker.untrack(channel_id)
            self._cleanup_timers.pop(channel_id, None)
            self._log.success(  # type: ignore[attr-defined]
                f"Deleted empty temp VC {channel_id} (was: {entry['owner_name']}'s VC)"
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
