# Drop-in module for Omar's exam app

Copy the complete `public/` directory under any path on the app's HTTPS origin, for example `/exam/assets/proctor/`. Keep core, workers, vendor and models alongside proctoring-module.mjs. The module does not navigate, provide a login screen, or ask for an exam ID. Omar supplies the exam UUID, DOM container and a function returning the current Cognito access token. The standalone HTML pages are development harnesses only.

```js
import {
  renderConsent, startProctoring, stopProctoring, mountReview
} from './assets/proctor/proctoring-module.mjs';

const apiBase = 'https://gnlnv6dd5j.execute-api.eu-north-1.amazonaws.com';
const getAccessToken = async () => authSession.getAccessToken(); // host implementation
const container = document.querySelector('[data-exam-proctor]');

// Optional explicit step. startProctoring presents consent if it was not already accepted.
const consent = await renderConsent({ container, apiBase, getAccessToken });
const session = await startProctoring({
  examId, apiBase, getAccessToken, container,
  onStatus: ({ state, message }) => updateExamStatus(state, message),
  onFlag: event => showNonBlockingNotice(event.reasons),
  onError: error => showProctoringError(error.message)
});
// The rendered Capture face reference button enrolls the student. Monitoring arms
// only after enrollment and a 7.5-second pre-roll. session.enroll() is also available.

// On exam submission or leaving this page, await this BEFORE navigation:
try {
  await stopProctoring();
  // Continue the host's submission/navigation only after success.
} catch (error) {
  // Keep this view open: allow retry/download; do not discard unsent evidence.
  showProctoringError(error.message);
}
```

`renderConsent` returns `{consentedAt, policyVersion}` or rejects if declined, cancelled or policy unavailable. It fetches the approved seven-day policy. Accepted consent is scoped to that container, API base and mode, then consumed by one start. The policy is checked again before camera access. It is not stored in localStorage.

`startProctoring` returns after the camera/models are ready, not after enrollment or after the entire exam. Its controller provides `enroll()`, `stop()`, `exportDiagnostics()` and `recordIdentityTrial({alias,referenceAlias,participantConsent,split})`. The optional `trial` field captures alias/round/scenario/consent metadata for evaluation. Thresholds remain the existing defaults. Status callbacks use `{state,message}`; flag callbacks receive a copy of the event metadata, never images/embeddings. Exceptions thrown by host callbacks cannot interrupt cleanup. One session may be active per imported module.

`stopProctoring` stops camera tracks and detectors immediately. It then finishes encoding already captured evidence, waits for uploads/logging, and retries failed evidence. If stopping before the full post-trigger window, the clip is explicitly partial. Finishing can take tens of seconds. Stop is idempotent while in progress. It rejects if clips remain unsent; the retry/download controls stay available and a new session is blocked until those uploads are resolved. A page close cannot reliably flush browser memory or pending network requests. Hidden-tab interruption can also prevent reliable encoding; errors remain visible.

```js
const review = mountReview({
  container: document.querySelector('[data-proctor-review]'),
  examId, apiBase, getAccessToken
});
await review.ready; // initial list attempt completed; errors shown in its UI
await review.reload();
// When unmounting:
review.destroy();
```

Review uses email and the full returned event/version. 409 reloads; 410 shows the exact seven-day message. The backend returns at most 200 events; no fabricated pagination is offered.

## Development harness only

`index.html` and `review.html` call the same exports. Their exam-ID controls and Cognito login adapter belong to the harness, not the embeddable module. Production should use Omar's existing authentication. Optional `mode:'demo', synthetic:true` is accepted only against a same-origin demo API; never use it against the deployed endpoint. `session.setScenario()` exists solely for this explicit local test mode. Live mode is the default.

## Asset URL and hosting contract

ES module imports, CSS, worker URLs and face-api assets resolve against their own module URL. Classic workers resolve runtime/model/WASM URLs against their own worker location, which is necessary because classic-worker scripts cannot use import.meta. They do not assume the site's root.

| Extension | HTTP Content-Type |
|---|---|
| .mjs, .js | text/javascript |
| .wasm | application/wasm |
| .json | application/json |
| .task, .tflite, .bin, extensionless identity weight shards | application/octet-stream |
| .css | text/css |
| .html | text/html; charset=utf-8 |

Binary model files and JSON must not be served as JavaScript. Upload all extensionless identity shards too. Keep filenames/case unchanged. Do not map missing asset URLs to the SPA's HTML fallback. Invalidate CloudFront when replacing a release; use a versioned asset folder to avoid mixed JS/model caches. Same-origin hosting avoids worker origin restrictions. If a different CDN origin is required, validate CORS and worker loading separately; it is not the supported drop-in configuration here.

No COOP/COEP or SharedArrayBuffer is required by the shipped single-threaded model configuration. The nested-path model smoke test exercises actual files without cross-origin isolation. HTTPS is needed for getUserMedia outside localhost. Allow camera for the app's origin; no microphone is requested. If embedding inside an iframe, the host must explicitly permit camera access. A restrictive CSP must allow same-origin modules/workers/WASM plus the API and S3 origins; validate the exact policy on CloudFront rather than assuming permissive defaults. Host app CSP/permissions may still block a correctly copied module.

The module requests video only and keeps reference embeddings and rolling frames in RAM. Diagnostic exports include scalar timing, distances and aliases, not frames, embeddings or tokens. CPU % and total process memory are not portable browser APIs: collect them with the target laptop's OS tooling, and report the laptop model.
