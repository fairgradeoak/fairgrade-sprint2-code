> Sprint 3 update: use Omar's deployed root API contract and seven-day policy. Required deliberate counts are phone 10, second face 10, leaving frame 10, identity swap 5; at least three consenting people and five 10-minute normal sessions. See LIVE-ACCEPTANCE.md and PARTICIPANT-CONSENT.md. Earlier references to deploying our proposal are superseded.

# Real-world validation protocol — Khaled

No participant trials have been performed by this update. All empty result fields mean **not measured**. Automated synthetic clips and blank-image model checks must never be mixed with human accuracy results.

## Before each session

Explain the purpose, video-only monitoring, self-captured face reference, expected flags, who can review clips, retention, stopping/withdrawal process and the voluntary alternative. Obtain the institution's required participant consent. Use aliases P01–P05 in research data; keep any consent records and identity key separately under the institution's controls. Never export face embeddings or reference images. Avoid incidental people and identifying background material. In live mode the event records still use institutional student UUIDs; aliases apply to evaluation records.

Record laptop CPU/RAM/GPU, OS/browser/version, power mode, webcam resolution, room/lighting description, model provenance SHA-256, config thresholds, network type and backend mode. Use one visible active tab, connect power, close unnecessary applications. On the page, set trial consent, alias, round and scenario **before starting**. Session metadata is fixed at start; separate sessions per scenario make denominators auditable. Start webcam, enroll the reference, wait for MONITORING. Begin the trial timer only after this state.

## September 22–25: hardware and identity

1. Run `npm run verify:models`. Start with `npm start`, open localhost, allow the camera only after consent. Observe bounding boxes, landmarks, person/phone counts, identity distance and latency. Export diagnostics after stopping. The diagnostics include capture FPS, camera FPS where supported, inference frequency/median/p95, rolling buffer bytes and browser JS heap where available. Missing metrics are null, not zero.
2. For face, phone and second-person observations, test bright/front light, dim light and backlight; frontal and left/right turns; near/far objects. Record each expected observation, whether a box appeared, count, confidence and delay. Include no-object controls. YOLO person count is displayed, but the current extra-person flag is based on **second face**, so a second person without a detectable face can be missed. Landmarks/head turns are diagnostic only, not guilt or gaze inference.
3. Identity: at least 3 consenting people, aliases only. For each reference identity collect multiple separate genuine attempts and attempts from the other people. Reposition and wait for new inference between attempts; consecutive frames are not independent subjects. Use “Record current identity distance” with actual participant and reference aliases. `genuine` means the aliases match. One clear face is required. Unknown/failed inferences must be separately tallied, never silently counted as matches.
4. Predefine calibration and held-out validation attempts. Select `identity_calibration` or `identity_validation`. Keep validation attempts out of threshold selection. Aim for at least 10 genuine and 10 impostor attempts per reference across different positions/lighting; this is a feasibility target, not proof of population-level accuracy. The summary proposes the calibration threshold minimizing balanced error under a 5% empirical false-accept cap and reports held-out FAR/FRR with Wilson intervals. It does not change config automatically. The current 0.55 default is **not tuned** from human data.
5. Run 20–30 minutes continuously on the target laptop with all detectors. Sample OS process memory separately every minute: JS heap excludes GPU/WASM and total process memory. Check FPS, p95 latency, input responsiveness, buffer span and frame count, failed inference, pending queues and dropped/partial clips. Re-enroll/restart several times afterward to check resource cleanup. Export diagnostics at the end. If results become stale (>1.5s default), sustained detection is reset; do not hide this by claiming a good frame rate. Lower inference cost or use appropriate hardware before evaluation.

## September 26–28: baseline false-positive round

Use approximately 5 consenting participants, **10 armed minutes each**, split into five 2-minute scenarios: normal head movement, glasses glare (record N/A if no glasses), lighting variation within comfortable conditions, reading aloud, and ordinary nearby objects such as a notebook or mug. Record the exact armed duration, not scheduled duration. No deliberate second person, phone use or swap during these normal-behavior exposure segments.

