"""Write the short factsheet used by the project guide and release review."""
import json
from pathlib import Path
from config import ROOT, DATA

def main():
    summary=json.loads((DATA/'summary.json').read_text())
    validation=json.loads((DATA/'validation.json').read_text()) if (DATA/'validation.json').exists() else {}
    lines=['# FloodLens release report','',f"Generated from release **{summary.get('release_id','unknown')}**.",'',
           '## Coverage','',f"- Archive: **{summary.get('start')} to {summary.get('end')}** (UTC daily records).",f"- Reference locations: **{len(summary.get('locations',[]))}** Sri Lankan districts / monitoring points.",f"- Daily rows: **{summary.get('daily_rows',0):,}**; valid discharge rows: **{summary.get('flood_rows',0):,}**.",f"- Original hourly evidence: **{summary.get('original_hourly_rows',summary.get('hourly_rows',0)):,}** rows (the compact deployable release stores daily data).",f"- Detected episodes: **{summary.get('event_count',0):,}** using the 99th-percentile signal rule.",'', '## Validation','',f"- Status: **{validation.get('status','not run')}**.",f"- Checks: {', '.join(validation.get('checks',[]))}.",f"- Missing flow by location is retained in `public/data/validation.json` rather than being imputed.",'', '## Interpretation','', 'The score is an exploratory screening index. It is not a calibrated probability, an inundation map, or an official warning. Forecasts are provider values from Open-Meteo; the project does not train a machine-learning model.', '', '## Refresh','', 'GitHub Actions runs `pipeline/update.py` daily. A successful staged release is validated, committed to the repository, and can trigger a Vercel deploy hook.']
    (ROOT/'docs'/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Wrote docs/REPORT.md')
if __name__=='__main__':main()
