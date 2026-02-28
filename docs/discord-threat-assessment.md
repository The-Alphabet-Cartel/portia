---
title: "Discord Threat Assessment"
description: "Why The Alphabet Cartel must migrate away from Discord"
category: Research
tags:
  - discord
  - privacy
  - threat-assessment
  - migration
author: "PapaBearDoes"
version: "v2.0"
last_updated: "2026-02-25"
---
# Discord Threat Assessment

============================================================================
**Bragi**: Bot Infrastructure for The Alphabet Cartel
**The Alphabet Cartel** - [The Alphabet Cartel](https://fluxer.gg/yGJfJH5C) | [alphabetcartel.net](https://alphabetcartel.net)
============================================================================

**Document Version**: v2.0
**Created**: 2026-02-20
**Status**: 🚨 Active Concern — Updated with developments through February 25, 2026
**Last Updated**: 2026-02-25

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Mandatory Age Verification](#2-mandatory-age-verification)
3. [The Persona Exposure — A Surveillance Stack Hiding in Plain Sight](#3-the-persona-exposure--a-surveillance-stack-hiding-in-plain-sight)
4. [The 2025 Data Breach](#4-the-2025-data-breach)
5. [The Palantir / ICE Connection — Now Significantly Worse](#5-the-palantir--ice-connection--now-significantly-worse)
6. [DHS Subpoenas — Discord Named](#6-dhs-subpoenas--discord-named)
7. [Discord's Response — Delay, Not Reversal](#7-discords-response--delay-not-reversal)
8. [Impact on LGBTQIA+ Members Specifically](#8-impact-on-lgbtqia-members-specifically)
9. [Summary: The Threat Model](#9-summary-the-threat-model)
10. [Sources](#10-sources)

---

## 1. Purpose

This document summarizes the concrete, documented threats that Discord's recent policy changes and government entanglements pose to members of [The Alphabet Cartel](https://alphabetcartel.net). It is intended to inform staff and help communicate the urgency of our platform migration to the broader community.

These are not hypothetical risks. Every threat described below is active, documented, and has developed further since this assessment was first written in February 2026. This version reflects the state of affairs as of February 25, 2026.

The situation has materially worsened since the original assessment. Discord delayed its global age verification rollout in response to backlash — but the structural problems that made the original assessment urgent have not been resolved. They have, in several respects, become clearer and more alarming.

---

## 2. Mandatory Age Verification

### What Was Announced

In early February 2026, Discord announced that all users would be placed into a "teen-appropriate experience" by default. To escape restrictions — content filtering, limited DMs, no Stage channel access — flagged users would need to submit either a **facial scan** or a **government-issued photo ID** through a third-party verification vendor.

### The March Rollout Is Delayed — Not Cancelled

Following widespread backlash, Discord's co-founder and CTO Stanislav Vishnevskiy published a blog post on February 24, 2026 acknowledging that Discord had "missed the mark" and announcing a delay of the global rollout to the **second half of 2026**. Discord claims approximately 90% of users will not need to verify their age, as the platform's internal signals — account age, payment method on file, server membership patterns — can already determine most adult users automatically.

What Discord did not do: reverse the policy. The age verification rollout is still coming. The delay buys time. It does not eliminate the threat. Discord also explicitly stated it will continue meeting legal verification obligations in the UK, Australia, and Brazil in the interim.

### Why "Voluntary" Is Not Reassuring

Discord is not legally required to implement age verification globally. Other major platforms — including Reddit — have fought age verification legislation in court. Discord chose to build this infrastructure ahead of any mandate. The Electronic Frontier Foundation has stated there is "no reason for Discord to comply in advance" with laws that have not been passed or enforced against them.

The choice to build a biometric identity pipeline when not required to do so tells us something about the platform's direction of travel. The delay is a response to user revolt. The infrastructure intent remains unchanged.

---

## 3. The Persona Exposure — A Surveillance Stack Hiding in Plain Sight

This is the most significant new development since the original assessment and deserves detailed treatment.

### What Was Found

In February 2026, security researchers discovered that the frontend code for **Persona Identities, Inc.** — Discord's age verification vendor for a UK test — was **publicly accessible on the open internet**. Approximately **2,456 files** were found sitting on a US government-authorized server endpoint, specifically a **FedRAMP-authorized** (Federal Risk and Authorization Management Program) domain.

The exposure was reported independently by researcher "Celeste" (X: @vmfunc), covered by Malwarebytes, IBTimes, and Fortune, and confirmed before the files were removed.

### What the Exposed Code Revealed

This is where the story becomes significantly more alarming than the original Persona/Palantir investor link documented in v1.0.

The exposed files showed that Persona is not simply an age-checking tool. It is a comprehensive **Know Your Customer (KYC) and Anti-Money Laundering (AML) surveillance platform** that performs, among other things:

- **269 distinct verification checks** on each user
- **Facial recognition against watchlists** and lists of politically exposed persons (PEPs)
- **Adverse media screening** across 14 categories, including terrorism and espionage
- **Risk and similarity scoring** on submitted identities
- Selfie analytics including suspicious-entity detection, pose repeat detection, and age inconsistency flags
- **Data retention of up to three years** for IP addresses, browser fingerprints, device fingerprints, government ID numbers, phone numbers, names, and faces

Discord had told users that biometric data would not leave their device. UK users discovered a deleted disclaimer stating that their data would in fact leave their device and be stored for up to seven days. The Persona files indicated retention periods of **up to three years** — a direct contradiction of Discord's public reassurances.

### The FedRAMP Endpoint

The fact that Persona's exposed code sat on a **FedRAMP-authorized endpoint** is not incidental. FedRAMP is a US government program that authorizes cloud services for use by federal agencies. Persona's CEO Allen Song confirmed in an interview with Fortune that Persona is actively pursuing FedRAMP authorization — meaning Persona is building the compliance infrastructure to provide identity verification services directly to the US federal government.

Persona's own documentation and an independent investigation by The Rage (a financial surveillance publication) identified a domain — `withpersona-gov.com` — that may query identity verification requests connected to an OpenAI government database. Persona's COO denied any partnership with federal agencies including ICE or DHS. The files on a FedRAMP endpoint tell a more complicated story about where Persona's ambitions lie.

### Discord Ends Persona Partnership

Faced with this exposure, Discord confirmed it had ended its "limited test" of Persona. Both companies state the relationship lasted less than a month and involved a small test group in the UK. Discord's CTO described Persona as failing to meet the platform's privacy bar.

This is better than nothing. It does not change what the exposed code revealed about what Persona's system was doing to users who went through it, and it does not address the question of who Discord will use instead.

---

## 4. The 2025 Data Breach

In late 2024/early 2025, Discord disclosed that attackers had accessed a third-party vendor's systems used for age-related appeals, exposing approximately **70,000 users' government-issued ID photos** and associated sensitive personal data. Discord won the Electronic Frontier Foundation's 2025 "We Still Told You So" Breachies Award for this incident.

Discord has since switched to different vendors and states it no longer routes ID uploads through general support infrastructure. The breach is directly relevant to the current moment for two reasons:

First, it is the precedent against which Discord's new reassurances must be evaluated. The company has already demonstrated that highly sensitive identity data it collects can be compromised through vendor relationships. The current rollout creates the same class of risk through a new vendor pipeline.

Second, Discord's announcement of its global age verification rollout came **while users were still aware of this breach**. The trust deficit it created amplified the backlash to the February 2026 announcement significantly.

---

## 5. The Palantir / ICE Connection — Now Significantly Worse

The original assessment documented the investment relationship between Persona, Founders Fund (Peter Thiel's venture firm), and Palantir. That connection remains accurate. What has developed since then is that the Palantir/ICE relationship has expanded dramatically and become substantially more alarming.

### ImmigrationOS — A $30 Million Surveillance Platform

In April 2025, ICE awarded Palantir a **$30 million sole-source contract** to build a system called **ImmigrationOS** — an integrated surveillance platform for immigration enforcement. The contract runs through September 2027.

ImmigrationOS is built on top of ICE's existing Investigative Case Management (ICM) platform, which Palantir has operated for over a decade. Its three core functions:

1. **Targeting and enforcement prioritization**: AI-driven identification and apprehension of individuals flagged for removal
2. **Self-deportation tracking**: Near-real-time monitoring of whether individuals are voluntarily leaving the US
3. **Immigration lifecycle management**: End-to-end logistics from identification through removal

The system pulls data from across federal databases — passport records, Social Security files, IRS tax data, Medicaid records, DMV files, utility bills, court records, and license-plate reader data.

### ELITE — The Targeting App

A subsequent contract for **ELITE** (Enhanced Leads Identification & Targeting for Enforcement), part of the same $29.9 million contract framework, deploys a Palantir tool that functions, per its own documentation, like Google Maps populated with people instead of restaurants. ICE agents draw shapes on a map to identify "target-rich areas" for raids. Each person in the system has a dossier with their photo, address, and a **confidence score** predicting whether they are at that location — derived in part from Medicaid address updates and similar routine data submissions.

Former Palantir employees — 13 of them — signed a public letter in May 2025 condemning the ICE contracts, stating: "Companies are placating Trump's administration, suppressing dissent, and aligning with his xenophobic, sexist, and oligarchic agenda."

### The Stephen Miller / Palantir Conflict

The American Immigration Council has reported that **Stephen Miller** — the Trump administration's chief architect of immigration enforcement policy — holds a **substantial financial stake in Palantir**. The official most responsible for directing deportation policy has a direct personal financial interest in Palantir's government contract growth.

### The Chain of Custody, Updated

The chain documented in v1.0 has become significantly more concrete:

```
Discord age verification data
    → Persona (identity vendor)
        → Founders Fund (major investor in both Persona and Palantir)
            → Palantir
                → ImmigrationOS / ELITE (active ICE targeting infrastructure)
                    → Deportation targeting of individuals identified via AI surveillance
```

Palantir has received more than **$900 million in federal contracts** since Trump took office.

---

## 6. DHS Subpoenas — Discord Named

In the weeks following the original assessment, this situation has not improved. Multiple reports confirm that Google, Meta, Reddit, and Discord have received **hundreds of administrative subpoenas** from the Department of Homeland Security demanding identifying information about accounts that criticized ICE, reported ICE agent locations, or tracked immigration enforcement activity.

Administrative subpoenas require no judicial approval. DHS issues them directly. They were previously used primarily for serious criminal investigations — child trafficking, terrorism. They are now being used against people posting neighborhood watch alerts and political commentary.

IBTimes reported in February 2026 that at least three of the four platforms — Google, Meta, and Reddit — have complied with some of these requests. Discord has declined to publicly comment on whether it has complied.

The Alphabet Cartel is an LGBTQIA+ advocacy community. We discuss political issues. We have members who are immigrants or who advocate for immigrant communities. We are exactly the profile these subpoenas target. Member usernames, email addresses, IP logs, account creation data, and message metadata already exist on Discord's servers and are accessible via this mechanism.

---

## 7. Discord's Response — Delay, Not Reversal

Discord's CTO Stanislav Vishnevskiy published a blog post on February 24, 2026 outlining the following commitments:

- Global age verification rollout delayed to **second half of 2026**
- Persona partnership ended ("did not meet that bar")
- Vendor transparency: Discord will publish a list of verification vendors and their practices
- Additional verification options coming: credit card verification, on-device facial estimation
- Approximately 90% of users will not be required to verify

What Vishnevskiy also wrote: *"Many of you are worried that this is just another big tech company finding new ways to collect your personal data. That we're creating a problem to justify invasive solutions. I get that skepticism. It's earned, not just toward us, but toward the entire tech industry. But that's not what we're doing."*

The acknowledgment that the skepticism is earned is accurate. The reassurance that Discord is an exception to it is not something the available evidence supports. A platform that:

- Built a biometric identity pipeline before being legally required to
- Used a vendor (Persona) conducting 269 surveillance checks without disclosing this to users
- Allowed a vendor breach that exposed 70,000 users' government IDs
- Deleted a privacy disclaimer it had published
- Has not publicly addressed compliance with DHS subpoenas

...is asking users to extend trust it has not demonstrated it has earned. The delay changes the timeline. It does not change the structural situation.

---

## 8. Impact on LGBTQIA+ Members Specifically

The combination of mandatory facial age estimation, forced government ID submission, and the surveillance infrastructure connected to this pipeline creates specific, outsized harm for LGBTQIA+ individuals:

**Trans and nonbinary members** are disproportionately likely to be misidentified by facial age estimation tools, which are documented to perform poorly across gender-nonconforming presentations. Being flagged triggers the mandatory ID submission pathway — where the government ID may not match the member's presented identity, exposing them to discrimination and potential outing.

**Members who rely on pseudonymity** — including LGBTQ+ youth, survivors of abuse, people in unsupportive family or work environments, and those exploring identity — face a direct choice between submitting biometric data and government documentation to a corporation or losing full access to the community they depend on for support.

**Members with immigration concerns** — whether personally undocumented, mixed-status household members, or advocates — are directly in the crosshairs of the surveillance infrastructure Persona is being built to serve, and that Palantir's ImmigrationOS/ELITE system is actively operationalizing.

**Members engaged in political advocacy** — including any who have been vocal about immigration enforcement, trans rights legislation, or other advocacy topics — may have account data subject to government subpoena simply for expressing political opinions on a platform that has not publicly committed to resisting such requests.

The EFF has stated directly: no one should have to choose between accessing online communities and protecting their privacy. For an LGBTQIA+ community in the current political climate, this is not abstract. It is a material safety concern for specific, identifiable members of our community.

---

## 9. Summary: The Threat Model

The risks are not theoretical. They are documented, current, and active — and have materially worsened since February 20, 2026.

| Threat | Status | Impact |
|--------|--------|--------|
| Age verification rollout delayed to H2 2026 (not cancelled) | 🔴 Delayed, still coming | Biometric identity pipeline still the stated direction |
| Persona conducted 269 surveillance checks including watchlist screening | 🔴 Confirmed via code exposure | Far beyond "age check" — a full KYC/AML surveillance stack |
| Persona code sat on a FedRAMP-authorized US government endpoint | 🔴 Confirmed | Direct link between Discord's identity pipeline and federal infrastructure |
| 2025 breach of 70,000 users' government IDs | 🔴 Occurred | Demonstrated inability to secure this class of data |
| Persona funded by Founders Fund (Thiel) | 🔴 Confirmed | Investment connection to Palantir/ICE infrastructure |
| Palantir ImmigrationOS: $30M ICE targeting platform | 🔴 Active, contract through 2027 | AI-driven deportation targeting drawing on broad federal databases |
| Palantir ELITE: real-time location targeting tool used by ICE agents | 🔴 Active | "Google Maps for finding deportation targets" — fed by Medicaid, DMV, utility data |
| Stephen Miller financial stake in Palantir | 🔴 Confirmed | Policy architect has personal financial interest in contract growth |
| DHS subpoenas targeting political speech on Discord | 🔴 Active | Account metadata accessible without warrant; 3 of 4 platforms confirmed compliant |
| Facial estimation unreliable for trans/nonbinary members | 🔴 Documented | Disproportionate harm to our most vulnerable members |
| Discord's response: delay and rebranding, not structural reversal | 🟡 Ongoing | No evidence the underlying approach is changing |

We have made the right decision to move. The delay to H2 2026 does not change the calculus — it confirms that the platform we are migrating away from is still planning to build exactly what we assessed as unacceptable. Our community is on Fluxer. That is where we should be.

---

## 10. Sources

- [Discord Voluntarily Pushes Mandatory Age Verification Despite Recent Data Breach](https://www.eff.org/deeplinks/2026/02/discord-voluntarily-pushes-mandatory-age-verification-despite-recent-data-breach) — Electronic Frontier Foundation, February 12, 2026
- [Age verification vendor Persona left frontend exposed, researchers say](https://www.malwarebytes.com/blog/news/2026/02/age-verification-vendor-persona-left-frontend-exposed) — Malwarebytes, February 20, 2026
- [Hackers Expose Discord Age Verification System Issue After Persona Frontend Code Left Wide Open](https://www.ibtimes.co.uk/discord-age-verification-security-breach-1780591) — IBTimes UK, February 20, 2026
- [Discord distances itself from Peter Thiel–backed verification software after its code was found on a U.S. government server](https://fortune.com/2026/02/24/discord-peter-thiel-backed-persona-identity-verification-breach/) — Fortune, February 24, 2026
- [Discord delays its global age verification after upsetting almost everyone on Earth: 'We've made mistakes'](https://www.pcgamer.com/software/platforms/discord-delays-its-global-age-verification-rollout-and-cuts-ties-with-peter-thiel-backed-verification-vendor-after-upsetting-almost-everyone-on-earth-weve-made-mistakes/) — PC Gamer, February 24, 2026
- [Discord delays global rollout of age verification after backlash](https://techcrunch.com/2026/02/24/discord-delays-global-rollout-of-age-verification-after-backlash/) — TechCrunch, February 24, 2026
- [Discord Severs Persona Links After Peter Thiel-Backed Verification Software's US Surveillance Ties Are Revealed](https://www.ibtimes.co.uk/discord-cuts-ties-persona-surveillance-concerns-1781345) — IBTimes UK, February 24, 2026
- [US Department of Homeland Security has reportedly demanded personal information about ICE's critics from Discord, Reddit, Google, and Meta](https://www.pcgamer.com/software/platforms/us-department-of-homeland-security-has-reportedly-demanded-personal-information-about-ices-critics-from-discord-reddit-google-and-meta-and-at-least-3-of-those-platforms-have-complied/) — PC Gamer, February 17, 2026
- [DHS Sends Subpoenas to Google, Meta, Reddit, and Discord to Identify Americans Who Criticize ICE](https://www.nytimes.com/2026/02/13/technology/dhs-anti-ice-social-media.html) — New York Times, February 13, 2026
- [ICE to Use ImmigrationOS by Palantir, a New AI System, to Track Immigrants' Movements](https://www.americanimmigrationcouncil.org/blog/ice-immigrationos-palantir-ai-track-immigrants/) — American Immigration Council, 2025
- [Palantir's ELITE App: "Kind of Like Google Maps" for Finding Deportation Targets](https://stateofsurveillance.org/news/palantir-elite-ice-targeting-app-confidence-scores-2026/) — State of Surveillance, January 2026
- [Discord faces backlash over age checks after data breach exposed 70,000 IDs](https://arstechnica.com/tech-policy/2026/02/discord-faces-backlash-over-age-checks-after-data-breach-exposed-70000-ids/) — Ars Technica, February 2026
- [Discord is rolling out facial scanning and ID checks globally in March](https://www.pcgamer.com/games/discord-is-rolling-out-facial-scanning-and-id-checks-in-march-for-everyone-who-doesnt-want-to-be-locked-into-a-teen-appropriate-experience/) — PC Gamer, 2026

---

**Built with care for chosen family** 🏳️‍🌈
