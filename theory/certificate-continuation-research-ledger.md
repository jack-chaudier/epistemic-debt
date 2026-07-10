# Certificate continuation: research ledger

Status: active research note, 2026-07-09. This is not a paper and makes no
public novelty claim.

Evidence vocabulary in this note:

- **THEOREM** — accompanied here by a proof.
- **EXACT** — exhaustively computed by a committed validator.
- **OBSERVED** — an empirical repository result outside this note.
- **INFERENCE** — a conclusion from established or exact premises.
- **CONJECTURE** — a precise mathematical claim still needing proof.
- **IMPLEMENTATION ARTIFACT** — a property of the current encoding or program.
- **SPECULATION** — a possible direction without enough evidence for a conjecture.

The north star remains literal: an indefinitely growing intelligent history
must not silently lose the ability to recover, update, use, or completely
justify what it learned. Contract-relative state is a possible mechanism, not
a redefinition of that objective. An exact versioned archive remains necessary
whenever future queries are not frozen.

## 1. Result ledger

| ID | Status | Result | Artifact or obligation |
|---|---|---|---|
| E0.1 | **EXACT** | The audit masks for \(Q_{3,2}\), \(Q_{4,2}\), and \(Q_{5,3}\) are minimum common-certificate partitions and right congruences over all exact raw continuations. State counts are 6, 7, and 9. | `proofs/certificate_continuation.py`; frozen JSON; independent `certificate_continuation_naive.py` |
| E0.2 | **EXACT** | The lexicographically first \(Q_{5,3}\) static optimum is not right-congruent. Its first split is rows 6/9 under raw continuation `(0, (-1,-1,0))`, landing in rows 7/8. | Same artifacts |
| E0.3 | **EXACT** | No checked reported partition is left-congruent. The pre-existing probe-row quotient itself has representative-dependent left transitions. | Same artifacts |
| T1 | **THEOREM; standard characterization** | Exact deterministic finite online certificate state exists iff the contract admits a finite-index answer- and certificate-admissible right congruence. | Proof in §4; closest prior art in §10 |
| T2a | **THEOREM** | Every exact history implementation of the coded monotone \(Q_{k,p}\) contract needs at least \(k+1+p\) states, and a fixed-priority quotient attains the bound. | Reachable-behavior lower bound and construction in §5 |
| T2b | **THEOREM + EXACT instances** | Among active states required to be functions of the probe-joint row, minimum static and right-congruent partitions both have \(k+1+p\) blocks. Static minima number \(\prod_{s=2}^{p}s^{\binom ps}\); exactly \(p!\) minimum row partitions are right congruences, the fixed-priority selectors. | Proof in §5; checks in `certificate_priority_theorem.py` |
| T3 | **THEOREM** | For a fixed priority output in \(Q_{k,p}\), the minimum two-sided/chunk-composable quotient has \(\binom{k+p+2}{p+1}-1\) states: 34, 55, and 209 in E0. | Proof in §5; exact homomorphism and distinguishability checks |
| N1 | **THEOREM + EXACT instances** | Static common-certificate minimality can understate continuation state by an unbounded factor: a unary \(n\)-state chain has static minimum 2 and right-congruent minimum \(n\). | Proof in §6; exhaustive instances through \(n=8\) |
| N2 | **THEOREM + EXACT instance** | Minimum certificate machines need not be unique; admissible congruences are closed under meets but need not admit joins. | Proof/counterexample in §7 |
| N3 | **THEOREM + EXACT instance** | Pairwise certificate compatibility is not transitive and cannot replace nonempty global block intersection. | §7 and executable counterexample |
| N4 | **THEOREM** | Allowing arbitrary witness deletion in the survivor-set layer changes answer-continuation state from \(p+1\) under add-only updates to all \(2^p\) subsets. | §5; exact instances through \(p=8\) |
| N5 | **THEOREM + EXACT instances** | For a history-identifying contract in the deterministic cell-probe model of §8.4, a fast path with \(b\) active bits and \(t\) reads of \(w\) bits satisfies \(2^{b+tw}\ge N-F-E\), where \(F\) histories fall back and \(E\) are wrong. | `proofs/certificate_access_tradeoff.py`; exhaustive finite transcript assignments |
| N6 | **THEOREM + state-minimal EXACT instance** | Disjoint history fibers can project to an overlapping closed cover that is smaller than every partition of pre-aggregated semantic states: 2 implementation states versus a 3-state semantic partition minimum. | `proofs/certificate_congruence_counterexamples.py`; §10.1 |
| D1 | **EXACT + elementary counting theorem** | In a two-source/two-proposition versioned contract, complete current justification has 1/12/66/228 right-congruent frontier states at horizons 0–3; exact histories have 1/12/144/1,728. For fixed \(m\) cells, current frontier count is polynomial in horizon. | `proofs/versioned_memory_contract.py`; §8.5 |
| D2 | **EXACT + theorem for the model** | Complete all-as-of certificate sequences reconstruct every event and therefore have identity-size 1/12/144/1,728 state at horizons 0–3. | Same artifact |
| D3 | **EXACT counterexamples** | Current answer alone is not right-sufficient under retraction, and a later beta/as-of query separates histories soundly merged by an alpha-only contract. | Same artifact |
| D4 | **THEOREM + EXACT schedules** | For predeclared complete-frontier checkpoints \(0=t_0<\cdots<t_r=n\), exact certificate state factors as \(\prod_jG(t_j-t_{j-1})\). A sublinear checkpoint count gives sublinear active bits; for a nontrivial event alphabet \(m v\ge2\), linear checkpoint density forces linear bits. The degenerate \(m=v=1\) alphabet has zero information growth. | `proofs/checkpoint_frontier_theorem.py`; §8.5; every schedule checked through horizon 4 |
| D5 | **THEOREM + EXACT counterexample** | Permission to ask even one complete-frontier query at an adversarially selected past boundary makes all \((3m)^n\) event histories distinguishable. The number of queries exercised is not the relevant resource; the admissible boundary family is. | §8.5; first-differing-event proof |
| O1 | **OPEN** | Beyond D1's fixed finite ontology, does a broad revision-aware agent contract retain sublinear continuation state with low exact-fallback frequency as sources, propositions, and query semantics evolve? | Contract-family sweep and adversarial benchmark |
| O2 | **OPEN beyond N5** | Can one prove a nontrivial active-state/query-work/certificate-size/fallback tradeoff for noninjective answers, adversarial negative queries, or distributional workloads? | N5 settles only the history-identifying deterministic counting case |
| O3 | **RESOLVED / PRIOR ART** | T2b's row-selector law is path independence on the union semilattice; the total-priority classification is a classical special case. | Plott 1973; selector identity in §5 |

