import{configureHarness}from'./core/harness.mjs';
import{mountReview}from'./proctoring-module.mjs';import{mountAuth}from'./core/auth.mjs';
const $=id=>document.getElementById(id),config=await(await fetch(new URL('./config.json',import.meta.url))).json();
configureHarness(config,$('mode'),$('exam'));
const auth=await mountAuth(config,$('auth'));let mounted;
$('load').onclick=()=>{try{mounted?.destroy();const demo=$('mode').value==='demo';mounted=mountReview({container:$('review'),examId:$('exam').value,apiBase:demo?new URL('./api',import.meta.url).href:config.apiBase,getAccessToken:auth.getAccessToken,mode:demo?'demo':'live'});}catch(e){$('status').textContent=e.message;}};
