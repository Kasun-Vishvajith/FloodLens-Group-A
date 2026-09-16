import React from 'react';
import {createRoot} from 'react-dom/client';
import {flushSync} from 'react-dom';
import {Analysis} from './pages/Analysis.jsx';
import {GlobalExplorer} from './pages/Explorer.jsx';
let root;
export function mountView(element,{route,html,summary,location,onLocation}){if(!root)root=createRoot(element);flushSync(()=>root.render(route==='analysis'?<Analysis summary={summary} location={location} onLocation={onLocation}/>:route==='explore'?<GlobalExplorer/>:<div key={route+':'+html.length} dangerouslySetInnerHTML={{__html:html}}/>));}
