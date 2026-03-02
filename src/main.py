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
Main entry point for portia-bot. Initialises managers, configures the Fluxer
client, loads handlers, registers the voice state dispatcher, and starts the
bot.

Single on_voice_state_update dispatcher pattern used because fluxer-py only
supports one registered handler per event type.
----------------------------------------------------------------------------
FILE VERSION: v1.5.0
LAST MODIFIED: 2026-02-27
BOT: portia-bot
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/PapaBearDoes/bragi
============================================================================
"""

import sys
import traceback

import fluxer

from src.managers.config_manager import create_config_manager
from src.managers.logging_config_manager import create_logging_config_manager
from src.managers.channel_tracker_manager import create_channel_tracker_manager


def main() -> None:

    # -------------------------------------------------------------------------
    # Initialise logging (must be first)
    # -------------------------------------------------------------------------
    logging_manager = create_logging_config_manager(app_name="portia-bot")
    log = logging_manager.get_logger("main")

    log.info("portia-bot starting up")

    # -------------------------------------------------------------------------
    # Initialise config
    # -------------------------------------------------------------------------
    try:
        config_manager = create_config_manager()
    except Exception as e:
        log.critical(f"Failed to initialise ConfigManager: {e}")
        sys.exit(1)

    # Re-initialise logging with config values
    logging_manager = create_logging_config_manager(
        log_level=config_manager.get("logging", "level", "INFO"),
        log_format=config_manager.get("logging", "format", "human"),
        log_file=config_manager.get("logging", "file"),
        console_enabled=config_manager.get_bool("logging", "console", True),
        app_name="portia-bot",
    )
    log = logging_manager.get_logger("main")

    # -------------------------------------------------------------------------
    # Validate token
    # -------------------------------------------------------------------------
    token = config_manager.get_token()
    if not token:
        log.critical("Bot token is missing — cannot start")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # Validate lobby channel ID
    # -------------------------------------------------------------------------
    lobby_id = config_manager.get("voice", "lobby_channel_id", "")
    if not lobby_id:
        log.critical("Lobby channel ID not configured — cannot start")
        sys.exit(1)
    log.info(f"Monitoring lobby channel: {lobby_id}")

    # -------------------------------------------------------------------------
    # Initialise Fluxer client
    # -------------------------------------------------------------------------
    intents = fluxer.Intents.all() if hasattr(fluxer.Intents, 'all') else fluxer.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.voice_states = True

    bot = fluxer.Bot(
        command_prefix=config_manager.get("bot", "command_prefix", "!"),
        intents=intents,
    )

    # -------------------------------------------------------------------------
    # Initialise managers
    # -------------------------------------------------------------------------
    channel_tracker = create_channel_tracker_manager(
        config_manager=config_manager,
        logging_manager=logging_manager,
    )
    log.success(f"Channel tracker ready ({channel_tracker.count()} tracked)")  # type: ignore[attr-defined]

    # -------------------------------------------------------------------------
    # Initialise handlers
    # -------------------------------------------------------------------------
    from src.handlers.voice_lobby import VoiceLobbyHandler
    from src.handlers.sweep import SweepHandler
    from src.handlers.utility_temp import UtilityTempHandler

    voice_lobby = VoiceLobbyHandler(
        bot, config_manager, logging_manager, channel_tracker
    )
    voice_lobby.set_token(token)
    log.success("Loaded handler: voice_lobby")  # type: ignore[attr-defined]

    sweep = SweepHandler(
        bot, config_manager, logging_manager, channel_tracker
    )
    sweep.set_token(token)
    log.success("Loaded handler: sweep")  # type: ignore[attr-defined]

    utility = UtilityTempHandler(bot, config_manager, logging_manager)
    log.success("Loaded handler: utility (staff commands)")  # type: ignore[attr-defined]

    # -------------------------------------------------------------------------
    # Single on_message dispatcher
    # -------------------------------------------------------------------------
    @bot.event
    async def on_message(message: fluxer.Message) -> None:
        """Routes messages to relevant handlers."""
        if message.author.bot:
            return
        try:
            await utility.handle(message)
        except Exception as e:
            log.error(
                f"utility handler error: {e}\n{traceback.format_exc()}"
            )

    # -------------------------------------------------------------------------
    # Single on_voice_state_update dispatcher
    # -------------------------------------------------------------------------
    @bot.event
    async def on_voice_state_update(*args, **kwargs) -> None:
        """Routes all voice state changes to the voice lobby handler.

        fluxer-py sends a single raw dict with the full voice state payload.
        """
        if not args:
            return

        payload = args[0]
        if not isinstance(payload, dict):
            log.warning(f"Unexpected payload type: {type(payload).__name__}")
            return

        try:
            await voice_lobby.handle_voice_state_update(payload)
        except Exception as e:
            log.error(
                f"voice_lobby handler error: {e}\n{traceback.format_exc()}"
            )

    # -------------------------------------------------------------------------
    # on_error — surface unhandled exceptions
    # -------------------------------------------------------------------------
    @bot.event
    async def on_error(event: str, *args, **kwargs) -> None:
        log.error(
            f"Unhandled exception in event '{event}':\n"
            f"{traceback.format_exc()}"
        )

    # -------------------------------------------------------------------------
    # on_ready — startup reconciliation + sweep loop
    # -------------------------------------------------------------------------
    @bot.event
    async def on_ready() -> None:
        log.success(  # type: ignore[attr-defined]
            f"portia-bot connected as {bot.user} (ID: {bot.user.id})"
        )

        # Reconcile any tracked channels from before restart
        await sweep.run_startup_reconciliation()

        # Start the periodic sweep loop
        sweep.start()

    # -------------------------------------------------------------------------
    # Start — bot.run() is blocking
    # -------------------------------------------------------------------------
    bot.run(token)


if __name__ == "__main__":
    main()
