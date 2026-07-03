# The Justification Gap: Toward a Resource Theory of Being Right for Reasons

**Status: vision document / research program. Everything here is labeled conjecture, theorem-target, or exact check. Nothing below should be cited as established except where it points at an existing stark artifact.**

---

## 0. The kernel, restated at full altitude

The mirage program's core finding, stripped of its scaffolding:

> **Being right and knowing why are different physical resources, and the exchange rate between them is computable.**

Correctness is cheap. Justification is expensive. Under any memory budget between the two prices, a system exists — and, we conjecture, is *preferentially found* by any behavior-optimizing process — that answers perfectly while its reasons are gone. That zone is the mirage shelf.

Everything in this document is an attempt to promote that finding from a property of one finite quotient family to a *law of compressed cognition* — with consequences for machine learning, complexity theory, cognitive science, and institutional design.

---

## 1. A theorem hiding in the existing formulas (the fibration reading)

This section is new, exact, and checkable today against artifacts already in this repository.

Observe that the bare answer quotient is the p = 1 case of the witness quotient:

```
|M_k|      = Σ_{d=0}^{k} (d+2)      = (k+1)(k+4)/2
|Q_(k,p)|  = Σ_{d=0}^{k} (d+2)^p
⇒  M_k = Q_(k,1)        (confirmed: Q_(1,1)..Q_(5,1) = 5, 9, 14, 20, 27 = M_1..M_5 in the phase-sweep table)
```

So the witness quotient is a **fibration over the answer quotient**: each answer-level state at depth d carries a fiber of (d+2)^(p−1) witness configurations. The answer quotient is the base space; witness identity lives in the fibers; compression that respects answers is free to scramble fibers.

**The check.** The separator-closure experiment measured the post-closure shelf width for Q_(5,3) as **4.858 bits**. The fibration predicts the shelf width should be the log answer-weighted mean fiber size:

```
ω_closed = log2( |Q_(k,p)| / |M_k| ) = log2( Σ(d+2)^p / Σ(d+2) )
Q_(5,3):  log2(783 / 27) = log2(29) = 4.857981  ✓  (matches the measured 4.858 exactly)
```

The measured quantity and the structural quantity coincide. This upgrades the shelf from "an observed gap" to a **computable invariant with a closed form**: the shelf width is the entropy of the witness fiber.

**Shelf Width Law (theorem target).** *For any witness-faithful contract whose witness quotient fibers over its answer quotient, the closed (probe-complete) shelf width equals the log of the answer-state-weighted mean witness-orbit size:*

```
ω(C) = log2( E_{answer states}[ |witness orbit| ] )
```

**The symmetry refinement.** The existing symmetry count `|Q^sym| = C(k+p+2, p+1) − 1` says: when the task is invariant under permuting witnesses, you pay only for the multiset, not the labeled tuple. This generalizes the law to:

> **The justification cost of a task is the entropy of its witness orbit under the answer-preserving symmetry group the task actually respects.**

This is a gauge-theoretic statement. Answers are the gauge-invariant observables; witnesses are the gauge; symmetry reduction is gauge fixing; the shelf is the volume of the gauge orbit. Systems under memory pressure spontaneously "fix the gauge" — they keep invariants and discard the section — and no observable defined on invariants can detect that it happened. This is why the mirage is *silent* by construction, not by accident.

Immediate work: (a) verify the law on Q_(3,2) — prediction ω_closed = log2(54/14) = 1.9475 bits — and across the closure sweep grid; (b) prove it for the fibered case; (c) state the general (non-fibered) version via orbit counting.

---

## 2. The reframe that raises the stakes: memory prices on the ladder of causation

The program's causal framing is not decoration. It is the point.

In Pearl's hierarchy, rung 1 (association) asks what is true; rung 2 (intervention) asks what would happen if we acted; the adjustment set — the *witness* — is precisely the information that licenses the climb from rung 1 to rung 2. The stark result, read causally:

> **Rung-1 sufficiency and rung-2 sufficiency have different memory prices, and lossy compression pays the cheaper one.**

A compressed reasoner keeps its observational answers (they are protected by every eval it faces) and sheds its identification machinery (protected by nothing). It then *passes every observational test* — because rung-1 behavior is exactly what survived — while its capacity to answer "what if the world changes" has been destroyed. The failure is invisible until an intervention occurs, at which point the system fails with full confidence.

This converts the mirage program from a faithfulness/interpretability topic into a theory of **brittleness under distribution shift**:

