# FloodLens Group A — complete handover

**Project:** FloodLens Sri Lanka — DS 4004, Option 3 (Flood and Extreme Weather Analytics)  
**Team:** Kasun Vishvajith, Akindu Liyanage, Yasuri Fernando  
**Prepared:** 16 September 2026  
**Package:** clean Vercel + GitHub Actions edition

## 1. Product verdict

FloodLens meets the practical requirements of Option 3: it uses Flood API and weather data, analyses extreme conditions, identifies high-risk reference regions, detects unusual events, provides EDA, and exposes provider forecasts. It is intentionally a manageable course project: the data pipeline, transparent calculations, map and UI demonstrate big-data engineering without introducing an unvalidated machine-learning model.

The bundled release contains 25 Sri Lankan district reference points and daily data from **2016-01-01 to 2026-09-15**. `as_of` is **2026-09-16**. A later successful workflow run extends the end date automatically to the latest completed UTC day. Future dates are never fabricated.

The map is a real district map from geoBoundaries rendered with Leaflet/OpenStreetMap when available, with a geographic SVG fallback. A point colour is a sampled location indicator; it is not an inundation polygon or district-wide mean.

## 2. Architecture and languages

| Layer | Technology | Why it is used |
| --- | --- | --- |
| Browser UI | HTML, modern CSS, vanilla JavaScript, React 18 | Fast static delivery, reusable EDA components, accessible tables and controls. |
| Build | Node.js, esbuild | One small production bundle with no runtime server requirement. |
| Processing | Python 3.10+, pandas, NumPy | Clear tabular transformations, rolling windows, percentiles and validation. |
| Storage | Versioned JSON/CSV in `public/data/`; gzip request cache and run evidence in `data/` | Browser-friendly release plus reproducible audit evidence. |
| Automation | GitHub Actions cron/manual workflow | Daily collection and persistence without paying for a server. |
| Hosting | Vercel static output (`dist/`) | Free, simple deployment; the collector runs in Actions rather than a long-running Vercel process. |

There is no required AWS, RDS, Databricks, Docker or backend service in this edition. `pipeline/spark_check.py` is optional local evidence only and is not part of the runtime path.

## 3. Repository layout

- `src/index.html`: application shell and semantic landmarks.
- `src/app.js`: route controller, state, legacy analytical screens, map, filters, exports and live refresh.
- `src/views.jsx`: mounts the React EDA and global explorer routes.
- `src/pages/Analysis.jsx`: EDA page (distributions, correlations, monsoons, annual rates, ranking, scatter, heatmap, calendar).
- `src/pages/Explorer.jsx`: Sri Lanka/global search, GPS, coordinate loading and forecast table.
- `src/components/analysis-charts.jsx`: React chart/table components.
- `src/components/time-series.js`: SVG line chart used by history, flood, event replay and forecast pages.
- `src/lib/analytics.js`: null-safe statistics, severity, midrank helpers, episode grouping, forecast alignment, ordinal suffixes and log tick conversion.
- `src/lib/api.js`: browser API cache/in-flight request deduplication, 15-minute localStorage TTL and 30-second timeout.
- `src/interface.js`: navigation disclosure, scroll hints and published-release change detection.
- `src/styles/`: style system and responsive/accessibility rules; `index.css` imports the modules.
- `public/data/`: deployable release inputs. `dist/data/` is the generated copy served by Vercel.
- `pipeline/config.py`: one source of truth for paths, dates, provider variables and column order.
- `pipeline/provider.py`: serial HTTP client, deterministic gzip cache, retries, Retry-After handling, quota guard and JSONL audit log.
- `pipeline/update.py`: lock, recent collection, forecast snapshots, staging, analysis, EDA, validation and atomic promotion.
- `pipeline/analyze.py`: full-archive rolling fields, monthly percentiles, severity, lag correlations and episodes.
- `pipeline/eda.py`: descriptive statistics, histograms, correlations, monsoon/year summaries and 0–100 screening ranking.
- `pipeline/validate.py`: independent release gate and `validation.json` writer.
- `pipeline/report.py`: concise generated release factsheet.
- `tests/`: Python numerical/persistence tests and Node/jsdom UI tests.
- `.github/workflows/daily-data.yml`: scheduled/manual refresh and optional Vercel deploy hook.
- `scripts/build.mjs`: clean build into `dist/`.
- `vercel.json`: Vercel build/output/cache/security configuration.
- `docs/`: this handover plus methodology, deployment, testing and contribution notes.

## 4. Data contract and storage

### Published files

Each location file (`public/data/<location-id>.json`) has a stable `columns` array and a `rows` matrix. Columns are:

`date, rain, temp, humidity, wind, pressure, tmax, q, r3, r7, qp, rp, tp, wp, severity, weather_model, flow_source`.

