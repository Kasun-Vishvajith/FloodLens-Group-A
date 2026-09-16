# FloodLens Group A — Project Handover

**Prepared:** 16 September 2026  
**Project:** FloodLens Sri Lanka — DS 4004, Option 3  
**Team listed in the project:** Kasun Vishvajith, Akindu Liyanage, Yasuri Fernando

## 1. Purpose and current status

FloodLens is a Sri Lankan flood and extreme-weather analytics dashboard. It combines historical weather data, modelled river discharge, transparent exploratory analytics, provider forecasts, district screening indicators, and a location explorer.

The product is intentionally **not** a trained flood-prediction model. Forecast values are supplied by Open-Meteo provider products. FloodLens adds the ingestion, quality checks, aggregation, EDA, percentile-based indicators, UI, exports, and deployment paths around those provider data.

The packaged data currently reports:

| Item | Current value |
|---|---:|
| Reference locations / districts | 25 |
| Historical start | 2016-01-01 |
| Latest completed historical day | 2026-09-15 |
| Data as-of date | 2026-09-16 |
| Hourly rows | 2,346,600 |
| Daily rows | 97,775 |
| Flood/discharge rows | 89,953 |
| Weather variables | Rain, temperature, humidity, wind, pressure |
| Unique weather grids | 25 |
| Missing hourly weather cells | 0 |
| Missing forecast flow locations | 2 |
| Detected analytical episodes | 870 |

The current dataset summary is in `dist/data/summary.json`; the latest validation result is in `dist/data/validation.json`.

## 2. Important handover note about file history

This folder is not a Git working tree: there is no usable `.git` directory at the project root. Therefore, an exact commit diff or a definitive list of files changed by a particular person/session cannot be reconstructed from Git metadata.

This document is an evidence-based implementation inventory. It describes the code and artifacts currently present, and uses the 16 September file timestamps and the project’s validation documents to identify the strongest recent revision area. It should be kept with the project if the repository is later placed under Git.

## 3. Application architecture

### Frontend

- `dist/index.html` is the static application shell.
- `dist/app.js` is the main application controller and existing historical-screen renderer.
- `dist/core.mjs` contains reusable analytical helpers such as null-safe statistics, severity levels, threshold comparison, episode grouping, and forecast signal handling.
- `frontend/react-ui.jsx` contains the newer React views.
- `dist/react-ui.js` is the generated production bundle from `frontend/react-ui.jsx`.
- `dist/interface.mjs` handles shared interface behavior that is independent of the main route renderer.
- `dist/style.css`, `dist/theme.css`, `dist/layout.css`, and `dist/apple.css` provide the visual system, responsive layout, and accessibility styles.
- `dist/data/` contains the packaged JSON/CSV data used by the static deployment.

The project uses an incremental React architecture. The original dashboard routes remain rendered by `dist/app.js`; the React bundle is mounted into the content area for the EDA and Global Explorer routes. `build.mjs` bundles the React source with esbuild.

### Optional backend

`backend/main.py` is a read-only FastAPI service. It can serve packaged data or query PostgreSQL when `DATABASE_URL` is configured. The frontend can use it by setting `apiBase` in `dist/config.js`; the current config deliberately has an empty API base, so the static edition remains deployable without a server.

### Data and cloud paths

- Python ingestion and transformations are under `pipeline/`.
- `data/raw/` stores compressed provider responses and quota metadata.
- `data/processed-v2/` stores processed daily/hourly outputs and SQLite materialization.
- `data/parquet/` stores typed, partitioned Parquet outputs for analytical/cloud workflows.
- `infra/` contains Terraform and PostgreSQL schema material.
- `docker-compose.yml` provides local PostgreSQL and FastAPI containers.
- Cloud execution is supplied as code/configuration but is not claimed as completed unless the team runs it in its own accounts.

## 4. UI routes and behavior

The navigation currently contains eight routes:

