# Reach: the highest-value frontier after the infinite-context audit

**Status:** internal research map, not a novelty claim

**Evidence authority:** [`results/RESULTS.md`](../results/RESULTS.md)

**Full adversarial audit:** [`sol-synthesis-audit.md`](sol-synthesis-audit.md)

## The short answer

The program does **not yet** have a millennium-defining theory of infinite context.
It has something more useful than an inflated conclusion: a small collection of exact
results, a decisive map of where the general story becomes classical, and one sharply
defined place where deeper mathematics could still exist.

The existing theory separates three questions that had been blurred together:

1. **Sufficiency:** did the retained state preserve the distinction a future contract
   needs?
2. **Reconstruction:** given an archive layout, how much must be read to recover that
   distinction?
3. **Verification:** how much must be inspected to exclude every history that would
   falsify the claimed answer or provenance?

These are not three wordings of one quantity. They are different geometries on the
same old-state fiber. The best current hope is not another architecture. It is a
matched theorem explaining when those geometries can be coupled cheaply under online
contract evolution—and when one of them must become large.

## Evidence key

Repository evidence labels are literal:

- **THEOREM:** a general proof under stated assumptions;
- **EXACT:** exhaustive computation over the stated finite domain;
- **PREREGISTERED:** predictions and thresholds were frozen before a confirmatory run;
- **OBSERVED:** a reproduced pattern without a general proof or confirmatory status;
- **REFUTED:** a formal counterexample or failed frozen test destroys the claim;
- **CONJECTURE:** a formal target whose proof is incomplete.

`VOID`, `LATENT`, `INAPPLICABLE`, and `SPLIT` are outcome modifiers, not upgrades.
**Strong specialized result**, **classical reframing**, **negative boundary**, and
**speculation** are evaluative descriptions used by the audit; they are not additional
evidence classes.

Agreement between research agents does not strengthen a label. They shared the same
repository, prompt family, vocabulary, and several proof programs.

## The five highest-value findings

### 1. Sparse causal checkpoints have an exact phase law

**Status: THEOREM + EXACT; strong specialized result.**

Fix a finite ontology of `m` cells and `v` values. Events are immutable append-only
publications. A free exogenous schedule announces checkpoint boundaries exactly when
they occur:

```text
0 = t_0 < t_1 < ... < t_r = n.
```

For a segment of length `ell`, let

```text
G_{m,v}(0) = 1

G_{m,v}(ell)
  = sum_{u=1}^{min(m,ell)} C(m,u) C(ell-1,u-1) v^u.
```

The exact number of complete-frontier checkpoint states is

```text
N_T(n) = product_{j=1}^r G_{m,v}(t_j-t_{j-1}).
```

For fixed `m,v`,

```text
log2 N_T(n) = O(r + r log(1+n/r)).
```

Therefore fixed `r` needs `O(log n)` active information and `r=o(n)` gives a
sublinear active state. When the event alphabet is nontrivial (`m*v>=2`),
positive-density positive gaps force linear active information. An exact suffix window
of width `w` adds `O(log n+w)` active information and recovers new boundaries inside
the window with at most `w` event replays. The degenerate `m=v=1` alphabet has only
one possible event and therefore no information-growth lower bound.

Why it matters: this is an exact non-degradation theorem for a natural temporal
obligation class. It survives independently of current LLM architectures.

Why it is not foundational yet: the ontology is fixed; publications cannot be
targetedly invalidated; the schedule arrives for free; and completeness is relative to
a trusted maintained frontier. The theorem does not price local nonmembership proofs,
source-version invalidation, or proof repair.

Artifacts:

- [`proofs/checkpoint_frontier_theorem.py`](../proofs/checkpoint_frontier_theorem.py)
- [`proofs/versioned_memory_contract.py`](../proofs/versioned_memory_contract.py)
- [`certificate-continuation-research-ledger.md`](certificate-continuation-research-ledger.md)

### 2. State sufficiency, reconstruction, and verification are different geometries

**Status: THEOREM as a classical synthesis; not a new universal law.**

Let `H` be a finite history space, `s:H->S` the visible retained state, and
`B_z={h:s(h)=z}` an old-state fiber. Let `D(h)` be a fixed archive layout and
`q:H->Y` a future exact contract.

Three separate quantities appear:

1. **Semantic split geometry.** Zero archive access is possible exactly when `q` is
   constant on every `B_z`; equivalently, `q=g o s` for some `g`.