> **Witnesses are the currency of counterfactual transfer. Answers are sufficient for the training distribution; witnesses are what let you recompute answers when the distribution moves.**

Chesterton's fence is the folk version: the fence (answer) outlives the reason it was built (witness); the institution keeps functioning until the environment shifts and nobody can recompute whether the fence still matters. The mirage shelf is Chesterton's fence with an exact bit-count.

---

## 3. Three conjectured laws

These are the physics of the program. Each is stated as a law, then as a formal target.

### Law 1 — Justification has no gradient (the ordering law)

*Any process that compresses state under behavioral loss sheds witness information before answer information — not sometimes, structurally.*

Answer bits are defended by the loss: perturb them and the loss rises, so optimization pressure actively maintains them. Witness bits that don't change behavior on the training distribution are *gradient-orphaned*: nothing in the objective repairs them, so they decay at the ambient noise rate (regularization, quantization, distillation, cache eviction, forgetting). Unfaithfulness is not a bug in behavior-trained systems; it is their thermodynamic ground state.

Formal targets:

- **Rate-distortion version.** Give the task two distortion measures, d_A (answer error) and d_W (witness error). Since witnesses determine answers, R_A(0) ≤ R_W(0) always; the shelf is the interval [R_A(0), R_W(0)), and its width is the Shannon-setting generalization of ω above. Under a budget in the shelf, *every* optimal code has perfect answers and imperfect witnesses. This makes the shelf a property of the rate-distortion geometry, not of any particular compressor.
- **Toy SGD theorem.** In a linear or shallow model trained on answer loss with weight decay/noise, information about Y is maintained at equilibrium while information about W|Y decays exponentially at the regularization rate. Quantify the half-life of justification as a function of the noise scale. This would be a clean, publishable lemma.
- **Observed consequences already in the literature** (converging evidence, not confirmation): answers robust to CoT ablation (Lanham et al.); attributional drift — FFN pathway generates the claim while the attention pathway fails to ground it (FACTUM); citation quality more fragile than answer quality in long-context evals (L-CiteEval). Law 1 predicts all three and says why they must co-occur.

### Law 2 — Conservation of epistemic debt

Define the **epistemic debt** of a system at budget B:

```
D(B) = P(answer correct ∧ witness unrecoverable)
```

*At fixed budget, debt can be converted between phenotypes but not destroyed. Only witness bits annihilate it.*

The two phenotypes are already in the stark policy pair: under **forced** decoding, debt expresses as confabulation (a majority-witness is emitted — fluent, wrong, unflagged); under **breach** (abstention), the same mass converts to explicit coverage loss ("I don't know"). The naive conjecture — exchange rate exactly 1 — **was tested exactly and is FALSE** (see §Appendix A). What replaces it is sharper: converting debt to abstention costs a multiple of the debt (the **honesty tax**), because justified and unjustified mass are entangled in the same memory states; and the size of the multiple depends on whether the memory layout was optimized for answers or for honesty (the **honesty premium** — see Appendix A for the measured 18× vs 0.47× asymmetry). The conservation law survives as an accounting identity plus a lower bound: abstention mass ≥ debt, with equality only on disentangled layouts.

Corollaries (of the refined version):

- Confabulation and calibrated ignorance are the *same quantity* wearing different output policies. You choose which one your system exhibits; you do not choose how much of it there is.
- Debt is measurable **behaviorally, without interpretability access**: run the system with and without an abstain option; the divergence maps the correct-but-unjustified set. (The abstention-delta probe — no one in the abstention literature uses abstention to *localize* unjustified correctness; they use it to reduce error.)
- Debt is invariant under representation change — already checked: the shelf survives prefix, suffix, and interleaved bit geometries in the phase sweep. A conserved quantity should be coordinate-free; it is.

### Law 3 — Debt is brittleness (the transfer law)

*Adaptation error under intervention is lower-bounded by epistemic debt.*

