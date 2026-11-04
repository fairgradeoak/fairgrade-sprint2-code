# Client hosting only - use Omar's deployed backend

The previous self-deployment instructions are superseded. Do NOT deploy backend/proctoring/handler.py or apply infra/schema.sql / infra/storage.tf. Omar's API is already deployed according to the supplied contract.

Follow docs/EMBEDDING.md for copying public/ under the exam app's HTTPS origin and setting S3/CloudFront Content-Type metadata. Use the main app's Cognito access-token provider. All client live settings are in public/config.json; the API base has no prefix and retention is seven days. The standalone harness now includes Omar's supplied public Cognito domain/client and registered http://localhost:3000/ and /review.html callbacks. API CORS reportedly permits only http://localhost:3000; never use 127.0.0.1 or another port. Passwords are entered privately in Cognito. Public app hosting still requires HTTPS and separately registered callbacks/CORS.

Omar controls CORS, IAM, RDS schema and retention enforcement. Use the configured localhost origin and supplied account names, obtain passwords privately, then use docs/LIVE-ACCEPTANCE.md to collect actual browser evidence. No AWS deployment is performed by this package. npm run package:backend is disabled with a superseded notice.
