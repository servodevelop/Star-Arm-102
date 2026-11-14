import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {STLLoader} from './vendor/STLLoader.js';
import {finite,torqueVisual} from './torque.js';
import * as Motion from './motion.js';
import {PoseTimeline,labelColumns} from './presentation.js';

const $=id=>document.getElementById(id);
const names=['底座回转','肩部俯仰','肘部俯仰','腕部俯仰','腕部偏转','腕部旋转','夹爪'];
const colors=['#2563eb','#d97706','#0d9488','#7c3aed','#c2417e','#4d7c0f','#64748b'];
const fmt=(value,places=2)=>finite(value)?value.toFixed(places):'—';
const poseTimeline=new PoseTimeline();
const forceElements=[],forceMarkers=[],forceAnchors=[];
let token='',settings=null,boot=null,dirty=false,editRevision=0,selected=0,latest=null,latestStatus=null;
let busy=false,saving=false,networkFailed=false,statusEpoch=0,startPending=false,activeView='workspace';
let forceFresh=false,forceSource='live',freshDeadline=0,readbackTimer=null,noticeSource='welcome',frameArrivalMs=0,frameAgeAtArrival=Infinity;
function text(element,value){Motion.text(element,String(value));}
function notice(message,type='',source='user'){
  noticeSource=source;text($('noticeText'),message);$('notice').className='notice '+type;
  if($('notice').hidden||$('notice').inert)Motion.show($('notice'),true,{collapse:true});
}
async function api(path,body){
  const response=await fetch(path,{method:body===undefined?'GET':'POST',headers:body===undefined?{}:{'Content-Type':'application/json','X-RS-Token':token},body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(4000)});
  const data=await response.json();if(!response.ok)throw new Error(data.error||`HTTP ${response.status}`);return data;
}
function markDirty(){dirty=true;editRevision++;text($('dirty'),'未保存');$('dirty').className='tag pending';}
function lockInputs(){return [...document.querySelectorAll('[data-lock-field]')];}
function dampingInputs(){return [...document.querySelectorAll('[data-damping-index]')];}
function lockTuningSupported(){
  return lockInputs().length===6&&lockInputs().every(input=>{
    const key=input.dataset.lockField,field=boot.gripper_fields?.[key];
    return Array.isArray(field)&&field.length===4&&finite(field[0])&&finite(field[1])&&field[0]<field[1]&&finite(settings.gripper_lock?.[key]);
  });
}
function formDraft(){
  return {damping:$('dampingEnabled').checked,powers:dampingInputs().map(input=>input.value),lock:$('gripperLockEnabled').checked,hold:$('gripperHoldPower').value,
    fields:Object.fromEntries(lockInputs().map(input=>[input.dataset.lockField,input.value]))};
}
function restoreDraft(draft){
  $('dampingEnabled').checked=draft.damping;
  dampingInputs().forEach((input,i)=>{if(i<draft.powers.length)input.value=draft.powers[i];});
  if(!$('gripperLockEnabled').disabled)$('gripperLockEnabled').checked=draft.lock;
  if(!$('gripperHoldPower').disabled)$('gripperHoldPower').value=draft.hold;
  for(const input of lockInputs())if(!input.disabled&&Object.hasOwn(draft.fields,input.dataset.lockField))input.value=draft.fields[input.dataset.lockField];
}
function buildParams(){
  const draft=dirty?formDraft():null;
  $('dampingEnabled').checked=settings.damping_enabled;
  $('dampingRows').innerHTML=names.map((name,i)=>`<label class="axis-setting"><span><b style="--axis:${colors[i]}">J${i+1}</b><small>${name}</small></span><span><input type="number" data-damping-index="${i}" min="0" max="1500" step="1" required value="${settings.joint_damping_mw[i]}" aria-label="J${i+1} 固定阻尼功率"><em>mW</em></span></label>`).join('');
  const lock=settings.gripper_lock,supported=typeof lock?.enabled==='boolean'&&Number.isInteger(lock.hold_mw),tuning=supported&&lockTuningSupported();
  $('gripperLockEnabled').disabled=$('gripperHoldPower').disabled=!supported;
  $('gripperLockEnabled').checked=supported&&lock.enabled;$('gripperHoldPower').value=supported?lock.hold_mw:'';
  $('gripperUnavailable').hidden=tuning;
  for(const input of lockInputs()){
    const key=input.dataset.lockField,field=boot.gripper_fields?.[key];input.disabled=!tuning;input.value=tuning?lock[key]:'';
    if(tuning){input.min=field[0];input.max=field[1];text($(input.id+'Range'),`${field[0]}–${field[1]} ${field[3]}`);}
    else text($(input.id+'Range'),'更新网页服务后可调');
  }
  if(draft)restoreDraft(draft);
  for(const input of document.querySelectorAll('.params-panel input'))input.oninput=input.onchange=markDirty;
}
function collectSettings(){
  const next=structuredClone(settings),powers=dampingInputs();
  if(next.format!=='stararm-rs-unloaded-damping-v1'||powers.length!==7)throw new Error('配置格式不正确，请重新连接本项目网页服务。');
  next.damping_enabled=$('dampingEnabled').checked;
  next.joint_damping_mw=powers.map((input,i)=>{
    const value=Number(input.value);
    if(String(input.value).trim()===''||!Number.isInteger(value)||value<0||value>1500||!input.checkValidity())throw new Error(`J${i+1} 固定阻尼须为 0–1500 mW 的整数`);
    return value;
  });
  if(!$('gripperLockEnabled').disabled){
    const input=$('gripperHoldPower'),value=Number(input.value);
    if(String(input.value).trim()===''||!Number.isInteger(value)||value<100||value>1500||!input.checkValidity())throw new Error('夹爪保持功率须为 100–1500 mW 的整数');
    next.gripper_lock.enabled=$('gripperLockEnabled').checked;next.gripper_lock.hold_mw=value;
    if(lockTuningSupported()){
      for(const input of lockInputs()){
        const key=input.dataset.lockField,[lo,hi,label,unit]=boot.gripper_fields[key],value=Number(input.value);
        if(String(input.value).trim()===''||!finite(value)||value<lo||value>hi||!input.checkValidity())throw new Error(`${label}须为 ${lo}–${hi} ${unit} 范围内的有限数值`);
        next.gripper_lock[key]=value;
      }
      if(next.gripper_lock.release_torque_nm>=next.gripper_lock.contact_torque_nm)throw new Error('释放扭矩阈值必须小于接触扭矩阈值');
    }
  }
  return next;
}
function restoreDampingDefaults(){
  $('dampingEnabled').checked=boot.defaults.damping_enabled;
  dampingInputs().forEach((input,i)=>{input.value=boot.defaults.joint_damping_mw[i];});markDirty();
  notice('已恢复七轴固定阻尼默认值，夹爪锁止编辑已保留；点击保存并应用后生效。');
}
async function saveSettings(){
  if(saving)return;
  try{const next=collectSettings(),atSave=editRevision;saving=true;$('save').disabled=true;settings=await api('/api/settings',next);dirty=editRevision!==atSave;
    text($('dirty'),dirty?'未保存':'已保存');$('dirty').className='tag'+(dirty?' pending':'');
    notice(latestStatus?.running?'参数已保存，等待控制循环确认；请查看已应用版本。':'参数已保存，下次启动时生效。','success');
  }catch(error){notice(error.message,'error');}finally{saving=false;$('save').disabled=false;}
}
function setButtons(){
  const running=latestStatus?.running===true;
  $('start').disabled=busy||running||networkFailed||!settings;
  $('stop').disabled=busy||!running||latestStatus?.stop_requested===true||networkFailed;
}
async function startSession(){
  if(busy||latestStatus?.running)return;
  if(dirty){notice('有未保存参数，请先保存并应用。','error');return;}
  busy=true;startPending=true;statusEpoch++;setButtons();
  try{clearTelemetry();notice('正在连接机械臂，请查看运行日志。','','connecting');renderStatus(await api('/api/start',{mode:'teleop'}));}
  catch(error){notice(error.message,'error');}finally{startPending=false;busy=false;setButtons();}
}
async function stopSession(){
  if(busy)return;busy=true;setButtons();
  try{renderStatus(await api('/api/stop',{}));notice('已发送正常停止请求，等待回零或卸力完成。');}
  catch(error){notice(error.message,'error');}finally{busy=false;setButtons();}
}
function navigate(view){
  activeView=view;
  document.querySelectorAll('[data-view]').forEach(button=>button.setAttribute('aria-selected',String(button.dataset.view===view)));
  document.querySelectorAll('[data-page]').forEach(page=>{page.hidden=page.dataset.page!==view;});
  text($('pageTitle'),{workspace:'空载阻尼工作台',parameters:'固定阻尼与夹爪锁止',logs:'会话运行日志'}[view]);
  if(view==='logs')loadLog();
}
function selectJoint(index){
  selected=index;
  for(const row of $('jointRows').rows){const chosen=Number(row.dataset.joint)===index;row.classList.toggle('selected',chosen);row.setAttribute('aria-selected',String(chosen));}
  updateDetail();updateForces();
}
function buildTables(){
  $('jointRows').innerHTML=names.map((name,i)=>`<tr data-joint="${i}" tabindex="0" aria-selected="${i===selected}" class="${i===selected?'selected':''}"><td><div class="joint-name"><i style="background:${colors[i]}"></i><span>J${i+1}<small>${name}</small></span></div></td><td id="pos${i}">—</td><td id="torque${i}">—</td><td id="current${i}">—</td><td><span id="mode${i}" class="mode UNKNOWN">—</span><b id="power${i}" class="power-value">—</b></td></tr>`).join('');
  for(const row of $('jointRows').rows){row.onclick=()=>selectJoint(Number(row.dataset.joint));row.onkeydown=event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();selectJoint(Number(row.dataset.joint));}};}
  names.forEach((name,i)=>{
    const label=document.createElement('button');label.className='force-label unavailable';label.setAttribute('aria-pressed',String(i===selected));
    label.innerHTML=`<span><span class="force-axis">J${i+1}</span><span class="force-level">等待</span></span><span><b>—</b><em>Nm</em></span>`;label.onclick=()=>selectJoint(i);$('forceLabels').appendChild(label);
    const line=document.createElementNS('http://www.w3.org/2000/svg','path');$('forceLines').appendChild(line);
    forceElements.push({label,line,value:label.querySelector('b'),level:label.querySelector('.force-level')});
  });
}
function leaderReadback(joint,fresh,frameAgeS=0){
  const age=joint?.leader_monitor_age_s;
  if(!fresh||!finite(frameAgeS)||frameAgeS<0||!finite(age)||age<0||age+frameAgeS>.25)return {current:null,power:null,voltage:null,age:null};
  return {current:finite(joint.leader_current_a)?joint.leader_current_a:null,power:finite(joint.leader_measured_power_mw)?joint.leader_measured_power_mw:null,voltage:finite(joint.leader_voltage_v)?joint.leader_voltage_v:null,age:age+frameAgeS};
}
function frameAgeNow(){return frameAgeAtArrival+Math.max(0,performance.now()-frameArrivalMs)/1000;}
function updateDetail(frameAgeS=frameAgeNow()){
  clearTimeout(readbackTimer);readbackTimer=null;
  const joint=latest?.joints?.[selected],reading=leaderReadback(joint,forceFresh,frameAgeS);
  text($('selectedTitle'),`J${selected+1} ${names[selected]}`);text($('selectedReason'),!forceFresh?'等待新鲜设备数据':joint?.reason||'固定空载阻尼');
  text($('selectedLeader'),forceFresh&&finite(joint?.leader_pos_deg)?fmt(joint.leader_pos_deg,1)+'°':'—');
  text($('selectedCurrent'),reading.current===null?'—':fmt(reading.current)+' A');
  text($('selectedPower'),reading.power===null?'—':fmt(reading.power,0)+' mW');
  text($('selectedVoltage'),reading.voltage===null?'—':fmt(reading.voltage)+' V');
  if(reading.age!==null)readbackTimer=setTimeout(()=>{for(const id of ['selectedCurrent','selectedPower','selectedVoltage'])text($(id),'—');readbackTimer=null;},Math.max(0,.25-reading.age)*1000);
}
function gripperLockView(frame,fresh){
  const lock=frame?.gripper_lock;
  if(!fresh||!lock)return {label:lock?'状态未确认':'等待数据',mode:'UNKNOWN',power:null,reason:lock?'数据过期，不能确认夹爪已保持或释放。':'等待夹爪状态'};
  const labels={DISABLED:'锁止已关闭',FREE:'自由',CONTACT_CANDIDATE:'接触确认中',LOCKED:'接触保持',OPENING:'反向释放',INVALID:'状态无效'};
  const mode=lock.phase==='LOCKED'?'HOLD':Object.hasOwn(labels,lock.phase)&&lock.phase!=='INVALID'?'FREE':'UNKNOWN';
  const reasons={'waiting for contact':'等待夹爪接触','closing contact confirmed':'夹住物体，请求限力保持','Leader opening; hold released':'反向张开，保持已释放','Leader opening; waiting for reclosure':'夹爪张开中，等待重新合拢','object lost: closing torque released':'夹持力矩持续降低，保持已释放','object lost: gripper continued closing':'物体脱落，保持已释放','disabled':'夹爪锁止关闭，按固定阻尼设置输出'};
  return {label:labels[lock.phase]||'状态未确认',mode,power:mode==='UNKNOWN'?null:frame.output_enabled===false?0:lock.power_mw,reason:reasons[lock.reason]||lock.reason||'等待状态更新'};
}
function renderGripperLock(frame,fresh){
  const view=gripperLockView(frame,fresh);text($('gripperLockPhase'),view.label);$('gripperLockPhase').className='mode '+view.mode;
  text($('gripperLockPower'),finite(view.power)?fmt(view.power,0)+' mW':'—');text($('gripperLockReason'),view.reason);
}
function renderTelemetry(frame,fresh=true,frameAgeS=0){
  latest=frame;forceFresh=fresh;frameArrivalMs=performance.now();frameAgeAtArrival=frameAgeS;
  text($('source'),fresh?'实时 CAN':'数据已过期');$('source').className='tag '+(fresh?'live':'pending');
  const joints=frame.joints||[];let maximum=null,maxAxis=0,active=0;
  for(let i=0;i<7;i++){
    const joint=joints[i]||{},mode=fresh&&['FREE','DAMPING','HOLD'].includes(joint.leader_mode)?joint.leader_mode:'UNKNOWN';
    text($('pos'+i),fmt(joint.motor_pos_deg,1));text($('torque'+i),fresh?fmt(joint.torque_nm):'—');text($('current'+i),fresh?fmt(joint.current_a):'—');
    text($('mode'+i),mode==='UNKNOWN'?'—':mode);$('mode'+i).className='mode '+mode;text($('power'+i),fresh?fmt(joint.leader_power_mw,0):'—');
    if(fresh&&finite(joint.torque_nm)&&(maximum===null||Math.abs(joint.torque_nm)>maximum)){maximum=Math.abs(joint.torque_nm);maxAxis=i;}
    if(mode==='DAMPING'&&joint.leader_power_mw>0)active++;
  }
  text($('activeCount'),fresh?active:'—');text($('outputDetail'),fresh?frame.damping_enabled?'固定空载阻尼已启用':'固定阻尼关闭 · 夹爪锁独立':'等待新鲜设备数据');
  text($('maxTorque'),fmt(maximum));text($('maxTorqueJoint'),maximum===null?'RS 电机读回':`J${maxAxis+1} · ${names[maxAxis]}`);
  updateDetail(frameAgeS);renderGripperLock(frame,fresh);
  if(fresh)poseTimeline.push(joints,frame.monotonic_s,`live:${frame.run_id??''}`,performance.now());updateForces();
}
function clearTelemetry(){
  latest=null;forceFresh=false;poseTimeline.clear();clearTimeout(readbackTimer);readbackTimer=null;
  for(let i=0;i<7;i++){for(const key of ['pos','torque','current','power'])text($(key+i),'—');text($('mode'+i),'—');$('mode'+i).className='mode UNKNOWN';}
  for(const id of ['activeCount','maxTorque'])text($(id),'—');text($('source'),'等待数据');$('source').className='tag';text($('maxTorqueJoint'),'RS 电机读回');text($('outputDetail'),'等待实时数据');
  updateDetail();renderGripperLock(null,false);updateForces();
}
function renderStatus(data){
  latestStatus=data;networkFailed=false;setButtons();document.body.classList.toggle('stale',!data.fresh);
  const phases={idle:'未启动',connecting:'连接中',running:'运行中',stopping:'正在停止',exited:'已结束'};
  text($('session'),phases[data.phase]||'未知');text($('sessionDetail'),data.phase==='exited'?`退出代码 ${data.exit_code}`:'Star Arm 102 / B601 RS');
  text($('connection'),data.fresh?'实时数据已连接':data.running?'等待设备数据':'本地网页已连接');$('led').className='led '+(data.fresh?'green':data.running?'orange':'');
  const age=finite(data.age_s)&&data.age_s>=0?data.age_s:null;
  freshDeadline=data.fresh&&age!==null?performance.now()+Math.max(0,.8-age)*1000:0;
  text($('freshness'),data.fresh&&age!==null?`${Math.round(age*1000)} ms`:data.running?'等待数据':'—');
  const saved=data.saved_revision??settings?.revision??'—',applied=data.telemetry?.applied_revision;
  text($('revision'),data.running&&applied!==undefined?`已应用 v${applied} / 已保存 v${saved}${applied!==saved?' · 等待应用':''}`:`已保存 v${saved} · 启动后应用`);
  if(data.telemetry)renderTelemetry(data.telemetry,data.fresh,age??Infinity);else if(latest)clearTelemetry();
  if(data.telemetry?.settings_error)notice('参数未应用：'+data.telemetry.settings_error,'error','settings-error');
  else if(data.phase==='exited'&&![0,-2,null,undefined].includes(data.exit_code))notice(`会话已结束（退出代码 ${data.exit_code}），查看运行日志了解原因。`,'error','session-exit');
  else if(noticeSource==='network'||data.running&&['welcome','session-exit'].includes(noticeSource)||data.phase==='running'&&noticeSource==='connecting'){noticeSource='';Motion.show($('notice'),false,{collapse:true});}
}
async function poll(){
  const epoch=statusEpoch;
  try{if(!startPending){const data=await api('/api/state');if(epoch===statusEpoch&&!startPending)renderStatus(data);}}
  catch(error){if(epoch===statusEpoch&&!startPending){networkFailed=true;setButtons();document.body.classList.add('stale');text($('connection'),'网页服务连接中断');text($('freshness'),'已过期');$('led').className='led orange';if(latest)renderTelemetry(latest,false);notice('网页服务暂不可达；此状态不能确认机械臂已停止。','error','network');}}
  setTimeout(poll,latestStatus?.running?80:500);
}
async function loadLog(){
  try{text($('log'),(await api('/api/log')).text||'尚无运行日志');$('log').scrollTop=$('log').scrollHeight;}
  catch(error){text($('log'),'无法读取运行日志：'+error.message);}
}
function updateForces(){
  text($('forceStatus'),!latest?'等待关节数据':forceFresh?'RS 实际电机扭矩 · Nm':'数据过期 · 保留最后姿态');
  forceElements.forEach((item,i)=>{
    const visual=torqueVisual(latest?.joints?.[i],{fresh:forceFresh,source:'live',metric:'torque_nm',scale:Number($('heatScale').value)}),available=visual.value!==null,active=i===selected;
    item.label.style.setProperty('--heat',visual.color);item.line.style.setProperty('--heat',visual.color);text(item.value,fmt(visual.value));
    text(item.level,!latest?'等待':!forceFresh?'已过期':available?visual.level:'无数据');item.label.classList.toggle('unavailable',!available);item.label.classList.toggle('selected',active);item.label.setAttribute('aria-pressed',String(active));
    item.label.setAttribute('aria-label',`J${i+1} ${names[i]}，实际扭矩 ${available?fmt(visual.value)+' Nm':'暂无有效数据'}`);
    if(!modelReady)return;
    forceMarkers[i].material.color.set(visual.color);forceMarkers[i].userData.selected=active;
    for(const name of i<6?[`link${i+1}`]:['gripper_end','gripper_left','gripper_right'])for(const mesh of linkGroups[name].children){
      if(!mesh.userData.baseColor)continue;mesh.userData.targetColor=mesh.userData.baseColor.clone().lerp(new THREE.Color(visual.color),available ? .15+visual.ratio*.35 : .08);
      mesh.userData.targetEmissive=new THREE.Color(available?visual.color:0x000000);mesh.userData.targetIntensity=available?(active ? .22 : .1):0;
    }
  });
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
    renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.shadowMap.enabled=true;renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.2;
    view.appendChild(renderer.domElement);controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.minDistance=.3;controls.maxDistance=3.;controls.maxPolarAngle=Math.PI*.49;resetView();
    scene.add(new THREE.HemisphereLight(0xffffff,0xa7b6cd,2.1));const sun=new THREE.DirectionalLight(0xf9fbff,3);sun.position.set(1,-1,2);sun.castShadow=true;sun.shadow.mapSize.set(1024,1024);sun.shadow.camera.left=-1;sun.shadow.camera.right=1;sun.shadow.camera.top=1;sun.shadow.camera.bottom=-1;sun.shadow.bias=-.0005;scene.add(sun);
    const rim=new THREE.DirectionalLight(0xdde9ff,2);rim.position.set(-1,.5,1);scene.add(rim);
    const grid=new THREE.GridHelper(2,40,0xd4deed,0xe9eef5);grid.rotation.x=Math.PI/2;grid.position.z=-.001;scene.add(grid);
    const floor=new THREE.Mesh(new THREE.PlaneGeometry(5,5),new THREE.ShadowMaterial({opacity:.12}));floor.position.z=-.002;floor.receiveShadow=true;scene.add(floor);
    const model=await(await fetch('model/robot.json')).json();robotGroup=new THREE.Group();scene.add(robotGroup);
    for(const link of model.links){const group=new THREE.Group();group.name=link.name;linkGroups[link.name]=group;}
    robotGroup.add(linkGroups[model.root]);
    for(const joint of model.joints){const base=new THREE.Group(),moving=new THREE.Group();poseObject(base,joint);base.add(moving);moving.add(linkGroups[joint.child]);linkGroups[joint.parent].add(base);modelJoints.push({...joint,base,moving,axisVector:new THREE.Vector3(...joint.axis),lastValue:null});
      if(joint.type==='revolute'){const helper=new THREE.AxesHelper(.055);helper.visible=false;helper.material.transparent=true;helper.material.opacity=0;base.add(helper);axes.push(helper);}}
    for(let i=0;i<7;i++){
      const anchor=i<6?modelJoints.find(j=>j.name===`joint${i+1}`).base:linkGroups.gripper_end;
      const marker=new THREE.Mesh(new THREE.SphereGeometry(.009,16,12),new THREE.MeshBasicMaterial({color:0x92a29e,depthTest:false,transparent:true,opacity:.85}));marker.renderOrder=5;anchor.add(marker);forceAnchors.push(anchor);forceMarkers.push(marker);
    }
    const loader=new STLLoader(),cache=new Map();let completed=0,total=model.links.reduce((n,l)=>n+l.visuals.length,0);
    const tasks=model.links.flatMap(link=>link.visuals.map(async v=>{
      if(!cache.has(v.mesh))cache.set(v.mesh,loader.loadAsync(v.mesh));const geometry=await cache.get(v.mesh);geometry.computeVertexNormals();
      const baseColor=new THREE.Color(...v.color.slice(0,3));if(v.color[1]>.5&&v.color[0]<v.color[1])baseColor.set(v.color[0]>.5?0x7f96b6:0x333c4a);const material=new THREE.MeshStandardMaterial({color:baseColor,metalness:.48,roughness:.5});const mesh=new THREE.Mesh(geometry,material);mesh.userData.baseColor=material.color.clone();modelMeshes.push(mesh);mesh.castShadow=true;mesh.receiveShadow=true;mesh.scale.fromArray(v.scale);poseObject(mesh,v);linkGroups[link.name].add(mesh);text($('modelLoadingText'),`正在加载模型 ${++completed}/${total}`);
    }));await Promise.all(tasks);modelReady=true;Motion.show($('modelLoading'),false,{duration:400});updateForces();
    const resize=()=>{const w=view.clientWidth,h=view.clientHeight;if(w<1||h<1)return;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();};new ResizeObserver(resize).observe(view);resize();
    $('resetView').onclick=resetView;$('showAxes').onchange=()=>axes.forEach(axis=>{axis.visible=true;axis.material.transparent=true;});controls.addEventListener('start',()=>{cameraReset=null;});
    let previousRender=performance.now();
    const animate=()=>{
      requestAnimationFrame(animate);
      if($('workspace').hidden||document.hidden)return;
      const now=performance.now(),dt=Math.min(.1,Math.max(0,(now-previousRender)/1000));previousRender=now;
      if(forceFresh){const positions=poseTimeline.at(now);if(positions)setPose(positions);}
      if(cameraReset){const t=Math.min(1,(performance.now()-cameraReset.time)/550),ease=1-(1-t)**4;camera.position.copy(cameraReset.position).lerp(new THREE.Vector3(.82,-.98,.67),ease);controls.target.copy(cameraReset.target).lerp(new THREE.Vector3(0,0,.27),ease);if(t===1)cameraReset=null;}
      axes.forEach(axis=>{const target=$('showAxes').checked?1:0;if(axis.material.transparent)axis.material.opacity=Motion.reducedMotion()?target:THREE.MathUtils.lerp(axis.material.opacity,target,.18);axis.visible=axis.material.opacity>.01&&($('showAxes').checked||axis.material.transparent);});
      const blend=Motion.reducedMotion()?1:1-Math.exp(-dt/.065);
      forceMarkers.forEach(marker=>{const target=$('showForces').checked ? .85 : 0;marker.material.opacity=Motion.reducedMotion()?target:THREE.MathUtils.lerp(marker.material.opacity,target,.18);marker.visible=marker.material.opacity>.005;const size=THREE.MathUtils.lerp(marker.scale.x,marker.userData.selected?1.35:1,blend);marker.scale.setScalar(size);});
      modelMeshes.forEach(mesh=>{if(mesh.userData.targetColor){mesh.material.color.lerp(mesh.userData.targetColor,blend);mesh.material.emissive.lerp(mesh.userData.targetEmissive,blend);mesh.material.emissiveIntensity=THREE.MathUtils.lerp(mesh.material.emissiveIntensity,mesh.userData.targetIntensity,blend);}});
      controls.update();renderer.render(scene,camera);positionForceLabels();
    };animate();view.classList.add('model-ready');Motion.show($('forceLabels'),$('showForces').checked,{duration:380});Motion.show($('forceLines'),$('showForces').checked,{duration:380});
  }catch(e){text($('modelLoadingText'),'模型加载失败：'+e.message);console.error(e);}
}
function setPose(positions){
  if(!modelReady)return;
  let changed=false;
  for(const joint of modelJoints){
    const index=joint.type==='revolute'?Number(joint.name.replace('joint',''))-1:6,value=positions[index];
    if(!finite(value)||value===joint.lastValue)continue;
    joint.lastValue=value;
    if(joint.type==='revolute')joint.moving.quaternion.setFromAxisAngle(joint.axisVector,value*Math.PI/180);
    else if(joint.type==='prismatic')joint.moving.position.copy(joint.axisVector).multiplyScalar(THREE.MathUtils.clamp(value/270,0,1)*.05);
    else continue;
    changed=true;
  }
  if(changed)renderer.shadowMap.needsUpdate=true;
}
function highlightModel(){updateForces();}

