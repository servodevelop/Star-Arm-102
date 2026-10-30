// Original native motion primitives, inspired by the interaction patterns in
// beUI and Transitions.dev. No React runtime or network dependency is required.
const preference = matchMedia('(prefers-reduced-motion: reduce)');
export const reducedMotion = () => preference.matches;
export const EASE = 'cubic-bezier(.22,1,.36,1)';
const active = new WeakMap();
function setHidden(element, hidden) {
  // SVGElement.hidden is not an HTML hidden-attribute reflector.
  element.hidden=hidden;
  if(hidden)element.setAttribute('hidden','');else element.removeAttribute('hidden');
}

export function animate(element, frames, options = {}) {
  if (!element || reducedMotion()) return null;
  return element.animate(frames, {duration:280, easing:EASE, ...options});
}

export function enter(scope = document, delay = 0) {
  const elements = scope.matches?.('[data-enter]') ? [scope] : [...scope.querySelectorAll('[data-enter]')];
  elements.filter(element => element.getClientRects().length).forEach((element, i) => {
    animate(element, [{opacity:0, transform:'translateY(9px)'}, {opacity:1, transform:'translateY(0)'}], {duration:460,delay:delay+Math.min(i*22,160)});
  });
}

export async function show(element, visible, {collapse = false, duration = 240} = {}) {
  const previous = active.get(element);
  const startHeight = element.getBoundingClientRect().height;
  const endMargin = parseFloat(getComputedStyle(element).marginBottom)||0;
  const opacity = previous ? getComputedStyle(element).opacity : visible ? 0 : 1;
  previous?.cancel();
  setHidden(element,false);
  element.inert = !visible;
  if (visible) element.style.removeProperty('height');
  const endHeight = element.getBoundingClientRect().height;
  if (reducedMotion()) {setHidden(element,!visible);element.inert=!visible;return;}
  const frames = collapse
    ? [{height:`${visible ? startHeight : endHeight}px`,marginBottom:`${visible?0:endMargin}px`,opacity},{height:`${visible ? endHeight : 0}px`,marginBottom:`${visible?endMargin:0}px`,opacity:visible?1:0}]
    : [{opacity,transform:visible?'translateY(5px) scale(.985)':'translateY(0) scale(1)'},{opacity:visible?1:0,transform:visible?'translateY(0) scale(1)':'translateY(5px) scale(.985)'}];
  const animation=animate(element,frames,{duration,fill:'both'});active.set(element,animation);
  if(collapse)element.style.overflow='hidden';
  try{await animation.finished;}catch{return;}
  if(active.get(element)!==animation)return;
  setHidden(element,!visible);element.inert=!visible;
  animation.cancel();active.delete(element);
  if(collapse){element.style.removeProperty('height');element.style.removeProperty('overflow');}
}

export function text(element, value) {
  value=String(value);if(element.textContent===value)return;
  element.textContent=value;
  // State text changes get a quiet dissolve; telemetry numbers stay readable.
  if(element.matches('[data-state-motion]')) {
    active.get(element)?.cancel();
    active.set(element,animate(element,[{opacity:.35,transform:'translateY(2px)'},{opacity:1,transform:'translateY(0)'}],{duration:180}));
  }
}

let fallbackTransition;
async function layoutMorph(update) {
  const surface=document.getElementById?.('contentSurface');
  if(!surface){update();return;}
  fallbackTransition?.();
  const oldPage=surface.querySelector('[data-page]:not([hidden])');
  const start=surface.getBoundingClientRect();
  update();
  const newPage=surface.querySelector('[data-page]:not([hidden])');
  const end=surface.getBoundingClientRect();
  if(!oldPage||!newPage)return;
  const oldStyle=oldPage.getAttribute('style'),oldAria=oldPage.getAttribute('aria-hidden'),oldInert=oldPage.inert;
  const surfaceStyle=surface.getAttribute('style');
  const animations=[];
  if(oldPage!==newPage){
    oldPage.hidden=false;oldPage.inert=true;oldPage.setAttribute('aria-hidden','true');
    Object.assign(oldPage.style,{position:'absolute',inset:'0 auto auto 0',width:`${start.width}px`,height:`${start.height}px`,pointerEvents:'none',zIndex:'2'});
    animations.push(animate(oldPage,[{opacity:1,translate:'0 0',scale:1},{opacity:0,translate:'0 -7px',scale:.99}],{duration:170,fill:'both'}));
  }
  surface.style.position='relative';surface.style.overflow='clip';
  animations.push(animate(surface,[{height:`${start.height}px`},{height:`${end.height}px`}],{duration:420,fill:'both'}));
  animations.push(animate(newPage,[{opacity:0,translate:'0 9px',scale:.995},{opacity:1,translate:'0 0',scale:1}],{duration:360,delay:30,fill:'both'}));
  let cleaned=false;
  const cleanup=()=>{
    if(cleaned)return;cleaned=true;
    animations.forEach(animation=>animation?.cancel());
    if(oldPage!==newPage){oldPage.hidden=true;oldPage.inert=oldInert;oldStyle===null?oldPage.removeAttribute('style'):oldPage.setAttribute('style',oldStyle);oldAria===null?oldPage.removeAttribute('aria-hidden'):oldPage.setAttribute('aria-hidden',oldAria);}
    surfaceStyle===null?surface.removeAttribute('style'):surface.setAttribute('style',surfaceStyle);
    if(fallbackTransition===cleanup)fallbackTransition=null;
  };
  fallbackTransition=cleanup;
  try{await Promise.all(animations.map(animation=>animation.finished));}catch{/* Interrupted by the next requested layout. */}
  finally{cleanup();}
}

