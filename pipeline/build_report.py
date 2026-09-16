"""Rebuild the release report and its scientific plots from published data."""
import json,calendar,html
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs';FIG=DOC/'figures';FIG.mkdir(exist_ok=True)
s=json.loads((ROOT/'dist/data/summary.json').read_text());current=json.loads((ROOT/'dist/data/current.json').read_text())
base=json.loads((ROOT/'dist/data/baselines.json').read_text())
def frame(lid):
 j=json.loads((ROOT/'dist/data'/f'{lid}.json').read_text());d=pd.DataFrame(j['rows'],columns=j['columns']);d['date']=pd.to_datetime(d.date);return d
frames={l['id']:frame(l['id']) for l in s['locations']}
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#315367','xtick.color':'#315367','ytick.color':'#315367','axes.edgecolor':'#c6d6df','grid.color':'#e4eaee','figure.facecolor':'white'})
def finish(fig,name):
 fig.tight_layout();fig.savefig(FIG/name,dpi=175,bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(figsize=(9,3.8))
for lid,c in [('ratnapura','#07868b'),('jaffna','#3b7aba'),('batticaloa','#ca8d22')]:
 d=frames[lid];b=d[d.date<'2021-01-01'];v=b.groupby(b.date.dt.month).rain.mean();ax.plot(v.index,v.values,'o-',label=next(l['name'] for l in s['locations'] if l['id']==lid),color=c)
ax.set(xlabel='Calendar month',ylabel='Mean daily rainfall (mm)',xticks=range(1,13));ax.grid(axis='y');ax.legend(frameon=False,ncol=3);finish(fig,'seasonality.png')
# Use one reproducible historical event: highest modelled flow after the baseline.
ev=max((e for e in s['events'] if e.get('peak_q') is not None),key=lambda e:e['peak_q'])
el=next(l for l in s['locations'] if l['id']==ev['location_id']);d=frames[el['id']];peak=pd.Timestamp(ev['peak_date']);g=d[d.date.between(peak-pd.Timedelta(days=8),peak+pd.Timedelta(days=8))]
fig,axs=plt.subplots(2,1,figsize=(9,5),sharex=True);axs[0].bar(g.date,g.rain,color='#74bcc0');axs[0].set_ylabel('Daily rainfall (mm)');axs[1].plot(g.date,g.q,color='#07868b',label='GloFAS modelled discharge');axs[1].set_ylabel('Discharge (m³/s)');axs[1].legend(frameon=False);axs[1].tick_params(axis='x',rotation=35)
for ax in axs:ax.grid(axis='y')
finish(fig,'event.png')
fig,ax=plt.subplots(figsize=(8.5,3.6));ax.plot([b['rows']/1e6 for b in s['benchmarks']],[b['seconds_median'] for b in s['benchmarks']],'o-',color='#07868b');ax.set(xlabel='Actual hourly records (millions)',ylabel='Median SQL query time (seconds)');ax.grid();finish(fig,'benchmark.png')
lid='ratnapura';wd=current['weather'][lid]['daily'];fd=current['flood'][lid]['daily'];dates=pd.to_datetime(wd['time']);qdates=pd.to_datetime(fd['time'])
fig,axs=plt.subplots(2,1,figsize=(9,4.5),sharex=True);axs[0].bar(dates,wd['precipitation_sum'],color='#72bac0');axs[0].set_ylabel('Forecast rain (mm)');axs[1].plot(qdates,fd['river_discharge_median'],color='#07868b',label='GloFAS median');axs[1].fill_between(qdates,fd['river_discharge_p25'],fd['river_discharge_p75'],color='#72bac0',alpha=.25,label='25th-75th ensemble');axs[1].set_ylabel('Flow (m³/s)');axs[1].tick_params(axis='x',rotation=30);axs[1].legend(frameon=False)
for ax in axs:ax.grid(axis='y')
finish(fig,'forecast.png')
# Geographic data plot, using the actual supplied district coordinates.
geo=json.loads((ROOT/'dist/data/districts.geojson').read_text());fig,ax=plt.subplots(figsize=(5,6))
for feature in geo['features']:
 geometry=feature['geometry'];polys=[geometry['coordinates']] if geometry['type']=='Polygon' else geometry['coordinates']
 for poly in polys:
  for ring in poly:
   xy=np.array(ring);ax.plot(xy[:,0],xy[:,1],color='#8ba5b0',linewidth=.45)
ax.scatter([l['lon'] for l in s['locations']],[l['lat'] for l in s['locations']],s=22,c=['#07868b' if l['river'] else '#c48d29' for l in s['locations']],zorder=3)
ax.set_aspect(1/np.cos(np.deg2rad(7.8)));ax.set(xlabel='Longitude',ylabel='Latitude');ax.set_title('Sri Lanka: actual district boundaries');finish(fig,'map.png')
# Additional EDA figures use the actual daily dataset.
eda=json.loads((ROOT/'dist/data/eda.json').read_text());rain=frames['ratnapura'].rain.dropna()
fig,axs=plt.subplots(1,2,figsize=(9,3.5));axs[0].hist(rain,bins=20,color='#11868a',edgecolor='white');axs[0].set(xlabel='Daily rainfall (mm)',ylabel='Valid days',title='Ratnapura rainfall distribution')
keys=['rain','temp','humidity','wind','pressure','q'];cm=frames['ratnapura'][keys].corr(min_periods=30);im=axs[1].imshow(cm,vmin=-1,vmax=1,cmap='BrBG');axs[1].set(xticks=range(6),yticks=range(6),xticklabels=keys,yticklabels=keys,title='Paired daily Pearson correlation');axs[1].tick_params(axis='x',rotation=45);fig.colorbar(im,ax=axs[1],shrink=.7);finish(fig,'eda.png')

# Store reproducible facts for the slide edit.
facts={'summary':s,'event':{**ev,'location_name':el['name']},'forecast':{'location':'Ratnapura','start':wd['time'][0],'end':wd['time'][-1],'rain_total':sum(x for x in wd['precipitation_sum'] if x is not None),'peak_flow':max(x for x in fd['river_discharge_median'] if x is not None),'retrieved_at':current['retrieved_at']}}
(DOC/'presentation-facts.json').write_text(json.dumps(facts,indent=2))
for name,file in [('DejaVu','DejaVuSans.ttf'),('DejaVu-Bold','DejaVuSans-Bold.ttf')]:pdfmetrics.registerFont(TTFont(name,str(ROOT/'pipeline/fonts'/file)))
styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodyX',fontName='DejaVu',fontSize=10,leading=15,spaceAfter=11,textColor=colors.HexColor('#18394b')));styles.add(ParagraphStyle(name='TitleX',fontName='DejaVu-Bold',fontSize=25,leading=31,spaceAfter=18,textColor=colors.HexColor('#103a54')));styles.add(ParagraphStyle(name='HeadX',fontName='DejaVu-Bold',fontSize=16,leading=22,spaceAfter=12,textColor=colors.HexColor('#087f83')));styles.add(ParagraphStyle(name='SmallX',fontName='DejaVu',fontSize=8,leading=12,spaceAfter=9))
story=[];md=['# FloodLens Sri Lanka - DS 4004 final report','Release date: '+s['as_of']]
def para(t,style='BodyX'):story.append(Paragraph(t,styles[style]));md.append(t.replace('<b>','**').replace('</b>','**'))
def heading(t):para(t,'HeadX')
def page(title):
 if story:story.append(PageBreak())
 para(title,'TitleX')
def table(rows,widths=None):
 md.append('\n'.join(['| '+' | '.join(str(c) for c in rows[0])+' |','| '+' | '.join('---' for _ in rows[0])+' |']+['| '+' | '.join(str(c) for c in r)+' |' for r in rows[1:]]))
 data=[[Paragraph(html.escape(str(c)),styles['SmallX']) for c in row] for row in rows];t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5f0f1')),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#a5bfc8')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7)]));story.append(t);story.append(Spacer(1,12))