Progress classification: E0 is Level 1 validation. The combined package reaches
Level 3 as a theorem/counterexample map plus one fixed-ontology dynamic model;
T1, the path-independent selector algebra, and the compatible-state/closed-cover
skeleton are classical. There is no Level 4 general theory of broad lifelong
contracts and no Level 5 system result.

## 2. Resource model and target

Let \(H\subseteq\Sigma^*\) be a prefix-closed domain of admissible finite event
histories. “Indefinite” means every finite prefix, with no fixed maximum
length. It does not mean that a physical device completes an actually infinite
run. For a partial domain, histories sharing one machine state must agree on
which next events are admissible, or the contract must be totalized with an
explicit invalid-history state.

A contract is

\[
K=(H,\Sigma,Q,A,C),
\]

where, for history \(h\) and declared query \(q\):

- \(A_q(h)\) is the required answer;
- \(C_q(h)\) is the nonempty set of accepted sound certificate objects for
  that answer.

Equivalently, define the allowed answer-certificate relation

\[
O_q(h)=\{(A_q(h),c):c\in C_q(h)\}.
\]

Pairing answer and certificate prevents the same certificate syntax from
silently licensing conflicting answers. The certificate object may contain proof terms, source-version identifiers,
coverage claims, contradiction sets, temporal intervals, uncertainty, and
negative-evidence obligations. If the contract permits abstention, abstention
and its missing-obligation certificate must be represented explicitly as an
accepted output; it is not silently treated as correctness.

This program separates three resource models:

1. **Closed fixed state.** Total internal and external durable state is fixed.
2. **Fixed active / growing archive.** Online state is bounded or slowly
   growing, while an exact immutable archive grows and is available for
   fallback.
3. **Growing active state.** The online state itself may grow with the
   continuation index required by the contract.

All positive compact-state results below concern a **fixed declared contract**.
They do not preserve arbitrary queries invented after ingestion unless the raw
archive is retained. Query computation is not assumed free. For infinite
\(Q\), an effective implementation additionally needs computable answer and
certificate selectors.

## 3. Core definitions

### 3.1 Static admissibility

A block \(B\subseteq H\) is certificate-admissible when, for every
\(q\in Q\):

\[
\forall h,h'\in B,\quad A_q(h)=A_q(h'),
\]

and

\[
\bigcap_{h\in B} C_q(h)\ne\varnothing.
\]

The second condition is a global intersection. A chain of pairwise-overlapping
certificate sets is insufficient.

A static certificate partition is a partition into admissible blocks. It says
nothing yet about online updates.

### 3.2 Continuation admissibility

An equivalence relation \(\sim\) on histories is a right congruence when

\[
h\sim h'\Longrightarrow hx\sim h'x
\quad\text{for every }x\in\Sigma^*.
\]

It suffices to check all one-event continuations when events generate
\(\Sigma^*\). An **admissible right congruence** is both a right congruence and
certificate-admissible blockwise.

Right congruence is the exact online requirement: the next state is determined
by the current compact state and an exact incoming event. Left congruence is a
different and stronger requirement. It is needed if an independently compressed
history chunk is to be placed on the right and composed without reopening that
chunk. A two-sided congruence supplies a binary quotient semigroup. An online
transducer only requires a right action.

### 3.3 Machines

An exact deterministic certificate machine has:

- states \(S\), initial state \(s_0\), and transition
  \(\delta:S\times\Sigma\to S\);
- an output function \(o:S\times Q\to A\times\mathcal C\);
- for every history \(h\), if \(s(h)=\delta^*(s_0,h)\), then
  \(o(s(h),q)=(A_q(h),c)\) with \(c\in C_q(h)\).

The output function may emit a complete certificate or a machine-checkable
pointer to an exact retained object, provided pointer validity, version, and
coverage are part of the contract.

Define

\[
N_K=\min\{|S|:S\text{ implements }K\},
\]

with \(N_K=\infty\) when no finite machine exists. The working information
quantity is \(\log_2 N_K\) bits. For finite horizons, let \(N_K(n)\) be the
minimum state count for all histories and continuations whose total length is
at most \(n\). Calling \(\log_2N_K(n)\) a new invariant would be premature: it
is contract-specific finite-horizon state complexity, closely descended from
Myhill–Nerode theory.

## 4. Certificate-continuation characterization

### Theorem T1

For a fixed contract with nonempty accepted-certificate sets, an exact
deterministic \(m\)-state online certificate machine exists if and only if
there is an admissible right congruence of index at most \(m\). For an effective
machine, the quotient transition and a common certificate selector must also be
computable.

#### Proof

Forward direction: given a machine, define

\[
h\sim_M h'\iff s(h)=s(h').
\]

