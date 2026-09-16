# FloodLens Sri Lanka - DS 4004 final report

Release date: 2026-09-10

FloodLens Sri Lanka

Flood and Extreme Weather Analytics

DS 4004 · Group A · Option 3<br/>Release: 2026-09-10

This project collects, processes and visualizes historical weather and modelled river discharge for Sri Lanka. It identifies unusual conditions at sampled locations and interprets upcoming weather and river-flow forecasts supplied by Open-Meteo. No forecasting model is fitted by the project.

| Release evidence | Value |
| --- | --- |
| Historical dates | 2016-01-01 to 2026-09-09 |
| Hourly weather records | 2,343,000 |
| Daily analytical records | 97,625 |
| Valid daily flow values | 89,815 |
| Monitoring points | 25 districts; 23 with valid flow |
| Reference period | 2016-2020, month-specific |
| Prediction source | Weather Forecast API and GloFAS Flood API |

The result is a React-based, deployable dashboard with an optional FastAPI service with real geographic boundaries, interactive filters, a historical explorer, flood indicators, event replay, forecast interpretation and CSV exports. A separate incremental pipeline updates the shared data.

Group A: Kasun Vishvajith · Akindu Liyanage · Yasuri Fernando. Add registration numbers and a verified contribution log before submission.

1. Scope and data sources

The assignment requires real-time and historical API data, exploratory analysis of five indicators, efficient storage, user inputs, an interactive dashboard, and Option 3 analyses of extreme conditions and priority regions. It mentions forecasting but does not mandate fitting a prediction model.

| Product | Role and limitation |
| --- | --- |
| ERA5 historical weather | Hourly historical weather; recent publication lag requires a labelled IFS tail. |
| ECMWF IFS | Recent historical weather until ERA5 becomes available; a different product and resolution. |
| GloFAS discharge | Modelled daily flow; consolidated history followed by the default seamless API, which can include forecast-backed records. |
| Weather Forecast API | Current conditions and 16-day weather outlook, including rain probability. |
| GloFAS forecast | Ensemble median, 25th and 75th percentiles of daily river flow. |
| Geocoding API | Global place search; coordinates and GPS also select locations. Custom places have live data, not precomputed historical baselines. |

Historical coverage ends on 2026-09-09 UTC, the latest completed day targeted by this build. Forecast records are stored separately. Retrieval timestamps and source-product changes remain visible.

| Variable | Unit | Daily transformation |
| --- | --- | --- |
| Precipitation | mm | Sum; all 24 hours required |
| Temperature | degrees C | Mean and maximum; all 24 hours required |
| Relative humidity | % | Mean; all 24 hours required |
| Wind speed | km/h | Maximum; all 24 hours required |
| Sea-level pressure | hPa | Mean; all 24 hours required |
| River discharge | m³/s | Daily modelled value, not an hourly sum |

2. Geographic coverage

Twenty-five district reference points cover all nine provinces and all 25 districts. Available discharge points sample nearby modelled channels. Returned API grid coordinates can differ from requested coordinates. A marker is a sampled point, not a district average or a catchment measurement.

Map geometry: geoBoundaries LKA ADM2, 25 districts, source representation year 2017, build December 2023. Source: OpenStreetMap/Wambacher, ODbL 1.0. The web map uses Leaflet and attributed OpenStreetMap tiles. Bundled district geometry remains available without remote tiles.

3. Analytical methodology

Quality and transformations

Hourly records are indexed by location and timestamp. Daily frames are reindexed to consecutive UTC dates before rolling calculations. Missing values remain missing; no synthetic records or zero-filled measurements are introduced. Range checks cover precipitation, wind, discharge, humidity and percentile bounds.

Seasonal baseline and events

For each location and calendar month, the reference distribution uses 2016-2020 values. We calculate a midrank percentile, 100 × (count below + 0.5 × count equal) / reference count. This treats repeated zero values fairly. Baseline thresholds use the 50th, 95th and 99th quantiles.

Historical severity uses the largest available percentile among 3-day rainfall, modelled flow, daily maximum temperature and wind. Values at or above the 95th percentile are elevated; values at or above the 99th are unusual. Missing indicators do not automatically imply typical conditions.

