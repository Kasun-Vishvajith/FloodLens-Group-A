export const finite = x => typeof x === 'number' && Number.isFinite(x);
export const sum = a => {const b=a.filter(finite);return b.length?b.reduce((x,y)=>x+y,0):null;};
export const mean = a => {const b=a.filter(finite);return b.length?sum(b)/b.length:null;};
export const maximum = a => {const b=a.filter(finite);return b.length?Math.max(...b):null;};
export const fmt = (n,d=1) => finite(n)?n.toLocaleString('en-US',{maximumFractionDigits:d,minimumFractionDigits:d}):'—';
export const esc = s => String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const dateLabel = d => d?new Date(d+'T00:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'}):'—';
export const severity = p => !finite(p)?-1:p>=99?2:p>=95?1:0;
export function rankReason(row){
 const pairs=[['river discharge',row?.qp],['3-day rainfall',row?.rp],['maximum temperature',row?.tp],['wind speed',row?.wp]].filter(x=>finite(x[1]));
 return pairs.sort((a,b)=>b[1]-a[1])[0]??['insufficient data',null];
}
export function monthly(rows,key){const groups=new Map();for(const r of rows){let k=r.date.slice(0,7);if(!groups.has(k))groups.set(k,[]);groups.get(k).push(r[key]);}return [...groups].map(([date,v])=>({date:date+'-01',value:key==='rain'?sum(v):mean(v)}));}
export function episodes(rows,threshold=99,kind='flood'){
 const out=[];let current=null;
 for(const row of rows){const p=kind==='heat'?row.tp:kind==='wind'?row.wp:kind==='rain'?row.rp:maximum([row.qp,row.rp]);
  if(finite(p)&&p>=threshold){if(!current){current={start:row.date,end:row.date,days:0,peak:0,peakDate:row.date};out.push(current);}current.days++;current.end=row.date;const v=kind==='heat'?row.tmax:kind==='wind'?row.wind:kind==='rain'?row.r3:(row.q??row.r3);if(finite(v)&&v>current.peak){current.peak=v;current.peakDate=row.date;}}
  else current=null;
 }return out.sort((a,b)=>b.days-a.days||b.peak-a.peak);
}
// Forecast interpretation uses provider values and fixed historical thresholds.
export function thresholdLevel(value, baseline){
 if(!finite(value)||!baseline||baseline.n<30||!finite(baseline.p95))return -1;
 if(value<=0)return 0;
 if(finite(baseline.p99)&&baseline.p99>0&&value>=baseline.p99)return 2;
 return baseline.p95>0&&value>=baseline.p95?1:0;
}
export const snapshotFresh = (stamp, now=Date.now()) => !!stamp && Number.isFinite(Date.parse(stamp)) && now-Date.parse(stamp)<86400000 && Date.parse(stamp)<=now+300000;
export function forecastSignals(weather, flood, base, {weatherFresh=true,floodFresh=true}={}){
 const wd=weather?.daily,fd=flood?.daily;
 const dates=[...new Set([...(wd?.time||[]),...(fd?.time||[])])].sort();
 return dates.map(date=>{
  const wi=wd?.time.indexOf(date)??-1,fi=fd?.time.indexOf(date)??-1,m=String(Number(date.slice(5,7)));
  const rain=wi>=0?wd.precipitation_sum?.[wi]:null,q=fi>=0?fd.river_discharge_median?.[fi]:null;
  const rainLevel=weatherFresh?thresholdLevel(rain,base?.rain?.[m]):-1;
  const flowLevel=floodFresh?thresholdLevel(q,base?.q?.[m]):-1;
  return {date,rain,q,rainLevel,flowLevel,level:Math.max(rainLevel,flowLevel),rainP95:base?.rain?.[m]?.p95??null,flowP95:base?.q?.[m]?.p95??null,p25:fi>=0?fd.river_discharge_p25?.[fi]:null,p75:fi>=0?fd.river_discharge_p75?.[fi]:null};
 });
}
