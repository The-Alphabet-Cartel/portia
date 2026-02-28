<p align="center">
  <img src="images/Portia-PFP.png" alt="Portia" width="200" />
</p>

# Portia

Voice channel gatekeeper for [The Alphabet Cartel](https://fluxer.gg/yGJfJH5C)'s Fluxer community.

Part of the [Bragi](https://github.com/the-alphabet-cartel/bragi) bot infrastructure.

---

## What Portia Does

Named for Shakespeare's brilliant advocate from *The Merchant of Venice*, Portia manages temporary voice channels for the community. She monitors a designated lobby voice channel — when a user joins, Portia creates a private voice channel named after them and moves them into it. When the channel has been empty for a configurable duration, Portia deletes it automatically.

**No orphaned channels.** Portia tracks every channel she creates in a persistent data file. On restart, she reconciles tracked channels against actual server state and cleans up anything left behind. A periodic sweep task provides an additional safety net.

**Event deduplication.** fluxer-py delivers every gateway event twice. Portia includes a dedup guard that filters duplicate events within a configurable window, preventing double channel creation or premature cleanup.

**Grace period protection.** Moving a user between voice channels causes a brief disconnect event before the reconnect. Portia ignores empty-channel events during a 15-second grace period after channel creation, preventing premature deletion during the move.

---

## How It Works

1. A user joins the configured **lobby** voice channel
2. Portia creates a new voice channel: `{username}'s VC`
3. Portia moves the user into the new channel via `member.edit()`
4. Other users can join and leave freely
5. Portia tracks occupancy in real-time via gateway voice state events
6. When the channel has been **empty** for the configured timeout (default 60s), Portia deletes it
7. If someone rejoins during the countdown, the timer resets

### Resilience

- **Restart recovery:** Tracked channels persist to `/app/data/temp_channels.json` via a Docker volume. On startup, Portia reconciles and cleans up any empties.
- **Periodic sweep:** Every 5 minutes (configurable), Portia checks all tracked channels via HTTP API. Stale entries are pruned, empty channels are deleted.
- **Safe deletion:** Portia only ever deletes channels she created and tracked — never manually-created channels.
- **In-memory occupancy:** Voice channel membership is tracked in real-time from `VOICE_STATE_UPDATE` gateway events, eliminating API calls for occupancy checks.

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
| `LOG_LEVEL` | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `LOG_FORMAT` | `human` | `human` (colorized) or `json` (structured) |
| `LOG_CONSOLE` | `true` | Enable console logging |
| `LOG_FILE` | — | Optional log file path |
| `PORTIA_GUILD_ID` | — | Fluxer guild ID (**required**) |
| `PORTIA_LOBBY_CHANNEL_ID` | — | Voice channel ID to monitor (**required**) |
| `PORTIA_CATEGORY_ID` | — | Category for temp channels (optional) |
| `PORTIA_EMPTY_TIMEOUT` | `60` | Seconds before deleting empty channel (5–300) |
| `PORTIA_CHANNEL_NAME_FORMAT` | `{username}'s VC` | Name template for new channels |
| `PORTIA_SWEEP_INTERVAL` | `300` | Seconds between reconciliation sweeps (60–600) |
| `PUID` | `1000` | Container user ID |
| `PGID` | `1000` | Container group ID |

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
# Edit .env — set PORTIA_LOBBY_CHANNEL_ID and PORTIA_GUILD_ID at minimum

# 3. Create the bot token secret
mkdir -p secrets
printf 'your-token-here' > secrets/portia_fluxer_token
chmod 600 secrets/portia_fluxer_token

# 4. Deploy
docker compose up -d
```

### Fluxer Bot Permissions

Portia requires both **guild role permissions** and **channel-level overrides** on the lobby channel and its parent category. Fluxer gates gateway event dispatch on channel-level permissions — without explicit overrides, voice state events will not be received.

| Permission | Scope | Why |
|------------|-------|-----|
| View Channels | Guild + Channel override | See the lobby and receive voice events |
| Connect | Guild + Channel override | Access voice channels |
| Manage Channels | Guild | Create and delete temp voice channels |
| Move Members | Guild + Channel override | Move users from lobby to temp channel |
| Send Messages | Guild | Future: notify users |

The bot's role must be positioned **above** other roles in the Fluxer role hierarchy, or member move operations will fail with `Forbidden`.

---

## Project Structure

```
portia/
├── docker-compose.yml            ← Container orchestration
├── Dockerfile                    ← Multi-stage build (Rule #10)
├── docker-entrypoint.py          ← PUID/PGID + tini (Rule #12)
├── .env.template                 ← Config reference (committed)
├── requirements.txt              ← fluxer-py + httpx
├── images/
│   └── Portia-PFP.png           ← Bot profile picture
├── secrets/
│   ├── README.md                 ← Setup instructions (committed)
│   └── portia_fluxer_token      ← Bot token (gitignored)
└── src/
    ├── main.py                   ← Entry point + event dispatcher
    ├── config/
    │   └── portia_config.json    ← JSON defaults (Rule #4)
    ├── handlers/
    │   ├── voice_lobby.py        ← Lobby join + temp channel lifecycle
    │   └── sweep.py              ← Periodic reconciliation task
    └── managers/
        ├── config_manager.py           ← Three-layer config (Rule #7)
        ├── logging_config_manager.py   ← Colorized logging (Rule #9)
        └── channel_tracker_manager.py  ← Persistent temp channel tracking
```

---

## Technical Notes

Portia uses a **hybrid approach** due to fluxer-py limitations:

- **Channel creation & deletion:** Direct HTTP calls to the Fluxer REST API via `httpx`, because `guild.create_voice_channel()` does not exist in fluxer-py 0.3.1.
- **Member moves:** `member.edit(guild_id=..., channel_id=...)` via fluxer-py's gateway session, because the REST endpoint returns 403 `MISSING_PERMISSIONS`.
- **Occupancy tracking:** In-memory state maintained from `VOICE_STATE_UPDATE` gateway events, because `fetch_channel()` does not return voice member data.

Voice state events arrive as **raw dicts** (not typed objects), and every event fires **twice** due to a fluxer-py gateway quirk. See the [fluxer-py Quirks & API Reference](https://github.com/the-alphabet-cartel/bragi/blob/main/docs/standards/fluxer-py_quirks.md) for full details.

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
| #8 Real-World Testing | ✅ Tested on live Fluxer instance |
| #9 LoggingConfigManager | ✅ Standard colorization |
| #10 Python 3.12 + Venv | ✅ Multi-stage Docker build |
| #11 File System Tools | ✅ |
| #12 Python Entrypoint + tini | ✅ PUID/PGID support |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| [fluxer-py](https://github.com/akarealemil/fluxer.py) | Fluxer bot library |
| [httpx](https://www.python-httpx.org/) | HTTP client for REST API calls |

---

## Naming

Portia is Shakespeare's brilliant advocate from *The Merchant of Venice* — known for her wisdom and fair judgment. As the voice channel gatekeeper, she ensures everyone gets their own space. Pairs with [Puck](https://github.com/the-alphabet-cartel/puck) (stream monitor, from *A Midsummer Night's Dream*) and [Prism](https://github.com/the-alphabet-cartel/prism) (welcome bot) in the Bragi bot family.

---

**Built with care for chosen family** 🏳️‍🌈