Formal target in the quotient model: define a perturbation class (edit the world's weights/graph; re-pose the query). States in the answer quotient cannot recompute the new answer — they retained only the old output; states in the witness quotient can — they retained the machinery. Theorem shape:

```
E[transfer error after intervention] ≥ f(D) ,  with f explicit on the finite family
```

This is the law that matters economically. It says the mirage shelf is not an epistemological curiosity — it is a *quantitative early-warning invariant for systems that will fail when the world changes*, measurable before the change happens. No current eval measures anything like it.

---

## 4. The Honesty Theorem (mechanism design)

The abstention result, pushed to its limit, is a statement about the price of honesty:

**Conjecture (Honesty Theorem).** *Calibrated confidence costs as much memory as justification. Formally: the minimal state supporting the contract "answer correctly or abstain, with abstention exactly on witness-ambiguous states" is the witness quotient — the answer quotient does not suffice for any calibrated abstention policy with full coverage of the unambiguous region.*

In slogan form: **you cannot know that you know for less than it costs to know why.** A system can be right cheaply, but it cannot be *reliably confident* cheaply — because telling justified correctness apart from mirage correctness requires exactly the fiber information that the shelf destroyed.

If provable (and the finite machinery to prove or refute it exists in this repo), the mechanism-design consequence is large: **mandating calibrated abstention forces systems to carry witness state.** Auditability stops being a favor you ask of a model and becomes a resource requirement you impose on it. You don't inspect the system's reasons; you make it structurally impossible to be confidently right without having them. This is a compliance mechanism enforced by information theory rather than by trust — the difference between asking for honesty and making dishonesty unaffordable.

Contrapositive, equally important: any system that never abstains is *free* to live on the shelf, and by Law 1 it will. Confident systems are cheap precisely because confidence without calibration carries no witness obligation. That is a design indictment of every always-answer deployment.

---

## 5. The mathematics to build

Four programs, ordered by tractability.

### 5.1 Self-certifying streaming complexity (JSPACE)

Classical complexity separates decision from search. The streaming/annotation literature (Chakrabarti et al.) separates verification with an external prover. The missing object: **the machine itself must retain its certificate.**

Define JSPACE(f): problems solvable by a streaming algorithm in space O(f) that outputs, alongside its decision, a witness checkable by a logspace verifier with one more pass. The program: prove a **decision/self-certification hierarchy** — natural problems where SPACE(decision) = O(log n) but JSPACE = Ω(n^α), with the gap governed by the witness-orbit entropy of §1. The stark family provides the exact finite base cases; the asymptotic theorem is the prize. The Shelf Width Law becomes the finite shadow of a space-complexity separation.

### 5.2 The witness ε-machine

Computational mechanics (Crutchfield–Shalizi) defines the minimal predictive state — the ε-machine — as the quotient by "same conditional future." That is the *answer* quotient of stochastic prediction. Define the **witness ε-machine**: quotient by "same conditional future *and* same recoverable generating cause." Its statistical complexity C_W ≥ C_μ, and the gap C_W − C_μ is the stochastic-process version of the shelf. Since recent work shows transformers represent belief-state geometry (the ε-machine simplex) in their residual streams, this yields a direct mechanistic-interpretability prediction: **trained transformers should represent the answer ε-machine, not the witness ε-machine, and the missing simplex directions are exactly the confabulation modes.** This is a falsifiable bridge from the finite theory to actual model internals.

### 5.3 The cohomology of justification

The holonomy tower (pair → simplex → global; static vs dynamic obstructions) should be rewritten in sheaf-theoretic language — not to decorate it, but because the machinery there is stronger than what has been rebuilt by hand. Justifications form a presheaf over the cover of observation contexts; a global justification is a section; the mirage is **local consistency without a global section** — precisely an Abramsky–Brandenburger contextuality class, with Vorob'ev's theorem giving the acyclicity criterion for when the shelf *cannot* exist. Conjecture worth chasing: static obstructions (states disagree now) and dynamic obstructions (states will diverge) land in different cohomological degrees, which would explain the observed fact that their first failures occur on structurally different families (5-edge vs 4-edge). If the shelf is a cohomology class, then "adding abstention kills the mirage" should be a statement about passing to a refinement on which the class vanishes — a genuinely new theorem shape, and the one part of the transport program that would survive as original after honest repositioning.

### 5.4 Epistemic gauge theory (speculative, kept honest)

§1's orbit formulation suggests the full structure: task symmetry group G acting on witnesses over an answer base; justification = choice of section; compression = projection to invariants; debt = volume of the orbit; abstention = refusing to answer where no canonical section exists. Whether this is a useful theory or just a useful metaphor depends on whether the connection/curvature analogies produce theorems (does the composition law define a connection? are the dynamic obstructions its curvature?). Flagged as the highest-risk, highest-beauty branch.

---

## 6. Kill-shot experiments

Each law above has a cheap empirical assassin. In order of impact-per-dollar:

1. **Distillation widens the gap (Law 1).** Take a teacher and its distilled student. Standard benchmarks will show near-parity — that is what distillation optimizes. Prediction: on *counterfactual variants* (same questions, perturbed premises requiring recomputation) the student degrades disproportionately, and its witness fidelity degrades before its accuracy does. If confirmed across model families, this is a headline result: **the entire compression-deployment pipeline of modern ML systematically manufactures epistemic debt that no current eval detects.**
2. **The abstention-delta probe (Law 2).** Production diagnostic requiring no internals: run with/without an abstain option under context pressure; the divergence set localizes the mirage. Validate on the fixed Grok protocol (non-repeating distractors, paraphrase-tolerant judge), then ship as an eval standard: report Δ = accuracy − justified-accuracy next to every accuracy number.
3. **KV-eviction counterfactual test (Laws 1+3).** The existing n=12 result — answers flip while evidence remains in the input text — is the cleanest mechanistic cousin of the shelf. Fix the RoPE confound, scale n, then add the transfer arm: evicted-cache models should fail counterfactual re-queries at a rate predicted by their witness loss, not their accuracy loss.
4. **Human confabulation as forced decoding (cross-domain).** The forced/breach policy pair is a formal model of the confabulation literature (Nisbett–Wilson; split-brain interpreter): expertise is answer-quotient cognition; explanation lags skill because skill compression is behavior-optimized (Law 1 applies to practice, not just SGD). Prediction: manipulating working-memory load during skill execution should increase confabulated justifications at a rate tracking the task's witness-orbit entropy, while accuracy holds. A collaboration-ready hypothesis for a cognition lab.

---

## 7. Why this could matter at world scale

- **Evals.** Every leaderboard measures the answer quotient. Law 1 says optimization will therefore *specifically* sacrifice everything else. The field is currently steering by exactly the invariant that the mirage preserves. A standardized debt metric (Δ, the abstention-delta) is the correction, and it is measurable today.
- **Safety.** Post-hoc justification asked of a system on the shelf is confabulation by theorem, not by malice. Oversight regimes built on "explain your reasoning" fail precisely in the regime where they're needed. The Honesty Theorem offers the alternative: calibrated-abstention mandates make auditability a resource requirement, checkable from behavior alone.
- **Systems that must survive change.** Law 3 turns the shelf into a brittleness forecast. Anything long-lived and compressed — model caches, agent memory, distilled deployment models, institutional knowledge bases — accumulates debt silently and fails abruptly under shift. An accounting discipline for epistemic debt (what did compaction drop, and was it fiber or base?) is to AI operations what error budgets are to SRE.
- **A genuinely old problem, priced.** Plato asked what separates true belief from knowledge; the classical answer was justification. This program's contribution is not the distinction — it is the discovery that the distinction has a **price in bits, a closed form, a conservation law, and a market** (systems under pressure sell justification first, because the loss function doesn't charge for it). Making "knowledge minus true belief" a measurable physical quantity, with laws, is the kind of move that reorganizes fields.

