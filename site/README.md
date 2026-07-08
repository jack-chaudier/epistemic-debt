# site/ — splash page

Single self-contained `index.html` (no build step, no dependencies, light/dark themes).
Two views, hash-routed: **The Ledger** (findings, default) and **The Road to Infinite
Context** (`#road` — prospectus; mechanisms cite evidence, stages carry plans, and it must
never present an unproven stage as a result).

## Updating

Everything editable is marked with an `UPDATE` comment in `index.html`:

- **Findings** — copy one `<article class="finding">` block in section 2. Labels:
  `exact` | `prereg` | `refuted` | `observed`. Keep the copy honest to the evidence
  label in `results/RESULTS.md`.
- **Numbers strip** — the four figures under the abstract track the README results
  table and spend line.
- **Footer date** — bump `last updated` when findings change.

## Deploying to Vercel

Static deploy, root directory = `site/`:

```bash
cd site && vercel --prod
```

or in the Vercel dashboard: import the repo, set **Root Directory** to `site`,
framework preset **Other** (no build command, output directory `.`).
