// Loopback-only synthetic demo. This is NOT Omar's deployed backend.
import http from 'node:http';import{readFile,writeFile,mkdir,rename,unlink,readdir,stat}from'node:fs/promises';
import{resolve,dirname,extname,sep}from'node:path';import{fileURLToPath}from'node:url';import{randomUUID}from'node:crypto';
import{REASONS}from'../public/core/triggers.mjs';import{isUuid}from'../public/core/ids.mjs';
const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const MIME={'.html':'text/html','.mjs':'text/javascript','.js':'text/javascript','.json':'application/json','.css':'text/css','.wasm':'application/wasm','.task':'application/octet-stream','.tflite':'application/octet-stream','.bin':'application/octet-stream'};
const problem=(code,message)=>Object.assign(Error(message),{code});
async function body(req,limit=65536){const parts=[];let size=0;for await(const p of req){size+=p.length;if(size>limit)throw problem(413,'Body too large');parts.push(p);}return Buffer.concat(parts);}
async function json(req){try{return JSON.parse((await body(req)).toString());}catch(e){if(e.code)throw e;throw problem(400,'Invalid JSON');}}
export async function createDemoServer({dataDir=resolve(ROOT,'data'),retentionDays=7,now=()=>Date.now()}={}){
 if(!Number.isInteger(retentionDays)||retentionDays<1)throw Error('Invalid retention');await mkdir(resolve(dataDir,'clips'),{recursive:true});
 const db=resolve(dataDir,'events.json');let events;try{events=JSON.parse(await readFile(db,'utf8'));}catch(e){if(e.code!=='ENOENT')throw e;events=[];}
 const tickets=new Map(),playbacks=new Map();let mutations=Promise.resolve();const serialize=fn=>{const p=mutations.then(fn);mutations=p.catch(()=>{});return p;};
 const save=async()=>{await writeFile(db+'.tmp',JSON.stringify(events,null,2));await rename(db+'.tmp',db);};
 const cleanup=async()=>{
  for(const event of events)if(!event.clipExpired&&Date.parse(event.expiresAt)<=now()){await unlink(resolve(dataDir,'clips',event.objectKey)).catch(e=>{if(e.code!=='ENOENT')throw e;});event.clipExpired=true;}
  for(const [token,t]of tickets)if(t.expires<now())tickets.delete(token);
  for(const [token,t]of playbacks)if(t.expires<now())playbacks.delete(token);
  for(const file of await readdir(resolve(dataDir,'clips'))){if(events.some(e=>e.objectKey===file)||[...tickets.values()].some(t=>t.objectKey===file))continue;const path=resolve(dataDir,'clips',file);if((await stat(path)).mtimeMs<now()-300000)await unlink(path);}
  await save();
 };
 await cleanup();const timer=setInterval(()=>serialize(cleanup).catch(()=>{}),60000);timer.unref();
 const publicEvent=e=>{const{objectKey,requestPayload,...rest}=e;return rest;};
 const server=http.createServer(async(req,res)=>{
  res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','no-referrer');res.setHeader('Permissions-Policy','camera=(self), microphone=()');
  const send=(status,value)=>{res.writeHead(status,{'Content-Type':'application/json'});res.end(status===204?undefined:JSON.stringify(value));};
  try{
   const port=server.address().port,host=req.headers.host;if(![`localhost:${port}`,`127.0.0.1:${port}`].includes(host))throw problem(403,'Unrecognized host');const origin=`http://${host}`;
   if(req.headers.origin&&req.headers.origin!==origin)throw problem(403,'Cross-origin denied');const url=new URL(req.url,origin);
   if(['/api/','/demo-upload','/demo-playback/'].some(p=>url.pathname.startsWith(p)))return await serialize(async()=>{
    const role=req.headers['x-demo-role'];const requireRole=r=>{if(role!==r)throw problem(403,'Wrong demo role');};
    if(req.method==='GET'&&url.pathname==='/api/policy'){if(!['student','instructor'].includes(role))throw problem(403,'Demo role required');return send(200,{approved:true,policyVersion:'fairgrade-2026-10',retentionDays,metadataNotice:'Event details (time, reasons, review decision) are kept with the exam record after the clip is deleted.'});}
    if(req.method==='POST'&&url.pathname==='/api/clips/presign'){
     requireRole('student');const p=await json(req);if(!isUuid(p.eventId)||!isUuid(p.examId)||!/^video\/webm(;codecs=vp[89])?$/.test(p.contentType))throw problem(400,'Invalid reservation');
     const token=randomUUID(),objectKey=p.eventId+'.webm';tickets.set(token,{...p,objectKey,expires:now()+300000});
     return send(200,{uploadUrl:origin+'/demo-upload',fields:{'Content-Type':p.contentType,key:objectKey,demoToken:token},objectKey,maxBytes:20971520,expiresAt:new Date(now()+300000).toISOString()});
    }
    if(req.method==='POST'&&url.pathname==='/demo-upload'){
     const bytes=await body(req,20971520+65536);let form;try{form=await new Request(origin,{method:'POST',headers:{'Content-Type':req.headers['content-type']},body:bytes}).formData();}catch{throw problem(400,'Invalid multipart form');}
     const t=tickets.get(form.get('demoToken'));if(!t||t.expires<now())throw problem(403,'Policy expired');
     if(form.get('key')!==t.objectKey||form.get('Content-Type')!==t.contentType)throw problem(400,'Form mismatch');const file=form.get('file');
     if(!file||typeof file.arrayBuffer!=='function'||file.size<1||file.size>20971520||file.type!==t.contentType)throw problem(400,'Invalid file');
     t.sizeBytes=file.size;t.uploaded=true;const path=resolve(dataDir,'clips',t.objectKey);await writeFile(path+'.tmp',Buffer.from(await file.arrayBuffer()));await rename(path+'.tmp',path);return send(204);
    }
    if(req.method==='POST'&&url.pathname==='/api/events'){
     requireRole('student');const p=await json(req);if(!isUuid(p.eventId)||!isUuid(p.examId)||!Array.isArray(p.reasons)||!p.reasons.length||p.reasons.some(r=>!REASONS.includes(r))||new Set(p.reasons).size!==p.reasons.length||!Number.isFinite(Date.parse(p.triggeredAt)))throw problem(400,'Invalid event');
     const existing=events.find(e=>e.eventId===p.eventId);if(existing){if(JSON.stringify(p)!==JSON.stringify(existing.requestPayload))throw problem(409,'Event conflicts');return send(200,{event:publicEvent(existing)});}
     const t=[...tickets.values()].find(t=>t.eventId===p.eventId&&t.examId===p.examId&&t.objectKey===p.objectKey&&t.uploaded&&t.contentType===p.contentType&&t.sizeBytes===p.sizeBytes);if(!t)throw problem(400,'Verified upload required');
     const e={...p,studentEmail:'demo-student@example.test',createdAt:new Date(now()).toISOString(),expiresAt:new Date(now()+retentionDays*86400000).toISOString(),detection:{thresholds:p.thresholds,triggerMonotonicMs:p.triggerMonotonicMs,sustainedMs:p.sustainedMs},reviewed:false,instructorDecision:null,reviewedAt:null,version:0,clipExpired:false,requestPayload:p};events.push(e);await save();return send(201,{event:publicEvent(e)});
    }
    if(req.method==='GET'&&url.pathname==='/api/events'){requireRole('instructor');const exam=url.searchParams.get('examId');if(!isUuid(exam))throw problem(400,'Invalid exam');return send(200,{events:events.filter(e=>e.examId===exam).sort((a,b)=>b.createdAt.localeCompare(a.createdAt)).slice(0,200).map(publicEvent)});}
    const match=url.pathname.match(/^\/api\/events\/([^/]+)\/(review|playback)$/);
    if(match){requireRole('instructor');const e=events.find(e=>e.eventId===match[1]);if(!e)throw problem(404,'Not found');
     if(req.method==='PATCH'&&match[2]==='review'){const p=await json(req);if(!['confirmed','dismissed'].includes(p.decision)||!Number.isInteger(p.version))throw problem(400,'Invalid review');if(p.version!==e.version)throw problem(409,'Review changed');e.version++;e.reviewed=true;e.instructorDecision=p.decision;e.reviewedAt=new Date(now()).toISOString();await save();return send(200,publicEvent(e));}
     if(req.method==='GET'&&match[2]==='playback'){if(e.clipExpired||Date.parse(e.expiresAt)<=now())throw problem(410,'Clip retention ended');const token=randomUUID();playbacks.set(token,{event:e,expires:now()+300000});return send(200,{url:origin+'/demo-playback/'+token,expiresAt:new Date(now()+300000).toISOString()});}
    }
    if(req.method==='GET'&&url.pathname.startsWith('/demo-playback/')){const t=playbacks.get(url.pathname.split('/').at(-1));if(!t||t.expires<now())throw problem(403,'Playback expired');if(t.event.clipExpired||Date.parse(t.event.expiresAt)<=now())throw problem(410,'Clip retention ended');const bytes=await readFile(resolve(dataDir,'clips',t.event.objectKey));res.writeHead(200,{'Content-Type':t.event.contentType,'Content-Length':bytes.length});return res.end(bytes);}
    throw problem(404,'Route not found');
   });
   if(!['GET','HEAD'].includes(req.method))throw problem(405,'Method not allowed');
   const publicRoot=resolve(ROOT,'public');const path=resolve(publicRoot,'.'+decodeURIComponent(url.pathname==='/'?'/index.html':url.pathname));if(!path.startsWith(publicRoot+sep))throw problem(403,'Forbidden path');
   const bytes=await readFile(path);res.writeHead(200,{'Content-Type':MIME[extname(path)]||'application/octet-stream'});res.end(req.method==='HEAD'?undefined:bytes);
  }catch(e){if(!res.headersSent)send(e.code==='ENOENT'?404:Number.isInteger(e.code)?e.code:500,{error:Number.isInteger(e.code)?e.message:'Request failed'});else res.end();}
 });server.on('close',()=>clearInterval(timer));return{server,cleanup:()=>serialize(cleanup)};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){const{server}=await createDemoServer();server.listen(Number(process.env.PORT||3000),'127.0.0.1',()=>console.log(`FairGrade local demo: http://localhost:${server.address().port}`));}