2. **Search geometry.** If `q` is not state-determined, its query cost is the
   deterministic decision-tree or cell-probe complexity of `q|B_z` under the actual
   layout `D`.
3. **Falsifier geometry.** For a claimed output `y`, an accepting verifier must inspect
   coordinates hitting every same-visible-state history on which `y` is false. In the
   finite nonuniform probe-only model, the minimum is the smallest observed cylinder
   containing no falsifier.

The separations are concrete:

- first-bit and parity can split a fiber into the same number of answer classes while
  having very different raw-layout search costs;
- existential presence and complete absence both have one-bit answers, but presence
  has a one-cell witness while absence can require all `n` raw cells;
- a gigantic direct-answer archive can make every Boolean future contract one-probe
  while storing exponentially or doubly-exponentially many indexed answers.

The consequence is negative but important: obligation count, answer entropy, split
multiplicity, proof length, or “context density” cannot be the universal scalar. Any
general theory must retain the geometry of the contract and the organization of the
stored information.

### 3. Exact flexible cover compression exists beyond semantic partitions

**Status: audited THEOREM in the Fable source snapshot; specialist novelty unresolved;
the full upstream proof program has not been promoted into this branch.**

For the full formal raw monoid of the fixed-priority `Q_(k,p)` family, the audited
path-dependent sticky-champion construction has two-sided cover size

```text
f(k,p) = (k+1) + p(k+1)(k+2)/2.
```

A matching pairwise-incompatible family supplies the lower bound. Exact checks include
`(k,p)=(3,2),(4,2),(5,3)`.

Why it matters: semantic partitions are not always the correct state object. A hidden
path state can implement overlapping compatible blocks more compactly than every
partition of semantic rows. Provenance identity can then remove that advantage. This
is the cleanest bridge between continuation memory and proof-carrying state design.

Why it is not yet a public theorem claim: the general object is classical
incomplete-machine compatible-block/closed-cover theory; a direct prior formula match
has not been ruled out; and the source validator/proof remains in the audited Fable
worktree rather than this repository branch. Promote the proof and independent checker
before citing the formula externally.

### 4. Complete justification has a falsifier-hitting cost that answer entropy misses

**Status: THEOREM in a finite nonuniform probe-only model; classical certificate
complexity boundary.**

Fix a visible state, a true history `h`, and a claimed output `y`. For every
same-state falsifier `h'`, let

```text
Delta(h,h') = {j : D_j(h) != D_j(h')}.
```

Every accepting verifier execution must probe a set intersecting every
`Delta(h,h')`. Otherwise the same proof and observations would be accepted on `h'`.
With unbounded proof length, unbounded verifier computation, and an uncharged
nonuniform validity table, the optimal accepted-proof probe count is the minimum
falsifier-free coordinate cylinder.

This explains the asymmetry:

- complete absence over `n` independent uncommitted bits needs `n` raw probes;
- an existential positive claim needs one witness probe.

This does **not** imply that every absence query costs `n`. A maintained exact count,
authenticated nonmembership index, or persistent snapshot changes the visible/probed
coordinates. Its storage and update cost must then be charged elsewhere.

### 5. A storage-free “no anticipation” law is false

**Status: REFUTED.**

The audited Fable report correctly proved a storage-sensitive counting bound. For an
old fiber `B`, archive address set `A`, `w`-bit cells, and depth `t`, supporting every
Boolean extension requires

```text
2^(t w) log2(2|A|) >= |B|,
```

so some extension needs

```text
t >= (log2|B| - log2 log2(2|A|))/w.
```

It then overreached to a claim quantified over archives “however large.” That stronger
claim is false. Allocate one one-bit cell `a_f` for every Boolean function
`f:B->{0,1}` and store `D(h)[a_f]=f(h)`. A future extension named by `f` reads one
cell. The storage is enormous, but that is the point: there is no storage-free probe
lower bound.

The durable lesson is a tradeoff, not a slogan:

```text
future-contract richness × archive space × update work × query access
```

must be modeled together.

## The object that might be worth reaching for

### Contract-refinement spectrum

**Audit descriptor: speculative proposed research object; no repository evidence claim.**

Let `K_0 <= K_1 <= ...` be an online sequence of exact contract extensions over an
unbounded stream. Fix a natural syntactic contract class `C`, an archive model `A`, a
word size, and a soundness model. For a uniform implementation `Pi`, measure at horizon
`n`:

