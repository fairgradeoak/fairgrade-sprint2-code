import {ApiClient,LIVE_API_BASE,STORAGE_ORIGIN} from './core/api.mjs';
import {requireUuid} from './core/ids.mjs';
import {TriggerEngine,identityMismatch,REASONS} from './core/triggers.mjs';
import {EvidenceRecorder} from './core/recorder.mjs';
import {Detectors} from './core/detectors.mjs';
import {Telemetry} from './core/telemetry.mjs';

export const DEFAULT_THRESHOLDS=Object.freeze({phoneMs:2000,secondFaceMs:1500,mismatchMs:3000,noFaceMs:3000,cooldownMs:30000,maxSampleGapMs:1500,identityDistance:0.55,objectConfidence:0.55});
const consents=new WeakMap();let active=null;
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text)n.textContent=text;if(cls)n.className=cls;return n;};
function options(input,role='student') {
 const {container,apiBase=LIVE_API_BASE,getAccessToken,mode='live'}=input;
 if(!(container instanceof HTMLElement))throw Error('container must be a DOM element');
 if(!['live','demo'].includes(mode))throw Error('Invalid mode');
 if(mode==='demo' && new URL(apiBase,location.href).origin!==location.origin)throw Error('Demo mode requires a same-origin demo server');
 const config={mode,apiBase,thresholds:{...DEFAULT_THRESHOLDS},uploadOrigins:[STORAGE_ORIGIN],playbackOrigins:[STORAGE_ORIGIN]};
 return{container,config,api:new ApiClient(config,role,fetch,{getAccessToken})};
}
function view(container,title) {
 const root=node('section',null,'fg-module');
 const style=node('link');style.rel='stylesheet';style.href=new URL('./module.css',import.meta.url).href;
 root.append(style,node('h2',title));container.replaceChildren(root);return root;
}
function notify(callback,value){try{callback?.(value);}catch{/* A host callback must not interrupt camera cleanup or uploads. */}}
function validPolicy(p){if(p?.approved!==true || p.retentionDays!==7 || typeof p.policyVersion!=='string' || !p.policyVersion || typeof p.metadataNotice!=='string')throw Error('Approved 7-day privacy policy unavailable');return p;}

/** Displays explicit consent. No camera access. Tokens are supplied by the host. */
export async function renderConsent(input) {
 const {container,config,api}=options(input);const policy=validPolicy(await api.policy());
 if(input.signal?.aborted)throw Error('Consent cancelled');
 const root=view(container,'Before monitoring begins');
 root.append(node('p',config.mode==='demo'?'LOCAL DEMONSTRATION - synthetic testing, no AWS storage.':'Webcam monitoring - observations are reviewed by an instructor.'));
 root.append(node('p','Your webcam is processed on this device. Face references and a rolling buffer stay in memory. Sustained phone, second-face, face-absence or identity-change signals can save up to 7.5 seconds before and after a flag. No microphone is used.'));
 root.append(node('p',`Flagged clips are kept for 7 days. ${policy.metadataNotice}`));
 root.append(node('p','The reference is self-captured: this does not verify institutional identity or perform liveness checks. Keep this tab visible. Closing the page can lose unsent clips. Flags support human review and do not prove misconduct.'));
 const label=node('label',null,'fg-check'),check=node('input');check.type='checkbox';label.append(check,document.createTextNode(' I understand and consent to webcam processing and flagged clip storage for instructor review.'));
 const accept=node('button','Agree and continue'),decline=node('button','Decline');accept.disabled=true;
 check.onchange=()=>accept.disabled=!check.checked;root.append(label,accept,decline);
 return new Promise((resolve,reject)=>{
  let settled=false;
  const finish=(error)=>{if(settled)return;settled=true;input.signal?.removeEventListener('abort',cancel);accept.disabled=decline.disabled=true;
   if(error){consents.delete(container);reject(error);return;}
   const record={consentedAt:new Date().toISOString(),policyVersion:policy.policyVersion};
   consents.set(container,{...record,policy,base:api.base,mode:config.mode});resolve(record);
  };
  const cancel=()=>finish(Error('Consent cancelled'));input.signal?.addEventListener('abort',cancel,{once:true});
  decline.onclick=()=>finish(Error('Consent declined'));accept.onclick=()=>{if(check.checked)finish();};
 });
}