Consecutive unusual days form episodes. The event view explores episodes from 2021 onward, after the baseline period, with rainfall, flow and surrounding days. The user can also choose heat or wind episodes. No episode is claimed to be an independently confirmed flood disaster.

Regional comparison and lag analysis

Priority points are ranked by the proportion of valid days with unusual rainfall or flow. A separate count shows days when both are elevated. District labels provide geographic context without implying area-wide measurements. A separate latest-day screening score combines 60% flow and 40% 3-day rainfall percentile; locations without flow use explicitly labelled rain-only scores. Lag correlations compare local rainfall with later flow after subtracting monthly seasonal means; these are exploratory associations, not causal estimates.

4. Exploratory weather findings

The chart compares mean daily rainfall for the same baseline years at Ratnapura, Jaffna and Batticaloa. It demonstrates why a single nationwide rainfall threshold can hide seasonal and geographic differences. The dashboard repeats this exploration for temperature, humidity, wind and pressure.

Monthly rainfall plots show the sum of available complete daily totals. Other monthly plots show the mean of daily summaries. The valid-day count is displayed so incomplete periods can be recognized. Comparing a partial year against a full year without adjustment is inappropriate.

These are point-level modelled weather patterns. The five-year baseline supports this project’s exploratory comparisons but is shorter than a formal multi-decade climate normal. Changes in source products can also affect apparent trends.

EDA: distributions and monsoons

The histogram shows the distribution of real daily rainfall at Ratnapura. The matrix uses pairwise complete daily records and includes rainfall, temperature, humidity, wind, pressure and modelled discharge. Seasonality and serial dependence can affect these associations.

| Ratnapura season | Valid rain days | Mean rain mm/day | Mean flow m³/s |
| --- | --- | --- | --- |
| Southwest monsoon | 1662 | 9.40 | 34.26 |
| Northeast monsoon | 951 | 15.17 | 68.41 |
| Inter-monsoon | 1292 | 11.89 | 36.34 |

Southwest monsoon months are May-September; northeast months are November-January. This full-archive comparison uses daily means rather than unequal-length seasonal totals. The dashboard also presents yearly unusual-day counts and rates, explicitly marking partial years.

5. Flood-related event example

Selected event: **Kalutara**, with peak modelled flow on **2025-11-29**. The recorded peak is **1354.19 m³/s**. The plot displays the surrounding rainfall and discharge using separate axes and units.

Replay connects the timing of local rainfall and river response. Upstream rainfall, routing, reservoir operations and model assumptions may explain differences; local rainfall alone is not a complete catchment input. The event selection is reproducible from the published episode list, not a claim of observed damage.

6. API forecasts and upcoming signals

Ratnapura forecast snapshot: 2026-09-10 to 2026-09-25; retrieved 2026-09-10T13:54:34.059796+00:00. Forecast rain totals 286.6 mm across these dates. The graph shows the ensemble median and middle 50% of flow members.

The project uses the forecast values directly. A watch flag is triggered at the location’s monthly historical 95th percentile; a high flag at its 99th percentile. Rainfall and flow are assessed separately. Missing values, inadequate reference samples and snapshots older than 24 hours do not generate forecast flags.

Ensemble spread is variation among model members, not a calibrated flood probability. Forecast and historical products can have different grids and biases. These threshold comparisons are exploratory and require gauge/event validation before operational use.

7. Engineering and measured performance

The collection pipeline caches original responses with source URLs and retrieval times. The release packages hourly compressed CSV and reproducible Parquet conversion. Spark processes typed records in Databricks; S3 upload and PostgreSQL loading scripts support the proposed cloud path. The local SQLite benchmark below is measured; it is not evidence of a Spark or AWS run. Prepared daily JSON keeps the static frontend lightweight.

| Actual records | Median query time |
| --- | --- |
| 585,750 | 0.478 seconds |
| 1,171,500 | 1.077 seconds |
| 2,343,000 | 2.031 seconds |