- `b`: active information;
- `s`: auxiliary archive/index information beyond the immutable event log;
- `u`: amortized update probes and writes;
- `x`: information transferred during contract refinement;
- `q`: query-time archive probes;
- `p`: proof length;
- `v`: verifier probes/work;
- `r`: proof invalidation and repair work;
- `f`: fallback mass;
- `e`: error.

Define the **contract-refinement spectrum** as the Pareto-minimal achievable resource
vectors:

```text
R_n(C,A) = ParetoMin_Pi (b,s,u,x,q,p,v,r,f,e).
```

The definition alone is not a discovery. The potentially deep theorem would identify a
natural, noncircular structural parameter `rho(C)` for which:

1. `rho=o(n)` has a constructive sublinear exact-justified regime;
2. `rho=Theta(n)` forces a matching linear cost on at least one charged coordinate;
3. the lower bound is stable under re-encoding, persistence, and authenticated indexes;
4. the theorem explains state-fiber splits, search trees, falsifier transversals, and
   proof repair as projections of the same object; and
5. the statement does not reduce immediately to view maintenance, dynamic data
   structures, annotated streams, or classical automata minimization.

If such a `rho` exists, it could be the sought invariant. If no natural `rho` exists,
the correct foundational result may instead be an impossibility theorem: exact future
semantic freedom has no representation-independent one-dimensional price.

### A more concrete conjectural duality

For locally verifiable provenance under bounded-dependency invalidation, there may be a
maintenance/verification duality:

> Every falsifier distinction not paid during updates by refining a binding index must
> be paid at query time by probes that hit the remaining falsifier family, or be exposed
> as fallback/error.

This is deliberately not labeled a theorem. The missing work is to define one fixed
dynamic archive model in which “paid during updates,” “binding,” and “remaining
falsifier family” are representation-independent enough to support a lower bound.

## What would actually change the verdict

### Confirmation threshold

A foundational candidate needs one theorem with all of these in the same model:

1. a contract grammar defined independently of the chosen data structure;
2. delayed boundary identity, ontology refinement, source invalidation, and continued
   ingestion after extension;
3. exact answers and locally binding exact justification;
4. fixed word size and charged active state, index space, update writes, query probes,
   verifier work, proof bytes, and repair;
5. a nonempty sublinear construction;
6. a matching lower bound within logarithmic factors;
7. an explicit counterexample or parameter boundary that kills the theorem outside its
   positive class; and
8. a serious primary-literature nonreduction audit.

### Kill threshold

Any of these would sharply lower the program:

- a direct prior theorem yields the exact checkpoint or `Q_(k,p)` formula;
- constant-radius invalidation forces linear repair even in the proposed positive
  class;
- charging schedules, authenticated summaries, address space, and indexes reveals
  hidden linear information in every “sublinear” construction;
- the proposed contract-refinement spectrum has no useful natural parameter beyond a
  restatement of arbitrary decision-tree complexity.

## The decisive 30-day program

Freeze a stable-key, bounded-dependency versioned-memory model:

- immutable event log;
- stable keys and source versions;
- dependency degree and invalidation radius `d=O(1)`;
- `w=Theta(log n)` external-memory cells;
- persistent authenticated B-tree/posting index;
- charged active bits, index bits, update reads/writes, refinement transfer, query
  probes, proof bytes, verifier probes, and repair writes;
- syntax-bounded contracts for membership, nonmembership, latest-valid-source
  provenance, and one delayed temporal boundary;
- adversarial continued ingestion and invalidation after each extension.

Build two independent finite checkers through `n<=8`: one over raw histories and one
over symbolic dependency/version states. Stop with exactly one of:

1. a matched upper/lower theorem within logarithmic factors;
2. a smallest constant-description linear-cost counterexample;
3. a formal reduction to a primary prior theorem; or
4. an honest `UNRESOLVED` verdict because an uncharged oracle remains.

Do not substitute a larger finite enumeration for one of those outcomes.

## Copy-paste GPT prompt: search for the missing mathematics

The prompt below is intentionally more creative than the Sol audit, but it keeps the
same proof and evidence discipline.