---

## 8. Risk register (what would kill this)

- **The IB-triviality objection.** "I(Z;W) can vanish while I(Z;Y) stays maximal — that's obvious information bottleneck." Response: the static fact is trivial; the program's content is the *compositional* version (state must compose associatively under streaming, which is what forces the quotient structure and exact counts), the *closed-form width*, the *conservation law*, and the *transfer bound*. If those reduce to known IB results, the program collapses to a rediscovery. Priority: check against IB-with-side-information literature early.
- **The shelf might be an artifact of forced decoding.** If real systems, unlike the forced policy, hold graded uncertainty, debt may partly self-report. The Grok data (0/36 degradation flags at high confidence) argues otherwise, but on one model, with confounds. Kill-shot #2 settles it.
- **Law 2's exchange rate may only hold on pure-answer buckets.** Then conservation becomes an inequality — still useful, less beautiful. Checkable this week against the pareto JSON.
- **The Honesty Theorem may be false**: there might exist clever sub-witness state sufficient for calibration (knowing *that* the fiber is ambiguous without knowing the fiber). If so, that failure is itself interesting — it would define exactly the cheapest honest state, a new quotient between M and Q. Either outcome is a result.
- **Reinvention exposure.** The quotient/holonomy substrate must be repositioned on Myhill–Nerode / ε-machines / Vorob'ev / Abramsky–Brandenburger *before* any external claim is staked, or credibility dies on contact with the first expert reviewer.

---

## Appendix A — First exact checks (2026-07-03)

Both checks run against artifacts already in this repository; verification scripts in the session scratchpad (`verify_conservation.py`).

### A.1 Shelf Width Law: VERIFIED (3/3 closure families)

