# November 3 rerun

After installing Omar's public Cognito settings and adding live/demo exam selection, 25 JavaScript tests, 13 Python tests (5 evaluation plus 8 superseded-backend regressions), and 31 browser checks passed. The four new browser checks use the shipped config at localhost:3000 with intercepted Cognito/API responses; they are not a real account login or AWS test. Model/vendor SHA-256 verification passed for all 21 assets. Thresholds and the embedded detection module were not edited. The physical camera, target laptop and participant trials remain unmeasured; current worksheets are in evidence/live/.

Source configuration checks are in tests/live-config.test.mjs; browser flow checks are in scripts/localhost-config-test.mjs. Run npm run test:localhost with port 3000 free. The suite does not send live API writes. Current verification is recorded in evidence/november-config/verification-summary.json.

## Historical October verification

# Executed validation - 31 October 2026

22 JavaScript client/demo tests passed. 5 Python statistics tests passed. 8 Python regression tests for the superseded proposal passed; these do not validate Omar's live service.

27 browser checks passed: 9 local complete-window workflow, 5 mocked authentication/policy checks, 13 embedded-module checks. These cover nested paths, 409/410 messages, full EVENT replacement, immediate camera stop, partial-clip flush, failed-upload retention and recovery. Mock endpoints and synthetic camera/detector inputs are identified in each report.

Actual model files loaded under /exam/assets/proctor/ and inferred on a blank canvas. 25 relative asset requests; crossOriginIsolated=False; SharedArrayBuffer available=False. Initial latency: face 118.5 ms; identity 788.9 ms; YOLO 8964.0 ms. Slow headless/software YOLO is NOT target-laptop readiness evidence. Hardware acceleration and steady-state latency must be measured on the actual laptop.

Current reports/screenshots: evidence/phase3/. Previous phase2 evidence and the synthetic-only 20-minute soak are historical, not human or AWS evidence. The one-page PDF, architecture diagram and screenshots were visually checked.

Omar reports AWS deployed/tested, but no real-camera authenticated AWS run or human evaluation was performed here. No threshold changes were made. Superseded backend files and thresholds were compared against the prior ZIP; teammate files were compared against the supplied repository commit.
