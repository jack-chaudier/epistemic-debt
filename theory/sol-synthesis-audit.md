# Sol synthesis audit: exact memory under evolving contracts

**Audit date:** 2026-07-09/10

**Auditor:** Sol, independent synthesis judge

**Baseline:** `f3c460603bb13fc68465d6ea074c3f7515c1d27e`

**Audit branch/worktree:** `codex/sol-synthesis-audit` at `/Users/jackg/Developer/active/justification-gap-sol-audit`

**Publication scope:** the audit was produced without merging, publishing, or editing the
site. A later explicit user request authorized committing and pushing this report, the
`reach.md` synthesis, and their ledger/queue entries on the isolated audit branch. The
follow-up also includes the narrow `m*v>=2` consistency correction on the README,
research ledger, and static site required by the repository's public-claim rules. It
does not authorize a merge, deployment, pull request, public novelty claim, or import
of either upstream agent's uncommitted worktree.

## 1. Executive verdict

**NOT YET.**

The two investigations found real theorem-level structure, but they did not find a
world-changing theory of infinite, non-degrading context. The strongest positive
result is a sharply scoped exact state theorem for sparse, exogenously scheduled
checkpoint obligations over an immutable, fixed ontology. The strongest negative
result says that a verifier of complete justification must probe archive coordinates
that hit every same-visible-state falsifier. Both matter. Neither is yet a new
architecture-independent conservation law.

Most of the unrestricted theory reduces to established objects:

- retained-state fibers and continuation equivalence reduce to sufficient views and
  Myhill--Nerode-style residual behavior;
- archive-free future answering is view determinacy;
- archive-free update is materialized-view self-maintainability;
- active-state refinements are conditional data-structure/decision-tree problems;
- accepting-proof archive access is certificate or nondeterministic decision-tree
  complexity;
- overlapping state blocks are compatible blocks and closed covers of incomplete
  machines;
- one-read historical snapshots are persistence, with the information paid in the
  archive.

There is a useful synthesis: **state sufficiency, answer reconstruction, and proof
verification are three different geometries on the same retained-state fiber.** A
single scalar such as obligation count, answer entropy, split multiplicity, proof
length, or “context density” cannot govern all three. That synthesis explains why
several tempting laws fail. Its clauses are, however, substantially classical. It is
a research map, not yet a new foundational invariant.

### Verdicts

| Subject | Verdict | Reason |
|---|---|---|
| Fable / Claude | **STRONG SPECIALIZED RESULT**, with one **FALSE** generalization and several open claims | The exact flexible two-sided optimum for `Q_{k,p}` and several counterexamples survive. The later storage-independent refinement slogan contradicts Fable's own storage-sensitive counting bound. The “anchored” converse and semilattice representation are unproved. |
| Codex 5.6 | **STRONG SPECIALIZED RESULT + CLASSICAL REFRAMING + NEGATIVE BOUNDARY** | Its exact formulas, checkpoint phase theorem, rank specialization, and finite verifier-hitting theorem reproduce. It correctly refuses the foundational verdict and records the free schedule, trusted summary, fixed ontology, and nonuniform-verifier limitations. |
| Combined result | **CLASSICAL REFRAMING**, with a promising **INTERESTING CONJECTURE** about coupling the three geometries online | The conjunction is more diagnostically useful than either report alone, but no new matched upper/lower law couples active state, index storage, probes, proof repair, and contract refinement. |

### What “infinite context” must mean

Let `H_n` be the length-`n` histories, `s_n : H_n -> S_n` the active retained
state, `D_n(h)` an optional external archive/index, and `q` a contract that maps a
history to an exact answer or a set of acceptable answer/certificate pairs. The
phrase “infinite context” otherwise conflates at least eight different requirements:

1. **Raw-history retention.** The total representation `(s_n,D_n)` is injective on
   histories. This permits exact reconstruction, but says nothing about active RAM or
   query time.
2. **Fixed-contract exactness.** A fixed family `Q` announced before ingestion factors
   through `s_n`, or through bounded probes to `D_n`. This can require exponentially
   less information than raw retention.
3. **Adversarial post-hoc exactness.** Every future query in a rich class is supported
   after compression. If the class contains all history distinctions, total retained
   information must be injective or supplied by an equivalent external service.
4. **Exact justification.** The output includes locally sound and complete provenance,
   not merely the correct answer. Proof validity may require archive access even when
   the answer itself is state-determined.
5. **Contract or ontology evolution.** The semantics can split old state fibers after
   ingestion. A migration must then obtain the missing conditional information,
   restrict the extension, fall back, or accept error.
6. **Active-state bounds.** Bounded, logarithmic, sublinear, or amortized active state
   concerns `log |S_n|` (or a charged encoding), not the total bits in archives,
   indexes, snapshots, proof caches, schedules, and version services.
7. **Permitted services and time.** External archives, authenticated indexes, retrieval
   oracles, lossy approximation, bounded error, and unbounded reconstruction time are
   separate resource choices. A theorem must charge or explicitly assume each one.
8. **Operational non-forgetting versus information retention.** A system can appear
   never to forget for its supported contracts while irreversibly merging histories
   that an unanticipated contract would distinguish. Conversely, a persistent raw log
   retains all information while offering no bounded active-state or query-time
   guarantee.

Only the first and third meanings approach universal retention. The positive theorems
here establish the second, fourth only relative to a trusted frontier primitive, and
restricted forms of the fifth through seventh.

## 2. Chain of custody and reproduction

### 2.1 Located artifacts

No output was silently substituted for another. The repository states were inspected
with `git worktree list`, branch resolution, status, baseline diffs, file inventories,
and content hashes.

| Package | Location and branch | Base/HEAD | State against baseline | Primary artifacts | Custody status |
|---|---|---|---|---|---|
| Shared baseline | `/Users/jackg/Developer/active/justification-gap` / `main` as named by the brief | `f3c460603bb13fc68465d6ea074c3f7515c1d27e` | Baseline commit subject: “Establish exact continuation theory and correct evidence scope” | Existing theory, proofs, tests, ledger, `NEXT.md` | Reproduced in the clean Sol worktree before audit changes. |
| Fable / Claude | `/Users/jackg/Developer/active/justification-gap/.claude/worktrees/infinite-context-theory-7da1b2`; branch `claude/infinite-context-theory-7da1b2` | HEAD exactly `f3c4606...` | All output is untracked under `dossier/`; no branch commit | `dossier/DOSSIER.md`; 29 Python validators | Located. Dossier says a C2 semilattice validator was pending/being added, but no such file exists. |
| Codex 5.6 | Original main worktree `/Users/jackg/Developer/active/justification-gap` | HEAD still `f3c4606...` | 9 modified tracked files and 20 untracked artifacts; no commit | `theory/infinite-context-boundary.md`, 8 new proof/result files, dual general-search implementations, reference experiment, tests, ledger edits | Located as an uncommitted worktree package. Its status was unchanged after reproduction. |
| Sol audit | `/Users/jackg/Developer/active/justification-gap-sol-audit`; branch `codex/sol-synthesis-audit` | Created from `f3c4606...` | Separate clean worktree before this report | At the audit snapshot, this file only; a follow-up adds `reach.md` and explicit ledger/queue entries | Isolated from `main`, Fable, and Codex output trees. |