Predicted `ω_closed = log2(|Q_(k,p)| / |M_k|)` vs measured post-closure shelf width in
[separator_closure_experiment.md](../../../results/quotient-thresholds/separator-closure-experiment/separator_closure_experiment.md):

| family | measured | predicted | answer states at closure |
|---|---|---|---|
| Q_(3,2) | 1.948 | 1.947533 | 14 = \|M_3\| |
| Q_(4,2) | 2.170 | 2.169925 | 20 = \|M_4\| |
| Q_(5,3) | 4.858 | 4.857981 | 27 = \|M_5\| |

The closure tables confirm the mechanism: the answer channel saturates at exactly the fibration base M_k while the joint channel saturates at Q_(k,p). The closed shelf is the fiber entropy, as §1 predicts.

### A.2 Conservation: rate-1 REFUTED; honesty tax and honesty premium discovered

Method: at each budget, find the forced-optimal partition (the layout a behavior-optimizer picks), then evaluate both policies on it; separately find the breach-optimal layout. Quantities: debt `D = A_f − J` (right answer, wrong witness); honesty tax `= J − C` (justified mass destroyed by abstention on the same layout); honesty premium `= A_f − C*` (accuracy sacrificed at the best honest layout).

Findings (full tables in the session log):

- **Accounting identity** `A_f − C = D + tax` holds everywhere (sanity).
- **Rate-1 conversion is false**: on forced-optimal layouts, tax/D runs **2.5–6.4×** on the synthetic Q families and hits **18×** on causal_referee at 3 bits. Abstention over-fires: it destroys justified answers that share memory states with debt.
- **Honesty is a layout property, not a policy property**: on causal_referee at 2 bits, the forced-optimal layout carries D = 0.359 and retrofitted honesty costs 0.640 (tax 1.78×) — but the breach-optimal layout at the *same budget* certifies C* = 0.832, a premium of only 0.168 = **0.47× the debt**. Designing memory for honesty can cost less than the debt itself; retrofitting honesty onto answer-optimized memory can cost an order of magnitude more.
- The realistic corpus (causal_referee) behaves differently from the synthetic families — its premium/D crosses below 1 — suggesting real task structure is *more* honesty-friendly than worst-case synthetic structure when the layout is chosen for it.

New theorem targets raised by A.2:
1. **Layout dichotomy**: characterize the budgets/contracts where premium ≤ D (honesty cheaper than the debt it removes) vs premium ≫ D. Conjecture: premium ≤ D iff there exists a partition simultaneously near-answer-optimal and witness-pure-given-answer.
2. **The retrofit gap** `tax(forced layout) / premium(best layout)` as an invariant of contract structure — measured up to ~38× here (18.01/0.47). This is the exact-model version of a deep ML question: the cost difference between *training for faithfulness* and *bolting faithfulness onto an answer-trained model*. It is a resource-theoretic argument that process supervision and citation training must happen during optimization, not after it.

## Appendix B — LLM pilot 1: contract-visible compaction (2026-07-03, null, informative)

Grok-4-1-fast, 30 procedurally generated go/no-go incident files (~1,450 words), compressed to an 80-word budget by the same model *with the decision policy visible in the document*, then answered from summary only. Result: **no mirage** — answer accuracy 1.000 full and compressed, witness retention in summaries 90/90, zero abstentions; the compressor found and kept the three deciding values every time (summaries averaged 29 of 80 allowed words). Total cost ≈ $0.03; 162/162 calls parsed.

Interpretation: this is the theory behaving, not failing. When the compressor knows the contract, the witness quotient is cheap — it need only preserve 3 named values. The shelf is predicted to appear under **contract-blind** compression, where the compactor cannot know which of many facts will be load-bearing; there, answer-sufficient *gist* ("several readings were out of spec" — the bare threshold quotient M_k) is radically cheaper than named witness identity (Q_(k,p)), and the compressor should spontaneously implement the bare quotient. This also validates, in miniature, the design principle behind witness-aware compaction tooling: declaring the contract to the compactor collapses the problem. Pilot 2 (contract-blind, 12 parameters, 3 secretly policy-relevant, 60-word budget) targets the shelf directly.

## Appendix C — LLM pilot 2: contract-blind compaction (2026-07-03, differential shelf CONFIRMED)

Same model; 60 items, 12 numeric parameters each (3 secretly policy-relevant), compressor blind to the policy, 40-word budget. Real witness loss achieved (policy retention 0.817, indistinguishable from non-policy 0.839 — the blindness worked). Cost ≈ $0.05.

The aggregate shows no mirage (accuracy −0.117 ≈ witness −0.150), but the class-conditional structure is the theory's own differential prediction, confirmed:

