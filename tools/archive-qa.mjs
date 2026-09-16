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

const result=await evaluate(`(async()=>{const input=document.getElementById('end-date');const response=await fetch('data/summary.json',{cache:'no-store'});const summary=await response.json();if(input.max!==summary.end)throw Error('Calendar cutoff mismatch');const current=input.max;input.max='2026-09-09';window.dispatchEvent(new Event('focus'));for(let i=0;i<30&&!document.getElementById('archive-update');i++)await new Promise(r=>setTimeout(r,100));const banner=document.getElementById('archive-update');if(!banner||!banner.textContent.includes(summary.end))throw Error('Update notice missing');input.max=current;banner.remove();return {calendarMax:current,noticeVerified:true}})()`);
console.log(JSON.stringify(result));ws.close();
