// Display-only interpolation; never extrapolate a motor position.
export class PoseTimeline {
  constructor(delay = .16) { this.delay=delay;this.clear(); }
  clear() { this.samples=[];this.source=null;this.arrived=0;this.playhead=null; }
  push(joints,time,source,arrived) {
    if(!Number.isFinite(time)||!Number.isFinite(arrived))return false;
    let last=this.samples.at(-1);
    if(source!==this.source||(last&&(time<last.time||time-last.time>.8))){this.clear();last=null;}
    if(last&&time===last.time)return false;
    this.source=source;this.arrived=arrived;
    const positions=Array.from({length:7},(_,i)=>Number.isFinite(joints[i]?.motor_pos_deg)?joints[i].motor_pos_deg:last?.positions[i]??null);
    this.samples.push({time,positions});
    if(this.samples.length>32)this.samples.shift();
    return true;
  }
  at(now) {
    const last=this.samples.at(-1);if(!last)return null;
    const target=last.time+Math.max(0,now-this.arrived)/1000-this.delay;
    this.playhead=Math.min(last.time,Math.max(this.playhead??-Infinity,target));
    const next=this.samples.findIndex(sample=>sample.time>=this.playhead);
    if(next<=0)return this.samples[0].positions;
    const a=this.samples[next-1],b=this.samples[next];
    const fraction=(this.playhead-a.time)/(b.time-a.time);
    return a.positions.map((value,i)=>value===null?b.positions[i]:b.positions[i]===null?value:value+(b.positions[i]-value)*fraction);
  }
}

// Fixed joint order keeps moving geometry from moving a hovered hit target.
export function labelColumns(width,height,labelWidth,labelHeight) {
  const positions=[];
  for(const indices of [[0,1,2],[3,4,5,6]]){
    const left=indices[0]===0,minY=Math.min(64,Math.max(8,height-labelHeight-12));
    const maxY=Math.max(minY,height-34-labelHeight);
    const gap=Math.min(labelHeight+9,(maxY-minY)/(indices.length-1));
    const start=minY+(maxY-minY-gap*(indices.length-1))/2;
    indices.forEach((index,row)=>{positions[index]={x:left?14:width-labelWidth-14,y:start+row*gap,left};});
  }
  return positions;
}
