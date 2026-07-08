#!/usr/bin/env python3
"""Minimal stdlib RLM loop (see prereg_rlm_audit.md §Harness).

Faithful to the essential mechanic of Recursive Language Models (arXiv 2512.24601;
github.com/alexzhang13/rlm-minimal): the long context lives OUTSIDE the root model's window as
addressable slices; the root iteratively issues sub-queries against slices; the sub-call *return*
(not the slice) re-enters the root's window; the root then answers.

Fidelity note (frozen in prereg): rlm-minimal exposes the context as a Python variable inside a
free-form REPL where the root writes `llm_query(...)` calls. We replace the arbitrary-code REPL
with a constrained action grammar (`QUERY <id>: <question>` / `DECISION:`+`PARAMETER:`). This
keeps the audited channel — the sub-call return — identical to the paper's while being
deterministic (temp 0), idempotent-cacheable, and safe (no code execution). The mechanic we price
is the return, not the REPL syntax; the grammar change does not touch it.

Two return regimes, matched word budget (the confound guard, row 30):
  - "vanilla": sub-reader returns a free-form answer (≤ W words).
  - "cert":    sub-reader returns the certificate contract (CLAIM/WITNESS/POINTER or NO_FINDING),
               and the root is contracted to cite the witness chain or name the missing value.

`run_rlm(api, item, condition, cfg)` drives one item. `api(call_name, messages) -> text` is the
caller's idempotent/cached/capped call primitive (keys are deterministic in condition+iter+slice,
so re-running replays identical keys). Returns a trace dict the scorer consumes.
"""
import re

MAX_ITERS = 6      # root turns per item
MAX_SUB = 8        # sub-calls per item (recursion breadth cap)
SUB_WORDS = 45     # matched sub-call return budget (both regimes)

# ── root system prompts ───────────────────────────────────────────────────────
_ROOT_COMMON = (
    "You are the ROOT of a recursive reading system. A large collection of documents is stored "
    "OUTSIDE your context as numbered slices; you CANNOT see their contents — only the manifest "
    "below (each slice's type and code). To read a slice you issue a sub-query; a sub-reader reads "
    "that slice and returns a short finding — the finding, NOT the slice, comes back to you.\n\n"
    "ACTIONS (write these literally, one per line):\n"
    "  QUERY <id>: <your question>   — read slice <id>; you may issue several in one turn.\n"
    "When (and only when) you have read the relevant slice and can decide, output your final "
    "answer as exactly two lines:\n"
    "  DECISION: APPROVED    (or DENIED)\n"
    "  PARAMETER: <name>     (the single failing policy parameter, or NONE if APPROVED)\n"
    "Do not guess a DECISION before a sub-reader has returned the relevant readings. The policy "
    "names the code of the one slice that matters; find it in the manifest and query it.")

_CERT_ROOT = (
    "\n\nThe sub-readers return CERTIFICATES: each finding carries a CLAIM, the verbatim WITNESS "
    "value(s), and a POINTER (or NO_FINDING). Base your DECISION and PARAMETER ONLY on values that "
    "came back inside a WITNESS. If a policy reading you need was never returned with its witness "
    "value, do NOT invent it: output PARAMETER: MISSING <name-of-the-value-you-lack> and decide "
    "conservatively. Before your two final lines, add one line CITE: <the witness values you "
    "used>.")

ROOT_SYS = {"vanilla": _ROOT_COMMON, "cert": _ROOT_COMMON + _CERT_ROOT}

# ── sub-reader system prompts (matched budget) ────────────────────────────────
SUB_SYS = {
    "vanilla": (
        "You are a sub-reader in a recursive reading system. Read the document below and answer the "
        f"root's question in at most {SUB_WORDS} words. Be direct; report what the document says."),
    "cert": (
        "You are a sub-reader in a recursive reading system. Read the document below and answer the "
        f"root's question in at most {SUB_WORDS} words, using ONLY this certificate format:\n"
        "CLAIM: <one-sentence finding>\n"
        "WITNESS: <the verbatim deciding value(s): name + number + unit>\n"
        "POINTER: <where in the document>\n"
        "If the document does not contain what was asked, reply exactly:\n"
        "NO_FINDING: <what you searched for, what was absent>"),
}

