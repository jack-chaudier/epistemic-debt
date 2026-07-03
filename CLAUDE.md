# justification-gap — agent workflow

Research repo: exact theory + LLM experiments on the answer/justification gap under memory pressure. Read `README.md` for the results table, `theory/justification-gap-program.md` for the program (laws, conjectures, theorem targets).

## Ground rules

- **Evidence labels are load-bearing.** Every claim in `results/RESULTS.md` and the theory doc carries one of: `THEOREM` (proved), `EXACT` (exhaustive computation), `PREREGISTERED` (predictions fixed before the run, pass/fail reported), `OBSERVED` (pattern, not yet confirmatory), `REFUTED`, `CONJECTURE`. Never upgrade a label without the corresponding evidence. Refutations are results — record them, don't bury them.
- **Preregister confirmatory runs.** Fix predictions (with thresholds) in the run spec before spending API calls; report each as pass/fail even when failure is awkward. Exploratory runs are fine but must be labeled exploratory.
- **Secrets:** API keys come from the environment (`XAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) or a file outside the repo. Never write a key into code, logs, artifacts, or reports. `tests/test_experiment_artifacts.py::test_no_api_key_material_anywhere` enforces this — keep it passing. No `.env` files in the tree.
- **Determinism:** runners use seeded `random.Random`, temperature 0, an idempotent response cache keyed by (item, call-type), and a hard call cap. Re-running a completed experiment must be a no-op.
- **Costs:** log token usage from every response; report cumulative cost in every experiment writeup.

## Where things go

- New experiment campaign → `experiments/<name>/<date>/`; protocol iterations as `v1/, v2/ ...` each with `runner*.py`, `items.jsonl`, `responses_raw.jsonl`, `scored.csv`, a short `README.md` (design, confounds found, verdict), and `*_results.json` for confirmatory runs.
- New exact verification → `proofs/` (stdlib-only, self-contained, exit code 0 iff verified) + a regression test in `tests/`.
- Every finding → one row in `results/RESULTS.md` with status label and artifact link; substantive interpretation → an appendix in the theory doc.

## Workflow

```bash
python3 -m pytest tests/ -q        # must pass before and after your change
python3 proofs/shelf_width_law.py  # exact checks are cheap — run them
```

For multi-step work (new experiment design, multi-model replication), plan the design first — item generation is where validity lives; the three pilot confounds documented in theory-doc Appendix B (salience leak, verdict leak, metric confound) are the checklist. Smoke-test 3 items end-to-end and inspect raw outputs before spending the full call budget.

## Style

Python stdlib only in runners and proofs (no pip dependencies). Match existing code. Small, focused diffs. Commit only when asked.
