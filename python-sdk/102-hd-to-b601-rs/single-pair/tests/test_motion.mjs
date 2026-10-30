import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

// Controlled Web Animations doubles exercise interruption and final DOM state.
let reduced=false;
globalThis.matchMedia=()=>({get matches(){return reduced;}});
globalThis.getComputedStyle=()=>({opacity:'1',marginBottom:'10px'});
const pending=[];
function element(height=100){
  return {hidden:false,inert:false,attrs:{},setAttribute(key,value){this.attrs[key]=value;},removeAttribute(key){delete this.attrs[key];},getAttribute(key){return this.attrs[key]??null;},style:{removeProperty(key){delete this[key];}},
    getBoundingClientRect(){return {height:this.hidden?0:height};},
    animate(frames,options){
      let resolve,reject;
      const animation={frames,options,finished:new Promise((a,b)=>{resolve=a;reject=b;}),finish(){resolve();},cancel(){reject(new Error('superseded'));}};
      pending.push(animation);return animation;
    }};
}
globalThis.document={startViewTransition:undefined};
const source=await readFile(new URL('../stararm_rs_feedback/web/motion.js',import.meta.url),'utf8');
const motion=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));

const panel=element();
const exit=motion.show(panel,false,{collapse:true});
assert.equal(panel.hidden,false,'exit must remain rendered until animation finishes');
assert.equal(panel.inert,true,'exiting controls must not accept interaction');
pending.at(-1).finish();await exit;assert.equal(panel.hidden,true);

const opening=motion.show(panel,true);pending.at(-1).finish();await opening;
assert.equal(panel.hidden,false);assert.equal(panel.inert,false);

const closing=motion.show(panel,false);
const reversed=motion.show(panel,true);pending.at(-1).finish();await Promise.all([closing,reversed]);
assert.equal(panel.hidden,false,'rapid hide/show must preserve the latest intent');
assert.equal(panel.inert,false);

// SVG's hidden property does not hide its rendering; the attribute must be set.
const svg=element();
const svgExit=motion.show(svg,false);pending.at(-1).finish();await svgExit;
assert.equal(svg.getAttribute('hidden'),'','SVG exit must set the actual hidden attribute');
const svgEnter=motion.show(svg,true);pending.at(-1).finish();await svgEnter;
assert.equal(svg.getAttribute('hidden'),null);
const svgClose=motion.show(svg,false),svgReopen=motion.show(svg,true);
pending.at(-1).finish();await Promise.all([svgClose,svgReopen]);
assert.equal(svg.getAttribute('hidden'),null,'reversing an SVG exit must keep the overlay visible');

reduced=true;const count=pending.length;
await motion.show(panel,false);assert.equal(panel.hidden,true);
await motion.show(panel,true);assert.equal(panel.hidden,false);
assert.equal(pending.length,count,'reduced motion bypasses animation');
let updates=0;await motion.morph(()=>updates++);assert.equal(updates,1);

reduced=false;document.startViewTransition=()=>{throw new Error('unavailable snapshot');};
await motion.morph(()=>updates++,{snapshot:true});assert.equal(updates,2,'snapshot failure must not block navigation');
document.startViewTransition=callback=>{callback();return {finished:Promise.reject(new Error('superseded'))};};
await motion.morph(()=>updates++,{snapshot:true});assert.equal(updates,3,'interrupted snapshot must not apply the update twice');

const details=element(32),summary=element(32);details.open=false;details.scrollHeight=180;
summary.attrs={};summary.setAttribute=(key,value)=>summary.attrs[key]=value;
summary.addEventListener=(name,callback)=>summary.click=callback;
details.querySelector=()=>summary;
motion.accordion(details);
const first=summary.click({preventDefault(){}});assert.equal(details.open,true);
const second=summary.click({preventDefault(){}});pending.at(-1).finish();await Promise.all([first,second]);
assert.equal(details.open,false);assert.equal(summary.attrs['aria-expanded'],'false');
assert.equal(details.style.overflow,undefined);

// The embedded browser may lack View Transitions: verify the native layout fallback.
function attributes(node){node.attrs={};node.getAttribute=key=>node.attrs[key]??null;node.setAttribute=(key,value)=>node.attrs[key]=value;node.removeAttribute=key=>delete node.attrs[key];return node;}
const pages=[attributes(element()),attributes(element(180))];pages[1].hidden=true;
let current=0;
const surface=attributes(element());surface.querySelector=()=>pages[current];surface.getBoundingClientRect=()=>({height:current?180:100,width:400});
document.startViewTransition=undefined;document.getElementById=()=>surface;
const forward=motion.morph(()=>{pages[0].hidden=true;pages[1].hidden=false;current=1;});
assert.equal(pages[0].inert,true,'outgoing layout is temporarily rendered but inert');
const back=motion.morph(()=>{pages[1].hidden=true;pages[0].hidden=false;current=0;});
pending.slice(-3).forEach(animation=>animation.finish());await Promise.all([forward,back]);
assert.equal(pages[0].hidden,false);assert.equal(pages[1].hidden,true);
assert.equal(pages[0].inert,false);assert.equal(pages[1].inert,false);
assert.equal(pages[1].getAttribute('aria-hidden'),null,'temporary exit accessibility state is restored');
console.log('Motion: exit lifecycle, inert state, reversal, reduced motion, native and fallback layout transitions, and accordion interruption passed.');