Units are rainfall mm, temperature °C, humidity %, wind km/h, pressure hPa and discharge m³/s. `historical-daily.csv` is the same daily archive in download form. `forecast-daily.csv` contains provider forecast weather and flow with independent weather/flood retrieval timestamps. `current.json` stores current/16-day snapshots. `summary.json` contains release ID, coverage, location metadata, provenance and counts. `baselines.json`, `lags.json`, `eda.json`, `districts.geojson`, `elevation.json`, `map-provenance.json` and `validation.json` support the UI and audit trail.

The source package intentionally ships daily data for a compact deployment. The earlier hourly evidence count remains recorded as `original_hourly_rows: 2,346,600`; the original hourly files are not claimed to be inside this reduced ZIP.

### Runtime and transient files

`data/raw/` contains gzip responses keyed by SHA-256 URL hash. `data/request-log.jsonl` records endpoint, status, attempts, cache hits, estimated units, bytes, latency, UTC time and run ID. `data/runs/<run-id>.json` stores stage durations and outcome. `data/refresh-status.json` stores the latest run. `data/refresh.lock` is a one-byte process lock and must never be committed. Temporary `data/floodlens-*` directories are deleted after a run and are excluded from the final package.

## 5. API collection logic

Open-Meteo is key-free. The provider URLs are defined in `pipeline/update.py`:

1. Historical weather: `https://archive-api.open-meteo.com/v1/archive` with precipitation, temperature, humidity, wind and pressure. ERA5 is used for the archive; the newest tail is labelled ECMWF IFS when the provider exposes it.
2. Historical/modelled flow: `https://flood-api.open-meteo.com/v1/flood` with daily `river_discharge`.
3. Forecast weather: `https://api.open-meteo.com/v1/forecast` with current conditions and 16 daily values.
4. Forecast flow: Flood API with `river_discharge_median`, p25 and p75 where available.
5. Geocoding: `https://geocoding-api.open-meteo.com/v1/search` for typed names.
6. Elevation: Open-Meteo elevation endpoint for explorer context.

The first historical build was split by location and date because provider limits and response size make one giant request fragile. The daily workflow only requests a 14-day overlap ending on yesterday, in chunks of at most 31 days. The overlap safely corrects late revisions and prevents duplicate dates. Each request is serialised, bounded by a 60-second timeout, retried up to five times for transient 429/5xx/URL errors, and respects `Retry-After`. The client refuses requests above 550 estimated units/minute and stops a run above its conservative daily budget.

At the time of handover, provenance metadata contains **549 source records** across the 25 locations (ERA5/original ERA5, recent IFS and GloFAS entries). The local interrupted refresh audit contains **13 HTTP attempts: 11 successful and 2 failed**, all recorded in `data/request-log.jsonl`; it was not promoted. The last successful offline release used **0 HTTP calls** and completed in **8.6 seconds** (analysis 4.45 s, EDA 2.42 s, validation 1.70 s). Exact future call counts depend on how many days are missing and provider responses; every run records its own count.

## 6. Aggregation and quality rules

`aggregate()` converts hourly responses to UTC daily rows. Duplicate timestamps keep the last copy. Values outside physical ranges are set missing. Rain, mean temperature, mean humidity, maximum wind, mean pressure and maximum temperature are calculated only when all 24 hourly observations for that field are valid. A missing value is preserved as missing; it is never changed to zero. Discharge is left missing when the Flood API has no usable value. The validator checks date uniqueness, consecutive coverage from 2016-01-01, column order, physical ranges, 25 unique districts, 25 GeoJSON features and forecast date alignment.

The two current locations without valid flow in the bundled archive are Trincomalee and Mullaitivu (3,911 missing flow days each). They remain usable for weather analysis and are shown as weather-only where appropriate.

## 7. Analytical logic

### Rolling rainfall

`r3` and `r7` are three-day and seven-day sums. The first two or six days remain missing because a complete window is required.

### Seasonal percentiles

For each location and calendar month, the complete 2016–latest archive is the reference distribution. Percentiles are computed with NumPy quantiles for thresholds and an average (midrank) of left/right ranks for each observation. At least 30 valid monthly observations are required. The seasonal baseline has three threshold values (`p50`, `p95`, `p99`) and `n` in `baselines.json`.

The 95th percentile is used for an **elevated/watch** signal: it identifies the top approximately 5% of comparable calendar-month values without making the UI too noisy. The 99th percentile is used for an **unusual/high** signal and episode trigger: it focuses attention on approximately the most exceptional 1% of comparable values. They are empirical screening cut-offs, not legal warning levels or 2-, 5- or 20-year return periods. Full-archive retrospective ranks can change when a new year is appended; the UI states this limitation.

