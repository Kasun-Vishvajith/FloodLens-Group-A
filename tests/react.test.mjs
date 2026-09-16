// DOM integration tests with the real React production bundle and packaged data.
// This is not a visual browser test or a live-provider availability test.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {JSDOM} from 'jsdom';
const dom=new JSDOM(await readFile(new URL('../dist/index.html',import.meta.url),'utf8'),{url:'http://localhost:8000/',pretendToBeVisual:true});
for(const k of ['window','document','navigator','location','localStorage','HTMLElement','Node','Event','MouseEvent'])Object.defineProperty(globalThis,k,{value:dom.window[k],configurable:true});
window.HTMLDialogElement.prototype.showModal=function(){this.open=true};window.HTMLDialogElement.prototype.close=function(){this.open=false};
globalThis.fetch=async url=>{const path=String(url);if(!path.startsWith('data/'))throw Error('Network unavailable in test');const body=await readFile(new URL('../dist/'+path,import.meta.url),'utf8');return {ok:true,json:async()=>JSON.parse(body)}};
const app=await import('../node_modules/.cache/floodlens-test.mjs');await app.ready;
assert.match(document.getElementById('page-title').textContent,/Sri Lanka/);
const summary=JSON.parse(await readFile(new URL('../dist/data/summary.json',import.meta.url),'utf8'));
let combinations=0;
for(const l of summary.locations){app.selectLocation(l.id);for(const route of ['overview','weather','history','flood','events','quality']){app.navigate(route);const content=document.getElementById('content').textContent;assert(content.length>100,`${l.id} ${route}`);assert(!/\bNaN\b|\bundefined\b/.test(content),`${l.id} ${route} invalid content`);combinations++;}}
app.navigate('history');document.getElementById('start-date').value='2010-01-01';document.getElementById('apply-dates').click();assert.match(document.getElementById('notice').textContent,/valid range/);
app.navigate('analysis');await new Promise(r=>setTimeout(r,100));assert.match(document.getElementById('content').textContent,/Correlation matrix/);assert.match(document.getElementById('content').textContent,/Monsoon comparison/);
app.navigate('explore');assert.match(document.getElementById('content').textContent,/Use my GPS/);const inputs=[...document.querySelectorAll('#content input[type=number]')];inputs[0].value='100';inputs[0].dispatchEvent(new Event('input',{bubbles:true}));
assert.equal(document.querySelectorAll('#content input[type=number]').length,2);
app.navigate('overview');assert.match(document.getElementById('content').innerHTML,/geographic-fallback/);
console.log(`PASS: ${combinations} location/view renders, React EDA/global route mounting, invalid dates, geographic fallback`);
assert.equal(document.querySelectorAll('#global-filters').length,1);
assert(!document.getElementById('main').contains(document.getElementById('location')));
app.selectLocation('hanwella');app.navigate('weather');assert.match(document.getElementById('global-context').textContent,/Hanwella.*Provider forecast/);
app.navigate('analysis');assert.match(document.getElementById('global-context').textContent,/Full archive/);
app.navigate('explore');assert.match(document.getElementById('filter-scope').textContent,/own search/);
app.navigate('overview');assert.match(document.getElementById('global-context').textContent,/Hanwella/);
assert.match(document.getElementById('update-feedback').textContent,/Updated/);assert.equal(document.getElementById('global-filters').open,false);
console.log('PASS: single global filter, retained location and route-specific scope');
app.navigate('analysis');assert.match(document.getElementById('export-context').textContent,/2016/);
assert.match(document.getElementById('export-context').textContent,/not an analysis report/);
app.navigate('weather');assert.match(document.getElementById('export').textContent,/forecast CSV/);
app.navigate('explore');assert(document.getElementById('export').hidden);
app.selectLocation('trincomalee');app.navigate('overview');assert.match(document.getElementById('location-context').textContent,/unavailable at this point/);
console.log('PASS: export scope, full archive labels, independent explorer and unavailable river context');
const sampleDates=['2026-12-30','2026-12-31','2027-01-01','2027-01-02','2027-02-01'];
const plotted=document.createElement('div');
plotted.innerHTML=app.chart([{name:'Forecast rainfall',points:sampleDates.map((d,i)=>({d,v:i===3?null:i}))}],{unit:'mm'});
assert.equal(plotted.querySelectorAll('.forecast-date').length,5);
assert.equal(plotted.querySelectorAll('.forecast-point').length,4);
assert.deepEqual([...plotted.querySelectorAll('.forecast-date')].map(e=>[...e.children].map(t=>t.textContent)),[['30','Dec','2026'],['31'],['01','Jan','2027'],['02'],['01','Feb']]);
assert.match(plotted.querySelector('.forecast-point').getAttribute('aria-label'),/2026-12-30, 0\.0 mm/);
console.log('PASS: every forecast date, month/year transitions, zero marker and null gap');
dom.window.close();





