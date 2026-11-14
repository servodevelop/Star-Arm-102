import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';

const source=await readFile(new URL('../stararm_rs_damping/web/app.js',import.meta.url),'utf8');
const html=await readFile(new URL('../stararm_rs_damping/web/index.html',import.meta.url),'utf8');
const actual=name=>{
  const prefix=`^(?:async )?function ${name}\\([^\\n]*\\)\\{`;
  const match=source.match(new RegExp(prefix+'[^\\n]*\\}$','m'))||source.match(new RegExp(prefix+'[\\s\\S]*?^\\}','m'));
  assert.ok(match,`test the actual ${name} implementation`);return match[0];
};
const plain=value=>JSON.parse(JSON.stringify(value));
function element(){
  return {value:'',checked:false,disabled:false,hidden:false,textContent:'',className:'',style:{},dataset:{},
    classList:{toggle(){},add(){},remove(){}},setAttribute(name,value){this[name]=String(value);}};
}
function number(value,min,max,step=1){
  const input=Object.assign(element(),{min,max,step,required:true});let raw=String(value);
  Object.defineProperty(input,'value',{get:()=>raw,set:value=>{raw=String(value);}});
  input.checkValidity=()=>raw.trim()!==''&&Number.isFinite(Number(raw))&&Number(raw)>=Number(input.min)&&Number(raw)<=Number(input.max)&&(input.step==='any'||Number.isInteger(Number(raw)));
  return input;
}
const lock={enabled:true,hold_mw:1200,contact_torque_nm:.45,release_torque_nm:.2,contact_dwell_s:.12,release_dwell_s:.1,open_release_leader_deg:.4,open_release_dwell_s:.06,closing_sign:-1,extra_fixed_field:'preserve'};
const original={format:'stararm-rs-unloaded-damping-v1',revision:3,damping_enabled:true,joint_damping_mw:Array(7).fill(100),gripper_lock:lock};
const fields={contact_torque_nm:[.05,5,'接触扭矩阈值','Nm'],release_torque_nm:[.01,5,'释放扭矩阈值','Nm'],contact_dwell_s:[.04,1,'接触确认时间','s'],release_dwell_s:[.04,1,'失物释放确认时间','s'],open_release_leader_deg:[.1,5,'反向解锁角度','°'],open_release_dwell_s:[.02,.5,'反向解锁确认时间','s']};
const ids=[...html.matchAll(/id="([^"]+)"/g)].map(match=>match[1]);
assert.equal(new Set(ids).size,ids.length,'each static DOM target is unique');
const elements=Object.fromEntries(ids.map(id=>[id,element()]));
elements.gripperHoldPower=number(1200,100,1500);
const lockFields=[...html.matchAll(/<input id="([^"]+)" data-lock-field="([^"]+)"[^>]*>/g)].map(([,id,key])=>{
  const input=Object.assign(number(lock[key],0,0,'any'),{id,dataset:{lockField:key}});elements[id]=input;return input;
});
assert.equal(lockFields.length,6);
let powers=[];
elements.dampingRows={set innerHTML(value){powers=[...value.matchAll(/data-damping-index="(\d+)" min="(\d+)" max="(\d+)" step="1" required value="(\d+)"/g)].map(([,index,min,max,value])=>Object.assign(number(value,min,max),{dataset:{dampingIndex:index}}));}};
for(let i=0;i<7;i++)for(const key of ['pos','torque','current','mode','power'])elements[key+i]=element();
const body=element(),timerCallbacks=new Map();let timerId=0,now=1000;
const context=vm.createContext({structuredClone,$:id=>elements[id],
  names:['底座回转','肩部俯仰','肘部俯仰','腕部俯仰','腕部偏转','腕部旋转','夹爪'],colors:Array(7).fill('#000'),
  finite:value=>typeof value==='number'&&Number.isFinite(value),fmt:(value,places=2)=>typeof value==='number'&&Number.isFinite(value)?value.toFixed(places):'—',
  performance:{now:()=>now},setTimeout:(fn,delay)=>{timerCallbacks.set(++timerId,{fn,delay});return timerId;},clearTimeout:id=>timerCallbacks.delete(id),
  document:{body,querySelectorAll(selector){if(selector==='[data-lock-field]')return lockFields;if(selector==='[data-damping-index]')return powers;if(selector==='.params-panel input')return [elements.dampingEnabled,elements.gripperLockEnabled,elements.gripperHoldPower,...powers,...lockFields];return [];}},
  Motion:{text:(el,value)=>{el.textContent=String(value);},show:(el,visible)=>{el.hidden=!visible;}},
  poseTimeline:{samples:[],push(...sample){this.samples.push(sample);},clear(){this.samples=[];}},
  updateForces(){},api:async()=>{throw new Error('mock API not configured');}
});
const functions=['text','notice','markDirty','lockInputs','dampingInputs','lockTuningSupported','formDraft','restoreDraft','buildParams','collectSettings','restoreDampingDefaults','saveSettings','setButtons','startSession','stopSession','leaderReadback','frameAgeNow','updateDetail','gripperLockView','renderGripperLock','renderTelemetry','clearTelemetry','renderStatus','poll','loadLog'];
vm.runInContext(`let settings=${JSON.stringify(original)},boot={defaults:${JSON.stringify(original)},gripper_fields:${JSON.stringify(fields)}};
  let dirty=false,editRevision=0,selected=0,latest=null,latestStatus=null,busy=false,saving=false,networkFailed=false,statusEpoch=0,startPending=false;
  let forceFresh=false,freshDeadline=0,readbackTimer=null,noticeSource='welcome',frameArrivalMs=0,frameAgeAtArrival=Infinity;
  ${functions.map(actual).join('\n')}`,context);
