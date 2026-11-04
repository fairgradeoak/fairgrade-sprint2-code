const percentile=(xs,p)=>xs.length?[...xs].sort((a,b)=>a-b)[Math.min(xs.length-1,Math.floor(xs.length*p))]:null;
export class Telemetry {
 constructor({synthetic,thresholds}){this.startedAt=new Date().toISOString();this.start=performance.now();this.synthetic=synthetic;this.thresholds=structuredClone(thresholds);this.samples=[];this.inference={face:[],object:[],identity:[]};this.flags=[];this.identityTrials=[];this.armedAt=null;this.lastSample=0;this.lastFrameTime=null;this.lastVideoFrames=null;this.truncated=false;}
 detection(kind,data){const xs=this.inference[kind];xs.push({time:data.time,latencyMs:data.latencyMs??null});if(xs.length>10000){xs.shift();this.truncated=true;}}
 sample(recorder,source){const now=performance.now();if(now-this.lastSample<2000)return null;
 const frames=recorder.buffer.frames;const videoFrames=source.getVideoPlaybackQuality?.().totalVideoFrames??null;
 const cameraFps=this.lastVideoFrames!==null&&videoFrames!==null?(videoFrames-this.lastVideoFrames)*1000/(now-this.lastSample):null;
 const sample={elapsedMs:now-this.start,bufferFrames:frames.length,bufferBytes:recorder.buffer.bytes,bufferSpanMs:frames.length?frames.at(-1).time-frames[0].time:0,
 captureFps:frames.length>1?(frames.length-1)*1000/(frames.at(-1).time-frames[0].time):0,cameraFps,
 heapBytes:performance.memory?.usedJSHeapSize??null,pending:recorder.pending.length,queued:recorder.queue.length,encoding:!!recorder.encoding};
 this.lastSample=now;this.lastVideoFrames=videoFrames;this.samples.push(sample);if(this.samples.length>1800){this.samples.shift();this.truncated=true;}return sample;}
 flag(event){this.flags.push({eventId:event.eventId,reason:event.reasons[0],triggeredAt:event.triggeredAt});}
 export(){const elapsedMs=performance.now()-this.start;return {schemaVersion:2,startedAt:this.startedAt,exportedAt:new Date().toISOString(),synthetic:this.synthetic,thresholds:this.thresholds,elapsedMs,armedMs:this.armedAt===null?0:(this.endedAt??performance.now())-this.armedAt,ended:!!this.endedAt,truncated:this.truncated,samples:this.samples,flags:this.flags,identityTrials:this.identityTrials,
 inference:Object.fromEntries(Object.entries(this.inference).map(([k,xs])=>[k,{samples:xs.length,medianLatencyMs:percentile(xs.map(x=>x.latencyMs).filter(Number.isFinite),.5),p95LatencyMs:percentile(xs.map(x=>x.latencyMs).filter(Number.isFinite),.95),inferencesPerSecond:xs.length>1?(xs.length-1)*1000/(xs.at(-1).time-xs[0].time):null}])),limitations:['Camera FPS and JS heap may be unavailable in this browser','JS heap excludes GPU/WASM and process memory; record OS memory separately','Synthetic data is not human evaluation']};}
}