At the custody snapshot (2026-07-10 02:05 UTC):

- Fable contained 30 source artifacts (one dossier plus 29 validators), 10,788
  aggregate lines, source-tree SHA-256
  `b2deb8424fb6bb011b9ca3ea1ea6e1b9ede2c80d3e0425ad42d987819453425d`, and
  dossier SHA-256
  `480cd76c22dde61b857b8e06e32d92a497ec4b9292d81e85727e4ce017c6daed`.
- Codex contained 29 changed artifacts, 11,206 aggregate lines, changed-source
  SHA-256 `4846e48247dbd82f36f92d6afe64a43a4aaf02a2c603136633df72dfaca4212d`,
  and report SHA-256
  `fffc28a35ab36f75578ab5eb7798312d6e299bbea6a4bfef76104292107b7d63`.

These hashes identify the audited snapshots. Neither package was committed, so its
branch name alone is not a durable artifact identifier.

### 2.2 Changed-file inventory

Fable's non-cache files were:

- `dossier/DOSSIER.md`;
- `dossier/validators/a1_multi_certificate.py` through
  `a5_endogenous_checkpoints.py`;
- `c1_persistence_deflation.py`, `c3_refinement_premium.py`,
  `c4_canonical_covers.py`;
- 21 `v1_...` through `v8_...` independent or package-crosscheck validators.

There is no `c2_semilattice_rep.py`. This matters because the dossier labels the
semilattice representation pending; it is not a missing generated byproduct of an
otherwise complete claim.

Codex's modified tracked files were:

- `NEXT.md`, `proofs/README.md`, five existing proof programs,
  `results/RESULTS.md`, and `theory/certificate-continuation-research-ledger.md`.

Its untracked output comprised:

- `theory/infinite-context-boundary.md`;
- `tests/test_infinite_context_boundary.py`;
- `proofs/general_contract_search{,_naive}.py` plus results;
- `proofs/linear_obligation_rank.py` plus results;
- `proofs/evolving_checkpoint_refinement.py` plus results;
- `proofs/certificate_cover_resource.py` plus results;
- `proofs/certificate_verifier_hitting.py` plus results; and
- the seven-file `experiments/infinite-context-reference/2026-07-09/` fixture.

### 2.3 Reproduction table

| Target | Command/scope rerun | Result | Evidentiary meaning |
|---|---|---|---|
| Clean baseline | `uv run --with pytest --no-project -- pytest tests/ -q` | **80 passed in 74.73s** | Establishes the supplied commit is healthy before either output. |
| Sol worktree after report | Same full repository command | **80 passed in 69.70s** | Confirms the isolated audit deliverable did not disturb baseline validation. |
| Fable inherited relevant tests | `tests/test_certificate_continuation.py tests/test_proofs.py` | **15 passed in 71.75s** | Baseline package checks still pass in Fable's worktree. |
| Fable validators | Every one of the 29 validator entrypoints, individually | **29/29 exit 0** | Reproduces every executable Fable artifact that actually exists. It cannot reproduce the absent C2 claim. |
| Codex full suite | Full repository test command in Codex's changed worktree | **95 passed in 86.25s** | Reproduces baseline and 15 new boundary tests together. |
| Codex exact programs | 13 relevant legacy/new entrypoints, including general search, rank, checkpoint refinement, cover, verifier hitting, and reference runner | **13/13 exit 0** | Reproduces the exact counts and canonical ledgers in the report. |
| Codex finite counts | Test assertions and direct runner output | E0 `6/7/9`; `Q_{5,3}` static/right `24/6`; full/generated `34/55/209` and `32/53/206`; uniform layer total `886`; boundary-plus-current `3,685`; matrix pairs `16,452`; causal cases `82,453`; window answers `28,195`; cover hypergraphs `646`; hitting/cylinder cases `525,348` | Proof-backed finite theorems for the enumerated domains, not by themselves asymptotic proofs. |
| Reference benchmark | `runner.py --json` and test comparison to generated CSV/JSON | 96 records; zero answer/justification errors against independent replay for the fixture | An exact implementation artifact under its trusted-frontier/index contract. It is not an entropy theorem or a general extension experiment. |
| Diff hygiene | `git diff --check` in Codex worktree | pass | No whitespace error; not mathematical validation. |

The Codex asymptotic statements are supported by written algebraic proofs in addition
to enumeration. Fable's `Q_{k,p}` optimum likewise contains a general construction and
fooling-family lower bound. Claims supported only by sweeps are labeled finite below.

### 2.4 Generated evidence versus prose

- **Executable and reproduced:** the finite quotient counts, counterexamples, flexible
  `Q_{k,p}` construction, checkpoint identities, linear-rank checks, resource-cover
  bounds, verifier-hitting equality on finite models, and reference-fixture ledgers.
- **Proof in prose plus executable instances:** the general `Q_{k,p}` flexible optimum,
  checkpoint segment-product law, rank formula, storage-dependent hard-extension
  counting bound, and verifier-hitting necessity/equality in the declared nonuniform
  model.
- **Prose only or incomplete:** Fable's semilattice representation, the converse for
  its “anchored” class, the naturalness of arbitrary Boolean extensions, and a general
  coupled law for active state + archive layout + proof repair.
- **Implementation artifact only:** canonical JSON byte sizes and the exact workload's
  zero-error strategy comparison.

## 3. Normalized claim matrix

### 3.1 Common definitions and evidence rules

For a finite horizon, let `H` be the history set, `s : H -> S` the visible state,
`D : H -> ({0,1}^w)^A` a deterministic archive layout with address set `A`, and
`q : H -> Y` a deterministic answer contract. For relational contracts, let
`R(h)` be the accepted answer/certificate labels. A **state fiber** is
`B_z = {h : s(h)=z}`. A **falsifier** for claimed output `y` at `h` is an `h'` in
the same visible fiber on which `y` is not valid. Active information is
`ceil(log2 |S|)` unless a different charged encoding is explicit.

Repository evidence labels used here are load-bearing:

- **THEOREM:** a complete general proof under explicit definitions;
- **EXACT:** exhaustive computation over its stated finite domain; an accompanying
  asymptotic theorem is labeled separately rather than inferred from the sweep;
- **PREREGISTERED:** predictions and thresholds were frozen before a confirmatory run;
- **OBSERVED:** a reproduced pattern or workload result without the claimed general
  proof or confirmatory status;
- **REFUTED:** a stated claim has a proof-level counterexample or a failed frozen test;
- **CONJECTURE:** a formal statement with an outstanding proof obligation.

`VOID`, `LATENT`, `INAPPLICABLE`, and `SPLIT` remain outcome modifiers and never
upgrade evidence. The brief also asks the audit to identify metaphors, speculation,
classical reframings, negative boundaries, and strong specialized results. Those are
**audit verdicts**, not additional repository evidence classes. In particular, the
brief's phrase “proof-backed finite theorem” is recorded as `EXACT` unless a separate
general proof earns `THEOREM`; “empirical” is recorded as `OBSERVED` unless a frozen
protocol earns `PREREGISTERED`.

Agreement between agents does not change any label: both inherited the same baseline,
prompt vocabulary, and many of the same proof programs.

### 3.2 Claim table

