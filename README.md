# FloodLens — Sri Lanka Flood & Extreme-Weather Analytics

FloodLens is a transparent web dashboard for exploring historical rainfall, weather, and modelled river-discharge conditions across Sri Lanka. It combines a reproducible Python data pipeline with a lightweight React/JavaScript interface and static deployment on Vercel.

The project is designed as a screening and exploration tool. It does not produce a calibrated flood probability, replace official warnings, or represent district-wide inundation. All results are based on documented provider data, representative reference points, and explicit analytical rules.

## Highlights

- Historical daily archive for 25 Sri Lankan district reference points.
- Weather data from Open-Meteo Historical Weather and modelled river discharge from the Open-Meteo Flood API/GloFAS.
- Current conditions and 16-day provider forecasts.
- Exploratory analysis including distributions, summary statistics, correlations, monsoon comparisons, annual rates, scatter plots, seasonality heatmaps, and extreme-condition calendars.
- Transparent rainfall accumulation, seasonal percentile, severity, episode, and screening-score calculations.
- Interactive Leaflet/OpenStreetMap district map with a geographic fallback.
- CSV exports for historical and forecast data.
- Automated daily refresh through GitHub Actions, with validation before publication.
- Static Vercel deployment with no long-running backend server.

## Architecture

```text
Open-Meteo APIs
      │
      ▼
Python ingestion and validation pipeline
      │  staged release; quality checks; audit evidence
      ▼
Versioned JSON/CSV data in public/data/
      │
      ├── React and JavaScript browser application
      │
      └── esbuild production bundle
                    │
                    ▼
                 Vercel / dist/
```

The pipeline stages a new release in a temporary directory, recalculates derived analytics, validates the complete release, and promotes it only after all checks pass. If a refresh fails, the previous published data remains intact.

## Data and analytical approach

The collector requests hourly weather data and daily river discharge, then converts the weather observations into daily records:

| Field | Unit | Description |
| --- | --- | --- |
| `rain` | mm | Daily precipitation total |
| `temp` | °C | Mean daily temperature |
| `humidity` | % | Mean relative humidity |
| `wind` | km/h | Maximum wind speed |
| `pressure` | hPa | Mean sea-level pressure |
| `tmax` | °C | Maximum temperature |
| `q` | m³/s | Modelled river discharge |
| `r3`, `r7` | mm | Three-day and seven-day rainfall totals |
| `qp`, `rp`, `tp`, `wp` | percentile | Seasonal retrospective percentile fields |
| `severity` | class | Typical, elevated, unusual, or unavailable |

Data-quality rules are intentionally conservative:

- Duplicate timestamps are removed deterministically.
- Values outside physical limits are treated as missing.
- Daily weather fields require a complete set of valid hourly observations.
- Missing values remain missing; they are never silently replaced with zero.
- Historical percentiles are calculated by calendar month to account for seasonality.
- Percentiles are analytical screening thresholds, not official warning levels or return periods.
- The screening score is an interpretable 0–100 ranking aid, not a calibrated probability.

Detailed definitions are documented in [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md), while the complete data contract and operational notes are in [`docs/HANDOVER.md`](docs/HANDOVER.md).

## Repository structure

| Path | Responsibility |
| --- | --- |
| `src/` | Frontend source, routes, React views, charts, analytics helpers, API cache, and styles. |
| `src/pages/Analysis.jsx` | Exploratory analysis page and chart panels. |
| `src/pages/Explorer.jsx` | Location search, coordinates, and forecast explorer. |
| `src/components/` | Reusable chart and time-series components. |
| `src/lib/` | Shared browser analytics, API, and page-guide utilities. |
| `public/data/` | Versioned browser data release consumed by the application. |
| `pipeline/config.py` | Shared paths, date policy, field names, and data schema. |
| `pipeline/provider.py` | HTTP client, retries, gzip cache, quota guard, and request audit log. |
| `pipeline/update.py` | Collection, staging, forecast refresh, promotion, and end-to-end data update. |
| `pipeline/analyze.py` | Rolling rainfall, seasonal percentiles, severity, lag relationships, and episodes. |
| `pipeline/eda.py` | Descriptive statistics, histograms, correlations, summaries, and screening ranking. |
| `pipeline/validate.py` | Independent release validation and `validation.json` generation. |
| `pipeline/report.py` | Generated release factsheet. |
| `tests/` | Python pipeline tests and Node/jsdom frontend tests. |
| `scripts/build.mjs` | Copies deployable assets and bundles the frontend with esbuild. |
| `.github/workflows/daily-data.yml` | Scheduled/manual collection, validation, persistence, and optional redeployment. |
| `docs/` | Methodology, deployment, testing, contribution, and handover documentation. |
| `dist/` | Generated production output; do not edit manually. |

## Requirements

- Python 3.10 or newer
- Node.js 18 or newer
- npm
- Internet access for live API collection and geocoding

Python dependencies are listed in [`requirements.txt`](requirements.txt). JavaScript dependencies and scripts are defined in [`package.json`](package.json).

