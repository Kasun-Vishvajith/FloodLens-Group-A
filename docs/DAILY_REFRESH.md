# Daily updates and interaction feedback

The Codex thread automation `refresh-floodlens-daily` is active at 07:05 Asia/Colombo daily. It runs `pipeline/refresh_daily.py` using the available Python runtime. This is a local desktop automation, not an always-on cloud deployment: the computer/app must be available. Existing GitHub workflow scheduling is supplied separately but has not been enabled or verified on a remote repository here.

The runner executes ingestion, analytics, current forecasts, EDA and validation sequentially. It records the current stage and completion/failure in `data/refresh-status.json` and refuses overlapping runs using `data/.daily-refresh.lock`. Check the PID before removing a lock left by a terminated process. API availability and quotas may delay updates.

Historical days are UTC: a September 16 run requests completed history through September 15. September 16 conditions and forecasts come from the provider separately. A September 17 run requests completed history through September 16. Missing values remain null. Failed flood refreshes preserve the older flood snapshot and its original retrieval timestamp.

Completed manual refresh on September 16: all 25 reference locations, 2,346,600 hourly rows and 97,775 daily rows, January 1 2016 through September 15 2026. Weather forecasts refreshed for all 25 locations; two points still have missing flow. EDA and dataset validation passed. Report/slides have not been regenerated.

Changing a reference location, applying dates or choosing a quick range now closes the filter disclosure and announces the applied context in a five-second status message. Content gets a short opacity transition; reduced-motion users receive static status feedback. No artificial data-loading delay is introduced for locally available data.
