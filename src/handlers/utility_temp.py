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
Utility handler for portia-bot. Provides staff commands for server management.
Currently implements !roles (admin-only) for listing guild roles and IDs.
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-02-27
BOT: portia-bot
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/The-Alphabet-Cartel/portia
============================================================================
"""

import fluxer

from src.managers.config_manager import ConfigManager
from src.managers.logging_config_manager import LoggingConfigManager


class UtilityTempHandler:
    """Lists guild roles via !roles command. Temporary — remove after setup."""

    def __init__(
        self,
        bot: fluxer.Bot,
        config_manager: ConfigManager,
        logging_manager: LoggingConfigManager,
    ) -> None:
        self.bot = bot
        self.log = logging_manager.get_logger("utility_temp")
        self.guild_id = config_manager.get_int("bot", "guild_id", 0)

        if not self.guild_id:
            self.log.warning("Guild ID is not configured — !roles will not work")

    async def handle(self, message: fluxer.Message) -> None:
        """Process a message. Called by the main dispatcher."""
        if message.content.strip().lower() != "!roles":
            return

        # Fetch member to check roles for admin status
        guild_id = message.channel.guild_id
        try:
            guild = await self.bot.fetch_guild(guild_id)
            member = await guild.fetch_member(message.author.id)
            roles = await guild.fetch_roles()
        except Exception as e:
            self.log.error(f"Could not fetch guild data: {e}")
            return

        # Build a set of role IDs the member has (member.roles is list of ints)
        member_role_ids = set(member.roles)

        # Check if any of the member's roles have administrator permission
        # Fluxer uses the same permissions bitfield as Discord: 0x8 = Administrator
        is_admin = any(
            r for r in roles
            if r.id in member_role_ids and getattr(r, "permissions", 0) & 0x8
        )

        if not is_admin:
            self.log.debug(
                f"!roles ignored for {message.author} — not an administrator"
            )
            return

        self.log.info(f"!roles used by {message.author} in #{message.channel}")

        lines = ["**Guild Roles and IDs:**\n```"]
        for role in sorted(roles, key=lambda r: r.position, reverse=True):
            lines.append(f"{role.name:<40} {role.id}")
        lines.append("```")

        output = "\n".join(lines)

        if len(output) <= 2000:
            await message.reply(output)
        else:
            chunks = []
            chunk = ["**Guild Roles and IDs:**\n```"]
            for role in sorted(roles, key=lambda r: r.position, reverse=True):
                line = f"{role.name:<40} {role.id}"
                if sum(len(ln) for ln in chunk) + len(line) > 1900:
                    chunk.append("```")
                    chunks.append("\n".join(chunk))
                    chunk = ["```"]
                chunk.append(line)
            chunk.append("```")
            chunks.append("\n".join(chunk))
            for c in chunks:
                await message.reply(c)
