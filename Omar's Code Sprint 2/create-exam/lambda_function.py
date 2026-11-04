"""
FairGrade API router - public Lambda (outside the VPC).

Handles routing, input validation, role checks and Gemini grading. It has no
database credentials: every read or write goes through the private
FairGradeDB Lambda inside the VPC.

Who the caller is always comes from the verified JWT ("sub" claim), never
from the request body.
"""
import json
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone

import boto3

REGION = "eu-north-1"

# Load the Gemini API key from SSM before importing the grading module,
# because GeminiClient reads GEMINI_API_KEY at import time.
# Runs once per cold start. Skipped when the variable is already set
# (the CI smoke test sets a dummy value).
if not os.environ.get("GEMINI_API_KEY"):
    _ssm = boto3.client("ssm", region_name=REGION)
    os.environ["GEMINI_API_KEY"] = _ssm.get_parameter(
        Name="/fairgrade/gemini-api-key", WithDecryption=True
    )["Parameter"]["Value"]

from grading_api import grade_text, grade_code  # noqa: E402  (Ahmed's grader)
from fairgrade import judge0_client  # noqa: E402
from fairgrade.log_config import setup_logging  # noqa: E402

setup_logging()  # grader logs are capped in length and never contain answers or model replies
logger = logging.getLogger()
logger.setLevel(logging.INFO)

lambda_client = boto3.client("lambda", region_name=REGION)
s3_client = boto3.client("s3", region_name=REGION, endpoint_url=f"https://s3.{REGION}.amazonaws.com")
DB_FUNCTION = os.environ.get("DB_FUNCTION_NAME", "FairGradeDB")
UPLOAD_BUCKET = "fairgrade-submission-oak"
CLIP_BUCKET = os.environ.get("CLIP_BUCKET", "fairgrade-proctoring-clips-oak")
CLIP_RETENTION_DAYS = int(os.environ.get("CLIP_RETENTION_DAYS", "7"))
MAX_CLIP_BYTES = 20 * 1024 * 1024  # 20 MiB
CLIP_TYPES = {"video/webm", "video/webm;codecs=vp8", "video/webm;codecs=vp9"}
PROCTORING_REASONS = {"phone", "second_face", "identity_mismatch", "no_face"}
POLICY = {
    "approved": True,
    "policyVersion": "fairgrade-2026-10",
    "retentionDays": CLIP_RETENTION_DAYS,
    "metadataNotice": "Event details (time, reasons, review decision) are kept with the exam "
                      "record after the clip is deleted.",
}

def _run_tests_through_vpc(language_id, source_code, test_cases, deadline):
    """Replaces the grader's direct Judge0 call.

    The Judge0 server is private (inside the VPC, no public port). This Lambda is outside the VPC,
    so the test runs are relayed through FairGradeDB, the only Lambda that can reach it.
    """
    seconds = deadline.remaining()
    if seconds < 1:
        raise judge0_client.Judge0Error("no time left to run the test cases")
    resp = lambda_client.invoke(
        FunctionName=DB_FUNCTION,
        InvocationType="RequestResponse",
        Payload=json.dumps({"op": "run_tests", "params": {
            "language_id": int(getattr(language_id, "value", language_id)),
            "source_code": source_code,
            "test_cases": [list(case) for case in test_cases],
            "seconds": seconds,
        }}),
    )
    result = json.loads(resp["Payload"].read())
    if resp.get("FunctionError") or not result.get("ok"):
        raise judge0_client.Judge0Error(result.get("error") or "the Judge0 relay failed")
    return result["data"]["statuses"]


judge0_client.run_tests = _run_tests_through_vpc  # the grader calls judge0_client.run_tests(...)


HTTP_STATUS = {"not_found": 404, "forbidden": 403, "conflict": 409, "gone": 410,
               "bad_request": 400, "db_error": 500}
SUPPORTED_QUESTION_TYPES = {"short_answer", "coding"}


