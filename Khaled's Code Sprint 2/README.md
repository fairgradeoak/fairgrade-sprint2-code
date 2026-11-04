# FairGrade proctoring - Sprint 3 / Omar contract adaptation

Updated 3 November 2026 with Omar's supplied localhost/Cognito settings. Original deadline: 1 November; improvement window: 2-14 November 2026. The browser now follows Omar's supplied deployed contract exactly: root API paths, Cognito bearer tokens, S3 multipart POST, seven-day policy, wrapped event creation and full-event review updates.

**SUPERSEDED - DO NOT DEPLOY:** `backend/proctoring/handler.py`, `infra/schema.sql`, and `infra/storage.tf` are the earlier backend proposal. Omar's deployed backend replaces them. They are retained only for history/legacy regression tests. Backend packaging is disabled. No AWS resources or teammate source files were changed.

## Use in the exam app

Copy `public/` beneath Omar's HTTPS app. Import `public/proctoring-module.mjs` and supply the exam UUID, container and access-token provider. Exports:

```js
renderConsent({container, apiBase, getAccessToken})
startProctoring({examId, apiBase, getAccessToken, container, onStatus, onFlag, onError})
stopProctoring()
mountReview({container, examId, apiBase, getAccessToken})
```

See **docs/EMBEDDING.md** for complete examples, lifecycle/flush behavior, asset paths, correct Content-Type metadata and hosting requirements. No page navigation or global element IDs are used in the module. Its current models do not require COOP/COEP or SharedArrayBuffer; actual nested-path model checks run without isolation. Main-app authentication belongs to Omar; no tokens are stored in localStorage.

Live API: https://gnlnv6dd5j.execute-api.eu-north-1.amazonaws.com

Upload/playback origin: https://s3.eu-north-1.amazonaws.com

Policy: GET /policy, approved seven-day clip retention; metadata remains with the exam record. The frontend does not deploy or enforce S3 lifecycle itself.

## Run the local harness

Install Node.js 22+, extract the ZIP, then open a terminal inside `Khaled_Code/FairGrade-Proctoring`:

```bash
npm start
```

Open http://localhost:3000. Select **Local synthetic demonstration**, click **Load policy and consent**, check consent, then **Agree and continue**. Wait for Monitoring active, select phone, and allow approximately 25 seconds for post-roll and encoding. Click **Stop and flush uploads** before leaving. Open http://localhost:3000/review.html, select Local synthetic demo and click Load review.

Models and vendor assets are provided in separate ZIPs to avoid incomplete large transfers; extract all three ZIPs into the same parent folder. Local synthetic mode uses `data/` and has no AWS connection. Live mode now has Omar's public Cognito settings and enrolled exam ID installed. Run START_FAIRGRADE.cmd and open http://localhost:3000/ exactly. See docs/LIVE-ACCEPTANCE.md for student/instructor sign-in, real-camera evidence and trials. Private passwords remain with Omar; do not put passwords or tokens in source/config files.

## Validation commands

```bash
npm ci
npx playwright install chromium
python -m pip install -r backend/proctoring/requirements.txt -r evaluation/requirements.txt
npm test
npm run check
npm run test:python
npm run test:browser
npm run test:live-ui
npm run test:module
npm run test:models
npm run verify:models
npm run evaluate
```

Tests include POST-form construction and expiry retry, 409/410 UI handling, full-event replacement, nested-path embedding, consent, singleton lifecycle, camera release and pending/failed-upload flushing. Python backend tests exercise the superseded proposal locally for regression only; they are **not** proof of Omar's deployed backend. Model smoke tests use actual assets on a blank canvas, not human accuracy trials. Current evidence is under `evidence/phase3/`; `phase2/` is historical.

## Field work not performed here

Omar reports his backend deployed/tested. This environment does not have his test-account access, HTTPS exam session, Khaled's physical webcam/laptop, or written participant consents. Therefore the real-camera AWS run, target-laptop 20-minute CPU/FPS/memory measurement and human trials remain unmeasured. No synthetic result replaces those data. See `evidence/live/status.json` and `docs/LIVE-ACCEPTANCE.md`.

Required human evaluation: at least three consenting people; five 10-minute normal sessions; phone 10 cases, second face 10, leaving frame 10, identity swap 5. Use `docs/TRIAL-PROTOCOL.md`, the in-page scalar diagnostics/identity capture, and the summary utility. Defaults are unchanged because no human data supports tuning. CPU % and laptop model require operator/OS measurements. Empty rates remain null, never fabricated zero error.

## Sprint 3 design handoff

- `docs/BACKEND-CONTRACT.md`: Omar's authoritative request/response contract.
- `docs/EMBEDDING.md`: module usage and CloudFront asset metadata.
- `docs/design/proctoring-architecture.png`: precise architecture PNG.
- `output/pdf/FairGrade-Sprint3-Evaluation-Summary.pdf`: one-page evidence/evaluation table.
- `docs/LIMITATIONS.md`: committee-ready limitations.
- `docs/FILE-GUIDE.md`: file purposes and presentation walkthrough.
- `docs/SPRINT3-STATUS.md`: task-by-task completion and external blockers.

AI assistance: this adaptation and its tests/documents were prepared with ChatGPT assistance. Khaled should review, run and explain the implementation, its test evidence and remaining limits; do not claim unperformed trials or independent authorship of AI-assisted portions.
