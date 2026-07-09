# Third-party and public-domain notices

The repository is published as a reproducible research record. The project license applies
only to material that Jack Gaffney has the right to license.

## Benchmark material

- GSM8K-derived items in
  `experiments/distill-parity/2026-07-08/capability_items.jsonl` and
  `experiments/forced-cot/2026-07-09/capability_items.jsonl` originate from
  [OpenAI's grade-school-math repository](https://github.com/openai/grade-school-math),
  Copyright © 2021 OpenAI, licensed under MIT. The complete permission notice is retained
  in [`LICENSES/MIT-GSM8K.txt`](LICENSES/MIT-GSM8K.txt).
- MMLU-derived items in those capability files originate from
  [hendrycks/test](https://github.com/hendrycks/test), distributed under MIT with
  Copyright © 2020 Dan Hendrycks; underlying question-source rights may vary. The complete
  permission notice is retained in [`LICENSES/MIT-MMLU.txt`](LICENSES/MIT-MMLU.txt).

## Vendored exact-model modules

`proofs/vendor/**` contains pinned modules from `jack-chaudier/stark`, Copyright © 2026
Jack Gaffney, retained under the MIT license in
[`LICENSES/MIT-STARK.txt`](LICENSES/MIT-STARK.txt). The copies are patched only to use
local imports so the exact checks remain self-contained.

## NTSB source material

The source narratives in `experiments/realdoc/2026-07-08/sources/**`, source-text fields in
`sources.jsonl`, and embedded NTSB prose in that experiment's `items.jsonl` are works of the
United States National Transportation Safety Board and are public domain in the United
States under 17 U.S.C. § 105. No ownership is claimed over that prose. The project's
selection, arrangement, injected policy readings, annotations, and original analysis are
licensed as described in [LICENSING.md](LICENSING.md).

## Recursive Language Models

The constrained RLM harness acknowledges
[Recursive Language Models](https://arxiv.org/abs/2512.24601) by Alex L. Zhang, Tim Kraska,
and Omar Khattab, and the MIT-licensed
[`alexzhang13/rlm-minimal`](https://github.com/alexzhang13/rlm-minimal) reference
implementation. The local `rlm_loop.py` is an independent constrained-grammar
implementation; no upstream source file is vendored here.

## Model and provider outputs

Raw LLM responses and provider logs are retained to make scoring and audits reproducible.
They are not covered by the project's blanket Apache-2.0 or CC-BY-4.0 grants. Their reuse may
be governed by the relevant provider, model, dataset, and source-material terms.