| class | answer structure | quotient relation | predicted | observed |
|---|---|---|---|---|
| APPROVED | conjunction (all 3 values) | answer ≈ witness quotient | no shelf | acc 0.800, errors track lost values |
| DENIED | disjunction (∃ failure = bare M_k gist) | answer ≪ witness quotient | shelf | acc 0.967; the worst-retention cell (nfail=3, retention 0.667) scored 10/10 |

The shelf appears exactly where the answer quotient is coarser than the witness quotient and nowhere else. Additional findings: a **missing≈failing** conservative bias (6/7 errors were APPROVED→DENIED — fabricated pessimism, not fabricated approval); **77% confabulation rate** on the 13 items objectively non-determinable from their summaries even with an abstain option; the 3 abstentions that did occur all landed on lost-witness items (P3-directional). The counterfactual-brittleness test (Law 3) was non-discriminative by design flaw (the CF supplies the queried value; gist + priors carry the rest) — v3 replaces it with within-item right-answer/wrong-reason probes and a no-notes baseline.

## Appendix D — LLM pilot 3: within-item dissociation (2026-07-03, shelf + confabulation locus)

Same model. Items with 12 parameters (3 policy-relevant), compressor contract-blind; DENIED items have exactly one failing parameter. Per item, from the same compressed notes: DECISION (gist-sufficient), WHICH parameter caused the denial (witness-required), REPAIR (minimal change to flip — intervention-required), WHICH-ABSTAIN, and a no-notes prior baseline. At the aggressive budget (15-word instruction; policy retention 0.389):

| DENIED cell | n | decision | WHICH | REPAIR |
|---|---|---|---|---|
| failing value retained | 6 | 6/6 | 6/6 | 6/6 |
| failing value lost | 6 | **4/6** | **0/6** | 1/6 |

Right-without-knowing-why, within single items: the verdict survives witness destruction (above the 5/12 no-notes floor) while reason identification hits zero and repair capacity collapses to guessing. Two findings beyond the confirmation:

1. **Incoherence, not confabulation, in identification.** In the lost cell the model does not invent a wrong parameter — it answers "DENIED" and "PARAMETER: NONE" about the same notes (4/6), and takes the abstain option 4/6 when offered. The answer channel and the witness channel don't just decouple in accuracy; they decouple into *mutually inconsistent outputs*.
2. **Confabulation lives in the action channel.** REPAIR named a specific parameter and value in 6/6 lost-cell items with no evidential basis. The epistemic debt is invisible in "what happened" probes and surfaces as unfounded specificity exactly when the system is asked to *act*. For agent safety this is the worst possible locus: verdicts look calibrated, plans are fabricated.

Also: gist supports the verdict, not the witness (out-of-spec whiffs survived in 2/6 lost items; WHICH still failed on both); one summary described a DENIED incident as "nominal telemetry" (gist inversion). APPROVED control moved as predicted (decision and WHICH=NONE together, 13/20 each). Caveats: lost-cell n=6; cross-budget confound between arms. A preregistered single-budget confirmatory run (v4, N=60, predictions P-A through P-D fixed in advance) is in flight. Cumulative pilot cost through v3: ≈ $0.11.

## Appendix E — LLM pilot 4: preregistered confirmation (2026-07-03, REPLICATED)

Single-budget, preregistered, fresh corpus (N=60; 30 DENIED with exactly one failing parameter; 15-word compression instruction; retention 0.372; artifacts in [results/llm-pilots/2026-07-03-grok/v4](../../../results/llm-pilots/2026-07-03-grok/v4/v4_results.json)). Predictions: P-B, P-C, P-D **pass**; P-A fails only on its floor conjunct, and informatively (below).

Headline cells (Wilson 95% CIs):

| cell | count | p | CI |
|---|---|---|---|
| DENIED decision, witness lost | 13/14 | 0.929 | [0.685, 0.987] |
| WHICH (name the reason), lost | 1/14 | 0.071 | [0.013, 0.315] |
| WHICH, retained | 15/16 | 0.938 | [0.717, 0.989] |
| REPAIR, lost | 2/14 | 0.143 | [0.040, 0.399] |

Non-overlapping CIs on the reason channel; WHICH-lost is below 1-of-3 guessing. Secondary structure, all replicated: **incoherence** (verdict DENIED + "no failing parameter", same notes) 12/14 lost vs 0/16 retained — the cleanest single behavioral signature of the shelf found so far; **confabulation locus** — witness confabulation 1/14 in identification probes vs unfounded specific repair actions **14/14** in action probes; **abstention as a near-perfect debt detector** — 13/14 uptake on lost, 0/16 false abstains on retained (the empirical face of the Law-2 abstention-delta probe).

