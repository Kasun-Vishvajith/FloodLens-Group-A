// Native disclosure navigation: immediate feedback, keyboard dismissal and focus return.
const toggle=document.getElementById('nav-toggle');
const navigation=document.getElementById('navigation');
const compact=matchMedia('(max-width: 950px)');
function setOpen(open,restoreFocus=false){
 document.body.classList.toggle('navigation-open',open);
 toggle.setAttribute('aria-expanded',String(open));
 if(restoreFocus)toggle.focus();
}
toggle.addEventListener('click',()=>setOpen(toggle.getAttribute('aria-expanded')!=='true'));
navigation.addEventListener('click',e=>{if(compact.matches&&e.target.closest('[data-route]'))setOpen(false,true)});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&toggle.getAttribute('aria-expanded')==='true')setOpen(false,true)});
document.addEventListener('pointerdown',e=>{if(!e.target.closest('.sidebar'))setOpen(false)});
compact.addEventListener('change',()=>setOpen(false));

// Discover overflow after React renders and after resizing; keep keyboard access local.
let scheduled=false;
function updateScrollHints(){
 scheduled=false;
 document.querySelectorAll('.table-wrap,.forecast-strip,.forecast-chart-scroll').forEach((panel,i)=>{
  const overflowing=panel.scrollWidth>panel.clientWidth+2;
  let hint=panel.previousElementSibling;
  if(!hint?.classList.contains('scroll-hint')){hint=document.createElement('p');hint.className='scroll-hint';hint.id='scroll-hint-'+i;panel.before(hint);}
  const canLeft=panel.scrollLeft>1,canRight=panel.scrollLeft+panel.clientWidth<panel.scrollWidth-2;
  const hintText=canLeft&&canRight?'← More columns on both sides →':canLeft?'← Scroll back for earlier columns':'More dates or columns → Swipe or scroll sideways';
  if(hint.textContent!==hintText)hint.textContent=hintText;hint.hidden=!overflowing;
  panel.tabIndex=overflowing?0:-1;
  panel.setAttribute('role','region');panel.setAttribute('aria-label',panel.classList.contains('table-wrap')?'Data table; scroll horizontally for all columns':'Daily forecast; scroll horizontally for all dates');
  if(!panel.dataset.scrollBound){panel.addEventListener('scroll',scheduleHints,{passive:true});panel.dataset.scrollBound='true';}
 });
}
function scheduleHints(){if(!scheduled){scheduled=true;requestAnimationFrame(updateScrollHints)}}
new MutationObserver(scheduleHints).observe(document.getElementById('content'),{childList:true,subtree:true});
window.addEventListener('resize',scheduleHints);scheduleHints();

// An open tab retains its loaded archive until reload; surface new published dates.
let checkingArchive=false;
async function checkArchiveDate(){
 if(document.hidden||checkingArchive)return;
 const loadedEnd=document.getElementById('end-date').max;
 if(!loadedEnd)return;
 checkingArchive=true;
 try{
  const response=await fetch('data/summary.json',{cache:'no-store',signal:AbortSignal.timeout(10000)});
  if(!response.ok)return;
  const latest=await response.json();
  if(window.floodlensRelease&&latest.release_id!==window.floodlensRelease&&!document.getElementById('archive-update')){
   const banner=document.createElement('div');banner.id='archive-update';banner.className='notice';banner.setAttribute('role','status');
   const text=document.createElement('span');text.textContent=`New historical data is available through ${latest.end}. Reload to update the calendar and charts. `;
   const button=document.createElement('button');button.className='button';button.textContent='Load latest data';button.addEventListener('click',()=>location.reload());
   banner.append(text,button);document.getElementById('global-filters').before(banner);
  }
 }catch{/* Keep the loaded archive usable while offline. */}
 finally{checkingArchive=false;}
}
window.addEventListener('focus',checkArchiveDate);
document.addEventListener('visibilitychange',checkArchiveDate);
setInterval(checkArchiveDate,60000);