def picture(name,w=480):
 from PIL import Image as PI
 im=PI.open(FIG/name);story.append(Image(str(FIG/name),width=w,height=w*im.height/im.width));story.append(Spacer(1,10))
page('FloodLens Sri Lanka')
para('Flood and Extreme Weather Analytics','HeadX');para('DS 4004 · Group A · Option 3<br/>Release: '+s['as_of'])
para('This project collects, processes and visualizes historical weather and modelled river discharge for Sri Lanka. It identifies unusual conditions at sampled locations and interprets upcoming weather and river-flow forecasts supplied by Open-Meteo. No forecasting model is fitted by the project.')
table([['Release evidence','Value'],['Historical dates',s['start']+' to '+s['end']],['Hourly weather records',f"{s['hourly_rows']:,}"],['Daily analytical records',f"{s['daily_rows']:,}"],['Valid daily flow values',f"{s['flood_rows']:,}"],['Monitoring points',str(len(s['locations']))+' districts; '+str(sum(l.get('valid_q',0)>0 for l in s['locations']))+' with valid flow'],['Reference period','2016-2020, month-specific'],['Prediction source','Weather Forecast API and GloFAS Flood API']],[220,260])
para('The result is a React-based, deployable dashboard with an optional FastAPI service with real geographic boundaries, interactive filters, a historical explorer, flood indicators, event replay, forecast interpretation and CSV exports. A separate incremental pipeline updates the shared data.')
para('Group A: Kasun Vishvajith · Akindu Liyanage · Yasuri Fernando. Add registration numbers and a verified contribution log before submission.','SmallX')
page('1. Scope and data sources')
para('The assignment requires real-time and historical API data, exploratory analysis of five indicators, efficient storage, user inputs, an interactive dashboard, and Option 3 analyses of extreme conditions and priority regions. It mentions forecasting but does not mandate fitting a prediction model.')
table([['Product','Role and limitation'],['ERA5 historical weather','Hourly historical weather; recent publication lag requires a labelled IFS tail.'],['ECMWF IFS','Recent historical weather until ERA5 becomes available; a different product and resolution.'],['GloFAS discharge','Modelled daily flow; consolidated history followed by the default seamless API, which can include forecast-backed records.'],['Weather Forecast API','Current conditions and 16-day weather outlook, including rain probability.'],['GloFAS forecast','Ensemble median, 25th and 75th percentiles of daily river flow.'],['Geocoding API','Global place search; coordinates and GPS also select locations. Custom places have live data, not precomputed historical baselines.']],[135,345])
para('Historical coverage ends on '+s['end']+' UTC, the latest completed day targeted by this build. Forecast records are stored separately. Retrieval timestamps and source-product changes remain visible.')
table([['Variable','Unit','Daily transformation'],['Precipitation','mm','Sum; all 24 hours required'],['Temperature','degrees C','Mean and maximum; all 24 hours required'],['Relative humidity','%','Mean; all 24 hours required'],['Wind speed','km/h','Maximum; all 24 hours required'],['Sea-level pressure','hPa','Mean; all 24 hours required'],['River discharge','m³/s','Daily modelled value, not an hourly sum']],[145,75,260])
page('2. Geographic coverage')
picture('map.png',260)
para('Twenty-five district reference points cover all nine provinces and all 25 districts. Available discharge points sample nearby modelled channels. Returned API grid coordinates can differ from requested coordinates. A marker is a sampled point, not a district average or a catchment measurement.')
para('Map geometry: geoBoundaries LKA ADM2, 25 districts, source representation year 2017, build December 2023. Source: OpenStreetMap/Wambacher, ODbL 1.0. The web map uses Leaflet and attributed OpenStreetMap tiles. Bundled district geometry remains available without remote tiles.','SmallX')
page('3. Analytical methodology')
heading('Quality and transformations')
para('Hourly records are indexed by location and timestamp. Daily frames are reindexed to consecutive UTC dates before rolling calculations. Missing values remain missing; no synthetic records or zero-filled measurements are introduced. Range checks cover precipitation, wind, discharge, humidity and percentile bounds.')
heading('Seasonal baseline and events')
para('For each location and calendar month, the reference distribution uses 2016-2020 values. We calculate a midrank percentile, 100 × (count below + 0.5 × count equal) / reference count. This treats repeated zero values fairly. Baseline thresholds use the 50th, 95th and 99th quantiles.')
para('Historical severity uses the largest available percentile among 3-day rainfall, modelled flow, daily maximum temperature and wind. Values at or above the 95th percentile are elevated; values at or above the 99th are unusual. Missing indicators do not automatically imply typical conditions.')
para('Consecutive unusual days form episodes. The event view explores episodes from 2021 onward, after the baseline period, with rainfall, flow and surrounding days. The user can also choose heat or wind episodes. No episode is claimed to be an independently confirmed flood disaster.')
heading('Regional comparison and lag analysis')
para('Priority points are ranked by the proportion of valid days with unusual rainfall or flow. A separate count shows days when both are elevated. District labels provide geographic context without implying area-wide measurements. The latest-day 0-100 screening score combines 50% flood severity, 30% 3-day rainfall percentile and 20% unusual weather percentile; unavailable components are omitted and the remaining weights are rescaled and labelled. Lag correlations compare local rainfall with later flow after subtracting monthly seasonal means; these are exploratory associations, not causal estimates.')
page('4. Exploratory weather findings')
picture('seasonality.png')
para('The chart compares mean daily rainfall for the same baseline years at Ratnapura, Jaffna and Batticaloa. It demonstrates why a single nationwide rainfall threshold can hide seasonal and geographic differences. The dashboard repeats this exploration for temperature, humidity, wind and pressure.')
para('Monthly rainfall plots show the sum of available complete daily totals. Other monthly plots show the mean of daily summaries. The valid-day count is displayed so incomplete periods can be recognized. Comparing a partial year against a full year without adjustment is inappropriate.')
para('These are point-level modelled weather patterns. The five-year baseline supports this project’s exploratory comparisons but is shorter than a formal multi-decade climate normal. Changes in source products can also affect apparent trends.')
page('EDA: distributions and monsoons')
picture('eda.png')
para('The histogram shows the distribution of real daily rainfall at Ratnapura. The matrix uses pairwise complete daily records and includes rainfall, temperature, humidity, wind, pressure and modelled discharge. Seasonality and serial dependence can affect these associations.')
table([['Ratnapura season','Valid rain days','Mean rain mm/day','Mean flow m³/s'],*[[x['season'],x['rain_days'],f"{x['rain_mean']:.2f}" if x['rain_mean'] is not None else 'Missing',f"{x['flow_mean']:.2f}" if x['flow_mean'] is not None else 'Missing'] for x in eda['locations']['ratnapura']['monsoons']]],[150,100,115,115])
para('Southwest monsoon months are May-September; northeast months are November-January. This full-archive comparison uses daily means rather than unequal-length seasonal totals. The dashboard also presents yearly unusual-day counts and rates, explicitly marking partial years.')

