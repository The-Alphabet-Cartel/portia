# Secrets

This directory holds Docker Secret files for Portia. These files are **never committed to git**.

## Required Secrets

| Filename | Description |
|---|---|
| `portia_fluxer_token` | Bot token from the Fluxer Developer Portal |

## Setup

Create each secret file with no trailing newline:

```
printf 'your-token-here' > secrets/portia_fluxer_token
```
