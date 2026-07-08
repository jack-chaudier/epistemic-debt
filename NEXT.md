# NEXT — live scratchpad: next steps, open questions, ideas

Agent- and human-facing. Read this before proposing new work; append to it when a run or a
re-analysis surfaces something worth chasing. Conventions:

- **Queue entries** carry: what / why (which fear or law it addresses) / design sketch / est.
  cost / status. Move an entry to *done* (with the artifact link) rather than deleting it.
- **Ideas** are cheap to add and carry no obligation — date them, one paragraph max.
- This file is a map, not a ledger. Claims live in `results/RESULTS.md` with evidence labels;
  nothing here is citable. Preregister before spending (see CLAUDE.md).
- Current shared infrastructure for new campaigns: `experiments/lib/domains.py` (6
  confound-guarded generators + mechanical selfcheck) and `experiments/lib/dissociation.py`
  (protocol, corrected parser, Wilson CIs, idempotent cache). Copy the highpower/domains
  campaign shape: `gen_items.py` + `prereg_*.md` + `runner.py` (smoke/run/score) + README
  verdict + a regression test pinning the headline numbers.

## Queue (ranked by leverage per dollar)

1. **Semantic-judge WHICH re-score of the Tier 1+2 cached responses.** (~$0.50, no new
   compression calls.) Retires the abbreviation parser artifact that decided grok's P-D3
   (LVEF/SBP acronyms → UNMATCHED — third scoring-regex incident), applies the
   NONE_NO_FAILURE / NONE_MISSING_DATA split at scale (n≈900 lost-cell responses vs the
   original 19–28), and measures elimination-vs-retrieval per domain directly. Pattern exists:
   `experiments/rescore/2026-07-06/judge.py` (dual judge, adjudication file, agreement bar).
   Status: **ready to build**.
2. **Reader inference boundary — DONE, and it REFUTED the depth-1 hypothesis.** The hypothesis
   was "recovery = one-step elimination, nothing deeper — no arithmetic." It is **false**: all 3
   models deploy one `base±offset` arithmetic step to recover the lost witness (recovery 0.65/
   0.65/0.93; confirmatory c2 with the base-only leak forced to 0 upholds it, 0.65/0.73/0.98).
   → `experiments/reader-inference-boundary/2026-07-08/` (README rows 28; RESULTS 2026-07-08).
   **Successor (the boundary must be deeper):** the depth-1 arithmetic step is deployed, so the
   real question is where computation *stops*. Design a depth ladder — 1 step (done), 2 chained
   steps (a = total − b − c, needing two prior resolutions), a multiplication/ratio step, and a
   2-hop dependency (resolve X to know which of Y/Z is the candidate). Prereg a monotone
   recovery decay with depth and locate the per-model half-depth. If depth is model-ordered and
   stable, "read-time inference depth" is the α-generating constant (a model-card axis). Also:
   candidate-HIDDEN variants of each class (the I.3 artifact-content quantity vs deployed J).
   (~$2–4, probe calls only.) Status: **ready to build on the same harness.**
3. **Gist–witness allocation frontier — first quantitative curve test.** Every confirmed
   result so far is directional; the vendored exact machinery
   (`proofs/vendor/exact_pareto_frontier.py`) predicts an actual *curve*. H.2 already observed
   the trade empirically (grok value-only notes: retention up, decision accuracy 0.68→0.53 —
   witness density starves the gist channel). Design: sweep compaction instructions across the
   gist↔values allocation at fixed *realized* budget (5–7 allocation points × 2 models), plot
   achieved (decision accuracy, witness retention) pairs against the exact frontier; prereg
   whether readers sit on it, below it by a roughly constant factor, or violate its shape —
   any outcome is a result. Also gives P-D2's gist channel its formal slot: gist = a noisy
   verdict token competing for the same budget as witnesses. Moves the program from "theory
   predicts signs" to "theory predicts curves." (~$3–5.) Status: design sketch.