/** One active monitoring session per imported module. Call stopProctoring before navigation. */
export async function startProctoring(input) {
 if(active)throw Error('A proctoring session is already active or stopping');
 const examId=requireUuid(input.examId,'Exam ID');const {container,config,api}=options(input);
 const synthetic=input.synthetic===true;
 if(synthetic && config.mode!=='demo')throw Error('Synthetic mode is demo-only');
 const s={input,container,config,api,examId,synthetic,phase:'starting',controller:new AbortController(),failed:new Map(),uploads:new Set(),errors:[],monoStart:performance.now(),wallStart:Date.now(),engine:new TriggerEngine(config.thresholds),scenario:'normal'};
 active=s;s.telemetry=new Telemetry({synthetic,thresholds:config.thresholds});s.telemetry.trial=input.trial??null;
 const status=(state,message)=>{s.phase=state;if(s.status)s.status.textContent=message;notify(input.onStatus,{state,message});};
 const error=e=>{s.errors.push({at:new Date().toISOString(),message:e.message});if(s.errors.length>3000)s.errors.shift();notify(input.onError,e);if(s.status)s.status.textContent=e.message;};
 s.statusFn=status;s.errorFn=error;
 try {
  let consent=consents.get(container);
  const policy=validPolicy(await api.policy());
  if(active!==s || s.controller.signal.aborted)throw Error('Session cancelled');
  if(!consent || consent.base!==api.base || consent.mode!==config.mode || consent.policyVersion!==policy.policyVersion || consent.policy.metadataNotice!==policy.metadataNotice){
   await renderConsent({...input,signal:s.controller.signal});consent=consents.get(container);
  }
  if(s.controller.signal.aborted)throw Error('Session cancelled');
  const latestPolicy=validPolicy(await api.policy());
  if(latestPolicy.policyVersion!==consent.policyVersion||latestPolicy.metadataNotice!==consent.policy.metadataNotice){consents.delete(container);throw Error('Privacy policy changed. Read the new policy and consent again.');}
  if(s.controller.signal.aborted)throw Error('Session cancelled');s.consent=consent;consents.delete(container);
  const root=view(container,'Session monitor');s.root=root;
  const media=node('div',null,'fg-media');s.video=node('video');s.video.muted=true;s.video.autoplay=true;s.video.playsInline=true;
  s.canvas=node('canvas');s.canvas.width=640;s.canvas.height=480;s.canvas.hidden=!synthetic;s.video.hidden=synthetic;
  s.overlay=node('canvas',null,'fg-overlay');media.append(s.video,s.canvas,s.overlay);root.append(media);
  s.status=node('p');s.status.setAttribute('role','status');root.append(s.status);
  s.signals=node('p','Waiting for detection signals');root.append(s.signals);
  s.performance=node('p','Warming the evidence buffer');root.append(s.performance);
  const enroll=node('button','Capture face reference');enroll.disabled=true;root.append(enroll);
  const stop=node('button','Stop monitoring');root.append(stop);stop.onclick=()=>stopProctoring().catch(error);
  s.pending=node('div');root.append(s.pending);
  const submit=async(event,blob)=>{
   const operation=(async()=>{try{
    const saved=await api.submit(event,blob);s.failed.delete(event.eventId);
    s.telemetry.uploads??=[];s.telemetry.uploads.push({eventId:event.eventId,triggerToLoggedMs:performance.now()-event.triggerMonotonicMs});
    if(s.telemetry.uploads.length>1000)s.telemetry.uploads.shift();
    status(s.controller.signal.aborted?'stopping':'monitoring','Evidence saved and event logged for instructor review.');return saved;
   }catch(e){if(s.failed.size>=3&&!s.failed.has(event.eventId))throw Error('Upload queue is full; evidence could not be retained');s.failed.set(event.eventId,{event,blob});throw e;}
   finally{renderFailed();}})();s.uploads.add(operation);try{return await operation;}finally{s.uploads.delete(operation);}
  };
  const renderFailed=()=>{s.pending.replaceChildren();for(const {event,blob}of s.failed.values()){
   const row=node('div'),text=node('p','An evidence upload failed. Keep this page open to retry or download the clip.');
   const retry=node('button','Retry upload');retry.onclick=async()=>{retry.disabled=true;try{await submit(event,blob);}catch(e){error(e);renderFailed();}};
   const download=node('button','Save unsent clip');download.onclick=()=>{const url=URL.createObjectURL(blob),a=node('a');a.href=url;a.download=`${event.eventId}.webm`;a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);};row.append(text,retry,download);s.pending.append(row);
  }};
  s.submit=submit;
  function observe(reason,value,time){
   if(active!==s || s.phase==='stopping' || !s.enrolled || !s.recorder?.ready || document.hidden)return;
   if(performance.now()-time>config.thresholds.maxSampleGapMs){s.engine.observe(reason,null,performance.now());return;}
   const trigger=s.engine.observe(reason,value,time);if(!trigger)return;
   const event={eventId:crypto.randomUUID(),examId,reasons:[reason],triggeredAt:new Date(s.wallStart+time-s.monoStart).toISOString(),synthetic,
    consentVersion:s.consent.policyVersion,consentedAt:s.consent.consentedAt,thresholds:config.thresholds,triggerMonotonicMs:time,sustainedMs:trigger.sustainedMs};
   s.telemetry.flag(event);notify(input.onFlag,structuredClone(event));status('monitoring','An observation was flagged. Preparing a short clip for human review.');
   try{s.recorder.trigger(event);}catch(e){error(e);void stopProctoring().catch(()=>{});}
  }
  s.observe=observe;
  if(!isSecureContext || !globalThis.MediaRecorder)throw Error('Use HTTPS or localhost with a supported browser');
  if(!synthetic){
   status('starting','Requesting webcam permission');
   const stream=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:640},height:{ideal:480},frameRate:{ideal:15,max:20}},audio:false});
   if(s.controller.signal.aborted){stream.getTracks().forEach(t=>t.stop());throw Error('Session cancelled');}
   s.stream=stream;s.video.srcObject=stream;await s.video.play();
   if(s.controller.signal.aborted)throw Error('Session cancelled');
   for(const track of stream.getTracks())track.onended=()=>{if(active===s&&s.phase!=='stopping'){error(Error('Camera disconnected'));void stopProctoring().catch(()=>{});}};
   status('starting','Loading local detection models');
   const failed=e=>{if(active===s&&s.phase!=='stopping'){error(e);void stopProctoring().catch(()=>{});}};
   s.detectors=new Detectors(s.video,config,{
    face:d=>{s.face=d;s.telemetry.detection('face',d);observe('second_face',d.faceCount>1,d.time);observe('no_face',d.faceCount===0,d.time);},
    object:d=>{s.objects=d;s.telemetry.detection('object',d);observe('phone',d.boxes.some(b=>b.classId===67),d.time);},
    identity:d=>{s.identity=d;s.telemetry.detection('identity',d);observe('identity_mismatch',identityMismatch(d.distance,d.faceCount,config.thresholds.identityDistance),d.time);},error:failed});
   await s.detectors.load();if(s.controller.signal.aborted)throw Error('Session cancelled');
  }else s.enrolled=true;
  s.recorder=new EvidenceRecorder(synthetic?s.canvas:s.video,submit,error);s.recorder.start();
  const enrollReference=async()=>{if(s.phase==='stopping'||s.controller.signal.aborted)throw Error('Session stopped');if(synthetic)return;enroll.disabled=true;
   try{await s.detectors.enroll();if(s.controller.signal.aborted)throw Error('Session stopped');s.enrolled=true;status('warming','Reference captured; filling pre-roll');}
   catch(e){enroll.disabled=false;throw e;}};
  enroll.disabled=synthetic;enroll.onclick=()=>enrollReference().catch(error);
  status(synthetic?'warming':'enroll',synthetic?'Synthetic signals; filling 7.5-second pre-roll':'Capture a clear face reference before monitoring');
  s.visibility=()=>{if(document.hidden&&active===s){error(Error('Tab hidden; monitoring stopped. Pending clips may be incomplete.'));void stopProctoring().catch(()=>{});}};
  document.addEventListener('visibilitychange',s.visibility);
  s.pagehide=()=>{s.detectors?.stop();s.stream?.getTracks().forEach(t=>t.stop());s.recorder?.stop();s.controller.abort();if(active===s)active=null;};
  window.addEventListener('pagehide',s.pagehide);
  s.tick=(async()=>{while(active===s&&s.phase!=='stopping'){
   const time=performance.now();
   if(synthetic){const ctx=s.canvas.getContext('2d');ctx.fillStyle='#183e33';ctx.fillRect(0,0,640,480);ctx.fillStyle='white';ctx.font='24px sans-serif';ctx.fillText('SYNTHETIC DEMONSTRATION',25,50);ctx.fillText(s.scenario,25,100);ctx.fillText(`${((time-s.monoStart)/1000).toFixed(1)} seconds`,25,440);for(const reason of REASONS)observe(reason,s.scenario===reason,time);}
   else{s.detectors.tick(time).catch(failedInference);draw(s);}
   if(s.enrolled&&s.recorder.ready&&!s.telemetry.armedAt){s.telemetry.armedAt=performance.now();status('monitoring','Monitoring active. Keep this tab visible.');}
   const sample=s.telemetry.sample(s.recorder,synthetic?s.canvas:s.video);
   if(sample)s.performance.textContent=`Capture ${sample.captureFps.toFixed(1)} fps; buffer ${(sample.bufferBytes/1048576).toFixed(1)} MiB; JS heap ${sample.heapBytes===null?'unavailable':(sample.heapBytes/1048576).toFixed(1)+' MiB'}`;
   await wait(100);
  }})();
  function failedInference(e){if(active===s&&s.phase!=='stopping'){error(e);void stopProctoring().catch(()=>{});}}
  const controller={enroll:enrollReference,stop:stopProctoring,
   setScenario:value=>{if(!synthetic||config.mode!=='demo')throw Error('Synthetic control is demo-only');if(!['normal',...REASONS].includes(value))throw Error('Invalid scenario');s.scenario=value;},
   exportDiagnostics:()=>({exportedAt:new Date().toISOString(),telemetry:{...s.telemetry.export(),uploads:s.telemetry.uploads??[]},trial:s.telemetry.trial,errors:s.errors}),
   recordIdentityTrial:({alias,referenceAlias,participantConsent,split='calibration'})=>{
    const d=s.identity;if(synthetic||!participantConsent||![alias,referenceAlias].every(v=>typeof v==='string'&&/^[A-Za-z][A-Za-z0-9_-]{0,19}$/.test(v))||!['calibration','validation'].includes(split))throw Error('Consenting real participants and valid aliases are required');
    if(!d||performance.now()-d.time>3000||d.faceCount!==1||!Number.isFinite(d.distance)||s.lastIdentityTrial===d.time)throw Error('A new, recent clear-face inference is required');
    if(s.telemetry.identityTrials.length>=1000)throw Error('Export the trial batch before continuing');s.lastIdentityTrial=d.time;
    const trial={trialId:crypto.randomUUID(),at:new Date().toISOString(),alias,referenceAlias,participantConsent:true,split,genuine:alias===referenceAlias,distance:d.distance};s.telemetry.identityTrials.push(trial);return trial;
   }};
  s.public=controller;return controller;
 }catch(e){error(e);if(active===s)await stopProctoring().catch(()=>{});throw e;}
}
function draw(s){
 const c=s.overlay;c.width=s.video.videoWidth||640;c.height=s.video.videoHeight||480;const ctx=c.getContext('2d');ctx.lineWidth=2;ctx.font='16px sans-serif';
 if(s.face&&performance.now()-s.face.time<2000){ctx.strokeStyle='#74efb7';for(const b of s.face.boxes)ctx.strokeRect(b.originX,b.originY,b.width,b.height);ctx.fillStyle='#74efb7';for(const face of s.face.landmarks)for(const p of face){ctx.fillRect(p.x*c.width,p.y*c.height,1,1);}}
 if(s.objects&&performance.now()-s.objects.time<2000)for(const b of s.objects.boxes){ctx.strokeStyle='#ffc96b';ctx.fillStyle='#ffc96b';ctx.strokeRect(b.x,b.y,b.width,b.height);ctx.fillText(`${b.label} ${Math.round(b.score*100)}%`,b.x,Math.max(18,b.y-6));}
 s.signals.textContent=`Faces: ${s.face?.faceCount??'unknown'}; people: ${s.objects?.boxes.filter(b=>b.classId===0).length??'unknown'}; phones: ${s.objects?.boxes.filter(b=>b.classId===67).length??'unknown'}; identity distance: ${s.identity?.distance?.toFixed(3)??'unavailable'}`;
}