const run=code=>vm.runInContext(code,context);

run('buildParams()');
assert.deepEqual(powers.map(input=>Number(input.value)),Array(7).fill(100),'all seven default powers, including J3, must be 100 mW');
assert.equal(elements.dampingEnabled.checked,true);
assert.equal(elements.gripperLockEnabled.checked,true);
assert.ok(lockFields.every(input=>!input.disabled));
assert.deepEqual(plain(run('collectSettings()')),original);
for(let index=0;index<7;index++){
  const input=powers[index];
  for(const invalid of ['', ' ', '-1', '1501', '100.5', 'NaN', 'Infinity']){
    input.value=invalid;assert.throws(()=>run('collectSettings()'),new RegExp(`J${index+1} 固定阻尼`));
  }
  for(const boundary of [0,1500]){input.value=boundary;assert.equal(run('collectSettings().joint_damping_mw')[index],boundary);}
  input.value=100;
}
elements.dampingEnabled.checked=false;
assert.equal(run('collectSettings().damping_enabled'),false);
assert.equal(run('collectSettings().gripper_lock.enabled'),true,'fixed damping switch must not disable independent gripper lock');
assert.deepEqual(plain(run('settings')),original,'collecting must not change saved or running settings');
elements.gripperLockEnabled.checked=false;powers[6].value='450';
assert.equal(run('collectSettings().joint_damping_mw[6]'),450);
assert.equal(run('collectSettings().gripper_lock.enabled'),false);

elements.gripperLockEnabled.checked=true;elements.gripperHoldPower.value='1390';
elements.openAngle.value='.3';elements.openDwell.value='';powers[2].value='';
run('markDirty();buildParams()');
assert.equal(powers[2].value,'','form rebuild must preserve invalid unsaved fixed damping');
assert.equal(elements.openDwell.value,'','form rebuild must preserve invalid unsaved lock timing');
assert.equal(elements.openAngle.value,'.3');assert.equal(elements.gripperHoldPower.value,'1390');
run('restoreDampingDefaults()');
assert.deepEqual(powers.map(input=>Number(input.value)),Array(7).fill(100));
assert.equal(elements.dampingEnabled.checked,true);
assert.equal(elements.gripperLockEnabled.checked,true);
assert.equal(elements.openDwell.value,'','damping defaults must preserve all gripper drafts, including blanks');
assert.equal(elements.openAngle.value,'.3');assert.equal(elements.gripperHoldPower.value,'1390');
assert.deepEqual(plain(run('settings')),original,'default restoration must not mutate saved values');
assert.throws(()=>run('collectSettings()'),/反向解锁确认时间/);
elements.openDwell.value='.04';
for(const input of lockFields){
  const valid=input.value;
  for(const invalid of ['', 'NaN', 'Infinity', String(fields[input.dataset.lockField][1]+.01)]){input.value=invalid;assert.throws(()=>run('collectSettings()'),/有限数值/);}
  input.value=valid;
}
elements.releaseTorque.value='.45';assert.throws(()=>run('collectSettings()'),/必须小于/);elements.releaseTorque.value='.2';
for(const invalid of ['',99,1501,100.5]){elements.gripperHoldPower.value=invalid;assert.throws(()=>run('collectSettings()'),/100–1500/);}elements.gripperHoldPower.value=1390;
run('dirty=false');powers[0].oninput();assert.equal(run('dirty'),true);run('dirty=false');elements.gripperLockEnabled.onchange();assert.equal(run('dirty'),true);