class ApiError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def db(op, **params):
    """Call one named operation on the private FairGradeDB Lambda."""
    resp = lambda_client.invoke(
        FunctionName=DB_FUNCTION,
        InvocationType="RequestResponse",
        Payload=json.dumps({"op": op, "params": params}),
    )
    result = json.loads(resp["Payload"].read())
    if resp.get("FunctionError"):
        raise ApiError("db_error", "Database service error")
    if not result.get("ok"):
        raise ApiError(result.get("code", "db_error"), result.get("error", "Database error"))
    return result["data"]


def respond(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


# --------------------------------------------------------------------------
# Identity and validation helpers
# --------------------------------------------------------------------------

def claims(event):
    try:
        return event["requestContext"]["authorizer"]["jwt"]["claims"]
    except KeyError:
        return {}


def caller_sub(event):
    sub = claims(event).get("sub")
    if not sub:
        raise ApiError("forbidden", "Missing identity")
    return sub


def require_group(event, group):
    groups = claims(event).get("cognito:groups", [])
    if isinstance(groups, str):
        groups = groups.strip("[]").replace('"', "").replace(" ", "").split(",")
    if group not in groups:
        raise ApiError("forbidden", f"Forbidden: {group}s only")


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def need_text(body, field, max_len):
    v = body.get(field)
    if not isinstance(v, str) or not v.strip():
        return f"'{field}' is required and must be non-empty text"
    if len(v) > max_len:
        return f"'{field}' must be at most {max_len} characters"
    return None


def need_positive_int(body, field):
    v = body.get(field)
    if not is_int(v) or v <= 0:
        return f"'{field}' is required and must be a positive whole number"
    return None


def check(errors):
    errors = [e for e in errors if e]
    if errors:
        raise ApiError("bad_request", "; ".join(errors))


RUBRIC_ID = re.compile(r"^c\d+$")


def validate_rubric(rubric):
    """Rubric: list of {id: 'c1', requirement: text, weight_fraction: 0-1}, weights summing to 1."""
    if not isinstance(rubric, list) or not rubric:
        return "'rubric' must be a non-empty list of criteria"
    seen, total = set(), 0.0
    for i, item in enumerate(rubric, 1):
        if not isinstance(item, dict):
            return f"Rubric item {i} must be an object"
        cid, req, w = item.get("id"), item.get("requirement"), item.get("weight_fraction")
        if not isinstance(cid, str) or not RUBRIC_ID.match(cid):
            return f"Rubric item {i}: 'id' must look like 'c1', 'c2', ..."
        if cid in seen:
            return f"Rubric item {i}: duplicate id '{cid}'"
        seen.add(cid)
        if not isinstance(req, str) or not req.strip():
            return f"Rubric item {i}: 'requirement' must be non-empty text"
        if not is_number(w) or not 0 < w <= 1:
            return f"Rubric item {i}: 'weight_fraction' must be greater than 0 and at most 1"
        total += w
    if abs(total - 1.0) > 0.01:
        return f"Rubric weights must add up to 1.0 (they add up to {round(total, 3)})"
    return None


def path_id(event):
    return (event.get("pathParameters") or {}).get("id")


UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def need_uuid(body, field):
    v = body.get(field)
    if not isinstance(v, str) or not UUID_RE.match(v):
        return f"'{field}' is required and must be a UUID"
    return None


def need_timestamp(body, field):
    v = body.get(field)
    try:
        datetime.fromisoformat(v.replace("Z", "+00:00"))
        return None
    except (AttributeError, ValueError):
        return f"'{field}' is required and must be an ISO 8601 timestamp"


def validate_test_cases(cases):
    """Coding tests: list of {input: text, expected_output: text, hidden: optional bool}."""
    if not isinstance(cases, list) or not 1 <= len(cases) <= 20:
        return "'test_cases' must be a list of 1 to 20 test cases"
    for i, case in enumerate(cases, 1):
        if not isinstance(case, dict):
            return f"Test case {i} must be an object"
        if not isinstance(case.get("input"), str) or not isinstance(case.get("expected_output"), str):
            return f"Test case {i}: 'input' and 'expected_output' must be text"
        if "hidden" in case and not isinstance(case["hidden"], bool):
            return f"Test case {i}: 'hidden' must be true or false"
    return None


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

def create_exam(event, body):
    require_group(event, "Instructor")
    duration = body.get("duration_minutes")
    check([
        need_text(body, "course_id", 64),
        need_text(body, "title", 255),
        need_positive_int(body, "total_points"),
        None if duration is None or (is_int(duration) and 0 < duration <= 600)
        else "'duration_minutes' must be a whole number from 1 to 600, or left out for no time limit",
    ])
    data = db("create_exam", sub=caller_sub(event), course_id=body["course_id"],
              title=body["title"].strip(), total_points=body["total_points"],
              duration_minutes=duration)
    return respond(201, {"message": "Exam created!", "exam_id": data["exam_id"]})


def create_question(event, body):
    require_group(event, "Instructor")
    question_type = body.get("question_type", "short_answer")
    if question_type not in SUPPORTED_QUESTION_TYPES:
        raise ApiError("bad_request",
                       f"'question_type' must be one of: {', '.join(sorted(SUPPORTED_QUESTION_TYPES))}")
    errors = [
        need_text(body, "exam_id", 64),
        need_text(body, "question_text", 5000),
        need_positive_int(body, "points"),
        need_text(body, "model_answer", 20000),  # for coding: the reference solution
    ]
    if question_type == "coding":
        # The grader scores code against the rubric, using the test results as evidence.
        errors += [
            need_positive_int(body, "language_id"),  # Judge0 language ID, e.g. 71 = Python 3
            validate_test_cases(body.get("test_cases")),
            None if isinstance(body.get("starter_code", ""), str) else "'starter_code' must be text",
        ]
    errors.append(validate_rubric(body.get("rubric")))
    check(errors)
    data = db("create_question", sub=caller_sub(event), exam_id=body["exam_id"],
              question_text=body["question_text"].strip(), points=body["points"],
              question_type=question_type, model_answer=body["model_answer"].strip(),
              rubric=body.get("rubric"), language_id=body.get("language_id"),
              starter_code=body.get("starter_code"), test_cases=body.get("test_cases"))
    return respond(201, {"message": "Question created!", "question_id": data["question_id"]})


def submit_answer(event, body):
    require_group(event, "Student")
    check([
        need_text(body, "exam_id", 64),
        need_text(body, "question_id", 64),
        need_text(body, "answer_text", 20000),
    ])

    # 1. Save the answer and load the grading context.
    #    The student is identified from the JWT; any student_id in the body is ignored.
    ctx = db("start_submission", sub=caller_sub(event), exam_id=body["exam_id"],
             question_id=body["question_id"], answer_text=body["answer_text"])
    submission_id = ctx["submission_id"]
    q = ctx["question"]

    # 2. Grade with Ahmed's grader. It never raises: every outcome comes back as a result with a status.
    question = {
        "subject_name": q["subject_name"] or "General",
        "subject_description": q["subject_description"] or "",
        "question_text": q["question_text"],
        "question_type": q["question_type"],
        "model_answer": q["model_answer"] or "",
        "max_points": q["max_points"],
        "rubric": q["rubric"] or [],
        "language_id": q.get("language_id"),
        "test_cases": q.get("test_cases") or [],
    }
    grade_fn = grade_code if q["question_type"] == "coding" else grade_text
    result = grade_fn(question, body["answer_text"])
    status = result.get("status")

    instructor_feedback = result.get("instructor_feedback") or ""
    if result.get("review_reasons"):
        instructor_feedback += "\n\nReview reasons: " + "; ".join(str(r) for r in result["review_reasons"])

    if status == "graded":
        grade = {
            "score": result["grade"],
            "confidence": result.get("confidence"),
            "needs_review": bool(result.get("needs_review")),
            "criteria_breakdown": result.get("rubric_breakdown") or [],
            "instructor_feedback": instructor_feedback,
            "student_feedback": result.get("student_feedback") or "",
        }
        message = "Answer submitted and graded successfully!"
    elif status == "injection_flagged":
        # Not graded: the instructor decides the score from the review queue.
        grade = {
            "score": None,
            "confidence": None,
            "needs_review": True,
            "criteria_breakdown": [],
            "instructor_feedback": instructor_feedback or "Flagged as a possible prompt injection.",
            "student_feedback": "Your answer was sent to your instructor for review.",
        }
        message = "Answer submitted. It will be reviewed by your instructor."
    else:
        # A temporary failure (model or code runner): the student can simply submit again.
        logger.error("Grading failed: attempts=%s", result.get("attempts"))
        db("fail_submission", submission_id=submission_id)
        return respond(502, {"error": "Grading failed. Please submit again."})

    # 3. Save the grade and mark the submission 'completed'.
    db("save_grade", submission_id=submission_id, **grade)
    return respond(201, {
        "message": message,
        "submission_id": submission_id,
        "status": "graded" if status == "graded" else "under_review",
    })


def get_grade(event, body):
    # Students see only their own grade and student feedback;
    # instructors see everything for their own courses.
    return respond(200, db("get_grade", sub=caller_sub(event), submission_id=path_id(event)))


SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]")


