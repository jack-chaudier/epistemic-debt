# Witness-preserving RLM — scope (2026-07-08)

Flagship deliverable (see NEXT.md). Thesis for the public artifact: **context utilization is
mismeasured** — accuracy can't distinguish an answer that survived with its justification from
an orphaned verdict. We ship the meter (Δ) and a model that keeps the reasons.

## Anchor & moat

- Anchor: Recursive Language Models (arXiv 2512.24601; verified — they post-trained
  RLM-Qwen3-8B, +28.3% over base). RLM treats the long prompt as an external environment the
  root model recursively queries; sub-call *returns* land in the root's window.
- Core observation: **RLM relocates compaction rather than eliminating it.** Every sub-call
  return is a compaction artifact. Law 1 predicts those returns shed witnesses unless
  certificate-tasked. Nobody has measured whether RLM answers are *justified*.
- Moat: the certificate contract + the Δ meter — not the recursion. We extend, not race.
- Fork base: `rlm-minimal` (MIT, Python, OpenAI-client backends; verified 2026-07-08).

## The certificate contract (the novel piece)

Sub-call return type — instead of free-form summaries, every recursive call must return:

```
CLAIM: <one-sentence finding>
WITNESS: <the verbatim deciding value(s), name + number + unit>
POINTER: <source slice id / line range>
```
(or `NO_FINDING: <what was searched, what was absent>`)

Root contract: the final answer must cite the witness chain (claims + pointers used) or
abstain naming the specific missing value. This is the fusion register (B5a: incoherence → 0)
plus the certificate format (B1: best-J arm) plus the ledger pointer (row 21: recall 1.00),
lifted from compaction artifacts to recursion returns.

## Stages

### R1 — Δ-audit of vanilla RLM (~$5; standalone result either way)
- Harness: fork rlm-minimal; adapt backend to our providers (grok/haiku/gpt) or gpt-4.1-mini.
- Corpora: (a) concatenated ledger corpora from experiments/lib (many docs → one long context;
  ground truth exact), (b) the realdoc NTSB corpus (real prose). Query = the standard
  decision + WHICH probes against the long context.
- Instrument BOTH layers: final answers (decision/WHICH/Δ as usual) AND every sub-call return
  (witness survival of the deciding value through the return channel — the "relocated
  compaction" measurement, which no one has).
- Prereg sketch (freeze before calls): P-R1-1 RLM final accuracy ≥ naive-compaction baseline
  (replicates their claim on our corpora); P-R1-2 Law-1 prediction — deciding-witness survival
  through sub-call returns < 0.5 when returns are free-form; P-R1-3 Δ(RLM) vs Δ(compaction):
  preregister BOTH readings (high Δ = hidden debt in RLM; low Δ = RLM beats compaction
  *because* it preserves witnesses — either is the first pricing of RLM justification);
  P-R1-4 the certificate-prompted variant (same scaffold, returns forced into the contract
  above, no training) cuts Δ by ≥ half vs free-form returns. R1 thus already contains the
  prompt-level ablation of the whole thesis.
- Confounds to guard: sub-call return length (match budgets free-form vs certificate);
  candidate disclosure (state policy-visibility per probe, per CLAUDE.md #3); REPL
  nondeterminism (seed; temperature 0; log every sub-call).

### R2 — Certificate-typed trace dataset ($0 API)
Wrap the B4 gold-templating machinery in RLM trace format: (context slice, query) →
certificate returns; root traces that assert-with-witness-chain or abstain-naming-the-loss.
Reuse ft-dataset generators + realdoc corpus; split by item as before. Target ≥ 3k traces.

### R3 — Train the root (~$5–10 GPU)
QLoRA Qwen3-4B first (cheap sanity), then Qwen3-8B (their post-train scale). Pod workflow is
proven (PTY-transfer runbook in experiments/ft-dataset/2026-07-08/remote/; pod stopped, can
respin). Eval = R1 harness before/after: headline Δ, witness-chain citation rate,
abstain-naming-the-loss rate, with R1's vanilla + certificate-prompted numbers as baselines.
The tune must beat certificate-*prompting* (P-R1-4) to justify existing.

### R4 — Ship (HF Space + weights + model card): THE DEMO

Design goal: one screen that makes the thesis undeniable in 30 seconds. Split-screen,
**same base model, same document, same question**:

- LEFT ("how everyone does it"): naive compaction → answer. Confident prose, no receipts.
- RIGHT (witness-RLM): answer + **clickable witness chain** — click a certificate, the exact
  source span lights up in the document pane. When evidence is missing: the explicit
  `MISSING:` flag naming the value, and a FETCH that repays it from the archive.
- **The Δ meter**: live justified-accuracy vs accuracy on a preset probe battery for the
  loaded document, both sides. The number nobody else's demo shows.
- **The compression slider** (the showstopper): drag the context budget down 80→15 words per
  slice. LEFT degrades into confident vibes (the realdoc crash→DENY reflex, live). RIGHT's
  answers stay pinned to receipts or degrade into *named* gaps. The exchange-rate curve
  (row 17) made tangible.
- Preloaded examples where ground truth is verifiable: 2–3 real NTSB narratives (public
  domain, already in-repo — including an APPROVED case the naive side gets wrong on vibes),
  one long RFC/codebase doc, one synthetic ledger corpus. Plus paste-your-own.
- Weights: LoRA adapter on HF hub; model card written like a prereg page (claims with
  thresholds, refutations included — the P-R1-4 prompting ablation reported honestly).
- Framing: "mismeasured, and here's the meter." Never "misunderstood."

## Generalization path (G-track): a general assistant with the register baked in

Don't train a general assistant — start from one (Qwen3-8B-Instruct) and train only the deltas.

- **G1. The three-way epistemic register** (generalizes the fusion contract): every factual
  claim carries WITNESSED (value + pointer into session archive) / PARAMETRIC (from weights —
  say so) / MISSING (context should contain it, doesn't — name it). Training mix ≈ 50%
  certificate/RLM traces broadened across domains (the realdoc injection method is a factory:
  works on any public long document), 30% existing attribution-QA/RAG-citation data rewritten
  into the register, 20% general instruction replay (no chat regression).
- **G2. Two-sided eval prereg**: our Δ battery for the new behavior AND a general-capability
  no-regression guard (IFEval-style spot checks). A register model that loses general
  competence is a failed run, preregistered as such.
- **G3. Serve inside the runtime**: chat harness where every conversation has an append-only
  archive + loss ledger; RLM recursion is the escalation path (context overflow or
  ledger-flagged query → certificate-typed recursive retrieval), not the default. The user
  experiences an assistant that never *silently* forgets.
- **RLVR endgame (the scaling story):** certificate validity is mechanically checkable —
  WITNESS-at-POINTER is a deterministic string check, no judge. The register is therefore a
  native target for RL with verifiable rewards; our ledger machinery IS the reward function.
  SFT installs the register; RLVR is how it hardens at scale. "The honesty layer ships with a
  free verifier."

## Budget & sequence

R1 ≈ $5 → R2 $0 → R3 $5–10 → R4 $0 (Space is free tier). Total ≈ $15–20.
R1 first — it's a paper-grade result alone and tells R2/R3 exactly what to fix.

## Risks

- RLM authors iterate fast (May 2026 revision); moat discipline: certificate contract + Δ.
- Sub-call instrumentation depends on rlm-minimal's trace visibility — verify early in R1.
- 8B tune may not beat certificate-prompting (P-R1-4 strong) — then the deliverable is the
  prompt-level contract + audit, and R3 is honestly reported as unnecessary. That is still a
  shippable result ("the fix is a contract, not a checkpoint").