_QUERY_RE = re.compile(r"QUERY\s+(\d+)\s*:\s*(.+)", re.I)
_DECISION_RE = re.compile(r"DECISION\s*:\s*\**\s*(APPROVED|DENIED)", re.I)
# PARAMETER line: capture MISSING marker + name, or a plain name / NONE
_PARAM_RE = re.compile(r"PARAMETER\s*:\s*\**\s*([^\n*]+)", re.I)


def _manifest(item):
    lines = ["MANIFEST — slices available (contents hidden; query to read):"]
    for s in item["slices"]:
        lines.append(f"  [{s['slice_id']}] {s['header']}")
    return "\n".join(lines)


def parse_final(text, params, match_param):
    """(decision, parameter_label) from a root turn; parameter_label in the scorer's vocabulary."""
    dm = _DECISION_RE.search(text or "")
    decision = dm.group(1).upper() if dm else None
    pm = _PARAM_RE.findall(text or "")
    parameter = None
    if pm:
        raw = pm[-1].strip().rstrip(".")
        up = raw.upper()
        if up.startswith("NONE"):
            parameter = "NONE"
        elif "MISSING" in up or "INSUFFICIENT" in up:
            parameter = "MISSING"
        else:
            parameter = match_param(raw, params) or "UNMATCHED"
    return decision, parameter


def parse_queries(text):
    out = []
    for line in (text or "").splitlines():
        m = _QUERY_RE.match(line.strip())
        if m:
            out.append((int(m.group(1)), m.group(2).strip()))
    return out


def run_rlm(api, item, condition, match_param):
    """Drive one item through the RLM loop. `api(call, messages)->text` handles caching/cap.
    Returns dict(decision, parameter, subcalls[...], n_iters, gave_up, transcript)."""
    slices = item["slices"]
    task = (item["policy_text"] +
            "\n\nQuestion: Was the return-to-service/go decision APPROVED or DENIED per this "
            "policy, and if DENIED which single policy parameter's reading caused it?")
    transcript = [{"role": "system", "content": ROOT_SYS[condition]},
                  {"role": "user", "content": _manifest(item) + "\n\n" + task}]
    subcalls, n_sub, gave_up = [], 0, False
    decision, parameter, n_iters = None, None, 0
    for it_i in range(MAX_ITERS):
        n_iters = it_i + 1
        root_txt = api(f"{condition}_root_{it_i}", transcript)
        transcript.append({"role": "assistant", "content": root_txt})
        dec, par = parse_final(root_txt, item["parameters"], match_param)
        queries = parse_queries(root_txt)
        if dec is not None or par is not None:      # final answer wins
            decision, parameter = dec, par
            break
        if not queries:                             # no action, no answer → loop stalled
            gave_up = True
            break
        blocks = []
        for sid, question in queries:
            if n_sub >= MAX_SUB:
                blocks.append(f"[slice {sid}] sub-call budget exhausted; decide from what you have.")
                continue
            if not (0 <= sid < len(slices)):
                blocks.append(f"[slice {sid}] no such slice.")
                continue
            sub_msgs = [{"role": "system", "content": SUB_SYS[condition]},
                        {"role": "user", "content": "Document:\n" + slices[sid]["document"] +
                         "\n\nRoot's question: " + question}]
            ret = api(f"{condition}_sub_{it_i}_{sid}", sub_msgs)
            subcalls.append(dict(iter=it_i, slice_id=sid, is_relevant=(sid == item["relevant_slice"]),
                                 question=question, ret=ret, ret_words=len((ret or "").split())))
            blocks.append(f"[return from slice {sid}]\n{ret}")
            n_sub += 1
        transcript.append({"role": "user", "content": "\n\n".join(blocks) +
                           "\n\nContinue: issue more QUERY lines, or give your final DECISION and "
                           "PARAMETER lines now."})
    return dict(decision=decision, parameter=parameter, subcalls=subcalls,
                n_iters=n_iters, n_sub=n_sub, gave_up=gave_up)
