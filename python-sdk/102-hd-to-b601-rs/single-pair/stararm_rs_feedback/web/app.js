import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {STLLoader} from './vendor/STLLoader.js';
import {finite,torqueVisual} from './torque.js';
import * as Motion from './motion.js';
import {buttonContent} from './icons.js';
import {translate,rememberText,initLanguage} from './i18n.js';
function text(element,value){Motion.text(element,translate(value));rememberText(element,value);}

const $=id=>document.getElementById(id);
const names=['底座回转','肩部俯仰','肘部俯仰','腕部俯仰','腕部偏转','腕部旋转','夹爪'];
const colors=['#2563eb','#d97706','#0d9488','#7c3aed','#c2417e','#4d7c0f','#64748b'];
let token='',settings=null,boot=null,dirty=false,selected=0,latest=null,latestStatus=null;
let replay=null,replayIndex=0,replayTimer=null,history=[],lastHistory=null,busy=false,logOpen=false,networkFailed=false;
const fmt=(v,n=2)=>typeof v==='number'&&Number.isFinite(v)?v.toFixed(n):'—';
let forceMetric='torque_nm',forceFresh=false,forceSource='live',freshDeadline=0;
const forceElements=[],forceMarkers=[],forceAnchors=[];
let activeView='workspace',navIndicator,metricIndicator;
function setButton(id,label,name){
  const button=$(id);if(button.dataset.content===`${name}:${label}`)return;
  button.querySelectorAll('.button-ghost').forEach(ghost=>ghost.remove());
  const previous=button.innerHTML,oldWidth=button.getBoundingClientRect().width,visible=button.getClientRects().length>0;
  button.dataset.content=`${name}:${label}`;button.innerHTML=buttonContent(name,label);
  if(visible&&!Motion.reducedMotion()){
    const width=button.getBoundingClientRect().width;
    if(oldWidth&&Math.abs(width-oldWidth)>1)Motion.animate(button,[{width:`${oldWidth}px`},{width:`${width}px`}],{duration:280});
    if(previous){const ghost=document.createElement('span');ghost.className='button-ghost';ghost.innerHTML=previous;ghost.setAttribute('aria-hidden','true');button.append(ghost);const exit=Motion.animate(ghost,[{opacity:.7,translate:'0 0'},{opacity:0,translate:'0 -5px'}],{duration:130});exit.finished.catch(()=>{}).then(()=>ghost.remove());}
    Motion.animate(button.querySelector('.icon'),[{opacity:0,scale:.7},{opacity:1,scale:1}],{duration:230});
    Motion.animate(button.querySelector('.button-label'),[{opacity:0,translate:'0 4px'},{opacity:1,translate:'0 0'}],{duration:250});
  }
}
function initInterface(){
  $('contentSurface').dataset.motionEngine='layout-morph';
  document.querySelectorAll('[data-icon]').forEach(button=>setButton(button.id,button.textContent.trim(),button.dataset.icon));
  setButton('defaults','恢复默认','rotate-ccw');setButton('save','保存并应用','save');setButton('advancedToggle','滤波与响应参数','chevron-down');
  navIndicator=Motion.slidingIndicator(document.querySelector('.page-tabs'),'[aria-selected=true]');
  metricIndicator=Motion.slidingIndicator(document.querySelector('.segmented'),'[aria-pressed=true]');
  initScaleMenu();
  document.querySelectorAll('[data-view]').forEach(button=>button.onclick=()=>navigate(button.dataset.view));
  document.querySelector('.brand').onclick=event=>{event.preventDefault();navigate('workspace');};
  document.querySelector('.page-tabs').addEventListener('keydown',event=>{
    const buttons=[...document.querySelectorAll('[data-view]')],index=buttons.indexOf(document.activeElement);
    if(!['ArrowRight','ArrowLeft','Home','End'].includes(event.key))return;event.preventDefault();
    const next=event.key==='Home'?0:event.key==='End'?buttons.length-1:(index+(event.key==='ArrowRight'?1:-1)+buttons.length)%buttons.length;
    buttons[next].focus();navigate(buttons[next].dataset.view);
  });
  Motion.accordion(document.querySelector('.joint-inspector'));Motion.tooltipSystem();
  $('dismissNotice').onclick=()=>Motion.show($('notice'),false,{collapse:true});
  const chart=$('trend');chart.addEventListener('pointermove',event=>{const box=chart.getBoundingClientRect();chartHover={x:event.clientX-box.left,y:event.clientY-box.top};drawTrend();});
  chart.addEventListener('pointerleave',()=>{chartHover=null;Motion.show($('trendTooltip'),false,{duration:120});drawTrend();});
  chart.tabIndex=0;let cursor=null;
  chart.addEventListener('keydown',event=>{
    if(event.key==='Escape'){chartHover=null;Motion.show($('trendTooltip'),false);drawTrend();return;}
    if(!['ArrowLeft','ArrowRight'].includes(event.key)||!history.length)return;event.preventDefault();
    cursor=Math.max(0,Math.min(history.length-1,(cursor??history.length-1)+(event.key==='ArrowLeft'?-1:1)));
    chartHover={x:32+(history[cursor].time-history.at(-1).time+30)/30*(chart.clientWidth-46),y:0};drawTrend();
  });
  chart.addEventListener('blur',()=>{cursor=null;chartHover=null;Motion.show($('trendTooltip'),false);drawTrend();});
  Motion.enter();
}
function initScaleMenu(){
  const select=$('heatScale'),wrapper=select.parentElement,trigger=document.createElement('button'),menu=document.createElement('div');
  select.classList.add('native-scale');select.tabIndex=-1;select.setAttribute('aria-hidden','true');
  trigger.type='button';trigger.className='scale-trigger';trigger.setAttribute('aria-haspopup','listbox');trigger.setAttribute('aria-expanded','false');trigger.setAttribute('aria-controls','scaleMenu');
  menu.id='scaleMenu';menu.className='scale-menu';menu.hidden=true;menu.setAttribute('role','listbox');menu.setAttribute('aria-label','选择颜色量程');
  let opened=false;
  const sync=()=>{trigger.innerHTML=buttonContent('chevron-down',select.selectedOptions[0].textContent);trigger.setAttribute('aria-label',`显示量程 ${select.selectedOptions[0].textContent}`);menu.querySelectorAll('[role=option]').forEach(option=>option.setAttribute('aria-selected',String(option.dataset.value===select.value)));};
  const toggle=visible=>{opened=visible;trigger.setAttribute('aria-expanded',String(visible));Motion.show(menu,visible,{collapse:true,duration:220});if(visible)Motion.enter(menu);};
  [...select.options].forEach(option=>{const button=document.createElement('button');button.type='button';button.dataset.value=option.value;button.textContent=option.textContent;button.setAttribute('role','option');button.setAttribute('data-enter','');button.tabIndex=-1;
    button.onclick=()=>{select.value=option.value;select.dispatchEvent(new Event('change',{bubbles:true}));sync();toggle(false);trigger.focus();};menu.append(button);
  });
  wrapper.querySelector('svg')?.remove();wrapper.append(trigger,menu);sync();
  trigger.onclick=()=>toggle(!opened);
  trigger.onkeydown=event=>{if(!['ArrowDown','ArrowUp'].includes(event.key))return;event.preventDefault();toggle(true);menu.querySelector('[aria-selected=true]').focus();};
  menu.onkeydown=event=>{const options=[...menu.querySelectorAll('[role=option]')],index=options.indexOf(document.activeElement);
    if(event.key==='Escape'){event.preventDefault();toggle(false);trigger.focus();return;}
    if(!['ArrowDown','ArrowUp','Home','End'].includes(event.key))return;event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?options.length-1:(index+(event.key==='ArrowDown'?1:-1)+options.length)%options.length;options[next].focus();
  };
  document.addEventListener('pointerdown',event=>{if(opened&&!wrapper.contains(event.target))toggle(false);});
  document.addEventListener('focusin',event=>{if(opened&&!wrapper.contains(event.target))toggle(false);});
}
function navigate(view){
  if(view===activeView)return;activeView=view;
  const titles={workspace:['实时工作台','力反馈工作台'],parameters:['反馈调校','阻尼参数'],logs:['运行日志','会话记录']};
  document.querySelectorAll('[data-view]').forEach(button=>{const chosen=button.dataset.view===view;button.setAttribute('aria-selected',String(chosen));button.tabIndex=chosen?0:-1;});navIndicator();
  text($('pageName'),titles[view][0]);text($('pageTitle'),titles[view][1]);
  Motion.morph(()=>{document.querySelectorAll('[data-page]').forEach(page=>{page.hidden=page.dataset.page!==activeView;});Motion.enter($(activeView));});
}
function selectJoint(index){
  selected=index;
  for(const row of $('jointRows').rows){const active=Number(row.dataset.joint)===index;row.classList.toggle('selected',active);row.setAttribute('aria-selected',String(active));}
  forceElements.forEach((item,i)=>{item.label.classList.toggle('selected',i===index);item.label.setAttribute('aria-pressed',String(i===index));});
  document.querySelectorAll('[data-curve]').forEach(button=>button.setAttribute('aria-pressed',String(Number(button.dataset.curve)===index)));
  updateDetail();highlightModel();drawTrend();
}
function notice(message,type=''){ text($('noticeText'),message);$('notice').className='notice '+type;if($('notice').hidden||$('notice').inert)Motion.show($('notice'),true,{collapse:true}); }
async function api(path,body){
  const response=await fetch(path,{method:body===undefined?'GET':'POST',headers:body===undefined?{}:{'Content-Type':'application/json','X-RS-Token':token},body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(4000)});
  const data=await response.json();if(!response.ok)throw new Error(data.error||`HTTP ${response.status}`);return data;
}
function markDirty(){dirty=true;text($('dirty'),'未保存');$('dirty').className='tag replay';}
function buildTables(){
  $('jointRows').innerHTML=names.map((n,i)=>`<tr data-joint="${i}" class="${i===selected?'selected':''}"><td><div class="joint-name"><span style="background:${colors[i]}"></span><div>J${i+1}<small>${n}</small></div></div></td><td id="pos${i}">—</td><td id="cur${i}" title="RS iqf 滤波电流，约 2.86 Hz">—</td><td><div class="power"><span id="mode${i}" class="mode UNKNOWN">—</span><span id="power${i}" class="pval">—</span></div><div class="powerbar"><i id="bar${i}" style="width:0%"></i></div></td></tr>`).join('');
  $('legend').innerHTML=colors.map((c,i)=>`<button data-curve="${i}" style="--curve:${c}" aria-label="突出 J${i+1} ${names[i]} 曲线" aria-pressed="${i===selected}"><i></i>J${i+1}</button>`).join('');
  document.querySelectorAll('[data-curve]').forEach(button=>button.onclick=()=>selectJoint(Number(button.dataset.curve)));
  document.querySelectorAll('#jointRows tr').forEach(row=>row.setAttribute('data-enter',''));
  for(const tr of $('jointRows').rows){tr.tabIndex=0;tr.setAttribute('aria-selected',String(Number(tr.dataset.joint)===selected));tr.addEventListener('click',()=>selectJoint(Number(tr.dataset.joint)));tr.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectJoint(Number(tr.dataset.joint));}});}
  names.forEach((name,i)=>{
    const label=document.createElement('button');label.className='force-label unavailable';label.setAttribute('aria-pressed',String(i===selected));
    label.innerHTML=`<span><span class="force-axis">J${i+1}</span><span class="force-level">等待</span></span><span><b>—</b><em>N·m</em></span>`;
    label.onclick=()=>selectJoint(i);label.title=`J${i+1} · ${name}`;$('forceLabels').appendChild(label);
    const line=document.createElementNS('http://www.w3.org/2000/svg','path');$('forceLines').appendChild(line);
    forceElements.push({label,line,value:label.querySelector('b'),level:label.querySelector('.force-level')});
  });
  document.querySelectorAll('[data-metric]').forEach(button=>button.onclick=()=>{
    forceMetric=button.dataset.metric;document.querySelectorAll('[data-metric]').forEach(item=>item.setAttribute('aria-pressed',String(item===button)));
    metricIndicator();text($('forceNote'),forceMetric==='torque_nm'?'电机扭矩含重力与运动影响  非末端接触力':'模型残差含摩擦与建模误差  模型无效时不显示数值');updateForces();
  });
  $('heatScale').onchange=()=>{text($('scaleMax'),`${$('heatScale').value} N·m`);updateForces();};
  $('showForces').onchange=()=>{const visible=$('showForces').checked;Motion.show($('forceLabels'),visible);Motion.show($('forceLines'),visible);};
  updateForces();
}
function buildParams(){
  $('maxPower').value=settings.max_power_mw;
  $('paramRows').innerHTML=names.map((n,i)=>`<tr><td><div class="joint-name"><span style="background:${colors[i]}"></span>J${i+1}<small>${n}${i===5?' · 普通阻尼关闭':''}</small></div></td>${['joint_power_mw',...Object.keys(boot.arrays)].map(key=>{const bounds=key==='joint_power_mw'?[0,1500]:boot.arrays[key];return `<td><input aria-label="J${i+1} ${key==='joint_power_mw'?'功率上限':boot.arrays[key][2]}" type="number" data-key="${key}" data-index="${i}" min="${bounds[0]}" max="${bounds[1]}" step="${key==='joint_power_mw'?10:.01}" value="${settings[key][i]}" ${i===5?'disabled':''}></td>`;}).join('')}</tr>`).join('');
  $('advancedFields').innerHTML=Object.entries(boot.scalars).map(([key,[lo,hi,label,unit]])=>`<label>${label}<span>${unit}</span><input type="number" data-key="${key}" min="${lo}" max="${hi}" step="${hi>100?100:.01}" value="${settings[key]}"></label>`).join('');
  for(const input of document.querySelectorAll('.params-panel input'))input.addEventListener('input',markDirty);
  document.querySelectorAll('#paramRows tr,#advancedFields label').forEach(element=>element.setAttribute('data-enter',''));if(activeView==='parameters')Motion.enter($('parameters'));
}
function collectSettings(){
  const next=structuredClone(settings);next.max_power_mw=Number($('maxPower').value);
  for(const input of document.querySelectorAll('[data-key]')){
    if(!input.checkValidity())throw new Error(`请检查 ${input.getAttribute('aria-label')||input.dataset.key} 的范围`);
    if(input.dataset.index!==undefined)next[input.dataset.key][Number(input.dataset.index)]=Number(input.value);
    else next[input.dataset.key]=Number(input.value);
  }
  if(!$('maxPower').checkValidity())throw new Error('总功率上限须为 400–1500 mW');return next;
}
$('save').onclick=async()=>{try{const next=collectSettings();$('save').disabled=true;settings=await api('/api/settings',next);dirty=false;text($('dirty'),'已保存');$('dirty').className='tag';notice(latestStatus?.running?'参数已保存，等待控制循环确认生效。':'参数已保存，下次启动时生效。','success');}catch(e){notice(e.message,'error');}finally{$('save').disabled=false;}};
$('defaults').onclick=()=>{const revision=settings.revision;settings=structuredClone(boot.defaults);settings.revision=revision;Motion.morph(()=>{buildParams();markDirty();},{snapshot:true});notice('已填入默认值  保存并应用后生效');};
let advancedOpen=false;
$('advancedToggle').onclick=()=>{advancedOpen=!advancedOpen;$('advancedToggle').setAttribute('aria-expanded',String(advancedOpen));Motion.show($('advancedFields'),advancedOpen,{collapse:true,duration:300});setButton('advancedToggle',advancedOpen?'收起响应参数':'滤波与响应参数',advancedOpen?'chevron-down':'settings-2');};
async function start(mode){
  if(busy)return;
  if(dirty){notice('有未保存参数，请先保存或恢复已保存值。','error');return;}
  busy=true;setButtons();
  try{history=[];lastHistory=null;latest=null;notice('正在连接机械臂，请查看运行日志。');renderStatus(await api('/api/start',{mode}));}
  catch(e){notice(e.message,'error');}finally{busy=false;setButtons();}
}
$('start').onclick=()=>start('feedback');$('monitor').onclick=()=>start('monitor');
$('stop').onclick=async()=>{if(busy)return;busy=true;setButtons();try{renderStatus(await api('/api/stop',{}));notice('已发送正常停止请求，等待回零/卸力清理。');}catch(e){notice(e.message,'error');}finally{busy=false;setButtons();}};
function setButtons(){const running=latestStatus?.running;$('start').disabled=busy||running||!!replay||networkFailed;$('monitor').disabled=$('start').disabled;$('stop').disabled=busy||!running||latestStatus?.stop_requested||networkFailed;$('replay').disabled=busy||running||networkFailed;}
function explain(reason){
  if(!reason)return '等待实时数据';
  return reason.replace('RS DYNAMIC: ','').replace('RS GRIPPER: ','').replace('current moving residual (experimental)','按运动中剩余力矩更新').replace('current residual (experimental)','按当前剩余力矩更新').replace('current motor torque (experimental)','按夹爪当前电机力矩更新').replace('home-pose gravity model invalid','近零姿态模型无效').replace('this joint damping released','本轴普通阻尼已释放').replace('near joint limit','接近本轴软件限位').replace('Leader feedback gap','主臂缺帧').replace('ordinary damping released','普通阻尼已释放').replace('gripper damping released','夹爪普通阻尼已释放').replace('warming up','初始化').replace('no stationary pose required','无需停稳');
}
function updateDetail(){
  const j=latest?.joints?.[selected];text($('selectedTitle'),`J${selected+1} ${names[selected]}`);
  text($('selectedTemp'),fmt(j?.temperature_c,1)+' °C');text($('selectedReason'),explain(j?.reason));
  text($('selectedResidual'),fmt(j?.residual_nm)+' Nm');text($('selectedDeadzone'),fmt(j?.deadzone_nm)+' Nm');text($('selectedLeader'),fmt(j?.leader_pos_deg,1)+'°');
}
function renderTelemetry(frame,source,fresh=true){
  latest=frame;forceFresh=fresh;forceSource=source;text($('source'),source==='replay'?'日志回放 · 非实时':fresh?'实时 CAN':'数据已过期');$('source').className='tag '+(source==='replay'?'replay':fresh?'live':'replay');
  const joints=frame.joints||[];let max=-1,axis=0,active=0;
  Array.from({length:7},(_,i)=>joints[i]||{}).forEach((j,i)=>{
    text($('pos'+i),fmt(j.motor_pos_deg,1));text($('cur'+i),fresh?fmt(j.current_a):'—');
    const mode=fresh?(j.leader_mode||'UNKNOWN'):'UNKNOWN';text($('mode'+i),mode==='UNKNOWN'?'过期':mode);$('mode'+i).className='mode '+mode;
    text($('power'+i),fresh?fmt(j.leader_power_mw,0):'—');$('bar'+i).style.width=fresh?`${Math.min(100,(j.leader_power_mw||0)/1500*100)}%`:'0%';
    if(finite(j.torque_nm)&&Math.abs(j.torque_nm)>max){max=Math.abs(j.torque_nm);axis=i;}if(j.leader_mode==='DAMPING'&&j.leader_power_mw>0)active++;
  });
  text($('activeCount'),fresh?active:'—');text($('outputDetail'),source==='replay'?'历史请求值':frame.holding?'HOLD · 独立堵转保持':frame.output_enabled?'反馈输出已启用':'仅监测 · 未发送 Leader 阻尼');
  text($('maxTorque'),fmt(max<0?null:max));text($('maxTorqueJoint'),`J${axis+1} · ${names[axis]}`);
  updateDetail();setPose(joints);updateForces();
  if(fresh&&frame.monotonic_s!==lastHistory){
    lastHistory=frame.monotonic_s;history.push({time:frame.monotonic_s,torque:joints.map(j=>j.torque_nm)});
    history=history.filter(p=>frame.monotonic_s-p.time<=30);drawTrend();
  }
}
function clearTelemetry(){
  latest=null;forceFresh=false;updateForces();updateDetail();text($('source'),'等待数据');$('source').className='tag';text($('activeCount'),'—');text($('outputDetail'),'等待反馈数据');text($('maxTorque'),'—');text($('maxTorqueJoint'),'RS 电机反馈值');
  for(let i=0;i<7;i++){for(const key of ['pos','cur','power'])$(key+i).textContent='—';text($('mode'+i),'—');$('mode'+i).className='mode UNKNOWN';$('bar'+i).style.width='0%';}
}
function renderStatus(data){
  latestStatus=data;networkFailed=false;setButtons();if(replay)return;
  freshDeadline=data.fresh?performance.now()+Math.max(0,.8-(data.age_s??0))*1000:0;
  document.body.classList.toggle('stale',!data.fresh);
  const phase={idle:'未启动',connecting:'连接中',running:'运行中',stopping:'正在停止',exited:'已结束'};
  text($('session'),phase[data.phase]||'未知');text($('sessionDetail'),data.phase==='exited'?`退出代码 ${data.exit_code}`:data.fresh&&data.telemetry?.leader_targets_paused?'主臂短暂缺帧 · 跟随目标暂停，阻尼按 RS 更新':'Star Arm 102 / B601 RS');
  $('led').className='led '+(data.fresh?'green':data.running?'orange':'');text($('connection'),data.fresh?'实时数据已连接':data.running?'等待设备数据':'本地网页已连接');
  text($('freshness'),data.age_s===null?'—':data.fresh?`${Math.round(data.age_s*1000)} ms`:'已过期');
  const applied=data.telemetry?.applied_revision;
  text($('revision'),data.running&&applied!==undefined?`已应用 v${applied} / 已保存 v${data.saved_revision}${applied!==data.saved_revision?' · 等待应用':''}`:`已保存 v${data.saved_revision} · 启动后应用`);
  if(data.telemetry)renderTelemetry(data.telemetry,'live',data.fresh);else if(latest)clearTelemetry();
  if(data.telemetry?.settings_error)notice('参数未应用：'+data.telemetry.settings_error,'error');
  if(data.phase==='exited'&&data.exit_code!==0&&data.exit_code!==-2)notice(`会话已结束（退出代码 ${data.exit_code}），展开日志查看原因。`,'error');
  if(data.log_file)text($('logPath'),data.log_file);
}
async function poll(){try{renderStatus(await api('/api/state'));}catch(e){networkFailed=true;setButtons();document.body.classList.add('stale');$('led').className='led orange';text($('connection'),'网页服务连接中断');text($('freshness'),'已过期');if(latest&&!replay)renderTelemetry(latest,'live',false);notice('网页服务暂不可达；此状态不能确认机械臂已停止。','error');}setTimeout(poll,250);}
// Expire on the client even while a state request is still waiting for its timeout.
setInterval(()=>{if(!replay&&forceFresh&&performance.now()>freshDeadline){document.body.classList.add('stale');text($('freshness'),'已过期');text($('connection'),'等待新鲜设备数据');$('led').className='led orange';renderTelemetry(latest,'live',false);}},100);
$('replay').onclick=async()=>{
  if(replay){clearInterval(replayTimer);replay=null;history=[];lastHistory=null;drawTrend();setButton('replay','日志回放','rotate-ccw');notice('已退出回放，尚未连接机械臂。');renderStatus(await api('/api/state'));return;}
  try{replay=await api('/api/replay');replayIndex=0;history=[];lastHistory=null;setButton('replay','退出回放','square');setButtons();notice(`正在回放 ${replay.file}，所有数值为历史数据；旧日志缺少电流时显示“—”。`);document.body.classList.remove('stale');
    text($('session'),'日志回放');text($('sessionDetail'),replay.file);text($('connection'),'历史数据 · 非实时');$('led').className='led orange';text($('freshness'),'回放中');text($('revision'),'历史日志参数');
    replayTimer=setInterval(()=>{if(replayIndex>=replay.frames.length){replayIndex=0;history=[];lastHistory=null;}renderTelemetry(replay.frames[replayIndex++],'replay',true);},100);
  }catch(e){replay=null;notice(e.message,'error');}
};
$('toggleLog').onclick=()=>{logOpen=!logOpen;Motion.show($('log'),logOpen,{collapse:true,duration:300});Motion.show($('logEmpty'),!logOpen,{collapse:true,duration:300});setButton('toggleLog',logOpen?'收起日志':'展开日志',logOpen?'chevron-down':'terminal');loadLog();};
async function loadLog(){if(logOpen){try{Motion.text($('log'),(await api('/api/log')).text||translate('尚无运行日志'));$('log').scrollTop=$('log').scrollHeight;}catch{}}}
setInterval(loadLog,1500);
let chartHover=null;
function drawTrend(){
  const canvas=$('trend'),width=canvas.clientWidth,height=canvas.clientHeight;
  if(width<1||height<1)return;
  const dpr=devicePixelRatio||1;canvas.width=width*dpr;canvas.height=height*dpr;
  const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);ctx.clearRect(0,0,width,height);
  const values=history.flatMap(point=>point.torque.filter(finite).map(Math.abs));
  const range=Math.ceil(Math.max(1,...values)*1.15*2)/2;
  const left=32,right=width-14,top=10,bottom=height-12,mid=(top+bottom)/2;
  const toY=value=>mid-value/range*(bottom-top)/2;
  ctx.font='8px Consolas,monospace';ctx.fillStyle='#aab6c8';ctx.strokeStyle='#edf1f7';ctx.lineWidth=1;
  for(const value of [-range,0,range]){const y=toY(value);ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(right,y);ctx.stroke();ctx.fillText(value.toFixed(1),5,y+3);}
  if(history.length<2){ctx.fillText(translate('等待关节数据'),left+9,mid-8);return;}
  const end=history.at(-1).time,start=end-30,toX=time=>left+(time-start)/30*(right-left);
  const order=colors.map((_,i)=>i).filter(i=>i!==selected);order.push(selected);
  order.forEach(i=>{const color=colors[i];
    ctx.beginPath();ctx.strokeStyle=color;ctx.lineWidth=i===selected?2.2:1.25;ctx.globalAlpha=i===selected?1:.78;let connected=false;
    for(const point of history){const value=point.torque[i];if(!finite(value)){connected=false;continue;}const x=toX(point.time),y=toY(value);if(connected)ctx.lineTo(x,y);else ctx.moveTo(x,y);connected=true;}
    ctx.stroke();
  });ctx.globalAlpha=1;
  if(chartHover&&chartHover.x>=left&&chartHover.x<=right){
    const time=start+(chartHover.x-left)/(right-left)*30;
    const point=history.reduce((nearest,p)=>Math.abs(p.time-time)<Math.abs(nearest.time-time)?p:nearest,history[0]);
    const value=point.torque[selected],x=toX(point.time);
    ctx.strokeStyle='#c9d7ed';ctx.setLineDash([2,3]);ctx.beginPath();ctx.moveTo(x,top);ctx.lineTo(x,bottom);ctx.stroke();ctx.setLineDash([]);
    if(finite(value)){ctx.fillStyle=colors[selected];ctx.beginPath();ctx.arc(x,toY(value),3,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#fff';ctx.lineWidth=1.5;ctx.stroke();}
    const tip=$('trendTooltip');tip.style.setProperty('--curve',colors[selected]);tip.replaceChildren();const title=document.createElement('b'),subtitle=document.createElement('span');
    title.textContent=`J${selected+1}  ${fmt(value)} N·m`;text(subtitle,`${replay?'历史回放':'历史采样'}  ${fmt(end-point.time,1)} s 前`);tip.append(title,subtitle);
    tip.style.left=`${Math.max(8,Math.min(width-122,chartHover.x-50))}px`;tip.style.top='5px';
    if(tip.hidden||tip.inert)Motion.show(tip,true,{duration:160});
  }else if(chartHover){Motion.show($('trendTooltip'),false,{duration:100});}
}
let scene,camera,renderer,controls,robotGroup,modelJoints=[],linkGroups={},axes=[],modelReady=false;
const modelMeshes=[];
function poseObject(obj,pose){obj.position.fromArray(pose.xyz);obj.quaternion.setFromEuler(new THREE.Euler(...pose.rpy,'ZYX'));}
let cameraReset=null;
function resetView(){
  if(!modelReady||Motion.reducedMotion()){camera.position.set(.82,-.98,.67);controls.target.set(0,0,.27);controls.update();return;}
  cameraReset={position:camera.position.clone(),target:controls.target.clone(),time:performance.now()};
}

async function initModel(){
  try{
    const view=$('viewport');scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(38,1,.005,20);camera.up.set(0,0,1);
    renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.2;
    view.appendChild(renderer.domElement);controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.minDistance=.3;controls.maxDistance=3.;controls.maxPolarAngle=Math.PI*.49;resetView();
    scene.add(new THREE.HemisphereLight(0xffffff,0xa7b6cd,2.1));const sun=new THREE.DirectionalLight(0xf9fbff,3);sun.position.set(1,-1,2);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);sun.shadow.camera.left=-1;sun.shadow.camera.right=1;sun.shadow.camera.top=1;sun.shadow.camera.bottom=-1;sun.shadow.bias=-.0005;scene.add(sun);
    const rim=new THREE.DirectionalLight(0xdde9ff,2);rim.position.set(-1,.5,1);scene.add(rim);
    const grid=new THREE.GridHelper(2,40,0xd4deed,0xe9eef5);grid.rotation.x=Math.PI/2;grid.position.z=-.001;scene.add(grid);
    const floor=new THREE.Mesh(new THREE.PlaneGeometry(5,5),new THREE.ShadowMaterial({opacity:.12}));floor.position.z=-.002;floor.receiveShadow=true;scene.add(floor);
    const model=await(await fetch('model/robot.json')).json();robotGroup=new THREE.Group();scene.add(robotGroup);
    for(const link of model.links){const group=new THREE.Group();group.name=link.name;linkGroups[link.name]=group;}
    robotGroup.add(linkGroups[model.root]);
    for(const joint of model.joints){const base=new THREE.Group(),moving=new THREE.Group();poseObject(base,joint);base.add(moving);moving.add(linkGroups[joint.child]);linkGroups[joint.parent].add(base);modelJoints.push({...joint,base,moving});
      if(joint.type==='revolute'){const helper=new THREE.AxesHelper(.055);helper.visible=false;helper.material.transparent=true;helper.material.opacity=0;base.add(helper);axes.push(helper);}}
    for(let i=0;i<7;i++){
      const anchor=i<6?modelJoints.find(j=>j.name===`joint${i+1}`).base:linkGroups.gripper_end;
      const marker=new THREE.Mesh(new THREE.SphereGeometry(.009,16,12),new THREE.MeshBasicMaterial({color:0x92a29e,depthTest:false,transparent:true,opacity:.85}));marker.renderOrder=5;anchor.add(marker);forceAnchors.push(anchor);forceMarkers.push(marker);
    }
    const loader=new STLLoader(),cache=new Map();let completed=0,total=model.links.reduce((n,l)=>n+l.visuals.length,0);
    const tasks=model.links.flatMap(link=>link.visuals.map(async v=>{
      if(!cache.has(v.mesh))cache.set(v.mesh,loader.loadAsync(v.mesh));const geometry=await cache.get(v.mesh);geometry.computeVertexNormals();
      const baseColor=new THREE.Color(...v.color.slice(0,3));if(v.color[1]>.5&&v.color[0]<v.color[1])baseColor.set(v.color[0]>.5?0x7f96b6:0x333c4a);const material=new THREE.MeshStandardMaterial({color:baseColor,metalness:.48,roughness:.5});const mesh=new THREE.Mesh(geometry,material);mesh.userData.baseColor=material.color.clone();modelMeshes.push(mesh);mesh.castShadow=true;mesh.receiveShadow=true;mesh.scale.fromArray(v.scale);poseObject(mesh,v);linkGroups[link.name].add(mesh);text($('modelLoadingText'),`正在加载模型 ${++completed}/${total}`);
    }));await Promise.all(tasks);modelReady=true;Motion.show($('modelLoading'),false,{duration:400});if(latest)setPose(latest.joints);updateForces();
    const resize=()=>{const w=view.clientWidth,h=view.clientHeight;if(w<1||h<1)return;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();drawTrend();};new ResizeObserver(resize).observe(view);resize();
    $('resetView').onclick=resetView;$('showAxes').onchange=()=>axes.forEach(axis=>{axis.visible=true;axis.material.transparent=true;});controls.addEventListener('start',()=>{cameraReset=null;});
    const animate=()=>{
      requestAnimationFrame(animate);
      if($('workspace').hidden)return;
      if(cameraReset){const t=Math.min(1,(performance.now()-cameraReset.time)/550),ease=1-(1-t)**4;camera.position.copy(cameraReset.position).lerp(new THREE.Vector3(.82,-.98,.67),ease);controls.target.copy(cameraReset.target).lerp(new THREE.Vector3(0,0,.27),ease);if(t===1)cameraReset=null;}
      axes.forEach(axis=>{const target=$('showAxes').checked?1:0;if(axis.material.transparent)axis.material.opacity=Motion.reducedMotion()?target:THREE.MathUtils.lerp(axis.material.opacity,target,.18);axis.visible=axis.material.opacity>.01&&($('showAxes').checked||axis.material.transparent);});
      const blend=Motion.reducedMotion()?1:.22;
      forceMarkers.forEach(marker=>{const target=$('showForces').checked ? .85 : 0;marker.material.opacity=Motion.reducedMotion()?target:THREE.MathUtils.lerp(marker.material.opacity,target,.18);marker.visible=marker.material.opacity>.005;marker.scale.lerp(new THREE.Vector3().setScalar(marker.userData.selected?1.35:1),blend);});
      modelMeshes.forEach(mesh=>{if(mesh.userData.targetColor){mesh.material.color.lerp(mesh.userData.targetColor,blend);mesh.material.emissive.lerp(mesh.userData.targetEmissive,blend);mesh.material.emissiveIntensity=THREE.MathUtils.lerp(mesh.material.emissiveIntensity,mesh.userData.targetIntensity,blend);}});
      modelJoints.forEach(joint=>{if(joint.targetQuaternion)joint.moving.quaternion.slerp(joint.targetQuaternion,blend);if(joint.targetPosition)joint.moving.position.lerp(joint.targetPosition,blend);});
      controls.update();renderer.render(scene,camera);positionForceLabels();
    };animate();view.classList.add('model-ready');Motion.show($('forceLabels'),$('showForces').checked,{duration:380});Motion.show($('forceLines'),$('showForces').checked,{duration:380});
  }catch(e){text($('modelLoadingText'),'模型加载失败：'+e.message);console.error(e);}
}
function setPose(joints){if(!modelReady)return;for(const j of modelJoints){if(j.type==='revolute'){const index=Number(j.name.replace('joint',''))-1;const angle=(joints[index]?.motor_pos_deg??0)*Math.PI/180;j.targetQuaternion=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(...j.axis),angle);}else if(j.type==='prismatic'){const opening=THREE.MathUtils.clamp((joints[6]?.motor_pos_deg??0)/270,0,1)*.05;j.targetPosition=new THREE.Vector3(...j.axis).multiplyScalar(opening);}}}
function highlightModel(){updateForces();}
function updateForces(){
  const scale=Number($('heatScale').value),options={fresh:forceFresh,source:forceSource,metric:forceMetric,scale};
  text($('forceStatus'),!latest?'等待关节数据':forceSource==='replay'?'历史回放 · 非实时受力':forceFresh?'实时受力 · N·m':'数据过期 · 保留最后姿态');
  forceElements.forEach((item,i)=>{
    const visual=torqueVisual(latest?.joints?.[i],options),active=selected===i,available=visual.value!==null;
    item.label.style.setProperty('--heat',visual.color);item.line.style.setProperty('--heat',visual.color);item.value.textContent=fmt(visual.value);
    text(item.level,!latest?'等待':!forceFresh?'已过期':available?`${visual.level} · ${Math.round(visual.ratio*100)}%`:'无效 / 缺失');
    item.label.classList.toggle('unavailable',!available);item.label.classList.toggle('selected',active);
    item.label.setAttribute('aria-label',`J${i+1} ${names[i]}，${forceSource==='replay'?'历史回放，':''}${forceMetric==='torque_nm'?'电机扭矩':'模型剩余力矩'} ${available?fmt(visual.value)+' N·m':!forceFresh&&latest?'数据过期':'暂无有效数据'}`);
    if(!modelReady)return;
    forceMarkers[i].material.color.set(visual.color);forceMarkers[i].userData.selected=active;
    const links=i<6?[`link${i+1}`]:['gripper_end','gripper_left','gripper_right'];
    for(const name of links)for(const mesh of linkGroups[name].children){
      if(!mesh.userData.baseColor)continue;
      mesh.userData.targetColor=mesh.userData.baseColor.clone().lerp(new THREE.Color(visual.color),available ? .15+visual.ratio*.35 : .08);
      mesh.userData.targetEmissive=new THREE.Color(available?visual.color:0x000000);mesh.userData.targetIntensity=available ? (active ? .22 : .1) : 0;
    }
  });
}
const projectedPoint=new THREE.Vector3();
function positionForceLabels(){
  if(!modelReady||$('forceLabels').hidden)return;
  const width=$('viewport').clientWidth,height=$('viewport').clientHeight,labelWidth=forceElements[0].label.offsetWidth,labelHeight=forceElements[0].label.offsetHeight;
  const projected=forceAnchors.map((anchor,i)=>{anchor.getWorldPosition(projectedPoint);projectedPoint.project(camera);return {i,x:(projectedPoint.x+1)*width/2,y:(1-projectedPoint.y)*height/2,visible:Math.abs(projectedPoint.z)<=1&&Math.abs(projectedPoint.x)<=1&&Math.abs(projectedPoint.y)<=1};});
  for(const side of [[0,1,2],[3,4,5,6]]){
    const items=side.map(i=>projected[i]).sort((a,b)=>a.y-b.y),gap=labelHeight+9,minY=94,maxY=height-43-labelHeight;
    const positions=items.map((point,index)=>Math.max(minY+index*gap,Math.min(maxY,point.y-labelHeight/2)));
    for(let k=1;k<positions.length;k++)positions[k]=Math.max(positions[k],positions[k-1]+gap);
    if(positions.at(-1)>maxY){positions[positions.length-1]=maxY;for(let k=positions.length-2;k>=0;k--)positions[k]=Math.min(positions[k],positions[k+1]-gap);}
    items.forEach((point,index)=>{
      const left=side[0]===0,x=left?14:width-labelWidth-14,y=positions[index],item=forceElements[point.i];
      const position=item.position||(item.position={x,y});
      const blend=Motion.reducedMotion()?1:.22;position.x+=(x-position.x)*blend;position.y+=(y-position.y)*blend;
      item.label.style.transform=`translate(${position.x}px,${position.y}px)`;item.line.style.opacity=point.visible ? '.3' : '0';
      const fromX=left?position.x+labelWidth:position.x,fromY=position.y+labelHeight/2,elbow=left?fromX+12:fromX-12;
      item.line.setAttribute('d',`M ${fromX} ${fromY} L ${elbow} ${fromY} L ${point.x} ${point.y}`);
    });
  }
}
async function init(){
  initInterface();buildTables();initLanguage(()=>{navIndicator();metricIndicator();drawTrend();Motion.animate($('contentSurface'),[{opacity:.7},{opacity:1}],{duration:200});});Motion.enter($('jointRows'));drawTrend();new ResizeObserver(drawTrend).observe($('trend'));initModel();
  try{boot=await api('/api/bootstrap');token=boot.token;settings=boot.settings;text($('version'),'v'+boot.version);buildParams();poll();}
  catch(e){networkFailed=true;setButtons();notice('网页初始化失败：'+e.message,'error');}
}
window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});init();
