# Sections — the fail-direction fingerprint (2026-07-09)

## VERDICT (confirmatory run, frozen prereg 976526b): NOT upheld as frozen — 1/3, 1/3, 1/3 —
## and the failure is a discovery: the section is (model × artifact-type)-indexed.

Surgical-ablation run (360 items × 2 sides × 3 models, 5,040 calls, $3.65):

| model | surgical section | strength | domain range | prior gap (P-SEC-2) | held-out sign-hit | sv1 margin | compression transfer (3c) | realdoc transfer (3b) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| haiku | DENIED | 0.919 | 0.233 ✓ | 0.191 ✗ | **0.961 ✓** | 0.92 ✓ | **0.943** | **1.000** (30/30) |
| gpt | DENIED | 0.794 | 0.317 ✗ | 0.078 ✗ | 0.792 ✗ (by 0.008) | 0.58 ✓ | **0.952** | **1.000** (30/30) |
| grok | **APPROVED** | 0.808 | 0.417 ✗ | 0.808 ✓ | 0.833 | 0.00 ✗ | **0.229** | — |

- **The discovery inside the refutation: grok's default FLIPPED SIGN across artifact types.**
  Prior always-DENY; compression-lost cells deny-leaning (cached); surgical deletion →
  APPROVE at 0.81. Mechanism (readable off the design): surgical removal leaves a clean
  document whose visible policy evidence all passes → closed-world reading approves;
  compression leaves a visibly mutilated gist → suspicion denies. The section is conditioned
  on *how the evidence died*, so "one fingerprint per model" is REFUTED; the object that
  survives is a fingerprint per (model, mutilation-type) pair. grok's 3c transfer (0.229 —
  its surgical section anti-predicts its compression failures) quantifies the flip.
- **haiku is the clean D1 exemplar:** artifact-type-invariant fail-closed section
  (surgical 0.92 / compression 0.94 transfer / realdoc 1.00), stable across domains,
  perturbation-stable, held-out sign-hit 0.961 with the full 0.92 cross-model margin. gpt is
  directionally identical but misses three frozen thresholds narrowly (hit 0.792 vs 0.80;
  range 0.317 vs 0.25; conditionality gap 0.078 — its prior parses deny-ish here with 48%
  hedges, shrinking the measured gap).
- **P-SEC-1d sensitivity annex: PASS 3/3** — section signs agree between the official
  `retained()` definition and the numeric-containment variant (grok 0.330/0.257, haiku
  0.094/0.088, gpt 0.065/0.063). The fresh-eyes haiku ~0.31 is reproduced by *neither*
  definition and stays unexplained (likely a different cell conditioning).
- **Design lessons recorded:** (i) the truth-marginal null EQUALS the sign-hit for any
  constant-section forecaster by construction — it is uninformative exactly where the section
  is strong; the sv1 cross-model margin did the real discriminating work. (ii) the sv1
  comparator cannot discriminate approve-leaning models (grok margin 0 is definitional, not
  evidential); the successor needs a deny-leaning AND an approve-leaning reference section.
- Abstention offered changes everything: with an explicit INSUFFICIENT_EVIDENCE option,
  haiku abstains 0.88 and gpt 0.91 on ablated cells (grok 0.07) — the section is a
  *forced-choice* object; the deployable failure mode is systems that don't offer the out.

Run: `gen_items.py` → `runner.py run --model all` → `runner.py score` + `score_cached.py`.
Artifacts: `items.jsonl`, `responses_raw.jsonl`, `sections_results.json`,
`sections_cached_annex.json`. Cost: $3.65 API, $0 GPU.

---

## Original exploratory reanalysis (pre-freeze, 2026-07-09)

**Status: EXPLORATORY — no new API calls, no prereg yet.** Reanalysis of cached responses
(domain battery 2026-07-06; distill-parity delta battery 2026-07-08) prompted by a fresh-eyes
audit: *evidence absence never produces noise in this program's data — it produces systematic
verdicts.* Formal frame: compaction is a quotient map; on a collapsed fiber the reader emits a
learned default representative (**a section**), not "unknown". Debt is information *replaced*,
not just lost. Run `python3 reanalysis_sections.py` (deterministic, $0).

## Numbers (self-compressed artifacts; scent, not a row)