4. **Gist-belief follow-up (the P-D2 discovery).** Why does grok trust its own false-nominal
   gist over its always-DENY prior while gpt/haiku hold the verdict? Design: same corpora,
   probe the *decision* channel with (a) summaries stripped of gist adjectives ("nominal",
   "no issues"), (b) gist-only summaries (no values), (c) the manifest `OMITTED:` line —
   isolate whether the flip is driven by asserted-normality tokens. This is a new failure
   mode (compaction manufacturing a wrong answer with a reassuring gist); it deserves its own
   named result. (~$3.) Status: design sketch only.
5. **Fresh preregistered loss-ledger router run.** The row-21 result (recall 1.00, 30/30) is
   OBSERVED on cached data with a simulated ledger. Real version: compactor emits dropped
   value-*names* out-of-band; router intersects ledger with the query's policy; include a
   debt-rare corpus arm for the token-economics story P-D3(routing) left open. (~$3.)
   Status: mechanism validated, needs the honest run.
6. **Law 3 / distillation kill-shot — the headline gap.** Teacher–student ladders that exist
   in the market (gpt-4.1→mini→nano; gemini flash→flash-lite; sonnet→haiku): match on standard
   items, diverge on counterfactual re-queries; prediction: witness fidelity falls before
   accuracy, students degrade disproportionately. A cached-summary pilot now shows strong
   witness-conditioned transfer localization but fails the original-accuracy guard (README row 27), so
   the next run must first match ordinary accuracy using value-dense or looser-budget source
   artifacts. (~$10–20.) Status: **pilot complete; full kill-shot still open**.
   **2026-07-08 upgrade — controlled distillation-parity run (RunPod):** replace the market
   ladder with two students QLoRA-distilled from the same Qwen3-8B teacher on identical items,
   differing only in trace content (verdict-only vs verdict+witness fusion register); engineer
   benchmark parity, prereg Δ separation + Δ-predicts-shift-failure + calibration curve, with
   the honest negative-result branch. Full design, budget (~$30–50 GPU, ~$0 API), and RunPod
   runbook → `experiments/distill-parity/2026-07-08/PLAN.md`. Design-reviewed 2026-07-08
   (weight-borne vs artifact-borne shift arms split; DPI prediction moved to WHICH-lost;
   surface-leak audit added); prereg drafted alongside (`prereg_distill_parity.md`, freezes on
   commit). Status: **prereg ready to freeze; build next**.
7. **Real-document tier — DONE 2026-07-08, external validity UPHELD with a load-bearing
   caveat.** On 12 real NTSB narratives with injected readings, the dissociation *sharpens*:
   blind compaction keeps narrative valence, not content (crash→DENY reflex, APPROVED-side
   decision accuracy 0.00 both models, Δ 0.87/0.93), and fusion recovers J to 0.67/0.77 but
   only partially at short budgets. → `experiments/realdoc/2026-07-08/` (P-RD-1..4 4/4×2).
   **Caveat for all external claims:** on real prose the naive-compaction failure is
   *unreliable answers*, not just missing justification. Successors: the in-harness variant
   (probe a real Claude Code session post-compaction) and longer-budget/selection-truncation
   fusion for 500-word docs. Status: **passed with caveat; successors open**.
8. **Coarseness sweep, conjunctive/disjunctive (roadmap item 2).** Shelf ∝ answer-quotient
   coarseness — the remaining quantitative theory test; Tier 2 deliberately held logical
   structure fixed, this varies it. (~$3.)
9. **Small cheap ones:** compaction-path ensembles (chain∪direct witness union was 14/30 vs
   10–11 alone — is diversity a real intervention? ~$1); the U-shaped decision curve (verdict
   accuracy worst at mid-compression — characterize the dip, possible standalone note);
   Gemini P-G3 completion when a billed key exists.

