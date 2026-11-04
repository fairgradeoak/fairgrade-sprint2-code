# Omar / Khaled Sprint 3 handoff

Omar's 31 October supplied contract has been adopted. Use public/proctoring-module.mjs inside the HTTPS exam app, with the root API base and a host-provided Cognito access-token callback. The standalone pages are only harnesses. Review docs/EMBEDDING.md for exports, lifecycle and MIME types.

Client integration is now POST-form S3 upload with every signed field plus the clip last; no checksum, If-None-Match or requiredHeaders. Event creation unwraps {event}; review replaces its complete EVENT, uses studentEmail/clipExpired, reloads on 409 and explains seven-day expiry on 410. Defaults are unchanged. Seven-day consent comes from GET /policy.

The prior Lambda/SQL/Terraform files are superseded and must not be deployed. Omar's source files are unchanged. Legacy backend tests are retained only as regression history.

Before reporting integration/evaluation complete, use the now-configured localhost harness, obtain private passwords and run the real-camera worksheet in docs/LIVE-ACCEPTANCE.md. Khaled must then perform the target-laptop session and written-consent human trials. Their measured rates and confidence intervals remain unknown. The supplied one-page table distinguishes local checks from absent field evidence.

For the design document: docs/design/proctoring-architecture.png, output/pdf/FairGrade-Sprint3-Evaluation-Summary.pdf, docs/LIMITATIONS.md. For the presentation: docs/FILE-GUIDE.md and the AI-assistance disclosure in README.md. No team sync or direct message is claimed as completed.

## 3 November configuration handoff (draft to send)

Omar, I have installed your Cognito public client and localhost:3000 callbacks, configured the enrolled exam ID, kept the seven-day policy and existing thresholds, and corrected the Windows launcher to port 3000. The delivery is split into code, vendor and models ZIPs, with integrity verification before launch. Local automated checks are reported separately from field evidence. The real-camera AWS run, target-laptop 20-minute measurements and consented participant trials still require operation on the physical laptop with the privately supplied passwords; no live success or human accuracy numbers have been invented. Remaining trials are planned within the 2-14 November improvement window, with participant dates still to be arranged.

This is a draft; no message was sent and no participant session was booked. Use docs/LIVE-ACCEPTANCE.md and evidence/live/ for the actual run.