1. **Overview** — Sri Lankan district map, selected-date status, location ranking, rainfall summaries, and historical/forecast map modes.
2. **Current & forecast** — current weather, 16-day provider forecast, rainfall, temperature/wind, modelled river discharge, and forecast signal comparisons.
3. **Historical explorer** — daily charts and summary comparisons for rainfall, temperature, humidity, wind, and pressure; date filtering and CSV export.
4. **Flood indicators** — river discharge, 3-day/7-day rainfall accumulation, seasonal comparisons, lag indicators, and location comparison.
5. **Event replay** — algorithmically detected extreme episodes with event selection, slider scrubbing, play/pause replay, daily values, and supporting charts.
6. **EDA & district risk** — the React `Analysis` view described below.
7. **Global explorer** — the React `GlobalExplorer` view described below.
8. **Data, methods & project guide** — coverage, sources, limitations, processing, downloads, and project guidance.

### Shared filter and context changes

- A single collapsible **Location & dates** control is shared across the historical routes.
- The control includes district/reference location, start date, end date, Apply dates, and quick ranges: last 30 days, this year, and full archive.
- Route-specific filtering is applied: weather, events, and analysis hide irrelevant historical date controls; the explorer and project guide do not expose the district filter panel.
- Applying a location, date range, or quick range closes the filter disclosure and writes a short status message in the five-second update-feedback area.
- Invalid date ranges are rejected with an explanatory notice rather than changing the active state.
- The loaded archive date is checked when the tab regains focus, becomes visible, and periodically while open. If a newer archive is published, the UI shows an update notice and a Load latest data action.
- The UI keeps historical archive dates separate from forecast dates and retrieval timestamps.

### Overview/map changes

- The map uses real geoBoundaries district geometry and Leaflet/OpenStreetMap when available.
- There is a geographic SVG fallback so the dashboard still renders district geometry when Leaflet is unavailable.
- Monitoring points are selectable and preserve the selected location across routes.
- Historical mode colours points by sampled-location severity for the selected date. Forecast mode colours points by forecast signal.
- The UI explicitly says that point colours are not inundation polygons and that a reference point is not a district average or whole-basin measurement.

### React EDA view

`frontend/react-ui.jsx` implements the `Analysis` component and mounts it from `mountView()` when the route is `analysis`.

The view loads `dist/data/eda.json` in static mode or `/api/analysis` when a backend API base is set. It provides:

- selectable variables and null-safe distribution summaries;
- valid-day count, mean, median, standard deviation, and 95th percentile;
- histogram bars;
- Pearson correlation matrix with paired-record counts in tooltips;
- Southwest, Northeast, and inter-monsoon comparisons;
- annual unusual-day counts/rates with partial-year labels;
- district screening score bar chart;
- rainfall/discharge scatter plot on log axes;
- monthly seasonality heatmap for rainfall, discharge, or unusual-day rate;
- 2021-onward extreme-condition calendar heatmap;
- ranking table with score, score basis, elevation, latest date, and clickable location selection.

The view includes interpretation warnings: correlations are not causation, modelled discharge is not a gauge observation, and the screening index is not a flood probability or official warning.

### Global Explorer view

`frontend/react-ui.jsx` implements the `GlobalExplorer` component and mounts it for the `explore` route.

- Searches Sri Lanka by default through Open-Meteo geocoding.
- Supports a Global view toggle for worldwide place search.
- Accepts latitude/longitude manually with range validation.
- Supports browser GPS with a clear denied/unavailable fallback.
- Allows map clicks to populate coordinates.
- Loads weather, flood, and elevation results concurrently in static mode.
- Uses `/api/place` through FastAPI mode, where upstream requests are server-side.
- Uses a request version token so an older response cannot overwrite a newer location selection.
- Uses a 30-second request timeout and partial provider handling.
- Shows available data when one provider fails and retains missing values as dashes rather than converting them to zero.
- Aligns weather and flood forecast rows by UTC date.
- Displays current temperature, elevation, humidity, wind, daily rain, min/max temperature, max wind, median flow, and flow P25–P75 spread.

### Apple-style visual and responsive revision

The recent UI revision is represented primarily by `dist/apple.css`, `dist/layout.css`, `dist/interface.mjs`, and the regenerated static bundle/assets.

