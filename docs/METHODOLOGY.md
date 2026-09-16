# FloodLens methodology

## Scope and sources

The release covers Sri Lanka only: one representative coordinate for each of the 25 districts. A point is a model sample location; it is not a district mean, a basin average, or an inundation polygon. Weather comes from Open-Meteo Historical Weather (ERA5 for the archive and labelled ECMWF IFS values for the recent tail). Modelled daily discharge comes from the Open-Meteo Flood API / GloFAS. Current and future values come from the Open-Meteo forecast and flood forecast products. Geocoding and elevation are used by the location explorer. District geometry is supplied by geoBoundaries; basemap tiles are attributed to OpenStreetMap.

## Fields and units

Hourly provider fields are converted to daily rows: rainfall sum (mm), mean temperature (°C), mean relative humidity (%), maximum wind (km/h), mean sea-level pressure (hPa), maximum temperature (°C), and daily river discharge (m³/s). Daily rows also contain `r3` and `r7` rainfall accumulation, monthly percentile fields `qp`, `rp`, `tp`, `wp`, a severity class, and source labels. Rain, temperature, humidity, wind and pressure are checked against physical limits. A day with fewer than 24 valid hourly observations is left missing rather than silently filled.

## Percentiles and severity

For each location and calendar month, the full archive is the reference distribution. A value is assigned a retrospective midrank percentile: ties receive the average rank, so repeated zero-rain observations do not all become an artificial 0th percentile. At least 30 valid reference days are required; otherwise the percentile remains missing. This seasonal comparison prevents wet monsoon months being compared directly with dry months. The baseline is intentionally retrospective: adding a new year can change old percentile ranks.

The four signals are discharge (`qp`), three-day rain (`rp`), maximum temperature (`tp`) and maximum wind (`wp`). A day is **typical** below the 95th percentile, **elevated** from the 95th, and **unusual** from the 99th. These are analytical thresholds, not return periods. Open-Meteo does not provide the proposed 2-, 5- and 20-year thresholds in this project’s data contract, so the interface never labels a percentile as a return period.

## Screening score

The latest historical day receives a 0–100 exploratory screening index:

- flood severity percentile: 50%
- three-day rainfall percentile: 30%
- maximum of temperature and wind percentiles: 20%

When a location has no usable flow variation or another component is missing, available weights are rescaled and the basis is displayed. This is a ranking aid, not a calibrated probability, exposure estimate, or official warning.

## Episodes and relationships

An episode groups consecutive days where the maximum of discharge and three-day rainfall is at least the 99th percentile. A date gap closes an episode. The replay view shows the selected values and explicitly calls the result an algorithmic event in modelled data. Rainfall/discharge lag correlations subtract each calendar-month mean first, then calculate Pearson correlation for lags 0–7; they describe association and do not establish causation.

## Forecast interpretation

The 16-day provider forecast is aligned by date independently for weather and river flow. Historical same-month p95 and p99 thresholds provide context. Missing or older-than-24-hour snapshots do not create flags. Flow p25–p75 is the provider ensemble spread, not a calibrated confidence interval.