def get_upload_url(event, body):
    file_name = (event.get("queryStringParameters") or {}).get("file_name")
    if not file_name:
        raise ApiError("bad_request", "Missing file_name in query parameters")
    # The server chooses the key: a per-user folder plus a random prefix, so
    # nobody can overwrite or guess someone else's file.
    safe = SAFE_NAME.sub("_", os.path.basename(file_name))[:100] or "file"
    key = f"uploads/{caller_sub(event)}/{uuid.uuid4()}-{safe}"
    url = s3_client.generate_presigned_url(
        "put_object",
        Params={"Bucket": UPLOAD_BUCKET, "Key": key},
        ExpiresIn=900,
    )
    return respond(200, {"upload_url": url, "key": key})


def get_exam(event, body):
    return respond(200, db("get_exam", sub=caller_sub(event), exam_id=path_id(event)))


def get_exam_questions(event, body):
    questions = db("get_exam_questions", sub=caller_sub(event), exam_id=path_id(event))
    return respond(200, {"questions": questions})


def start_exam(event, body):
    require_group(event, "Student")
    attempt = db("start_exam", sub=caller_sub(event), exam_id=path_id(event))
    return respond(200, {"message": "Exam started", "attempt": attempt})


def finalize_exam(event, body):
    require_group(event, "Student")
    attempt = db("finalize_exam", sub=caller_sub(event), exam_id=path_id(event))
    return respond(200, {"message": "Exam finalized successfully", "attempt": attempt})


