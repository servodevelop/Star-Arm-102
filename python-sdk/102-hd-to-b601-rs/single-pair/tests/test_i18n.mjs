import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('../stararm_rs_feedback/web/i18n.js',import.meta.url),'utf8');
const storage=new Map();
globalThis.localStorage={getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)};
globalThis.NodeFilter={SHOW_TEXT:4,SHOW_ELEMENT:1};
let notify;
globalThis.MutationObserver=class{constructor(callback){notify=callback;}observe(){}};
function element(tag,text='',attrs={}){
  const el={nodeType:1,tag,attrs,childNodes:[],parentElement:null,
    getAttribute(k){return this.attrs[k]??null;},setAttribute(k,v){this.attrs[k]=String(v);},
    closest(){return ['script','style','pre'].includes(this.tag)||'data-no-i18n' in this.attrs?this:this.parentElement?.closest();}};
  if(text)el.childNodes.push({nodeType:3,data:text,parentElement:el});
  Object.defineProperty(el,'firstChild',{get:()=>el.childNodes[0]});return el;
}
const root=element('html'),heading=element('h1','力反馈工作台'),status=element('span','已保存 v2 · 启动后应用'),input=element('input','',{'aria-label':'J2 基础死区'}),log=element('pre','主臂缺帧'),button=element('button','中文 / EN',{'data-no-i18n':''});
root.childNodes=[heading,status,input,log,button];root.childNodes.forEach(n=>n.parentElement=root);
globalThis.document={documentElement:root,getElementById:()=>button,createTreeWalker(scope){
  const nodes=[];function visit(n){for(const child of n.childNodes??[]){nodes.push(child);visit(child);}}visit(scope);
  let i=-1;return {nextNode(){return nodes[++i];},get currentNode(){return nodes[i];}};
}};
const uri='data:text/javascript;base64,'+Buffer.from(source).toString('base64');
const locale=await import(uri);locale.initLanguage();
assert.equal(root.lang,'zh-CN');
assert.equal(locale.translate('正在加载模型 12/25','en'),'Loading model 12/25');
assert.equal(locale.translate('J3 肘部俯仰','en'),'J3 Elbow pitch');
locale.setLanguage('en');
assert.equal(heading.firstChild.data,'Force feedback');
assert.equal(status.firstChild.data,'Saved v2 · Applies on start');
assert.equal(input.getAttribute('aria-label'),'J2 Base deadzone');
assert.equal(log.firstChild.data,'主臂缺帧','raw logs must remain verbatim');
assert.equal(storage.get('stararm102.language'),'en');
// Values updated while English is active must retain a canonical source.
status.firstChild.data=locale.translate('已应用 v3 / 已保存 v3');locale.rememberText(status,'已应用 v3 / 已保存 v3');
notify([{type:'characterData',target:status.firstChild}]);
const inserted=element('label','力矩滤波时间');inserted.parentElement=root;root.childNodes.push(inserted);
notify([{type:'childList',addedNodes:[inserted]}]);assert.equal(inserted.firstChild.data,'Torque filter time');
input.setAttribute('aria-label','J4 最大运动余量');notify([{type:'attributes',target:input}]);
assert.equal(input.getAttribute('aria-label'),'J4 Max motion margin');
locale.setLanguage('zh-CN');
assert.equal(heading.firstChild.data,'力反馈工作台');
assert.equal(status.firstChild.data,'已应用 v3 / 已保存 v3');
assert.equal(input.getAttribute('aria-label'),'J4 最大运动余量');
assert.equal(inserted.firstChild.data,'力矩滤波时间');
// Repeated switches cannot accumulate translated text or alter data inputs.
for(let i=0;i<8;i++){locale.setLanguage('en');locale.setLanguage('zh-CN');}
assert.equal(heading.firstChild.data,'力反馈工作台');
locale.setLanguage('en');
const reloaded=await import(uri+'#reload');assert.equal(reloaded.currentLanguage(),'en');
console.log('i18n checks passed: dynamic states, attributes, inserted fields, raw logs, persistence and reversal');