const projectedPoint=new THREE.Vector3();
let labelLayout=null;
function positionForceLabels(){
  if(!modelReady||$('forceLabels').hidden)return;
  const width=$('viewport').clientWidth,height=$('viewport').clientHeight;
  const labelWidth=forceElements[0].label.offsetWidth,labelHeight=forceElements[0].label.offsetHeight;
  const key=`${width}:${height}:${labelWidth}:${labelHeight}`;
  if(labelLayout?.key!==key){
    labelLayout={key,positions:labelColumns(width,height,labelWidth,labelHeight)};
    forceElements.forEach((item,i)=>{const {x,y}=labelLayout.positions[i];item.label.style.transform=`translate(${x}px,${y}px)`;});
  }
  forceAnchors.forEach((anchor,i)=>{
    projectedPoint.setFromMatrixPosition(anchor.matrixWorld).project(camera);
    const visible=Math.abs(projectedPoint.z)<=1&&Math.abs(projectedPoint.x)<=1&&Math.abs(projectedPoint.y)<=1;
    const pointX=(projectedPoint.x+1)*width/2,pointY=(1-projectedPoint.y)*height/2;
    const {x,y,left}=labelLayout.positions[i],fromX=left?x+labelWidth:x,fromY=y+labelHeight/2;
    const item=forceElements[i],path=`M ${fromX} ${fromY} L ${left?fromX+12:fromX-12} ${fromY} L ${pointX.toFixed(1)} ${pointY.toFixed(1)}`;
    if(item.path!==path){item.path=path;item.line.setAttribute('d',path);}
    if(item.visible!==visible){item.visible=visible;item.line.style.opacity=visible?'.3':'0';}
  });
}

