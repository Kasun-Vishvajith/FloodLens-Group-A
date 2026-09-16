# FloodLens Sri Lanka — Group A

Flood and Extreme Weather Analytics · DS 4004 · Option 3

**Kasun Vishvajith · Akindu Liyanage · Yasuri Fernando**

A downloadable React-based dashboard with historical analytics, real Sri Lankan district geometry, district screening indicators, event replay and provider forecasts. It includes FastAPI, Spark/Databricks processing, Parquet conversion, S3 publishing and PostgreSQL/RDS deployment files. No forecasting model is trained.

## Open the website locally

Install Python 3.12. Extract this entire folder and double-click `START_WINDOWS.bat`, or run `python serve.py`. Open http://localhost:8000. The committed frontend bundle and data require no Python packages. Internet access is needed for live forecasts, search and map tiles; bundled geographic boundaries and history remain available locally.

## Deploy on Vercel

Import the extracted project into your GitHub repository and connect it to Vercel. Choose **Other**, output **dist**, build **npm run build**. The included vercel.json supplies these settings. Keep `dist/config.js` API base empty for the static edition. Deployment is not performed by this package. The daily update workflow must be enabled separately.

## What the dashboard covers

- Overview with a real Leaflet/OpenStreetMap map and actual 25-district geometry.
- Historical rainfall, temperature, humidity, wind and pressure; date filters and CSV export.
- Current conditions and up to 16 days of weather/river forecasts from Open-Meteo.
- River discharge, accumulated rain, seasonal percentile indicators and event replay.
- EDA distributions, summary statistics, correlation matrix, monsoon comparisons and yearly unusual-day rates.
- District screening scores using a transparent 0–100 method: 50% flood severity, 30% 3-day cumulative rainfall and 20% unusual weather, with explicit rescaling when a component is unavailable.
- Global place search, coordinates, GPS and Elevation API data.
- Data provenance, missing values, forecast freshness and limitations.

## Data dates

History begins **2016-01-01** and targets the latest completed UTC day; never the rest of 2026 as historical observations. The exact verified bundled coverage is recorded in `dist/data/summary.json` and displayed in the application. Forecast dates and retrieval timestamps are separate. ERA5 supplies older weather; recent IFS values are labelled. GloFAS is modelled discharge, not gauge observations.

## Rebuild data

Create a Python virtual environment and install `requirements.txt`. Run these commands in order:

```
python pipeline/ingest_v2.py
python pipeline/analyze.py
python pipeline/refresh_current.py
python pipeline/eda.py
python pipeline/validate_v2.py
```

For Parquet/cloud dependencies, install `pipeline/requirements-cloud.txt`, then run `python pipeline/export_parquet.py`. Follow `docs/CLOUD_SETUP.md` for FastAPI, PostgreSQL, Databricks and AWS. Bulk collection is cached and quota-limited; resuming may require the next quota window. Daily refresh revises recent history because provider products can change.

The included `FloodLens-Colab.ipynb` runs the same pipeline online and downloads daily and optional combined hourly CSV files.

## Build React

Node 20+; run `npm ci`, then `npm run build`. Source: `frontend/react-ui.jsx`; the existing historical screens use a React-mounted HTML/SVG adapter in `dist/app.js`. This is an incremental React architecture, with new EDA/global views implemented as React components. FastAPI serves all history when an API base is configured.

## Course handover

Read `docs/ASSIGNMENT_COVERAGE.md`, `docs/TESTING.md`, `docs/CONTRIBUTIONS.md` and `docs/CLOUD_SETUP.md`. Report and presentation describe measured local results separately from cloud execution still required in the team's accounts. Cloud resources are not automatically created; AWS credits and Databricks access must be checked.

**Proposal correction:** Open-Meteo does not expose 2-, 5- or 20-year flood return thresholds. Historical percentiles and ensemble spread are not return periods or flood probabilities. See https://open-meteo.com/en/docs/flood-api.
