import test from 'node:test';
import assert from 'node:assert/strict';
import { TriggerEngine, identityMismatch } from '../public/core/triggers.mjs';
import { FrameBuffer, selectWindow } from '../public/core/window.mjs';
import { decodeYolo } from '../public/core/yolo.mjs';
import { ApiClient } from '../public/core/api.mjs';

test('phone trigger requires sustained observations, resets on flicker, and latches', () => {
  const engine = new TriggerEngine();
  assert.equal(engine.observe('phone', true, 0), null);
  assert.equal(engine.observe('phone', false, 1000), null);
  assert.equal(engine.observe('phone', true, 1500), null);
  assert.equal(engine.observe('phone', true, 2500), null);
  assert.equal(engine.observe('phone', true, 3500).reason, 'phone');
  assert.equal(engine.observe('phone', true, 4500), null);
});
test('no-face requires three seconds and unknown inference resets its timer', () => {
  const engine = new TriggerEngine();
  for (let t = 0; t <= 2000; t += 1000) assert.equal(engine.observe('no_face', true, t), null);
  engine.observe('no_face', null, 2500);
  for (let t = 3000; t < 6000; t += 1000) assert.equal(engine.observe('no_face', true, t), null);
  assert.equal(engine.observe('no_face', true, 6000).reason, 'no_face');
});
test('stale or duplicate samples cannot manufacture sustained detection', () => {
  const engine = new TriggerEngine();
  engine.observe('phone', true, 0);
  assert.equal(engine.observe('phone', true, 5000), null);
  assert.equal(engine.observe('phone', true, 5000), null);
  assert.equal(engine.observe('phone', true, 4000), null);
  assert.equal(engine.observe('phone', true, 6000), null);
  assert.ok(engine.observe('phone', true, 7000));
});
test('independent reasons and per-reason cooldown', () => {
  const engine = new TriggerEngine({ phoneMs: 100, secondFaceMs: 100, cooldownMs: 1000 });
  engine.observe('phone', true, 0); engine.observe('second_face', true, 0);
  assert.ok(engine.observe('phone', true, 100)); assert.ok(engine.observe('second_face', true, 100));
  engine.observe('phone', false, 200); engine.observe('phone', true, 300);
  assert.equal(engine.observe('phone', true, 500), null);
  assert.ok(engine.observe('phone', true, 1100));
});
test('identity unknown is not a mismatch, and equality is a match', () => {
  assert.equal(identityMismatch(null, 1), null); assert.equal(identityMismatch(0.9, 2), null);
  assert.equal(identityMismatch(0.55, 1), false); assert.equal(identityMismatch(0.8, 1), true);
});
test('invalid trigger configuration and reasons are rejected', () => {
  assert.throws(() => new TriggerEngine({ noFaceMs: -1 }));
  assert.throws(() => new TriggerEngine().observe('bad', true, 0));
});
const frames = (start, end, step = 100) => Array.from({ length: Math.floor((end - start) / step) + 1 }, (_, i) => ({ time: start + i * step, blob: new Blob(['frame']) }));
test('rolling selection covers exactly requested pre/post timestamps with explicit tolerance', () => {
  const { metadata } = selectWindow(frames(0, 20000), 10000);
  assert.equal(metadata.requestedStartMs, 2500); assert.equal(metadata.requestedEndMs, 17500);
  assert.equal(metadata.preMs, 7500); assert.equal(metadata.postMs, 7500); assert.equal(metadata.complete, true);
});
test('short pre-roll, missing post-roll and internal gaps are marked partial', () => {
  assert.equal(selectWindow(frames(5000, 18000), 10000).metadata.complete, false);
  assert.equal(selectWindow(frames(0, 14000), 10000).metadata.complete, false);
  assert.equal(selectWindow(frames(0, 20000).filter(f => f.time < 9000 || f.time > 10000), 10000).metadata.complete, false);
  assert.throws(() => selectWindow([], 100));
});
test('rolling buffer enforces memory and time limits and clears', () => {
  const buffer = new FrameBuffer({ maxBytes: 12, keepMs: 200 });
  frames(0, 1000).forEach(f => buffer.push(f));
  assert.ok(buffer.bytes <= 12); assert.ok(buffer.frames.at(-1).time - buffer.frames[0].time <= 200);
  buffer.clear(); assert.equal(buffer.bytes, 0); assert.equal(buffer.frames.length, 0);
});
function output(rows, channelsFirst = true) {
  const data = new Float32Array(rows.length * 84);
  rows.forEach((r, i) => r.forEach((x, j) => { data[channelsFirst ? j * rows.length + i : i * 84 + j] = x; }));
  return { data, shape: channelsFirst ? [1, 84, rows.length] : [1, rows.length, 84] };
}
function row(cls, score, center = [320, 320, 100, 100]) { const r = Array(84).fill(0); r.splice(0, 4, ...center); r[cls + 4] = score; return r; }
test('YOLO decodes both layouts, undoes letterboxing, and keeps COCO phone/person', () => {
  for (const layout of [true, false]) {
    const { data, shape } = output([row(67, 0.9), row(0, 0.8), row(2, 0.99)], layout);
    const boxes = decodeYolo(data, shape, { width: 640, height: 480 });
    assert.equal(boxes.length, 2); assert.equal(boxes[0].label, 'cell phone'); assert.equal(boxes[0].y, 190);
  }
});
test('YOLO NMS is class-aware and unsupported schemas fail clearly', () => {
  const { data, shape } = output([row(0, 0.9), row(0, 0.8), row(67, 0.85)]);
  assert.equal(decodeYolo(data, shape, { width: 640, height: 640 }).length, 2);
  assert.throws(() => decodeYolo(data, [1, 85, 3], { width: 640, height: 640 }));
});
const E='44444444-4444-4444-8444-444444444444', X='11111111-1111-4111-8111-111111111111';
const cfg={mode:'live',apiBase:'https://gnlnv6dd5j.execute-api.eu-north-1.amazonaws.com',uploadOrigins:['https://s3.eu-north-1.amazonaws.com']};
const opts={getAccessToken:async()=> 'access-token',sleep:async()=>{}};
const ticket={uploadUrl:'https://s3.eu-north-1.amazonaws.com/fairgrade-proctoring-clips-oak',objectKey:'proctoring/clip.webm',maxBytes:20971520,expiresAt:new Date(Date.now()+300000).toISOString(),fields:{'Content-Type':'video/webm',key:'proctoring/clip.webm',policy:'signed-policy','x-amz-signature':'signature'}};
const event={eventId:E,examId:X,synthetic:false};
test('POST upload: every signed field preserved, file last, bearer only on API; event wrapper unwrapped',async()=>{
 const calls=[];const api=new ApiClient(cfg,'student',async(url,options)=>{calls.push({url,options});if(url.endsWith('presign'))return Response.json(ticket);if(url.endsWith('/events'))return Response.json({event:{...event,version:0}},{status:201});return new Response(null,{status:204});},opts);
 const result=await api.submit(event,new Blob(['video'],{type:'video/webm'}));
 assert.deepEqual(calls.map(c=>c.options.method),['POST','POST','POST']);assert.equal(calls[0].url,cfg.apiBase+'/clips/presign');
 assert.equal(calls[0].options.headers.Authorization,'Bearer access-token');assert.equal(calls[1].options.headers,undefined);
 assert.ok(calls.every(c=>c.options.credentials==='omit'));assert.deepEqual(JSON.parse(calls[0].options.body),{eventId:E,examId:X,contentType:'video/webm'});
 assert.deepEqual([...calls[1].options.body.keys()],[...Object.keys(ticket.fields),'file']);for(const[k,v]of Object.entries(ticket.fields))assert.equal(calls[1].options.body.get(k),v);
 const logged=JSON.parse(calls[2].options.body);assert.equal(logged.sizeBytes,5);assert.equal(logged.checksumSha256,undefined);assert.equal(result.version,0);
});
test('failed uploads never log events; three attempts get fresh tickets',async()=>{
 const calls=[];const api=new ApiClient(cfg,'student',async(url)=>{calls.push(url);return url.endsWith('presign')?Response.json(ticket):new Response('',{status:503});},opts);
 await assert.rejects(api.submit(event,new Blob(['v'],{type:'video/webm'})),/three attempts/);assert.equal(calls.length,6);assert.ok(!calls.some(x=>x.endsWith('/events')));
 api.config={...cfg,uploadOrigins:[]};calls.length=0;await assert.rejects(api.submit(event,new Blob(['v'],{type:'video/webm'})),/allowlisted/);assert.equal(calls.length,1);
});
test('expired POST policy renews; ordinary S3 403 stops',async()=>{
 let presigns=0,uploads=0;const api=new ApiClient(cfg,'student',async(url)=>{if(url.endsWith('presign')){presigns++;return Response.json(ticket);}if(url.endsWith('/events'))return Response.json({event});uploads++;return uploads===1?new Response('<Message>Policy expired</Message>',{status:403}):new Response(null,{status:204});},opts);
 await api.submit(event,new Blob(['v'],{type:'video/webm'}));assert.equal(presigns,2);
 const denied=new ApiClient(cfg,'student',async url=>url.endsWith('presign')?Response.json(ticket):new Response('Access denied',{status:403}),opts);await assert.rejects(denied.submit(event,new Blob(['v'],{type:'video/webm'})),e=>e.status===403);
});
test('client rejects synthetic live uploads, empty/oversize files and unsupported types',async()=>{
 let count=0;const api=new ApiClient(cfg,'student',async()=>{count++;},opts);
 for(const blob of[new Blob([],{type:'video/webm'}),new Blob(['x'],{type:'video/mp4'}),new Blob([new Uint8Array(20971521)],{type:'video/webm'})])await assert.rejects(api.submit(event,blob));
 await assert.rejects(api.submit({...event,synthetic:true},new Blob(['x'],{type:'video/webm'})));assert.equal(count,0);
});
test('status and error message preserved for 409/410; list has no cursor requirement',async()=>{
 const api=new ApiClient(cfg,'instructor',async()=>Response.json({error:'Changed by another reviewer'},{status:409}),opts);await assert.rejects(api.review(E,'confirmed',0),e=>e.status===409&&e.message==='Changed by another reviewer');
 const expired=new ApiClient(cfg,'instructor',async()=>Response.json({error:'Clip retention ended'},{status:410}),opts);await assert.rejects(expired.playback(E),e=>e.status===410);
 const list=new ApiClient(cfg,'instructor',async()=>Response.json({events:[]}),opts);assert.deepEqual(await list.list(X),{events:[]});
});
test('expired access token refreshes once; persistent unauthorized stops',async()=>{
 const refresh=[];let calls=0;const api=new ApiClient(cfg,'student',async()=>{calls++;return new Response('{}',{status:401});},{...opts,getAccessToken:async o=>{refresh.push(o.forceRefresh);return 'x';}});
 await assert.rejects(api.list(X));assert.equal(calls,2);assert.deepEqual(refresh,[false,true]);
});
test('no token and malformed UUID fail before network; fetch global receiver retained',async()=>{
 let calls=0;const api=new ApiClient(cfg,'student',async()=>{calls++;return Response.json({});});await assert.rejects(api.list(X),/Sign in/);assert.equal(calls,0);assert.throws(()=>api.list('exam'),/UUID/);
 const demo=new ApiClient({mode:'demo',apiBase:'/api'},'student',function(){assert.equal(this,globalThis);return Promise.resolve(Response.json({events:[]}));});await demo.list(X);
});
