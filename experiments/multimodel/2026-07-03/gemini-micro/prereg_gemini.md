# Gemini micro-arm preregistration — the transfer test under a 20-requests/day/model quota

Fixed 2026-07-03, before any gemini-micro API call.

## Constraint and design

The provided GEMINI key is free-tier: every model bucket is independently capped at 20 requests/day. A full arm (360 calls) is infeasible; a *stratified reader test* is not. Design: Gemini-family models act as **answerers** on the grok compressor's cached v5 summaries (grok is an applicable compressor: 22 lost / 8 retained DENIED cells). Fixed stratified sample, chosen by seeded RNG before running: **12 lost + 8 retained = 20 items**. Each probe channel is assigned to its own Gemini model bucket, 20 calls each:

| channel | primary bucket | fallback order |
|---|---|---|
| WHICH | gemini-3-flash-preview | gemini-3.1-flash-lite, gemini-2.5-pro, gemini-3-pro-preview |
| WHICH-ABSTAIN | gemini-3.1-flash-lite | gemini-3-flash-preview, gemini-2.5-pro, gemini-3-pro-preview |
| DECISION | gemini-2.5-pro | gemini-3-pro-preview, gemini-3-flash-preview, gemini-3.1-flash-lite |

A channel runs entirely within one bucket (no mixing models within a channel); if a bucket 429s mid-channel, the channel restarts in the next fallback bucket and the partial calls are discarded from scoring (logged). Temperature 0; thinking disabled where the API allows; max 800 output tokens. Hard cap: 100 calls total.

## Preregistered predictions (thresholds set for the small n; Wilson CIs reported)

- **P-G1 (debt transfers to Gemini readers)**: `which_lost ≤ 1/3` (n=12) AND `which_retained ≥ 0.7` (n=8).
- **P-G2 (abstention detects debt for Gemini readers)**: `abstain_lost ≥ 0.5` AND `abstain_retained ≤ 0.25`.
- **P-G3 (the verdict shelf transfers to Gemini readers)**: `decision_lost ≥ 0.6`.

These extend transfer P-T1/P-D/P-T2 to a fourth model family. Each is evaluated on whichever single bucket completed its channel. Interpretation fixed in advance: pass ⇒ the artifact-borne-debt result covers all four provided vendors; fail ⇒ a Gemini reader extracts witness signal other families cannot (would refute representation-independence) or refuses the verdict (would bound the shelf's universality). Either way it is reported.

## Exploratory

Incoherence/confabulation rates per channel; cross-bucket consistency; anything else post-hoc.

## Cost

Free tier: $0.00 by construction (that is the maximum the provided key permits); calls and tokens logged as usual.