export async function morph(update, {snapshot = false} = {}) {
  if(reducedMotion()){fallbackTransition?.();update();return;}
  // Keep controls live during full-view navigation instead of snapshotting them.
  if(!snapshot||!document.startViewTransition){await layoutMorph(update);return;}
  let applied=false;
  try{await document.startViewTransition(()=>{applied=true;update();}).finished;}
  catch{if(!applied)update();/* A superseding transition may skip the snapshot animation. */}
}

export function slidingIndicator(container, selector) {
  const indicator=document.createElement('span');indicator.className='sliding-indicator';indicator.setAttribute('aria-hidden','true');container.prepend(indicator);
  const update=()=>{const item=container.querySelector(selector);if(!item)return;indicator.style.width=`${item.offsetWidth}px`;indicator.style.height=`${item.offsetHeight}px`;indicator.style.transform=`translate(${item.offsetLeft}px,${item.offsetTop}px)`;};
  new ResizeObserver(update).observe(container);update();return update;
}

export function accordion(details) {
  const summary=details.querySelector('summary');let opening=details.open;
  summary.setAttribute('aria-expanded',String(opening));
  summary.addEventListener('click',async event=>{
    event.preventDefault();opening=!opening;summary.setAttribute('aria-expanded',String(opening));
    const start=details.getBoundingClientRect().height;active.get(details)?.cancel();details.open=true;
    const end=opening?details.scrollHeight:summary.getBoundingClientRect().height;
    if(reducedMotion()){details.open=opening;return;}
    details.style.overflow='hidden';
    const animation=animate(details,[{height:`${start}px`},{height:`${end}px`}],{duration:340,fill:'both'});active.set(details,animation);
    try{await animation.finished;}catch{return;}
    if(active.get(details)!==animation)return;
    details.open=opening;animation.cancel();active.delete(details);details.style.removeProperty('overflow');
  });
}

export function tooltipSystem() {
  const tip=document.getElementById('uiTooltip');let timer,target;
  const dismiss=()=>{clearTimeout(timer);if(target)target.removeAttribute('aria-describedby');target=null;show(tip,false,{duration:110});};
  const reveal=element=>{clearTimeout(timer);target=element;timer=setTimeout(()=>{
    if(target!==element)return;
    tip.textContent=element.dataset.tooltip;tip.hidden=false;const rect=element.getBoundingClientRect();
    const x=Math.max(10,Math.min(innerWidth-tip.offsetWidth-10,rect.left+(rect.width-tip.offsetWidth)/2));
    tip.style.left=`${x}px`;tip.style.top=`${rect.bottom+tip.offsetHeight+14<innerHeight?rect.bottom+8:rect.top-tip.offsetHeight-8}px`;
    element.setAttribute('aria-describedby','uiTooltip');show(tip,true,{duration:160});
  },220);};
  document.addEventListener('pointerover',event=>{const element=event.target.closest('[data-tooltip]');if(element&&element!==target)reveal(element);});
  document.addEventListener('pointerout',event=>{if(target&&!target.contains(event.relatedTarget))dismiss();});
  document.addEventListener('focusin',event=>{const element=event.target.closest('[data-tooltip]');if(element)reveal(element);});
  document.addEventListener('focusout',dismiss);document.addEventListener('keydown',event=>{if(event.key==='Escape')dismiss();});
  window.addEventListener('scroll',dismiss,{passive:true});
}
