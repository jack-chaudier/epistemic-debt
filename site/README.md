# site/ — living research note

Single self-contained `index.html` (no build step, no dependencies, light/dark themes).
Two views, hash-routed: **Evidence ledger** (findings, default) and **Road to durable
context** (`#road` — prospectus). The road defines “infinite context” as an operational,
finite-horizon destination: bounded active state over growing versioned evidence, with no
silent unsupported assertions. It must never present an unbuilt stage as a result.

## Updating

- **Findings** — copy one `<article class="finding">` block in section 1. Labels:
  `exact` | `prereg` | `refuted` | `observed`. Keep the copy honest to the evidence
  label in `results/RESULTS.md`.
- **Numbers strip** — track the README result count and verified public scope.
- **Figures** — plot recorded values, identify sample/model/horizon in the caption, and add
  a mobile data table. Never draw an unmeasured extension as an observed line.
- **Road** — attach an evidence status to every mechanism or stage. `results/RESULTS.md`
  remains authoritative.

## Deploying to Vercel

The GitHub-linked Vercel project deploys `main` automatically with root directory `site/`.
For a manual fallback:

```bash
cd site && vercel --prod
```

or in the Vercel dashboard: import the repo, set **Root Directory** to `site`,
framework preset **Other** (no build command, output directory `.`).