const writes=[];
context.api=async(path,body)=>{writes.push({path,body:plain(body)});return {...plain(body),revision:4};};
run('latestStatus={running:true}');await run('saveSettings()');
assert.equal(writes.length,1);assert.equal(writes[0].path,'/api/settings');assert.equal(writes[0].body.revision,3);
assert.deepEqual(writes[0].body.joint_damping_mw,Array(7).fill(100));assert.equal(writes[0].body.gripper_lock.extra_fixed_field,'preserve');
assert.equal(run('settings.revision'),4);assert.equal(run('dirty'),false);assert.match(elements.noticeText.textContent,/等待控制循环确认/);
context.api=async(path,body)=>{elements.gripperHoldPower.value='1400';run('markDirty()');return {...plain(body),revision:5};};
await run('saveSettings()');assert.equal(run('dirty'),true,'edits made while saving must remain unsaved');assert.equal(elements.gripperHoldPower.value,'1400');

run('delete boot.gripper_fields;delete settings.gripper_lock.open_release_dwell_s;buildParams()');
assert.ok(lockFields.every(input=>input.disabled));assert.equal(elements.gripperUnavailable.hidden,false);
assert.equal(elements.gripperLockEnabled.disabled,false,'missing tuning metadata must keep existing lock switch and power available');
assert.equal(Object.hasOwn(plain(run('collectSettings().gripper_lock')),'open_release_dwell_s'),false,'compatibility must not fabricate settings');

const freshJoint={motor_pos_deg:12,torque_nm:-.8,current_a:.32,leader_mode:'DAMPING',leader_power_mw:100,leader_pos_deg:20,leader_monitor_age_s:.05,leader_current_a:.01,leader_measured_power_mw:90,leader_voltage_v:8.2};
context.frame={monotonic_s:10,run_id:'new-project',damping_enabled:true,joints:Array.from({length:7},()=>({...freshJoint})),gripper_lock:{enabled:true,phase:'LOCKED',power_mw:1200,reason:'closing contact confirmed'}};
context.frame.joints[6]={...freshJoint,leader_mode:'HOLD',leader_power_mw:1200};
run('renderTelemetry(frame,true,.02)');
assert.equal(elements.pos0.textContent,'12.0');assert.equal(elements.torque0.textContent,'-0.80');assert.equal(elements.current0.textContent,'0.32');
assert.equal(elements.mode0.textContent,'DAMPING');assert.equal(elements.power0.textContent,'100');assert.equal(elements.mode6.textContent,'HOLD');assert.equal(elements.power6.textContent,'1200');
assert.equal(elements.activeCount.textContent,'6');assert.equal(elements.gripperLockPhase.textContent,'接触保持');assert.equal(elements.gripperLockPower.textContent,'1200 mW');
assert.equal(elements.selectedPower.textContent,'90 mW','measured Leader power must remain distinct from the request');
const expiry=[...timerCallbacks.values()].at(-1);assert.ok(Math.abs(expiry.delay-180)<1e-7);expiry.fn();assert.equal(elements.selectedPower.textContent,'—');
now+=300;run('updateDetail()');assert.equal(elements.selectedPower.textContent,'—','selecting or redrawing details cannot revive expired measured readback');
for(const age of [null,NaN,Infinity,-1,.251]){
  context.joint={...freshJoint,leader_monitor_age_s:age};assert.equal(run('leaderReadback(joint,true).power'),null);
}
for(const value of [NaN,Infinity,null,undefined]){context.joint={...freshJoint,leader_measured_power_mw:value};assert.equal(run('leaderReadback(joint,true).power'),null);}
context.joint={...freshJoint,leader_measured_power_mw:0};assert.equal(run('leaderReadback(joint,true).power'),0);
run('renderTelemetry(frame,false)');
for(const key of ['torque','current','power'])assert.equal(elements[key+'0'].textContent,'—');
assert.equal(elements.pos0.textContent,'12.0','stale state may retain last posture with an explicit expired tag');
assert.equal(elements.mode0.textContent,'—');assert.equal(elements.gripperLockPhase.textContent,'状态未确认');assert.equal(elements.gripperLockPower.textContent,'—');
assert.equal(elements.selectedPower.textContent,'—');
context.frame.gripper_lock={enabled:true,phase:'FREE',power_mw:0,reason:'waiting for contact'};context.frame.joints[6]={...freshJoint,leader_mode:'FREE',leader_power_mw:0};
run('renderTelemetry(frame,true,0)');assert.equal(elements.mode6.textContent,'FREE');assert.equal(elements.gripperLockPhase.textContent,'自由');

