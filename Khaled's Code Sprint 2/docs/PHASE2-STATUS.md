> Phase-2 context. The current integration is documented in README.md, docs/BACKEND-CONTRACT.md and docs/SPRINT3-STATUS.md. The old backend proposal is superseded. Current evidence is in evidence/phase3/.

# Khaled phase 2 status — prepared 30 October 2026

Khaled owns browser proctoring: consent and webcam processing, detection/identity signals, sustained triggers, evidence capture, integration with private storage and event logging, instructor review, and evaluation. Omar owns deployment/backend coordination; Ahmed owns grading. Flags support human review and do not establish misconduct.

The dates below are the requested plan dates, **not claims that work happened on those dates**. Implementation and automated verification in this delivery occurred on 30 October. No real participants, target laptop, AWS account or team approvals were available.

| Planned day | Delivered work | Remaining evidence / owner |
|---|---|---|
| Sept 22 | Fixed model installer; bundled pinned model/runtime assets; SHA-256 verifier; real model load/inference smoke test; FPS/latency export | Khaled: target-laptop webcam/performance |
| Sept 23 | Live detector UI and trial protocol for lighting/angles/misses | Khaled: actual face/phone/person trials |
| Sept 24 | Alias-based distance capture, calibration/held-out threshold utility, FAR/FRR intervals | Khaled: at least 3 people; reference is self-captured, no liveness |
| Sept 25 | Bounded telemetry; detector lifecycle fixes; wall-clock synthetic buffer soak script/report | Khaled: 20–30 minute all-detector laptop soak and OS memory |
| Sept 26 | Participant consent/alias/scenario protocol and candidate-data importer | Team: institution-approved participant process |
| Sept 27 | Reviewed human flags/hour and CI analysis | Khaled: about 5 × 10 minute baseline trials |
| Sept 28 | Tuning log and reproducible comparison workflow | Human-data-based tuning; Omar contract discussion |
| Sept 29 | Detailed bearer/UUID/WebM/dedicated-bucket contract | Omar must agree actual contract/config |
| Sept 30 | Cognito PKCE, in-memory tokens/refresh, bearer API calls, configurable base URL and UUID IDs | Real Cognito app client and authenticated browser test |
| Oct 1 | UUID upload/event/review-audit SQL matching Omar's parent keys | Omar applies/reviews migration in target PostgreSQL |
| Oct 2 | Signed PUT, checksums, immutable upload, scoped CORS configuration | Actual private S3 and browser CORS verification |
| Oct 3 | Upload verification, unique event ID, canonical request hash and retry behavior | Real RDS row/idempotency checks |
| Oct 4 | Instructor list pagination, private playback, versioned decisions, atomic audit | Real API/Cognito/instructor ownership acceptance |
| Oct 5 | Dedicated-bucket lifecycle IaC, approval template, server policy and consent integration | Dr. Turki approves retention; Omar applies/verifies |
| Oct 6 | Local trigger→clip→upload→review browser test and optional real AWS runner | Full real-camera AWS run |
| Oct 7 | Integrated-round flag rates and confidence interval utility | Human integrated round |
| Oct 8 | Deliberate-case protocol; detection rate and interval analysis | Phone/second-face/swap/absence real cases |
| Oct 9 | Baseline/tuned/integrated comparison and threshold recommendation | Actual measured comparison; defaults remain untuned |
| Oct 10 | Auth/UUID/upload failure tests, SQL/handler tests, browser checks | Real infrastructure failure/network testing |
| Oct 11 | README, real automated results, consent/review screenshots | Human numbers and approved retention must replace pending fields |
| Oct 12 | Team handoff documentation and limitations | Actual team sync and acceptance |

No messages were sent to Omar or Ahmed. No AWS resources were changed. No GitHub commit or pull request was published. Original Omar/Ahmed source files are preserved in the ZIP.