This kernel has at most \(m\) classes. Determinism gives
\(s(hx)=\delta^*(s(h),x)=\delta^*(s(h'),x)=s(h'x)\), so the kernel is a right
congruence. The single output emitted from the shared state has the same answer
and is an accepted certificate for every history in the class. Hence every
class is admissible.

Reverse direction: let \(\sim\) be an admissible right congruence. Use its
classes as states, \([\epsilon]\) as the initial state, and

\[
\delta([h],a)=[ha].
\]

Right congruence makes this well-defined. For each class and query, emit the
common answer and choose one element of the nonempty certificate intersection.
The block conditions make the output sound for every represented history.
There are at most \(m\) states. ∎

**Novelty assessment.** The proof is a kernel/quotient argument. Incompletely
specified and nondeterministic FSM minimization already studies compatible
states, closure under implied transitions, permissible outputs, and multiple
state-minimal implementations. T1 should be used to fix definitions, not sold
as a foundational new theorem.

### Fallback degeneracy

If a cost-free symbol `FALLBACK` is declared an accepted output for every
history and query, the universal one-block congruence implements the contract.
Then \(N_K=1\), a vacuous result. Exact fallback must therefore be modeled as a
charged resource or constrained service: report worst-case/frequency, archive
cells touched, latency, workspace, and proof size; or require the active state
to distinguish certified sufficiency from insufficiency. The archive-backed
architecture is valuable only if the fast path has nontrivial coverage.

### Proposition T1.1: selector-index form

For each deterministic admissible selector

\[
g_q(h)\in C_q(h),
\]

let \(O_g(h)=(A_q(h),g_q(h))_{q\in Q}\), and define

\[
h\equiv_g h'
\iff
\forall x\in\Sigma^*,\quad O_g(hx)=O_g(h'x).
\]

Then

\[
N_K=\min_g \operatorname{index}(\equiv_g).
\]

For fixed \(g\), \(\equiv_g\) is the canonical behavioral quotient. Optimizing
over multiple accepted certificates is what destroys the ordinary uniqueness
of the minimum object.

Proof: \(\equiv_g\) implements the selected single-valued output behavior. Any
machine induces such a selector from its emitted outputs, and its kernel
refines the corresponding behavioral equivalence. Minimize over selectors. ∎

### Proposition T1.2: monotonicity and composition

- Restricting queries, restricting continuations, or weakening accepted
  certificate requirements cannot increase \(N_K\).
- Adding queries, adding continuations, or strengthening certificate
  requirements cannot decrease \(N_K\).
- For the conjunction \(K_1\otimes K_2\) of two contracts over the same event
  system,

\[
\max(N_{K_1},N_{K_2})
\le N_{K_1\otimes K_2}
\le N_{K_1}N_{K_2}.
\]

The upper bound is the product machine; the lower bound follows because a
machine for the conjunction implements either projection. These are useful
accounting laws, but classical automata-product reasoning.

## 5. The \(Q_{k,p}\) law behind E0

The current coded family has raw states

\[
(d,c_1,\ldots,c_p),\qquad
0\le d\le k,\quad \bot\le c_i\le d,
\]

with capped shift-and-max right composition. Let

\[
S(h)=\{i:c_i=k\}
\]

be the surviving exact witnesses.

### Lemma T2.1: semantic row form

The probe-joint rows are exactly:

- \(B_d\), for \(0\le d\le k\), when \(S(h)=\varnothing\);
- \(F_S\), for every nonempty \(S\subseteq[p]\), when the survivors are \(S\).

Thus the probe-joint quotient has \(k+2^p\) rows. The answer quotient has
\(k+2\) states.

The optimized and naive validators reconstruct these rows independently from
all raw output traces. This semantic identification is **EXACT** for E0 and
follows algebraically from the coded output definition for general \(k,p\).

### Theorem T2a: exact history-state cardinality

For \(k\ge1,p\ge1\), every exact deterministic implementation on actual
histories needs at least \(k+1+p\) active states, and a fixed-priority
certificate quotient attains this bound.

Choose reachable histories with the \(k+1\) blocked behaviors
\(B_0,\ldots,B_k\). Their continuation answer profiles are pairwise distinct,
so no two can share a machine state. Choose reachable histories with singleton
survivor behaviors \(F_{\{1\}},\ldots,F_{\{p\}}\). At the identity query each
has a different sole accepted witness; they require \(p\) further states and
cannot merge with blocked histories because the answer differs. Thus every
history machine needs \(k+1+p\) states. A fixed total witness priority supplies
an exact quotient with that many states, proving equality. ∎

This cardinality proof is on history fibers and does not assume that active
state is a function of the pre-aggregated row. It therefore survives the
closed-cover distinction in §10.1.

### Theorem T2b: row-functional priority classification

Require that active state be a function of the probe-joint row. Then, for
\(k\ge1,p\ge1\):

1. the minimum static common-certificate partition has \(k+1+p\) blocks;
2. every static minimum is a selector \(f\) assigning each nonempty survivor
   set \(S\) to some \(f(S)\in S\);
3. the number of static minima is

   \[
   \prod_{\varnothing\ne S\subseteq[p]}|S|
   =\prod_{s=2}^{p}s^{\binom ps};
   \]

4. a static minimum is right-congruent exactly when a fixed total priority
   order \(\prec\) exists such that

   \[
   f(S)=\min_\prec S;
   \]

5. consequently the minimum right-congruent row-partition count is also
   \(k+1+p\), and there are exactly \(p!\) minimum right-congruent row
   partitions.

#### Proof

The \(k+1\) blocked rows cannot merge under the answer behavior exposed by the
probe family. Among feasible rows, singleton survivor sets \(F_{\{i\}}\) have
mutually incompatible sole certificates, so at least \(p\) feasible blocks are
needed. Conversely, assign every \(F_S\) to a block indexed by one selected
member \(f(S)\in S\). That member is a common certificate for the whole block,
giving \(k+1+p\) blocks. This proves the lower bound, construction, selector
form, and product count.

Under an exact right continuation, a feasible survivor set changes by union:

\[
S\mapsto S\cup U.
\]

Therefore a selector partition is right-congruent exactly if

\[
f(S)=f(T)\Longrightarrow f(S\cup U)=f(T\cup U)
\quad\text{for all }U.
\tag{1}
\]

Define \(i\prec j\) when \(f(\{i,j\})=i\). This is a tournament. If
\(i\prec j\) and \(j\prec \ell\), apply (1) to the equal-choice pairs
\((\{i,j\},\{i\})\) with addition \(\{\ell\}\), and
\((\{j,\ell\},\{j\})\) with addition \(\{i\}\). Both determine
\(f(\{i,j,\ell\})\), forcing \(i\prec\ell\). Hence \(\prec\) is transitive and
therefore a total order.

If \(f(S)=j\) while some \(i\in S\) has \(i\prec j\), apply (1) to \(S\) and
\(\{j\}\), which share choice \(j\), adding \(\{i\}\). It would force
\(f(\{i,j\})=j\), a contradiction. Thus \(f(S)=\min_\prec S\).

Conversely, if \(f\) chooses the minimum of a fixed order and
\(f(S)=f(T)=i\), then both \(S\cup U\) and \(T\cup U\) choose the minimum of
\(\{i\}\cup U\). So (1) holds. Blocked-state transitions depend only on their
depth and the exact continuation; when they become feasible, the same priority
selector applies. This supplies the full right action. There are \(p!\) total
orders. ∎

T2b does **not** classify every minimum history implementation. A history
machine may retain which witness it selected along the path even when two
histories project to the same survivor row. Such path-dependent machines have
disjoint fibers on histories but overlapping projected row blocks; §10.1 gives
the exact closed-cover construction.

The finite checker confirms selector counts through \(p=4\):

| \(p\) | static minima | right-congruent minima |
|---:|---:|---:|
| 1 | 1 | 1 |
| 2 | 2 | 2 |
| 3 | 24 | 6 |
| 4 | 20,736 | 24 |

It also checks 900,669 raw transition instances through \(k=5,p=3\). These
computations support the implementation and catch encoding mistakes; the proof,
not the sweep, establishes the general result.

### Left-composition boundary

**THEOREM for this row encoding.** The probe-row quotient is not left stable
for \(k,p\ge1\). At depth zero, the raw states

\[
(0,\bot,\ldots,\bot)
\quad\text{and}\quad
(0,\bot,\ldots,0,\ldots,\bot)
\]

both lie in \(B_0\). Prepending the exact state
\((k,\bot,\ldots,\bot)\) leaves the first blocked but shifts the marked zero in
the second to a surviving witness. Thus a left continuation distinguishes two
representatives already merged inside one row.

This does **not** mean the exact raw monoid lacks a two-sided representation;
the discrete raw-state partition does. It means the compact \(k+1+p\) object is
a right action for streaming exact events, not a semigroup quotient capable of
combining two independently compressed histories.

### Theorem T3: fixed-priority two-sided quotient

Fix priority \(1\prec2\prec\cdots\prec p\). For raw state
\((d,c_1,\ldots,c_p)\), define prefix maxima

\[
m_i=\max_{j\le i}c_j,
\qquad
\Phi(d,c_1,\ldots,c_p)=(d,m_1,\ldots,m_p).
\]

Then \(\Phi\) is a semigroup homomorphism and is the minimum two-sided quotient
for this fixed priority-selected output. Its exact state count is

\[
\left|\operatorname{im}\Phi\right|
=\sum_{d=0}^{k}\binom{d+p+1}{p}
=\binom{k+p+2}{p+1}-1.
\]

Proof: capped shift is monotone, so taking a prefix maximum commutes with the
coordinatewise shift-and-max composition:

\[
\max_{j\le i}\max(c_j,\operatorname{shift}_d(t_j))
=
\max(m_i,\operatorname{shift}_d(\max_{j\le i}t_j)).
\]

The priority-selected certificate is the first \(i\) with \(m_i=k\), so the
summary determines the output. Different depths are already distinguished by
the blocked residual behavior. At equal depth, if the first differing prefix
maximum is \(m_i<n_i\), prepend depth \(k-n_i\) with bottom coordinates. A
priority at most \(i\) reaches \(k\) in the second state but not the first, so
their selected outputs differ. Hence no two image states can merge for the
fixed behavior. At depth \(d\), the nondecreasing sequence
\(-1\le m_1\le\cdots\le m_p\le d\) has \(\binom{d+p+1}{p}\) possibilities;
the hockey-stick identity gives the total. ∎

For E0 this yields 34, 55, and 209 states. The primary validator independently
finds exactly 34/55/209 distinct continuation actions and emits their binary
composition tables; the theorem checker separately verifies the prefix-max
homomorphism and constructive distinguishers.

This sharpens the systems boundary:

| Capability | Exact state in \(Q_{k,p}\) |
|---|---:|
| append exact events to compact active state | \(k+1+p\) |
| combine independently summarized chunks for a fixed priority behavior | \(\binom{k+p+2}{p+1}-1\) |
| retain the full probe-joint witness behavior | \(k+2^p\) rows, but not left-stable after the raw-to-row collapse |

T3 proves fixed-selector minimality. Whether another allowed, path-dependent
certificate-selection strategy has a smaller two-sided realization remains an
open relational-minimization question.

### Significance of T2a/T2b

T2a upgrades the audit’s three finite observations to a general state-count
theorem for the coded family. T2b classifies the row-functional optima. They
also expose the real assumption: survivor evidence is
monotone under right updates, and one fixed-priority surviving witness is always
an accepted certificate. That is far narrower than versioned reasoning with
retractions, contradictions, or complete negative evidence.

The coded blocked output uses the empty witness tuple as an accepted certificate.
That is an **IMPLEMENTATION ARTIFACT**, not a machine-checkable proof that no
witness exists or that all relevant sources were searched. D1 supplies an
actual negative-evidence contract by requiring an authenticated complete source
frontier; T2a/T2b alone do not establish complete negative justification.

Equation (1) implies

\[
f(S\cup T)=f(\{f(S),f(T)\}),
\]

the standard path-independence identity for a single-valued choice function on
the union semilattice. The total-priority classification is therefore a direct
specialization of classical path-independent choice, not an independently new
choice theorem. The repository-specific bridge to accepted justification is
useful; the algebraic selector result itself is prior art.

### Theorem N4: arbitrary retraction phase transition

On the survivor-set layer, add-only updates \(S\mapsto S\cup T\) admit the
empty state plus \(p\) priority states. If arbitrary deletions
\(D_T(S)=S\setminus T\) are permitted, every two subsets are
answer-continuation-distinguishable. For \(S\ne S'\), choose
\(i\in S\triangle S'\) and delete every witness except \(i\). One result is
feasible and the other empty. Therefore even answer-only exactness requires all
\(2^p\) survivor subsets.

This is an exact add/retract boundary, not merely a warning that retractions
“might be harder.” It explains why T2a cannot be extrapolated to arbitrary
belief revision.

## 6. Static compatibility does not predict online memory

### Theorem N1: unbounded static/continuation gap

For every \(n\ge3\), there is a deterministic unary contract with one constant
answer whose minimum static certificate partition has 2 blocks but whose
minimum right-congruent certificate machine has \(n\) states.

#### Construction and proof

Take states \(0,1,\ldots,n-1\), unary update

\[
T(i)=\min(i+1,n-1),
\]

certificate set \(\{\alpha\}\) for states below \(n-1\), and
\(\{\beta\}\) at state \(n-1\). The partition

\[
\{0,\ldots,n-2\}\mid\{n-1\}
\]

is a valid static two-block partition, and one block is impossible because
\(\alpha\) and \(\beta\) do not intersect.

Suppose \(i<j<n-1\) were merged by a right congruence. After
\(n-1-j\) updates, \(j\) reaches the \(\beta\)-only state while \(i\) remains
\(\alpha\)-only. Right congruence would require those incompatible states to
remain merged, contradiction. The final state is already incompatible with all
earlier states. Hence every state is separate and the minimum is \(n\). ∎

This family is the sharp counterexample to the tempting generalization that E0
could have supported. The E0 equality is a special algebraic law, not a general
property of common-certificate aggregation.

A three-state commutative-monoid version is state-minimal: with elements
\(e,a,z\), identity \(e\), \(a^2=z\), and absorbing \(z\), give \(e,a\) only
certificate \(\alpha\) and \(z\) only \(\beta\). Static minimum is 2; right,
left, and two-sided minimum are all 3. No two-state counterexample exists,
because if its static minimum were one block, every transition maps that sole
block into itself.

## 7. Global intersections and noncanonical minima

### Proposition N2: nonuniqueness and failure of joins

Minimum admissible certificate machines need not be unique. Consider states
\(e,u,v,w\): \(e\) has start output/certificate \(z\); inputs \(U,V,W\) send
\(e\) to the correspondingly named absorbing state; and accepted certificates
at \(u,v,w\) are \(\{\alpha\}\), \(\{\alpha,\beta\}\), and \(\{\beta\}\).

There are two minimum three-state right machines:

\[
\{e\}\mid\{u,v\}\mid\{w\}
\quad\text{and}\quad
\{e\}\mid\{u\}\mid\{v,w\}.
\]

Their equivalence-relation join merges \(u,v,w\), whose certificate
intersection is empty. Thus the join is not admissible.

Admissible right congruences are closed under arbitrary meets: intersection
refines each relation, right congruence survives, and smaller blocks cannot
lose an existing common certificate. They need not be closed under joins, so
there need not be one coarsest/canonical minimum congruence. The canonical
object returns only after an accepted-certificate selector is fixed.

### Proposition N3: pairwise compatibility is insufficient

Certificate sets \(\{a,b\}\), \(\{b,c\}\), and \(\{a,c\}\) have nonempty
intersection for every pair but empty three-way intersection. Even the full
pairwise compatibility graph can therefore accept an invalid block. The
simpler chain \(\{a\},\{a,b\},\{b\}\) also shows that pairwise compatibility
is not transitive. Certificate blocks are hyperedges defined by global
intersection, not equivalence classes obtained by transitive closure of
pairwise overlap.

This is where ordinary pairwise-compatible-state machinery must be translated
carefully: the repository’s contract requires one certificate valid for every
history in a block, which is stronger than pairwise overlap when accepted sets
lack a Helly property.

## 8. State-complexity boundaries

### 8.1 Fixed contract

**THEOREM.** A fixed contract has bounded exact active state precisely when its
admissible continuation index is finite (T1). T2a is an \(O(1)\) example after
the capped \(k,p\) contract is fixed. N1 shows that a tiny static certificate
description does not imply a tiny continuation index.

### 8.2 Arbitrary future queries

**THEOREM.** Let histories of length \(n\) range over an alphabet of size
\(|\Sigma|\ge2\), and let the future query family contain enough predicates to
distinguish every pair of histories—for example, exact-history equality or
coordinate queries. Any exact closed-state system needs at least
\(|\Sigma|^n\) states, or \(n\log_2|\Sigma|\) bits.

Proof: two histories mapped to one state would receive identical future
outputs, while a distinguishing admissible query requires different answers.
This is the pigeonhole argument with its resource model and separating query
family stated explicitly. ∎

If those distinguishing queries may be introduced after ingestion, no fixed
contract quotient can protect a distinction it discarded. An exact archive is
therefore not optional for the literal evolving-query objective.

### 8.3 Exact archive and fallback

**THEOREM / construction.** For every finite prefix and every total computable
query under retained versioned semantics, a bounded-active system can match a
halting direct-access reference by keeping an injective archive and replaying
it. Storage and worst-case query work are allowed to grow.

This is logical possibility, not a compact-state breakthrough. The scientific
question is whether a certified fast state makes replay rare on a broad
contract without ever making an unsupported assertion.

### 8.4 Working width quantity

For finite horizons, the tentative quantity

\[
W_K(n)=\log_2 N_K(n)
\]

has immediate but mostly classical laws:

- query restriction and certificate weakening cannot increase it;
- contract conjunction lies between the maximum and sum of component widths;
- unrestricted history-separating queries give \(W_K(n)=\Omega(n)\);
- the unary delayed-certificate family has \(N=n\), hence
  \(W=\Theta(\log n)\), despite static width of one bit;
- fixed finite-index contracts have \(W=O(1)\).

The potentially important work is not naming this logarithm. It is finding
natural lifelong contracts with provably favorable growth, or proving that
revision, contradiction, negative evidence, and evolving ontologies force
identity-like growth.

#### Deterministic archive-access/fallback bound

Fix a query whose accepted answer/certificate output sets are pairwise disjoint
on \(N\) histories. Suppose a deterministic responder starts from \(b\) bits of
active state and adaptively reads at most \(t\) cells of \(w\) bits from a
history-dependent exact archive with a fixed address space. Read addresses are
functions of the query, active state, and previous cell contents, so the
active-state/read transcript has at most \(2^{b+tw}\) values.

If the responder falls back on \(F\) histories and is wrong on \(E\), then

\[
2^{b+tw}\ge N-F-E,
\qquad
b+tw\ge\left\lceil\log_2(N-F-E)\right\rceil.
\]

Proof: every correct nonfallback history must have a different transcript;
otherwise the deterministic responder emits the same output on two histories
whose accepted output sets are disjoint. There are at least \(N-F-E\) such
histories and at most \(2^{b+tw}\) transcripts. ∎

If each accepted fast output is a fixed-length string of at most \(L\) bits,
then independently \(2^L\ge N-F-E\). Certificate length is therefore a second
bottleneck, not a term that can simply be added to information the responder
never accessed. This kills a tempting but ill-specified additive inequality:
the valid bound depends on the communication and verification model.

Applied to D2, \(N=(3m)^n\). If the no-read fast path has only the
current-frontier state, \(2^b\) is polynomial in \(n\) for fixed \(m\), so its
maximum correct coverage on the history-identifying all-as-of contract tends to
zero exponentially and the forced fallback fraction tends to one. At \(m=4\),
\(n=4\), 10 current-frontier bits can cover at most 1,024 of 20,736 histories,
forcing at least 95.06% fallback or error. The executable exhaustively verifies
the finite transcript-capacity core and the D1/D2 counts. This is a standard
counting/communication lower bound made contract-explicit, not a novelty claim.

### 8.5 Versioned dynamic contract: the first non-\(Q\) boundary

`proofs/versioned_memory_contract.py` defines a formal contract with two
sources, two propositions, and three publication events per source/proposition
cell: support, refute, and retract. Repeated publication is a revision; every
event increments the immutable source-local version. The contract includes:

- current `UNKNOWN` / `SUPPORTED` / `REFUTED` / `CONFLICT` queries;
- as-of-prefix temporal queries;
- additions, polarity-changing revisions, retractions, and contradictions;
- delayed relevance under later query-family expansion;
- complete negative-evidence certificates containing the latest authenticated
  version/value or authenticated absence for every source.

The exact finite-horizon result is:

| horizon | exact histories | current answers | current complete-certificate right states | full source-local ledgers | temporal answers | complete all-as-of certificate states |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1 | 12 | 5 | 12 | 12 | 5 | 12 |
| 2 | 144 | 11 | 66 | 90 | 29 | 144 |
| 3 | 1,728 | 15 | 228 | 540 | 173 | 1,728 |
| 4 | 20,736 | — | 579 | 2,835 | — | 20,736 |

The horizon-4 row is an extension check; dashes indicate values not frozen as
headline anchors, not failed computations.

For \(m\) fixed source/proposition cells, three event values, and exact horizon
\(n>0\), the current complete frontier count is

\[
N_{\mathrm{current}}(n)
=
\sum_{r=1}^{\min(m,n)}
\binom mr\binom{n-1}{r-1}3^r
=\Theta(n^{m-1}).
\]

Choose the \(r\) cells touched, distribute \(n\) positive event counts among
them, and choose each cell’s latest value. Because the accepted current
certificate is a singleton authenticated frontier, distinct frontiers cannot
merge statically; equality blocks are right-congruent under every publication.
For fixed \(m\), active information grows only as \(O(\log n)\) bits even
though exact global histories number \((3m)^n\) and require \(\Theta(n)\) bits.
The compact current state discards cross-cell interleaving and superseded
values while preserving the complete latest provenance/coverage contract.

The positive result has a matching negative boundary. Asking for the complete
frontier at every as-of boundary reconstructs the changed cell, new version,
and value at every step. The all-as-of certificate quotient is therefore the
identity on histories in this model. Full source-local value ledgers, which
discard only cross-cell interleaving, still number

\[
\binom{n+m-1}{m-1}3^n.
\]

#### Checkpoint factorization and temporal-density phase law

Let the event alphabet contain \(m\) cells and \(v\) possible publication
values per cell. For a segment of length \(\ell>0\), define

\[
G_{m,v}(\ell)=
\sum_{s=1}^{\min(m,\ell)}
\binom ms\binom{\ell-1}{s-1}v^s,
\qquad G_{m,v}(0)=1.
\]

This counts the segment's per-cell publication increments and final value for
each touched cell. For exogenously declared complete-frontier checkpoints

\[
0=t_0<t_1<\cdots<t_r=n,
\]

the exact minimum certificate-state count is

\[
N_T(n)=\prod_{j=1}^{r}G_{m,v}(t_j-t_{j-1}).
\tag{2}
\]

Proof: adjacent complete frontiers reveal every per-cell count increment by
version subtraction and the segment's final value for each touched cell.
Conversely, applying any valid segment summary to a prefix frontier determines
the next frontier. Starting from the fixed empty frontier gives a bijection
between checkpoint-frontier tuples and independent segment summaries. Because
the accepted complete-frontier certificate is unique, distinct tuples cannot
merge. ∎

Every checkpoint subset through horizon four is exhaustively checked against
(2), including an independent cell/value implementation that imports none of
the semantic contract code. For \(m=4,v=3,n=4\), current-only needs 579 states; boundaries
\(\{1,4\}\) need 2,736; \(\{2,4\}\) need 4,356; \(\{1,2,4\}\) need 9,504;
and all boundaries need 20,736, exactly the history count.

For fixed \(m>1,v>1\),

\[
\log N_T(n)
=\Theta\!\left(r+(m-1)\sum_j\log(t_j-t_{j-1})\right).
\]

Consequently a fixed number of predeclared checkpoints needs \(O(\log n)\)
bits; \(r=o(n)\) checkpoints need \(o(n)\) bits; and \(r=\Theta(n)\) forces
\(\Theta(n)\) bits. Unit gaps give exact identity. A last-\(r\)-boundaries
rolling window has

\[
G_{m,v}(n-r)(mv)^r
\]

states: a compact prefix frontier plus the exact last \(r\) events.

The sharp negative is stronger than “print every old certificate.” If the
system will receive only one temporal query but its boundary may be selected
adversarially from \(\{1,\ldots,n\}\) after ingestion, all \((mv)^n\) histories
are distinguishable. For two different histories, query the boundary of their
first differing event; the version vector or latest value differs there. Thus
the admissible boundary family, not the number of queries eventually exercised,
sets the state requirement.

Archive-free online updates require that a later contract never newly demand
an older boundary that was not retained. The smallest failure is the pair
`AB` and `BA`: they share the same complete current frontier after two events,
but their boundary-one frontiers differ. A retroactively introduced boundary-
one query therefore requires replay or a prior refinement. Exact version
counters, one-cell events, unique authenticated complete frontiers, a fixed
event alphabet, and an exogenous checkpoint schedule are load-bearing.

Two adversaries pin the contract assumptions:

1. current answer alone merges “Alice supports alpha” with “Bob supports
   alpha”; retracting Alice separates the next answers (`UNKNOWN` versus
   `SUPPORTED`), so answer-only state is not right-sufficient;
2. two histories differing only on beta are safely merged under an alpha-only
   contract, but a later beta as-of query separates them. Query expansion
   therefore requires archive fallback or certified refinement.

**Interpretation.** This is the first meaningful non-\(Q\) construction in the
program. It gives a real logarithmic-active-state path for complete **current**
justification over a frozen finite ontology, while proving identity-like cost
for complete **all-as-of** justification. It is not yet a broad lifelong-agent
theorem: the source/proposition universe and semantics are fixed, frontier
completeness is authenticated, exact history still grows, and arbitrary new
queries fall back to that archive.

## 9. Architecture implied by the mathematics

The strongest architecture still standing is a **verified contract cache over
an exact archive**:

1. append each event and every relied-upon source version to a content-addressed,
   immutable, ordered archive;
2. compile a fixed query/update/certificate contract into a deterministic
   certificate transducer or a sound refinement of one;
3. maintain a compact active state plus a machine-checkable proof that the
   current history maps to it;
4. attach provenance, version, contradiction, temporal, uncertainty, and
   coverage obligations to each emitted certificate;
5. permit a fast answer only when the state’s common-certificate condition is
   verified for the query;
6. otherwise abstain or execute exact replay over the archive;
7. turn every replay counterexample into a state split, in a
   counterexample-guided refinement loop;
8. when the query contract or ontology changes, invalidate the old sufficiency
   proof and recompile/refine from the archive;
9. gate every consequential assertion on certificate verification.

Resource accounting is explicit:

| Resource | Fast path | Exact fallback |
|---|---|---|
| Archive storage | grows at least with retained exact information | same archive |
| Active state | \(\lceil\log_2N_K\rceil\) bits, plus integrity metadata | workspace may grow |
| Update work | transducer update plus archive append | recompilation may scan history |
| Query work | state/query output and certificate verification | reference computation, potentially full replay |
| Proof size | contract-dependent | may grow with evidence and negative coverage |
| Latency | small only when sufficiency is certified | unbounded in history length in the worst case |

This is not ordinary RAG: retrieval success is insufficient without a proof of
coverage and source/version validity. It is not universal compression: the raw
archive pays the information cost. The proposed capability is narrower—prove
when the compact state is behaviorally equivalent to full replay, and fail
closed when that proof is absent.

## 10. Primary-literature novelty attack

| Prior object | Direct source | What it already supplies | What, if anything, remains distinct here |
|---|---|---|---|
| Myhill–Nerode continuation equivalence | [A. Nerode, “Linear Automaton Transformations,” 1958](https://doi.org/10.1090/S0002-9939-1958-0135681-9) | Finite-index right equivalence and canonical minimal deterministic behavior | T1 is a relational-output restatement after selecting accepted certificates, not a new iff principle |
| Sequential-machine distinguishability | [E. F. Moore, “Gedanken-Experiments on Sequential Machines,” 1956](https://doi.org/10.1515/9781400882618-006) | Behavioral state distinguishability under future experiments | Supports the continuation viewpoint; does not add justification semantics |
| Incompletely specified FSM minimization | [Rho, Hachtel, Somenzi, Jacoby, “Exact and Heuristic Algorithms for the Minimization of Incompletely Specified State Machines,” 1994](https://web.cecs.pdx.edu/~mperkows/CLASS_573/Asynchr_Febr_2007/00259940.pdf) | Compatible states, implications, closed covers, exact minimization, multiple state-minimal machines; explicitly distinguishes a covering lower bound with closure dropped | Static certificate partitions versus right closure reuse this classical optimization skeleton |
| Permissible/nondeterministic FSM behavior | [Kam, Villa, Brayton, Sangiovanni-Vincentelli, “Theory and Algorithms for State Minimization of Non-Deterministic FSM’s,” 1995](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1995/ERL-95-107.pdf) | Selects a deterministic behavior contained in a set-valued specification using generalized compatibles and minimum closed covers | This is the closest prior art and makes the naked certificate-selector minimization problem non-novel; proof/provenance semantics and resource tradeoffs would need to supply the difference |
| Path-independent choice | [C. R. Plott, “Path Independence, Rationality, and Social Choice,” 1973](https://authors.library.caltech.edu/records/besvk-pqy14) | Union/path-stable single-valued choice has an established algebraic characterization | T2b’s row-selector identity is a direct special case; O3 is resolved against novelty |
| Persistent data structures | [Driscoll, Sarnak, Sleator, Tarjan, “Making Data Structures Persistent,” 1989](https://www.cs.cmu.edu/~sleator/papers/making-data-structures-persistent.pdf) | Access to old and new versions with efficient structural sharing | Solves version retention, not query-contract state minimization or justification completeness |
| Database provenance | [Buneman, Khanna, Tan, “Why and Where,” 2001](https://www.research.ed.ac.uk/files/16509989/Why_and_Where_A_Characterization_of_Data_Provenance.pdf); [Green, Karvounarakis, Tannen, “Provenance Semirings,” 2007](https://www.cs.ucdavis.edu/~green/papers/pods07.pdf) | Source lineage and compositional provenance annotations | Supplies certificate representation pieces; positive semiring provenance alone does not certify negation, completeness, or future continuation sufficiency |
| Truth maintenance | [J. Doyle, “A Truth Maintenance System,” 1979](https://doi.org/10.1016/0004-3702(79)90008-0) | Recorded reasons, contradictions, belief revision, explanation, dependency-directed repair | Natural substrate for the dynamic contract; no compact continuation-state theorem identified |
| Reversible computation | C. H. Bennett, reversible-simulation/time-space results | Exact reconstruction by retaining history/garbage and explicit time-space tradeoffs | Reinforces that reversibility preserves information by paying resources; it is not a compact epistemic quotient |
| Recursive language models | [Zhang, Kraska, Khattab, “Recursive Language Models,” 2025](https://arxiv.org/abs/2512.24601) | Programmatic access to external prompts and recursive subcalls beyond the base window | A query-work mechanism; it does not prove completeness, source validity, or non-degradation for every delayed query |

**Current novelty verdict.** The general certificate-continuation object is a
proof/provenance interpretation of classical minimization of incompletely
specified or nondeterministic machines with permissible outputs. T1, selector
optimization, closure, nonunique minima, and path-independent choice are not a
new automata-theoretic foundation. The exact \(Q_{k,p}\) bridge, T3's quantified
right-versus-two-sided gap, and D1/D2's current-versus-all-as-of boundary are
useful repository results, but no novelty claim is made for their bare
automata skeleton. A lasting contribution would require certificate-specific
semantics or a new theorem about proof completeness, provenance, contract
refinement, or the state/work/proof/fallback tradeoff.

### 10.1 Partitions, history fibers, and closed covers

Classical incompletely specified-machine minimization uses overlapping
**closed covers**, not only partitions. This creates three optimization problems
that must not be silently conflated:

1. a quotient that is a function only of the repository's current aggregated
   row state;
2. an arbitrary deterministic implementation over actual histories, whose
   state fibers are disjoint on histories;
3. a closed cover obtained by projecting those history fibers onto a
   pre-aggregated relational specification, where compatible sets may overlap.

The E0 validator solves the first problem exactly. Its analytic singleton and
depth lower bounds protect T2a's \(k+1+p\) right-state count for the coded
\(Q_{k,p}\) history contract, so the reported E0 optimum is not merely a
partition-search artifact. In a general pre-aggregated semantic model, however,
partition-only search can miss a smaller history-dependent implementation.

The smallest strict example has semantic states \(0,1,2\), with accepted
certificates \(\{\alpha\}\), \(\{\alpha,\beta\}\), and \(\{\beta\}\). Input
\(x\) maps \(0,1,2\) to \(2,1,0\); reset-like input \(r\) maps all three to
\(1\). Every admissible right-congruent semantic partition has three blocks,
but the overlapping blocks

\[
X=\{0,1\},\qquad Y=\{1,2\}
\]

form a two-state closed cover: \(x\) swaps \(X,Y\), while \(r\) may retain the
current cover state because its image \(\{1\}\) lies in both. From one initial
state, semantic state 1 is reachable paired with either implementation state.
One implementation state is impossible because states 0 and 2 have disjoint
certificates. No strict cover advantage is possible with fewer than three
semantic states. The executable checks every partition, cover transition, and
reachable semantic/implementation pair.

For \(Q_{k,p}\), the overlapping feasible blocks

\[
C_i=\{F_S:i\in S\}
\]

together with singleton \(B_d\) blocks form a \(k+1+p\)-block closed cover.
They implement a path-dependent “sticky witness”: choose a valid witness when
feasibility first appears and retain it, since monotone continuation never
removes it. Thus the lower bound protects the optimum **cardinality**, but the
\(p!\) count classifies only minimum row-functional congruence partitions, not
all minimum history machines.

If \(H=\Sigma^*\), path-dependent selectors are admissible. If the contract
instead declares the finite raw continuation semigroup itself as \(H\), or
requires every decomposition of an equal raw product to induce the same active
transition, the implementation must factor through that semantic quotient.
Those are different contracts. Translating accepted proof objects and global
common-certificate obligations into closed-cover semantics is therefore a
load-bearing scope choice, not optional terminology.

## 11. Dependency graph

```text
fixed contract K
  |
  +-- accepted answer/certificate relation O(h,q)
  |       |
  |       +-- global block intersection (not pairwise overlap)
  |
  +-- exact update action on histories
          |
          +-- admissible right congruence
                    |
                    +-- finite index <=> finite exact online machine (T1)
                    |
                    +-- minimum index N_K
                          |
                          +-- fixed selector: canonical Nerode quotient
                          +-- flexible selector: possibly nonunique minima
                          +-- composition/monotonicity bounds

history fibers --many-to-one semantic projection--> overlapping closed cover
  +-- may beat every partition of semantic states (N6)
  +-- does not invalidate the history-fiber theorem

Q_(k,p) survivor-union algebra
  +-- static selector blocks
  +-- union stability
  +-- history-state cardinality (T2a)
  +-- row-functional total-priority classification (T2b)

versioned complete-frontier algebra
  +-- current frontier: polynomial states for fixed ontology (D1)
  +-- ex ante checkpoints: product over segment summaries (D4)
  +-- adversarial retrospective boundary: identity (D5)

literal evolving-query objective
  +-- fixed quotient can be invalidated by a new separating query
  +-- exact archive required
  +-- certified compact state is a cache, never the sole source of truth
```

## 12. Failed ideas and assumptions doing the work

1. **Failed generalization:** “a minimum static certificate partition can
   always be chosen right-congruent at the same size.” N1 refutes it with an
   unbounded gap.
2. **Failed canonicality:** flexible accepted outputs can yield multiple
   state-minimal machines and no admissible join.
3. **Failed pairwise reduction:** overlap is nontransitive and does not imply a
   blockwise common certificate.
4. **Failed two-sided interpretation:** E0’s compact state does not compose two
   independently summarized chunks.
5. **Load-bearing positive assumption in T2a/T2b:** witness survival is monotone by
   set union, and any one surviving witness remains a permanently accepted
   certificate.
6. **Load-bearing global assumption in T1:** the query/update/certificate
   contract is fixed. Evolving ontologies can split every old state.
7. **Load-bearing systems assumption:** an exact archive, source versions, and
   interpreters are retained. A pointer to mutable or vanished bytes is not
   reconstruction.

## 13. Next decisive questions

Priority order:

1. D4/D5 solve temporal density for unique complete frontiers. Now vary the
   source/proposition universe, incomplete coverage, multiple accepted proofs,
   cross-proposition dependencies, and permitted retractions. Determine which
   proof semantics preserve the segment factorization.
2. Generalize N6's exact closed-cover gap to proof-carrying machines: determine
   when a projected overlapping cover is implementable with machine-checkable
   provenance and when factorization through a semantic quotient is required.
3. Formalize contract extension and counterexample-guided refinement: quantify
   the archive work needed when a later query splits an old active state.
4. Strengthen N5 beyond the history-identifying counting case. Seek a lower
   bound for noninjective answers with completeness certificates, adversarial
   negative queries, or distributional fallback.
5. Stress D1 with delayed queries whose relevance appears
   only after retractions, version changes, contradictions, or long dependency
   chains.
6. Preregister a reference verified-contract-cache architecture around D1/D4.
   Measure answer correctness and complete justified correctness separately,
   together with archive growth, active state, records touched, proof size,
   latency, and fallback frequency.

### Kill criteria for the compact-state sliver

The nontrivial path is substantially weakened if either result appears:

- for the intended broad dynamic contract, \(N_K(n)\) approaches the exact
  semantic/history state count and certified fast-path coverage tends to zero;
- computing or verifying the common certificate requires essentially the same
  work as exact replay on adversarial histories.

The raw-archive construction would remain logically correct, but the hoped-for
new compact invariant would be gone.

### Evidence that would raise significance

- a natural revision-aware contract with provably sublinear or bounded
  continuation width while complete justification remains exact;
- a compositional refinement theorem that handles contract extension without
  replaying most history;
- a nontrivial lower/upper tradeoff matching state, query work, proof size, and
  fallback;
- independent replication on an adversarial dynamic benchmark showing flat
  answer and complete-justification quality across increasing horizons.

Until then, the candid verdict is: a real theorem was found in the toy algebra,
a stronger tempting theorem was decisively killed, semantic partitions were
separated from history machines, and one revision-aware fixed-ontology contract
now has an exact temporal-density phase law. The surviving foundational sliver
is a certified fast state over exact history. An adversarially selectable single
past boundary already collapses that state to identity, so broad ontologies,
evolving queries, and low fallback frequency remain the decisive tests for a
general theory of lifelong context.
