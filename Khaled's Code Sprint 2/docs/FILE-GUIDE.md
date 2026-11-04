# File guide and presentation rehearsal - Khaled

This adaptation was prepared with ChatGPT assistance. Khaled should read and run it, explain its decisions and limitations, and acknowledge assistance according to university policy. The original teammate files were preserved; no independent authorship or unperformed trials are claimed.

## Explain the flow in your own words

1. The host passes examId, a DOM container and an access-token callback. The module fetches the seven-day policy and obtains consent before camera access.
2. MediaPipe finds faces/landmarks, YOLO finds phone/person boxes, and face-api compares a self-captured reference. These signals are imperfect observations, not proof of identity or misconduct.
3. TriggerEngine requires fresh sustained samples and cooldowns. Defaults are unchanged. The RAM ring supplies pre-trigger frames; captured evidence is replayed into a new decodable WebM.
4. ApiClient asks Omar for signed POST fields, appends them unchanged and the file last, then POSTs without a bearer token to S3. Only after 204 does it log the event with the same UUID. The server owns idempotency.
5. Instructors load newest events, see studentEmail, get private playback and submit decisions with the loaded version. A 409 refreshes state; 410 explains expiry. Review response replaces the full card record.
6. stopProctoring immediately releases camera/detectors, then finishes captured clips/uploads. Ending during post-roll makes a partial clip. Failure is surfaced and retained, so the host must not navigate away prematurely.
7. Automated tests prove the stated software paths. They cannot stand in for physical laptop metrics, real-camera AWS acceptance or consenting participant trials.

## Questions to rehearse

- Why FormData and no manual Content-Type? The browser supplies the multipart boundary; S3 needs the signed fields and file last.
- Why not send the Cognito token to S3? S3 uses its temporary signed form/link, while Cognito authorizes API calls.
- What do the two event response shapes mean? POST /events wraps {event}; PATCH review returns the full event directly.
- Why no pagination UI? Omar's contract has no cursor and caps the newest-first list at 200.
- How is consent linked? policyVersion and consentedAt go with the event; the runtime policy is read before monitoring.
- Why are unmeasured rates null? No participant exposure cannot establish zero false positives or perfect detection.
- What changed with AI help? The contract adapter, module extraction, lifecycle fixes, tests, diagrams and documentation. Explain and demonstrate them before presenting.

## File inventory

Paths are relative to Khaled_Code/FairGrade-Proctoring. Model shards and generated evidence are data, not hand-written algorithms. Historical proposal files are explicitly labeled below.

