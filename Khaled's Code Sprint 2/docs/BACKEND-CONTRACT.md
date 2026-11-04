# Omar's deployed backend - authoritative client contract

Updated 31 October 2026 from Omar's contract supplied by Khaled. Omar reports that the AWS backend is deployed and tested. This delivery adapts the browser; it does not deploy or modify AWS.

**Base URL:** https://gnlnv6dd5j.execute-api.eu-north-1.amazonaws.com
No `/proctoring` or `/api` prefix. Every API request sends `Authorization: Bearer <Cognito access token>`. No cookies or CSRF. `Idempotency-Key` is allowed but ignored; eventId controls idempotency. Never send the access token to S3.

Students: Cognito Student group and enrollment in the exam course. Instructors: Instructor group and course ownership. Errors are `{"error":"message"}`. Use HTTP status: 400 invalid; 403 wrong role/not your upload; 404 not found/not enrolled; 409 conflict; 410 clip retention ended.

## GET /policy

Any signed-in user, 200:
```json
{"approved":true,"policyVersion":"fairgrade-2026-10","retentionDays":7,"metadataNotice":"Event details (time, reasons, review decision) are kept with the exam record after the clip is deleted."}
```
Consent uses this response. The integration requires the approved 7-day policy, displays metadataNotice and records consentedAt/policyVersion. It never substitutes a frontend approval setting.

## POST /clips/presign

Student body (extra fields are ignored):
```json
{"eventId":"<uuid>","examId":"<uuid>","contentType":"video/webm"}
```
Allowed types: video/webm, video/webm;codecs=vp8, video/webm;codecs=vp9. Ticket expires after five minutes. 200 response:
```json
{"uploadUrl":"https://s3.eu-north-1.amazonaws.com/fairgrade-proctoring-clips-oak","fields":{"Content-Type":"video/webm","key":"...","x-amz-algorithm":"...","x-amz-credential":"...","x-amz-date":"...","x-amz-security-token":"...","policy":"...","x-amz-signature":"..."},"objectKey":"proctoring/<examId>/<studentUserId>/<eventId>.webm","maxBytes":20971520,"expiresAt":"<ISO 8601>"}
```

## S3 form upload

POST uploadUrl as FormData. Append **every** returned fields entry exactly, then append the clip **last** under `file`. Do not set the request Content-Type; the browser must generate the multipart boundary. Do not add bearer headers, checksums or If-None-Match. Success: 204. A 403 containing `Policy expired` causes a fresh ticket and retry. The client makes at most three S3 attempts with new tickets; network/temporary failures also retry. Other 403 failures stop and remain available for explicit retry. Client checks 1 byte through 20 MiB, allowed WebM type, ticket limit and allowed storage origin.

Allowed upload and playback origin: `https://s3.eu-north-1.amazonaws.com`.

## POST /events

Student body, preserving the same UUID, object key and content type:
```json
{"eventId":"<uuid>","examId":"<uuid>","reasons":["phone"],"triggeredAt":"<ISO 8601>","objectKey":"<ticket objectKey>","contentType":"video/webm","sizeBytes":141439,"synthetic":false,"consentVersion":"fairgrade-2026-10","consentedAt":"<ISO 8601>","clip":{},"thresholds":{},"triggerMonotonicMs":0,"sustainedMs":0}
```
Reasons: non-empty, no duplicates, subset of phone, second_face, identity_mismatch, no_face. The server checks stored size/content type. Synthetic true is rejected live; the module allows synthetic signals only with explicit local demo mode. 201 created / 200 identical retry; changed payload under the same eventId is 409. Response is **`{"event": EVENT}`**; ApiClient.submit returns the unwrapped EVENT. On an event-logging retry use the same complete body, not a new trigger time or UUID.

## Instructor endpoints

- GET `/events?examId=<uuid>` -> `{"events":[EVENT,...]}`; newest first, at most 200. There is no nextCursor. The client treats absence as the end, and does not invent pagination.
- GET `/events/<eventId>/playback` -> `{"url":"<presigned S3 GET>","expiresAt":"..."}`; five-minute link; 410 after seven-day retention. UI: “Clip deleted after the 7-day retention period”.
- PATCH `/events/<eventId>/review`, body `{"decision":"confirmed"|"dismissed","version":<loaded version>}` -> **full updated EVENT**, not a wrapper. Replace card data and use its version. On 409: “Changed by another reviewer, reloading”, then reload the list.

EVENT:
```json
{"eventId":"...","studentEmail":"student_1@test.com","reasons":["phone"],"triggeredAt":"...","createdAt":"...","contentType":"video/webm","sizeBytes":141439,"clip":{},"detection":{"thresholds":{},"triggerMonotonicMs":0,"sustainedMs":0},"consentVersion":"...","expiresAt":"...","reviewed":false,"instructorDecision":null,"reviewedAt":null,"version":0,"clipExpired":false}
```
The review page displays studentEmail, uses clipExpired and shows no synthetic label in live mode.

## Superseded proposal

`backend/proctoring/handler.py`, `infra/schema.sql`, `infra/storage.tf` are the earlier proposal, retained for history only. They are **superseded** by Omar's live implementation. Do not deploy/apply them. Their legacy tests do not validate Omar's backend. Earlier PUT/checksum, /proctoring prefix, cursor, studentId and client-side policy-approval assumptions no longer apply.