/** Stops camera immediately, then drains captured evidence and retries failed uploads once.
 * Partial post-roll is labeled. Rejects if evidence remains unsent; retain the page to retry. */
export async function stopProctoring(){
 const s=active;if(!s)return;if(s.stopping)return s.stopping;
 s.phase='stopping';s.controller.abort();s.telemetry.endedAt=performance.now();
 s.detectors?.stop();s.stream?.getTracks().forEach(t=>t.stop());if(s.video)s.video.srcObject=null;
 document.removeEventListener('visibilitychange',s.visibility);window.removeEventListener('pagehide',s.pagehide);
 s.stopping=(async()=>{
  try{s.statusFn('stopping','Camera stopped; finishing captured clips and pending uploads.');await s.recorder?.finish();await Promise.allSettled([...s.uploads]);
   for(const {event,blob}of [...s.failed.values()]){try{await s.submit(event,blob);}catch{/* retained with explicit download/retry UI */}}
   if(s.failed.size)throw Error(`${s.failed.size} clip(s) remain unsent. Keep this page open and retry or save them.`);
   if(s.recorder?.failures.some(e=>e.evidenceEncodingFailure) || s.errors.some(e=>/queue is full/i.test(e.message)))throw Error('Some evidence could not be encoded. Inspect session diagnostics.');
   s.statusFn('stopped','Monitoring stopped. Camera, reference and rolling buffer cleared; pending uploads finished.');
  }finally{s.recorder?.stop();if(s.failed.size){s.phase='upload_failed';s.stopping=null;}else if(active===s)active=null;}
 })();return s.stopping;
}

