# Related-Work Positioning: The Adversarial Novelty Audit

**Status: internal positioning document (not evidence). Purpose: try to *scoop* the program.**
For every major claim, this file records the closest published work, the sharpest honest
statement of the difference, and a novelty verdict (NOVEL / PARTIALLY ANTICIPATED / SCOOPED).
A SCOOPED verdict is a success of this exercise, not a failure of the program. Compiled
2026-07-08 from a five-cluster web sweep (CoT faithfulness; prompt/KV compression; agent-memory
& summarization factuality; RAG attribution & abstention tuning; information-theory / provenance /
term-collision).

**Citation-reliability caveat.** Pre-2025 anchors (Lanham, Turpin, Kadavath, ALCE, AttributedQA/AIS,
R-Tuning, H2O/SnapKV/StreamingLLM, Wyner–Ziv, computational mechanics) are well-established and safe.
FACTUM (arXiv:2601.05866), "When Summaries Distort Decisions" (arXiv:2606.29251), the "epistemic debt"
term-collision papers (arXiv:2602.20206, viXra:2601.0013), and Łajewska et al. (arXiv:2503.19114) were
individually verified during the sweep. Several other 2026 arXiv IDs cited below (Abstain-R1 2604.17073;
Bounded-Interaction Myhill–Nerode 2603.21399; Knowledge Objects 2603.17781; Proof-Carrying Numbers
2509.06902; and the "justification gap"/CoT-compression id 2601.21576) were reported by the sweep agents
but are **not yet hand-verified** — confirm each on arXiv before putting it in an external paper. Two IDs
(2606.25449, 2605.30842) surfaced with summaries echoing this project's own framing and could not be
tied to real papers; they are excluded.

---

## Summary verdict table