## Flagship deliverable: the witness-preserving RLM (adopted 2026-07-08)

Public artifact goal — a usable model + HuggingFace demo proving the thesis: **context
utilization is being mismeasured** — accuracy metrics can't distinguish an answer that survived
with its justification from an orphaned verdict. Anchor: Recursive Language Models (arXiv
2512.24601, Zhang/Kraska/Khattab — verified 2026-07-08; they post-trained RLM-Qwen3-8B, so
"train the root" has precedent). Key observation: **RLM relocates compaction rather than
eliminating it** — every recursive sub-call returns a summary into the root's window, and that
return value is a compaction artifact our instruments can audit. Moat = the certificate
contract + the Δ meter, NOT the recursion (we extend their work, we don't race it).

- **R1. Δ-audit of vanilla RLM** (~$5, first — a standalone result either way). Run an open
  RLM implementation (verify minRLM/rlm-minimal forks exist; else implement the thin loop from
  the paper) over our ledger corpora + the realdoc corpus; pipe sub-call returns and final
  answers through the existing Δ/witness pipeline. Prereg: Law 1 predicts sub-call returns
  shed witnesses unless certificate-tasked — high accuracy + high Δ = hidden debt inside the
  year's hottest long-context result; low Δ = explains *why* RLM beats compaction, in our
  terms. Either is the first pricing of RLM justification.
- **R2. Certificate-typed RLM trace dataset** ($0 API): wrap the B4 generator in RLM trace
  format — sub-calls must return `claim + witness + source pointer`, root must cite the
  witness chain or abstain-naming-the-loss. Reuses the ft-dataset gold-templating machinery.
- **R3. Train the root** (~$5–10 GPU): QLoRA Qwen3-8B (or 4B first) on R2 traces. The pod
  workflow is proven (PTY transfer runbook in experiments/ft-dataset/2026-07-08/remote/).
- **R4. Ship**: HF Space (Gradio) — paste a long doc, ask questions; UI shows answer + clickable
  witness chain + a live **Δ meter** vs the same base model with naive compaction; weights +
  model card written like a prereg page (claims, thresholds, refutations included). Framing:
  "mismeasured, and here's the meter" — not "misunderstood".

## Infinite-context build track (the road — see site/#road)

Goal, honestly defined: **bounded-debt memory** — an agent that cannot forget *silently*
(dropped → logged → reclaimable → else flagged; Δ = 0 by construction). Not lossless memory
(Shelf Width Law forbids it). Stages are sequential; each gets its own prereg. The splash
page's road tab mirrors these stages — update its status chips as stages land.

- **B1. Certificate-compaction pilot — DONE 2026-07-08, quotient transfers PARTIALLY.**
  Certificates are the best-J arm on every model (0.956–0.978, Δ ≤ 0.04) and beat blind
  value-dense at <½ the words — but the matched-access economy is REFUTED (a policy-aware
  value-dense writer is terser than the certificate scaffolding), and the APPROVED side breaks
  calibration (writer false-denies on grok; reader over-abstains on haiku; only gpt clean).
  → `experiments/certificates/2026-07-08/`. **Successor rules:** B2 must compare against the
  policy-aware value-dense arm (`vda`), not blind vd, or the economy flatters itself; and the
  writer-side false-deny is the deployable risk to chase — a certificate is only as calibrated
  as the writer's policy evaluation. Status: **done; B2 comparison rule updated**.
- **B2. Depth-calibrated basis compaction** (~$3, after the queue-2 depth ladder). Compactor
  drops anything re-derivable within the reader's measured inference depth d; store a
  generating set, not the knowledge. Prereg: justified accuracy at basis-compaction ≥
  value-dense at strictly fewer realized words. Status: blocked on depth ladder.
- **B3. The fixed point** (~$5, after the length-clamped ρ̄ rerun). Head-to-head over 10+
  rounds: naive stack (ρ̄ ≈ 0.93) vs ledger runtime (compact → ledger → route → re-expand);
  prereg effective ρ̄ ≥ 0.99 and flat Δ. Headline metric: rounds-to-half-witness (naive ~9 vs
  ∞). Status: blocked on length-clamped rerun.
- **B4. Calibrated-reader fine-tune — groundwork DONE 2026-07-08** →
  `experiments/ft-dataset/2026-07-08/`. Deterministic, $0-API SFT dataset distilling the
  calibrated debt-acknowledgment phenotype: 5,906 chat examples (5,021 train / 885 eval, split
  by item) over 1,077 items × 3 corpora × 3 notes-models; six gold classes templated from
  ground truth (cited-witness fusion / conservative missing-data / NONE_NO_FAILURE vs
  NONE_MISSING_DATA); grok-as-notes-source excluded in the artifact-affected corpus. Training
  options costed in `training_plan.md`: OpenAI `gpt-4.1-mini` FT ≈ $15–25 (`launch_openai_ft.py`
  ready, not run) or open-weight Qwen3-4B QLoRA ≈ $2–5 GPU (recommended — unlocks the
  J-lens/tuned-lens internal witness probe). Eval: dissociation battery before/after; Δ,
  incoherence, coherent-debt-ack rate, fusion-register compliance; retained-cell guard against
  over-abstention. Status: **dataset ready — awaiting spend authorization**.
- **B5. Signpost protocol — prose that guards itself against mirages.** Rethinks context as a
  *language convention* instead of a pipeline. Four designs, ranked; row-12 (manifest) is the
  standing caution that artifact-side signals need reader cooperation, and co-trained
  writer/reader conventions must stay human-legible (steganography risk).
  - **B5a. Fusion contract** (~$3): ban naked gist — the compactor may never state an
    evaluative/verdict-bearing claim without its deciding value in the same clause
    ("blocked — error_rate 7.2% > 5%", never "blocked"). Hypothesis: the shelf exists because
    verdict and witness are separable strings; fusion makes them survive or die together, so
    the gap collapses *by construction* (theory 5.1 as a prose register). Prereg sketch: at
    matched realized budget, Δ(fusion) ≤ ½·Δ(control) per model; on lost items, verdict
    accuracy falls toward prior (no unwitnessed confidence) OR WHICH rises with survival —
    either direction shrinks Δ. Status: **DONE 2026-07-08** →
    `experiments/signpost-fusion/2026-07-08/` (RESULTS 2026-07-08). Split: the *mechanism* is
    confirmed (P-FU-2 no-unwitnessed-confidence 6/6, P-FU-4 survival→~1.0 4/4; gap collapses where
    a shelf exists — P-FU-1 2/3 at 15w, gpt Δ 0.44→0.07) but the **"by construction at a matched
    budget" claim is REFUTED**: the fusion rule *overrides* the word budget in all 3 models
    (realized 1.7–1.9× control at 15w → P-FU-3 fails 3/3). Fusion is a witness-retention/value-
    dense instruction that buys the gap with realized length, not a free register — deployable
    fusion needs **enforced truncation** (realized-token budget; ties to the realized-vs-instructed
    parking-lot note). **Successor:** re-run fusion under a hard realized-token cap on the
    compactor (reject-and-retry over budget), so the contract must *select* which fused claims to
    keep; only then is the matched-budget hypothesis honestly testable. grok phenotype needs a
    semantic dual-judge (frozen parser UNMATCHED 9→16 on acronyms).
  - **B5b. Salience transfer** (~$2): weaponize confound #1 — salience steers contract-blind
    compactors. Writer marks decision-relevant values as structurally load-bearing; test
    whether *another vendor's* naive compaction preserves marked witnesses at higher rate than
    unmarked (protection that travels in the text, no pipeline cooperation). Status: design
    sketch.
  - **B5c. Calibrated register** — invert the gist channel (P-D2: readers natively weight
    rhetorical stance): unwitnessed claims carry hedged prose, witnessed claims assert flatly.
    Fold into the B4 fine-tune as a writer-side objective.
  - **B5d. Canary witnesses** — sentinel values embedded at write time; reader quizzed on a
    canary before being trusted on the real question; failed canary → route to re-expansion.
    Ground-truth-free debt tripwire for the B3 runtime. Pairs with the parse-failure-as-debt
    idea (parking lot 2026-07-06).
- **Gate:** the real-document tier (queue 7) — **passed with caveat 2026-07-08** (dissociation
  survives and sharpens on real prose; naive-compaction failure = unreliable answers, not just
  missing justification). Remaining before production claims: long-document budgets,
  selection-truncation fusion, and the in-harness real-transcript variant. The road tab
  wording must carry the caveat.

## Open theory questions

- **Formalize J = α·S + β.** Reader efficiency α is model-specific (0.89–1.20 corrected);
  α>1 = candidate-set elimination (disclosed-candidate recovery), α<1 = retrieval slippage.
  What determines α? Is it stable per model across corpora? (Tier 1+2 data can answer the
  stability question for free.)
- **The gist channel as a second information carrier.** P-D2 shows the artifact carries not
  just values but *asserted normality*, and some readers weight it above their prior. The
  quotient theory has no slot for this — the summary's rhetorical stance is neither answer
  nor witness. Candidate formalization: gist = a noisy verdict token embedded in the artifact.
- **Blind-vs-aware covering gap** (Appendix H.5): blind compactor pays Σ|candidates|, aware
  pays fiber entropy; price of blindness → 0 when candidates fit the budget. Prove it.
- **Certificate-honesty semantics.** The exact check found the quotient between M and Q for Q families. Formalize the general certificate quotient: what counts as a certificate object, how it composes, and when it collapses to full witness identity.
- **Fibered Shelf Width Law + repositioning** on Myhill–Nerode / ε-machines / Vorob'ev before
  any external claim (risk-register item; unchanged).

## Ideas parking lot (dated, no obligation)

- 2026-07-06 — *Coherent-debt-acknowledgment rate as a training metric.* Haiku natively says
  "the readings are absent" (0.79) where grok/gpt assert contradictions (0.00). If that rate
  were tracked during model training the honesty premium says it's cheap to buy there and
  ~38× to retrofit. Possible short position paper: "measure debt-acknowledgment, not
  hallucination."
- 2026-07-06 — *Unparseable output as a debt signal.* Format degradation concentrates on
  lost-witness items (retained cells parse perfectly). A production system could treat
  parse-failure rate as a free debt proxy. Worth one exploratory plot over existing data.
- 2026-07-06 — *Realized-vs-instructed budget as the control knob.* The paraphrase arm halved
  realized length at the same nominal budget; every campaign shows overshoot ~1.5×. Compaction
  contracts should be specified in realized tokens, not instructed words — engineering note
  for the ledger-router design.
- 2026-07-06 — *Startup framing (from the market scan):* the durable asset is deterministic,
  judge-free debt measurement (ledger = guaranteed floor, not accuracy estimate — J ≥ S is the
  honest fine print), wedged into regulated voice agents; Morph/platform compaction absorbs
  the "preserve values" half. Kill-risk: table-stakes absorption. Fallback: own "justified
  accuracy" as an open standard.

- 2026-07-07 — *Iterated compaction: the epistemic interest rate.* **DONE 2026-07-08** →
  `experiments/iterated-compaction/2026-07-08/` (README row 29). Confirmed on grok+haiku: witness
  survival decays geometrically at ρ̄ ≈ 0.93/round while the verdict persists (shelf widens
  +0.11/+0.14); gpt near-idempotent (ρ̄ 0.985). Disclosed confound: realized length also settles
  below budget per round, so ρ̄ mixes iteration loss with length-settling.
  **Successor (length-clamped interest rate):** force each round to *spend* the full budget
  (reject-and-retry summaries shorter than ~0.9·W, or a fixed-token budget), extend to R=6–8, to
  partition ρ̄ into pure iteration loss vs length-settling and test ρ stability deep in the chain.
  If ρ is still ≈ 0.93 cross-model under the clamp, it is a genuine dynamical constant. (~$1–2.)
- 2026-07-07 — *Vorob'ev acyclicity as an empirical kill-shot.* Section 5.3's sheaf reading makes
  a zero-parameter structural prediction: the mirage (local consistency without a global section)
  can only exist when the observation-context hypergraph is cyclic; on acyclic covers the shelf
  *cannot form*. Design item families identical in size/values but differing only in cover
  topology (acyclic vs minimal 4-cycle); predict the shelf appears on cyclic covers only. If it
  holds, compaction debt is literally a contextuality class and the field's first bridge from
  Abramsky–Brandenburger to LLM memory. Needs the sheaf formalization first — month-scale, but
  the single most headline-grade falsifiable claim in the theory doc.
- 2026-07-07 — *Read-time inference depth as a universal model constant.* If queue item 2's
  boundary replicates across models and domains at the same depth (recovery at one elimination
  step, collapse at two), then "inference depth of the read channel" is a measurable constant of
  behavior-optimized readers — plausibly THE quantity that α estimates, and a new axis for model
  cards: not "can it reason" but "how much reasoning does it deploy to justify retrieved answers."
  Test-time-compute variants (reasoning readers, G.1) should move the depth; if they don't, that
  is a much deeper statement about where justification lives.

- 2026-07-08 — *Verdict–justification ordering interference (from the distill-parity teacher
  gates).* Same teacher, same items, three orderings: bare verdict 0.784/0.800, justify-with-
  verdict-first 0.427, evidence-then-verdict 1.000 (DENIED side; distill-parity README has the
  frozen note + provenance). Micro-experiment queued: isolate emission-garbling vs decision
  interference by crossing ordering × whether the verdict token is pre-committed. Cheap (~$1,
  API or pod). Do not fold into the distill-parity campaign.

## Done (moved from queue)

- ~~High-power replication (Tier 1)~~ → `experiments/highpower/2026-07-06/` — P-H1/H2/H4 3/3,
  P-H3 2/3 (haiku over-abstains); prior objection retired for haiku/gpt.
- ~~Domain battery (Tier 2)~~ → `experiments/domains/2026-07-06/` — P-D1 14/16 applicable
  (15/16 semantic); NEW: P-D2 gist-belief-overrides-prior split (grok 1/6 vs gpt/haiku 6/6).
- ~~Parser-artifact audit + phenotype re-score~~ → `experiments/rescore/2026-07-06/`.
- ~~J = S budget line~~ → REFUTED toward J ≥ S, `experiments/laws/2026-07-03/budgetline/`.
- ~~Honesty premium reproduction~~ → `proofs/honesty_premium.py` (0.47×, 38.4×, dichotomy).
- ~~Honesty Theorem exact check~~ → `proofs/honesty_theorem.py` — exact-witness honesty requires Q on all checked models; one-certificate honesty has an intermediate quotient on Q families (5/6/7, 6/7/8, 7/9/13 answer/certificate/joint states).
- ~~Reader inference boundary (depth-1 hypothesis)~~ → `experiments/reader-inference-boundary/2026-07-08/` — REFUTED: readers deploy one arithmetic step of witness recovery (main + confirmatory c2). Successor = a deeper depth ladder (see queue item 2).
- ~~Iterated compaction: the epistemic interest rate~~ → `experiments/iterated-compaction/2026-07-08/` — CONFIRMED 2/3 (grok/haiku ρ̄ ≈ 0.93/round, verdict persists; gpt near-idempotent null). Successor = length-clamped variant (see the dated idea above).
