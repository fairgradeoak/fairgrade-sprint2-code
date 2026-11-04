> Phase-2 context. The current integration is documented in README.md, docs/BACKEND-CONTRACT.md and docs/SPRINT3-STATUS.md. The old backend proposal is superseded. Current evidence is in evidence/phase3/.

# Installed model assets and provenance

The delivery bundles 21 model/runtime files in `public/models` and `public/vendor`. `public/models/provenance.json` records source URL, exact byte length and SHA-256 of every downloaded file. `npm run verify:models` checks the bundle. Hashes detect local corruption; they are not an independent upstream authenticity audit.

| Component | Pinned source |
|---|---|
| MediaPipe Tasks Vision | npm `@mediapipe/tasks-vision@0.10.21`, CPU face worker |
| Face detector | MediaPipe BlazeFace short range float16 model version 1 |
| Face landmarks | MediaPipe Face Landmarker float16 model version 1 |
| TensorFlow.js | npm `@tensorflow/tfjs@4.22.0`, isolated YOLO worker |
| face-api.js | npm `face-api.js@0.22.2`, its own TF runtime |
| Identity weights | face-api.js repository commit `a86f011d72124e5fb93e59d5c4ab98f699dd5c9c` |
| YOLOv8n TFJS graph | Hyuto/yolov8-tfjs commit `b6a8bc691c0c1897802373d7da65dc889af1f451` |

The old face-api.js tag URL for weights returned 404. The installer now uses the pinned repository commit. YOLO downloads a pre-exported model and its four shards; a compatible local export can override it using `npm run setup:models -- --yolo-dir PATH`.

YOLO requires NHWC `[1,640,640,3]` input, center letterbox padding 114, normalization /255 and one raw COCO detection output `[1,84,N]` or `[1,N,84]`. Decoder supports class 0 person and 67 cell phone with class-aware NMS. Other output schemas fail explicitly. Face-api tiny detector/68 tiny landmarks/recognition model load locally; three reference embeddings stay only in RAM. Face/YOLO models run in separate workers; identity inference uses face-api's separate runtime on the page.

`npm run test:models` loads the actual files and executes all three systems on a blank canvas. This passed in the current headless environment. A blank canvas validates initialization, tensor compatibility and execution; it does not validate face/phone accuracy, embedding match quality, or laptop performance. Initial CPU/software YOLO inference was slow; see the exact measured values in `evidence/phase2/model-smoke.json`. Sustained trigger logic rejects stale results, so target hardware must be measured before accepting monitoring readiness.

License copies and source notices are under `third_party`. MediaPipe/TensorFlow runtime projects use Apache-2.0; face-api.js uses MIT. The pinned YOLO TFJS example repository has no standalone LICENSE file; do not infer a permissive model license from it. Ultralytics model licensing is separate from the wrapper; its current AGPL-3.0 license text is included for review. Do not assume the wrapper's MIT license makes the YOLO weights unrestricted. Upstream model-card/license terms must be reviewed by the team before distribution/deployment.

References: https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector/web_js ; https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/web_js ; https://github.com/justadudewhohacks/face-api.js ; https://github.com/Hyuto/yolov8-tfjs ; https://docs.ultralytics.com/integrations/tfjs/ .