| ID | Source | Normalized formal statement, quantifiers, and resource model | Evidence and smallest case | Attack result / counterexample | Closest prior art | Status |
|---|---|---|---|---|---|---|
| F-T1 | Fable | On a prefix-closed partial history domain, continuation equivalence must quantify only over jointly defined extensions; the baseline total-domain wording is too broad. | Explicit four-history witness `H={epsilon,a,b,ab}` and independent validator. | Survives; this repairs scope rather than creates a new theory. | Partial automata and Myhill--Nerode residuals. | **CLASSICAL REFRAMING / correction.** |
| F-A1 | Fable | Checkpoint factorization over certificate-coordinate sets requires independent/disjoint coordinate semantics. If several labels are interchangeable for one checkpoint, quotient factors can collapse. | Exhaustive small counterexample; reproduced validator. | Survives. It identifies a load-bearing assumption in the product law. | Product congruences; nondeterministic/relational transducers. | **STRONG SPECIALIZED RESULT.** |
| F-A2 | Fable | In the one-cell targeted-read model, complete absence among `n` named positions costs `n` reads, while an existential positive claim costs one witness read. The difficulty is adversarial naming/coverage, not a metaphysical property of negation. | Exact finite enumeration and direct adversary; smallest nontrivial case `n=2`. | Survives only when no paid aggregate or authenticated index already refines the visible state. | Certificate complexity, set disjointness, nondeterministic cell probe. | **CLASSICAL REFRAMING / NEGATIVE BOUNDARY.** |
| F-A4 | Fable | If an ontology split designates one of `k'` previously merged position classes and the archive exposes one raw position per probe, worst-case exact migration needs `k'-1` targeted reads and that is sufficient. | Exact dichotomy validator for finite instances. | Survives its one-cell/raw-position model; layout-sensitive and not universal. | Decision trees and static cell-probe search. | **STRONG SPECIALIZED RESULT.** |
| F-A5 | Fable | With endogenous rather than exogenous checkpoint placement, a fixed-boundary product is replaced by a sum over legal placements of the corresponding segment products. | Exact enumeration for small horizons plus combinatorial decomposition. | Survives. It weakens, rather than generalizes, the exogenous phase theorem; the placement description must also be charged. | Renewal/segmentation dynamic programming; temporal view state. | **STRONG SPECIALIZED RESULT.** |
| F-PI | Fable | Define composability premium `Pi(C)=N_two-sided(C)/N_right(C)` for a fixed contract. Frontier-homomorphic certificates have `Pi=1`; fixed-priority selection can have `Pi>1`. | Algebraic definitions and exact package counts. | Correct as a contract functional, but a ratio of two classical minimization quantities, not a universal invariant. It changes with certificate semantics. | Syntactic congruence versus right congruence; transition semigroups. | **CLASSICAL REFRAMING with useful terminology.** |
| F-Q | Fable | For the full formal raw monoid of fixed-priority `Q_{k,p}`, allowing path-dependent flexible compatible blocks gives minimum two-sided cover size `f(k,p)=(k+1)+p(k+1)(k+2)/2`. A sticky-champion construction attains it; a pairwise-incompatible fooling family of the same size lower-bounds it. | General construction and lower-bound argument; exact checks include `(k,p)=(3,2),(4,2),(5,3)`, with 24 at `(3,2)`. | Survives code and proof audit. Scope is full raw monoid, not the smaller depth-one generated event submonoid. | Compatible blocks/closed covers for incompletely specified sequential machines; exact formula match not found. | **STRONG SPECIALIZED RESULT; novelty unresolved.** |
| F-REF | Fable | On an old fiber `B`, supporting **every** Boolean future extension with depth `t` over `|A|` addresses of `w` bits requires `2^(tw) log2(2|A|) >= |B|`, hence some extension needs `t >= (log2|B|-log2 log2(2|A|))/w`. | Counting proof; `c3_refinement_premium.py` finite checks. | The storage-sensitive inequality survives. The hard functions are arbitrary truth tables, generally of exponential description length. | Static cell-probe counting and asymmetric communication. | **THEOREM, classical/nonexplicit.** |
| F-REF-U | Fable | Dossier §7.3 strengthens F-REF to: “for every archive layout, however large, some one-bit extension costs `Omega(n/w)`.” | Prose only; no supporting executable. | **False.** Store one `w=1` cell for every Boolean function `f:B->{0,1}`, with cell `f` holding `f(h)`. Then every extension takes one probe; `|A|=2^|B|`, and Fable's own lower bound becomes vacuous. Verified directly for `|B|=2,4,8,16`. | Standard tabulation/nonuniform data structures. | **FALSE.** |
| F-ANCHOR | Fable | An extension family computed by at most `s` designated observables on a standard index has `O(s)` migration/query cost; dossier language sometimes says cheap costs occur “exactly” for this anchored class. | Sufficient construction and small fixtures. | Sufficiency survives. Necessity does not: “anchored” is partly defined by the cheap observable implementation, and the dossier explicitly lists the converse as open. | Index selection, view adaptation, sufficient statistics. | Upper bound **THEOREM**; converse **CONJECTURE**; “exactly” **unsupported**. |
| F-PERSIST | Fable | A persistent packed snapshot per boundary answers historical frontier queries in one archive read after one snapshot write per event. | Reproduced 19.2-million-query finite sweep for one fixed encoding. | Correct, but archive information grows linearly and the word must grow with horizon or be decomposed. It refutes a query-read lower bound only when persistence storage/writes are uncharged. | Fully persistent data structures and event sourcing. | **EXACT implementation result / CLASSICAL REFRAMING.** |
| F-CANON | Fable | Under reflexive symmetric transitive compatibility plus an appropriate Helly/intersection condition, compatibility classes yield a canonical lattice-like minimum; without those conditions minimal covers need not be unique and joins can be inadmissible. | General elementary proof plus exact/random finite sweeps. | Survives. The hypotheses largely reinstate an equivalence relation and closure, so the result is not surprising. | Compatible-block and closed-cover theory. | **CLASSICAL REFRAMING.** |
| F-ODD | Fable | The `ODDCOUNT` example has linear refinement cost under the tested raw layout. | Exact only through `n<=5`. | No induction or reduction proves asymptotic `Theta(n)`. | Parity decision-tree lower bounds. | Finite claim **EXACT**; asymptotic claim **CONJECTURE**. |
| F-C2 | Fable | A semilattice representation characterizes the candidate refinement structure. | Dossier says pending; no validator or formal completed statement exists. | Cannot be reproduced or normalized beyond intent. | Semilattice-valued summaries, abstract interpretation. | **UNRESOLVED / absent artifact.** |
| C-GEN | Codex | For any finite explicit contract, exact continuation state is the minimum admissible continuation congruence; if hidden path-dependent machine states are allowed, the analogue is a transition-closed accepted-output cover. | Dual structurally different enumerators agree on declared small domains; written definitions. | Correct but tautological at the fully general semantic level; unrestricted contracts encode arbitrary distinction geometries. | Myhill--Nerode; incomplete-machine minimization. | **CLASSICAL REFRAMING.** |
| C-LIN | Codex | For fixed horizon `n`, binary histories with output `A_n x` have exactly `2^rank(A_n)` quotient states. Given only old state `Ax`, new linear rows `B` are archive-dormant iff `row(B) subseteq row(A)`; minimal additional tag has rank increment `rank([A;B])-rank(A)`. | Rank-nullity proof; 16,452 matrix-pair checks. | Survives. It becomes online only with cross-horizon-compatible matrix families and charged auxiliary state. | Linear sketches and sufficient statistics. | **STRONG SPECIALIZED RESULT / classical linear algebra.** |
| C-CHK | Codex | For fixed `m,v`, immutable publications, no targeted invalidation, a free exogenous checkpoint schedule `0=t_0<...<t_r=n`, and authenticated maintained frontiers, exact abstract state count is `prod_j G_{m,v}(t_j-t_{j-1})`; fixed `m,v` gives `O(r+r log(1+n/r))` bits. | Combinatorial proof, direct/segment representations, 82,453 history/schedule checks. Smallest nontrivial scheduled split at horizon 2. | Survives. Free timing metadata, trusted frontier, fixed ontology, and absence of invalidation are essential. No matched lower bound in a fixed external-memory model. | Temporal/materialized view maintenance; segment monoids. Exact formula match not found. | **STRONG SPECIALIZED RESULT; novelty unresolved.** |
| C-WIN | Codex | Retaining the exact last-`w` events plus the frontier before the window uses `O(log n+w)` active information (fixed alphabet) and answers any newly declared boundary within the window with at most `w` event replays; boundaries earlier than the window are not determined in general. | Direct algorithm, AB/BA obstruction, 28,195 exact answers. | Survives. Replay is query work; the theorem does not support arbitrary retroactivity. | Sliding-window algorithms and bounded-history temporal queries. | **STRONG SPECIALIZED RESULT / classical construction.** |
| C-HIT | Codex | In a finite nonuniform probe-only model with unbounded proof and verifier computation, any accepting execution's probed coordinates must hit the raw-cell difference support of every same-state falsifier. Minimum accepting-proof probes equal the smallest coordinate set whose observed cylinder contains no falsifier. | General adversary proof; 525,348 hitting/cylinder comparisons. | Survives exactly as scoped. It fails if one charges an already-maintained exact aggregate as a raw cell without including its update/storage cost; cryptographic soundness is computational, not perfect information-theoretic soundness. | Certificate complexity; nondeterministic decision trees/cell probes. | **NEGATIVE BOUNDARY / CLASSICAL REFRAMING.** |
| C-GAMMA | Codex | For fixed query `q`, accepted fibers `A_y`, and coverage curve `Gamma_q(C)=max_{|Y|<=C}|union_{y in Y} A_y|`, a fast path with `b` active bits and `t` adaptive `w`-bit reads, `F` fallbacks, and `E` errors satisfies `N-F-E <= Gamma_q(2^(b+tw))`. | Transcript-counting proof; two exact algorithms agree over 646 hypergraphs of 1--4 histories. | Survives. It is a necessary static bound, not an online achievable law; proof size and verifier work are not priced. | Communication transcript counting and maximum coverage. | **CLASSICAL REFRAMING / useful bound.** |
| C-COVER | Codex | Atomic accepted-output overlap can permit a two-state transition-closed cover when every semantic partition needs three; binding labels to exact provenance identities can remove the advantage. | Small exact counterexamples. | Survives as a refutation of universal cover collapse. It does not establish a locally verifiable proof-carrying advantage. | Paull--Unger compatible blocks and closed covers. | **EXACT / NEGATIVE BOUNDARY.** |
| C-BENCH | Codex | Eight strategies over a 50-event, 12-query versioned-memory fixture produce exact answers and justifications against independent replay, with coordinate-wise ledgers and zero paid model cost. | 96 reproduced records; canonical JSON/CSV tests; final fuzzing reported by Codex. | Valid fixture. Fixed query schema, caller-supplied trusted frontier, stable-key index, lack of continued ingestion after newly activated key obligation, and JSON byte encodings prevent information-theoretic or general claims. | Event sourcing, indexed views, authenticated/persistent dictionaries. | **OBSERVED / IMPLEMENTATION ARTIFACT.** |
| C-UNIV | Codex | No universal scalar based only on obligation count, split count, proof length, or answer entropy characterizes exact active state, archive access, and justification for arbitrary contracts. | Explicit counterexample catalog: equal split counts with different probe costs; long proof versus absence; query-count separations; provenance-binding collapse. | Survives. This is an anti-theorem about underspecified models, not a replacement invariant. | Arbitrary Boolean function/data-structure complexity. | **NEGATIVE BOUNDARY.** |

