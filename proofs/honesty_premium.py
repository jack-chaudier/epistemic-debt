#!/usr/bin/env python3
"""Honesty premium + retrofit gap: reproduce the Appendix A.2 headline numbers in-repo.

honesty_tax.py measures the tax on the *forced-optimal* layout (retrofitting abstention
onto answer-optimized memory). It does NOT compute the honesty *premium* — the accuracy
sacrificed by the *breach-optimal* layout, i.e. memory designed for honesty from the
start. That number (0.47x the debt on causal_referee @ 2 bits; retrofit gap ~38x) is
quoted in README row 3 / RESULTS / theory Appendix A.2 but was, until now, only derivable
from the unused breach frontier in exact_pareto_frontier. This script closes that gap:
the premium is the breach-optimal answer mass C* = solve_frontier(model,'breach').best_answer.

  premium(bits)     = A_f(forced-opt, bits) - C*(breach-opt, bits)
  retrofit_gap      = tax(forced-opt) / premium(breach-opt), matched where each is worst

Exit code 0 iff the reproduced constants match the recorded values to tolerance.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
import exact_pareto_frontier as epf
from honesty_tax import forced_optimal_partition, evaluate


def premium_table(model):
    """Return per-bit rows: A_f, J, D, tax, C_star, premium, tax/D, premium/D."""
    n = len(model.rows)
    breach_summ = epf.summarize_frontier(model, epf.solve_frontier(model, 'breach'))
    rows = []
    for bits in range(0, math.ceil(math.log2(n)) + 1):
        limit = min(1 << bits, n)
        A_f, J, C = evaluate(model, forced_optimal_partition(model, limit)[2])
        D, tax = A_f - J, J - C
        C_star = breach_summ[bits].best_answer
        rows.append(dict(bits=bits, A_f=A_f, J=J, D=D, tax=tax, C=C,
                         C_star=C_star, premium=A_f - C_star,
                         tax_over_D=(tax / D if D > 1e-12 else None),
                         premium_over_D=((A_f - C_star) / D if D > 1e-12 else None)))
    return rows


def main():
    models = [
        epf.build_probe_joint_model(3, 2),
        epf.build_probe_joint_model(4, 2),
        epf.build_probe_joint_model(5, 3),
        epf.build_dataset_support_model(epf.build_causal_referee_spec()),
    ]
    tables = {}
    print(f"{'model':16}{'bits':>5}{'A_f':>8}{'D':>8}{'tax':>8}{'tax/D':>8}"
          f"{'C*':>8}{'premium':>9}{'prem/D':>8}")
    for model in models:
        rows = premium_table(model)
        tables[model.label] = rows
        for r in rows:
            td = f"{r['tax_over_D']:8.2f}" if r['tax_over_D'] is not None else f"{'--':>8}"
            pd = f"{r['premium_over_D']:8.3f}" if r['premium_over_D'] is not None else f"{'--':>8}"
            print(f"{model.label:16}{r['bits']:>5}{r['A_f']:8.4f}{r['D']:8.4f}"
                  f"{r['tax']:8.4f}{td}{r['C_star']:8.4f}{r['premium']:9.4f}{pd}")
        print()

    # Reproduce the recorded causal_referee constants (theory Appendix A.2).
    ref = tables['causal_referee']
    at2 = next(r for r in ref if r['bits'] == 2)
    at3 = next(r for r in ref if r['bits'] == 3)
    tax_worst = at3['tax_over_D']            # 18.01x (forced layout, 3 bits)
    premium_best = at2['premium_over_D']     # 0.47x (breach layout, 2 bits)
    retrofit_gap = tax_worst / premium_best
    print(f"causal_referee: C*@2bits={at2['C_star']:.3f} premium@2bits={at2['premium_over_D']:.3f}xD "
          f"tax@3bits={tax_worst:.2f}xD  retrofit_gap={retrofit_gap:.1f}x")

    checks = [
        ('C*@2 == 0.832', abs(at2['C_star'] - 0.8317) < 2e-3),
        ('premium@2 == 0.47xD', abs(at2['premium_over_D'] - 0.469) < 5e-3),
        ('tax@3 == 18.01xD', abs(tax_worst - 18.01) < 0.1),
        ('retrofit gap ~38x', 36.0 < retrofit_gap < 40.0),
        ('premium<D exists (honesty cheaper than debt)',
         any(r['premium_over_D'] is not None and r['premium_over_D'] < 1.0 for r in ref)),
        ('premium/D > 1 on every synthetic family at every budget (dichotomy)',
         all(r['premium_over_D'] is None or r['premium_over_D'] > 1.0
             for label, rows in tables.items() if label != 'causal_referee' for r in rows)),
    ]
    ok = all(passed for _, passed in checks)
    for name, passed in checks:
        print(f"  [{'ok' if passed else 'FAIL'}] {name}")
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
