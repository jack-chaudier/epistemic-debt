# gemini-micro — PARTIAL (2 of 3 preregistered predictions confirmed; free-tier quota)

Design: [prereg_gemini.md](prereg_gemini.md) — a stratified reader test that fits the Gemini free-tier 20-req/day/model quota by assigning one probe channel per model bucket over a fixed 12-lost + 8-retained sample of grok's v5 summaries.

**Outcome.** Before the user paused Gemini use, two channels completed in full (20/20 items each, both landed in **gemini-3.1-flash-lite** after the `which` channel's first bucket hit its daily cap at call 10 and fell back per the preregistered order). The `decision` channel never ran. Scoring the two completed channels (spends nothing — data already collected):

| prediction | cell | result |
|---|---|---|
| **P-G1** debt transfers to a Gemini reader | which-lost 3/12 (0.25), which-retained 8/8 | **PASS** |
| **P-G2** abstention detects debt for a Gemini reader | abstain-lost 11/12 (0.92), abstain-retained 0/8 | **PASS** |
| P-G3 verdict shelf transfers | — | not run (decision channel unstarted) |

So the artifact-borne-debt result (transfer P-T1/P-D) extends to a **fourth vendor family**: on grok's witness-destroyed summaries, gemini-3.1-flash-lite names the lost reason at guessing (3/12) while naming every retained reason (8/8), and abstains almost exclusively on the lost cell. The 50 Gemini calls cost $0.00 (free tier). P-G3 and the full 360-call arms remain available when a billed key exists (spawned follow-up task; runners resume idempotently).
