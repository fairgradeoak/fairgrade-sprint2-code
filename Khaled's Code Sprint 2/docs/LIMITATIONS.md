# Known limitations for Sprint 3

- The reference is self-captured; no liveness check or proof of institutional identity.
- The tab must stay visible. Hidden tabs can interrupt detection and correctly timed encoding.
- Closing the page can lose buffered frames and unsent clips; await stopProctoring before host navigation. Flush can fail and must be handled.
- YOLOv8n is AGPL-3.0 licensed; the example wrapper's MIT declaration does not replace model licensing obligations.
- Flags support human review and do not prove misconduct or justify automatic penalties.
- Second-person boxes are displayed, but the additional-person trigger is based on a second detectable face. Occluded/body-only intrusions may be missed.
- Only supported WebM MediaRecorder browsers are accepted. Target-laptop performance remains unmeasured; software/headless YOLO inference was too slow for the freshness threshold.
- Reference matching, phone/face counts and false-positive rates require real participant trials. None were performed in this environment.
- Queues are bounded; overload and failed encoding are surfaced. A stopped session may produce a partial post-trigger window, clearly marked in the event.
- Review list is newest first and limited to 200 events by Omar's API. No pagination contract exists.
- Seven-day clip retention does not delete metadata; event details/review decisions remain with the exam record according to GET /policy.
