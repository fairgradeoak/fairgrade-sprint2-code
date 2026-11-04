// Synthetic wall-clock buffer soak. Does NOT exercise a real webcam or human model accuracy.
import { chromium } from 'playwright';
import { createDemoServer } from '../server/server.mjs';
import { mkdir, mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const minutes = Number(process.env.SOAK_MINUTES || 20);
if (!Number.isFinite(minutes) || minutes < 1) throw Error('Invalid duration');
const dir = await mkdtemp(join(tmpdir(),'fairgrade-soak-'));
const {server}=await createDemoServer({dataDir:dir});await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({args:['--no-sandbox']});
try {
 const page=await browser.newPage(); await page.goto(`http://127.0.0.1:${server.address().port}`);
 const result=await page.evaluate(async minutes=>{
  const {EvidenceRecorder}=await import('/core/recorder.mjs');
  const canvas=document.createElement('canvas');canvas.width=640;canvas.height=480;
  const ctx=canvas.getContext('2d');const errors=[];const recorder=new EvidenceRecorder(canvas,()=>{},e=>errors.push(e.message));
  recorder.start(); const samples=[];const start=performance.now();
  while(performance.now()-start<minutes*60000){
    ctx.fillStyle='#173b31';ctx.fillRect(0,0,640,480);ctx.fillStyle='white';ctx.fillText(String(performance.now()),10,30);
    await new Promise(r=>setTimeout(r,1000));
    samples.push({elapsedMs:performance.now()-start,frames:recorder.buffer.frames.length,bufferBytes:recorder.buffer.bytes,heapBytes:performance.memory?.usedJSHeapSize??null});
  }
  recorder.stop();return {kind:'synthetic-wall-clock-buffer-soak',elapsedMs:performance.now()-start,samples,errors,cleared:recorder.buffer.bytes===0,limitations:['No webcam, detector inference, participants or AWS','Heap measure is browser-specific; bounded buffers are not proof of absence of all leaks']};
 }, minutes);
 if(result.errors.length||!result.cleared||result.samples.some(s=>s.bufferBytes>48*1048576||s.frames>180))throw Error('Soak bounds failed');
 await mkdir('evidence/phase2',{recursive:true});await writeFile('evidence/phase2/soak-report.json',JSON.stringify(result,null,2)); console.log(JSON.stringify({passed:true,elapsedMs:result.elapsedMs,samples:result.samples.length}));
} finally {await browser.close();await new Promise(r=>server.close(r));await rm(dir,{recursive:true,force:true});}
