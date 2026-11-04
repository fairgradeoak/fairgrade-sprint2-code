import{configureHarness}from'./core/harness.mjs';
import{startProctoring,stopProctoring}from'./proctoring-module.mjs';
import{mountAuth}from'./core/auth.mjs';
const $=id=>document.getElementById(id);const config=await(await fetch(new URL('./config.json',import.meta.url))).json();
configureHarness(config,$('mode'),$('exam'));
const auth=await mountAuth(config,$('auth'));let controller;
const report=e=>$('status').textContent=e.message;
$('start').onclick=async()=>{const demo=$('mode').value==='demo';$('start').disabled=true;
 try{controller=await startProctoring({examId:$('exam').value,apiBase:demo?new URL('./api',import.meta.url).href:config.apiBase,getAccessToken:auth.getAccessToken,container:$('monitor'),mode:demo?'demo':'live',synthetic:demo,
 trial:{alias:$('alias').value,participantConsent:$('trial-consent').checked,round:$('round').value,scenario:$('trial-scenario').value},onStatus:report,onError:report,onFlag:e=>{$('status').textContent=`Flagged ${e.reasons.join(', ')} for human review`;}});$('simulation').hidden=!demo;
 }catch(e){report(e);$('start').disabled=false;}};
$('stop').onclick=async()=>{try{await stopProctoring();$('start').disabled=false;}catch(e){report(e);}};
$('scenario').onchange=()=>{try{controller?.setScenario($('scenario').value);}catch(e){report(e);}};
$('export').onclick=()=>{if(!controller)return;const blob=new Blob([JSON.stringify(controller.exportDiagnostics(),null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='fairgrade-diagnostics.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);};
$('identity').onclick=()=>{try{if(!controller)throw Error('Start a real-camera session first');const sample=controller.recordIdentityTrial({alias:$('alias').value,referenceAlias:$('reference').value,participantConsent:$('trial-consent').checked,split:$('trial-scenario').value==='identity_validation'?'validation':'calibration'});$('status').textContent=`Identity trial recorded: distance ${sample.distance.toFixed(3)}`;}catch(e){report(e);}};
