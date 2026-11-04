import {chromium} from 'playwright';import {mkdir,mkdtemp,readFile,writeFile,rm} from 'node:fs/promises';import{tmpdir}from'node:os';import{join,resolve,extname}from'node:path';import{createDemoServer}from'../server/server.mjs';
const dir=await mkdtemp(join(tmpdir(),'fairgrade-models-'));const{server}=await createDemoServer({dataDir:dir});await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({args:['--no-sandbox','--enable-unsafe-swiftshader']});
try{const context=await browser.newContext(),page=await context.newPage();
 const prefix='/exam/assets/proctor/';const assetRequests=[];
 await context.route('**/exam/assets/proctor/**',async route=>{
  const path=new URL(route.request().url()).pathname;assetRequests.push(path);
  const file=resolve('public',path.slice(prefix.length));if(!file.startsWith(resolve('public')+'/'))return route.abort();
  return route.fulfill({body:await readFile(file),contentType:({'.mjs':'text/javascript','.js':'text/javascript','.wasm':'application/wasm','.json':'application/json','.css':'text/css'})[extname(file)]||'application/octet-stream'});
 });page.setDefaultTimeout(180000);const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(`http://127.0.0.1:${server.address().port}`);
 const result=await page.evaluate(async()=>{
  const {Detectors}=await import('/exam/assets/proctor/core/detectors.mjs');const config=await(await fetch('/config.json')).json();
  const canvas=document.createElement('canvas');canvas.width=640;canvas.height=480;canvas.getContext('2d').fillRect(0,0,640,480);
  const results={},errors=[];const detector=new Detectors(canvas,config,{face:d=>results.face=d,object:d=>results.object=d,identity:d=>results.identity=d,error:e=>errors.push(e.message)});
  const start=performance.now();try{await detector.load();const loadMs=performance.now()-start;
   const identityStart=performance.now();const faces=await detector.descriptors();results.identity={faceCount:faces.length,latencyMs:performance.now()-identityStart};
   await detector.tick(performance.now());const deadline=performance.now()+90000;
   while((!results.face||!results.object)&&!errors.length&&performance.now()<deadline)await new Promise(r=>setTimeout(r,100));
   if(errors.length||!results.face||!results.object)throw Error(errors.join(';')||'Inference timeout');return{loadMs,results,crossOriginIsolated:globalThis.crossOriginIsolated,sharedArrayBufferAvailable:typeof SharedArrayBuffer!=='undefined'};
  }finally{detector.stop();}
 });if(errors.length)throw Error(errors.join(';'));
 await mkdir('evidence/phase3',{recursive:true});await writeFile('evidence/phase3/model-smoke.json',JSON.stringify({at:new Date().toISOString(),browser:browser.version(),assetRequests,...result,limitations:['Real model loading and inference on a blank canvas only','Not webcam testing or evidence of detection accuracy','Headless cloud machine, not target laptop']},null,2));console.log(JSON.stringify(result));
}finally{await browser.close();await new Promise(r=>server.close(r));await rm(dir,{recursive:true,force:true});}
