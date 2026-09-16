import {writeFile,mkdir} from 'node:fs/promises';
const tabs=await (await fetch('http://127.0.0.1:9223/json')).json();
const ws=new WebSocket(tabs.find(t=>t.type==='page').webSocketDebuggerUrl);
await new Promise(r=>ws.addEventListener('open',r,{once:true}));
let seq=0;const pending=new Map();
ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(pending.has(m.id)){const {resolve,reject}=pending.get(m.id);pending.delete(m.id);m.error?reject(Error(m.error.message)):resolve(m.result)}});
function call(method,params={}){return new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}))})}
async function evaluate(expression){const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value}
await call('Page.enable');await call('Page.navigate',{url:'http://127.0.0.1:8000/'});
await new Promise(r=>setTimeout(r,2000));
await evaluate("import('./app.js?v=archive-freshness-1').then(m=>m.ready)");
await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
const checks=await evaluate('('+async function(){
 const app=await import('./app.js?v=archive-freshness-1'),out=[],$=id=>document.getElementById(id),sleep=ms=>new Promise(r=>setTimeout(r,ms));
 function check(name,ok){out.push({name,pass:!!ok});}
 const originalFetch=window.fetch;
 const input=(el,value)=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el,value);el.dispatchEvent(new Event('input',{bubbles:true}));};
 app.selectLocation('hanwella');app.navigate('overview');
 $('global-filters').open=true;
 $('location').value='ratnapura';$('location').dispatchEvent(new Event('change',{bubbles:true}));
 check('Global location updates context',app.state.loc==='ratnapura'&&$('global-context').textContent.includes('Ratnapura'));
 document.querySelector('[data-date-preset=month]').click();check('30-day preset',document.getElementById('coverage').textContent.includes('30 daily'));
 $('start-date').value='2026-08-01';$('end-date').value='2026-08-03';$('apply-dates').click();check('Custom range applied',app.state.start==='2026-08-01'&&$('coverage').textContent.includes('3 daily'));
 $('start-date').value='2030-01-01';$('apply-dates').click();check('Invalid range rejected',app.state.start==='2026-08-01'&&!$('notice').hidden);
 document.querySelector('[data-date-preset=month]').click();
 check('Map mounted with district geometry',!!document.querySelector('.leaflet-container .leaflet-overlay-pane path'));
 document.querySelector('.leaflet-control-zoom-in')?.click();$('map-reset')?.click();check('Map controls remain mounted',!!$('map-reset'));
 const row=document.querySelector('.location-row');row.click();check('Ranking selects location',app.state.loc===row.dataset.location);
 app.navigate('history');for(const metric of ['temp','humidity','wind','pressure','rain']){document.querySelector(`[data-metric=${metric}]`).click();check('Historical variable '+metric,app.state.metric===metric&&!!document.querySelector('.chart'));}
 let blob;const originalURL=URL.createObjectURL,originalClick=HTMLAnchorElement.prototype.click;
 URL.createObjectURL=b=>{blob=b;return 'blob:test'};HTMLAnchorElement.prototype.click=function(){};
 $('export').click();const csv=await blob.text();check('CSV actual content matches selection',csv.includes(app.state.loc)&&csv.split('\r\n').length===31);
 URL.createObjectURL=originalURL;HTMLAnchorElement.prototype.click=originalClick;
 $('footer-method').click();check('Methodology opens',$('method-dialog').open);$('close-dialog').click();check('Methodology closes',!$('method-dialog').open);
 app.selectLocation('hanwella');app.navigate('events');const slider=$('replay-range');slider.value='2';slider.dispatchEvent(new Event('input',{bubbles:true}));check('Replay scrubbing',app.state.eventDay===2);
 $('play-replay').click();await sleep(950);check('Replay advances',app.state.eventDay>2);$('play-replay').click();check('Replay pauses',!app.state.playing);
 app.navigate('flood');check('Flood graphs and ranking',document.querySelectorAll('.chart').length>=3&&!!document.querySelector('table'));
 app.navigate('analysis');await sleep(300);const variable=document.querySelector('#content select');variable.value='humidity';variable.dispatchEvent(new Event('change',{bubbles:true}));await sleep(100);check('EDA variable updates',variable.value==='humidity'&&$('content').textContent.includes('Correlation matrix'));
 app.navigate('weather');window.fetch=(url,...args)=>String(url).startsWith('http')?Promise.reject(Error('Simulated offline')):originalFetch(url,...args);
 $('search-place').value='Colombo';$('search-button').click();await sleep(100);check('Search failure actionable',$('search-results').textContent.includes('could not connect'));
 $('refresh').click();await sleep(200);check('Refresh failure retains saved data',!$('refresh').disabled&&$('notice').textContent.includes('failed')&&!!app.state.live.weather.hanwella);
 app.navigate('explore');await sleep(100);let coords=document.querySelectorAll('#content input[type=number]');input(coords[0],'100');await sleep(50);[...document.querySelectorAll('#content button')].find(b=>b.textContent==='Load location').click();await sleep(100);check('Invalid coordinate rejected',$('content').textContent.includes('Enter valid latitude'));
 input(document.querySelector('#content input[type=number]'),'6.927');await sleep(50);[...document.querySelectorAll('#content button')].find(b=>b.textContent==='Load location').click();await sleep(150);check('Explorer provider failure reported',$('content').textContent.includes('unavailable'));
 const originalGPS=navigator.geolocation.getCurrentPosition;navigator.geolocation.getCurrentPosition=(yes,no)=>no({code:1});[...document.querySelectorAll('#content button')].find(b=>b.textContent==='Use my GPS').click();await sleep(100);check('GPS rejection fallback',$('content').textContent.includes('permission denied'));navigator.geolocation.getCurrentPosition=originalGPS;
 window.fetch=originalFetch;
 app.navigate('quality');const links=[...document.querySelectorAll('#content a[download]')];for(const a of links){const response=await fetch(a.href);check('Download asset '+a.getAttribute('href'),response.ok);}
 app.navigate('weather');$('search-place').value='Colombo';$('search-button').click();for(let i=0;i<55&&$('search-button')?.disabled;i++)await sleep(500);
 out.push({name:'Live geocoding',status:$('search-results').textContent.includes('could not connect')?'Provider unavailable':document.querySelector('[data-search-result]')?'Live results returned':'No results',detail:$('search-results').textContent.slice(0,150)});
 if(document.querySelector('[data-search-result]')){
  document.querySelector('[data-search-result]').click();
  for(let i=0;i<55&&!$('method-dialog').open&&!$('notice').textContent.includes('Could not retrieve');i++)await sleep(500);
  out.push({name:'Live searched-location forecast',status:$('method-dialog').open?'Forecast loaded':$('notice').textContent});
  if($('method-dialog').open)$('close-dialog').click();
 }
 $('refresh').click();
 for(let i=0;i<110&&$('refresh').disabled;i++)await sleep(500);
 out.push({name:'Live district weather/flood refresh',status:$('refresh').disabled?'Still pending':app.state.liveError||'Weather and flood providers updated'});
 app.state.liveError='';app.navigate('overview');$('global-filters').open=false;
 return out;
}.toString()+')()');
await mkdir('docs/layout-review',{recursive:true});
await writeFile('docs/layout-review/functionality.json',JSON.stringify(checks,null,2));
console.log(JSON.stringify(checks,null,2));ws.close();
if(checks.some(c=>c.pass===false))process.exitCode=1;