context.status={phase:'running',running:true,fresh:true,age_s:.04,saved_revision:5,telemetry:{...context.frame,applied_revision:5}};
run('noticeSource="welcome";renderStatus(status)');assert.equal(elements.session.textContent,'运行中');assert.equal(elements.revision.textContent,'已应用 v5 / 已保存 v5');assert.equal(elements.notice.hidden,true);
assert.equal(elements.start.disabled,true);assert.equal(elements.stop.disabled,false);
context.status.telemetry.settings_error='invalid';run('renderStatus(status)');assert.match(elements.noticeText.textContent,/参数未应用：invalid/);
context.status.telemetry.settings_error=null;run('clearTelemetry()');assert.equal(elements.gripperLockPhase.textContent,'等待数据');assert.equal(elements.pos0.textContent,'—');

const calls=[];context.api=async(path,body)=>{calls.push({path,body});return {phase:'connecting',running:true,fresh:false,age_s:null,saved_revision:5};};
run('latestStatus={running:false};dirty=true');await run('startSession()');assert.equal(calls.length,0,'dirty start must never connect the robot');
run('dirty=false');await run('startSession()');assert.equal(calls.length,1);assert.equal(calls[0].path,'/api/start');assert.deepEqual(plain(calls[0].body),{mode:'teleop'});
await run('startSession()');assert.equal(calls.length,1,'running session must not be launched twice');
await run('stopSession()');assert.equal(calls[1].path,'/api/stop');assert.deepEqual(plain(calls[1].body),{});assert.match(elements.noticeText.textContent,/等待回零或卸力完成/);

let resolveState,resolveStart;
const pendingState=new Promise(resolve=>{resolveState=resolve;}),pendingStart=new Promise(resolve=>{resolveStart=resolve;});
context.api=(path)=>path==='/api/state'?pendingState:pendingStart;
run('latestStatus={running:false};dirty=false');const polling=run('poll()'),starting=run('startSession()');
resolveState({phase:'exited',running:false,fresh:false,age_s:null,exit_code:1,saved_revision:4});await polling;
assert.match(elements.noticeText.textContent,/正在连接/,'an old state response must not overwrite the active startup notice');
resolveStart({phase:'connecting',running:true,fresh:false,age_s:null,saved_revision:5});await starting;
assert.equal(elements.session.textContent,'连接中');
context.api=async()=>({text:'test session text'});await run('loadLog()');assert.equal(elements.log.textContent,'test session text');

assert.doesNotMatch(source,/residual_nm|deadzone_nm|gripper_follow_mode|\/api\/replay|mode:'feedback'/,'the independent UI must not expose old load feedback or fast-follow controls');
assert.match(source,/new PoseTimeline\(\)/);assert.match(source,/labelColumns\(width,height,labelWidth,labelHeight\)/);
assert.doesNotMatch(source.match(/async function init\(\)\{[\s\S]*?\n\}/)[0],/startSession\(\)/,'opening the page must not start hardware');
assert.match(html,/默认七轴均为 100 mW/);assert.match(html,/J7 固定阻尼仅在夹爪锁止关闭时生效/);assert.match(html,/未接触和释放后均为 FREE/);
console.log('Unloaded damping UI: actual settings validation, all-seven 100 mW defaults, independent J7 lock, draft/default/save preservation, teleop start/stop, startup race, measured readback expiry and stale telemetry passed with mock APIs; no hardware access.');
