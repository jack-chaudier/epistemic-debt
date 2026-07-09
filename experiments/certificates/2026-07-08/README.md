# B1 — Certificate-Compaction Pilot (2026-07-08)

**Question.** The Honesty Theorem exact check (`proofs/honesty_theorem.py`, RESULTS row 13) found
that **certificate honesty admits a strictly cheaper state than exact-witness honesty** on the Q
families (answer/certificate/joint states 5/6/7, 6/7/8, **7/9/13** on `Q_(5,3)`): to answer
honestly you need only enough to *certify* the answer, not the full witness set. Does that
advantage have an LLM analog — does a **claim + minimal certificate + pointer** summary license
calibrated reader behaviour (verdict + reason-naming + abstention) at **fewer realized words**
than value-dense compaction, which stores the whole witness set?

**Design.** Four compaction arms at a matched **15-word nominal budget** (the shelf regime), same
90-item corpus (3 confound-guarded domains × 30, 45 DENIED; selfcheck 0 problems), same probes
(compress → decision → WHICH → WHICH-abstain, last-`PARAMETER:` parser) + a nonotes prior. All
predictions frozen in `prereg_certificates.md` before the full run.

- **ctrl** — contract-blind plain compaction (policy-blind).
- **vd** — H.2 value-dense (names+numbers+units), policy-blind. The deployed value-dense baseline.
- **vda** — value-dense, **policy-aware** writer. Matched-access control (store the whole witness
  set / joint quotient) — isolates *format* from *policy access*.
- **cert** — **policy-aware** certificate: verdict + single deciding value + pointer (the
  certificate quotient — store the deciding value + a pointer, not the set).

Models: grok (`grok-4-1-fast-non-reasoning`), haiku (`claude-haiku-4-5`), gpt (`gpt-4.1-mini`),
temperature 0, idempotent cache, hard cap 3000/model. Candidates disclosed (deployed behaviour).

## Results

decD/whichD = decision/WHICH accuracy on the 45 DENIED. **S** = failing-value survival on DENIED.
**J** = justified accuracy (decision ∧ WHICH correct, DENIED-only). **Δ** = decD − whichD. **rlzW**
= mean realized words. **#val** = mean numeric readings kept. appNONE/appFA = on APPROVED items,
the WHICH-abstain reader says NONE (correct) / INSUFFICIENT_EVIDENCE (false-abstain).

| model | arm | decD | whichD | S | J | Δ | rlzW | #val | appNONE | appFA |
|---|---|---|---|---|---|---|---|---|---|---|
| grok | ctrl | 0.889 | 0.422 | 0.778 | 0.422 | 0.467 | 26.6 | 9.2 | 0.578 | 0.133 |
| grok | vd   | 0.911 | 0.556 | 0.933 | 0.533 | 0.356 | 29.9 | 11.2 | 0.733 | 0.111 |
| grok | vda  | 1.000 | 0.733 | 1.000 | 0.733 | 0.267 | **10.1** | 3.1 | 1.000 | 0.000 |
| grok | **cert** | 1.000 | 0.956 | 0.956 | **0.956** | 0.044 | 15.9 | 2.0 | 0.222 | 0.333 |
| haiku | ctrl | 0.889 | 0.533 | 0.489 | 0.511 | 0.356 | 27.3 | 5.9 | 0.178 | 0.733 |
| haiku | vd   | 1.000 | 0.778 | 0.911 | 0.778 | 0.222 | 34.6 | 10.3 | 0.422 | 0.489 |
| haiku | vda  | 1.000 | 0.933 | 1.000 | 0.933 | 0.067 | 15.4 | 3.2 | 0.933 | 0.000 |
| haiku | **cert** | 1.000 | 0.978 | 0.978 | **0.978** | 0.022 | **13.9** | 1.0 | 0.756 | 0.222 |
| gpt | ctrl | 1.000 | 0.467 | 0.556 | 0.467 | 0.533 | 23.8 | 5.9 | 0.378 | 0.356 |
| gpt | vd   | 1.000 | 0.889 | 1.000 | 0.889 | 0.111 | 38.3 | 12.4 | 0.978 | 0.000 |
| gpt | vda  | 1.000 | 0.933 | 1.000 | 0.933 | 0.067 | **12.3** | 3.1 | 1.000 | 0.000 |
| gpt | **cert** | 1.000 | 0.978 | 1.000 | **0.978** | 0.022 | 13.6 | 1.1 | 0.978 | 0.000 |

