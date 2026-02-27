# Secrets

This directory holds Docker Secret files for Portia. These files are **never committed to git**.

## Required Secrets

| Filename | Description | Source |
|---|---|---|
| `portia_fluxer_token` | Bot token from the Fluxer App for Portia | Fluxer App |

---

## Setup: Fluxer Bot Token

1. Obtain a bot token from the Fluxer Developer Portal (or request one from
   the Fluxer team if no self-service portal exists yet)
2. Create the secret file:
   ```
   printf 'your-token-here' > ./secrets/portia_fluxer_token
   ```

---

## Deploying Secrets to Bragi

After creating all four secret files, set permissions:

```bash
chmod 600 /opt/bragi/secrets/portia_fluxer_token
```

## Security Reminders

- These files are referenced by `docker-compose.yml` and mounted at `/run/secrets/`
- The bot reads them via the `load_secret()` pattern in `config_manager.py`
- Never commit these files — only this README is tracked
- Rotate secrets periodically and after any suspected exposure
- The `secrets/` directory is gitignored in this repository

---

**Built with care for chosen family** 🏳️‍🌈
