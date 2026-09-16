const pending = new Map();
const PREFIX = 'floodlens-api-v4:';
const TTL = 15 * 60 * 1000;
export async function fetchJSON(url, {force = false} = {}) {
 const remote = String(url).startsWith('https://');
 const key = PREFIX + url;
 if (remote && !force) {
  try { const entry=JSON.parse(localStorage.getItem(key)); if(entry && Date.now()-entry.savedAt<TTL)return entry.value; } catch {}
 }
 if(pending.has(url))return pending.get(url);
 const request=(async()=>{
  const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),30000);
  try {
   const response=await fetch(url,{signal:controller.signal,cache:'no-store'});
   if(!response.ok)throw Error(`Request failed (${response.status}). Try again later.`);
   const value=await response.json();if(value.error)throw Error(value.reason||'Provider unavailable');
   if(remote)try{localStorage.setItem(key,JSON.stringify({savedAt:Date.now(),value}));}catch{}
   return value;
  } finally {clearTimeout(timer);}
 })();pending.set(url,request);
 try{return await request;}finally{pending.delete(url);}
}
