# Verification and remaining execution gates

Run the checks from the project root:

```
npm ci
npm run build
npm test
python pipeline/validate_v2.py
python tests/backend_test.py
```

The Node tests cover analytical edge cases and DOM integration with the real React bundle and packaged data. Backend tests start a real local HTTP server and check historical filtering, coordinate validation, unknown locations, compact response schema and the asset allowlist. Dataset validation checks date continuity, unique keys, physical ranges, missingness and provenance labels.

These are not visual browser tests. The available supervised browser preview does not support this project's static development setup; layout and live GPS permissions must also be checked in your own browser. Manual acceptance: open each view on desktop/mobile, change district/date/metric, zoom the map, replay an event, export CSV, search a global location, reject GPS permission once, and confirm graceful handling of a failed provider request.

The local Spark check additionally executes the notebook with Java 17 / Spark 3.5.6 and compares 13 analytical fields against the dashboard across every daily key (`python tests/reconcile_spark.py`). Rainfall is rounded to six decimal places before rank calculations to prevent floating-point artefacts from breaking ties.

Cloud checks require the team's accounts: Terraform validate/plan, an actual Spark notebook run, S3 upload, PostgreSQL upsert and API queries against RDS. Do not mark these as passed until executed. Preserve actual job logs and screenshots for the report. Confirm the daily GitHub Actions workflow and Vercel rebuild once configured.

`dist/data/validation.json` records the bundled dataset's measured verification results. `VALIDATION_RESULTS.txt` records the completed local release checks.
