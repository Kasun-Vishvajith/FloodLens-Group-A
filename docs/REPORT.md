# FloodLens release report

Generated from release **20260926T064112Z-26efc3d1**.

## Coverage

- Archive: **2016-01-01 to 2026-09-25** (UTC daily records).
- Reference locations: **25** Sri Lankan districts / monitoring points.
- Daily rows: **98,025**; valid discharge rows: **90,183**.
- Original hourly evidence: **2,346,600** rows (the compact deployable release stores daily data).
- Detected episodes: **735** using the 99th-percentile signal rule.

## Validation

- Status: **passed**.
- Checks: 25 unique districts, consecutive daily keys, physical ranges, full-archive percentile and rolling reconciliation, score bounds, forecast date alignment, 25 geometry features.
- Missing flow by location is retained in `public/data/validation.json` rather than being imputed.

## Interpretation

The score is an exploratory screening index. It is not a calibrated probability, an inundation map, or an official warning. Forecasts are provider values from Open-Meteo; the project does not train a machine-learning model.

## Refresh

GitHub Actions runs `pipeline/update.py` daily. A successful staged release is validated, committed to the repository, and can trigger a Vercel deploy hook.
