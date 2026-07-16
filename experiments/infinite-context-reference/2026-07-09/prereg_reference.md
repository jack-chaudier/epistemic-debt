# Post-smoke design checks — exact reference benchmark

**Evidence status:** implementation assertions for a deterministic exact
benchmark, revised after adversarial code review and frozen only for the final
canonical artifact generation.  The first draft compared heterogeneous
“active units”; that invalid comparison was removed in favor of canonical byte
encodings and separately charged event/index operations. The byte comparison
is explicitly an **IMPLEMENTATION ARTIFACT** of fixed JSON encodings, not an
information-theoretic state bound. These checks are
**not** a preregistered empirical result and must not be reported with the
repository's `PREREGISTERED` evidence label.

## Fixed workload and contract

- 50 immutable versioned events.
- Three declared sources.
- Additions, revisions, retractions, contradictions, one source-version
  invalidation, delayed-relevance keys, and exact wording.
- Fixed status/exact-source query schema with `launch` and `bridge` in the
  initially compiled key set.
- Causal complete-frontier checkpoints at boundaries 8 and 18.
- Twelve fixed queries, including a recent boundary, an unretained old
  boundary, a repeated new-key query, an exact-wording query, and a key absent
  from the complete source universe.
- Rolling exact window width 6.
- Stable-key index writes are charged once per event.

## Fixed success conditions

Every strategy must report:

1. zero answer error against exact replay;
2. zero complete-justification error against exact replay;
3. zero unsupported assertions after the assertion gate;
4. all event reads, index-entry reads, fallbacks, proof bytes, index writes,
   declared logical update work, cached-entry refinement writes, active bytes,
   and auxiliary-index bytes under the operation model below.

The operation model counts materialized archive event records, posting-list
directory/search/returned entries, online posting insertions, logical
event/frontier operations, and cached frontier-entry writes. It does not count
CPU instructions, hashing, allocations, serialization work, wall time, or
cryptographic verification.

The counterexample-refined strategy must additionally satisfy:

- at most 6 exact fallbacks;
- at most 30 query-time archive-event reads through the stable-key index;
- at most 40 total archive-event reads including update-time invalidation
  repair;
- at most 60 query-time and 80 total index-entry reads, counting both search
  probes and every returned posting entry;
- final active-plus-index canonical JSON bytes at least one third below the
  exact canonical archive JSON bytes (implementation encoding only).

The rolling-window strategy must finish below exact archive bytes and must
fall back for every requested boundary older than its retained base unless a
causal checkpoint covers it.

## Failure policy

The runner exits nonzero on any failed bound.  A failed condition remains a
result; the bound may not be edited in the generated JSON.  Any later protocol
change requires a new versioned directory.

## Trust boundary

The executable treats archive immutability/root identity, active-state
integrity, source-universe identity, and the stable-key posting directory's
completeness as exact trusted primitives.  It does not implement a
cryptographically binding dictionary.  The benchmark therefore tests semantic
exactness and resource accounting relative to those primitives, not
cryptographic soundness. New-key obligations under the fixed schema are
activated after ingestion; query-language extensions and continued updates
after activation are outside the fixed workload.
