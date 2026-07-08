#!/usr/bin/env python3
"""Assemble sources.jsonl + SOURCES.md from the harvested NTSB Analysis narratives.

Reads a keepers directory (produced by the corpus harvest): `<accident>.txt` files holding the
verbatim Analysis-section prose plus a `manifest.jsonl` of {accident, report_id, url, words}.
Cleans pdftotext line-break hyphenation artifacts (real prose only — no content edits), caps to
N_SOURCES, and writes sources.jsonl (id, url, text) + a human-readable SOURCES.md provenance table.

All source texts are US National Transportation Safety Board aviation-accident final-report Analysis
sections — works of the US federal government, in the public domain. Usage:
    python3 build_sources.py <keepers_dir>
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
N_SOURCES = 12


def clean(text):
    # join hyphenated line-break artifacts ("engine- driven" -> "engine-driven"); leave real hyphens.
    text = re.sub(r"(\w)-\s+(\w)", r"\1-\2", text)
    return re.sub(r"\s+", " ", text).strip()


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: build_sources.py <keepers_dir>")
    kd = sys.argv[1]
    manifest = [json.loads(l) for l in open(os.path.join(kd, "manifest.jsonl")) if l.strip()]
    manifest.sort(key=lambda m: m["accident"])
    sources, md = [], []
    for m in manifest:
        txt = clean(open(os.path.join(kd, f"{m['accident']}.txt")).read())
        wc = len(txt.split())
        if not (300 <= wc <= 800):
            continue
        sources.append(dict(id=m["accident"], url=m["url"], text=txt))
        md.append((m["accident"], m["report_id"], wc, m["url"]))
        if len(sources) >= N_SOURCES:
            break
    with open(os.path.join(HERE, "sources.jsonl"), "w") as f:
        for s in sources:
            f.write(json.dumps(s) + "\n")
    with open(os.path.join(HERE, "SOURCES.md"), "w") as f:
        f.write("# Corpus provenance — real-document tier (2026-07-08)\n\n")
        f.write("All source texts are the **Analysis** sections of US National Transportation Safety "
                "Board *Aviation Investigation Final Reports*. As works of the US federal government "
                "they are in the **public domain** (17 U.S.C. §105). Retrieved 2026-07-08 from the "
                "NTSB CAROL report generator (`data.ntsb.gov`). Only the verbatim Analysis prose is "
                "used; injected policy readings are added by `gen_items.py` (see its docstring).\n\n")
        f.write(f"{len(sources)} distinct narratives, {min(w for _,_,w,_ in md)}–"
                f"{max(w for _,_,w,_ in md)} words each.\n\n")
        f.write("| # | Accident number | Report id | Words | Source URL |\n")
        f.write("|---|---|---|---|---|\n")
        for i, (an, rid, wc, url) in enumerate(md, 1):
            f.write(f"| {i} | {an} | {rid} | {wc} | {url} |\n")
    print(f"wrote sources.jsonl ({len(sources)}) + SOURCES.md")
    for an, rid, wc, _ in md:
        print(f"  {an:12s} {wc}w  (id {rid})")


if __name__ == "__main__":
    main()
