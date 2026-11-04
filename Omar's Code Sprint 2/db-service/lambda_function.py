"""
FairGradeDB - private data service (runs inside the VPC).

It has no API Gateway route. Only Lambdas that are granted
lambda:InvokeFunction on it can call it, and they can only ask for one of
the named operations below. It never runs SQL supplied by the caller.

Every user-facing operation receives the caller's Cognito "sub" (taken by
the router from the verified JWT) and resolves the user here, so a caller
can never act as someone else by changing an ID in the request body.

Request:  {"op": "<operation>", "params": {...}}
Response: {"ok": true, "data": ...}
       or {"ok": false, "code": "not_found|forbidden|conflict|gone|bad_request|db_error", "error": "..."}
"""
import datetime
import decimal
import json
import logging
import os
import ssl
import uuid

import pg8000.dbapi
from fairgrade import judge0_client  # Ahmed's Judge0 client, used by the run_tests relay
from fairgrade.time_budget import Deadline

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Verify that the server really is our RDS instance (Amazon RDS CA bundle).
SSL_CONTEXT = ssl.create_default_context(
    cafile=os.path.join(os.path.dirname(os.path.abspath(__file__)), "global-bundle.pem")
)


class OpError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def _connect():
    return pg8000.dbapi.connect(
        host=os.environ["DB_HOST"],
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        ssl_context=SSL_CONTEXT,
        timeout=10,
    )


def _json_default(value):
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (uuid.UUID, datetime.datetime, datetime.date)):
        return str(value)
    raise TypeError(f"Cannot serialise {type(value).__name__}")


def _jsonable(data):
    # Decimal -> float, UUID/datetime -> str, so the result survives the Lambda response.
    return json.loads(json.dumps(data, default=_json_default))


# --------------------------------------------------------------------------
# Identity and access helpers
# --------------------------------------------------------------------------

def _me(cur, p, role=None):
    """Return the caller's users.id from their Cognito sub, optionally requiring a role."""
    cur.execute("SELECT id, role FROM users WHERE cognito_sub = %s;", (p["sub"],))
    row = cur.fetchone()
    if not row:
        raise OpError("forbidden", "User profile not found")
    if role and row[1] != role:
        raise OpError("forbidden", "Not allowed for your role")
    return row[0]


def _me_with_role(cur, p):
    cur.execute("SELECT id, role FROM users WHERE cognito_sub = %s;", (p["sub"],))
    row = cur.fetchone()
    if not row:
        raise OpError("forbidden", "User profile not found")
    return row[0], row[1]


def _is_exam_owner(cur, user_id, exam_id):
    cur.execute(
        """SELECT 1 FROM exams e JOIN courses c ON c.id = e.course_id
           WHERE e.id = %s AND c.instructor_id = %s;""",
        (exam_id, user_id),
    )
    return cur.fetchone() is not None


def _require_course_access(cur, user_id, course_id, owner_only=False):
    """Instructor must own the course; students (unless owner_only) must be enrolled."""
    cur.execute(
        """SELECT c.instructor_id = %s
           FROM courses c
           WHERE c.id = %s
             AND (c.instructor_id = %s
                  OR (NOT %s AND EXISTS (SELECT 1 FROM enrollments en
                                         WHERE en.course_id = c.id AND en.student_id = %s)));""",
        (user_id, course_id, user_id, owner_only, user_id),
    )
    row = cur.fetchone()
    if not row:
        raise OpError("not_found", "Course not found")
    return row[0]