The query groups hourly rainfall and temperature by location and month. Each size is timed three times; the chart reports the median. These single-machine measurements describe this build, not the user’s hardware or a distributed cluster.

Local Spark verification: version 3.5.6, local[2], 2g driver memory. The same notebook produced 97,625 unique daily records in 58.0 seconds. This is a local Spark run, not a Databricks cloud execution.

Daily updates refresh the recent 14 days, rerun analysis and validation, save forecast snapshots, and publish updated data through the supplied GitHub Actions/Vercel workflow once configured. A website deployment alone does not enable that schedule.

8. Cloud architecture and reproducibility

React frontend → FastAPI → PostgreSQL forms the connected application path. The static edition can also display packaged analytics without a backend. Python collects APIs, Spark cleans and aggregates data, Parquet preserves typed source records, S3 stores objects and RDS hosts PostgreSQL.

| Component | Delivered implementation / execution boundary |
| --- | --- |
| React + FastAPI | Built React components and a read-only API with validated coordinates, fixed upstream hosts and cached requests. |
| Parquet + S3 | Compressed Parquet exporter and authenticated S3 publisher. Local hourly partitions use district/year; Spark daily output uses district/date. |
| Spark / Databricks | Importable notebook with cleaning, complete-day aggregation, rolling rainfall, percentile flags and monsoon summaries. Team cloud execution required. |
| PostgreSQL / RDS | Schema, idempotent loader, Docker configuration and private encrypted RDS Terraform configuration. AWS account execution required. |
| Daily refresh | GitHub Actions workflow; must be enabled in the team repository and connected to deployment. |

Databricks Free Edition restricts external network access. Uploading source Parquet into a Unity Catalog volume is the free-compatible processing path. Direct S3/RDS access requires permitted storage/network configuration. AWS student credits do not guarantee a zero bill.

Correction to the proposal

The Open-Meteo Flood API does not expose 2-, 5- or 20-year return-period thresholds. Its p25/p75 variables are ensemble statistics. This implementation uses labelled historical percentile screening and does not equate it with return periods. A verified external threshold source would require a declared scope change.

Cloud provisioning and Databricks execution have not been performed in the team accounts. The final submission should include actual job results and screenshots once the team runs these components. Never present the local SQL benchmark as distributed-processing evidence.

9. Conclusions, limits and references

FloodLens meets the chosen direction by combining flood and weather APIs, identifying unusual conditions, comparing priority locations and presenting historical context alongside provider forecasts. Its contribution is a transparent, reproducible analytical application rather than a newly trained forecasting model.

Main limits: point sampling; unverified model-channel identity; reanalysis and forecast-product changes; a short baseline; no labelled flood-event ground truth; no exposure/vulnerability data; and service availability or scheduling delays. The dashboard is a research tool, not an official warning service.

Assignment deliverables and team evidence

The package contains source code, data, a deployable dashboard, report, presentation, validation scripts, deployment steps and contribution guidance. Each member should record actual decisions and verification in a contribution log and rehearse the demonstration.

References and attribution

Course brief: DS 4004 Group Project 2026, supplied PDF, pages 1-2.

Open-Meteo historical weather: https://open-meteo.com/en/docs/historical-weather-api

Open-Meteo Forecast API: https://open-meteo.com/en/docs

Open-Meteo Flood API: https://open-meteo.com/en/docs/flood-api

Open-Meteo Geocoding: https://open-meteo.com/en/docs/geocoding-api

Open-Meteo Elevation: https://open-meteo.com/en/docs/elevation-api

Databricks limits: https://docs.databricks.com/aws/en/getting-started/free-edition-limitations

API limits and attribution: https://open-meteo.com/en/pricing

District geometry: https://www.geoboundaries.org/api/current/gbOpen/LKA/ADM2/

OpenStreetMap licence: https://www.openstreetmap.org/copyright

Leaflet: https://leafletjs.com/

Credit Open-Meteo, ECMWF ERA5/IFS and Copernicus EMS GloFAS for weather/flow data. CC BY 4.0 attribution applies. Retain the separate map-source attribution and included Leaflet licence.