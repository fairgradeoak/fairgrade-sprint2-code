import {chromium} from 'playwright';
import {mkdir,mkdtemp,writeFile,rm} from 'node:fs/promises';
import {join} from 'node:path';import {tmpdir} from 'node:os';import assert from 'node:assert/strict';
import {createDemoServer} from '../server/server.mjs';
const dir=await mkdtemp(join(tmpdir(),'fairgrade-browser-')),out='evidence/phase3';await mkdir(out,{recursive:true});
const {server}=await createDemoServer({dataDir:dir});await new Promise(r=>server.listen(0,'127.0.0.1',r));
const origin=`http://127.0.0.1:${server.address().port}`,browser=await chromium.launch({args:['--no-sandbox']});
const checks=[],errors=[];
try{
 const page=await browser.newPage({viewport:{width:1366,height:1000}});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(origin);await page.selectOption('#mode','demo');await page.click('#start');
 await page.waitForSelector('.fg-check');assert.equal(await page.getByRole('button',{name:'Agree and continue',exact:true}).isDisabled(),true);checks.push('Consent required before monitoring');
 await page.screenshot({path:join(out,'consent-screen.png'),fullPage:true});
 await page.locator('.fg-check input').check();await page.getByRole('button',{name:'Agree and continue',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Monitoring active'),null,{timeout:20000});checks.push('Preroll warms before monitoring');
 await page.selectOption('#scenario','phone');
 await page.waitForFunction(()=>document.querySelector('#monitor').textContent.includes('Evidence saved and event logged'),null,{timeout:60000});checks.push('Trigger → encoding → POST-form upload → wrapped event');
 const {events}=await (await fetch(`${origin}/api/events?examId=11111111-1111-4111-8111-111111111111`,{headers:{'X-Demo-Role':'instructor'}})).json();
 assert.equal(events.length,1);const event=events[0];assert.equal(event.synthetic,true);assert.equal(event.clip.complete,true);assert.ok(Math.abs(event.clip.sourceDurationMs-15000)<=250);assert.ok(Math.abs(event.clip.encodedElapsedMs-15000)<=500);checks.push('15 second evidence window, pre/post timing within tolerance');
 await page.selectOption('#scenario','normal');await page.click('#stop');await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('pending uploads finished'),null,{timeout:30000});checks.push('Stop flushes evidence and clears buffer');
 await page.goto(`${origin}/review.html`);await page.selectOption('#mode','demo');await page.click('#load');await page.waitForSelector('.fg-event');await page.getByText('Load private clip',{exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('.fg-event video').readyState>=2);const video=await page.locator('video').evaluate(v=>({width:v.videoWidth,height:v.videoHeight}));assert.deepEqual(video,{width:640,height:480});checks.push('Recorded WebM decodes');
 await page.getByText('Confirm observation',{exact:true}).click();await page.waitForFunction(()=>document.querySelector('.fg-event').textContent.includes('Decision: confirmed'));
 await page.getByText('Reload events',{exact:true}).click();await page.waitForFunction(()=>document.querySelector('.fg-event')?.textContent.includes('Decision: confirmed'));checks.push('Instructor review persists across reload');
 await page.getByText('Load private clip',{exact:true}).click();await page.waitForFunction(()=>document.querySelector('.fg-event video').readyState>=2);
 await page.screenshot({path:join(out,'review-page.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);checks.push('Mobile review layout fits viewport');
 assert.deepEqual(errors,[]);checks.push('No uncaught browser exceptions');
 await writeFile(join(out,'browser-report.json'),JSON.stringify({at:new Date().toISOString(),browser:browser.version(),checks,event,video,errors,limitations:['Synthetic signals and local storage only; not webcam accuracy or AWS']},null,2));
 console.log(JSON.stringify({passed:checks.length,checks}));
}catch(e){await writeFile(join(out,'browser-failure.json'),JSON.stringify({error:e.message,errors,checks},null,2));throw e;}
finally{await browser.close();await new Promise(r=>server.close(r));await rm(dir,{recursive:true,force:true});}
