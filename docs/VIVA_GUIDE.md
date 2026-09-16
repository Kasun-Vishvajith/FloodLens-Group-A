# Viva preparation

- **Why no trained prediction model?** The product consumes forecasts produced by Open-Meteo's providers. The group's contribution is ingestion, quality checks, EDA, screening and presentation.
- **Are these observed floods?** No. GloFAS is modelled discharge. Threshold episodes have not been validated against independent disaster/gauge labels.
- **Where are 2/5/20-year thresholds?** They are not exposed by Open-Meteo Flood API. We corrected that proposal claim and label our percentile alternative explicitly.
- **Why Parquet rather than only CSV?** Types, compression and column pruning support analytical scans and Spark. CSV remains convenient for inspection/export; JSON suits API responses and small web payloads.
- **Why include a static edition?** It keeps the demonstration deployable on free frontend hosting. The same dashboard can connect to FastAPI/PostgreSQL when configured.
- **Why use district points?** They give reproducible nationwide sampling without pretending to measure the average of an entire district or upstream catchment.
- **How are missing values handled?** They remain missing. Incomplete hourly days cannot produce full-day aggregates. Missing or stale forecasts do not generate current flags.
- **Why 2016–2020 baseline?** It separates reference years from post-2020 event exploration. It is not a formal long-term climate normal.
- **What is the risk score?** A transparent percentile screening index with a labelled rain-only fallback. It is not the probability of flooding and excludes exposure, drainage and vulnerability.
- **Did you run Spark/AWS?** Answer with actual team evidence. The package provides code/configuration; do not claim a cloud run until you have executed it.
- **What makes this big-data analysis?** Multiple APIs, millions of genuine hourly records, typed/partitioned storage, reproducible transformations and a distributed-processing implementation. Do not inflate the dataset by copying rows.