/** Returns { ready, reload, destroy }. No routing, exam text box, or global element IDs. */
export function mountReview(input){
 const examId=requireUuid(input.examId,'Exam ID');const {container,config,api}=options(input,'instructor');
 const root=view(container,'Instructor evidence review'),status=node('p'),list=node('div');status.setAttribute('role','status');
 const reload=node('button','Reload events');root.append(reload,status,list);let disposed=false,generation=0;
 const expiredMessage='Clip deleted after the 7-day retention period';
 function card(initial){let event=initial;const article=node('article',null,'fg-event');
  function render(){article.replaceChildren();article.append(node('h3',event.reasons.join(' · ').replaceAll('_',' ')),node('p',`${event.studentEmail??'Email unavailable'} · ${new Date(event.triggeredAt).toLocaleString()}`));
   if(config.mode==='demo')article.append(node('p','LOCAL DEMONSTRATION - synthetic test'));
   article.append(node('p',event.clip?.complete?'Complete requested evidence window':'Partial evidence window - interpret cautiously'));
   article.append(node('p',event.reviewed?`Decision: ${event.instructorDecision}`:'Awaiting review'));
   const message=node('p');message.setAttribute('role','status');const video=node('video');video.controls=true;video.hidden=true;
   const play=node('button',event.clipExpired?'Clip expired':'Load private clip');play.disabled=!!event.clipExpired;
   if(event.clipExpired)message.textContent=expiredMessage;
   play.onclick=async()=>{play.disabled=true;try{video.src=await api.playback(event.eventId);if(disposed)return;video.hidden=false;message.textContent='Private playback loaded.';}catch(e){message.textContent=e.status===410?expiredMessage:e.message;if(e.status===410)event.clipExpired=true;}finally{play.disabled=!!event.clipExpired;}};
   video.onerror=()=>{message.textContent='Playback link failed or expired. Reload the private clip.';};
   const confirm=node('button','Confirm observation'),dismiss=node('button','Dismiss flag');
   for(const [button,decision]of [[confirm,'confirmed'],[dismiss,'dismissed']])button.onclick=async()=>{
    confirm.disabled=dismiss.disabled=true;try{const saved=await api.review(event.eventId,decision,event.version);if(disposed)return;event=saved;render();}
    catch(e){if(e.status===409){status.textContent='Changed by another reviewer, reloading';await load(true);}else message.textContent=e.message;}
    finally{confirm.disabled=dismiss.disabled=false;}
   };
   article.append(video,play,confirm,dismiss,message);
  }render();return article;
 }
 async function load(conflict=false){const id=++generation;reload.disabled=true;if(!conflict)status.textContent='Loading events';
  try{const {events}=await api.list(examId);if(disposed||id!==generation)return;list.replaceChildren(...events.map(card));status.textContent=(conflict?'Changed by another reviewer, reloading. ':'')+`${events.length} event(s). Newest first; backend returns at most 200.`;}
  catch(e){if(!disposed)status.textContent=e.message;}finally{if(!disposed)reload.disabled=false;}
 }
 reload.onclick=()=>load();return{ready:load(),reload:()=>load(),destroy(){disposed=true;generation++;for(const video of root.querySelectorAll('video')){video.pause();video.removeAttribute('src');video.load();}root.remove();}};
}