The P-A floor failure sharpens the claim: the no-notes prior is degenerate (always-DENY, 30/60 overall), so lost-cell verdict accuracy (0.929) is indistinguishable from prior — the surviving "correct answer" carries **zero evidential content**. The shelf is a *bias shelf*: on the disjunctive side, the answer channel needs no memory at all, which is the k→0 limit of the theory (the bare quotient degenerating to a constant), while the reason channel demonstrably tracks evidence. v5 criterion: compare against a calibrated base-rate prior instead.

Cumulative cost, all four pilots: 1,134 calls, ≈ $0.15.

## Appendix F — Multi-model campaign (2026-07-03): replication, artifact-borne debt, and the limits of loss manifests

Three preregistered phases on a fresh shared corpus (artifacts in `experiments/multimodel/2026-07-03/`; total spend $1.82 across xAI/Anthropic/OpenAI; the Gemini arm was quota-infeasible — free-tier key, 20 req/day/model — and is reported as such, not as evidence).

**F.1 The dissociation is not a Grok quirk.** claude-haiku-4.5 replicates the entire v4 core preregistered: verdict survives witness destruction (18/19), naming-the-reason collapses to **0/19** (grok: 0/22), identification stays honest, action probes fabricate, abstention detects debt near-perfectly (18/19 uptake, 1/11 false). Two vendors, two training pipelines, same fibration signature. gpt-4.1-mini failed the applicability guard for the most theoretically loaded reason available: at 15 words it implements the **bare answer quotient spontaneously** — retention 0.100, summaries like "no anomalies reported" — i.e., the compressor doesn't merely lose the witness, it discards *all* fine structure and keeps gist. At 30 words (exploratory) its cells populate and the full pattern reappears.

**F.2 The calibrated-prior criterion sharpened the bias-shelf claim.** P-E asked whether the surviving verdict carries any evidential content beyond a base-rate prior, using balanced accuracy so a degenerate always-DENY prior scores 0.5. Split verdict: grok clears it (0.624), haiku does not (0.574 vs 0.487). The honest summary: **the shelf verdict is mostly prior, with at most a thin film of gist** — which is exactly what the k→0 degeneration predicts. The v4 "bias shelf" reading survives contact with a criterion designed to kill it.

**F.3 Incoherence is a phenotype, not the phenomenon.** P-F failed on haiku (1/19) — not because haiku knows more, but because it *expresses* the same debt differently: it declines to name a parameter rather than asserting "DENIED" and "no failing parameter" in adjacent breaths. The transfer grid then showed this cleanly: on *identical* artifacts, incoherence-on-lost runs 0.73–0.86 when grok/gpt read them and 0.00–0.05 when haiku reads them, and haiku's confabulated-WHICH is 0.000 for every compressor. This is Law 2's conversion claim observed across model families — **debt quantity is fixed by the artifact; the output policy of the reader chooses the phenotype** (incoherent assertion vs declination vs abstention). Consequence for evals: incoherence detectors measure the reader's policy, not the artifact's debt; abstention-delta measures the debt.

