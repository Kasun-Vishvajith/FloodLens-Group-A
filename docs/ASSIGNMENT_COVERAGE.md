# Proposal and assignment coverage — Group A

| Requirement | Implementation | Qualification |
|---|---|---|
| Historical weather from 2016 onward | Resumable Python collector; five hourly variables and daily summaries | End is capped at the latest completed day; actual coverage shown in UI |
| All 25 districts | One geographically checked reference point per district | Point observations are not district averages |
| Flood API | Daily modelled discharge, flow forecasts and ensemble spread | All 25 reference points requested; unavailable flow remains missing |
| 2/5/20-year return thresholds | **Not supplied by Open-Meteo** | Historical monthly percentile screening is an explicit alternative, not a return period |
| 16-day forecast | Weather Forecast API and Flood API | No self-trained model; unavailable days remain missing |
| Geocoding / coordinates / GPS | Global explorer | GPS requires browser permission and a secure origin |
| Elevation API | Terrain height for reference points and custom places | Elevation alone is not a vulnerability model |
| Real map | geoBoundaries 25-district geometry + Leaflet/OSM | Map attribution retained; tiles need internet |
| EDA | Statistics, histograms, correlations, seasonal baseline | Pair counts and missing values retained |
| Flood frequency / year trends | Threshold-exceedance episodes and unusual-day rates by year | These are modelled exceedances, not confirmed flood disasters |
| Monsoons | SW May–September / NE November–January comparison | Daily means accommodate unequal season lengths |
| Risk and anomalies | Latest-day 0–100 score: 50% flood severity, 30% 3-day rainfall, 20% unusual weather; month-specific 2016–2020 baseline | Missing components are explicitly rescaled; this is a heuristic index, not a calibrated probability |
| React + FastAPI | React EDA/global components; React-mounted historical screens; connected API | Static fallback also deployable; incremental React architecture documented |
| Parquet + AWS S3 | Typed Parquet exporter, S3 upload script, private bucket Terraform | Cloud upload requires team credentials; local raw partitions use district/year |
| Spark / Databricks | Importable processing notebook | Team must execute in Databricks and record results |
| PostgreSQL / AWS RDS | Schema, upsert loader, Docker, private encrypted RDS Terraform | Team cloud account and permitted network required |
| Refresh | Daily GitHub Actions workflow + optional Vercel hook | Must be enabled in team's repo; scheduler delays remain possible |
| Report/presentation/contribution | Reproducible report, slides, Group A contribution log | Record actual individual work; don't claim unexecuted cloud runs |

The exact original proposal cannot be fulfilled under the claim “entirely Open-Meteo, predefined return-period thresholds” because those threshold fields are absent. Correct that statement before submission. AWS infrastructure is also not guaranteed zero-cost.
