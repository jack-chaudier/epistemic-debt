#!/usr/bin/env python3
"""Law 2 check: conservation of epistemic debt, with the honesty-tax refinement.

For each exact model, find the forced-optimal partition at each bucket budget
(the memory layout a behavior-optimizer would pick), then evaluate BOTH output
policies on that same partition:
  forced: majority answer; majority witness among answer-matching states
  breach: answer only when the bucket is jointly unanimous in that column

Quantities (probability mass, weighted by state weights x column multiplicity):
  A_f   forced answer accuracy
  J     jointly correct under forced (answer AND witness match majorities)
  D     epistemic debt = A_f - J   (right answer, wrong witness)
  C     breach credited mass (unanimous buckets)
  tax   J - C  (justified mass destroyed by abstention: entangled with debt)
Identity to verify:  A_f - C = D + tax  (accounting)  and measure tax/D.
Conservation (strict, rate 1) holds iff tax == 0.
"""
import math, sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
import exact_pareto_frontier as epf


def forced_optimal_partition(model, bucket_limit):
    """DP: maximize forced answer mass, tie-break witness mass; return blocks."""
    n = len(model.rows)
    scores = epf.cluster_scores(model, 'forced')  # (answer, witness) per subset mask

    @lru_cache(maxsize=None)
    def solve(mask, buckets):
        if mask == 0:
            return (0, 0, ()) if buckets == 0 else None
        if buckets == 0:
            return None
        anchor = mask & -mask
        best = None
        submask = mask
        while submask:
            if submask & anchor:
                rest = solve(mask ^ submask, buckets - 1)
                if rest is not None:
                    a, w = scores[submask]
                    cand = (rest[0] + a, rest[1] + w, rest[2] + (submask,))
                    if best is None or cand[:2] > best[:2]:
                        best = cand
            submask = (submask - 1) & mask
        return best

    full = (1 << n) - 1
    best = None
    for buckets in range(1, bucket_limit + 1):
        cand = solve(full, buckets)
        if cand is not None and (best is None or cand[:2] > best[:2]):
            best = cand
    return best  # (answer_mass, witness_mass, blocks)


def evaluate(model, blocks):
    """Compute A_f, J, C on a partition given as subset masks."""
    n = len(model.rows)
    cols = epf.compress_columns(model.rows)
    total = sum(model.state_weights) * sum(m for m, _ in cols)
    A_f = J = C = 0
    for mask in blocks:
        idx = [i for i in range(n) if mask & (1 << i)]
        for mult, sig in cols:
            outs = [sig[i] for i in idx]
            wts = [model.state_weights[i] for i in idx]
            # breach: unanimous joint output
            if len(set(outs)) == 1:
                C += sum(wts) * mult
            # forced: majority answer
            ac = Counter()
            for o, w in zip(outs, wts):
                ac[o.answer] += w
            pa = sorted(ac.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            am = sum(w for o, w in zip(outs, wts) if o.answer == pa)
            A_f += am * mult
            # majority witness among answer-matching
            wc = Counter()
            for o, w in zip(outs, wts):
                if o.answer == pa:
                    wc[o.witness] += w
            pw = sorted(wc.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if wc else ()
            J += sum(w for o, w in zip(outs, wts)
                     if o.answer == pa and o.witness == pw) * mult
    return A_f / total, J / total, C / total


def main():
    models = [
        epf.build_probe_joint_model(3, 2),
        epf.build_probe_joint_model(4, 2),
        epf.build_probe_joint_model(5, 3),
        epf.build_dataset_support_model(epf.build_causal_referee_spec()),
    ]
    print(f"{'model':16}{'bits':>5}{'A_f':>8}{'J':>8}{'D=A-J':>8}{'C':>8}"
          f"{'tax=J-C':>9}{'abst=1-C':>9}{'tax/D':>8}  identity")
    for model in models:
        n = len(model.rows)
        for bits in range(0, math.ceil(math.log2(n)) + 1):
            limit = min(1 << bits, n)
            res = forced_optimal_partition(model, limit)
            A_f, J, C = evaluate(model, res[2])
            D, tax = A_f - J, J - C
            ok = abs((A_f - C) - (D + tax)) < 1e-12
            ratio = f"{tax/D:8.2f}" if D > 1e-12 else f"{'--':>8}"
            print(f"{model.label:16}{bits:>5}{A_f:8.4f}{J:8.4f}{D:8.4f}{C:8.4f}"
                  f"{tax:9.4f}{1-C:9.4f}{ratio}  {'ok' if ok else 'FAIL'}")
        print()


if __name__ == '__main__':
    main()