```text
You are Aion, an independent mathematical research agent looking for a result that
could define the theory of persistent intelligent systems long after today's LLM
architectures are obsolete.

This is not a request to praise, summarize, or incrementally extend the repository.
Your task is to search for the deepest new mathematics latent in it—and to kill every
candidate that reduces to known theory or survives only because a resource was not
charged.

SOURCE REPOSITORY

  /Users/jackg/Developer/active/justification-gap

SOURCE REF

  origin/codex/sol-synthesis-audit

Before reading the files below, fetch that ref and create a new isolated worktree and
new research branch from it. Do not start from main: main does not yet contain this
audit or reach document. Treat the new worktree as REPOSITORY for every subsequent
path and command.

READ FIRST

  AGENTS.md
  CLAUDE.md
  theory/reach.md
  theory/sol-synthesis-audit.md
  theory/certificate-continuation-research-ledger.md
  theory/justification-gap-program.md
  results/RESULTS.md
  NEXT.md

BASELINE TRUTH YOU MUST NOT ERASE

1. “Infinite context” has multiple meanings: raw-history retention, exact fixed-query
   answering, adversarial future queries, exact justification, ontology evolution,
   bounded active state, archive-backed reconstruction, and operational non-forgetting.
   Keep them separate.
2. Sparse exogenous complete-frontier checkpoints have an exact segment-product phase
   law. This is a strong specialized theorem under a fixed immutable ontology and a
   trusted frontier.
3. General archive dormancy is view determinacy; update dormancy is self-maintainable
   view maintenance; unrestricted continuation state is Myhill–Nerode-like; overlapping
   machines are closed covers; proof probes are certificate/cell-probe complexity.
4. State sufficiency, answer reconstruction, and proof verification are different
   geometries on one retained-state fiber.
5. There is no storage-free future-extension lower bound. A huge direct-answer archive
   can make every Boolean extension one-probe. Any valid law must charge address space,
   update work, or contract description.
6. No foundational result has yet survived. Do not upgrade this merely because you
   find elegant notation.

THE OPEN POSSIBILITY

The most promising proposed object is a contract-refinement spectrum: the Pareto
frontier of

  active information,
  retained index/archive information,
  update reads and writes,
  contract-refinement information transfer,
  query probes,
  proof length,
  verifier probes/work,
  proof invalidation/repair,
  fallback,
  and error

for an online chain of evolving exact contracts.

This object is only a proposal. It may be circular, classical, or useless. Your first
job is to attack it.

MISSION

Find whether there is a genuinely new invariant, duality, phase transition, or
impossibility principle coupling:

  semantic fiber refinement
  + layout-relative search
  + falsifier-hitting verification
  + online information transfer under contract change.

The desired result should matter for databases, scientific records, autonomous agents,
legal or medical audit systems, distributed state, and any future intelligent system—not
just transformers.

CREATIVE DIRECTIONS TO TEST, NOT ASSUME

A. A maintenance/verification duality: distinctions not installed into a binding index
   during updates must be hit by verifier probes later.
B. A refinement analogue of communication complexity: contract changes communicate a
   split of an old sufficient-statistic fiber, and cumulative refinement transfer may be
   lower-bounded by a natural joint-refinement quantity.
C. A dynamic transversal or proof-repair invariant connecting falsifier hypergraphs
   across time.
D. A topology or lattice of admissible contract extensions—but use category, sheaf,
   lattice, or topology language only if it produces an exact mapping and a theorem.
E. A non-scalar result: perhaps no complete one-dimensional invariant exists, but a
   finite-dimensional spectrum or dual pair does.
F. A natural maximal positive class, such as stable-key bounded-dependency provenance,
   where sublinear active state, exact answers, exact local justification, online
   updates, delayed boundaries, and efficient retrieval coexist without a hidden linear
   oracle.
G. A sharp impossibility theorem showing that adversarial semantic freedom is
   equivalent to injective reconstructive information, even when arbitrary computation,
   proofs, and persistence are allowed—but state the external-service and time model
   exactly.

OPERATING RULES

- Work in a new isolated worktree. Do not modify main.
- Inspect before editing. Preserve the repository evidence taxonomy.
- Treat every world-changing claim as false until statement, proof, resource model,
  scope, and novelty survive attack.
- Search current primary literature. Use original papers, monographs, or authoritative
  technical reports, not summaries.
- Build the smallest counterexample before building a general proof.
- For every enumerator, build a structurally different checker.
- A finite sweep proves only its finite domain unless an explicit induction, bijection,
  invariant, or reduction closes the asymptotic claim.
- Charge all information-bearing services: schedules, archive addresses, indexes,
  persistent snapshots, authenticated summaries, proof caches, contract compilers,
  version maps, and reconstruction time.
- Distinguish information-theoretic exactness from computational/cryptographic
  soundness.
- Do not use implementation bytes as entropy.
- Do not make paid model calls unless a frozen preregistered empirical test is genuinely
  necessary. Prefer mathematics and exact computation.
- Do not publish, push, or update the site.

PHASE 1 — RECONSTRUCT THE PROBLEM FROM FIRST PRINCIPLES

Define histories, online updates, visible state, external archive, contract syntax,
accepted answers, exact justification, verifier, contract extension, proof repair,
fallback, error, and every charged resource. Give at least two inequivalent definitions
of “non-degrading context” and decide which is mathematically worth studying.

PHASE 2 — INVENT CANDIDATE OBJECTS

Propose 3–5 candidate invariants or spectra. At least one must be non-scalar. For each:

- give the formal definition and quantifiers;
- explain what examples it compresses;
- compute it on E0, fixed-priority Q_(k,p), sparse checkpoints, rolling windows,
  first-bit versus parity, existential presence versus complete absence, and the direct-
  answer archive counterexample;
- state what would falsify its usefulness;
- identify the closest classical object.

Do not choose a winner before the computations.

PHASE 3 — SEARCH FOR A DUALITY OR MATCHED BOUND

Try to prove one theorem in a fixed online external-memory model. A preferred form is:

  constructive upper bound for a natural evolving-contract class
  + matching lower bound within logarithmic factors
  + explicit counterexample outside the class.

The theorem must include continued ingestion and invalidation after contract extension.
It must locally bind provenance to archive/version state. It must not trust a free
frontier.

PHASE 4 — ATTACK

Try to destroy each candidate with:

- re-encoding or persistent tabulation;
- enormous address space;
- a free or hidden schedule;
- targeted invalidation;
- delayed boundary identity;
- contradictory evidence;
- proof reuse on a same-state falsifier;
- nonuniform verifier advice;
- unbounded query time;
- an external reconstructive service;
- a reduction to view determinacy, dynamic data structures, cell probe, annotated
  streams, truth maintenance, authenticated dictionaries, or closed-cover theory.

PHASE 5 — PRIOR-ART COLLISION

Construct a claim-to-literature reduction matrix. Search especially:

- dynamic and incremental view maintenance;
- cell-probe lower bounds and dynamic communication complexity;
- certificates, nondeterministic data structures, and annotated streams;
- persistent/authenticated data structures;
- temporal databases and provenance with negation;
- truth-maintenance and dependency-directed invalidation;
- online automata/transducer minimization and incomplete machines;
- sufficient statistics, Blackwell comparison, and information complexity;
- dynamic hypergraph transversal and proof complexity;
- computational mechanics/predictive state only when the mapping is exact.

PHASE 6 — DECIDE

Use only these verdicts:

  FOUNDATIONAL RESULT
  FOUNDATIONAL CANDIDATE
  STRONG SPECIALIZED RESULT
  CLASSICAL REFRAMING
  INTERESTING CONJECTURE
  FALSE
  UNRESOLVED

A foundational candidate needs correctness, a sharp boundary, natural generality,
architecture independence, plausible novelty, reproducibility, falsifiability, and a
consequence for what systems should attempt to build.

REQUIRED DELIVERABLE

Write one internal report, theory/reach-aion-audit.md, containing:

1. Exact definitions and resource model.
2. Candidate-object table.
3. Small-case computations and independent checker results.
4. Strongest counterexamples.
5. Prior-art reduction matrix.
6. Strongest proved theorem, if any.
7. Strongest conjecture and its single missing lemma.
8. Whether the contract-refinement spectrum is useful, circular, classical, or false.
9. One decisive 30-day theorem-or-kill program.
10. A fifty-year textbook sentence—or an explicit statement that none exists.

FINAL STANDARD

Be severe and imaginative simultaneously. A negative theorem can be foundational. A
new exact object can be more important than a new architecture. But elegant relabeling
is not discovery, and a hidden archive is not infinite memory.

The goal is not to preserve the project narrative. It is to find the deepest true
statement available—and to say “not yet” if the missing mathematics is still missing.
```

## Final position

The project has crossed an important threshold: it now knows which parts of its general
story are classical, which exact formulas are worth preserving, which lower-bound
slogans are false, and what a verdict-changing theorem would have to charge.

That is not the destination. It is a credible launch point.