page('5. Flood-related event example')
picture('event.png')
para(f"Selected event: <b>{el['name']}</b>, with peak modelled flow on <b>{ev['peak_date']}</b>. The recorded peak is <b>{ev['peak_q']:.2f} m³/s</b>. The plot displays the surrounding rainfall and discharge using separate axes and units.")
para('Replay connects the timing of local rainfall and river response. Upstream rainfall, routing, reservoir operations and model assumptions may explain differences; local rainfall alone is not a complete catchment input. The event selection is reproducible from the published episode list, not a claim of observed damage.')
page('6. API forecasts and upcoming signals')
picture('forecast.png')
para(f"Ratnapura forecast snapshot: {wd['time'][0]} to {wd['time'][-1]}; retrieved {current['retrieved_at']}. Forecast rain totals {facts['forecast']['rain_total']:.1f} mm across these dates. The graph shows the ensemble median and middle 50% of flow members.")
para('The project uses the forecast values directly. A watch flag is triggered at the location’s monthly historical 95th percentile; a high flag at its 99th percentile. Rainfall and flow are assessed separately. Missing values, inadequate reference samples and snapshots older than 24 hours do not generate forecast flags.')
para('Ensemble spread is variation among model members, not a calibrated flood probability. Forecast and historical products can have different grids and biases. These threshold comparisons are exploratory and require gauge/event validation before operational use.')
page('7. Engineering and measured performance')
picture('benchmark.png')
para('The collection pipeline caches original responses with source URLs and retrieval times. The release packages hourly compressed CSV and reproducible Parquet conversion. Spark processes typed records in Databricks; S3 upload and PostgreSQL loading scripts support the proposed cloud path. The local SQLite benchmark below is measured; it is not evidence of a Spark or AWS run. Prepared daily JSON keeps the static frontend lightweight.')
table([['Actual records','Median query time'],*[[f"{b['rows']:,}",f"{b['seconds_median']:.3f} seconds"] for b in s['benchmarks']]],[240,240])
para('The query groups hourly rainfall and temperature by location and month. Each size is timed three times; the chart reports the median. These single-machine measurements describe this build, not the user’s hardware or a distributed cluster.')
spark_path=ROOT/'dist/data/spark-validation.json'
if spark_path.exists():
 sv=json.loads(spark_path.read_text());para(f"Local Spark verification: version {sv['spark_version']}, {sv['master']}, {sv['driver_memory']} driver memory. The same notebook produced {sv['daily_rows']:,} unique daily records in {sv['elapsed_seconds']:.1f} seconds. This is a local Spark run, not a Databricks cloud execution.")
