// Explicit real integration runner; uses externally supplied short-lived access tokens.
// Never logs tokens or signed URLs. Requires an authorized, consenting test attempt.
import{readFile,writeFile,mkdir}from'node:fs/promises';import{ApiClient}from'../public/core/api.mjs';import{requireUuid}from'../public/core/ids.mjs';
const required=['FAIRGRADE_API_BASE','FAIRGRADE_EXAM_ID','FAIRGRADE_STUDENT_TOKEN','FAIRGRADE_INSTRUCTOR_TOKEN','FAIRGRADE_CLIP','FAIRGRADE_S3_ORIGIN'];
for(const name of required)if(!process.env[name])throw Error(`Missing ${name}; use docs/DEPLOYMENT.md. No AWS test has run.`);
if(process.env.FAIRGRADE_TRIAL_CONSENT!=='yes')throw Error('Run only with a consenting authorized test participant; set FAIRGRADE_TRIAL_CONSENT=yes');
const origin=new URL(process.env.FAIRGRADE_S3_ORIGIN).origin;
const config={mode:'live',apiBase:process.env.FAIRGRADE_API_BASE,uploadOrigins:[origin],playbackOrigins:[origin]};
const student=new ApiClient(config,'student',fetch,{getAccessToken:async()=>process.env.FAIRGRADE_STUDENT_TOKEN});
const teacher=new ApiClient(config,'instructor',fetch,{getAccessToken:async()=>process.env.FAIRGRADE_INSTRUCTOR_TOKEN});
const policy=await student.policy();if(!policy.approved)throw Error('Approved policy required');
const event={eventId:crypto.randomUUID(),examId:requireUuid(process.env.FAIRGRADE_EXAM_ID),reasons:['phone'],triggeredAt:new Date().toISOString(),consentedAt:new Date().toISOString(),consentVersion:policy.policyVersion,synthetic:false,
 clip:{audio:false,complete:false,preMs:0,postMs:0,sourceDurationMs:0,encodedElapsedMs:0},integrationTest:true};
// This script verifies transport only; use the browser for a real trigger/timing test.
event.consentedAt=event.triggeredAt;
const clip=new Blob([await readFile(process.env.FAIRGRADE_CLIP)],{type:'video/webm'});
await student.submit(event,clip);await student.submit(event,clip);
let cursor=null,match=[];do{const page=await teacher.list(event.examId,cursor);match.push(...page.events.filter(e=>e.eventId===event.eventId));cursor=page.nextCursor;}while(cursor);
if(match.length!==1)throw Error('Expected exactly one logged event after retry');
const playback=await teacher.playback(event.eventId);const response=await fetch(playback,{credentials:'omit',redirect:'error'});if(!response.ok)throw Error('Private playback failed');
const received=new Uint8Array(await response.arrayBuffer()),sent=new Uint8Array(await clip.arrayBuffer());if(received.length!==sent.length||received.some((v,i)=>v!==sent[i]))throw Error('Stored bytes mismatch');
const review=await teacher.review(event.eventId,'dismissed',match[0].version);
let conflict=false;try{await teacher.review(event.eventId,'confirmed',match[0].version);}catch(e){if(e.status===409)conflict=true;else throw e;}if(!conflict)throw Error('Stale review must conflict');
await mkdir('evidence/private',{recursive:true});await writeFile('evidence/private/aws-smoke.json',JSON.stringify({at:new Date().toISOString(),eventId:event.eventId,checks:['Upload','Byte-exact private playback','Duplicate retry one event','Dismissed test flag','Stale version rejected'],reviewVersion:review.version,limitations:['Transport test only','Operator must separately verify row and audit in RDS, S3 privacy, CORS in a browser, and lifecycle deployment']},null,2));
console.log('AWS transport checks passed. Evidence saved locally; no tokens or signed URLs recorded.');
