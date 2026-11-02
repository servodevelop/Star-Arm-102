import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('../stararm_rs_feedback/web/presentation.js',import.meta.url),'utf8');
const {PoseTimeline,labelColumns}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const pose=value=>Array.from({length:7},()=>({motor_pos_deg:value}));
const track=new PoseTimeline(.16);
assert.equal(track.at(0),null);
track.push(pose(0),10,'live:one',0);
assert.equal(track.at(0)[0],0);
track.push(pose(10),10.1,'live:one',100);
track.push(pose(20),10.2,'live:one',200);
assert.ok(Math.abs(track.at(200)[0]-4)<1e-9);
let previous=4;
for(let t=216;t<=344;t+=16){
  const value=track.at(t)[0];assert.ok(value>previous&&value<20);previous=value;
}
assert.equal(track.at(1000)[0],20,'a missing packet must never extrapolate movement');
assert.equal(track.push(pose(999),10.2,'live:one',1200),false,'polling duplicates must not restart the display clock');
assert.equal(track.at(1400)[0],20);
track.push(pose(30),10.3,'live:one',1500);
assert.ok(track.at(1500)[0]>=20,'late delivery must not rewind the displayed pose');
track.push([{motor_pos_deg:40},{motor_pos_deg:NaN}],10.4,'live:one',1600);
assert.equal(track.at(2000)[1],30,'invalid axes keep the last measured position');
track.push(pose(90),20,'live:one',2100);
assert.equal(track.at(2100)[0],90,'a long gap starts a new segment');
track.push(pose(-30),1,'replay',2200);
assert.equal(track.at(2200)[0],-30,'changing source must not blend unrelated runs');
track.push(pose(7),.5,'replay',2300);
assert.equal(track.at(2300)[0],7,'looped replay starts a fresh segment');
track.clear();assert.equal(track.at(2400),null);

const moving=new PoseTimeline(.16);let last=-Infinity,maxStep=0;
for(let tick=0;tick<180;tick++){
  const ms=tick*1000/60;
  if(tick%6===0)moving.push(pose(ms*.05),100+ms/1000,'live',ms);
  const value=moving.at(ms)[0];assert.ok(value>=last);
  if(Number.isFinite(last))maxStep=Math.max(maxStep,value-last);
  last=value;
}
assert.ok(maxStep<1,'10 Hz samples should become small continuous display steps');
for(const [width,height,labelWidth,labelHeight] of [[650,360,105,43],[364,365,85,40],[700,650,112,46]]){
  const positions=labelColumns(width,height,labelWidth,labelHeight);
  assert.equal(positions.length,7);
  for(const indices of [[0,1,2],[3,4,5,6]]){
    for(const [row,index] of indices.entries()){
      const p=positions[index];assert.ok(p.x>=0&&p.x+labelWidth<=width);
      assert.ok(p.y>=0&&p.y+labelHeight<=height);
      if(row)assert.ok(p.y-positions[indices[row-1]].y>=labelHeight,'fixed labels must not overlap');
    }
  }
  assert.deepEqual(labelColumns(width,height,labelWidth,labelHeight),positions,'joint motion cannot reorder hit targets');
}
console.log('Presentation: interpolation, jitter, duplicate samples, gaps, replay, invalid axes, no extrapolation and stable label columns passed.');