Three robust patterns:
- **Certificate has the best justified accuracy of any arm on every model** (J = 0.956 / 0.978 /
  0.978) and collapses the answer/justification gap (Δ ≤ 0.044) — the DENIED side transfers cleanly.
- **vda (policy-aware value-dense) is the *terse* arm** (10–15 words) — a writer that holds the
  policy keeps only the 3 policy readings (name+number+unit ≈ 9–12 words) and no prose. The
  certificate is 14–16 words: its verdict word + `vs threshold` + `other readings not included —
  see source` pointer is a **fixed prose overhead** that costs more than the 2 extra readings vda
  keeps. So the certificate quotient's "1 value < 3 values" storage win **inverts in realized
  words** on grok/gpt.
- **The APPROVED side is the theory's hard side and it strains** (appNONE/appFA): the value-free
  "all criteria met" certificate has no cheap single-object witness, so grok's *writer* false-denies
  passing items (appNONE 0.22, confab 0.44) and haiku's *reader* over-abstains (appFA 0.22); only
  gpt handles it cleanly (appNONE 0.978).

Side note: `cert` eliminates grok's WHICH abbreviation-parser artifact (UNMATCHED on DENIED: ctrl
12, vd 17, vda 12, **cert 0**) — the certificate names the failing parameter in full, so the parser
never mis-hits an acronym.

## Prediction scorecard (pass/fail)

| | grok | haiku | gpt |
|---|---|---|---|
| P-CE-1 certificate quotient (cert J ≥ vda J−.05 at **fewer** words) | **FAIL** | PASS | **FAIL** |
| P-CE-1b vs blind value-dense (cert J ≥ vd J−.05 at ≤ words) | PASS | PASS | PASS |
| P-CE-2 abstention calibrated on APPROVED (appFA ≤ .10, appNONE ≥ .90) | **FAIL**¹ | **FAIL**² | PASS |
| P-CE-3 beats control on J by ≥ .20 (shelf regime) | PASS | PASS | PASS |
| P-CE-4 word economy (cert rlzW ≤ vd **and** vda) | **FAIL** | PASS | **FAIL** |

¹ grok: certificate *writer* false-denies passing items (approved confab 0.44). ² haiku:
certificate *reader* over-abstains on the value-free approval certificate (appFA 0.22).

## Verdict

**The certificate quotient PARTIALLY transfers — its justified-accuracy dominance is real, but its
matched-budget economy is REFUTED, and the approved side breaks calibration.**

- **DENIED side, strong positive (P-CE-1b 3/3, P-CE-3 3/3):** certificate compaction gives the
  highest justified accuracy of any arm (J 0.956–0.978), beats naive compaction by +0.47 to +0.53,
  and beats *blind* value-dense at less than half the realized words (14–16 vs 30–38). Where the
  reader gets a certificate, one deciding value + verdict is a near-perfect DENIED-side summary.
- **Economy claim REFUTED at matched access (P-CE-1 1/3, P-CE-4 1/3):** against a policy-aware
  value-dense writer, the certificate is *not* cheaper on grok/gpt. A cooperative writer that just
  lists the 3 policy readings (10–12 words) beats the certificate's verdict-claim + `vs threshold`
  + pointer scaffolding (14–16 words). The 9-vs-13-states advantage assumes unit-cost states; in
  realized words the certificate pays a fixed linguistic overhead it cannot shed. This is the
  signpost-fusion lesson again — a prose register buys behaviour with words.
- **APPROVED-side asymmetry (P-CE-2 2/3 fail), as the theory predicts:** certificate honesty is
  cheap on the certifiable side (DENIED — one failing reading certifies denial) but the
  universally-quantified side (APPROVED — *all* criteria met) has no cheap single-object
  certificate. The value-free approval certificate therefore either makes the reader over-abstain
  (haiku) or shifts decision risk onto the writer, who false-denies (grok). gpt alone certifies
  approval accurately. The certificate quotient's feasible/infeasible asymmetry from
  `honesty_theorem.py` transfers to reader/writer behaviour.

