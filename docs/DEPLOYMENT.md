# Deployment

See `CLOUD_SETUP.md` for the complete Vercel, FastAPI, PostgreSQL, Databricks and AWS instructions.

For a quick local demonstration: extract the project and run `python serve.py` or `START_WINDOWS.bat`. Use Python 3.12. No dependency installation is needed to view the packaged static dashboard.

For Vercel: import the project, choose Other, build `npm run build`, output `dist`; use Node 20+. Keep `dist/config.js` API base empty unless you have deployed an HTTPS FastAPI service. API/database credentials never belong in frontend config.

A Vercel frontend deployment does not run the historical collector, Spark, RDS or a daily scheduler. Enable `.github/workflows/daily-data.yml` in your GitHub repository. Configure VERCEL_DEPLOY_HOOK if Git-based deploys do not already trigger after data commits. First use workflow_dispatch and confirm its successful run before relying on the schedule.

To connect FastAPI, set `apiBase` in `dist/config.js` to your API HTTPS origin and configure that frontend origin in FRONTEND_ORIGINS on the backend. Validate `/api/health`, `/api/summary`, `/api/history/hanwella` and `/docs` before deploying the frontend config change.