- System-font visual treatment with restrained teal actions and neutral Apple-like surfaces.
- Translucent structural sidebar with opaque content cards.
- Native button-driven mobile navigation.
- Mobile menu closes after route selection, closes on Escape, and returns focus to the menu button.
- Reduced-motion styles disable transitions/animations.
- Reduced-transparency styles remove the sidebar material effect.
- Shared content edges, panel padding, grid gaps, and metric alignment were normalized.
- Two-column layouts collapse to one column at narrow widths.
- Wide tables and forecast charts scroll inside their panels instead of creating page overflow.
- Explorer controls use responsive grids.
- The UI adds scroll hints and accessible region labels when a table or forecast strip overflows.
- The methodology dialog, skip link, live status regions, labels, and chart ARIA labels remain part of the accessibility surface.

The Chrome QA evidence is in `docs/layout-review/`. It records 40 route/viewport checks across eight routes and five widths, plus menu, Escape, reduced-motion, and reduced-transparency checks.

## 5. Data and analytical logic

### Collection and aggregation

`pipeline/ingest_v2.py` performs resumable real-data collection from Open-Meteo historical weather and flood APIs. It preserves cached responses, records source URLs/retrieval times/grid coordinates, validates expected units, and labels older ERA5 and recent IFS weather products.

For each of the 25 reference points it builds daily fields from hourly data:

- rainfall: daily precipitation sum, requiring a complete day;
- temperature: daily mean;
- humidity: daily mean;
- wind: daily maximum;
- pressure: daily mean;
- `tmax`: daily maximum temperature;
- `q`: daily modelled river discharge where the flood grid has usable data.

Missing values are retained as missing. A missing flow series is not silently treated as zero.

### Historical thresholds and severity

`pipeline/analyze.py` creates rolling and percentile fields:

- `r3`: 3-day cumulative rainfall;
- `r7`: 7-day cumulative rainfall;
- `qp`: month-specific percentile of modelled discharge;
- `rp`: month-specific percentile of 3-day rainfall;
- `tp`: month-specific percentile of daily maximum temperature;
- `wp`: month-specific percentile of daily maximum wind.

The reference baseline is 2016–2020 and is calculated by calendar month. Percentile severity is:

- **2 / Unusual** when the strongest available percentile is at least 99;
- **1 / Elevated** when it is at least 95;
- **0 / Typical** when data exists but is below the elevated threshold;
- **-1 / No data** when no usable component exists.

The 2016–2020 baseline is an analytical reference, not a formal climate normal.

### Episode logic

Episodes are detected from 2021 onward when either flow percentile or 3-day rainfall percentile reaches the unusual threshold. Consecutive qualifying days are grouped. The episode stores start/end, duration, peak date, peak flow, peak rainfall accumulation, score, and whether it is classified as high-flow/rainfall or rainfall-only. The UI replays these groups; it does not claim they are independently confirmed disasters.

### EDA and risk score

`pipeline/eda.py` writes `dist/data/eda.json`.

The 0–100 latest-day district screening score is:

```text
50% modelled flood/discharge severity
30% 3-day cumulative rainfall severity
20% unusual weather severity
```

The weather component is the maximum of temperature and wind percentile. If a component is unavailable, its weight is omitted and the remaining weights are rescaled. The ranking basis says when a fallback was used. If no usable component exists, the score is unavailable.

This is a transparent screening index. It is not a calibrated probability and does not model exposure, drainage, vulnerability, inundation depth, or official warning thresholds.

## 6. Forecast and provider logic

`pipeline/refresh_current.py` saves a timestamped 16-day forecast snapshot in `dist/data/current.json` and a flat CSV in `dist/data/forecast-daily.csv`.

- Weather is requested for all 25 reference points.
- River forecasts are requested for locations with river metadata.
- A failed flood refresh preserves the previous flood snapshot and its original retrieval timestamp.
- Forecast signal comparisons are suppressed when a snapshot is stale.
- Weather and flood results are aligned by date rather than by array index alone.
- River P25–P75 values describe ensemble spread; they are not return-period thresholds.
- Open-Meteo does not provide the originally proposed 2-, 5-, or 20-year flood return thresholds in the fields used here. The project correctly labels the percentile alternative instead.

The backend protects upstream access by using fixed provider hosts, a five-minute cache bucket, and a request budget. It does not accept arbitrary upstream URLs from the browser.

