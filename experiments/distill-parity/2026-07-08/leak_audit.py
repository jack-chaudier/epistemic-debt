#!/usr/bin/env python3
"""G1 surface-leak audit (FROZEN gate, prereg d24e198): can a dumb classifier predict the
verdict from the DOCUMENT ALONE, policy-relevant numerics masked?

The domains.py confound guards were built against compaction, not against SGD mining surface
regularities over thousands of gradient steps. If a shallow model beats chance here, Student-V
can reach parity via the leak and the Delta separation is confounded. Gate: held-out AUC >= 0.60
(5-fold CV mean) => regenerate the pool with tightened draws (ONE attempt), else STOP.

Features (per the campaign brief): token unigrams+bigrams (hashed), document length, policy-
parameter sentence positions, and binned non-policy numeric values. Policy-relevant numerics
are replaced by a mask token before tokenization. The policy text is never shown.

Classifier: hashed logistic regression, plain SGD, stdlib only. Deterministic (seeded folds,
fixed init). Writes leak_audit_results.json; prints per-fold and mean AUC. Exit 0 always —
the gate decision is reported, not silently enforced.
"""
import json
import math
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
POOL = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else "train_pool.jsonl")
OUT = os.path.join(HERE, "leak_audit_results.json")

DIM = 1 << 18
FOLDS = 5
EPOCHS = 4
LR = 0.1
SEED = 812900
TOKEN_RE = re.compile(r"[a-z]+|\d+(?:\.\d+)?")


def h(feat):
    return hash(feat) % DIM


def features(item):
    doc = item["document"]
    # mask every policy-relevant numeric (the value strings the verdict depends on)
    for p in item["parameters"]:
        if p["policy"]:
            doc = doc.replace(str(p["value"]), " VALMASK ")
    toks = TOKEN_RE.findall(doc.lower())
    feats = {}
    for t in toks:
        if re.fullmatch(r"\d+(?:\.\d+)?", t):
            continue  # raw numbers enter via the binned features below only
        feats[h("u:" + t)] = feats.get(h("u:" + t), 0.0) + 1.0
    for a, b in zip(toks, toks[1:]):
        feats[h("b:" + a + "_" + b)] = feats.get(h("b:" + a + "_" + b), 0.0) + 1.0
    # document length (word-count bucket)
    feats[h(f"len:{item['word_count'] // 25}")] = 1.0
    # policy-parameter sentence positions (order/position features)
    sents = re.split(r"(?<=[.!?])\s+", doc)
    for k, p in enumerate(pp for pp in item["parameters"] if pp["policy"]):
        for si, s in enumerate(sents):
            if p["name"] in s:
                feats[h(f"pos:{k}:{si * 10 // max(1, len(sents))}")] = 1.0
                break
    # non-policy numerics, log-binned
    for p in item["parameters"]:
        if not p["policy"]:
            v = abs(float(p["value"])) + 1e-9
            feats[h(f"num:{int(math.log10(v) * 4)}")] = \
                feats.get(h(f"num:{int(math.log10(v) * 4)}"), 0.0) + 1.0
    # L2-normalize counts
    norm = math.sqrt(sum(v * v for v in feats.values())) or 1.0
    return {k: v / norm for k, v in feats.items()}


def auc(scores, labels):
    pairs = sorted(zip(scores, labels))
    ranks, i = {}, 0
    while i < len(pairs):
        j = i
        while j < len(pairs) and pairs[j][0] == pairs[i][0]:
            j += 1
        r = (i + j + 1) / 2.0
        for k in range(i, j):
            ranks[k] = r
        i = j
    pos = [ranks[k] for k, (_, y) in enumerate(pairs) if y == 1]
    n1, n0 = len(pos), len(pairs) - len(pos)
    if n1 == 0 or n0 == 0:
        return None
    return (sum(pos) - n1 * (n1 + 1) / 2.0) / (n1 * n0)


def train_fold(train, epochs=EPOCHS, lr=LR):
    w = [0.0] * DIM
    rng = random.Random(SEED + 1)
    idx = list(range(len(train)))
    for _ in range(epochs):
        rng.shuffle(idx)
        for i in idx:
            x, y = train[i]
            z = sum(w[k] * v for k, v in x.items())
            p = 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))
            g = p - y
            for k, v in x.items():
                w[k] -= lr * g * v
    return w


def main():
    items = [json.loads(l) for l in open(POOL)]
    rng = random.Random(SEED)
    order = list(range(len(items)))
    rng.shuffle(order)
    data = [(features(items[i]), 1 if items[i]["truth"] == "DENIED" else 0) for i in order]
    fold_auc = []
    for f in range(FOLDS):
        test = [d for i, d in enumerate(data) if i % FOLDS == f]
        train = [d for i, d in enumerate(data) if i % FOLDS != f]
        w = train_fold(train)
        scores = [sum(w[k] * v for k, v in x.items()) for x, _ in test]
        a = auc(scores, [y for _, y in test])
        fold_auc.append(round(a, 4))
        print(f"fold {f}: n_test={len(test)} AUC={a:.4f}")
    mean_auc = round(sum(fold_auc) / len(fold_auc), 4)
    verdict = "PASS (< 0.60)" if mean_auc < 0.60 else "GATE FIRED (>= 0.60) — regenerate or STOP"
    result = dict(pool=os.path.basename(POOL), n=len(items), folds=fold_auc,
                  mean_auc=mean_auc, gate_threshold=0.60, verdict=verdict,
                  dim=DIM, epochs=EPOCHS, lr=LR, seed=SEED)
    json.dump(result, open(OUT, "w"), indent=1)
    print(f"\nG1 mean AUC = {mean_auc}  ->  {verdict}")
    print(f"wrote {os.path.basename(OUT)}")


if __name__ == "__main__":
    main()
