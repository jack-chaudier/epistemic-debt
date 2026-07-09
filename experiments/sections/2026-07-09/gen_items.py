#!/usr/bin/env python3
"""Sections campaign corpus: surgical evidence ablation, both verdict sides, no compressor.

6 domains x 60 items (30/30), fresh seed family 814xxx. For each item the ABLATED document has
exactly one sentence removed — the one carrying the deciding reading:
  DENIED items:   the failing parameter's reading sentence;
  APPROVED items: one seeded-chosen policy parameter's reading sentence (recorded).
Perturbation arms on the first two domains: `shuffle` (seeded re-order of the ablated doc's
body sentences) — probe-wording perturbation lives in the runner, not here.

Selfcheck: ablated doc no longer retains the ablated value; control doc does; exactly one
sentence removed; all other policy values still uniquely retained. Deterministic, no LLM.
"""
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "experiments", "lib"))
import domains as D  # noqa: E402
sys.path.insert(0, os.path.join(REPO, "experiments", "grok-pilots", "2026-07-03", "v3"))
from runner3 import retained  # noqa: E402

SEED_BASE = 814100
ABLATE_SEED = 814900
SHUFFLE_SEED = 814950
N_PER_DOMAIN = 60
PERTURB_DOMAINS = D.DOMAIN_KEYS[:2]


def sentences(doc):
    """Split into (header, [body sentences], end) preserving reconstruction."""
    paras = doc.split("\n\n")
    header, end = paras[0], paras[-1]
    body = []
    for p in paras[1:-1]:
        body.extend(re.split(r"(?<=\.)\s+", p))
    return header, body, end


def rebuild(header, body, end, rng=None):
    body = list(body)
    if rng is not None:
        rng.shuffle(body)
    paras, k = [], 0
    r = random.Random(0xB0D7)  # fixed paragraphing; content order is what varies
    while k < len(body):
        step = r.choice([3, 4, 5])
        paras.append(" ".join(body[k:k + step]))
        k += step
    return header + "\n\n" + "\n\n".join(paras) + "\n\n" + end


def main():
    arng = random.Random(ABLATE_SEED)
    srng = random.Random(SHUFFLE_SEED)
    out, problems = [], []
    for idx, key in enumerate(D.DOMAIN_KEYS):
        items = D.gen_items(key, seed=SEED_BASE + idx, n=N_PER_DOMAIN)
        problems += D.selfcheck(items)
        for j, it in enumerate(items):
            pol = [p for p in it["parameters"] if p["policy"]]
            target = (next(p for p in pol if not p["passes"]) if it["truth"] == "DENIED"
                      else pol[arng.randrange(3)])
            header, body, end = sentences(it["document"])
            keep = [s for s in body if not retained(s, target["value"])]
            if len(body) - len(keep) != 1:
                problems.append((it["id"], "ablation-count", len(body) - len(keep)))
                continue
            abl = rebuild(header, keep, end)
            rec = dict(id=f"sec-{key}-{j:03d}", domain=key, truth=it["truth"],
                       failing_param=it["failing_param"], ablated_param=target["name"],
                       ablated_value=target["value"], policy_text=it["policy_text"],
                       parameters=it["parameters"], document=it["document"],
                       document_ablated=abl,
                       document_ablated_shuffled=(rebuild(header, keep, end, srng)
                                                  if key in PERTURB_DOMAINS else None))
            # selfcheck: ablated value gone, siblings intact
            if retained(abl, target["value"]):
                problems.append((rec["id"], "ablated-value-survives"))
            for p in pol:
                if p["name"] != target["name"] and not retained(abl, p["value"]):
                    problems.append((rec["id"], "sibling-lost", p["name"]))
            out.append(rec)
    if problems:
        print(f"SELFCHECK FAILED ({len(problems)}):")
        for p in problems[:20]:
            print("  ", p)
        sys.exit(1)
    with open(os.path.join(HERE, "items.jsonl"), "w") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    den = sum(r["truth"] == "DENIED" for r in out)
    print(f"wrote {len(out)} items ({den} DENIED); perturb subset: "
          f"{sum(1 for r in out if r['document_ablated_shuffled'])} items; selfcheck clean")


if __name__ == "__main__":
    main()
