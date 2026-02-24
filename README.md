# Portia

Voice channel gatekeeper for [The Alphabet Cartel](https://discord.gg/alphabetcartel)'s Fluxer instance.

Part of the [Bragi](https://github.com/the-alphabet-cartel/bragi) bot infrastructure.

---

## What Portia Does

Portia monitors a designated voice channel lobby. When a user joins the lobby, Portia creates a temporary voice channel named after that user and moves them into it. When the temporary channel has been empty for a configurable duration, Portia deletes it automatically.

**No orphaned channels.** Portia tracks every channel she creates in a persistent data file. On restart, she reconciles tracked channels against actual server state and cleans up anything left behind. A periodic sweep task provides an additional safety net.

---

## How It Works

1. A user joins the configured **lobby** voice channel
2. Portia creates a new voice channel: `{username}'s VC`
3. Portia moves the user into the new channel
4. Other users can join and leave freely
5. When the channel has been **empty** for the configured timeout (default 60s), Portia deletes it
6. If someone rejoins during the countdown, the timer resets

### Resilience

- **Restart recovery:** Tracked channels persist to `/app/data/temp_channels.json` via a Docker volume. On startup, Portia reconciles and cleans up any empties.
- **Periodic sweep:** Every 5 minutes (configurable), Portia checks all tracked channels. Stale entries are pruned, empty channels are deleted.
- **Safe deletion:** Portia only ever deletes channels she created and tracked — never manually-created channels.

---

## Configuration

Portia uses the Bragi three-layer config stack:

```
portia_config.json    ← structural defaults (committed)
      ↓
.env                  ← runtime overrides (not committed)
      ↓
Docker Secrets        ← sensitive values (never in source)
```

### Environment Variables

Copy `.env.template` to `.env` and configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORTIA_LOG_LEVEL` | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `PORTIA_LOG_FORMAT` | `human` | `human` (colorized) or `json` (structured) |
| `PORTIA_GUILD_ID` | — | Fluxer guild ID |
| `PORTIA_LOBBY_CHANNEL_ID` | — | Voice channel ID to monitor (**required**) |
| `PORTIA_CATEGORY_ID` | — | Category for temp channels (optional) |
| `PORTIA_EMPTY_TIMEOUT` | `60` | Seconds before deleting empty channel (30–300) |
| `PORTIA_CHANNEL_NAME_FORMAT` | `{username}'s VC` | Name template for new channels |
| `PORTIA_SWEEP_INTERVAL` | `300` | Seconds between reconciliation sweeps (60–600) |

### Docker Secrets

| Secret | File | Description |
|--------|------|-------------|
| `portia_token` | `secrets/portia_fluxer_token` | Fluxer bot token |

---

## Deployment

### Prerequisites

- Docker Engine 29.x + Compose v5
- A Fluxer bot application with a token
- The `bragi` Docker network: `docker network create bragi`
- Host directories created:
  ```
  mkdir -p /opt/bragi/bots/portia-bot/logs
  mkdir -p /opt/bragi/bots/portia-bot/data
  ```

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/the-alphabet-cartel/portia.git
cd portia

# 2. Copy and configure environment
cp .env.template .env
# Edit .env — set PORTIA_LOBBY_CHANNEL_ID at minimum

# 3. Create the bot token secret
mkdir -p secrets
printf 'your-token-here' > secrets/fluxer_token
chmod 600 secrets/fluxer_token

# 4. Deploy
docker compose up -d
```

### Fluxer Bot Permissions

| Permission | Why |
|------------|-----|
| View Channels | See the lobby and category |
| Connect | Join voice channels |
| Manage Channels | Create and delete voice channels |
| Move Members | Move users from lobby to temp channel |

---

## Project Structure

```
portia/
├── docker-compose.yml          ← Container orchestration
├── Dockerfile                  ← Multi-stage build (Rule #10)
├── docker-entrypoint.py        ← PUID/PGID + tini (Rule #12)
├── .env.template               ← Config reference (committed)
├── requirements.txt
├── secrets/
│   ├── README.md               ← Setup instructions (committed)
│   └── fluxer_token            ← Bot token (gitignored)
└── src/
    ├── main.py                 ← Entry point + event dispatcher
    ├── config/
    │   └── portia_config.json  ← JSON defaults (Rule #4)
    ├── handlers/
    │   ├── voice_lobby.py      ← Lobby join + temp channel lifecycle
    │   └── sweep.py            ← Periodic reconciliation task
    └── managers/
        ├── config_manager.py           ← Three-layer config (Rule #7)
        ├── logging_config_manager.py   ← Colorized logging (Rule #9)
        └── channel_tracker_manager.py  ← Persistent temp channel tracking
```

---

## Charter Compliance

| Rule | Status |
|------|--------|
| #1 Factory Functions | ✅ All managers use `create_*()` |
| #2 Dependency Injection | ✅ All managers accept deps via constructor |
| #3 Additive Development | ✅ |
| #4 JSON Config + Secrets | ✅ Three-layer stack |
| #5 Resilient Validation | ✅ Fallbacks with logging |
| #6 File Versioning | ✅ All files versioned |
| #7 Config Hygiene | ✅ Secrets/env/JSON separated |
| #8 Real-World Testing | ✅ Designed for live Fluxer testing |
| #9 LoggingConfigManager | ✅ Standard colorization |
| #10 Python 3.12 + Venv | ✅ Multi-stage Docker build |
| #11 File System Tools | ✅ |
| #12 Python Entrypoint + tini | ✅ PUID/PGID support |

---

## Known Discovery Areas

Portia's voice channel functionality relies on fluxer-py APIs that haven't been empirically tested yet:

- `on_voice_state_update` event — signature assumed as `(member, before, after)`
- `guild.create_voice_channel()` — assumed to accept `name` and `category` kwargs
- `member.move_to(channel)` — assumed from discord.py pattern
- `channel.delete()` — assumed standard
- Voice channel member count — attempted via `.members` or `.voice_states` attributes

All handlers include detailed error logging with `type()` and `dir()` dumps to accelerate API discovery on first run. Findings will be added to the [fluxer-py API reference](docs/standards/fluxer-py-api-reference.md).

---

**Built with care for chosen family** 🏳️‍🌈
