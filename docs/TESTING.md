# Testing

Run `npm ci` and then `npm test`. The script builds the site and runs:

- `tests/core.test.mjs`: null-safe statistics, threshold levels, stale snapshot exclusion, date-aligned forecast signals, episode grouping, correct ordinal suffixes (`81st`), and logarithmic scatter tick conversion.
- `tests/react.test.mjs`: 25-location × route rendering, EDA and global explorer mounting, invalid date rejection, real-map fallback, filter scope, export scope, forecast date/month transitions, null gaps and unavailable flow handling.
- `python -m unittest discover -s tests -p '*_test.py'`: percentile tie handling, minimum sample policy, rolling windows, score weights, provider timestamp preservation, complete-day aggregation, and atomic release promotion.

`python pipeline/update.py --offline` is an end-to-end data gate. It rebuilds 97,775 daily rows in the bundled release, regenerates EDA and baselines, and runs the independent validator. Network availability is not required for this gate.