## Quick start

Install dependencies, build the site, run the tests, and start the local server:

```bash
npm ci
python -m pip install -r requirements.txt
npm run build
npm test
python serve.py
```

Open [http://localhost:8000](http://localhost:8000) in a browser.

On Windows, [`START_WINDOWS.bat`](START_WINDOWS.bat) can be used as a convenience launcher after dependencies have been installed.

## Common commands

| Command | Purpose |
| --- | --- |
| `npm run build` | Bundle the application into `dist/`. |
| `npm test` | Build the site and run the Node/jsdom test suite. |
| `npm run check` | Syntax-check the main JavaScript controller. |
| `python -m unittest discover -s tests -p '*_test.py'` | Run Python ingestion and analytical tests. |
| `python pipeline/update.py --offline` | Rebuild analytics from saved data without network requests. |
| `python pipeline/update.py` | Collect recent provider data and publish a validated release. |
| `python pipeline/report.py` | Generate the release factsheet in `docs/REPORT.md`. |
| `python serve.py` | Serve the built static site locally. |

The offline update is the safest way to verify the complete data-processing path locally. A live update makes provider requests and can take several minutes because requests are deliberately rate-limited and serialized.

## Storage model

The browser reads the published release from `public/data/`:

- `<location-id>.json` — daily records for one reference point.
- `historical-daily.csv` — combined historical archive for download and analysis.
- `current.json` — current conditions and 16-day forecast snapshots.
- `forecast-daily.csv` — forecast values with separate weather and flood retrieval times.
- `summary.json` — release metadata, coverage, locations, provenance, and counts.
- `baselines.json` — monthly percentile thresholds.
- `lags.json` — rainfall/discharge lag correlations and paired counts.
- `eda.json` — statistics and chart-ready exploratory-analysis data.
- `validation.json` — results from the independent release validator.
- `districts.geojson` — district boundary geometry used by the map.

Transient and audit data is kept under `data/`, including provider response cache files, request logs, refresh reports, snapshots, and the latest refresh status. `data/refresh.lock` is a runtime lock and must not be committed.

## Automated refresh and deployment

The GitHub Actions workflow in [`.github/workflows/daily-data.yml`](.github/workflows/daily-data.yml) runs daily at 01:35 UTC and can also be started manually. It:

1. Installs Python and Node dependencies.
2. Runs the Python safeguard tests.
3. Collects recent weather, discharge, and forecast data into a staged directory.
4. Recalculates analytics and runs independent validation.
5. Generates the release report and builds/tests the website.
6. Commits the validated `public/data/` release and evidence files.
7. Optionally triggers Vercel through the `VERCEL_DEPLOY_HOOK` secret.

Vercel uses the settings in [`vercel.json`](vercel.json):

```text
Install command: npm ci
Build command:   npm run build
Output directory: dist
```

The Vercel deployment is static. The Python collector runs in GitHub Actions, and the Git repository is the durable store for published releases.

## Testing strategy

The project uses both numerical pipeline tests and frontend integration tests:

- `tests/pipeline_test.py` checks aggregation, percentile ties, rolling windows, score weighting, timestamps, provider safeguards, and release promotion.
- `tests/core.test.mjs` checks null-safe statistics, thresholds, forecast alignment, episode grouping, ordinal formatting, and chart transformations.
- `tests/react.test.mjs` checks route rendering, filters, exports, map fallback, forecast transitions, missing values, and weather-only locations.

Run the complete verification suite with:

```bash
python -m unittest discover -s tests -p '*_test.py'
npm test
```

## Limitations and responsible use

- Reference points are model grid locations, not weather stations, district averages, or inundation polygons.
- River discharge is modelled and may be unavailable for some locations.
- Retrospective percentiles can change when new archive data is added.
- Forecast spread is a provider ensemble range, not a calibrated confidence interval.
- The screening score is not a probability, risk assessment, or official warning.
- FloodLens should not be used as a substitute for national meteorological or disaster-management alerts.

## Documentation

- [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) — data sources, transformations, thresholds, scores, and interpretation.
- [`docs/HANDOVER.md`](docs/HANDOVER.md) — full architecture, data contract, storage, API logic, and operational notes.
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — deployment and hosting instructions.
- [`docs/TESTING.md`](docs/TESTING.md) — test coverage and reproducibility commands.
- [`docs/CONTRIBUTIONS.md`](docs/CONTRIBUTIONS.md) — contributor evidence and project record.
- [`docs/REPORT.md`](docs/REPORT.md) — generated factsheet for the current release.

## Contributing

1. Create a branch for the change.
2. Keep ingestion, analytical, and UI changes documented in the relevant source or `docs/` file.
3. Run the Python tests, `npm test`, and an offline pipeline rebuild when changing data logic.
4. Do not commit secrets, provider credentials, `data/refresh.lock`, or generated temporary files.
5. Open a pull request describing the change, validation performed, and any effect on the published data contract.

## License

See [`LICENSE`](LICENSE) for the project license and usage terms.
