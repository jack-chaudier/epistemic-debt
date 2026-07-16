# Exact evolving-context reference benchmark

**Status: EXACT deterministic benchmark.  Cost: $0; no model calls.**

This directory implements the non-toy reference system justified by the
current mathematics.  It is an integration test, not evidence that the
architecture or its component data structures are novel.

## System

The workload uses an immutable versioned event archive, a fixed query schema
with an initially compiled key set, complete per-source frontiers, causal
checkpoints, a rolling exact
window, a stable-key posting index, a complete-certificate checker, an
assertion gate, exact fallback, query-triggered stable-key refinement, and a
declared logical-operation resource ledger.  The executable retains the historical strategy name
`counterexample_refined`, but this fixture is a demand cache, not a general
counterexample-guided abstraction-refinement learner.

The 50-event stream includes additions, repeated revisions, retractions,
contradictory sources, source-version invalidation, facts that become relevant
only after ingestion, exact wording, temporal obligations, and complete
negative evidence for a missing key. The delayed obligations add stable keys
under the fixed status/exact-source query schema; they do not extend the query
language. Twelve fixed queries exercise the fast path and its boundaries.

Run:

```bash
python3 experiments/infinite-context-reference/2026-07-09/runner.py
```

Canonical artifacts:

- `items.jsonl`: fixed event/query workload;
- `responses_raw.jsonl`: one exact strategy/query record per line;
- `scored.csv`: complete declared logical-counter ledger by strategy;
- `reference_results.json`: canonical report and design-bound verdicts;
- `prereg_reference.md`: frozen v1 design bounds and evidence limitation.

## Exact outcome

All eight strategies have zero answer error, zero complete-justification error,
and zero unsupported assertions because the compact strategies use exact
fallback when their retained state cannot support the claim. Five strategies
are maintained online event by event, two deliberately insufficient baselines
are batch-compiled by charged post-ingestion replay, and full replay retains no
active state.

The strongest structured strategy is `counterexample_refined`:

- 1,861 canonical active bytes plus 197 auxiliary index bytes, versus an
  8,147-byte canonical exact archive—an **IMPLEMENTATION ARTIFACT** of the
  fixed JSON encodings, not an information-theoretic or asymptotic bound;
- 5 fallbacks over 12 queries;
- 20 query-time and 8 update-time event reads;
- 43 query-time and 12 update-time index-entry reads, including every returned
  posting entry;
- 50 charged index writes;
- 24 charged refinement state writes;
- zero answer or justification error.

The rolling exact window retains 1,915 canonical active bytes, answers 8 of 12
queries locally, performs 25 update-time plus 36 query-time event reads, and
falls back on the four obligations outside its retained information.
Current-answer and one-witness strategies are small but cannot pass the
complete-certificate gate, so every query falls back.

The benchmark reports type-specific logical “active units” as diagnostics but
does not compare them across strategies. Event reads, index-entry reads, index
writes, active bytes, and auxiliary-index bytes are separately accounted. The
ledger is complete only for these declared logical counters: `update_work` is
logical frontier/event work and `refinement_work` is cached-entry writes. It
does not claim to count CPU instructions, hashing, allocation, serialization,
wall time, or cryptographic verification.

## Proof-carrying covers

The benchmark records both sides of the exact verdict:

- with shareable abstract proofs, the three-semantic-state fixture has a
  two-state proof-labelled closed cover;
- when proof identity is bound to source/version state as it is in this
  workload, the same overlap has empty proof intersections and the minimum is
  three.

This refutes collapse only for the abstract accepted-output relation. Whether
locally checkable proof protocols retain the overlap after proof bits, verifier
probes/work, archive dependence, and hidden path state are jointly charged
remains open. Semantic overlap also does not automatically survive provenance
binding.

## Boundary

The posting index is maintained at ingestion and its writes/storage are
charged.  Its completeness and the active state's integrity are trusted exact
primitives here.  No Merkle tree or signature scheme is implemented, so this
benchmark does not establish information-theoretic or cryptographic binding of
an untrusted archive. The gate is structural relative to a caller-supplied
trusted frontier, not an archive-bound completeness proof. It also does not
meet the evidentiary bar for a
`PREREGISTERED` positive result: the design bounds were frozen after
implementation smoke testing. All new-key obligations arrive after the event
stream under the already fixed query schema, so actual query-language
extension, continued ingestion after activation, and resulting proof
invalidation remain outside this fixture.
