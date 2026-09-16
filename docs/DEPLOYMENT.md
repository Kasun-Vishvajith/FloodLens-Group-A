# Deployment

## Vercel (recommended)

1. Push the project to GitHub, keeping `package.json`, `package-lock.json`, `src/`, `public/`, `pipeline/`, `scripts/`, and `vercel.json`.
2. Import the repository in Vercel. The included configuration runs `npm ci`, `npm run build`, and serves `dist/`.
3. In Vercel, create a Deploy Hook for the production branch. Add its URL to the GitHub repository secret `VERCEL_DEPLOY_HOOK`.
4. Enable the workflow in `.github/workflows/daily-data.yml`. Run it once with **Run workflow** and inspect the uploaded `refresh-evidence` artifact.

The first page load uses the committed release. Location search/GPS calls are made by the browser directly to Open-Meteo and are cached for 15 minutes. Daily permanent updates are performed by GitHub Actions because a static Vercel deployment cannot keep a Python collector running. The workflow is rate-limited below 600 estimated units per minute and serialises requests.

## Local API refresh

```bash
python -m pip install -r requirements.txt
python pipeline/update.py --offline   # recompute full-archive analytics, no network
python pipeline/update.py              # collect recent data and forecasts
npm run build
python serve.py
```

Use `--offline` when demonstrating reproducibility without network access. The online command writes request evidence to `data/request-log.jsonl`, run status to `data/runs/` and `data/refresh-status.json`, and only replaces `public/data/` after validation.

## Optional local Spark evidence

`pipeline/spark_check.py` is a small optional local verification using the published daily CSV. It is not required by the web app and no AWS, RDS, Databricks or Docker service is needed for the Vercel product.
