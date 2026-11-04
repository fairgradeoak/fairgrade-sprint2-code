# Real-camera acceptance run - localhost operator worksheet

Updated 3 November 2026. Omar supplied the public Cognito configuration and enrolled exam; these are installed in both config files. His Postman successes are reported evidence, not tests performed here. The original 1 November deadline has passed; use the requested 2-14 November improvement window for remaining real measurements. No appointment or team message has been sent automatically.

## Launch and sign in

1. Extract all three delivery ZIPs into the **same parent directory**. They merge into `FairGrade/`; models and vendor files must end up under `FairGrade/Khaled_Code/FairGrade-Proctoring/public/`. Do not create a nested `FairGrade/FairGrade` directory.
2. Install Node.js 22 or later. Run `START_FAIRGRADE.cmd` on Windows, or `sh START_FAIRGRADE.sh` on macOS/Linux. Both force port 3000 and verify every model/vendor hash before starting. No npm install is needed to run the bundled app; `npm ci` is needed for development tests.
3. Open **http://localhost:3000/**, never 127.0.0.1, a different port, `/index.html`, or a file URL. Only `/` and `/review.html` are registered callbacks. Localhost supports webcam permission without HTTPS. Public deployment still requires HTTPS and Omar's registration/CORS changes.
4. Keep **Omar's live API + camera** selected. The exam is prefilled with `f36e76ba-cbec-4943-ac1a-da15dd9031e8`. Sign in as `student_1@test.com` using the password Omar gives you privately, entered only in Cognito. Enrollment is required; starting an exam attempt is not required.
5. Click **Load policy and consent**, read the 7-day notice, consent, and grant camera permission. Capture the reference using the module button; wait for pre-roll and Monitoring active. A camera preview alone does not prove every detector is ready. Check inference updates/errors.
6. Hold a real phone clearly in view long enough to meet the unchanged sustained threshold; allow time for post-roll, encoding, upload and event logging. Stop and flush before closing or switching pages. Keep this tab visible throughout monitoring.
7. Open **http://localhost:3000/review.html** in a separate browser profile/private window, then sign in as `instructor_1@test.com`. This avoids Cognito reusing the student login. Click **Load review** and identify the event by time/reason; confirm studentEmail is shown.
8. Play the clip and confirm it. For the conflict test, sign in to two independent instructor tabs and load the same event/version in both before changing either. Confirm in one; then dismiss from the stale card in the other. Record 409 and the reload notice. Do not reload the stale card beforehand. Memory-only tokens mean a full page reload requires sign-in again (Cognito may reuse its session).

## Safe evidence collection

Open browser DevTools Network before the run. Record method, route path, HTTP status, timestamp and duration manually in `evidence/live/status.json`; keep URLs stripped of query strings. Do **not** export a HAR or copy request headers: these can contain tokens, cookies or signed S3 credentials. Record a sanitized error body if a step fails, excluding any credentials or participant information. For playback, distinguish the API's 200 from the actual S3 media GET (200 or 206).

Take a screenshot of each actual step after hiding the camera/video surface and any account/credential panels. Never screenshot a password, access token, authorization code, signed URL or upload fields. Keep original participant footage and signed consent forms private; aliases only in shared evaluation. Consent must cover the capture and sharing performed. List the resulting filenames in `realCameraScreenshots`; do not substitute the local/mock screenshots under phase3.

`liveHttpSteps` starts empty because no authenticated run has been observed here. Each recorded item should contain `step`, `method`, `route`, `observedAt`, `httpStatus`, `durationMs`, `result`, and an optional sanitized `errorBody`. Mark `status` as `passed` only after every required camera-to-review step really succeeds; otherwise use `failed` or `incomplete` and identify the failed step. A local fixture or terminal transport test cannot prove browser CORS or real inference.

| Step | Required observation | Actual HTTP / evidence |
|---|---|---|
| Student sign-in | Student access-token provider works | To be measured |
| GET /policy | 200, approved, 7 days, correct version | To be measured |
| Consent | Checked before any camera access | Screenshot pending real session |
| Camera + reference | All models loaded, reference enrolled, pre-roll ready | Screenshot and laptop metrics needed |
| Phone trigger | Sustained real phone observation, flag callback | Actual trigger time needed |
| POST /clips/presign | 200 with fields and five-minute expiry | To be measured |
| POST S3 multipart | 204; all fields, file last, browser boundary | To be measured |
| POST /events | 201, wrapped event; identical retry 200 | To be measured |
| Instructor GET /events | 200; studentEmail, correct event | To be measured |
| Playback | 200 signed GET; actual playable clip | To be measured |
| PATCH review | 200 full EVENT; version advances | To be measured |
| Conflict | Submit old version: 409; UI reloads list | To be measured |
| Retention | Approved expired test event: 410 and seven-day text | Coordinate test record with Omar |

Save operator-completed evidence under evidence/live privately. Do not call the existing synthetic screenshots real-camera evidence. A terminal transport check cannot prove browser CORS, camera inference or user consent.

## Performance and participants

Run 20 minutes on the target laptop with all three detectors. Record manufacturer/model, CPU/GPU/RAM, OS/browser, power mode and settings in evidence/live/performance.json. Take CPU % and browser-tab memory readings at 0, 10 and 20 minutes, using Task Manager / browser Task Manager and recording the measurement scope. Record average/minimum camera FPS from scalar diagnostics and at least three real trigger-to-event-logged latencies. Do not confuse camera FPS with per-detector throughput. Export scalar diagnostics after stopping; capture camera/capture FPS, per-detector latency, trigger-to-event-logged time, OS CPU % and process memory. Report null for unavailable metrics until actually measured.

Obtain written consent from at least three people, use aliases, and run five 10-minute normal sessions. Deliberate cases are separate: phone 10, second face 10, leaving frame 10, identity swap 5. Record detection/miss count and predeclared deadline for every attempt. Follow TRIAL-PROTOCOL.md; do not treat consecutive frames as independent attempts. Use scripts/summarize.py for flags/hour and confidence intervals. Defaults remain unchanged unless those results justify an adjustment; record before/after in evaluation/tuning-log.json.

## Evaluation data entry and summary

Add only completed, reviewed, written-consent observations to `evaluation/trials.json`. For a normal session, record `sessionId`, `round: "integrated"`, `alias`, `synthetic: false`, `participantConsent: true`, `reviewed: true`, actual `armedSeconds`, `thresholds`, and `flags` (each actual event needs `eventId`, `reason`, and a reviewed `falsePositive` boolean). Exclude enrollment/warmup. Five normal sessions need 600 seconds of armed exposure each; shortened sessions must retain their actual duration.

For each deliberate attempt record `caseId`, `round: "integrated"`, `alias`, `reason`, `synthetic: false`, `participantConsent: true`, and the observed `detected` boolean. Also record the predeclared deadline, onset and detection times, latency and miss notes. An aborted/unknown case is not a miss or a success: retain it separately in operator notes. Wait out cooldown and return to neutral between attempts. Leave the system visible during second-person and identity-swap cases.

Run `python scripts/summarize.py evaluation/trials.json --output evidence/live/trial-summary.json` (install `scipy` if needed). The utility produces exact Poisson intervals for flags/hour and Wilson intervals for detection rates. Report misses as total minus success. No observations produces null rates, not zero error. Keep unrun cases in `trial-plan.json`, outside the statistics input; add actual dates only after arranging participants. Thresholds remain unchanged unless reviewed calibration data supports a documented change.
