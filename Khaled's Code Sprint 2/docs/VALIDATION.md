> Phase-2 context. The current integration is documented in README.md, docs/BACKEND-CONTRACT.md and docs/SPRINT3-STATUS.md. The old backend proposal is superseded. Current evidence is in evidence/phase3/.

# Validation record - 30 October 2026

Source repository: fairgradeoak/fairgrade-sprint1-code, base commit 9575ed76a578049acf27b07ccd37bfb1ed4ea975. These are actual local execution results, not target-laptop or AWS results.

| Check | Outcome | Evidence |
|---|---|---|
| JavaScript unit/local-server tests | 20 passed | evidence/phase2/unit-test-results.txt |
| Python handler/SQL and evaluation tests | 13 passed | evidence/phase2/python-test-results.txt |
| JavaScript syntax | 27 files passed | evidence/phase2/syntax-check.txt |
| Local browser workflow | 9 checks passed | evidence/phase2/browser-report.json |
| Mocked authenticated UI | 5 checks passed | evidence/phase2/live-ui-report.json |
| Model assets | 21 SHA-256 checks passed | evidence/phase2/model-integrity.txt |
| Actual model inference | All three systems initialized and inferred on blank canvas | evidence/phase2/model-smoke.json |
| Synthetic buffer soak | 20.008 minutes, 1200 samples, no reported errors, buffer cleared | evidence/phase2/soak-report.json |

## What the checks establish

The browser generated a sustained synthetic phone trigger, selected a pre/post window, encoded WebM, uploaded to the local server, logged one event, played it back and persisted instructor confirmation. Observed source duration: 15000.0 ms; encoded elapsed: 15002.6 ms. Video decoded at 640 x 480. Consent gates the camera; changed server policy clears consent. API credentials are omitted from S3 requests. Unit tests cover retry failures, UUID validation and idempotent reuse.

Production handler SQL ran in a local PostgreSQL WASM engine (PGlite), using minimal parent tables matching Omar's UUID relationships. S3 was stubbed. Tests covered ownership/roles, upload-before-log, checksum mismatch, duplicate payload conflict, review version conflicts, transactional audit rollback, schema constraints and the installed SDK's signed conditional/checksum headers. They do not prove RDS connectivity, Gateway JWT verification, IAM or real concurrent cloud behavior.

The 20-minute wall-clock test used synthetic canvas frames and the real rolling buffer. Maximum buffered frames: 171; maximum compressed buffer: 0.580 MiB. No buffer errors were reported and stopping cleared it. Browser heap reporting was coarse/quantized and is not proof of no memory leaks. This test excludes real camera input, model inference and upload queues; the all-detector target-laptop soak remains required.

## Model performance limitation

Headless Chromium model load: 712.2 ms. Single blank-image inference latency: face 128.4 ms, identity 759.8 ms, object 9863.3 ms. This is a software/headless environment, not the target laptop. In particular the object inference is too slow for the default 1.5-second freshness tolerance. Loading success is not acceptable real-time performance; measure hardware acceleration and steady-state latency on Khaled's laptop before acceptance. No detector accuracy was measured.

## Evidence boundaries

Actual updated screenshots: consent-screen.png and review-page.png under evidence/phase2. They show local mode and synthetic footage. Human evaluation remains not_run with null rates in evaluation/phase2-summary.json. No human threshold tuning, real S3/RDS integration, deployed Terraform, retention approval or team sync is claimed. Original phase-1 evidence is retained outside phase2 and is historical.

Run instructions and exact commands are in README.md. Field acceptance and remaining tasks are in docs/TRIAL-PROTOCOL.md, docs/DEPLOYMENT.md and docs/PHASE2-STATUS.md.