| File | Purpose / what to explain |
|---|---|
| `.gitignore` | Excludes dependencies, local clips, private participant evidence, secrets, caches and Terraform state. |
| `README.md` | Current run instructions, superseded-backend notice and evidence boundaries. |
| `START_FAIRGRADE.cmd` | Supporting repository artifact; inspect its named contents before presentation. |
| `backend/proctoring/handler.py` | SUPERSEDED historical Lambda proposal. Not used or deployed; retained only for legacy regression. |
| `backend/proctoring/requirements.txt` | Dependencies for the legacy local Python tests, not instructions to deploy. |
| `docs/BACKEND-CONTRACT.md` | Documentation/protocol named by the filename. Current authority is BACKEND-CONTRACT.md and EMBEDDING.md; historical documents carry notices. |
| `docs/DEPLOYMENT.md` | Documentation/protocol named by the filename. Current authority is BACKEND-CONTRACT.md and EMBEDDING.md; historical documents carry notices. |
| `docs/EMBEDDING.md` | Documentation/protocol named by the filename. Current authority is BACKEND-CONTRACT.md and EMBEDDING.md; historical documents carry notices. |
| `docs/EVALUATION.md` | Documentation/protocol named by the filename. Current authority is BACKEND-CONTRACT.md and EMBEDDING.md; historical documents carry notices. |
| `docs/FILE-GUIDE.md` | Documentation/protocol named by the filename. Current authority is BACKEND-CONTRACT.md and EMBEDDING.md; historical documents carry notices. |
| `docs/KHALED-GUIDE.md` | Documentation/protocol named by the filename. Current authority is BACKEND-CONTRACT.md and EMBEDDING.md; historical documents carry notices. |
| `docs/LIMITATIONS.md` | Documentation/protocol named by the filename. Current authority is BACKEND-CONTRACT.md and EMBEDDING.md; historical documents carry notices. |
| `docs/LIVE-ACCEPTANCE.md` | Documentation/protocol named by the filename. Current authority is BACKEND-CONTRACT.md and EMBEDDING.md; historical documents carry notices. |
| `docs/MODELS.md` | Documentation/protocol named by the filename. Current authority is BACKEND-CONTRACT.md and EMBEDDING.md; historical documents carry notices. |
| `docs/PARTICIPANT-CONSENT.md` | Documentation/protocol named by the filename. Current authority is BACKEND-CONTRACT.md and EMBEDDING.md; historical documents carry notices. |
| `docs/PHASE2-STATUS.md` | Documentation/protocol named by the filename. Current authority is BACKEND-CONTRACT.md and EMBEDDING.md; historical documents carry notices. |
| `docs/SPRINT3-STATUS.md` | Documentation/protocol named by the filename. Current authority is BACKEND-CONTRACT.md and EMBEDDING.md; historical documents carry notices. |
| `docs/SPRINT3-VALIDATION.md` | Documentation/protocol named by the filename. Current authority is BACKEND-CONTRACT.md and EMBEDDING.md; historical documents carry notices. |
| `docs/STATUS.md` | Documentation/protocol named by the filename. Current authority is BACKEND-CONTRACT.md and EMBEDDING.md; historical documents carry notices. |
| `docs/TEAM-HANDOFF.md` | Documentation/protocol named by the filename. Current authority is BACKEND-CONTRACT.md and EMBEDDING.md; historical documents carry notices. |
| `docs/TRIAL-PROTOCOL.md` | Documentation/protocol named by the filename. Current authority is BACKEND-CONTRACT.md and EMBEDDING.md; historical documents carry notices. |
| `docs/VALIDATION.md` | Documentation/protocol named by the filename. Current authority is BACKEND-CONTRACT.md and EMBEDDING.md; historical documents carry notices. |
| `docs/design/proctoring-architecture.png` | Current PNG architecture diagram for the Sprint 3 design document; generated from the included plotting source. |
| `evaluation/phase2-summary.json` | Evaluation input/output artifact. Empty human datasets produce null rates; historical files retain earlier context. |
| `evaluation/phase3-summary.json` | Evaluation input/output artifact. Empty human datasets produce null rates; historical files retain earlier context. |
| `evaluation/requirements.txt` | SciPy and pytest requirements for evaluation/statistics checks. |
| `evaluation/results-summary.json` | Evaluation input/output artifact. Empty human datasets produce null rates; historical files retain earlier context. |
| `evaluation/results.json` | Evaluation input/output artifact. Empty human datasets produce null rates; historical files retain earlier context. |
| `evaluation/trials.json` | Empty human dataset. No trials have been fabricated. |
| `evaluation/tuning-log.json` | Recorded decision to keep defaults unchanged without human data. |
| `evidence/browser-report.json` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `evidence/historical/FairGrade-Khaled-Phase2-Handoff-SUPERSEDED.pdf` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `evidence/live/status.json` | Explicit record of blocked field work and missing prerequisites, not fabricated measurements. |
| `evidence/phase2/browser-report.json` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `evidence/phase2/consent-screen.png` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `evidence/phase2/delivery-manifest.json` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `evidence/phase2/live-ui-report.json` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `evidence/phase2/model-integrity.txt` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `evidence/phase2/model-smoke.json` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `evidence/phase2/python-test-results.txt` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `evidence/phase2/review-page.png` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `evidence/phase2/soak-report.json` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `evidence/phase2/syntax-check.txt` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `evidence/phase2/unit-test-results.txt` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `evidence/phase2/verification-summary.json` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `evidence/phase3/browser-report.json` | Current automated result or actual local screenshot. Its source and limitations are recorded; no human/AWS accuracy claim. |
| `evidence/phase3/consent-screen.png` | Current automated result or actual local screenshot. Its source and limitations are recorded; no human/AWS accuracy claim. |
| `evidence/phase3/live-ui-report.json` | Current automated result or actual local screenshot. Its source and limitations are recorded; no human/AWS accuracy claim. |
| `evidence/phase3/model-integrity.txt` | Current automated result or actual local screenshot. Its source and limitations are recorded; no human/AWS accuracy claim. |
| `evidence/phase3/model-smoke.json` | Current automated result or actual local screenshot. Its source and limitations are recorded; no human/AWS accuracy claim. |
| `evidence/phase3/module-report.json` | Current automated result or actual local screenshot. Its source and limitations are recorded; no human/AWS accuracy claim. |
| `evidence/phase3/python-test-results.txt` | Current automated result or actual local screenshot. Its source and limitations are recorded; no human/AWS accuracy claim. |
| `evidence/phase3/review-page.png` | Current automated result or actual local screenshot. Its source and limitations are recorded; no human/AWS accuracy claim. |
| `evidence/phase3/syntax-check.txt` | Current automated result or actual local screenshot. Its source and limitations are recorded; no human/AWS accuracy claim. |
| `evidence/phase3/unit-test-results.txt` | Current automated result or actual local screenshot. Its source and limitations are recorded; no human/AWS accuracy claim. |
| `evidence/phase3/verification-summary.json` | Current automated result or actual local screenshot. Its source and limitations are recorded; no human/AWS accuracy claim. |
| `evidence/review.png` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `evidence/student.png` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `evidence/synthetic-sample.webm` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `evidence/unit-test-results.txt` | Historical synthetic/local verification artifact; superseded reports are not current deployment instructions. |
| `infra/retention-approval.example.json` | Historical deployment-approval worksheet, not current runtime policy. |
| `infra/schema.sql` | SUPERSEDED historical UUID database proposal. Do not apply to Omar's deployed database. |
| `infra/storage.tf` | SUPERSEDED historical bucket/lifecycle proposal. Do not terraform apply. |
| `infra/terraform.tfvars.example` | Historical Terraform inputs. Not part of this integration deployment. |
| `output/pdf/FairGrade-Sprint3-Evaluation-Summary.pdf` | Current one-page committee summary separating local test results from missing field measurements. |
| `package-lock.json` | Exact npm dependency versions for reproducible test tooling. |
| `package.json` | Commands and development dependency declarations. npm start needs no installed production dependencies. |
| `public/app.mjs` | Thin standalone student harness: loads config/auth, passes container/exam to module, exposes synthetic controls and exports diagnostics. |
| `public/config.json` | Current root API, seven-day setting, regional S3 allowlists and unmodified thresholds. Supplied public Cognito localhost settings and enrolled test exam are installed. |
| `public/config.live.example.json` | Copy of the public live configuration shape; contains no tokens/passwords. |
| `public/core/api.mjs` | HTTP boundary: bearer API requests, HTTP-status errors, fresh signed POST forms, strict storage origins, event wrapper unwrapping and review/playback calls. Never sends bearer tokens to S3. |
| `public/core/auth.mjs` | Optional standalone Cognito PKCE adapter. Verifier/state are temporary sessionStorage data; tokens stay in memory. Main app supplies its own token callback. |
| `public/core/detectors.mjs` | Loads detector workers and face-api assets relative to this module. Captures three reference descriptors, computes Euclidean identity distance and limits overlapping inference. |
| `public/core/ids.mjs` | UUID validation plus fixed demo IDs. Does not authenticate a user. |
| `public/core/recorder.mjs` | JPEG frame sampling and fresh MediaRecorder WebM encoding. finish drains captured evidence; stop clears buffers. Partial windows and encoding failures remain explicit. |
| `public/core/telemetry.mjs` | Bounded scalar timing/FPS/buffer/heap measurements and alias-only trial data. No images, descriptors or tokens. |
| `public/core/triggers.mjs` | Sustained-condition timers, freshness resets, independent cooldowns and identity mismatch decision. Defaults were not retuned. |
| `public/core/window.mjs` | Bounded frame ring and timestamp window selection, including pre/post coverage and gap metadata. |
| `public/core/yolo.mjs` | Raw YOLO tensor decoding, class selection (person/phone), reverse letterbox coordinate mapping and class-aware NMS. |
| `public/index.html` | Development student harness controls. Production embedding does not depend on its element IDs. |
| `public/models/face_detector.tflite` | Pretrained MediaPipe model binary; not a participant recording. |
| `public/models/face_landmarker.task` | Pretrained MediaPipe model binary; not a participant recording. |
| `public/models/identity/face_landmark_68_tiny_model-shard1` | Pretrained face-api weight manifest/shard. Numeric model parameters, not student reference data; loaded locally for detection, landmarks or embeddings. |
| `public/models/identity/face_landmark_68_tiny_model-weights_manifest.json` | Pretrained face-api weight manifest/shard. Numeric model parameters, not student reference data; loaded locally for detection, landmarks or embeddings. |
| `public/models/identity/face_recognition_model-shard1` | Pretrained face-api weight manifest/shard. Numeric model parameters, not student reference data; loaded locally for detection, landmarks or embeddings. |
| `public/models/identity/face_recognition_model-shard2` | Pretrained face-api weight manifest/shard. Numeric model parameters, not student reference data; loaded locally for detection, landmarks or embeddings. |
| `public/models/identity/face_recognition_model-weights_manifest.json` | Pretrained face-api weight manifest/shard. Numeric model parameters, not student reference data; loaded locally for detection, landmarks or embeddings. |
| `public/models/identity/tiny_face_detector_model-shard1` | Pretrained face-api weight manifest/shard. Numeric model parameters, not student reference data; loaded locally for detection, landmarks or embeddings. |
| `public/models/identity/tiny_face_detector_model-weights_manifest.json` | Pretrained face-api weight manifest/shard. Numeric model parameters, not student reference data; loaded locally for detection, landmarks or embeddings. |
| `public/models/provenance.json` | Source URLs, byte sizes and SHA-256 values for downloaded runtime/model assets. |
| `public/models/yolov8n/group1-shard1of4.bin` | Pinned YOLOv8n graph metadata or numeric weights shard; paired files must stay together. AGPL-3.0 model licensing applies. |
| `public/models/yolov8n/group1-shard2of4.bin` | Pinned YOLOv8n graph metadata or numeric weights shard; paired files must stay together. AGPL-3.0 model licensing applies. |
| `public/models/yolov8n/group1-shard3of4.bin` | Pinned YOLOv8n graph metadata or numeric weights shard; paired files must stay together. AGPL-3.0 model licensing applies. |
| `public/models/yolov8n/group1-shard4of4.bin` | Pinned YOLOv8n graph metadata or numeric weights shard; paired files must stay together. AGPL-3.0 model licensing applies. |
| `public/models/yolov8n/model.json` | Pinned YOLOv8n graph metadata or numeric weights shard; paired files must stay together. AGPL-3.0 model licensing applies. |
| `public/module.css` | Scoped .fg-module styles, loaded relative to the module. No page-global ID selectors. |
| `public/proctoring-module.mjs` | Public integration API. Consent, session ownership, camera/model lifecycle, trigger callbacks, clip/upload drain, retained retries, and instructor cards. Uses caller containers and token callback. |
| `public/review.html` | Development instructor harness. Production module has no exam textbox or page navigation. |
| `public/review.mjs` | Thin standalone instructor harness: supplies host container, exam and token callback to mountReview. |
| `public/styles.css` | Standalone harness styling retained from the project. |
| `public/vendor/face-api.min.js` | Pinned upstream runtime/WASM bundle. Do not edit minified/generated vendor internals; explain its dependency role and license. |
| `public/vendor/mediapipe-wasm/vision_wasm_internal.js` | Pinned upstream runtime/WASM bundle. Do not edit minified/generated vendor internals; explain its dependency role and license. |
| `public/vendor/mediapipe-wasm/vision_wasm_internal.wasm` | Pinned upstream runtime/WASM bundle. Do not edit minified/generated vendor internals; explain its dependency role and license. |
| `public/vendor/mediapipe-wasm/vision_wasm_nosimd_internal.js` | Pinned upstream runtime/WASM bundle. Do not edit minified/generated vendor internals; explain its dependency role and license. |
| `public/vendor/mediapipe-wasm/vision_wasm_nosimd_internal.wasm` | Pinned upstream runtime/WASM bundle. Do not edit minified/generated vendor internals; explain its dependency role and license. |
| `public/vendor/tf.min.js` | Pinned upstream runtime/WASM bundle. Do not edit minified/generated vendor internals; explain its dependency role and license. |
| `public/vendor/vision_bundle.mjs` | Pinned upstream runtime/WASM bundle. Do not edit minified/generated vendor internals; explain its dependency role and license. |
| `public/workers/face-worker.mjs` | Classic worker dynamically imports MediaPipe; initializes face detector/landmarker; returns boxes/count/landmarks. Uses worker-location-relative WASM/model URLs. |
| `public/workers/object-worker.js` | Isolated TF.js 4 worker. Loads YOLO, letterboxes/normalizes frames, decodes objects, disposes tensors and closes transferred bitmaps. |
| `scripts/aws-smoke.mjs` | Optional credential-supplied transport test using the current ApiClient. Does not prove camera/CORS; not executed in this delivery. |
| `scripts/browser-test.mjs` | Playwright synthetic complete-window workflow: consent, trigger, POST upload, event, playback and persisted review. |
| `scripts/check.mjs` | Syntax-checks project JavaScript, excluding large vendor/model directories. |
| `scripts/create-architecture.py` | Matplotlib source for the precise PNG architecture diagram. |
| `scripts/create-handoff-pdf.py` | Compatibility alias to the current Sprint 3 summary generator; no longer generates the superseded proposal report. |
| `scripts/create-sprint3-summary.py` | ReportLab source for the one-page evaluation/evidence table. |
| `scripts/evaluate.mjs` | Node compatibility entry point that invokes the Python summary utility. |
| `scripts/export_yolo.py` | Historical model-export helper. Default delivery uses the pinned compatible TFJS graph; verify exporter compatibility before use. |
| `scripts/import-diagnostics.py` | Converts stopped consenting real-session scalar exports into an UNREVIEWED candidate dataset. Operator must classify flags. |
| `scripts/live-ui-test.mjs` | Mock Cognito/policy browser test. Checks PKCE callback, token storage boundaries, bearer policy and consent invalidation; not real AWS. |
| `scripts/model-smoke.mjs` | Actual model loading/inference under a nested path on a blank canvas. Captures asset requests and isolation/SAB availability, not accuracy. |
| `scripts/module-test.mjs` | Nested embedding and mock-API browser checks for email, full EVENT, 409/410, single session, immediate camera stop, partial flush and failed-upload recovery. |
| `scripts/package-backend.py` | Disabled: exits with a superseded-backend notice. |
| `scripts/setup-models.mjs` | Pinned asset downloader and source/hash provenance writer; optional compatible local YOLO export. |
| `scripts/soak-test.mjs` | 20-minute synthetic buffer soak; does not test physical laptop performance or participants. |
| `scripts/summarize.py` | Reviewed-human-data summary: flags/hour, exact Poisson intervals, Wilson detection/identity intervals, calibration/held-out threshold suggestion. |
| `scripts/verify-models.mjs` | Checks every installed asset against provenance SHA-256 and byte size. |
| `server/server.mjs` | Loopback demo server with role-header simulation, POST-form upload parsing, local events/review and cleanup. Never a production backend. |
| `tests/auth.test.mjs` | Automated assertions for the named subsystem; read each test name to explain inputs, expected outcome and boundaries. |
| `tests/core.test.mjs` | Automated assertions for the named subsystem; read each test name to explain inputs, expected outcome and boundaries. |
| `tests/pglite-bridge.mjs` | Legacy superseded-backend SQL regression in PostgreSQL WASM with mocked S3. Not a live-backend acceptance test. |
| `tests/server.test.mjs` | Automated assertions for the named subsystem; read each test name to explain inputs, expected outcome and boundaries. |
| `tests/test_backend.py` | Legacy superseded-backend SQL regression in PostgreSQL WASM with mocked S3. Not a live-backend acceptance test. |
| `tests/test_evaluation.py` | Automated assertions for the named subsystem; read each test name to explain inputs, expected outcome and boundaries. |
| `third_party/MediaPipe-Apache-2.0.txt` | Upstream license or source attribution; package MIT declarations do not override YOLO model licensing. |
| `third_party/NOTICE.md` | Upstream license or source attribution; package MIT declarations do not override YOLO model licensing. |
| `third_party/TensorFlow-Apache-2.0.txt` | Upstream license or source attribution; package MIT declarations do not override YOLO model licensing. |
| `third_party/Ultralytics-AGPL-3.0.txt` | Upstream license or source attribution; package MIT declarations do not override YOLO model licensing. |
| `third_party/face-api-MIT.txt` | Upstream license or source attribution; package MIT declarations do not override YOLO model licensing. |

### November additions

- `public/core/harness.mjs`: switches standalone pages between the enrolled live exam and isolated demo UUID; does not alter the embedded API.
- `tests/live-config.test.mjs`: checks supplied settings, unchanged thresholds, demo/live exam selection and strict callback origin matching.
- `START_FAIRGRADE.cmd` / `START_FAIRGRADE.sh`: verify assets and start on port 3000.
- `evidence/live/performance.json`: unmeasured laptop worksheet; null means no observation.
- `evidence/live/trial-plan.json`: requested counts and improvement window, separate from actual statistical input.

- `scripts/localhost-config-test.mjs`: tests shipped localhost callback settings with intercepted services; never real login evidence.
- `scripts/package-delivery.py`: splits the full project into three ZIPs, excludes dependencies/private data, checks ZIP CRC and compares every archived file to source.
- `evidence/november-config/`: current local verification, separate from real-camera evidence.