**F.4 Debt is artifact-borne (Law 2's invariance, cross-model).** P-T1 and P-T3 held with no near-misses: in all nine compressor×answerer cells, WHICH-lost ≤ 0.107 and WHICH-retained ≥ 0.909. Once the compressor destroys the witness, no reader — including a different vendor's model, including the compressor itself — recovers it; when the artifact retains the witness, every reader finds it. P-T2 (verdict survives for every reader) went 3/4 with one near-miss (grok→haiku 0.591 vs 0.6). The context-engineering reading: **in multi-model pipelines, the cheap compaction stage sets the epistemic debt of the whole system, and downstream model quality cannot buy it back.** Compaction is where justification dies; choose and audit the compactor, not the answerer.

**F.5 Loss manifests are not a fix (negative result, useful).** The cheapest debt-ledger intervention — one contract-blind `OMITTED:` line — raised abstention uptake on every model (grok 0.60→0.78, haiku 0.63→0.92, gpt 0.61→1.00) but failed its primary prediction: action-channel fabrication dropped ≥30 points only on haiku (0.94→0.54); grok and gpt fabricated repairs at 1.00 in both arms. Declaring the loss changes *epistemic* behavior (abstention) without changing *action* behavior in models whose action channel isn't already honesty-trained. This is Appendix A's retrofit-gap lesson recurring at the prompt level: honesty is a property of how the system was shaped, and metadata cannot bolt it on. What a manifest does buy: a calibrated abstention signal (the empirical face of the Law-2 probe) essentially for free.

**F.6 What this does to the roadmap.** Multi-model replication (roadmap item 2) is done for two vendors with preregistered passes; the paper-blocking items are now (a) a Gemini/open-model arm when a billed key exists, (b) the conjunctive/disjunctive coarseness sweep, (c) Law 3's transfer bound. The manifest negative result plus the transfer grid together suggest the productive intervention target is the **compactor's objective** (witness-aware compaction), not the reader's context — consistent with pilot v1, where contract-visible compression dissolved the shelf outright.

## Appendix G — Reasoning readers, quotient coarseness, and a fourth vendor (2026-07-03, follow-up)

Three cheap experiments run after Appendix F, all preregistered; artifacts under `experiments/multimodel/2026-07-03/`.

**G.1 Inference-time compute cannot buy back artifact-borne debt (the loophole closed).** Appendix F.4 left one out: perhaps a *reasoning* model, unlike the fast tier, mines subtle correlates of the destroyed witness (ordering, which values were kept) and recovers it. It does not. gpt-5-mini reading grok's witness-free summaries names the lost reason on 4/22 (0.18, CI [0.073, 0.385] — below the 1-of-3 floor) while naming every retained reason (8/8), abstains 20/22 on lost vs 0/8 on retained, and holds the verdict shelf (decision-lost 0.909). All three preregistered predictions pass. This is the strongest form of the artifact-borne-debt claim: **the debt is fixed at compaction, and no amount of downstream reasoning recovers it** — because there is nothing in the artifact to reason over. For deployment: a reasoning answerer over a compacted context inherits the compactor's epistemic debt in full; you cannot spend inference to un-drop a witness bit.

**G.2 The reason channel is retrieval, not inference — the fibration identity does not transfer to behavior.** The Shelf Width Law's base case is `M_k = Q_(k,1)`: with a single-condition policy the verdict logically *is* the reason (DENIED ⇒ the one condition failed), so witness-value loss should leave reason-naming intact. It does not. On p=1 items with the deciding value dropped, grok names the (logically forced) parameter on 2/13 and abstains on 10/13; at p=6 it names 0/16 as the coarser fiber predicts. Two things break the clean prediction: the p=1 verdict is a **pure always-DENY prior** (APPROVED accuracy 0/6 — the k→0 degeneracy of Appendix E, now reproduced by construction), and, more deeply, **the model treats "name the reason" as retrieval of the value from context, not as inference from verdict + policy structure.** The empirical dissociation is therefore *stronger* than the idealized quotient theory: even a size-1 witness fiber does not license recovery. The theory should say so — the finite quotient model is an *upper bound* on recoverable justification, and behavior-optimized readers sit strictly below it, because they don't perform the answer→witness logical collapse the quotient identifies. This sharpens Law 1: justification isn't merely gradient-orphaned during compression; at read time it is gated on *presence of the witness token*, not on its logical derivability.

**G.3 Fourth vendor, same signature (partial, free-tier).** A micro-arm sized to the Gemini free-tier quota (one probe channel per model bucket over a fixed 12-lost/8-retained sample of grok's summaries) completed two channels in gemini-3.1-flash-lite before Gemini spend was paused: reason-naming 3/12 on lost vs 8/8 on retained (P-G1 pass), abstention 11/12 vs 0/8 (P-G2 pass). The verdict channel (P-G3) was not reached. Within its n, the Google family behaves as grok, haiku, and gpt-5-mini do: the destroyed witness is unrecoverable and abstention localizes it. Four provided vendor families, one dissociation.

**G.4 Net effect on the program.** The artifact-borne-debt result now holds across four vendors and across the fast/reasoning tiers, and it survives the sharpest available attack (a reasoning reader). The one clean theoretical prediction that *failed* (p=1 recoverability) failed toward a stronger claim, not a weaker one. The productive next targets are unchanged from F.6, with G.2 adding a specific one: model the read-time reason channel as retrieval-gated, and ask whether a witness-aware compactor that emits the deciding value *as such* (not merely keeps it) closes the gap the manifest experiment could not.

## 9. The one-sentence version

**Justification is a conserved, priced resource: the shelf width is the entropy of the witness orbit, behavioral optimization always defaults on the debt, abstention is the only honest refinancing, and the bill arrives exactly when the world changes.**