### 3.3 Audit against the inherited exact package

The upstream reports were not judged only by their summaries. Their changes were
checked against the baseline's strongest exact results:

| Baseline object | Reproduction and audit disposition |
|---|---|
| E0 certificate continuation | The `6/7/9` minima reproduced. Fable's independent E0 validator and Codex's legacy/new suite agree. This remains a small exact witness for the static/right/two-sided distinction, not an asymptotic theory. |
| Delayed boundary identity | Direct history checks reproduce that an old boundary may cease to be determined by a current frontier. Codex's rolling-window AB/BA obstruction is a clean specialization; Fable's endogenous-boundary analysis confirms schedule information is load-bearing. |
| Checkpoint factorization | Direct cumulative-frontier enumeration, Fable's checkpoint bijection validator, and Codex's segment implementation agree where assumptions align. Fable A1 shows that interchangeable certificate labels can destroy naive product coordinates. |
| Static-versus-online separation | The smallest three-state and unary-family counterexamples reproduce. Codex correctly distinguishes exact layer widths from one uniform machine and reports 886 rather than 579 through horizon four. |
| Streaming/chunk-composition gaps | Full raw monoid and generated-event submonoid counts differ (`34/55/209` versus `32/53/206`). Fable's composability premium and exact flexible cover formula refine this gap; neither makes it universal. |
| Temporal-obligation phase behavior | Sparse exogenous checkpoints and bounded windows have exact positive regimes. Endogenous placement requires a sum over placements. Arbitrary retroactive boundaries remain identity/replay-like. |
| Active/archive/fallback tradeoffs | Codex's `Gamma_q` bound and reference ledger reproduce; Fable's persistence fixture shows archive reads alone are not conserved. Total index/storage/update cost must be included. |
| Naive certificate congruence | Nonunique minima, inadmissible joins, and cover advantages reproduce. Provenance binding can erase abstract overlap, so accepted-output covers are not automatically proof-carrying states. |
| Versioned-memory contract probes | The exact fixture answers its frozen workload correctly, but the complete frontier is trusted/replayed, true post-extension continued ingestion is absent, and locally binding nonmembership remains open. |

None of the new claims invalidates these exact baseline results after the four scope
corrections listed in §4.2. Conversely, none of the baseline finite minima licenses the
agents' asymptotic or novelty claims without the separate proofs audited above.

## 4. Agent-by-agent audit

### 4.1 Fable / Claude

**Strongest result.** The exact flexible two-sided optimum for `Q_{k,p}` is
Fable's best result. It is not merely a finite pattern: the sticky-champion summary is
an explicit associative/sound construction, and the matching fooling family supplies
the lower bound. The exact formula

```text
f(k,p) = (k+1) + p(k+1)(k+2)/2
```

is a **STRONG SPECIALIZED RESULT**. The prior-art skeleton is closed-cover minimization,
but no direct source for this exact family/formula was found. Specialist review is
still needed before any novelty claim.

