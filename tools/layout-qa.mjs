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
await mkdir('docs/layout-review',{recursive:true});
const results=[];
for(const width of [1440,1024,768,390,320]){
 await call('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:width<500});
 for(const route of ['overview','weather','history','flood','events','analysis','explore','quality']){
  await evaluate(`import('./app.js?v=archive-freshness-1').then(m=>m.navigate('${route}'))`);
  await new Promise(r=>setTimeout(r,250));
  const result=await evaluate(`(()=>{const grids=[...document.querySelectorAll('.workspace-grid,.two-grid,.bottom-grid,.replay-layout')];return {width:innerWidth,scroll:document.documentElement.scrollWidth,misaligned:grids.filter(g=>getComputedStyle(g).gridTemplateColumns.split(' ').length===2).flatMap(g=>{const a=[...g.children].map(c=>c.getBoundingClientRect());return a.length===2&&Math.abs(a[0].top-a[1].top)>1?[g.className]:[]}),overflow:[...document.querySelectorAll('main *,header *')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.right>innerWidth+1&&!e.closest('.table-wrap,.forecast-strip,.forecast-chart-scroll,.leaflet-container,.map-toolbar,.metric-tabs')}).slice(0,8).map(e=>e.className||e.tagName)}})()`);
  results.push({route,...result});
  if([1440,390].includes(width)){
   const shot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
   await writeFile(`docs/layout-review/${route}-${width}.png`,Buffer.from(shot.data,'base64'));
  }
 }
}
await writeFile('docs/layout-review/results.json',JSON.stringify(results,null,2));
console.log(JSON.stringify(results.filter(r=>r.scroll>r.width||r.misaligned.length||r.overflow.length),null,2));
console.log(`${results.length} route/viewport checks completed`);
const menu=await evaluate(`(()=>{const t=document.getElementById('nav-toggle'),n=document.getElementById('navigation');t.click();const opened=t.getAttribute('aria-expanded')==='true'&&getComputedStyle(n).display!=='none';document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));const dismissed=t.getAttribute('aria-expanded')==='false'&&document.activeElement===t;t.click();n.querySelector('[data-route=overview]').click();return {opened,dismissed,selected:document.body.dataset.view==='overview'&&t.getAttribute('aria-expanded')==='false',overflow:document.documentElement.scrollWidth>innerWidth}})()`);
if(!menu.opened||!menu.dismissed||!menu.selected||menu.overflow)throw Error('Mobile navigation failed: '+JSON.stringify(menu));
await call('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'},{name:'prefers-reduced-transparency',value:'reduce'}]});
const accessibility=await evaluate(`({motion:getComputedStyle(document.getElementById('nav-toggle')).transitionDuration,material:getComputedStyle(document.querySelector('.sidebar')).backdropFilter})`);
if(accessibility.motion!=='0s'||accessibility.material!=='none')throw Error('Accessibility preferences failed: '+JSON.stringify(accessibility));
await call('Emulation.setEmulatedMedia',{features:[]});
await writeFile('docs/layout-review/interactions.json',JSON.stringify({menu,accessibility},null,2));
console.log('PASS: mobile menu, Escape focus return, route selection, reduced motion and transparency');ws.close();




