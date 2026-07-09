# Licensing and ownership

Copyright © 2026 Jack Gaffney.

Epistemic Debt is a mixed research-software repository. Jack Gaffney retains copyright in
the original work and grants reuse under the path-specific terms below. Research facts,
mathematical truths, and ideas are not themselves claimed as property.

## Original software — Apache-2.0

Original source code, tests, workflows, and tooling are licensed under the
[Apache License 2.0](LICENSE), SPDX identifier `Apache-2.0`. This includes original Python
outside `proofs/vendor/`, GitHub Actions workflows, and project configuration.

## Original research materials — CC BY 4.0

Original research prose, documentation, site text and figures, synthetic inputs, curated
tables, and aggregate result artifacts are licensed under the
[Creative Commons Attribution 4.0 International license](LICENSES/CC-BY-4.0.txt), SPDX
identifier `CC-BY-4.0`. Attribution should identify Jack Gaffney, name *Epistemic Debt*,
link the repository when practical, and indicate modifications.

This grant covers only copyright and database rights that Jack Gaffney controls. It does
not restrict independent use of the underlying facts, results, or ideas.

Within `site/`, original HTML, CSS, and JavaScript are Apache-2.0; original prose and
figures are CC BY 4.0.

## Exceptions and excluded material

- `proofs/vendor/**` retains its upstream MIT license and copyright notice in
  [`LICENSES/MIT-STARK.txt`](LICENSES/MIT-STARK.txt).
- Third-party benchmark material and United States government source texts retain their
  original license or public-domain status.
- Raw model responses and provider logs — including `responses_raw*.jsonl`,
  `judge_raw.jsonl`, `teacher_raw*.jsonl`, `base_capability_raw.jsonl`,
  `probe_j_raw.jsonl`, `run*.log`, and equivalent response caches — are published for
  reproducibility but are not relicensed by this repository. Provider terms and embedded
  third-party rights may apply.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for provenance and attribution.
An explicit license notice in an individual file overrides this scope map for that file.

## Contributions

Unless a contribution states otherwise and is accepted on that basis, contributions are
licensed under the terms applicable to the files they modify. Contributors retain their
own copyright; this repository does not require copyright assignment.