**Deepest error.** Fable proves a storage-sensitive hard-extension inequality and then
states a storage-independent conclusion. Those are not equivalent. If an old fiber has
`|B|` histories, an archive can contain `2^|B|` one-bit cells, one for each Boolean
extension `f`, with cell `f` storing `f(h)`. Every future Boolean extension is then a
one-probe query. This may be absurdly expensive storage, but “however large” explicitly
permits it. The valid lower bound is a tradeoff among fiber size, word size, address
space, and probes. Removing the address-space term makes the statement false.

**Unsupported leap.** The dossier says cheap extension costs collapse “exactly” to an
anchored class while later conceding that the converse is open. Moreover, “anchored” is
defined operationally by access to a small set of standard-index observables. That is a
useful upper-bound class, but currently close to defining easy extensions as extensions
easy for the chosen index. No maximality or representation theorem has been proved.

**Most valuable new direction.** Replace arbitrary Boolean extensions with a natural,
syntax-bounded contract family and ask for a layout-sensitive space/probe/repair
trichotomy. Fable correctly identified the missing axis—contract description and
archive organization—even though its strongest prose sentence dropped that axis.

Other judgments:

- the “cost is naming, not absence” correction is conceptually healthy;
- persistence decisively kills any unqualified archive-*read* lower bound, while
  leaving total information and update-write bounds intact;
- endogenous checkpoints expose that schedule information is a resource;
- the C2 artifact is missing, and the `ODDCOUNT` asymptotic is not established.

### 4.2 Codex 5.6

**Strongest result.** The complete-frontier checkpoint factorization, strengthened with
causal freezing and a bounded exact replay window, is the strongest positive theorem.
It gives an exact state count, a sublinear phase for sparse obligations, an explicit
online update algorithm, and an obstruction outside the window. It is also honest about
what “complete” means: equality to a maintained frontier object, not a local proof of
archive completeness by a distrustful verifier.

**Deepest limitation.** The positive regime depends on a free schedule signal and an
authenticated frontier primitive under an immutable fixed ontology. Those assumptions
remove the hardest parts of the target: detecting obligations after compression,
targeted invalidation, proof repair, and locally binding historical nonmembership.
This is not a proof error—Codex states the limitations—but it prevents the theorem from
supporting the motivating general claim.

**Unsupported leap.** There is no major hidden foundational leap in the final report;
Codex explicitly classifies the work at Level 3. The most aggressive phrase is calling
the reference fixture “non-toy.” It is deterministic and nontrivial, but its fixed
50-event workload, trusted caller-supplied frontier, and stopped extension lifecycle
make “exact integration fixture” the defensible description. Its JSON byte comparison
is correctly labeled an implementation artifact.

**Most valuable new direction.** Couple the verifier-hitting geometry to online
refinement information transfer in one fixed external-memory model. Codex is right that
the missing theorem must price every maintained index write, every probe, proof repair,
the contract compiler, and continued ingestion after extension.

Codex also deserves credit for four material scope corrections to the inherited
package:

1. `34/55/209` counts the full raw monoid; the stated depth-one event generators reach
   `32/53/206`.
2. Add-only feasibility has two answer states; `p+1` is a fixed-priority certificate
   count. Arbitrary deletion forces `2^p` survivor answer subsets.
3. Exact-length layer width is not a uniform online machine: through horizon four the
   current-state machine has 886 states, not 579; boundary-one-plus-current has 3,685.
4. Recomputing a frontier from the raw history proves an extensional quotient, not a
   locally binding completeness proof.

## 5. Cross-agent synthesis

### 5.1 Genuine convergence and correlated-evidence risk

Both agents converge on the following defensible conclusions:

- fixed, structured obligations admit compact sufficient state;
- arbitrary retroactive distinctions can force identity-like retained information or
  archive access;
- complete negative evidence can cost more to verify than a positive witness;
- path-dependent covers can beat semantic partitions, but provenance binding can erase
  that advantage;
- no scalar based only on query count, certificate count, or split count is universal;
- archive layout and persistence can move cost between active state, writes, storage,
  probes, and reconstruction time.

This convergence is not independent replication. Both agents began from the same
baseline, inherited the same certificate-continuation vocabulary and exact programs,
and were explicitly asked to search for a universal law. It is strongest where their
implementations are structurally different (direct replay versus segment composition;
two independent general-contract enumerators) and weakest where both paraphrase the
same baseline theorem.

### 5.2 Conflicts

1. **Foundational status.** Fable calls the refinement layer a foundational candidate;
   Codex calls the general skeleton classical. Codex wins this dispute. Fable's valid
   counting result is a standard nonuniform data-structure tradeoff, and its stronger
   layout-free sentence is false.
2. **What causes negative-evidence cost.** Fable emphasizes naming/coverage; Codex
   formalizes the same fact as falsifier-support hitting. These are compatible. Codex's
   formalization makes Fable's conceptual correction precise.
3. **Persistence.** Fable's one-read snapshots appear to undercut archive-access lower
   bounds. Codex's fiber-relative V1 theorem shows why they do not contradict it: once a
   paid exact snapshot is a visible/probed coordinate, the falsifier geometry has
   changed. Persistence moves information; it does not create it.
4. **Canonical state.** Fable restores canonicity under equivalence/Helly-like
   conditions; Codex exhibits nonunique minimal path machines without them. Again these
   are compatible, and together delineate the classical closed-cover boundary.

### 5.3 The stronger combined statement

The following **fiber trichotomy** is the deepest defensible synthesis. It is a theorem
as a conjunction of three proved clauses, but not an apparently novel theorem.

Let `B=s^{-1}(z)` be an old visible-state fiber, let `q:B->Y` be a new exact
contract, and let `D` be a fixed charged `w`-bit-cell archive layout.

1. **Semantic sufficiency.** Zero archive access is possible exactly when `q` is
   constant on every `s`-fiber; equivalently, `q = g o s` for some `g`.
2. **Reconstruction/search.** Otherwise the minimum archive access is the deterministic
   decision-tree/cell-probe complexity of `q` restricted to `B` under layout `D`. Across
   all Boolean `q`, a counting lower bound necessarily depends on `|B|`, `w`, **and**
   `|A|`; it cannot be storage-free.
3. **Proof verification.** For a claimed output `y`, every accepting proof execution
   must probe a coordinate set hitting the difference support of every same-state
   falsifier. In the finite nonuniform probe-only model, the optimum is the minimum
   falsifier-free observed cylinder.

The three clauses use different geometry:

- semantic fibers ask which histories are merged;
- search trees ask how a layout reveals a distinguishing function;
- proof cylinders ask which falsifiers an accepting transcript excludes.

They cannot be collapsed. First-bit and parity can split a fiber into the same number
of answer classes but have radically different raw-layout query costs. Existential
presence and complete absence both have one-bit answers but different certificate
costs. A gigantic direct-answer archive can make every Boolean extension one-probe
without reducing total retained information.

What remains **CONJECTURE** is a natural online coupling theorem that relates these
geometries while charging update writes, address space, proof repair, verifier work,
and contract-description complexity. Neither agent proved it.

## 6. The strongest surviving candidate

### 6.1 Formal statement: causal complete-frontier checkpoint phase theorem

The strongest proved project-specific candidate is Codex's causal checkpoint theorem.
It is stronger than a workload observation and narrower than infinite context.

