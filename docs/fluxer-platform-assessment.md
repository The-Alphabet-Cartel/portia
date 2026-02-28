---
title: "Fluxer Platform Assessment"
description: "Research findings and recommendation for The Alphabet Cartel's migration to Fluxer"
category: Research
tags:
  - fluxer
  - platform
  - migration
  - privacy
  - discord-alternative
author: "PapaBearDoes"
version: "v1.0"
last_updated: "2026-02-22"
---
# Fluxer Platform Assessment

============================================================================
**Bragi**: Community Chat Platform — Platform Decision Briefing
**Community**: [The Alphabet Cartel](https://fluxer.gg/yGJfJH5C) | [alphabetcartel.net](https://alphabetcartel.org)
============================================================================

**Document Version**: v1.0
**Created**: 2026-02-22
**Status**: ✅ Decision Reached
**Last Updated**: 2026-02-22

---

## Table of Contents

1. [Summary](#1-summary)
2. [What Is Fluxer](#2-what-is-fluxer)
3. [Why Fluxer Fits Our Community](#3-why-fluxer-fits-our-community)
4. [Honest Concerns](#4-honest-concerns)
5. [Why Hosted Over Self-Hosted](#5-why-hosted-over-self-hosted)
6. [Bot Infrastructure — Bragi's New Role](#6-bot-infrastructure--bragis-new-role)
7. [Platform Scorecard](#7-platform-scorecard)
8. [Decision Log](#8-decision-log)
9. [Sources & References](#9-sources--references)

---

## 1. Summary

After researching Discord's threat model, Rocket.Chat's government entanglements, Matrix's federation CSAM/CP risks, Stoat's immaturity, and TeamSpeak's screen sharing limitations, we have identified **Fluxer** (https://fluxer.app) as the first viable community chat platform that genuinely meets our needs.

**The decision:** The Alphabet Cartel will migrate to the hosted **fluxer.app** instance rather than self-hosting. This is the right call for where Fluxer is today, and our members' Plutonium subscriptions (If they so choose to utilize it) directly fund an independent European developer building privacy-respecting open source software — rather than funding Discord's upcoming IPO.

---

## 2. What Is Fluxer

Fluxer is a free and open source instant messaging and VoIP platform (AGPLv3 licensed) built by Hampus Kraft, a 22-year-old Swedish computer engineering student at KTH Royal Institute of Technology in Stockholm.

**Company:** Fluxer Platform AB — a Swedish limited liability company (org. no. 559537-3993), registered and publicly verifiable in Sweden's corporate database. This is not an anonymous project.

**Developer background:** Hampus has been building Fluxer since 2020. He has a documented history as a Discord bug hunter, has reported and received bounties for security vulnerabilities in Discord itself, and led web infrastructure for a Minecraft server with 6 million registered players. His KTH thesis focused on distributed systems and was published in September 2025.

**Timeline:** Public beta launched January 2026. Following Discord's age verification announcement on February 9, 2026, approximately 1,000 lifetime "Visionary" supporter licenses sold at $299 each before being paused — generating roughly $300,000 in early funding for a solo developer. This materially improves the project's sustainability outlook.

**License:** AGPLv3 — the strongest copyleft license for our purposes. Any modifications to the software, even when served over a network, must be open-sourced. This prevents a proprietary fork from ever taking the project closed.

---

## 3. Why Fluxer Fits Our Community

### Legal Jurisdiction — Our Strongest Protection

Fluxer Platform AB is a **Swedish company operating under EU law and GDPR**. This is the single most important structural difference from every US-based platform we evaluated.

The DHS administrative subpoenas we documented in our Discord Threat Assessment — the ones demanding member data with 10-14 days to challenge in court — **cannot be served to a Swedish company.** US law enforcement would need to go through the EU-US Data Privacy Framework and MLAT (Mutual Legal Assistance Treaty) processes. These are slow, require judicial oversight on both sides, are politically complicated in the current environment, and are publicly visible. This is a materially different threat model.

### No Age Verification

Fluxer has no mandatory age verification, no facial scan pipeline, no Persona vendor, and no connection to Palantir's surveillance infrastructure. The March 2026 Discord deadline is not our problem.

### Affirming Community Policies

Fluxer's community guidelines explicitly prohibit content targeting individuals or groups based on gender, sexual orientation, and other protected characteristics. Our self-moderated community can enforce even stronger standards within our own space.

### Discord-Like UX

Fluxer is the closest feature-complete Discord alternative we found. Members will recognize channels, categories, roles, DMs, voice, reactions, and custom emoji. The learning curve is minimal.

**Current feature set:**
- Real-time messaging with typing indicators, reactions, and threaded replies
- Voice and video calls with screen sharing (powered by LiveKit)
- Text and voice channels organized into categories with granular permissions
- Custom emojis and stickers per community
- Rich media: link previews, image/video attachments, GIF search
- Full-text search
- Moderation tooling: roles, audit logs, moderation actions
- Web client + desktop apps + PWA for mobile (native mobile in active development)
- Bot API compatible with Discord's `@discordjs/core` library

### Business Model Alignment

No advertising. No data selling. No venture capital. Revenue comes from optional Plutonium subscriptions on the hosted instance and donations. Fluxer has committed in writing to never paywalling self-hosted features or requiring license key checks. No SSO tax.

When our members subscribe to Plutonium, they are directly funding an independent European developer building privacy-respecting infrastructure. That alignment is about as clean as it gets.

### Open Source and Auditable

The entire codebase is on GitHub at https://github.com/fluxerapp/fluxer. Anyone on our team can read it. The company is publicly registered. The developer is publicly identified. This is the opposite of a black box.

---

## 4. Honest Concerns

We present these transparently so staff can weigh them accurately. None are dealbreakers.

### Single Developer — Bus Factor

Hampus is currently the primary developer. This is a real risk. The mitigations are:

- AGPLv3 means the code cannot disappear or go closed — a community fork is always possible
- The February 2026 funding surge (~$300k from Visionary sales) has brought new contributors and financial runway
- Federation features are in active development, which will bring more community investment
- We are using the **hosted** fluxer.app instance, not self-hosting, so our continuity doesn't depend on us maintaining the server

### No Default E2EE

Fluxer is not end-to-end encrypted by default. The roadmap includes opt-in "secret chats" — ephemeral, fully E2EE sessions where nothing is stored in the database — but this is not yet shipped.

**What this means in practice:**
- Channel messages and DMs are encrypted in transit (TLS) and at rest on Fluxer's servers in Sweden
- Fluxer staff could theoretically read messages — as could any platform administrator
- For truly sensitive conversations (crisis support, coming-out discussions, anything members wouldn't want even a trusted admin to see), members should use **Signal**
- This is the same trust model as Discord, Slack, and every other non-E2EE platform — the difference is that Fluxer's servers are in Sweden under GDPR

### Public Beta Status

Fluxer is in public beta. The February 9 influx of Discord users caused stability issues on the hosted instance. These are growing pains, not structural failures. The platform is actively being refactored to handle the new load.

### No Native Mobile App Yet

Mobile access is currently a PWA (progressive web app). It works, but it doesn't feel fully native and lacks CallKit integration for voice. Native iOS and Android apps are the developer's stated first priority, with Flutter developers already engaged. Timeline is unclear but actively in motion.

---

## 5. Why Hosted Over Self-Hosted

We began this project intending to self-host our chat platform. Fluxer changes that calculus.

**Self-hosting complexity we avoid:**
- LiveKit requires open UDP ports that Cloudflare Tunnel cannot proxy — voice would have needed a separate public IP or port forwarding
- Self-hosting documentation is still maturing (a refactor is in progress)
- We become responsible for updates, backups, uptime, and security patches
- Running our own instance means we are the data controller — GDPR compliance becomes our operational burden

**What we gain by using fluxer.app:**
- Features ship to us automatically
- Fluxer Platform AB is the data controller — GDPR compliance and data subject rights are their operational responsibility
- The Swedish legal jurisdiction protections apply to the hosted instance
- Zero infrastructure overhead for the chat platform itself
- Our members' Plutonium subscriptions fund Fluxer's development directly

**The right tool for Bragi:** Bragi is a capable server sitting provisioned and ready. Redirecting it toward bot infrastructure is a better use than maintaining a chat backend we no longer need.

---

## 6. Bot Infrastructure — Bragi's New Role

Bragi will serve as the dedicated host for bots that serve The Alphabet Cartel's Fluxer community.

### Why Python is Viable

The official Fluxer quickstart demonstrates a bot using `@discordjs/core` (Node.js). This works because **Fluxer's API is intentionally compatible with Discord's API**, using the same Gateway protocol, REST patterns, and event model — just pointed at `https://api.fluxer.app` instead of Discord's endpoints.

This means Python Discord libraries can be adapted to connect to Fluxer by overriding the API base URL. The primary candidates to evaluate:

- **discord.py** — the dominant Python Discord library; customizable base URL via `DiscordClient` HTTP config
- **interactions.py** — more modern, slash-command focused (note: slash commands not yet on Fluxer)
- **hikari** — async Python library with clean REST and Gateway separation that may be simpler to redirect

**Caveat:** Fluxer notes that slash commands and interactions are not yet implemented. This means bot interactions will use prefix commands (like `!ping`) for now. Slash commands are on the roadmap.

### What We'll Need on Bragi

- Docker (already installed) running bot containers
- Python 3.12+ base images
- Docker Secrets for bot tokens (consistent with our existing secrets standards)
- Persistent volumes for any bot state (databases, configs)
- Network access to `api.fluxer.app` and `gateway.fluxer.app`

### Bot Registration Process (Already Confirmed Working)

1. Open User Settings → Applications in Fluxer
2. Create a new Application (becomes the bot's username)
3. Regenerate bot token — store in Docker Secret
4. Generate bot invite URL with "bot" scope
5. Invite to The Alphabet Cartel community with appropriate permissions

---

## 7. Platform Scorecard

| Requirement | Status | Notes |
|---|---|---|
| Self-hosted / no third-party data custody | ✅ Hosted in Sweden | EU jurisdiction, GDPR |
| Open source, auditable | ✅ AGPLv3 | Full codebase public |
| Outside US jurisdiction | ✅ Swedish company | MLAT required for US law enforcement |
| No age verification | ✅ | No Persona, no facial scan |
| LGBTQIA+ affirming policies | ✅ | Explicit in community guidelines |
| Discord-like UX | ✅ | Closest alternative found |
| Bot API | ✅ | Discord-compatible, Python viable |
| No government entanglement | ✅ | No DoD/IC contracts |
| No mandatory phone/ID | ✅ | Standard registration only |
| E2EE for channels | ⚠️ Not yet | Opt-in secret chats planned |
| Native mobile app | ⚠️ In progress | PWA works, native coming |
| Production stability | ⚠️ Beta | Growing pains from Discord exodus |
| Single-developer risk | ⚠️ Mitigated | AGPL + new funding + contributors |
| Voice without port issues | ✅ Hosted handles it | LiveKit managed by Fluxer |

---

## 8. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| Feb 2026 | Matrix/Synapse rejected | Federation CSAM replication risk unacceptable for our community |
| Feb 2026 | Rocket.Chat rejected | Active DoD/IC government marketing; mandatory workspace registration leaks metadata |
| Feb 2026 | Stoat (Revolt) — discovery layer only | E2EE not yet implemented; unstable under load |
| Feb 2026 | TeamSpeak 6 — voice-only consideration | Screen sharing unreliable on self-hosted; no text community features |
| Feb 2026 | Fluxer selected as primary platform | Swedish jurisdiction, AGPLv3, Discord-compatible API, honest roadmap |
| Feb 2026 | Hosted fluxer.app chosen over self-hosting | Eliminates LiveKit UDP complexity; GDPR compliance delegated to Fluxer AB |
| Feb 2026 | Bragi repurposed as bot infrastructure | Better use of provisioned hardware; chat platform no longer needs self-hosting |

---

## 9. Sources & References

- Fluxer application: https://fluxer.app
- Fluxer source code: https://github.com/fluxerapp/fluxer
- Fluxer developer blog — How I built Fluxer: https://blog.fluxer.app/how-i-built-fluxer-a-discord-like-chat-app/
- Fluxer 2026 Roadmap: https://blog.fluxer.app/roadmap-2026/
- Fluxer bot quickstart: https://docs.fluxer.app/quickstart
- Fluxer Platform AB (Swedish corporate registry): https://www.allabolag.se/foretag/fluxer-platform-ab/brandbergen/datacenters/2KJCA7DI5YDLG
- Fluxer privacy policy: https://fluxer.app/privacy
- Fluxer community guidelines: https://fluxer.app/guidelines
- Discord threat assessment (internal): docs/v1.0/discord-threat-assessment.md

---

**Built with care for chosen family** 🏳️‍🌈
