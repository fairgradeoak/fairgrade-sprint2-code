// Uses the shipped config with intercepted Cognito/API responses. NOT a live AWS test.
import {chromium} from 'playwright';
import {mkdtemp,mkdir,writeFile,rm,readFile} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import assert from 'node:assert/strict';
import {createDemoServer} from '../server/server.mjs';
const config=JSON.parse(await readFile('public/config.json','utf8'));
const dir=await mkdtemp(join(tmpdir(),'fairgrade-localhost-'));
const {server}=await createDemoServer({dataDir:dir});
await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(3000,'127.0.0.1',resolve);});
let browser;const checks=[];
try {
 browser=await chromium.launch({args:['--no-sandbox']});
 for(const path of ['/','/review.html']){
  const page=await browser.newPage(),errors=[];let authorize;
  page.on('pageerror',e=>errors.push(e.message));
  await page.route(config.auth.domain+'/**',async route=>{
   const u=new URL(route.request().url());
   if(u.pathname==='/oauth2/authorize'){
    authorize=u;
    return route.fulfill({contentType:'text/html',body:'<p>Intercepted test login. No real account used.</p>'});
   }
   assert.equal(u.pathname,'/oauth2/token');const body=new URLSearchParams(route.request().postData());
   assert.equal(body.get('client_id'),config.auth.clientId);assert.equal(body.get('redirect_uri'),'http://localhost:3000'+path);
   assert.ok(body.get('code_verifier'));assert.equal(body.has('client_secret'),false);
   return route.fulfill({json:{access_token:'mock-only-access',expires_in:3600}});
  });
  let apiCalls=0;
  await page.route(config.apiBase+'/**',async route=>{
   apiCalls++;assert.equal(route.request().headers().authorization,'Bearer mock-only-access');
   const u=new URL(route.request().url());
   if(path==='/') {assert.equal(u.pathname,'/policy');return route.fulfill({json:{approved:true,policyVersion:'fairgrade-2026-10',retentionDays:7,metadataNotice:'Fixture metadata notice.'}});}
   assert.equal(u.pathname,'/events');assert.equal(u.searchParams.get('examId'),config.examId);return route.fulfill({json:{events:[]}});
  });
  await page.goto('http://localhost:3000'+path);
  await page.waitForFunction(id=>document.querySelector('#exam').value===id,config.examId);
  await page.selectOption('#mode','demo');assert.equal(await page.inputValue('#exam'),'11111111-1111-4111-8111-111111111111');
  await page.selectOption('#mode','live');assert.equal(await page.inputValue('#exam'),config.examId);
  checks.push(path+' shipped config and demo/live exam switching');
  await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.waitForURL(config.auth.domain+'/**');
  assert.equal(authorize.searchParams.get('redirect_uri'),'http://localhost:3000'+path);
  assert.equal(authorize.searchParams.get('client_id'),config.auth.clientId);assert.equal(authorize.searchParams.get('scope'),'openid');
  assert.equal(authorize.searchParams.get('code_challenge_method'),'S256');
  await page.goto('http://localhost:3000'+path+'?code=fixture&state='+encodeURIComponent(authorize.searchParams.get('state')));
  await page.waitForFunction(()=>document.querySelector('#auth').textContent.includes('Signed in'));
  assert.deepEqual(await page.evaluate(()=>({query:location.search,local:localStorage.length,session:sessionStorage.length})),{query:'',local:0,session:0});
  await page.click(path==='/'?'#start':'#load');
  if(path==='/')await page.waitForSelector('.fg-check');else await page.getByText('0 event(s). Newest first; backend returns at most 200.',{exact:true}).waitFor();
  assert.ok(apiCalls);assert.deepEqual(errors,[]);
  checks.push(path+' intercepted PKCE callback, memory-only token and bearer API request');
  await page.close();
 }
 await mkdir('evidence/november-config',{recursive:true});
 await writeFile('evidence/november-config/browser-report.json',JSON.stringify({at:new Date().toISOString(),passed:checks.length,checks,limitations:['Cognito and API responses intercepted. No real sign-in, webcam, AWS upload or participant trial.']},null,2));
 console.log(JSON.stringify({passed:checks.length,checks}));
} finally {await browser?.close();await new Promise(r=>server.close(r));await rm(dir,{recursive:true,force:true});}