### Severity and episodes

For discharge, 3-day rain, maximum temperature and maximum wind, the greatest available percentile sets the day: 0 typical, 1 elevated (≥95), 2 unusual (≥99), −1 unavailable. Consecutive days with `max(discharge percentile, rainfall percentile) ≥99` form an episode; a date gap closes it. Event replay labels the episode as algorithmic and model-based.

### Lag relationship

For lags 0–7, monthly means are subtracted from rain and discharge before Pearson correlation. This removes the strongest calendar-season effect. Pair counts are stored. The result is exploratory association and does not establish causality.

### Screening score

The latest historical day has a transparent 0–100 score: 50% flow percentile, 30% three-day rainfall percentile and 20% maximum of heat/wind percentiles. Missing components are omitted and the remaining weights rescaled; the basis is displayed. This makes locations sortable while avoiding a false claim that the score is a calibrated probability.

## 8. UI behaviour and fixes made

- EDA is a first-class navigation route named **Exploratory analysis**, with visible distribution, correlation, monsoon, annual, ranking, scatter, heatmap and calendar panels.
- Rainfall, history, flood and replay time series are SVG lines with circular data-point markers; dashed lines are thresholds/secondary references. Bar lists remain for histograms and score ranking where bars are the appropriate encoding.
- Ordinal text uses a shared helper: `81st`, `82nd`, `83rd`, `11th`, `12th`, `13th` are correct.
- Scatter log-axis labels use the inverse transform `expm1(log1p(maximum) × fraction)` rather than a linear approximation.
- Forecast weather and flood retrieval timestamps are kept separately in `current.json` and `forecast-daily.csv`.
- Map forecast mode colours points from forecast signals; historical mode colours them from selected historical rows. SVG geography remains available when Leaflet cannot load.
- One collapsible location/date filter is shared across routes. Quick ranges include last 30 days, this year and the full archive. Invalid ranges are rejected with feedback.
- Browser API requests are deduplicated and cached for 15 minutes. The open tab checks the published `release_id` and offers a reload when a newer archive is available. A background refresh attempts fresh weather only when the tab is online and the last attempt is older than 15 minutes.
- Empty, stale, missing-flow and weather-only states are explicit. Missing values stay blank in exports.
- Cloud-specific files and unused backend paths were removed from this deployable edition. Documentation now explains the Vercel + GitHub Actions path instead of claiming AWS/Databricks execution.

## 9. How to run locally

```bash
npm ci
python -m pip install -r requirements.txt
npm run build
npm test
python serve.py
```

Open `http://localhost:8000`. For a no-network reproducibility run:

```bash
python pipeline/update.py --offline
npm run build
```

For a live collection run, use `python pipeline/update.py`. It may take several minutes because requests are deliberately serialised and rate-limited. Never delete `data/refresh.lock` while a process is running. The command promotes a release only after analysis, EDA and validation all succeed.

## 10. GitHub Actions and Vercel handover

Push the repository to GitHub and enable `.github/workflows/daily-data.yml`. It runs at 01:35 UTC each day and can also be started manually. It installs Python and Node, runs tests, executes the staged update, generates `docs/REPORT.md`, builds and tests the website, commits only published data/evidence, and optionally POSTs a Vercel Deploy Hook stored as `VERCEL_DEPLOY_HOOK`.

Vercel imports the repository, runs `npm ci` and `npm run build`, then serves `dist`. The free static deployment does not run the Python collector continuously; GitHub Actions is the daily scheduler and the Git commit is the durable store. If the action fails, the previous release remains online.

## 11. Current release facts and limitations

- 25 districts/reference points; 97,775 daily rows; 89,953 valid discharge rows; 870 episodes were reported by the previous packaged summary, while the clean full-archive recomputation currently yields 731 episodes because the baseline policy was corrected and recalculated.
- The archive is daily in this ZIP. Original hourly data is represented by a documented count and source metadata, not shipped as 300 MB of raw files.
- Weather values are modelled grid data and representative points, not station observations or district means. City searches are live point forecasts, not historical city archives.
- Flow is unavailable for Trincomalee and Mullaitivu in the current historical source. No value is imputed.
- Forecast ensemble spread is not a confidence interval. Percentiles are not return periods. The platform is not an emergency warning service.
- Daily update reliability depends on GitHub Actions, Open-Meteo availability and the repository/Vercel hook being configured. The code is ready for that setup; deployment credentials and the public Vercel URL are intentionally not included.

## 12. Contribution evidence

The named group members should add their agreed individual work and dates to `docs/CONTRIBUTIONS.md` before submission. The repository has no usable Git history, so an exact historical commit-by-person report cannot be reconstructed. The current code inventory, run metrics, validation output, request log and test commands provide reproducible evidence of what is in the final package.