Review every observation against the protocol and mark `falsePositive:true/false`; document disputed classifications separately. A flag is not a cheating conclusion. Keep intentional positive tests separate from normal exposure. Save each diagnostic export, import it using the command below, then review the candidate dataset. Use `reviewed:true` only after verifying its exposure, scenario and all flag classifications.

```bash
python scripts/import-diagnostics.py path/to/session1.json path/to/session2.json --output evaluation/private/candidate.json
python scripts/summarize.py evaluation/private/reviewed-trials.json --output evaluation/private/summary.json
```
Create `evaluation/private` first. The importer never marks trials reviewed or guesses false positives. It rejects synthetic, unfinished or truncated exports. Preserve originals privately; copy only approved alias-only aggregate results into a report. Merge datasets by stable session ID; duplicate sessions are rejected.

## Tuning and comparison

Freeze a baseline copy of config before trials. Review which reasons and scenarios cause false flags. Change one threshold/duration at a time, record the old/new value and rationale, then repeat the same scenarios with a held-out round. Do not increase cooldown merely to make flags/hour smaller; report detection rate and latency alongside it. Keep model versions, exposure and hardware comparable. `evaluation/tuning-log.json` records decisions but contains no invented tuning.

## October 6–9: integrated and missed-detection rounds

After real AWS acceptance, repeat normal-behavior sessions through trigger → capture → private S3 → RDS → instructor review. Label this `integrated`; do not call local mock tests integrated. Record upload/review failures, latency and missing clips as reliability outcomes.

Separately schedule deliberate cases: sustained visible phone, second person with visible face, identity swap after genuine enrollment, and sustained face absence. Respect the configured sustain duration; reset to normal and wait out cooldown before another attempt. Predefine an observation deadline (e.g. sustain duration + 5 seconds after detector warmup). Record every attempt, including misses, aborts and unavailable inference. For completed eligible attempts, `detected` is whether the matching flag occurred within that deadline; add latency and evidence-pipeline outcome. Do not count synthetic switches as detector successes. Do not label body-only second-person cases as supported face-count detection without recording the limitation.

## Dataset example (structure only — do not count this as data)

```json
{
 "sessions":[{"sessionId":"unique-session","alias":"P01","round":"baseline","scenario":"head_movement","synthetic":false,"participantConsent":true,"reviewed":true,"armedSeconds":120,"thresholds":{},"flags":[{"eventId":"observed-event-uuid","reason":"phone","falsePositive":true}]}],
 "identityTrials":[{"trialId":"unique-attempt","alias":"P02","referenceAlias":"P01","genuine":false,"distance":0.7,"split":"calibration","participantConsent":true}],
 "detectionCases":[{"caseId":"unique-case","alias":"P01","round":"integrated","reason":"phone","synthetic":false,"participantConsent":true,"detected":true,"latencyMs":2500,"deadlineMs":7000,"clipLogged":true}]
}
```

Report flags/hour and false flags/hour with exact 95% Poisson intervals; deliberate detection rate with 95% Wilson intervals; genuine/impostor distances and FAR/FRR; hardware/latency; dropped clips and upload failures. Poisson assumes independent constant-rate events; repeated participants, scenario clustering and cooldown can violate it. These are descriptive feasibility intervals, not proof that the system is fair or reliable for all students. Report participant counts, exposure and all exclusions.

## Acceptance and stop conditions

A crash, denied consent, broken camera, hidden tab, unavailable model, sustained excessive latency or unresolved data loss prevents a “passed” trial. Stop, preserve diagnostics and fix before retrying. Real readiness requires human trial evidence, agreed accuracy/performance targets, explicit approved retention, successful private AWS integration and team sign-off. This prototype does not provide liveness, official identity verification, attention/gaze conclusions or automatic misconduct decisions.