def my_submissions(event, body):
    require_group(event, "Student")
    rows = db("list_my_submissions", sub=caller_sub(event), exam_id=path_id(event))
    return respond(200, {"submissions": rows})


def exam_submissions(event, body):
    require_group(event, "Instructor")
    rows = db("list_exam_submissions", sub=caller_sub(event), exam_id=path_id(event))
    return respond(200, {"submissions": rows})


# --------------------------------------------------------------------------
# Users, courses and enrollment
# --------------------------------------------------------------------------

def get_me(event, body):
    return respond(200, db("get_me", sub=caller_sub(event)))


def get_policy(event, body):
    return respond(200, POLICY)


def list_courses(event, body):
    return respond(200, {"courses": db("list_courses", sub=caller_sub(event))})


def create_course(event, body):
    require_group(event, "Instructor")
    check([need_text(body, "course_code", 50), need_text(body, "course_name", 255)])
    data = db("create_course", sub=caller_sub(event), course_code=body["course_code"].strip(),
              course_name=body["course_name"].strip())
    return respond(201, {"message": "Course created!", "course_id": data["course_id"]})


def course_exams(event, body):
    return respond(200, {"exams": db("list_course_exams", sub=caller_sub(event), course_id=path_id(event))})


def course_enrollments(event, body):
    require_group(event, "Instructor")
    rows = db("list_enrollments", sub=caller_sub(event), course_id=path_id(event))
    return respond(200, {"students": rows})


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def enroll_student(event, body):
    require_group(event, "Instructor")
    email = body.get("email")
    if not isinstance(email, str) or not EMAIL_RE.match(email.strip()) or len(email) > 255:
        raise ApiError("bad_request", "'email' is required and must be a valid email address")
    data = db("enroll_student", sub=caller_sub(event), course_id=path_id(event), email=email.strip())
    return respond(201 if data["enrolled"] else 200,
                   {"message": "Student enrolled" if data["enrolled"] else "Student was already enrolled",
                    "email": data["email"]})