| model | DENIED-lost → approve | APPROVED-lost → deny | no-notes prior (approve, strict-anchored) | unanchored (hedge) share |
|---|---:|---:|---:|---:|
| gpt | 0.065 | 0.858 | 0.193 | 0.333 |
| haiku | 0.092 | 0.859 | 0.217 | 0.000 |
| grok | 0.330 | 0.661 | 0.000 | 0.000 |
| teacher Qwen3-8B | 0.404 | 0.562 | 0.765 | 0.837 |
| Student-V | 0.989 | **0.005** | 1.000 | 0.000 |
| Student-J | 0.820 | 0.161 | 0.986 | 0.756 |

Control cells (evidence present) approve/deny error rates are ≤ 0.05 for the frontier panel —
the section is invisible until evidence is destroyed.

## What the two added kill-checks show

1. **APPROVED-side ablation (fiber-filling vs generic conservatism):** gpt/haiku emit DENIED
   on *both* sides under evidence loss (0.86–0.94 DENIED regardless of truth) — a constant
   **fail-closed section**, directionally predictable. Student-V is the mirror: **fail-open on
   both sides** (approve 0.99 / deny 0.005). Not noise, not content-dependent filling: a
   per-model constant default.
2. **Section vs prior (is this just the bias shelf, rows 8/25?):** No — the taxonomy splits.
   *Conditional-section* models (gpt, haiku): hedgy or mild no-notes priors but decisive
   mutilation-triggered fail-closed behavior — the section only exists in the presence of an
   evidence-bearing-but-mutilated context. *Collapsed-prior* models (grok always-DENY;
   Student-V always-APPROVE): section ≈ degenerate prior pulled back — the known bias shelf.
   The 2-coordinate fingerprint (prior, section) — plus the hedge share as a third coordinate —
   distinguishes routes the ledger previously conflated.
3. **The section is trainable and sign-flippable by trace content alone:** verdict-only SFT
   turned a weak fail-closed teacher (0.40/0.56) into a hard fail-open student (0.99/0.005)
   with a degenerate always-approve prior — despite 50/50-balanced training data. Trace
   content sets the section. And Student-J reveals a **third route: the domain-shrunk
   section** — anchored on lost DENIED cells J approves at 0.82, the *same sign* as V, just
   softer, while routing ~76% of its no-evidence probability mass to the hedge channel.
   J-training didn't flip the section's sign; it shrank the section's *domain* (rerouted mass
   to abstention) and left the anchored default approve-leaning. Sign-flip (V) and
   domain-shrink (J) are different levers, and only the second is what calibration training
   should buy.

## Caveats (why this is a scent)

Self-compressed artifacts (lost cells conditioned on each model's own summaries); no
perturbation-stability arm; strict-anchor prior parse leaves 33–84% of some models' no-notes
responses unanchored (hedges — counted, not binned); the fresh-eyes haiku figure (~0.31) did
NOT reproduce under the standard lost-cell definition (we get 0.092) — definition sensitivity
is itself something the prereg must pin.

## Proposed confirmatory design (to prereg before any spend — sketch, not frozen)

Surgical-ablation corpus (delete the deciding sentence(s); no compressor — isolates the
reader's section from compaction noise and the self-compression confound), both verdict sides,
6 domains × 2 sides × ~50 items; perturbation arms (paraphrase + parameter-order shuffle) on a
subset; strict-anchored scoring with hedge shares surfaced. Predictions to freeze:

- **P-SEC-1 (existence/stability):** per frontier model, ablated-cell verdict bias ≥ 0.25 from
  coin, cross-domain spread ≤ 0.25, perturbation shift ≤ 0.10.
- **P-SEC-2 (conditionality — the anti-bias-shelf kill test):** |section − anchored prior|
  large for ≥ 2/3 frontier models; if not, D1 collapses into rows 8/25 and is reported dead.
- **P-SEC-3 (directional forecast — the money claim):** section measured on 3 domains predicts
  the *sign* of ≥ 80% of wrong answers on evidence-lost cells in 3 held-out domains + the
  cached realdoc and Arm-3b corpora (mostly reanalysis).
- **P-SEC-4 (two-route taxonomy):** grok/Student-V section ≈ own prior; gpt/haiku section ≠
  prior — preregistered per-model.

Est. cost: ~$4–6 API + $0 GPU (students scored from cache/local adapters). Theory-facing
follow-up (separate micro-design): the adaptedness/martingale frame — slide the evidence
position through the emission order and test whether verdict accuracy tracks measurability;
the already-queued forced-CoT probe on Student-V doubles as the test of whether its adapted
part still exists.