| # | Claim | Verdict | Closest / scooping work |
|---|-------|---------|-------------------------|
| 1 | Within-item answer/justification dissociation under context compression | **NOVEL as a package** | Lanham 2023 (answer-survives half); Turpin 2023 (stated≠true half); danger: "When Summaries Distort Decisions" 2606.29251 (converse phenotype) |
| 2 | Law 1 (justification has no gradient) + 3-way unification | **NOVEL law; ingredient (b) SCOOPED** | FACTUM 2601.05866 owns attribution drift; L-CiteEval 2410.02115 owns citation fragility; Barez 2025 owns "CoT is lossy" |
| 3 | Debt is artifact-borne (no reader recovers a destroyed witness; reasoning can't buy it back) | **NOVEL (leaning), umbrella anticipated** | KV-eviction content-selective drop (Pitfalls 2510.00231); compression info-retention (Łajewska 2503.19114) |
| 4 | Δ = accuracy − justified-accuracy + abstention-delta diagnostic | **PARTIALLY ANTICIPATED (metric scooped; localizer novel)** | AttributedQA/AIS 2112.12870, ALCE 2305.14627, RAGAS = "justified accuracy" already |
| 5 | Exact/finite-model program (state-count gaps; honesty tax/premium; certificate and continuation quotients) | **PARTIALLY ANTICIPATED; core automata mathematics old** | Bounded-Interaction Myhill–Nerode 2603.21399; incompletely specified FSMs/closed covers; computational mechanics; orbit-stabilizer; Wyner–Ziv/IB-side-info |
| 6 | Iterated compaction settlement (loss tracks contraction; flat-at-held-length in tested arms) | **PARTIALLY ANTICIPATED; constant-ρ novelty REFUTED** | Broken Telephone 2502.20258; Factory.ai; "Beyond Exponential Decay" 2505.24187 |
| 7 | Fusion contract / self-certifying prose | **SCOOPED (numeric); PARTIALLY ANTICIPATED (general)** | Proof-Carrying Numbers 2509.06902; SAFE 2505.12621; subsentence citations 2406.06125 |
| 8 | Loss-ledger routing (deterministic dropped-names ledger + re-expansion) | **NOVEL (mechanism), high convergence risk** | Knowledge Objects 2603.17781 (same phenotype, different fix); typed-provenance memory 2605.25869 |
| 9 | Real-document narrative-valence reflex (crash→DENY, accuracy conceals) | **NOVEL as conjunction** | "When Summaries Distort Decisions" 2606.29251 (attributes flips to decontextualization, NOT valence) |
| 10 | Calibrated debt-acknowledgment fine-tuning | **PARTIALLY ANTICIPATED, trending SCOOPED on phenotype** | Abstain-R1 2604.17073 (abstain + name-missing-evidence); context-faithful abstention tuning; R-Tuning 2311.09677 |
| — | The **term** "epistemic debt" / "justification gap" | **TERM SCOOPED (collision, not meaning)** | 2602.20206, viXra:2601.0013 (human-comprehension sense); Levine (phil-of-mind); CoT "justification gap" 2601.21576 |

---

## The three most dangerous nearby works overall

1. **"When Summaries Distort Decisions: Information Fidelity in LLM-Compressed Financial Analysis"**
   (Lee et al., 19 authors incl. Lopez-Lira & Zhangyang Wang, arXiv:2606.29251, 28 Jun 2026 — **verified, ~10 days old**).
   Independently instantiates the program's core experimental skeleton — *blind LLM compression of real
   documents that silently drops evidence and flips downstream decisions* — with evidence-retention
   quantified (context facts 25%→9%) and decision flips on 33% of real SEC filings. It threatens claims 1,
   3, and 9 at once. **Defensible daylight, which must be held explicitly:** (i) they attribute flips to
   *decontextualization / dropped qualifiers*; the program attributes them to a *content-free
   narrative-valence reflex* — a stronger, more falsifiable mechanism, but only if the program *dissociates
   valence from caveat-loss* (run their add-back diagnostic on the NTSB corpus). (ii) They measure decision
   *flips*; the program's justified-accuracy metric also catches the *spuriously preserved* correct answer
   (answer survives, justification dies) that a flip-rate misses. (iii) They report an aggregate flip rate;
   the program exposes an *asymmetric class collapse* (APPROVED→~0) that averaging hides. Cite prominently
   or a reviewer calls row 31 a special case of this paper.

2. **FACTUM — "Mechanistic Detection of Citation Hallucination in Long-Form RAG"** (Dassen, Yates, Duh
   et al., arXiv:2601.05866, 2026 — **verified; the theory doc's citation is accurate**). Owns one of the
   three phenomena Law 1 wants to unify (attribution drift), and does so *mechanistically*: FFN pathway
   forces the claim while the attention pathway fails to ground the citation — a "coordination failure
   between reading and recalling pathways." A skeptic can argue FACTUM already supplies the mechanism
   ("answer/parametric pathway defended, grounding/witness pathway not") and the program merely relabels
   it a "law." Concede attribution drift to FACTUM; stake Law 1's novelty on *directionality*, the
   *optimization derivation*, and *cross-phenomenon unification* — none of which FACTUM claims.

3. **Bounded-Interaction Myhill–Nerode (Agent-Bounded Indistinguishability)** (arXiv:2603.21399, Mar 2026
   — reported, not hand-verified). Independently formalizes the exact structural core of the exact-model
   program: a canonical/minimal quotient under a bounded observer, a coarser operational quotient, the *gap
   between them quantified*, and a value-transfer bound on that gap — in an exact/finite setting. It lacks
   only the calibration-and-gauge interpretation. If someone attaches "coarse quotient = actionable answer,
   fine quotient = justification, gap = economic honesty cost," claim 5's math is largely subsumed. The moat
   is the interpretive layer plus the measured honesty-premium numbers — not the quotient identity.

---

## Per-claim positioning

### Claim 1 — Within-item answer/justification dissociation under context compression

**Closest works.** Lanham et al., *Measuring Faithfulness in CoT Reasoning* (Anthropic 2023,
arXiv:2307.13702) — establishes "answer robust to CoT ablation," but ablates the model's own generated
reasoning, never the source artifact, and never pairs it with reason-naming collapse. Turpin et al.,
*Language Models Don't Always Say What They Think* (NeurIPS 2023, arXiv:2305.04388) — the ancestral
dissociation (stated reason ≠ operative cause), but via bias injection, and the justification is *wrong*,
not *absent/below-chance*. Lee et al. 2606.29251 — nearest *compression* neighbor, but reports the
*converse* (compression *moves* the answer). "Correct Chains, Wrong Answers" (arXiv:2604.13065, reported)
— a within-item dissociation in the *mirror* direction (right reasoning, wrong answer), no compression.

**Sharpest difference.** Every ingredient exists separately; no published work assembles the specific
configuration: (i) perturbation = lossy compression of the *source artifact*; (ii) answer held *correct*
while (iii) reason-naming from the *same compressed notes* drops *below chance*; (iv) reason-naming shown
to be *gated on witness-token presence in the artifact, not on derivability* (the program's G.2/M
finding). Element (iv) — reason recovery as a presence/retrieval problem, quantified within-item — was
not found anywhere.

**VERDICT: NOVEL as a package.** "Answer survives compression" is PARTIALLY ANTICIPATED by Lanham;
"stated reason ≠ true reason" by Turpin. The within-item, below-chance, witness-token-gated reason
collapse under *source* compression is the load-bearing, unanticipated contribution.

### Claim 2 — Law 1 (justification has no gradient) + unification of three phenomena

**Closest works.** FACTUM (2601.05866) — *owns* attribution drift as a phenomenon, mechanistically.
L-CiteEval (Tang et al., arXiv:2410.02115, ACL 2025) — *owns* "citation quality more fragile than answer
quality under long context," as a benchmark finding. Barez et al., *Chain-of-Thought Is Not Explainability*
(Oxford WhiteBox 2025) — the nearest *theory* neighbor: CoT is a "lossy projection" of distributed
computation. "Mechanistic Evidence for Faithfulness Decay in CoT" (arXiv:2602.11201, reported) — a
"reasoning horizon" at 70–85% of chain length, but empirical, no inevitability derivation.

**Sharpest difference.** Three moves no single prior work makes: (a) **directionality as a law** — witness
bits shed *before* answer bits, *because* answer bits are gradient-defended and justification bits
gradient-orphaned (the "lossy projection" framing is symmetric about *what goes first*); (b)
**inevitability vs observation** — a loss-geometry derivation of shedding as structural, not an empirical
report (not found published); (c) **cross-phenomenon unification** of CoT unfaithfulness + attribution
drift + citation fragility as *one predicted effect* (the surveys taxonomize; they do not fuse). The
unification is the most distinctive and most *exposed* claim: a skeptic will say the three phenomena share
only a family resemblance unless Law 1 emits a falsifiable prediction the component literatures don't.

**VERDICT: NOVEL in its two central moves (directional shedding law + three-way unification); ingredient
(b) attribution drift is SCOOPED by FACTUM and must be cited as prior, (c) citation fragility is
established by L-CiteEval, and the "CoT is lossy/structural" intuition is prior (Barez).** Novelty rests
entirely on delivering the falsifiable prediction — currently the toy-SGD half-life lemma is a target,
not a result.

### Claim 3 — Debt is artifact-borne (no reader recovers a destroyed witness; reasoning can't buy it back)

**Closest works.** "The Pitfalls of KV Cache Compression" (Chen et al., arXiv:2510.00231, 2025) — under
KV eviction, *certain instructions degrade far faster than average and are silently dropped*
(content-selective loss, system-prompt-leakage case study). Łajewska et al. (arXiv:2503.19114, EMNLP 2025
Findings) — separates *information retention* from *downstream performance*; accuracy can hold while
entities are dropped. Neither runs a multi-model transfer grid nor a *counterfactual re-query* keyed to
which evidence was destroyed.

**Sharpest difference.** The umbrella intuition — "compression drops specific load-bearing tokens while
accuracy looks fine" — is now published (2510.00231, 2503.19114). What is *not* anticipated: the
**invariance result** that once the compactor destroys the witness, *no downstream reader recovers it* —
not a different vendor, not a reasoning model, not the compactor itself — so *compaction sets the debt of
the whole pipeline*. That "compaction is where justification dies; downstream quality can't buy it back"
cross-model transfer statement occupies an empty slot.

**VERDICT: NOVEL (leaning), umbrella PARTIALLY ANTICIPATED.** Cite 2510.00231 and 2503.19114 as the
nearest "compression drops load-bearing content" prior; lead with the *artifact-borne / non-recoverable
across readers* invariance, which they do not measure. Caveat honestly against the program's own I.3/M
findings: string-survival S is a *conservative lower bound* — readers recover some witnesses by
elimination or one arithmetic step, so "destroyed" is not always "unrecoverable."

### Claim 4 — Δ = accuracy − justified-accuracy + abstention-delta diagnostic

**Closest works.** AttributedQA / AIS (Rashkin et al., *Computational Linguistics* 2023,
arXiv:2112.12870; Bohnet et al.) — reports the fraction of *correct* answers that are *attributable*;
"right AND deciding-evidence-recoverable" is answer-correctness ∩ AIS, i.e. justified accuracy under
another name. ALCE (Gao et al., EMNLP 2023, arXiv:2305.14627) — correctness and citation precision/recall
side by side, including the "correct-but-unattributable" quadrant, with lossy passage compression. RAGAS,
HELMET (Yen et al., ICLR 2025, arXiv:2410.02694), FACTS Grounding — correct ∧ grounded is standard
practice. Selective-prediction / forced-answer-accuracy (AbstentionBench, arXiv:2506.09038) — the
abstention-delta *mechanism* (forced answers on would-abstain items collapse accuracy) is already in use,
aggregate.

**Sharpest difference.** No one packages accuracy-minus-grounded-accuracy as a single headline scalar Δ —
but that is a *presentational repackaging* of an existing decomposition (correctness × attribution), not a
new measurement. The genuinely under-claimed piece is the **abstention-delta as a *localizer*** — using
the with/without-abstain *divergence set* to identify *which specific correct answers were unjustified*.
The abstention literature uses abstention to reduce error / trade coverage for risk; the "right for the
wrong reasons" line (McCoy et al., HANS 2019) localizes unjustified correctness but via sub-questions, not
abstention divergence.

**VERDICT: PARTIALLY ANTICIPATED.** The metric is *scooped in substance* — "justified accuracy" =
answer-correctness ∩ AIS/faithfulness. The scalar Δ is cosmetic. The abstention-delta-as-localizer is the
one novel, defensible seed. Drop any claim that Δ-the-metric is new; keep the emphasis on the localizer
and on doing it *under memory compression* (the attribution line evaluates single-turn RAG with passages
in-context — a citing failure, not an eviction failure).

### Claim 5 — Exact/finite-model program (count gaps; honesty tax/premium; certificate and continuation quotients)

**Closest works.** Bounded-Interaction Myhill–Nerode (arXiv:2603.21399, reported) — coarse-vs-fine
quotient hierarchy under a bounded observer, with the gap quantified and converted to a value-transfer
bound: the structural skeleton of the M→Q fibration minus the calibration/gauge reading. Computational
mechanics (Shalizi–Crutchfield, *J. Stat. Phys.* 2001) — causal states = minimal sufficient statistic;
statistical complexity C_μ; shelf width = conditional entropy of a finer causal partition given a coarser
predictive one. Wyner–Ziv (1976) / IB-with-side-information (privacy funnel, arXiv:1402.1774) — the rate
functional has the I(Z;W)−I(Z;Y) shape the risk register already flags. Orbit-stabilizer (folklore) —
log|orbit| = log|G|/|Stab| reproduces "gauge-orbit volume" in one line.

**Ruling on the IB-triviality objection (the risk register's own item).** *Not fatal to the framework, but
fatal to any claim that the quantity is new.* log₂|Q|/|M| = H(witness-class | answer-class) is a well-worn
object (orbit-stabilizer, Myhill–Nerode index, conditional entropy of nested sufficient statistics,
C_μ-vs-coarser-partition gap). The narrow "it's IB-trivial" phrasing is *wrong on the details* — IB is a
soft variational frontier over stochastic encoders with a distortion knob, while shelf width is an exact
combinatorial index of a quotient refinement; they coincide only in the deterministic/uniform corner. But
the broader "known information measure in new clothes" objection *lands*. The honesty tax/premium
*direction* (bolt-on costs more than build-in) is also now established literature (AbstentionBench
2506.09038; TruthRL 2509.25760; "Honesty over Accuracy" 2511.11500 — all reported: abstention needs
training-time intervention, degrades under post-hoc RLVR).

**VERDICT: PARTIALLY ANTICIPATED.** The math (fiber/orbit/quotient entropy) is old and independently
reformalized in 2603.21399; the gauge language is presentation. The novel, defensible contributions are
(a) the calibration/economic *interpretation* of the fiber as a priced "shelf," (b) the *exact
honesty-premium accounting* with measured multipliers (18–38× retrofit vs 0.47× build-in), and (c) the
*certificate-quotient split* (Appendix L) — an intermediate state between answer and full witness — which
no neighbor articulates. Claim the interpretation and the numbers, not the identity "shelf = fiber
entropy," which is a definitional restatement.

### Claim 6 — Iterated compaction settlement (contraction-gated loss, flat held-length survival)

**Closest works.** Zhu et al., *LLM as a Broken Telephone: Iterative Generation Distorts Information*
(arXiv:2502.20258, 2025) — 100 iterations, FActScore drift; finds roughly *linear/steady* per-iteration
decay and *explicitly argues against* an accelerating/exponential pattern; specifics erode while narrative
persists. Factory.ai, *Evaluating Context Compression* (practitioner, 2025–26) — per-cycle retention split
by type: semantic knowledge resilient (~62% at cycle 3), episodic facts vulnerable (~31.5%) — gist
survives, facts decay across rounds. Shumailov et al., *The Curse of Recursion / model collapse* (Nature
2024) — rare/tail content dies first under recursive *training* (not inference-time compaction). "Beyond
Exponential Decay: Rethinking Error Accumulation in LLMs" (arXiv:2505.24187, reported) — *disputes* clean
geometric decay directly.

**Sharpest difference.** Already published: iterated processing erodes specifics while gist survives,
and rare content dies first. The original fixed-ρ reading is now refuted by this program's own cached
re-analysis and length-clamped successor: ρ̄≈0.93 was a length-settling transient. In the tested arms,
survival is nearly flat when realized length is held and loss concentrates at forced contractions,
while verdicts remain flat. This is a useful empirical decomposition, not yet a universal law.

**VERDICT: PARTIALLY ANTICIPATED; CONSTANT-ρ NOVELTY RETIRED.** Keep the exact cached counts and the
preregistered per-model clamp result. Do not sell a stable interest rate, panel-wide settlement law, or
the qualitative “details erode while gist stays” observation as new. The remaining contribution is the
measurement design that separates repetition from contraction and the state-function hypothesis it
motivates.

### Claim 7 — Fusion contract / self-certifying prose (never assert without the witness in-clause)

**Closest works.** Proof-Carrying Numbers (arXiv:2509.06902, reported) — "each numeric claim includes a
checkable witness, verified at the point of assertion, in the same output": the fusion contract
specialized to numbers. Proof-Carrying Certificates for LLM Pipelines (arXiv:2605.16407, reported). SAFE:
Sentence-Level In-generation Attribution (arXiv:2505.12621, reported) and Verifiable Generation with
Subsentence-Level Citations (arXiv:2406.06125) — claim and justification in the same span, enforced at
generation time. Annotation/Arthur–Merlin streaming (Chakrabarti et al.) — space-bounded verifier with a
short certificate, but relies on an *external* prover; JSPACE folds prover and algorithm together
(generator certifies itself).

**Sharpest difference.** The generalization from "numeric witness" (PCN) to "any evaluative claim carries
its deciding value in-clause, enforced at the *prose register*" is real but *thin*. Only the register-level
discipline (self-certifying prose as a compaction *contract*, not a post-hoc check) is not directly
covered.

**VERDICT: SCOOPED for the numeric case (PCN 2509.06902); PARTIALLY ANTICIPATED for the general evaluative
form.** JSPACE-as-self-certification reads as a reframing of annotation-streaming + self-verification, not
a new complexity model. Position the fusion contract *explicitly as generalizing PCN* to non-numeric
evaluative claims at the register level, or it reads as reinvention. (The empirical B5a finding — the
fusion rule *overrides* the word budget, an instruction-hierarchy result — is a distinct, unclaimed
observation and is the freshest part of this row.)

### Claim 8 — Loss-ledger routing (deterministic dropped-names ledger + re-expansion)

**Closest works.** *Facts as First-Class Objects: Knowledge Objects for Persistent LLM Memory*
(arXiv:2603.17781, Mar 2026, reported) — independently reports the program's *exact calibrated-abstention
phenotype* after compaction (40% correct / 60% "I don't have that specific information" / 0%
hallucinated; constraints decay to 46% "with full confidence") — but *bypasses* compaction via external
hash-addressed storage; it does not log dropped facts or re-expand. *Mitigating Provenance-Role Collapse
via Typed Memory* (arXiv:2605.25869, reported) — typed memory atoms with provenance metadata, but for
retained content, not a dropped-fact debt ledger. Provenance fact-checkers (arXiv:2411.01022) track *what
was used*, not *what was dropped*.

**Sharpest difference.** No one logs *dropped* value-names as a reclaimable, deterministic debt ledger with
a Δ=0-by-construction floor and query-triggered re-expansion. The field either tracks provenance of
*retained* content, or *avoids* compaction entirely. The loss-ledger occupies an empty slot.

**VERDICT: NOVEL (mechanism), high convergence risk.** The *problem framing* (compaction loss is
architectural; the calibrated-abstention phenotype) is now common and independently corroborated by
2603.17781 — which strengthens the empirical claim but threatens to scoop the *observation*. The specific
loss-ledger-router / debt-floor construction is not anticipated. Ship soon; cite 2603.17781 as convergent
evidence, not prior art for the mechanism. Honest caveat: J ≥ S (row 24) means the ledger is a *floor*,
not an estimator — it can prove a value was dropped, not certify what a reader can still justify.

### Claim 9 — Real-document narrative-valence reflex (crash→DENY; accuracy conceals answer-unreliability)

**Closest works.** Lee et al. 2606.29251 — blind compression of real SEC filings flips the decision on
33% of filings (11% noise floor), context facts 25%→9%, but attributes flips to *decontextualization
(dropped caveats/qualifiers), explicitly NOT sentiment/tone*. AMEL: Accumulated Message Effects
(arXiv:2605.22714, reported) — negative *evaluation history* biases verdicts negative (1.62× asymmetry),
multi-turn, not compression. "ChatGPT Reads Your Tone" (arXiv:2507.21083, reported) — exogenous *prompt*
tone shifts outputs, not endogenous document valence. "Fixed RAG Compression Collapses Measured Reader
Scaling" (arXiv:2606.21807, reported) — compression raises average accuracy while *hiding* a collapse (same
"aggregate conceals compression-induced collapse" structure, different hidden quantity).

**Sharpest difference, sub-claim by sub-claim.** (a) *Valence overrides content in a categorical decision*
— PARTIALLY ANTICIPATED: AMEL and tone-framing show valence steering verdicts, but always via *exogenous*
affect; endogenous-document-valence overriding a co-located explicit policy is sharper. (b) *Compression
specifically induces the affect reflex* — **NOVEL**: 2606.29251 is the near-miss and attributes the same
decision-flips to dropped qualifiers, not tone, leaving the affective mechanism unclaimed. (c) *Plain
accuracy hides a class-specific collapse (APPROVED→0)* — PARTIALLY ANTICIPATED generically (balanced
accuracy is textbook), novel in this conjunction; the justification-conditioned metric is stricter than
balanced accuracy.

**VERDICT: NOVEL as a conjunction; PARTIALLY ANTICIPATED in its parts.** The compression→valence-reflex
mechanism is unscooped. Mandatory: cite 2606.29251, position against its decontextualization framing, and
*demonstrate valence (not mere caveat-loss) is the driver* — run their add-back diagnostic on the NTSB
corpus — or a reviewer calls row 31 a special case of 2606.29251.

### Claim 10 — Calibrated debt-acknowledgment fine-tuning

**Closest works.** Abstain-R1 (*Calibrated Abstention and Post-Refusal Clarification via Verifiable RL*,
arXiv:2604.17073, 2026, reported) — RLVR-trained not just to abstain but to **identify the key missing
piece of information**, with a reward that *verifies* the model named the missing item: nearly the exact
"the readings are absent" phenotype, on under-specified inputs. R-Tuning (Zhang, Diao et al., NAACL 2024
Outstanding, arXiv:2311.09677) — refusal on the model's *parametric* knowledge boundary; the program's
context-vs-parametric contrast is real *against R-Tuning specifically*. Context-faithful prompting (Zhou
et al. 2023, arXiv:2303.11315) and "Do RAG Models Know When They Don't Know?" (arXiv:2509.01476, reported)
— abstaining when the *provided context* is insufficient (context-grounded, not parametric). Unanswerable-QA
tuning (SQuAD 2.0 lineage).

**Sharpest difference.** The R-Tuning distinction the program leans on (context vs parametric) is genuinely
real — but it is *not the program's to claim*, because context-faithful / unanswerable-from-context tuning
already occupies that niche, and **Abstain-R1 additionally trains the model to *name the specific missing
evidence*** — the "calibrated debt-acknowledgment" behavior almost verbatim. The only remaining daylight is
the *framing* (memory-pressure / context-compaction as the cause of the dropped witness) and the "debt"
accounting vocabulary — not the trained behavior.

**VERDICT: PARTIALLY ANTICIPATED, trending SCOOPED on the phenotype.** Distinct from R-Tuning, yes — but
that distinction is already made by context-faithful/unanswerable-QA abstention tuning, and Abstain-R1
trains the "abstain AND state the missing evidence" behavior directly. Do not sell the fine-tuned phenotype
as new; position it as a domain-specific instance (context-compaction-induced evidence loss) and benchmark
*against* Abstain-R1. (Related, from claim 4's cluster: "incoherent confidence" — verdict asserted + basis
denied in the same output — appears to be an unclaimed *named* phenotype; it is the narrow NOVEL seed in
this neighborhood and should carry the calibration-quality framing rather than the fine-tune.)

### The term itself — "epistemic debt" and "justification gap"

**"Epistemic debt" is already taken, multiply, in 2026, in a different sense.** arXiv:2602.20206
(*Mitigating "Epistemic Debt" in Generative AI-Scaffolded Novice Programming*); viXra:2601.0013 (*The
Illusion of Competence: Defining "Epistemic Debt"* — "fragile experts"); arXiv:2604.26855 (*Cognitive
Atrophy…*); failingfast.io ("AI Epistemic Debt: The Hidden Cost of AI Speed"). Every prior usage means a
**human comprehension gap** — shipping code/answers people don't understand. The program's meaning — *a
machine holding a correct answer whose justification is lost under compression* — is orthogonal, but the
software/KM sense is dominant and faster-growing. This is a real brand collision.

**"Justification gap" collides twice:** Levine's explanatory/justification gap in philosophy of mind
(consciousness) — unrelated, pure citation-collision risk; and, more dangerously, an *adjacent* usage in
CoT-compression work ("justification gap" for problems where compression removes steps needed to justify
the answer, cf. arXiv:2601.21576 — reported, verify) — semantically near the thesis, so a reader may assume
derivation.

**VERDICT: TERM SCOOPED (collision, not meaning).** "Epistemic debt" is unavailable as a clean handle;
"justification gap" has an adjacent live usage. Either disambiguate explicitly on first use ("epistemic
debt — the machine-internal, justification-loss sense, distinct from the human-comprehension usage of
[2602.20206]") or adopt a distinct primary handle. The program's own coinages that appear *un-collided* —
"the mirage shelf," "shelf width," "witness quotient," and "artifact-borne debt" — are safer brand
anchors than "epistemic debt." The retired "interest rate" framing should not be used as a brand anchor.

---

## What the paper can honestly claim as new

The program's defensible novelty is a **coherent bundle around one axis no existing line crosses: the
answer/justification split induced *specifically by memory/context compression*, measured *within-item*,
and *priced***. Concretely, the parts that survived the adversarial sweep:

1. **The within-item, below-chance, witness-token-gated reason collapse under source compression** (claim
   1, element iv) — the single cleanest unanticipated empirical result. Reason recovery is a *presence*
   problem, not an inference problem, quantified per item.
2. **Artifact-borne / non-recoverable-across-readers debt** (claim 3) — compaction fixes the pipeline's
   debt; no downstream reader (other vendor, reasoning model, the compactor itself) buys it back. The
   multi-model transfer invariance is not in the compression literature.
3. **The narrative-valence reflex under compression** (claim 9b) — a distinct, more falsifiable mechanism
   than the decontextualization account of the nearest neighbor, *if* dissociated from caveat-loss.
4. **The exact honesty-premium accounting and the certificate-quotient split** (claim 5b/c) — measured
   retrofit-vs-build-in multipliers and an intermediate answer↔witness state that no neighbor formalizes.
5. **The abstention-delta as a *localizer*** of unjustified-but-correct answers (claim 4) — as opposed to
   the abstention literature's use of abstention to reduce error.
6. **"Incoherent confidence" as a named, jointly-measured phenotype** (verdict asserted + basis denied in
   one output) — narrowly novel within calibration/faithfulness.
7. **The loss-ledger router / bounded-debt-memory construction** (claim 8) — an empty architectural slot
   (log *dropped* names as a reclaimable debt floor), distinct from provenance-of-retained-content.
8. **The contraction-versus-repetition decomposition** (claim 6) — a preregistered, per-model empirical
   result and state-function hypothesis; the earlier constant-ρ novelty claim is retired.

The unifying framing — "being right and knowing why are different priced resources, and compression sells
justification first" — is a *synthesis* whose novelty is the assembly and the pricing, not any single
component.

## What must be cited and conceded

- **Attribution drift is FACTUM's** (2601.05866). Cite it; do not present it as a program prediction newly
  confirmed — it is prior art for phenomenon (b) of Law 1.
- **Citation fragility under long context is L-CiteEval's** (2410.02115). Cite as the established form of
  Law 1's phenomenon (c).
- **"Justified accuracy" already exists** as answer-correctness ∩ attribution (AttributedQA/AIS 2112.12870;
  ALCE 2305.14627; RAGAS). Concede the metric; claim only the localizer and the compression regime.
- **"Compression preserves answers while dropping load-bearing details" is published** (Łajewska et al.
  2503.19114, EMNLP 2025; Pitfalls of KV Cache Compression 2510.00231). Do not claim discovery of the bare
  dissociation; build on it.
- **The fusion contract is a generalization of Proof-Carrying Numbers** (2509.06902) and sentence-level
  in-generation attribution (SAFE 2505.12621). Position as generalization, not invention.
- **The calibrated-abstention *phenotype* is Abstain-R1's territory** (2604.17073) and the
  context-vs-parametric distinction is context-faithful abstention tuning's, not R-Tuning-vs-us. Benchmark
  against Abstain-R1.
- **The real-document compression→decision-flip experiment was independently run** (2606.29251, ~10 days
  before this audit). Cite prominently; hold the valence-vs-decontextualization and
  spuriously-preserved-answer daylight explicitly.
- **The quotient math is old** (Myhill–Nerode / orbit-stabilizer / computational mechanics C_μ;
  independently reformalized in 2603.21399). Concede the measure; claim the interpretation and the numbers.
- **The IB-triviality objection is not fatal but half-right**: the *quantity* is a known information
  measure; the *framework* (exact combinatorial index + economic interpretation) is not IB. State this
  distinction pre-emptively.
- **The term "epistemic debt" is taken** in an adjacent (human-comprehension) sense. Disambiguate or
  rename.

---

## Proposed integrations

Suggested one-line edits for the lead to apply (this file does not touch README, the theory doc, or the
site directly).

**For `README.md`** — add a one-line honesty note under the results table or in a new "Related work &
priority" stub:

> *Related work / priority (2026-07-08 audit → [related-work-positioning.md](related-work-positioning.md)):*
> *The answer/justification split is anticipated in parts — compression drops load-bearing content while
> accuracy holds (Łajewska et al., EMNLP 2025; "Pitfalls of KV Cache Compression" 2510.00231), attribution
> drift is FACTUM's (2601.05866), "justified accuracy" ≈ attribution-QA (AttributedQA/AIS; ALCE), and the
> real-document compression→decision-flip experiment was run independently ~10 days prior ("When Summaries
> Distort Decisions," 2606.29251). The program's defensible novelty is the bundle: within-item
> witness-token-gated reason collapse, artifact-borne non-recoverable debt, the priced honesty
> premium/certificate quotient, and the loss-ledger router. The term "epistemic debt" collides with a
> human-comprehension usage (2602.20206) — used here in the machine-internal justification-loss sense.*

**For the theory doc's risk register (§8)** — three lines to append (do not delete the existing
Myhill–Nerode/ε-machines/Vorob'ev item; sharpen it):

> - *Priority exposure, empirical:* "When Summaries Distort Decisions" (2606.29251, Jun 2026) independently
>   runs blind real-document compression that silently drops evidence and flips decisions. Row 31 must cite
>   it and hold the valence-vs-decontextualization + spuriously-preserved-answer daylight, or it reads as a
>   special case.
> - *Priority exposure, phenomenon:* attribution drift is owned by FACTUM (2601.05866); Law 1 must cite it
>   as prior for phenomenon (b), and the "justified accuracy" metric must concede AttributedQA/AIS/ALCE.
>   Calibrated debt-acknowledgment FT (B4) must benchmark against Abstain-R1 (2604.17073).
> - *Quotient-math exposure:* Bounded-Interaction Myhill–Nerode (2603.21399) independently reformalizes the
>   coarse/fine quotient gap in an exact setting. Sharpen the existing risk item: the moat is the
>   calibration interpretation + honesty-premium numbers + certificate/continuation obligations.
>   The earlier bare identity “shelf = fiber entropy” is not established: the natural
>   answer-preserving map has nonconstant fibers, and the global count ratio is not automatically
>   Shannon conditional entropy.
> - *Term collision:* "epistemic debt" is taken in the human-comprehension sense (2602.20206, viXra
>   2601.0013); "justification gap" collides with Levine and an adjacent CoT-compression usage. Disambiguate
>   on first external use.

**For the site (`site/index.html`)** — the page must never out-claim the ledger. Two suggestions: (1) add a
one-line "Prior & concurrent work" footnote near the thesis, conceding the compression-faithfulness line
and 2606.29251, so the page reads as honest synthesis rather than sole discovery; (2) on first use of
"epistemic debt," add a parenthetical distinguishing it from the human-comprehension sense. No evidence-label
chip changes are implied by this audit — it is positioning, not a new result.