Fix integers `m>=1` and `v>=1`. An event chooses one of `m` cells and publishes one
of `v` values. Publications are immutable and append-only. A segment frontier records,
for every cell, its publication count in the segment and its latest segment value when
the count is nonzero. Define

```text
G_{m,v}(0) = 1

G_{m,v}(ell)
  = sum_{u=1}^{min(m,ell)} C(m,u) C(ell-1,u-1) v^u,  ell>0.
```

The factors choose the `u` touched cells, a positive composition of `ell` events into
their counts, and a latest value for each touched cell.

Let a free exogenous signal announce checkpoint boundaries exactly when they occur:

```text
0 = t_0 < t_1 < ... < t_r = n.
```

Maintain the live segment frontier and freeze it on each signal. Under the assumptions
below, the exact number of reachable checkpoint signatures is

```text
N_T(n) = product_{j=1}^r G_{m,v}(t_j-t_{j-1}).
```

For fixed `m,v`, therefore,

```text
log2 N_T(n) = O(r + r log(1+n/r)).
```

Consequences:

- fixed `r` requires `O(log n)` active information;
- `r=o(n)` requires `o(n)` active information;
- when the event alphabet is nontrivial (`m*v>=2`), a positive density of positive
  independent gaps requires `Theta(n)` information;
- freezing a declared checkpoint needs zero archive reads and `O(m)` frontier-copy
  work;
- adding a standalone exact suffix window of width `w` costs `O(log n+w)` active
  information for fixed alphabet and answers a newly declared boundary inside the
  window by at most `w` event replays;
- the combined checkpoint-plus-window state is
  `O(r+r log(1+n/r)+log n+w)` bits for fixed `m,v`.

### 6.2 Exact assumptions and charged resources

The theorem assumes all of the following:

1. the cell/value ontology is finite and fixed before ingestion;
2. events are immutable append-only publications;
3. no targeted invalidation revises the truth of an earlier segment frontier;
4. checkpoint timing is supplied by an exogenous signal at the boundary, and the
   information/storage cost of that schedule is outside the bound;
5. the maintained frontier is an authenticated or otherwise trusted primitive;
6. “complete justification” means equality to that frontier object, not a new local
   proof to a verifier that distrusts it;
7. `log |S|` is the active-information measure; concrete pointers, word alignment,
   authentication metadata, archive storage, and CPU constants are not included;
8. window replay is query-time work, not persisted refinement;
9. `m` and `v` are constants in the asymptotic statement.

Changing any of 1--6 can change the theorem qualitatively. In particular, delayed
contract discovery is not equivalent to a free boundary signal, and source-version
invalidation can force proof repair beyond segment freezing.

### 6.3 Proof skeleton and executable witness

The proof has four independent pieces.

1. **Single-segment count.** A segment frontier of length `ell` is uniquely determined
   by its touched set, a positive composition of `ell` into per-cell counts, and one
   latest value per touched cell. Every such tuple is realizable, giving `G_{m,v}`.
2. **Product bijection.** Disjoint temporal segments are freely selectable. Mapping a
   history to its tuple of segment frontiers is onto the Cartesian product, and the
   tuple determines every cumulative checkpoint frontier. Thus the quotient state
   count is exactly the product, not merely upper-bounded by it.
3. **Sparse asymptotic.** For fixed `m,v`, `log G_{m,v}(ell)=O(1+log(1+ell))`.
   Concavity of `log` bounds the sum over gaps by
   `O(r+r log(1+n/r))`.
4. **Window obstruction.** Direct replay establishes the suffix-window upper bound.
   Two prefixes such as `AB` and `BA` can have the same current frontier and identical
   retained suffix while disagreeing at an older boundary, proving that arbitrary
   pre-window recovery is not generally state-determined.

`proofs/evolving_checkpoint_refinement.py` implements two structurally different
representations—direct prefix replay and independent segment composition—and compares
82,453 history/schedule cases. It also checks 28,195 rolling-window answers. The Sol
audit independently rebuilt the small product enumeration directly from cumulative
frontiers rather than calling the provided segment counter; all 15 nonempty schedules
through horizon four matched.

### 6.4 What is proved and what is not

**Proved:** the formula, sparse active-information phase, causal maintenance algorithm,
bounded-window upper bound, and an outside-window nondeterminacy witness in this exact
model.

**Not proved:** a matching lower bound in a charged external-memory model; local
archive-bound nonmembership proofs; efficient support for targeted invalidation;
continued ingestion after arbitrary ontology extension; a maximal natural extension
class; or novelty relative to specialist temporal-view/state-complexity literature.

### 6.5 Why this is not yet foundational

The result is architecture-independent and reproducible, and its exact product law is
mathematically clean. But it obtains sublinear active state by fixing the ontology,
receiving the obligation schedule for free, trusting a maintained sufficient view, and
excluding targeted retroactivity. Those are precisely the dimensions on which the
motivating “infinite context” problem becomes hard. It is a **STRONG SPECIALIZED
RESULT**, not a **FOUNDATIONAL CANDIDATE**.

Fable's `Q_{k,p}` optimum is the runner-up: arguably more novel as an exact cover
formula, but farther from the evolving-memory target and embedded in a classical
incomplete-machine optimization problem.

## 7. Prior-art collision report

This was a collision test, not a keyword survey. The question for each source is
whether the repository statement is equivalent, a corollary, a specialized exact
formula, or genuinely different. Sources below are original papers, technical reports,
or authoritative versions.

