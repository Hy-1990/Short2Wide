import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
class Element {
 constructor(){this.listeners={};this.attrs={};this.classList={toggle(){}};this.hidden=false;this.value='';this.children=[];this.dataset={};this.textContent=''}
 addEventListener(name,handler){(this.listeners[name]??=[]).push(handler)}
 removeEventListener(name,handler){this.listeners[name]=(this.listeners[name]||[]).filter(x=>x!==handler)}
 dispatch(name){for(const fn of [...this.listeners[name]||[]])fn({target:this})}
 setAttribute(k,v){this.attrs[k]=v}getAttribute(k){return this.attrs[k]}
 append(...nodes){this.children.push(...nodes)}replaceChildren(...nodes){this.children=nodes}
 querySelector(){return new Element()}
}
class Media extends Element {
 constructor(){super();this.paused=true;this.readyState=4;this.duration=30;this.muted=false;this.playbackRate=1;this.time=0}
 get currentTime(){return this.time}set currentTime(v){this.time=v;queueMicrotask(()=>{this.dispatch('seeking');this.dispatch('seeked')})}
 set src(v){this.attrs.src=v}get src(){return this.attrs.src}
 play(){this.paused=false;this.dispatch('play');return Promise.resolve()}
 pause(){if(!this.paused){this.paused=true;this.dispatch('pause')}}
}
async function setup(shotOverrides={}){
 const elements=new Map();const get=s=>{if(!elements.has(s))elements.set(s,s.includes('-video')?new Media():new Element());return elements.get(s)};
 get('#audio-mode').value='original';
 const project={id:'a'.repeat(32),name:'test',status:'ready',ratio:'16:9',busy:false,error:'',audio:true,configured:true,export_ready:false,shots:[{index:0,start:10,end:20,duration:10,status:'review',generated_duration:12,generated_audio:true,version:1,anchors:[],prompt:'',task_id:'existing',reviewed:false,...shotOverrides}]};
 const context={window:{reframeI18n:{addMessages(){},t:s=>s,language:()=> 'zh'},reframeUI:{message:e=>e?.message||e,toast(){}},addEventListener(){}},document:{querySelector:get,createElement:()=>new Element(),createTextNode:s=>s,addEventListener(){}},location:{search:`?id=${project.id}`},URLSearchParams,AbortSignal,Date,Promise,Map,WeakMap,Number,String,Math,JSON,console,queueMicrotask,setTimeout:()=>0,clearTimeout(){},setInterval:()=>0,clearInterval(){},confirm:()=>true,fetch:async()=>({ok:true,json:async()=>structuredClone(project)})};
 vm.runInNewContext(readFileSync(new URL('../project.js',import.meta.url),'utf8'),context);
 for(let i=0;i<12;i++)await Promise.resolve();
 return {get,source:get('#source-video'),result:get('#result-video')};
}
test('each player can start, pause and seek without controlling the other',async()=>{
 const {get,source,result}=await setup();
 assert.equal(get('#export-project').disabled,false,'completed clips export without individual approval');
 assert.equal(result.controls,true);
 await get('#play-result').onclick();assert.equal(source.paused,true);assert.equal(result.paused,false);
 await get('#play-source').onclick();assert.equal(source.paused,false);assert.equal(result.paused,false);
 await get('#play-result').onclick();assert.equal(source.paused,false);assert.equal(result.paused,true);
 const left=source.currentTime;result.currentTime=4;await Promise.resolve();assert.equal(source.currentTime,left);
});
test('sync always restarts both players and a solo action releases the link',async()=>{
 const {get,source,result}=await setup();source.currentTime=16;result.currentTime=5;await Promise.resolve();
 await get('#sync-play').onclick();assert.equal(source.currentTime,10);assert.equal(result.currentTime,0);assert.equal(source.paused,false);assert.equal(result.paused,false);assert.equal(result.muted,true);
 await get('#play-source').onclick();assert.equal(source.paused,true);assert.equal(result.paused,false);
 source.currentTime=18;result.currentTime=7;await Promise.resolve();await get('#sync-play').onclick();assert.equal(source.currentTime,10);assert.equal(result.currentTime,0);
 await get('#sync-play').onclick();assert.equal(source.paused,true);assert.equal(result.paused,true);
});
test('native audio sync matches segment duration and uses only the generated soundtrack',async()=>{
 const {get,source,result}=await setup();get('#audio-mode').value='native';get('#audio-mode').onchange();await Promise.resolve();
 await get('#sync-play').onclick();assert.equal(result.playbackRate,1.2);assert.equal(source.muted,true);assert.equal(result.muted,false);
 source.currentTime=20;source.dispatch('timeupdate');assert.equal(source.paused,true);assert.equal(result.paused,true);assert.equal(result.playbackRate,1);
});

test('silent native results retain the original soundtrack during explicit sync',async()=>{
 const {get,source,result}=await setup({generated_audio:false});get('#audio-mode').value='native';get('#audio-mode').onchange();await Promise.resolve();
 await get('#sync-play').onclick();assert.equal(source.muted,false);assert.equal(result.muted,true);assert.equal(result.playbackRate,1.2);
});
