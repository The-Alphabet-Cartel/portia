#!/usr/bin/env python3
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
Docker entrypoint for portia-bot. Reads PUID/PGID from environment, adjusts
the container user and group, fixes volume ownership, drops privileges, and
execs the bot process. Rule #12 compliant.
----------------------------------------------------------------------------
FILE VERSION: v1.1.0
LAST MODIFIED: 2026-03-02
BOT: portia-bot
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/The-Alphabet-Cartel/portia
============================================================================
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Tuple

COMPONENT_NAME = "portia-bot"
APP_USER = "appuser"
APP_GROUP = "appgroup"
DEFAULT_UID = 1000
DEFAULT_GID = 1000
WRITABLE_DIRECTORIES = ["/app/logs", "/app/data", "/app/src/config"]
DEFAULT_COMMAND = ["python", "src/main.py"]
CONFIG_DEFAULTS_DIR = "/app/config-defaults"
CONFIG_LIVE_DIR = "/app/src/config"

RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"


def log(level: str, msg: str) -> None:
    colors = {"INFO": CYAN, "SUCCESS": GREEN, "WARNING": YELLOW, "ERROR": RED}
    symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}
    color = colors.get(level, CYAN)
    symbol = symbols.get(level, "")
    print(f"{color}[entrypoint] {symbol} {msg}{RESET}", flush=True)


def get_puid_pgid() -> Tuple[int, int]:
    puid = int(os.environ.get("PUID", DEFAULT_UID))
    pgid = int(os.environ.get("PGID", DEFAULT_GID))
    return puid, pgid


def setup_user_and_permissions(puid: int, pgid: int) -> None:
    if os.geteuid() != 0:
        log("WARNING", "Not running as root — skipping UID/GID setup")
        return

    log("INFO", f"Configuring runtime user: UID={puid} GID={pgid}")
    subprocess.run(["groupmod", "-o", "-g", str(pgid), APP_GROUP], capture_output=True)
    subprocess.run(["usermod", "-o", "-u", str(puid), "-g", str(pgid), APP_USER], capture_output=True)

    for dir_path in WRITABLE_DIRECTORIES:
        path = Path(dir_path)
        if path.exists():
            os.chown(path, puid, pgid)
            for item in path.rglob("*"):
                try:
                    os.chown(item, puid, pgid)
                except PermissionError:
                    pass
    log("SUCCESS", "Volume ownership configured")


def drop_privileges(puid: int, pgid: int) -> None:
    if os.geteuid() != 0:
        return
    os.setgroups([])
    os.setgid(pgid)
    os.setuid(puid)
    log("SUCCESS", f"Privileges dropped → UID={puid} GID={pgid}")


def seed_config_volume() -> None:
    """Copy default config files into the mounted volume if they don't exist.

    The Dockerfile stages defaults into /app/config-defaults/. On first boot
    (or if a file is missing), they're copied into /app/src/config/ so the
    volume isn't empty. Existing files are never overwritten — the host
    directory is the source of truth after initial seeding.
    """
    defaults = Path(CONFIG_DEFAULTS_DIR)
    live = Path(CONFIG_LIVE_DIR)

    if not defaults.exists():
        log("WARNING", "Config defaults directory not found — skipping seed")
        return

    live.mkdir(parents=True, exist_ok=True)

    for src_file in defaults.glob("*.json"):
        dest_file = live / src_file.name
        if not dest_file.exists():
            import shutil
            shutil.copy2(src_file, dest_file)
            log("INFO", f"Seeded config: {src_file.name}")
        else:
            log("INFO", f"Config exists, skipping: {src_file.name}")


def main() -> None:
    log("INFO", f"Starting {COMPONENT_NAME} entrypoint")
    puid, pgid = get_puid_pgid()
    seed_config_volume()
    setup_user_and_permissions(puid, pgid)
    drop_privileges(puid, pgid)
    command = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_COMMAND
    log("INFO", f"Executing: {' '.join(command)}")
    os.execvp(command[0], command)


if __name__ == "__main__":
    main()