def _attempt(cur, student_id, exam_id):
    """The student's attempt for this exam with its deadline, or None."""
    cur.execute(
        """SELECT a.status, a.started_at, a.completed_at, e.duration_minutes,
                  a.started_at + make_interval(mins => e.duration_minutes) AS deadline_at,
                  (e.duration_minutes IS NOT NULL AND CURRENT_TIMESTAMP >
                   a.started_at + make_interval(mins => e.duration_minutes + 2)) AS time_up
           FROM exam_attempts a JOIN exams e ON e.id = a.exam_id
           WHERE a.exam_id = %s AND a.student_id = %s;""",
        (exam_id, student_id),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {"status": row[0], "startedAt": row[1], "completedAt": row[2],
            "durationMinutes": row[3], "deadlineAt": row[4], "timeUp": row[5]}


def _require_exam_access(cur, user_id, exam_id):
    """The caller must own the exam's course (instructor) or be enrolled in it (student)."""
    cur.execute(
        """SELECT 1
           FROM exams e
           JOIN courses c ON c.id = e.course_id
           WHERE e.id = %s
             AND (c.instructor_id = %s
                  OR EXISTS (SELECT 1 FROM enrollments en
                             WHERE en.course_id = c.id AND en.student_id = %s));""",
        (exam_id, user_id, user_id),
    )
    if not cur.fetchone():
        # Same message whether it doesn't exist or isn't theirs, so nothing leaks.
        raise OpError("not_found", "Exam not found")


# --------------------------------------------------------------------------
# Exams and questions
# --------------------------------------------------------------------------

def op_get_exam(cur, p):
    me, role = _me_with_role(cur, p)
    _require_exam_access(cur, me, p["exam_id"])
    cur.execute(
        """SELECT e.id, e.title, e.total_points, e.duration_minutes, c.id, c.course_code, c.course_name,
                  (SELECT COUNT(*) FROM questions q WHERE q.exam_id = e.id)
           FROM exams e JOIN courses c ON c.id = e.course_id
           WHERE e.id = %s;""",
        (p["exam_id"],),
    )
    row = cur.fetchone()
    exam = {"id": row[0], "title": row[1], "total_points": row[2], "duration_minutes": row[3],
            "course_id": row[4], "course_code": row[5], "course_name": row[6], "question_count": row[7]}
    if role == "student":
        exam["attempt"] = _attempt(cur, me, p["exam_id"])
    return exam


def op_get_exam_questions(cur, p):
    me, role = _me_with_role(cur, p)
    _require_exam_access(cur, me, p["exam_id"])
    owner = role == "instructor" and _is_exam_owner(cur, me, p["exam_id"])
    if not owner and _attempt(cur, me, p["exam_id"]) is None:
        # Students see the questions only after starting the exam.
        raise OpError("conflict", "Start the exam to see its questions")
    cur.execute(
        """SELECT id, question_text, points, question_type, language_id, starter_code,
                  model_answer, rubric, test_cases
           FROM questions WHERE exam_id = %s ORDER BY created_at;""",
        (p["exam_id"],),
    )
    questions = []
    for r in cur.fetchall():
        q = {"question_id": r[0], "question_text": r[1], "points": r[2], "question_type": r[3]}
        if r[3] == "coding":
            q["language_id"] = r[4]
            q["starter_code"] = r[5] or ""
        if owner:
            # Instructor view: everything needed to check and edit the question.
            q["model_answer"] = r[6]
            q["rubric"] = r[7]
            q["test_cases"] = r[8]
        questions.append(q)
    return questions


def op_create_exam(cur, p):
    me = _me(cur, p, "instructor")
    cur.execute(
        """INSERT INTO exams (course_id, title, total_points, duration_minutes)
           SELECT c.id, %s, %s, %s FROM courses c
           WHERE c.id = %s AND c.instructor_id = %s
           RETURNING id;""",
        (p["title"], p["total_points"], p.get("duration_minutes"), p["course_id"], me),
    )
    row = cur.fetchone()
    if not row:
        raise OpError("not_found", "Course not found")
    return {"exam_id": row[0]}


def op_create_question(cur, p):
    me = _me(cur, p, "instructor")
    cur.execute(
        """INSERT INTO questions (exam_id, question_text, points, question_type, model_answer,
                                  rubric, language_id, starter_code, test_cases)
           SELECT e.id, %s, %s, %s, %s, %s::jsonb, %s, %s, %s::jsonb
           FROM exams e JOIN courses c ON c.id = e.course_id
           WHERE e.id = %s AND c.instructor_id = %s
           RETURNING id;""",
        (
            p["question_text"],
            p["points"],
            p["question_type"],
            p["model_answer"],
            json.dumps(p["rubric"]) if p.get("rubric") is not None else None,
            p.get("language_id"),
            p.get("starter_code"),
            json.dumps(p["test_cases"]) if p.get("test_cases") is not None else None,
            p["exam_id"],
            me,
        ),
    )
    row = cur.fetchone()
    if not row:
        raise OpError("not_found", "Exam not found")
    return {"question_id": row[0]}


# --------------------------------------------------------------------------
# Submissions and grading
# --------------------------------------------------------------------------

def op_start_submission(cur, p):
    me = _me(cur, p, "student")
    _require_exam_access(cur, me, p["exam_id"])
    attempt = _attempt(cur, me, p["exam_id"])
    if attempt is None:
        raise OpError("conflict", "Start the exam before answering")
    if attempt["status"] == "completed":
        raise OpError("conflict", "This exam has already been submitted")
    if attempt["timeUp"]:
        raise OpError("conflict", "Time is up for this exam")

    # 1. Load the grading context, checking the question belongs to the exam.
    cur.execute(
        """SELECT c.course_name, c.course_code, q.question_text, q.question_type,
                  q.model_answer, q.points, q.rubric, q.language_id, q.test_cases
           FROM questions q
           JOIN exams e   ON q.exam_id = e.id
           JOIN courses c ON e.course_id = c.id
           WHERE q.id = %s AND q.exam_id = %s;""",
        (p["question_id"], p["exam_id"]),
    )
    q = cur.fetchone()
    if not q:
        raise OpError("not_found", "Question not found in this exam")

    question_type = q[3]
    rubric = q[6]
    if isinstance(rubric, str):
        rubric = json.loads(rubric)
    if question_type != "coding" and not rubric:
        # Grading without a rubric always scores 0, so refuse instead.
        raise OpError("bad_request", "This question has no rubric and cannot be graded yet")

    # 2. Save the answer. Short answers are graded right away ('grading');
    #    coding answers wait for the code runner ('pending'). A pending or
    #    failed submission may be replaced; a completed one may not.
    status = "pending" if question_type == "coding" else "grading"
    cur.execute(
        """INSERT INTO submissions (student_id, exam_id, question_id, answer_text, status)
           VALUES (%s, %s, %s, %s, %s)
           ON CONFLICT (exam_id, student_id, question_id)
           DO UPDATE SET answer_text = EXCLUDED.answer_text,
                         status = EXCLUDED.status,
                         created_at = CURRENT_TIMESTAMP
           WHERE submissions.status IN ('pending', 'failed')
           RETURNING id;""",
        (me, p["exam_id"], p["question_id"], p["answer_text"], status),
    )
    row = cur.fetchone()
    if not row:
        raise OpError("conflict", "This question has already been answered")

    return {
        "submission_id": row[0],
        "question": {
            "subject_name": q[0],
            "subject_description": q[1],
            "question_text": q[2],
            "question_type": q[3],
            "model_answer": q[4],
            "max_points": q[5],
            "rubric": rubric,
            "language_id": q[7],
            "test_cases": q[8],
        },
    }


def op_save_grade(cur, p):
    # Internal: called by the router right after start_submission.
    cur.execute(
        """INSERT INTO grades (submission_id, score, criteria_breakdown, confidence,
                               needs_review, instructor_feedback, student_feedback)
           VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s)
           ON CONFLICT (submission_id) DO UPDATE SET
               score = EXCLUDED.score,
               criteria_breakdown = EXCLUDED.criteria_breakdown,
               confidence = EXCLUDED.confidence,
               needs_review = EXCLUDED.needs_review,
               instructor_feedback = EXCLUDED.instructor_feedback,
               student_feedback = EXCLUDED.student_feedback,
               reviewed_by = NULL,
               reviewed_at = NULL,
               created_at = CURRENT_TIMESTAMP;""",
        (
            p["submission_id"],
            p["score"],
            json.dumps(p.get("criteria_breakdown", [])),
            p["confidence"],
            p["needs_review"],
            p.get("instructor_feedback", ""),
            p.get("student_feedback", ""),
        ),
    )
    # Keep the AI's original score, and mark the submission as done.
    cur.execute(
        "UPDATE submissions SET status = 'completed', ai_score = %s WHERE id = %s;",
        (p["score"], p["submission_id"]),
    )
    return {"submission_id": p["submission_id"]}


def op_fail_submission(cur, p):
    # Internal: called by the router when grading fails.
    cur.execute("UPDATE submissions SET status = 'failed' WHERE id = %s;", (p["submission_id"],))
    return {"submission_id": p["submission_id"]}


def op_get_grade(cur, p):
    me = _me(cur, p)
    cur.execute(
        """SELECT s.student_id, c.instructor_id, s.status,
                  g.score, g.student_feedback, g.instructor_feedback,
                  g.criteria_breakdown, g.confidence, g.needs_review, s.ai_score,
                  g.reviewed_at, g.id
           FROM submissions s
           JOIN exams e   ON e.id = s.exam_id
           JOIN courses c ON c.id = e.course_id
           LEFT JOIN grades g ON g.submission_id = s.id
           WHERE s.id = %s;""",
        (p["submission_id"],),
    )
    row = cur.fetchone()
    # Only the student who submitted it, or the course's instructor, may see it.
    if not row or me not in (row[0], row[1]):
        raise OpError("not_found", "Grade not found")
    if row[11] is None:
        raise OpError("not_found", f"Grade not available (submission is {row[2]})")
    status = "under_review" if row[3] is None else row[2]  # no score yet: waiting for the instructor

    if me == row[0]:
        # Student view: only what is meant for the student.
        return {
            "submission_id": p["submission_id"],
            "status": status,
            "score": row[3],
            "feedback": row[4],
        }
    # Instructor view: everything.
    return {
        "submission_id": p["submission_id"],
        "status": status,
        "score": row[3],
        "ai_score": row[9],
        "student_feedback": row[4],
        "instructor_feedback": row[5],
        "criteria_breakdown": row[6],
        "confidence": row[7],
        "needs_review": row[8],
        "reviewed_at": row[10],
    }


def op_start_exam(cur, p):
    me = _me(cur, p, "student")
    _require_exam_access(cur, me, p["exam_id"])
    cur.execute(
        """INSERT INTO exam_attempts (exam_id, student_id, status)
           VALUES (%s, %s, 'in_progress')
           ON CONFLICT (exam_id, student_id) DO NOTHING;""",
        (p["exam_id"], me),
    )
    attempt = _attempt(cur, me, p["exam_id"])
    if attempt["status"] == "completed":
        raise OpError("conflict", "This exam has already been submitted")
    return attempt  # starting again just returns the same attempt (same start time)


def op_finalize_exam(cur, p):
    me = _me(cur, p, "student")
    _require_exam_access(cur, me, p["exam_id"])
    cur.execute(
        """UPDATE exam_attempts SET status = 'completed', completed_at = CURRENT_TIMESTAMP
           WHERE exam_id = %s AND student_id = %s AND status = 'in_progress';""",
        (p["exam_id"], me),
    )
    attempt = _attempt(cur, me, p["exam_id"])
    if attempt is None:
        raise OpError("conflict", "Start the exam first")
    return attempt  # finishing twice is harmless: it stays completed


def op_list_my_submissions(cur, p):
    me = _me(cur, p, "student")
    _require_exam_access(cur, me, p["exam_id"])
    cur.execute(
        """SELECT s.id, s.question_id, q.question_type, q.points, s.status, s.created_at,
                  g.score, g.student_feedback
           FROM submissions s
           JOIN questions q ON q.id = s.question_id
           LEFT JOIN grades g ON g.submission_id = s.id
           WHERE s.exam_id = %s AND s.student_id = %s
           ORDER BY q.created_at;""",
        (p["exam_id"], me),
    )
    keys = ["submission_id", "question_id", "question_type", "max_points", "status",
            "submitted_at", "score", "feedback"]
    return [dict(zip(keys, r)) for r in cur.fetchall()]


def op_list_exam_submissions(cur, p):
    me = _me(cur, p, "instructor")
    if not _is_exam_owner(cur, me, p["exam_id"]):
        raise OpError("not_found", "Exam not found")
    cur.execute(
        """SELECT s.id, u.email, s.question_id, LEFT(q.question_text, 120), q.question_type,
                  q.points, s.status, s.created_at, s.ai_score,
                  g.id, g.score, g.needs_review, g.reviewed_at
           FROM submissions s
           JOIN users u     ON u.id = s.student_id
           JOIN questions q ON q.id = s.question_id
           LEFT JOIN grades g ON g.submission_id = s.id
           WHERE s.exam_id = %s
           ORDER BY u.email, q.created_at;""",
        (p["exam_id"],),
    )
    keys = ["submission_id", "student_email", "question_id", "question_preview", "question_type",
            "max_points", "status", "submitted_at", "ai_score",
            "grade_id", "score", "needs_review", "reviewed_at"]
    return [dict(zip(keys, r)) for r in cur.fetchall()]


# --------------------------------------------------------------------------
# Users, courses and enrollment
# --------------------------------------------------------------------------

def op_get_me(cur, p):
    cur.execute("SELECT id, email, role FROM users WHERE cognito_sub = %s;", (p["sub"],))
    row = cur.fetchone()
    if not row:
        raise OpError("forbidden", "User profile not found")
    return {"user_id": row[0], "email": row[1], "role": row[2]}


def op_list_courses(cur, p):
    me, role = _me_with_role(cur, p)
    if role == "instructor":
        where = "c.instructor_id = %s"
    else:
        where = "EXISTS (SELECT 1 FROM enrollments en WHERE en.course_id = c.id AND en.student_id = %s)"
    cur.execute(
        f"""SELECT c.id, c.course_code, c.course_name, u.email,
                   (SELECT COUNT(*) FROM exams e WHERE e.course_id = c.id)
            FROM courses c JOIN users u ON u.id = c.instructor_id
            WHERE {where}
            ORDER BY c.course_code;""",
        (me,),
    )
    keys = ["course_id", "course_code", "course_name", "instructor_email", "exam_count"]
    return [dict(zip(keys, r)) for r in cur.fetchall()]


def op_create_course(cur, p):
    me = _me(cur, p, "instructor")
    cur.execute(
        """INSERT INTO courses (instructor_id, course_code, course_name)
           VALUES (%s, %s, %s) RETURNING id;""",
        (me, p["course_code"], p["course_name"]),
    )
    return {"course_id": cur.fetchone()[0]}


def op_list_course_exams(cur, p):
    me, role = _me_with_role(cur, p)
    _require_course_access(cur, me, p["course_id"])
    cur.execute(
        """SELECT e.id, e.title, e.total_points, e.duration_minutes, e.created_at,
                  (SELECT COUNT(*) FROM questions q WHERE q.exam_id = e.id),
                  a.status, a.started_at, a.completed_at
           FROM exams e
           LEFT JOIN exam_attempts a ON a.exam_id = e.id AND a.student_id = %s
           WHERE e.course_id = %s
           ORDER BY e.created_at;""",
        (me, p["course_id"]),
    )
    exams = []
    for r in cur.fetchall():
        exam = {"exam_id": r[0], "title": r[1], "total_points": r[2], "duration_minutes": r[3],
                "created_at": r[4], "question_count": r[5]}
        if role == "student":
            exam["attempt_status"] = r[6] or "not_started"
            exam["started_at"] = r[7]
            exam["completed_at"] = r[8]
        exams.append(exam)
    return exams


def op_list_enrollments(cur, p):
    me = _me(cur, p, "instructor")
    _require_course_access(cur, me, p["course_id"], owner_only=True)
    cur.execute(
        """SELECT u.email, en.enrolled_at
           FROM enrollments en JOIN users u ON u.id = en.student_id
           WHERE en.course_id = %s ORDER BY u.email;""",
        (p["course_id"],),
    )
    return [{"email": r[0], "enrolled_at": r[1]} for r in cur.fetchall()]


def op_enroll_student(cur, p):
    me = _me(cur, p, "instructor")
    _require_course_access(cur, me, p["course_id"], owner_only=True)
    cur.execute("SELECT id, role FROM users WHERE lower(email) = lower(%s);", (p["email"],))
    row = cur.fetchone()
    if not row:
        raise OpError("not_found", "No user with this email. The student must sign up first")
    if row[1] != "student":
        raise OpError("bad_request", "Only students can be enrolled")
    cur.execute(
        """INSERT INTO enrollments (course_id, student_id) VALUES (%s, %s)
           ON CONFLICT (course_id, student_id) DO NOTHING RETURNING id;""",
        (p["course_id"], row[0]),
    )
    return {"email": p["email"], "enrolled": cur.fetchone() is not None}


# --------------------------------------------------------------------------
# Instructor review
# --------------------------------------------------------------------------

def op_get_review_queue(cur, p):
    me = _me(cur, p, "instructor")
    cur.execute(
        """SELECT g.id, g.submission_id, e.title, u.email, q.question_text, q.points,
                  s.answer_text, s.ai_score, g.score, g.confidence,
                  g.criteria_breakdown, g.instructor_feedback, g.student_feedback
           FROM grades g
           JOIN submissions s ON s.id = g.submission_id
           JOIN questions q   ON q.id = s.question_id
           JOIN exams e       ON e.id = s.exam_id
           JOIN courses c     ON c.id = e.course_id
           JOIN users u       ON u.id = s.student_id
           WHERE g.needs_review = TRUE AND c.instructor_id = %s
           ORDER BY g.created_at;""",
        (me,),
    )
    keys = ["grade_id", "submission_id", "exam_title", "student_email", "question_text",
            "max_points", "answer_text", "ai_score", "score", "confidence",
            "criteria_breakdown", "instructor_feedback", "student_feedback"]
    return [dict(zip(keys, r)) for r in cur.fetchall()]


def op_submit_review(cur, p):
    me = _me(cur, p, "instructor")
    cur.execute(
        """SELECT q.points
           FROM grades g
           JOIN submissions s ON s.id = g.submission_id
           JOIN questions q   ON q.id = s.question_id
           JOIN exams e       ON e.id = s.exam_id
           JOIN courses c     ON c.id = e.course_id
           WHERE g.id = %s AND c.instructor_id = %s
           FOR UPDATE OF g;""",
        (p["grade_id"], me),
    )
    row = cur.fetchone()
    if not row:
        raise OpError("not_found", "Grade not found")
    max_points = row[0]
    if not 0 <= p["score"] <= max_points:
        raise OpError("bad_request", f"Score must be between 0 and {max_points}")

    cur.execute(
        """UPDATE grades
           SET score = %s,
               instructor_feedback = COALESCE(%s, instructor_feedback),
               student_feedback = COALESCE(%s, student_feedback),
               needs_review = FALSE,
               reviewed_by = %s,
               reviewed_at = CURRENT_TIMESTAMP
           WHERE id = %s;""",
        (p["score"], p.get("instructor_feedback"), p.get("student_feedback"), me, p["grade_id"]),
    )
    return {"grade_id": p["grade_id"], "score": p["score"]}


# --------------------------------------------------------------------------
# Proctoring (Khaled's contract, adapted to our IDs and JWT identity)
# --------------------------------------------------------------------------

EVENT_COLUMNS = """pe.event_id, u.email, pe.reasons, pe.triggered_at, pe.created_at,
                   pe.content_type, pe.size_bytes, pe.clip_metadata, pe.consent_version,
                   pe.expires_at, pe.reviewed, pe.instructor_decision, pe.reviewed_at,
                   pe.version, (pe.expires_at < CURRENT_TIMESTAMP) AS clip_expired"""
EVENT_KEYS = ["eventId", "studentEmail", "reasons", "triggeredAt", "createdAt",
              "contentType", "sizeBytes", "clip", "consentVersion",
              "expiresAt", "reviewed", "instructorDecision", "reviewedAt",
              "version", "clipExpired"]


def _event(row):
    """Turn an EVENT_COLUMNS row into the API shape, splitting stored metadata."""
    event = dict(zip(EVENT_KEYS, row))
    meta = event.pop("clip") or {}
    event["clip"] = meta.get("clip")
    event["detection"] = {k: meta.get(k) for k in ("thresholds", "triggerMonotonicMs", "sustainedMs")}
    return event


def _select_event(cur, event_id):
    cur.execute(
        f"SELECT {EVENT_COLUMNS} FROM proctoring_events pe JOIN users u ON u.id = pe.student_id "
        "WHERE pe.event_id = %s;",
        (event_id,),
    )
    return _event(cur.fetchone())


def _clip_key(exam_id, student_id, event_id):
    return f"proctoring/{exam_id}/{student_id}/{event_id}.webm"


def _require_event_owner(cur, me, event_id, lock=False):
    """The caller must be the instructor of the course the event's exam belongs to."""
    cur.execute(
        """SELECT pe.object_key, pe.expires_at < CURRENT_TIMESTAMP
           FROM proctoring_events pe
           JOIN exams e   ON e.id = pe.exam_id
           JOIN courses c ON c.id = e.course_id
           WHERE pe.event_id = %s AND c.instructor_id = %s""" + (" FOR UPDATE OF pe;" if lock else ";"),
        (event_id, me),
    )
    row = cur.fetchone()
    if not row:
        raise OpError("not_found", "Event not found")
    return row


def op_proctoring_upload_key(cur, p):
    # Before upload: the student must be enrolled; the server decides the key.
    me = _me(cur, p, "student")
    _require_exam_access(cur, me, p["exam_id"])
    return {"object_key": _clip_key(p["exam_id"], me, p["event_id"])}


def op_create_proctoring_event(cur, p):
    me = _me(cur, p, "student")
    _require_exam_access(cur, me, p["exam_id"])
    if p["object_key"] != _clip_key(p["exam_id"], me, p["event_id"]):
        raise OpError("forbidden", "This upload does not belong to this event")

    cur.execute(
        """INSERT INTO proctoring_events
               (event_id, exam_id, student_id, reasons, triggered_at, object_key, content_type,
                size_bytes, clip_metadata, consent_version, consented_at, expires_at)
           VALUES (%s, %s, %s, %s::text[], %s::timestamptz, %s, %s, %s, %s::jsonb, %s,
                   %s::timestamptz, CURRENT_TIMESTAMP + make_interval(days => %s))
           ON CONFLICT (event_id) DO NOTHING
           RETURNING event_id;""",
        (
            p["event_id"], p["exam_id"], me, p["reasons"], p["triggered_at"], p["object_key"],
            p["content_type"], p["size_bytes"], json.dumps(p.get("clip_metadata") or {}),
            p["consent_version"], p["consented_at"], p["retention_days"],
        ),
    )
    created = cur.fetchone() is not None
    if not created:
        # A retry of the same event returns the original; anything else is a conflict.
        cur.execute(
            """SELECT student_id = %s AND exam_id = %s AND object_key = %s
                      AND reasons = %s::text[] AND triggered_at = %s::timestamptz
                      AND size_bytes = %s AND content_type = %s
               FROM proctoring_events WHERE event_id = %s;""",
            (me, p["exam_id"], p["object_key"], p["reasons"], p["triggered_at"],
             p["size_bytes"], p["content_type"], p["event_id"]),
        )
        same = cur.fetchone()
        if not same or not same[0]:
            raise OpError("conflict", "This event ID is already used with different details")

    return {"created": created, "event": _select_event(cur, p["event_id"])}


def op_list_proctoring_events(cur, p):
    me = _me(cur, p, "instructor")
    _require_exam_access(cur, me, p["exam_id"])
    cur.execute(
        f"""SELECT {EVENT_COLUMNS}
            FROM proctoring_events pe JOIN users u ON u.id = pe.student_id
            WHERE pe.exam_id = %s
            ORDER BY pe.triggered_at DESC
            LIMIT 200;""",
        (p["exam_id"],),
    )
    return [_event(r) for r in cur.fetchall()]


def op_get_proctoring_clip(cur, p):
    me = _me(cur, p, "instructor")
    object_key, expired = _require_event_owner(cur, me, p["event_id"])
    if expired:
        raise OpError("gone", "The retention period for this clip has ended")
    return {"object_key": object_key}


def op_review_proctoring_event(cur, p):
    me = _me(cur, p, "instructor")
    _require_event_owner(cur, me, p["event_id"], lock=True)
    # Optimistic concurrency: only update the version the reviewer actually saw.
    cur.execute(
        """UPDATE proctoring_events
           SET reviewed = TRUE, instructor_decision = %s, reviewed_by = %s,
               reviewed_at = CURRENT_TIMESTAMP, version = version + 1
           WHERE event_id = %s AND version = %s
           RETURNING version;""",
        (p["decision"], me, p["event_id"], p["version"]),
    )
    row = cur.fetchone()
    if not row:
        raise OpError("conflict", "This event was changed by someone else. Reload and try again")
    cur.execute(
        """INSERT INTO proctoring_review_audit (event_id, reviewer_id, decision, event_version)
           VALUES (%s, %s, %s, %s);""",
        (p["event_id"], me, p["decision"], row[0]),
    )
    return _select_event(cur, p["event_id"])  # the full updated event


# --------------------------------------------------------------------------
# Users
# --------------------------------------------------------------------------

def op_create_user(cur, p):
    cur.execute(
        """INSERT INTO users (cognito_sub, email, role)
           VALUES (%s, %s, 'student')
           ON CONFLICT (cognito_sub) DO NOTHING;""",
        (p["cognito_sub"], p.get("email")),
    )
    return {"cognito_sub": p["cognito_sub"]}


OPERATIONS = {
    "get_exam": op_get_exam,
    "get_exam_questions": op_get_exam_questions,
    "create_exam": op_create_exam,
    "create_question": op_create_question,
    "start_submission": op_start_submission,
    "save_grade": op_save_grade,
    "fail_submission": op_fail_submission,
    "get_grade": op_get_grade,
    "finalize_exam": op_finalize_exam,
    "get_review_queue": op_get_review_queue,
    "submit_review": op_submit_review,
    "create_user": op_create_user,
    "proctoring_upload_key": op_proctoring_upload_key,
    "create_proctoring_event": op_create_proctoring_event,
    "list_proctoring_events": op_list_proctoring_events,
    "get_proctoring_clip": op_get_proctoring_clip,
    "review_proctoring_event": op_review_proctoring_event,
    "start_exam": op_start_exam,
    "list_my_submissions": op_list_my_submissions,
    "list_exam_submissions": op_list_exam_submissions,
    "get_me": op_get_me,
    "list_courses": op_list_courses,
    "create_course": op_create_course,
    "list_course_exams": op_list_course_exams,
    "list_enrollments": op_list_enrollments,
    "enroll_student": op_enroll_student,
}

# PostgreSQL error codes -> our error codes
SQLSTATE_CODES = {
    "22P02": "bad_request",  # invalid input, e.g. a malformed UUID
    "22003": "bad_request",  # number out of range
    "23502": "bad_request",  # missing required value
    "23503": "bad_request",  # referenced row does not exist
    "23514": "bad_request",  # check constraint failed
    "23505": "conflict",     # duplicate
}
MESSAGES = {"bad_request": "Invalid input", "conflict": "Conflict with existing data", "db_error": "Database error"}


def op_run_tests(p):
    """Relay for the router: run a student's code on the private Judge0 server (no database needed)."""
    statuses = judge0_client.run_tests(
        int(p["language_id"]),
        p["source_code"],
        [(str(case[0]), str(case[1])) for case in p["test_cases"]],
        Deadline(max(0.0, float(p["seconds"]) - 0.3)),  # a little slack for the trip back
    )
    return {"statuses": statuses}


NO_DB_OPERATIONS = {"run_tests": op_run_tests}


def lambda_handler(event, context):
    op = event.get("op")
    params = event.get("params") or {}

    if op in NO_DB_OPERATIONS:
        try:
            return {"ok": True, "data": NO_DB_OPERATIONS[op](params)}
        except judge0_client.Judge0Error as e:
            return {"ok": False, "code": "judge0_error", "error": str(e)}  # messages carry no student data
        except (KeyError, TypeError, ValueError) as e:
            return {"ok": False, "code": "bad_request", "error": f"Invalid parameters ({type(e).__name__})"}

    handler = OPERATIONS.get(op)
    if handler is None:
        return {"ok": False, "code": "bad_request", "error": "Unknown operation"}

    try:
        conn = _connect()
    except Exception as e:
        logger.error("op=%s connection failed: %s", op, type(e).__name__)
        return {"ok": False, "code": "db_error", "error": "Database unavailable"}

    try:
        cur = conn.cursor()
        data = handler(cur, params)
        conn.commit()
        return {"ok": True, "data": _jsonable(data)}
    except OpError as e:
        conn.rollback()
        return {"ok": False, "code": e.code, "error": e.message}
    except KeyError as e:
        conn.rollback()
        return {"ok": False, "code": "bad_request", "error": f"Missing parameter: {e.args[0]}"}
    except pg8000.dbapi.DatabaseError as e:
        conn.rollback()
        details = e.args[0] if e.args and isinstance(e.args[0], dict) else {}
        sqlstate = details.get("C")
        code = SQLSTATE_CODES.get(sqlstate, "db_error")
        logger.error("op=%s failed sqlstate=%s", op, sqlstate)
        return {"ok": False, "code": code, "error": MESSAGES[code]}
    except Exception as e:
        conn.rollback()
        logger.error("op=%s unexpected error: %s", op, type(e).__name__)
        return {"ok": False, "code": "db_error", "error": MESSAGES["db_error"]}
    finally:
        conn.close()