## 7. Backend and deployment logic

`backend/main.py` exposes:

- `/api/health`
- `/api/summary`
- `/api/locations`
- `/api/history/{location_id}` with ISO date validation and range checks
- `/api/analysis`
- `/api/baselines`
- `/api/forecast-snapshot`
- `/api/download`
- `/api/place`
- `/api/search`
- `/api/assets/{name}` with an allowlist
- `/api/compact-history/{location_id}`

It supports packaged JSON by default and PostgreSQL for history when `DATABASE_URL` is configured. `infra/schema.sql` defines the `daily_weather` table, physical range checks, primary key, and date index. `docker-compose.yml` runs PostgreSQL and FastAPI locally.

The static deployment path is:

```text
npm run build
Vercel output directory: dist
API base: empty for static mode, HTTPS FastAPI origin for connected mode
```

The local demonstration path is `START_WINDOWS.bat` or `python serve.py`, then `http://localhost:8000`.

## 8. File inventory

### Core source and generated frontend files

- `frontend/react-ui.jsx` — React EDA and Global Explorer source.
- `build.mjs` — esbuild production bundle command.
- `package.json`, `package-lock.json` — Node scripts and React/esbuild/jsdom dependencies.
- `dist/index.html` — application shell and script/style loading order.
- `dist/app.js` — route state, historical screens, map, charts, filters, export, refresh, and event replay.
- `dist/core.mjs` — null-safe analytical helpers and forecast/episode logic.
- `dist/react-ui.js`, `dist/react-ui.js.LEGAL.txt` — generated React bundle and legal comments file.
- `dist/interface.mjs` — mobile menu, overflow hints, archive update detection, and focus behavior.
- `dist/page-guides.mjs` — route-specific reading guides.
- `dist/style.css`, `dist/theme.css`, `dist/layout.css`, `dist/apple.css` — visual theme, structure, responsive behavior, and accessibility styling.
- `dist/config.js` — runtime API configuration; currently static mode.

### Pipeline and backend files

- `pipeline/locations.json` — 25 checked reference points.
- `pipeline/ingest_v2.py` — resumable provider ingestion and daily/hourly preparation.
- `pipeline/analyze.py` — rolling fields, seasonal percentiles, severity, episodes, SQLite and summary output.
- `pipeline/eda.py` — distributions, correlations, monsoons, yearly rates, heatmap data, scatter data, and ranking.
- `pipeline/refresh_current.py` — weather/flood forecast snapshot refresh.
- `pipeline/refresh_daily.py` — single-writer daily pipeline runner and status/lock handling.
- `pipeline/validate_v2.py` — data continuity, uniqueness, range, provenance, map, forecast, and reconciliation checks.
- `pipeline/export_parquet.py`, `pipeline/publish_cloud.py`, `pipeline/run_spark_local.py`, `pipeline/databricks_spark.py` — Parquet, S3, Spark, and Databricks paths.
- `backend/main.py` — FastAPI API and safe upstream proxy.
- `backend/Dockerfile`, `backend/requirements.txt` — backend container/runtime.
- `infra/schema.sql` — PostgreSQL schema.
- `infra/main.tf`, `infra/terraform.tfvars.example` — AWS infrastructure templates.
- `docker-compose.yml` — local PostgreSQL/FastAPI setup.

### Tests, QA, and documentation