async function init(){
  buildTables();$('start').onclick=startSession;$('stop').onclick=stopSession;$('save').onclick=saveSettings;$('defaults').onclick=restoreDampingDefaults;$('refreshLog').onclick=loadLog;
  $('dismissNotice').onclick=()=>Motion.show($('notice'),false,{collapse:true});
  document.querySelectorAll('[data-view]').forEach(button=>button.onclick=()=>navigate(button.dataset.view));
  document.querySelector('.brand').onclick=event=>{event.preventDefault();navigate('workspace');};
  $('heatScale').onchange=()=>{text($('scaleMax'),$('heatScale').value+' Nm');updateForces();};
  $('showForces').onchange=()=>{Motion.show($('forceLabels'),$('showForces').checked);Motion.show($('forceLines'),$('showForces').checked);};
  initModel();
  try{boot=await api('/api/bootstrap');token=boot.token;settings=boot.settings;if(settings.format!=='stararm-rs-unloaded-damping-v1')throw new Error('当前服务的配置格式不匹配，请检查服务地址');text($('version'),'v'+boot.version+' · 8767');buildParams();setButtons();poll();}
  catch(error){networkFailed=true;setButtons();notice('网页初始化失败：'+error.message,'error','network');}
}
setInterval(()=>{if(forceFresh&&performance.now()>freshDeadline){document.body.classList.add('stale');text($('freshness'),'已过期');text($('connection'),'等待新鲜设备数据');$('led').className='led orange';renderTelemetry(latest,false);}},100);
setInterval(()=>{if(activeView==='logs')loadLog();},1000);
window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
init();
