import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {DEFAULT_THRESHOLDS} from '../public/proctoring-module.mjs';
import {configureHarness} from '../public/core/harness.mjs';
import {CognitoSession} from '../public/core/auth.mjs';

const read = name => readFile(new URL('../public/'+name,import.meta.url),'utf8').then(JSON.parse);
test('shipped live settings match Omar and preserve detection thresholds',async()=>{
 const config=await read('config.json');assert.deepEqual(config,await read('config.live.example.json'));
 assert.equal(config.mode,'live');assert.equal(config.apiBase,'https://gnlnv6dd5j.execute-api.eu-north-1.amazonaws.com');
 assert.equal(config.examId,'f36e76ba-cbec-4943-ac1a-da15dd9031e8');
 assert.deepEqual(config.thresholds,DEFAULT_THRESHOLDS);assert.equal(config.retentionDays,7);assert.equal(config.policyVersion,'fairgrade-2026-10');
 assert.deepEqual(config.uploadOrigins,['https://s3.eu-north-1.amazonaws.com']);assert.deepEqual(config.playbackOrigins,config.uploadOrigins);
 assert.deepEqual(config.auth,{domain:'https://eu-north-19fsulifsf.auth.eu-north-1.amazoncognito.com',clientId:'l648ijjqhpk1pt5bhv8b0us0b',redirectUris:{'/':'http://localhost:3000/','/review.html':'http://localhost:3000/review.html'},scopes:['openid']});
});
test('harness switches between enrolled live exam and isolated demo exam',async()=>{
 const config=await read('config.json');let change;const mode={value:'',addEventListener:(name,fn)=>{assert.equal(name,'change');change=fn;}},exam={value:''};
 configureHarness(config,mode,exam);assert.equal(mode.value,'live');assert.equal(exam.value,config.examId);
 mode.value='demo';change();assert.equal(exam.value,'11111111-1111-4111-8111-111111111111');
 mode.value='live';change();assert.equal(exam.value,config.examId);
});
test('registered callbacks work on localhost and reject alternate origins',async()=>{
 const config=await read('config.json');
 for(const pathname of ['/','/review.html']){
  const c={...config,auth:{...config.auth,redirectUri:config.auth.redirectUris[pathname]}};
  globalThis.location={origin:'http://localhost:3000',pathname};assert.equal(new CognitoSession(c).settings().redirectUri,c.auth.redirectUri);
  for(const origin of ['http://127.0.0.1:3000','http://localhost:4173']){
   globalThis.location={origin,pathname};assert.throws(()=>new CognitoSession(c).settings(),/must match this page/);
  }
 }
});