| Repository object | Primary source(s) | Collision judgment |
|---|---|---|
| Continuation equivalence and minimum exact retained state | A. Nerode, [“Linear Automaton Transformations,” 1958](https://doi.org/10.1090/S0002-9939-1958-0135681-9) | The unrestricted functional skeleton is equivalent to residual/continuation equivalence. Certificates and partial domains require careful relational/partial variants, but do not by themselves create a new minimization principle. |
| Transition-closed accepted-output covers and nonunique minima | Paull and Unger, [“Minimizing the Number of States in Incompletely Specified Sequential Switching Functions,” 1959](https://doi.org/10.1109/TEC.1959.5222697); Kam et al., [*State Minimization of Incompletely Specified Machines*](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1995/ERL-95-107.pdf) | Equivalent abstraction: compatible blocks and minimum closed covers. The repository contributes exact fixtures and possibly new formulas for its `Q_{k,p}` family, not the general cover concept. |
| Archive-dormant new query iff it factors through retained state | Nash, Segoufin, and Vianu, [“Views and Queries: Determinacy and Rewriting,” 2010](https://doi.org/10.1145/1806907.1806913) | Equivalent at the information-theoretic semantic level: the retained state is a view, and the new query must be determined by it. Efficient rewriting is an additional question. |
| Archive-dormant online update | Blakeley, Coburn, and Larson, [“Updating Derived Relations,” 1986](https://www.vldb.org/conf/1986/P457.PDF) | Direct overlap with materialized-view self-maintainability. The repository's event/frontier vocabulary is a specialization. |
| Retained auxiliary information to enable later redefinition/refinement | Gupta and Blakeley, [materialized-view adaptation work](https://doi.org/10.1016/0306-4379(95)00035-6) | Direct conceptual overlap: retaining extra information enlarges the class of future changes maintainable without base access. A new result would need a sharper natural extension class and matched resource bound. |
| Fable's all-Boolean hard-extension count | Gál and Miltersen, [“The Cell Probe Complexity of Succinct Data Structures,” 2003](https://doi.org/10.7146/brics.v10i44.21816); Miltersen, Nisan, Safra, and Wigderson, [“On Data Structures and Asymmetric Communication Complexity,” 1998](https://doi.org/10.1006/jcss.1998.1577) | Restricted special case of static cell-probe/counting reasoning. The explicit `|A|` term is essential. Arbitrary Boolean extensions are nonexplicit hard queries, not a natural ontology family. |
| Verifier-hitting/cylinder equality | Yin, [cell-probe proofs](https://doi.org/10.1007/978-3-540-70575-8_7); Wang and Yin, [“Certificates in Data Structures,” 2014](https://arxiv.org/abs/1404.5743) | Substantially equivalent to certificate/nondeterministic cell-probe complexity in a finite nonuniform presentation. The repository's value is aligning it with same-state falsifier supports and complete justification. |
| Proof/stream-state tradeoffs | Chakrabarti, Cormode, and McGregor, [“Annotations in Data Streams,” 2009](https://doi.org/10.1007/978-3-642-02927-1_20) | Direct novelty threat to any proposed `state + proof` conservation law. Prover access and soundness model must be stated; responder-generated proof bits cannot reveal unread archive information. |
| Persistent one-read snapshots | Driscoll, Sarnak, Sleator, and Tarjan, [“Making Data Structures Persistent,” 1989](https://doi.org/10.1016/0022-0000(89)90034-2) | Classical persistence. The Fable fixture is a computational witness for a standard time/storage shift, not a new principle. |
| Mergeable/segment summaries | Agarwal et al., [“Mergeable Summaries,” 2013](https://doi.org/10.1145/2500128) | Broad structural overlap for homomorphic segment combination. No exact collision was found for the complete-frontier `G_{m,v}` product formula. |
| Bounded temporal history/window behavior | Chomicki, [“Efficient Checking of Temporal Integrity Constraints Using Bounded History Encoding,” 1995](https://doi.org/10.1145/210197.210200); Toman, [“Expiring Data in a Warehouse,” 2002](https://doi.org/10.1109/TIME.2002.1027477) | The causal/window idea is classical temporal state maintenance. The exact state formula and the particular sparse checkpoint phase remain potentially specialized contributions. |
| Provenance algebra | Green, Karvounarakis, and Tannen, [“Provenance Semirings,” 2007](https://doi.org/10.1145/1265530.1265535) | General compositional provenance is established. The repository's certificate identities and negation/completeness obligations need not fit the positive semiring model, but novelty cannot rest on the word “provenance.” |
| Ambiguous acceptable outcomes and resolution depth | Hellerstein, [“Determination Provenance: From Ambiguity to Algebra,” 2026](https://arxiv.org/abs/2606.10270) | A recent, unreviewed but directly relevant preprint. Its support semiring and filtration pose a novelty risk for “accepted-output resolution” language; it does not prove this repository's exact formulas or online resource bounds. |
| Truth maintenance, revisions, and justification invalidation | Doyle, [“A Truth Maintenance System,” 1979](https://doi.org/10.1016/0004-3702(79)90008-0) | The systems concept is classical. A new theorem must price invalidation and repair rather than redescribe dependency tracking. |

### 7.1 Remaining novelty uncertainty

No immediate primary-literature match was found for:

1. the full-raw quotient `C(k+p+2,p+1)-1` and its depth-one-generated correction by
   `p`;
2. Fable's flexible two-sided optimum
   `(k+1)+p(k+1)(k+2)/2` for the exact `Q_{k,p}` family; or
3. the complete-frontier segment product `prod_j G_{m,v}(gap_j)`.

This is **absence of a located reduction, not evidence of novelty**. All three require
targeted review by specialists in syntactic/transition semigroups, incompletely
specified transducers, temporal database state complexity, and dynamic view
maintenance. The exact formulas could be new exercises inside established frameworks
without being foundational.

No apparent match was classified as category-theoretic, sheaf-theoretic,
information-bottleneck, predictive-state, or continual-learning theory because neither
agent supplied an exact mapping that adds explanatory or proof power. Invoking those
fields would currently be metaphor, not collision analysis.

## 8. Kill conditions

The three strongest ways to destroy the surviving candidate are:

1. **Direct prior theorem.** A specialist locates a theorem in temporal view-state
   complexity, transformation semigroups, or sequential-machine minimization that
   yields the exact segment product or `Q_{k,p}` formula as an immediate substitution.
   The mathematics would remain correct, but the novelty and foundational trajectory
   would collapse to **CLASSICAL REFRAMING**.
2. **Charged invalidation counterexample.** In a natural bounded-dependency,
   stable-key model, a constant-radius ontology extension or source-version
   invalidation forces `Omega(n)` index writes, proof repairs, or archive probes even
   when checkpoint density and active state are sublinear. That would show the positive
   sparse phase is an artifact of immutable publications and free frontier trust.
3. **Oracle accounting.** Once checkpoint schedules, authenticated nonmembership,
   address space, index writes, persistent versions, verifier probes, and contract
   descriptions are all charged, the apparent sublinear regime contains `Theta(n)`
   information or unbounded reconstruction work in an assumed service. That would not
   falsify the current scoped theorem; it would kill its relevance to no-hidden-oracle
   infinite context.

For Fable's broader refinement claim, the first kill condition has already occurred in
internal form: a direct-answer layout invalidates the “however large” archive version.

## 9. Confirmation conditions

Moving from **STRONG SPECIALIZED RESULT** or **INTERESTING CONJECTURE** to
**FOUNDATIONAL CANDIDATE** requires, at minimum, one theorem satisfying all of the
following in the same model:

1. **Natural contract syntax.** A class defined independently of the data structure,
   richer than fixed checkpoints, and supporting real delayed boundary identity,
   ontology refinement, and source invalidation.
2. **Fully charged resources.** Fixed word size, total auxiliary/index space, update
   writes and probes, query probes, proof length, verifier work/probes, refinement
   communication, fallback, and error.
3. **Online lifecycle.** Continued ingestion before and after `K_0 subset K_1 subset ...`
   contract extensions, with explicit proof invalidation and repair.
4. **Matched boundary.** A constructive sublinear regime and a lower bound, within at
   most logarithmic factors, showing which structural parameter makes the phase
   possible and when it fails.
5. **Local justification.** Completeness and provenance bind to the archive/version
   without trusting a caller-supplied frontier or treating a cryptographic digest as
   information-theoretically injective.
6. **Nonreduction audit.** Expert review demonstrating that the theorem is not an
   immediate instance of view adaptation, dynamic data structures, cell probe,
   annotated streams, authenticated dictionaries, or closed covers.
7. **Independent reproduction.** A second group rebuilds the lower-bound argument and
   the construction without inheriting the same enumerator or prompt.

A **FOUNDATIONAL RESULT** would additionally require a complete proof, externally
defensible novelty, and a consequence strong enough to redirect system design—not
merely a new exact constant for one contract.

## 10. One decisive next move: a 30-day theorem-or-kill program

### 10.1 Target

Fix one **stable-key, bounded-dependency ontology-extension model** and either prove a
matched resource theorem or produce a linear-cost counterexample. Do not run another
open-ended model campaign.

### 10.2 Inputs

- An append-only stream of versioned assertions `(key, value, source, version, deps)`.
- Stable keys; dependency graph with maximum out-degree and invalidation radius `d=O(1)`.
- A fixed external-memory layout: `w=Theta(log n)`-bit cells, persistent authenticated
  B-tree/posting structures, and no other oracle.
- Every archive/index bit, update read/write, query read, proof byte, verifier probe,
  and repair write charged.
- Contract chain `K_0 subset K_1 subset ...` where each extension is a syntax-bounded
  local provenance query of radius at most `d`, including membership, nonmembership,
  latest-valid-source, and one delayed temporal boundary operator.
- Continued adversarial ingestion and source-version invalidation after each extension.

The class must be specified syntactically before the data structure. It must not be
called “anchored” merely because the selected index answers it cheaply.

### 10.3 Required outputs

Produce exactly one of:

**A. Matched theorem.** An explicit uniform construction and lower bound showing, for a
natural structural parameter `rho`,

```text
active bits + charged index bits + amortized update/repair transfer
    versus
query/verifier probes + fallback/error
```

within a logarithmic factor, with a nonempty `rho=o(n)` exact-justified regime and an
`Omega(n)` boundary outside it.

**B. Kill counterexample.** A constant-`d`, constant-description contract extension and
adversarial update sequence that forces `Omega(n)` on at least one charged coordinate
despite sublinear checkpoint density and active state.

**C. Prior-art reduction.** A formal mapping from the whole model to an existing
dynamic-view/data-structure theorem that already supplies the claimed phase boundary.

Any of A--C changes the verdict. A can raise it to **FOUNDATIONAL CANDIDATE**; B narrows
or kills the hoped-for positive class; C lowers novelty decisively.

### 10.4 Controls and independent checks

1. Freeze the model, contract grammar, resource ledger, and three outcome criteria
   before running the search.
2. Implement two checkers for finite `n<=8`: one enumerates raw histories and update
   schedules; the other works from symbolic dependency/version states.
3. Include controls that isolate each resource move: raw log, full materialization,
   persistent snapshots, posting-only index, checkpoint-only state, and lossy/fallback
   baselines.
4. Test adversarial delayed identity, revocation, contradiction, complete absence, and
   continued ingestion after activation.
5. Do not use JSON byte size as information complexity; compute abstract state/index
   counts and separately report concrete bytes.
6. Have the lower-bound proof reviewed without access to the construction's source, and
   compare the two finite checkers' canonical cases and hashes.

### 10.5 Stop conditions

Stop by day 30 when the first of these occurs:

- a complete upper/lower proof survives both checkers and a written prior-art mapping;
- a smallest explicit linear-cost counterexample is independently reproduced;
- a direct primary-source theorem subsumes the target;
- or the proof still depends on an uncharged summary, schedule, validity table, address
  space, cryptographic idealization, or nonuniform compiler. In the last case, record
  **UNRESOLVED**, not a candidate.

The decisive quantity is not another large finite count. It is whether a natural
extension class admits a matched, fully charged online phase theorem.

## 11. Final fifty-year test

The strongest honest one-sentence candidate is:

> **For a fixed finite append-only ontology, exact complete-frontier state for
> exogenously signaled checkpoints factorizes over checkpoint gaps, so sparse temporal
> obligations require sublinear active information, while unrestricted post-hoc
> boundaries generally require retained distinctions or replay.**

That sentence would still matter if transformers and current LLMs vanished. It is about
temporal databases, persistent agents, audit logs, scientific records, and any online
system that must answer old-boundary questions exactly.

There is, however, **no honest sentence yet for a novel universal textbook law of
infinite non-degrading context**. The broader sentence—future exact contracts must be
constant on retained-state fibers or pay through information, access, error, or trusted
external service—is already the joint language of sufficient views, automata,
data-structure complexity, and information theory. To become a new textbook result,
the program must discover a natural coupling invariant with a matched boundary, not
rename that disjunction.

## Appendix A. Independent adversarial checks

The Sol audit did not call the upstream helper functions for the following checks. A
small one-off Python enumerator built raw histories, computed cumulative frontiers
directly, enumerated raw-position decision trees, and built a direct-answer archive.
It produced:

```text
checkpoint direct/product schedules through n=4: 15/15 PASS
EVERWAS raw-layout worst-case probes n=2..5: 1, 2, 3, 4
complete absence vs existential witness at n=4: 4 vs 1

direct-answer archive counterexample (w=1):
n=2: |B|=2,  |A|=4,     worst probes=1, counting floor=0
n=3: |B|=4,  |A|=16,    worst probes=1, counting floor=0
n=4: |B|=8,  |A|=256,   worst probes=1, counting floor=0
n=5: |B|=16, |A|=65536, worst probes=1, counting floor=0
```

The direct-answer construction is uniform as a nonuniform layout family: for every
Boolean `f:B->{0,1}`, allocate address `a_f` and store `D(h)[a_f]=f(h)`. A future
extension named by `f` probes `a_f`. This is intentionally an enormous archive. Its
purpose is to disprove a claim quantified over archives “however large,” not to propose
a practical system. Substituting `|A|=2^|B|` into Fable's valid counting inequality
makes the lower bound zero, so code, algebra, and counterexample agree.

The checkpoint cross-check used the direct set

```text
{ (frontier(h[:t_1]), ..., frontier(h[:t_r])) : h in Sigma^n }
```

and compared its cardinality with the product of independently enumerated segment
frontier sets. It did not invoke `checkpoint_count` or `combine_segments` from Codex's
implementation.

## Appendix B. Exact limitations to carry forward

1. **Finite enumeration scope.** The 646 acceptance hypergraphs cover only one to four
   histories and one to three distinct nonempty acceptance fibers. They validate the
   algorithm on that domain, not every hypergraph.
2. **Nonuniform verifier scope.** The exact hitting/cylinder equality permits unbounded
   proof length, computation, and an uncharged validity table/verifier description.
3. **Static versus online scope.** Fixed-horizon rank and cover minima do not imply a
   single uniform cross-horizon machine.
4. **Raw monoid versus generated events.** Full formal raw chunks and the actual
   depth-one generated submonoid have different counts.
5. **Answer versus certificate.** Answer-state counts cannot be replaced with
   fixed-priority certificate counts.
6. **Trusted view versus local proof.** A recomputed or caller-supplied complete
   frontier is not a locally binding proof of archive completeness.
7. **Active versus total information.** Persistent snapshots and posting indexes may
   make active state or queries small while total retained information remains linear
   or larger.
8. **Cryptographic versus information-theoretic exactness.** A digest can be treated as
   binding only under an explicit computational assumption; it is not an injective
   information-theoretic summary.
9. **Natural versus arbitrary extensions.** “Every Boolean function on the old fiber”
   includes truth tables with exponential description length. It proves a worst-case
   counting boundary, not a realistic ontology theorem.
10. **No public novelty claim.** The three unmatched formulas remain novelty-uncertain
    until specialist review; this report is an internal audit.

## Final classification

The current program is **Level 3: strong specialized theorems, classical general
skeleton, and genuine negative boundaries**. It is not a dead end. The precise failure
of scalar laws and the separation among state, search, and proof geometries are useful
research progress. But the world-changing result would be the missing matched online
coupling theorem. At present, calling that theorem discovered would be false.