def get_reviews(event, body):
    require_group(event, "Instructor")
    return respond(200, {"reviews": db("get_review_queue", sub=caller_sub(event))})


def submit_review(event, body):
    require_group(event, "Instructor")
    errors = []
    if not is_int(body.get("grade_id")):
        errors.append("'grade_id' is required and must be a whole number")
    if not is_number(body.get("score")):
        errors.append("'score' is required and must be a number")
    for field in ("instructor_feedback", "student_feedback"):
        if field in body and not isinstance(body[field], str):
            errors.append(f"'{field}' must be text")
    check(errors)
    data = db("submit_review", sub=caller_sub(event), grade_id=body["grade_id"],
              score=body["score"], instructor_feedback=body.get("instructor_feedback"),
              student_feedback=body.get("student_feedback"))
    return respond(200, {"message": "Review submitted successfully!", **data})


# --------------------------------------------------------------------------
# Proctoring (Khaled's contract: presign -> upload -> event -> list/playback/review)
# --------------------------------------------------------------------------

def clip_upload_ticket(event, body):
    require_group(event, "Student")
    check([
        need_uuid(body, "eventId"),
        need_uuid(body, "examId"),
        None if body.get("contentType") in CLIP_TYPES
        else f"'contentType' must be one of: {', '.join(sorted(CLIP_TYPES))}",
    ])
    key = db("proctoring_upload_key", sub=caller_sub(event), exam_id=body["examId"],
             event_id=body["eventId"])["object_key"]
    # A presigned POST lets S3 itself reject files that are too large or the wrong type.
    post = s3_client.generate_presigned_post(
        Bucket=CLIP_BUCKET,
        Key=key,
        Fields={"Content-Type": body["contentType"]},
        Conditions=[
            {"Content-Type": body["contentType"]},
            ["content-length-range", 1, MAX_CLIP_BYTES],
        ],
        ExpiresIn=300,
    )
    expires = datetime.now(timezone.utc) + timedelta(seconds=300)
    return respond(200, {
        "uploadUrl": post["url"],
        "fields": post["fields"],
        "objectKey": key,
        "maxBytes": MAX_CLIP_BYTES,
        "expiresAt": expires.isoformat(timespec="seconds").replace("+00:00", "Z"),
    })


def create_proctoring_event(event, body):
    require_group(event, "Student")
    reasons = body.get("reasons")
    errors = [
        need_uuid(body, "eventId"),
        need_uuid(body, "examId"),
        need_text(body, "objectKey", 300),
        need_text(body, "consentVersion", 100),
        need_timestamp(body, "triggeredAt"),
        need_timestamp(body, "consentedAt"),
        None if isinstance(reasons, list) and reasons and len(set(reasons)) == len(reasons)
        and set(reasons) <= PROCTORING_REASONS
        else f"'reasons' must be a non-empty list from: {', '.join(sorted(PROCTORING_REASONS))}",
        None if body.get("contentType") in CLIP_TYPES else "'contentType' is not a supported video type",
        None if is_int(body.get("sizeBytes")) and 0 < body["sizeBytes"] <= MAX_CLIP_BYTES
        else f"'sizeBytes' must be between 1 and {MAX_CLIP_BYTES}",
        "Synthetic test clips are not accepted" if body.get("synthetic") is True else None,
    ]
    check(errors)

    # Verify the upload really exists and matches what the client claims.
    try:
        head = s3_client.head_object(Bucket=CLIP_BUCKET, Key=body["objectKey"])
    except Exception:
        raise ApiError("bad_request", "Upload not found. Upload the clip before creating the event")
    if head.get("ContentLength") != body["sizeBytes"] or head.get("ContentType") != body["contentType"]:
        raise ApiError("bad_request", "The uploaded clip does not match the event details")

    # Client timing and detector details are stored as evidence metadata, not trusted facts.
    metadata = {k: body[k] for k in ("clip", "thresholds", "triggerMonotonicMs", "sustainedMs")
                if k in body}
    if len(json.dumps(metadata)) > 8000:
        raise ApiError("bad_request", "Clip metadata is too large")

    data = db("create_proctoring_event", sub=caller_sub(event), event_id=body["eventId"],
              exam_id=body["examId"], reasons=reasons, triggered_at=body["triggeredAt"],
              object_key=body["objectKey"], content_type=body["contentType"],
              size_bytes=body["sizeBytes"], clip_metadata=metadata,
              consent_version=body["consentVersion"], consented_at=body["consentedAt"],
              retention_days=CLIP_RETENTION_DAYS)
    return respond(201 if data["created"] else 200, {"event": data["event"]})