- `tests/core.test.mjs` — null handling, thresholds, stale snapshots, date alignment, and episode grouping.
- `tests/react.test.mjs` — 150 location/view DOM renders, React route mounting, dates, fallback map, filters, exports, and forecast chart labels.
- `tests/backend_test.py` — FastAPI HTTP smoke tests.
- `tests/eda_test.py` — full score, missing-component rescaling, and unavailable score tests.
- `tests/daily_refresh_test.py` — stage ordering, failure cleanup, and overlapping-run lock behavior.
- `tools/functionality-qa.mjs` — supervised Chrome interaction assertions.
- `tools/layout-qa.mjs` — route/viewport overflow and alignment checks.
- `tools/archive-qa.mjs` — new archive date notice check.
- `docs/TESTING.md` — test commands and manual acceptance checklist.
- `docs/VALIDATION_RESULTS.txt` — previously recorded local release validation.
- `docs/layout-review/` — screenshots, measurements, functionality evidence, and interaction evidence.
- `docs/DAILY_REFRESH.md` — refresh behavior and current refresh snapshot.
- `docs/ASSIGNMENT_COVERAGE.md` — requirement mapping and qualification notes.
- `docs/CLOUD_SETUP.md`, `docs/DEPLOYMENT.md` — deployment paths.
- `docs/DATA_DICTIONARY.md`, `docs/REPORT.md`, `docs/FloodLens-Report.pdf`, `docs/FloodLens-Presentation.pptx` — data/report/presentation material.
- `docs/DEMO_SCRIPT.md`, `docs/VIVA_GUIDE.md`, `docs/CONTRIBUTIONS.md` — handover, viva, demonstration, and contribution guidance.

### Current generated data/artifacts

- `dist/data/summary.json`, `baselines.json`, `lags.json`, `eda.json`, `current.json`, `validation.json`.
- `dist/data/historical-daily.csv`, `forecast-daily.csv`, and 25 location JSON files.
- `data/raw/` compressed source responses and quota ledger.
- `data/processed-v2/` daily/hourly processed CSVs, SQLite, and manifest.
- `data/parquet/` raw partitioned outputs.
- `docs/layout-review/*.png`, `results.json`, `functionality.json`, and `interactions.json`.

## 9. Verification status

Verified during this handover audit:

- `npm test` passed: core analytical tests and React/jsdom integration tests.
- `npm run check` passed: `dist/app.js` syntax check.
- Bundled Python `pipeline/validate_v2.py` passed with archive end `2026-09-15`, 25 districts, 2,346,600 hourly rows, and 97,775 daily rows.
- Bundled Python `tests/eda_test.py` passed.
- Bundled Python `tests/daily_refresh_test.py` passed.
- `docs/layout-review` contains the recorded 40 layout checks and interaction/accessibility results.

The normal `python` command is not installed in the current Windows shell, so the bundled workspace Python executable was used for the successful Python checks. The backend smoke test process did not return cleanly during this audit; the existing `docs/VALIDATION_RESULTS.txt` records that the backend HTTP routes had previously passed. Re-run `tests/backend_test.py` in a normal Python environment before a final release sign-off.

## 10. Known limitations and remaining work

- AWS provisioning, S3 upload, RDS integration, Databricks cloud execution, and Vercel deployment are not proven complete by this package.
- The daily GitHub Actions workflow must be enabled and connected to the team repository; the local refresh automation requires the computer/app to be available.
- Live APIs, map tiles, geocoding, GPS, elevation, and forecast freshness require internet access.
- Trincomalee and Mullaitivu have unavailable discharge at their current flood grids; nulls are preserved.
- ERA5, IFS, and GloFAS are modelled products, not local gauge measurements.
- District points do not represent district averages, inundated areas, or full catchments.
- Episodes are algorithmically detected and lack independent flood-event ground truth.
- Percentile levels and the risk index are analytical heuristics, not official warnings or return-period probabilities.
- Visual browser acceptance, GPS success, provider behavior for every location, and cloud deployment must be rechecked in the team’s actual environment.
- The 16 September refresh updated data artifacts, but `docs/REPORT.md` and the presentation were not regenerated afterward according to `docs/DAILY_REFRESH.md`.
- The project should be placed under Git and the first baseline commit should be created so future handovers can provide exact changed-file and line-level history.

## 11. Recommended next handover actions

1. Put the project under Git and commit the current known-good baseline.
2. Run the backend smoke test with the team’s normal Python environment.
3. Start the static server and manually exercise every route on desktop and mobile.
4. Verify one live search, one forecast refresh, one provider failure, GPS denial, date validation, event replay, and CSV export.
5. Decide whether to regenerate the report and presentation from the 16 September data.
6. Enable the intended GitHub Actions daily refresh only after confirming credentials, quotas, Vercel hook behavior, and artifact commit policy.
7. Record each student’s actual contribution with commits, test evidence, design decisions, and limitations in `docs/CONTRIBUTIONS.md`.

