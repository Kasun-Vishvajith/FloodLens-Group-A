# FloodLens Sri Lanka

FloodLens is a deployable dashboard for DS 4004 Option 3: flood and extreme-weather analytics for Sri Lanka. It combines Open-Meteo weather, GloFAS modelled river discharge, a real district boundary map, exploratory data analysis (EDA), historical episode replay, and a provider forecast view.

The product is deliberately a transparent **screening and exploration tool**. It does not train a machine-learning flood model, claim a flood probability, or replace an official warning service. Forecast values are fetched from the provider APIs; FloodLens adds data quality checks, daily aggregation, retrospective percentiles, indicators, charts, and exports.

## What is included

- 25 Sri Lankan district reference points with a real geoBoundaries district GeoJSON map and Leaflet/OpenStreetMap rendering.
- Historical archive from **2016-01-01 through 2026-09-15** in the bundled release (the daily workflow extends it after each successful run).
- Overview, current/16-day forecast, historical explorer, flood indicators, event replay, exploratory analysis, global location explorer, and methods pages.
- EDA: distributions, summary statistics, Pearson correlation matrix with paired-day counts, monsoon comparison, annual rates, screening-score ranking, rainfall/discharge scatter, seasonality heatmap, and extreme-condition calendar.
- CSV export for selected history and provider forecasts.
- Automatic 15-minute browser cache for live location searches, plus a daily GitHub Actions collector that persists validated data in the repository and optionally triggers Vercel.

## Quick start

```bash
npm ci
npm run build
npm test
python serve.py
```

Open `http://localhost:8000`. Python 3.10+ and Node 18+ are sufficient; Node 22 is used by the workflow. `npm test` rebuilds first, then runs numerical and DOM integration tests.

## Project layout

| Path | Purpose |
| --- | --- |
| `src/` | Source frontend: controller, React EDA/explorer views, charts, analytics helpers, API cache, and CSS. |
| `public/data/` | Versioned compact release consumed by the browser. JSON is used for location data and EDA; CSV is provided for downloads. |
| `pipeline/` | Python collection, caching, aggregation, analytics, EDA, validation, reporting, and optional local Spark check. |
| `tests/` | Python pipeline tests and Node/jsdom frontend tests. |
| `scripts/build.mjs` | Copies `public/` to `dist/` and bundles the frontend with esbuild. |
| `dist/` | Generated Vercel/static output. |
| `.github/workflows/daily-data.yml` | Scheduled/manual refresh, validation, commit, and optional Vercel deploy hook. |
| `docs/` | Methodology, deployment, testing, contribution and handover material. |

## Daily update model

Vercel serves the static `dist/` output. It is not used as a long-running Python process. GitHub Actions runs `pipeline/update.py` once per day, stages a temporary copy, requests only the recent missing/recently revised days, refreshes the 16-day provider snapshots, runs `analyze.py`, `eda.py`, and `validate.py`, and promotes the staged directory only after every check passes. The workflow commits `public/data/` and evidence files, then calls `VERCEL_DEPLOY_HOOK` when that secret is configured. A failed run leaves the previous published release intact.

See [`docs/HANDOVER.md`](docs/HANDOVER.md) for the complete data contract, API request logic, analytical definitions, storage, run instructions, API-call accounting, known limitations and contribution record.