def list_proctoring_events(event, body):
    require_group(event, "Instructor")
    exam_id = (event.get("queryStringParameters") or {}).get("examId")
    if not exam_id:
        raise ApiError("bad_request", "Missing examId in query parameters")
    return respond(200, {"events": db("list_proctoring_events", sub=caller_sub(event), exam_id=exam_id)})


def proctoring_playback(event, body):
    require_group(event, "Instructor")
    key = db("get_proctoring_clip", sub=caller_sub(event), event_id=path_id(event))["object_key"]
    url = s3_client.generate_presigned_url(
        "get_object", Params={"Bucket": CLIP_BUCKET, "Key": key}, ExpiresIn=300
    )
    expires = datetime.now(timezone.utc) + timedelta(seconds=300)
    return respond(200, {"url": url, "expiresAt": expires.isoformat(timespec="seconds").replace("+00:00", "Z")})


def review_proctoring_event(event, body):
    require_group(event, "Instructor")
    check([
        None if body.get("decision") in ("confirmed", "dismissed")
        else "'decision' must be 'confirmed' or 'dismissed'",
        None if is_int(body.get("version")) and body["version"] >= 0
        else "'version' is required and must be the version you loaded",
    ])
    data = db("review_proctoring_event", sub=caller_sub(event), event_id=path_id(event),
              decision=body["decision"], version=body["version"])
    return respond(200, data)


ROUTES = {
    "POST /exams": create_exam,
    "POST /questions": create_question,
    "POST /submissions": submit_answer,
    "GET /grades/{id}": get_grade,
    "GET /upload-url": get_upload_url,
    "GET /exams/{id}": get_exam,
    "GET /exams/{id}/questions": get_exam_questions,
    "POST /exams/{id}/submit": finalize_exam,
    "POST /exams/{id}/start": start_exam,
    "GET /exams/{id}/my-submissions": my_submissions,
    "GET /exams/{id}/submissions": exam_submissions,
    "GET /me": get_me,
    "GET /policy": get_policy,
    "GET /courses": list_courses,
    "POST /courses": create_course,
    "GET /courses/{id}/exams": course_exams,
    "GET /courses/{id}/enrollments": course_enrollments,
    "POST /courses/{id}/enrollments": enroll_student,
    "GET /reviews": get_reviews,
    "POST /reviews": submit_review,
    "POST /clips/presign": clip_upload_ticket,
    "POST /events": create_proctoring_event,
    "GET /events": list_proctoring_events,
    "GET /events/{id}/playback": proctoring_playback,
    "PATCH /events/{id}/review": review_proctoring_event,
}


def lambda_handler(event, context):
    route_key = event.get("routeKey", "")
    request_id = (event.get("requestContext") or {}).get("requestId")
    # Log only the route and request ID, never the body, token or answers.
    logger.info("route=%s request_id=%s", route_key, request_id)

    handler = ROUTES.get(route_key)
    if handler is None:
        return respond(404, {"error": "Route not found"})

    try:
        body = json.loads(event["body"]) if event.get("body") else {}
        if not isinstance(body, dict):
            raise ValueError
    except ValueError:
        return respond(400, {"error": "Invalid JSON format"})

    try:
        return handler(event, body)
    except ApiError as e:
        return respond(HTTP_STATUS.get(e.code, 500), {"error": e.message})
    except Exception as e:
        logger.error("route=%s unhandled error: %s", route_key, type(e).__name__)
        return respond(500, {"error": "Internal server error"})