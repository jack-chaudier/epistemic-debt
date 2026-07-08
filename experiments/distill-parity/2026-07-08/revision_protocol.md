# J-prompt revision protocol (frozen on commit, BEFORE any probe run)

Bounds set by the lead 2026-07-08 after the G3 STOP (1,586 < 3,000): the teacher prompt is
instrumentation, not a prereg item, but instrumentation tuned while staring at the gate metric
needs its own freeze — otherwise the J-condition is optimized and the V-condition is not.

## Rules

1. **Maximum two J-prompt revisions.** Each is committed (full text) before its probe runs.
2. **Fixed probe slice:** `probe_slice.jsonl` = 500 items (250 APPROVED / 250 DENIED), seeded
   sample (seed 813000) of the G2-kept 5 domains of `train_pool.jsonl`; disjoint from every
   eval set (the whole train pool already is). The same slice evaluates every revision.
3. **Proceed threshold, decided before any revised number is seen:** probe DENIED
   joint-survival ≥ 0.55, where joint-survival = the full G3 conjunction (cached bare-ANSWER
   verdict correct AND revised-J verdict correct AND named witness correct). The bare-verdict
   channel comes from the already-committed `teacher_raw.jsonl` (V prompt unchanged).
4. **On pass:** regenerate the pool at 5 kept domains × 1,900 (= 9,500 items), fresh raw file
   `teacher_raw_r1.jsonl` (never reuse the old cache across a prompt change), rebuild gates,
   re-run the G1 leak audit on the extended pool.
5. **On two misses:** fall back to option A (scale only, original J prompt), with the
   justification-interference disclosed as a teacher-capability fact.

## G3 definition (pinned; unchanged from the failed run)

An item survives iff **bare-ANSWER verdict correct AND J-response verdict correct AND named
deciding witness correct** — the conjunction. V-traces are built from the bare channel,
J-traces from the J channel. Per-channel DENIED rates in the failed run: bare 0.784,
J-response 0.427. Disclosure: the shared item set is conditioned on BOTH channels' teacher
competence, per-channel rates stated in the writeup.

## Revision 1 (this commit) — verdict-after-evidence ordering

Rationale: the dominant G3 failure is comparison inversion inside the fused clause (teacher
asserts APPROVED while quoting a reading that violates the threshold). Revision 1 forces the
reading to be quoted before the comparison and moves the verdict to a terminal DECISION: line.
Register change disclosed: this is mild verdict-after-evidence scaffolding — the J-loss now
pays for evidence-ordered justification, a superset of the row-30 fusion register.

Parser note (confound-checklist #2): the J verdict is parsed by a NEW last-anchor rule —
last `DECISION:` (colon required) — because the scaffold body may legitimately contain
APPROVED/DENIED tokens mid-justification. PARAMETER: stays last-anchor. Both parsers are in
`trace_builder.py`; the V channel parser (ANS_RE on `ANSWER:`) is unchanged.

Full revised request text (byte-identical constant `TEACHER_J_R1` in runner.py and `J_REQ_R1`
in trace_builder.py):

> For each policy parameter, quote its observed reading from the case file next to its policy
> threshold and state whether it passes or fails — never assert any conclusion without the
> deciding reading in the same clause. If a needed reading is absent from the file, write
> [MISSING DATA] and name what is missing. Then end with exactly two lines:
> DECISION: APPROVED or DECISION: DENIED
> PARAMETER: <the single failing parameter name> or PARAMETER: NONE

## Revision 2 (reserved; text to be committed before its probe if revision 1 misses)

Not written. If needed, it will be committed here before running.

## Cost

Probe: 500 J-calls ≈ 2 GPU-minutes. Regeneration on pass: ~19,000 calls ≈ $1–2.
