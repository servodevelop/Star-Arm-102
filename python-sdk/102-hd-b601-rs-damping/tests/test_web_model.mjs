import assert from 'node:assert/strict';
import {readFile,access} from 'node:fs/promises';
import vm from 'node:vm';

const base=new URL('../stararm_rs_damping/web/',import.meta.url);
const presentation=await readFile(new URL('presentation.js',base),'utf8');
const {PoseTimeline,labelColumns}=await import('data:text/javascript;base64,'+Buffer.from(presentation).toString('base64'));
const joints=angle=>Array.from({length:7},()=>({motor_pos_deg:angle}));
const timeline=new PoseTimeline();
assert.equal(timeline.at(1000),null);
assert.equal(timeline.push(joints(0),10,'run1',1000),true);
assert.deepEqual(timeline.at(1000),Array(7).fill(0));
assert.equal(timeline.push(joints(30),10.1,'run1',1100),true);
const middle=timeline.at(1200);for(const angle of middle)assert.ok(Math.abs(angle-12)<1e-7,'display pose must interpolate instead of snapping to every CAN frame');
assert.deepEqual(timeline.at(1400),Array(7).fill(30),'display pose must never extrapolate past a measured pose');
assert.equal(timeline.push(joints(90),10.1,'run1',1500),false,'repeated polls of one frame must not extend the display timeline');
assert.equal(timeline.push(joints(40),11.1,'run1',1600),true);assert.equal(timeline.samples.length,1,'long gaps must reset interpolation');
assert.equal(timeline.push(joints(50),11.2,'run2',1700),true);assert.equal(timeline.samples.length,1,'new sessions must not interpolate across runs');
for(const [width,height] of [[900,600],[500,450],[340,390]]){
  const labels=labelColumns(width,height,84,45);
  assert.equal(labels.length,7);
  assert.deepEqual(labels,labelColumns(width,height,84,45),'label hit targets must remain fixed while only robot geometry moves');
  for(const label of labels){assert.ok(label.x>=0&&label.x+84<=width);assert.ok(label.y>=0&&label.y+45<=height);}
}

const source=await readFile(new URL('app.js',base),'utf8');
const setPose=source.match(/^function setPose\(positions\)\{[\s\S]*?^\}/m)?.[0];assert.ok(setPose);
const rotations=[],translations=[];
const moving=index=>({quaternion:{setFromAxisAngle(axis,angle){rotations.push({index,axis,angle});}},position:{copy(axis){this.axis=axis;return this;},multiplyScalar(value){translations.push({index,value,axis:this.axis});return this;}}});
const modelJoints=Array.from({length:6},(_,i)=>({type:'revolute',name:`joint${i+1}`,axisVector:`axis${i}`,lastValue:null,moving:moving(i)}));
modelJoints.push({type:'prismatic',name:'gripper_joint1',axisVector:'left',lastValue:null,moving:moving(6)},{type:'prismatic',name:'gripper_joint2',axisVector:'right',lastValue:null,moving:moving(7)});
const renderer={shadowMap:{needsUpdate:false}};
const context=vm.createContext({modelReady:true,modelJoints,renderer,finite:Number.isFinite,THREE:{MathUtils:{clamp:(value,lo,hi)=>Math.max(lo,Math.min(hi,value))}}});
vm.runInContext(setPose,context);vm.runInContext('setPose([10,20,30,40,50,60,270])',context);
assert.equal(rotations.length,6);rotations.forEach((rotation,i)=>assert.ok(Math.abs(rotation.angle-(i+1)*10*Math.PI/180)<1e-10));
assert.deepEqual(translations.map(value=>value.value),[.05,.05]);assert.equal(renderer.shadowMap.needsUpdate,true);
vm.runInContext('setPose([10,20,30,40,50,60,270])',context);assert.equal(rotations.length,6,'duplicate poses must not rewrite model transforms');
vm.runInContext('setPose([NaN,20,30,40,50,60,270])',context);assert.equal(rotations.length,6,'missing joint positions must retain the last valid transform');

const model=JSON.parse(await readFile(new URL('model/robot.json',base),'utf8'));
assert.equal(model.joints.filter(joint=>joint.type==='revolute').length,6);
assert.equal(model.joints.filter(joint=>joint.type==='prismatic').length,2);
await Promise.all(model.links.flatMap(link=>link.visuals.map(visual=>access(new URL(visual.mesh,base)))));
for(const asset of ['vendor/three.module.js','vendor/OrbitControls.js','vendor/STLLoader.js','brand/fashionstar.png'])await access(new URL(asset,base));
console.log('RS model UI: actual interpolation, no extrapolation, duplicate/session/gap handling, fixed label targets, seven-axis transforms and all local mesh assets passed offline.');