para('Daily updates refresh the recent 14 days, rerun analysis and validation, save forecast snapshots, and publish updated data through the supplied GitHub Actions/Vercel workflow once configured. A website deployment alone does not enable that schedule.')

page('8. Cloud architecture and reproducibility')
para('React frontend → FastAPI → PostgreSQL forms the connected application path. The static edition can also display packaged analytics without a backend. Python collects APIs, Spark cleans and aggregates data, Parquet preserves typed source records, S3 stores objects and RDS hosts PostgreSQL.')
table([['Component','Delivered implementation / execution boundary'],['React + FastAPI','Built React components and a read-only API with validated coordinates, fixed upstream hosts and cached requests.'],['Parquet + S3','Compressed Parquet exporter and authenticated S3 publisher. Local hourly partitions use district/year; Spark daily output uses district/date.'],['Spark / Databricks','Importable notebook with cleaning, complete-day aggregation, rolling rainfall, percentile flags and monsoon summaries. Team cloud execution required.'],['PostgreSQL / RDS','Schema, idempotent loader, Docker configuration and private encrypted RDS Terraform configuration. AWS account execution required.'],['Daily refresh','GitHub Actions workflow; must be enabled in the team repository and connected to deployment.']],[135,345])
para('Databricks Free Edition restricts external network access. Uploading source Parquet into a Unity Catalog volume is the free-compatible processing path. Direct S3/RDS access requires permitted storage/network configuration. AWS student credits do not guarantee a zero bill.')
heading('Correction to the proposal')
para('The Open-Meteo Flood API does not expose 2-, 5- or 20-year return-period thresholds. Its p25/p75 variables are ensemble statistics. This implementation uses labelled historical percentile screening and does not equate it with return periods. A verified external threshold source would require a declared scope change.')
para('Cloud provisioning and Databricks execution have not been performed in the team accounts. The final submission should include actual job results and screenshots once the team runs these components. Never present the local SQL benchmark as distributed-processing evidence.')

