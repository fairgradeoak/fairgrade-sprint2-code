-- =====================================================================
-- FairGrade database schema (PostgreSQL 13+; production runs RDS 18.3)
-- Matches the live database after the Oct 31, 2026 migration (Part B).
-- Safe to re-run: every object uses IF NOT EXISTS, so running it on the
-- existing database changes nothing. It does NOT alter existing tables;
-- schema changes go in a separate migration script.
-- =====================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS users (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cognito_sub varchar(255) NOT NULL,
    email       varchar(255) NOT NULL,
    role        varchar(50)  NOT NULL,
    created_at  timestamptz  DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_cognito_sub_key UNIQUE (cognito_sub),
    CONSTRAINT users_email_key UNIQUE (email),
    CONSTRAINT users_role_check CHECK (role IN ('student', 'instructor', 'admin'))
);

CREATE TABLE IF NOT EXISTS courses (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    instructor_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_code   varchar(50)  NOT NULL,
    course_name   varchar(255) NOT NULL,
    created_at    timestamptz  DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT courses_instructor_code_key UNIQUE (instructor_id, course_code)
);

CREATE TABLE IF NOT EXISTS enrollments (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id   uuid NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    student_id  uuid NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
    enrolled_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT enrollments_course_student_key UNIQUE (course_id, student_id)
);
CREATE INDEX IF NOT EXISTS enrollments_student_idx ON enrollments (student_id);

CREATE TABLE IF NOT EXISTS exams (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id     uuid NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title         varchar(255) NOT NULL,
    total_points  integer NOT NULL,
    rubric_s3_key varchar(1024),
    created_at    timestamptz DEFAULT CURRENT_TIMESTAMP,
    duration_minutes integer
        CHECK (duration_minutes IS NULL OR (duration_minutes > 0 AND duration_minutes <= 600))
);

CREATE TABLE IF NOT EXISTS questions (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id       uuid NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    question_text text NOT NULL,
    points        integer NOT NULL,
    question_type varchar(20) NOT NULL DEFAULT 'short_answer',
    model_answer  text,
    rubric        jsonb,
    created_at    timestamptz DEFAULT CURRENT_TIMESTAMP,
    language_id   integer,
    starter_code  text,
    test_cases    jsonb,
    CONSTRAINT questions_points_check CHECK (points > 0),
    CONSTRAINT questions_question_type_check
        CHECK (question_type IN ('short_answer', 'mcq', 'true_false', 'matching', 'coding')),
    CONSTRAINT questions_coding_fields_check
        CHECK (question_type <> 'coding' OR (language_id IS NOT NULL AND test_cases IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS exam_attempts (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id      uuid NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    student_id   uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status       varchar(50) NOT NULL,
    completed_at timestamptz,
    started_at   timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT exam_attempts_exam_id_student_id_key UNIQUE (exam_id, student_id),
    CONSTRAINT exam_attempts_status_check CHECK (status IN ('in_progress', 'completed'))
);

CREATE TABLE IF NOT EXISTS submissions (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id           uuid NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    student_id        uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question_id       uuid REFERENCES questions(id) ON DELETE CASCADE,
    answer_text       text,
    submission_s3_key varchar(1024),
    status            varchar(50) NOT NULL DEFAULT 'pending',
    ai_score          numeric(5, 2),
    ai_feedback       text,
    created_at        timestamptz DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT submissions_exam_id_student_id_question_id_key UNIQUE (exam_id, student_id, question_id),
    CONSTRAINT submissions_status_check CHECK (status IN ('pending', 'grading', 'completed', 'failed'))
);

CREATE TABLE IF NOT EXISTS grades (
    id                  serial PRIMARY KEY,
    submission_id       uuid NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    score               numeric(5, 2),
    criteria_breakdown  jsonb,
    confidence          numeric(5, 2),
    needs_review        boolean DEFAULT false,
    instructor_feedback text,
    student_feedback    text,
    reviewed_by         uuid REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at         timestamptz,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT grades_submission_id_key UNIQUE (submission_id),
    CONSTRAINT grades_score_check CHECK (score >= 0),
    CONSTRAINT grades_confidence_check CHECK (confidence BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS proctoring_events (
    event_id            uuid PRIMARY KEY,
    exam_id             uuid NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    student_id          uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reasons             text[] NOT NULL CHECK (cardinality(reasons) > 0 AND
                          reasons <@ ARRAY['phone','second_face','identity_mismatch','no_face']::text[]),
    triggered_at        timestamptz NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    object_key          text NOT NULL UNIQUE,
    content_type        text NOT NULL,
    size_bytes          bigint NOT NULL CHECK (size_bytes > 0 AND size_bytes <= 20971520),
    clip_metadata       jsonb NOT NULL DEFAULT '{}'::jsonb,
    consent_version     text NOT NULL,
    consented_at        timestamptz NOT NULL,
    expires_at          timestamptz NOT NULL,
    reviewed            boolean NOT NULL DEFAULT false,
    instructor_decision text CHECK (instructor_decision IN ('confirmed', 'dismissed')),
    reviewed_by         uuid REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at         timestamptz,
    version             integer NOT NULL DEFAULT 0,
    CONSTRAINT proctoring_events_review_check CHECK (
        (reviewed AND instructor_decision IS NOT NULL AND reviewed_at IS NOT NULL)
        OR (NOT reviewed AND instructor_decision IS NULL AND reviewed_by IS NULL AND reviewed_at IS NULL))
);
CREATE INDEX IF NOT EXISTS proctoring_events_exam_time ON proctoring_events (exam_id, triggered_at DESC);

CREATE TABLE IF NOT EXISTS proctoring_review_audit (
    audit_id      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id      uuid NOT NULL REFERENCES proctoring_events(event_id) ON DELETE CASCADE,
    reviewer_id   uuid REFERENCES users(id) ON DELETE SET NULL,
    decision      text NOT NULL CHECK (decision IN ('confirmed', 'dismissed')),
    reviewed_at   timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_version integer NOT NULL,
    CONSTRAINT proctoring_review_audit_event_version_key UNIQUE (event_id, event_version)
);

COMMIT;