Net: the certificate is an excellent *DENIED-side* compaction (best J, gap-free, parser-clean, far
cheaper than blind value-dense) but is **not** a free lunch — a policy-aware value-dense writer is
already terser, and the approved side needs either a trusted writer (gpt) or the values after all.
The honest deployable lesson: **certificate compaction concentrates decision risk at the writer**;
its economy over value-dense is an accounting artifact once you pay for the pointer in real words.

## Confounds found / handled

1. **Policy access is a design axis, not a nuisance.** A certificate must name the *deciding*
   reading, so `cert`/`vda` are policy-aware and `ctrl`/`vd` blind. P-CE-1 (certificate quotient)
   is scored at *matched* access (cert vs vda); P-CE-1b reports the cert-vs-blind-vd literal. The
   matched-access `vda` arm is what refuted the economy claim — without it, cert-vs-blind-vd
   (P-CE-1b) would have falsely "confirmed" the quotient.
2. **Certificate writer accuracy is intrinsic, not a bug.** On APPROVED items the certificate bakes
   the verdict at write-time; a writer miscomputation propagates a confident false verdict (grok/gpt
   false-denied ops-004, reserve margin 76.53 ≥ 74 min, in smoke). Value-dense defers the verdict to
   read-time where the values are present. Reported as the theory's asymmetry, not tuned away.
3. **WHICH abbreviation-parser artifact (#2), grok.** Acronym readings → UNMATCHED on the blind
   arms (ctrl 12, vd 17); the certificate format incidentally fixes it (cert UNMATCHED 0). grok's
   blind-arm whichD is deflated by the parser and reported but flagged; haiku/gpt are clean.
4. **Candidate-set disclosure (#3).** policy_text discloses the 3 candidates (deployed-behaviour
   choice); identical across all four arms, cannot manufacture a between-arm contrast.
5. **Concurrent-writer divergence (this run).** Backgrounded runs were reaped and relaunched across
   turns; overlapping processes co-wrote `responses_raw.jsonl`, leaving 692 divergent duplicate keys
   (temp-0 sampling jitter). Resolved by keeping the first occurrence per key (deterministic, file
   order preserved) and re-verified 0 dup / 0 divergence. **Robustness check: scoring keep-first vs
   keep-last flips 0 / 15 predictions** — the incident does not affect any reported outcome. Raw
   pre-dedup file preserved out-of-tree.

## Cost

$1.58 total (grok $0.15, haiku $1.18, gpt $0.25) over 4,590 calls. Well under the $6 cap.

## Proposed ledger row

> | 2026-07-08 | **Certificate-compaction pilot (B1)**: the exact certificate-quotient advantage
> (honesty_theorem.py, 9 vs 13 states) only PARTIALLY transfers to LLM readers. A policy-aware
> `claim + deciding-value + pointer` certificate gives the **best justified accuracy of any arm**
> (J 0.956/0.978/0.978 on grok/haiku/gpt), a gap-free Δ ≤ 0.04, and beats *blind* value-dense at <½
> the realized words (14–16 vs 30–38; P-CE-1b, P-CE-3 3/3). But the **matched-budget economy is
> REFUTED** (P-CE-1, P-CE-4 1/3): against a policy-aware value-dense writer that just lists the 3
> policy readings (10–12 words), the certificate's verdict + `vs threshold` + pointer scaffolding is
> *longer* (14–16 words) on grok/gpt — the 9-vs-13 storage win inverts once the pointer is paid for
> in real words. The APPROVED side (no cheap single-object certificate) breaks calibration (P-CE-2
> 2/3 fail): grok's writer false-denies passing items, haiku's reader over-abstains; only gpt
> certifies approval cleanly. Certificate compaction concentrates decision risk at the writer. |
> PREREGISTERED (P-CE-1…4 frozen; 3 models × 4 arms × 90 items; $1.58) |
> [certificate campaign](.) |

## Files

`gen_items.py` · `items.jsonl` (90) · `prereg_certificates.md` · `runner.py` (smoke/run/score) ·
`responses_raw.jsonl` (deduped) · `scored.csv` (1080 rows) · `certificate_results.json` · this README.