page('9. Conclusions, limits and references')
para('FloodLens meets the chosen direction by combining flood and weather APIs, identifying unusual conditions, comparing priority locations and presenting historical context alongside provider forecasts. Its contribution is a transparent, reproducible analytical application rather than a newly trained forecasting model.')
para('Main limits: point sampling; unverified model-channel identity; reanalysis and forecast-product changes; a short baseline; no labelled flood-event ground truth; no exposure/vulnerability data; and service availability or scheduling delays. The dashboard is a research tool, not an official warning service.')
heading('Assignment deliverables and team evidence')
para('The package contains source code, data, a deployable dashboard, report, presentation, validation scripts, deployment steps and contribution guidance. Each member should record actual decisions and verification in a contribution log and rehearse the demonstration.')
heading('References and attribution')
for line in ['Course brief: DS 4004 Group Project 2026, supplied PDF, pages 1-2.','Open-Meteo historical weather: https://open-meteo.com/en/docs/historical-weather-api','Open-Meteo Forecast API: https://open-meteo.com/en/docs','Open-Meteo Flood API: https://open-meteo.com/en/docs/flood-api','Open-Meteo Geocoding: https://open-meteo.com/en/docs/geocoding-api','Open-Meteo Elevation: https://open-meteo.com/en/docs/elevation-api','Databricks limits: https://docs.databricks.com/aws/en/getting-started/free-edition-limitations','API limits and attribution: https://open-meteo.com/en/pricing','District geometry: https://www.geoboundaries.org/api/current/gbOpen/LKA/ADM2/','OpenStreetMap licence: https://www.openstreetmap.org/copyright','Leaflet: https://leafletjs.com/']:
 para(html.escape(line),'SmallX')
para('Credit Open-Meteo, ECMWF ERA5/IFS and Copernicus EMS GloFAS for weather/flow data. CC BY 4.0 attribution applies. Retain the separate map-source attribution and included Leaflet licence.','SmallX')
def footer(canvas,doc):
 canvas.setFont('DejaVu',8);canvas.setFillColor(colors.HexColor('#647e8c'));canvas.drawString(42,25,'FloodLens Sri Lanka | DS 4004 | release '+s['as_of']);canvas.drawRightString(553,25,str(doc.page))
SimpleDocTemplate(str(DOC/'FloodLens-Report.pdf'),pagesize=(595,842),rightMargin=48,leftMargin=48,topMargin=42,bottomMargin=46,title='FloodLens Sri Lanka - Final Report',author='DS 4004 project team').build(story,onFirstPage=footer,onLaterPages=footer)
(DOC/'REPORT.md').write_text('\n\n'.join(md))
print('Report and figures generated.')
