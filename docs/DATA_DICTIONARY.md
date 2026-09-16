# Data dictionary

All daily dates refer to UTC. Weather and river discharge are modelled products. An empty CSV cell / JSON null is missing, not zero.

| Field | Unit / meaning |
|---|---|
| location_id | Stable reference-point identifier |
| district | Sri Lankan district containing the requested coordinate |
| date | YYYY-MM-DD |
| rain | Precipitation, mm summed over 24 valid hours |
| temp / tmax | Daily mean / maximum temperature, °C |
| humidity | Daily mean relative humidity, % |
| wind | Daily maximum wind speed at 10 m, km/h |
| pressure | Daily mean sea-level pressure, hPa |
| q | Daily GloFAS discharge, m³/s |
| r3 / r7 | Complete 3-/7-day precipitation accumulation, mm |
| rp / qp / tp / wp | Same-month baseline midrank percentile for r3 / q / tmax / wind |
| severity | −1 unavailable; 0 typical; 1 elevated (≥95th); 2 unusual (≥99th), using largest available percentile |
| weather_model | ERA5 or explicitly labelled recent ECMWF IFS |
| flow_source | GloFAS consolidated or default seamless source |

Forecast CSV records remain separate and include UTC forecast date, min/max temperature, rainfall, maximum wind, rain probability where available, discharge ensemble median/P25/P75 and retrieval time. Ensemble statistics are not historical return-period thresholds.

Daily and accumulated rainfall are canonicalized to six decimal places before percentile ranking, so arithmetic round-off does not split tied measurements across processing engines.

The `dist/data/summary.json` location metadata retains requested coordinates, provider grid coordinates, source URLs, retrieval timestamps, missingness and date coverage. `elevation.json` separately records the 90 m DEM request and returned metres above sea level.

District risk is a screening index: 0.6 × qp + 0.4 × rp, with an explicitly labelled rp-only fallback when flow is unavailable or has no historical variation. A district reference point is not a district spatial average, upstream catchment model, vulnerability estimate or official warning.
