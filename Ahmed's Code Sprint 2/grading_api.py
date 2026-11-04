# The two entry points the rest of the system calls. Everything else in this project is internal.
#
#   grade_text(question: dict, answer: str) -> dict
#   grade_code(question: dict, code: str) -> dict
#
# `question` is a row coming from the database:
#   {"subject_name", "subject_description", "question_text", "question_type" ("short_answer" | "coding"),
#    "model_answer", "max_points", "rubric": [{"id", "requirement", "weight_fraction"}],
#    "language_id": int (judge0 language id, for example 71),                       # coding only
#    "test_cases": [{"input", "expected_output", "hidden"}]}                         # coding only
#
# Both functions return the result dict built by grader.build_result (never a json string) and never raise:
# bad input, model failures and judge0 failures all come back as a result with status "failed" so the
# submission can go to the instructor.

# Built-in
import logging
import time

# Project
from fairgrade.coding_question import CodingQuestion
from fairgrade.gemini_client import GeminiClient
from fairgrade.grader import Grader
from fairgrade.question import Question
from fairgrade.safe_errors import describe_error

# What is logged: the kind of grading, the status, the number of attempts, the time and error descriptions that carry
# no data. Never the student's answer, the question, the model's reply or the feedback.
logger = logging.getLogger("fairgrade.api")

TEXT_FIELDS = ("subject_name", "subject_description", "question_text", "question_type", "model_answer", "max_points", "rubric")
CODE_FIELDS = TEXT_FIELDS + ("language_id", "test_cases")


def max_points_of(question):
    try:
        return question.get("max_points")
    except Exception:
        return None


# returns a description of what is wrong with the input, or None when it is usable
def find_problem(question, student_input, student_label, fields):
    if(not isinstance(question, dict)):
        return "question must be a dict"
    missing = [field for field in fields if field not in question]
    if(missing):
        return f"question is missing: {', '.join(missing)}"
    if(not isinstance(student_input, str) or not student_input.strip()):
        return f"{student_label} must be a non-empty string"
    if(isinstance(question["max_points"], bool) or not isinstance(question["max_points"], (int, float)) or question["max_points"] <= 0):
        return "max_points must be a positive number"
    rubric = question["rubric"]
    if(not isinstance(rubric, list) or not rubric):
        return "rubric must be a non-empty list"
    for criterion in rubric:
        if(not isinstance(criterion, dict) or not {"id", "requirement", "weight_fraction"} <= criterion.keys()):
            return "every rubric entry needs id, requirement and weight_fraction"
    if(fields is CODE_FIELDS):
        if(isinstance(question["language_id"], bool) or not isinstance(question["language_id"], int)):
            return "language_id must be a judge0 language id (int)"
        if(not isinstance(question["test_cases"], list) or not question["test_cases"]):
            return "test_cases must be a non-empty list"
        if(len(question["test_cases"]) > 20):
            return "test_cases can have at most 20 entries"
        for test_case in question["test_cases"]:
            if(not isinstance(test_case, dict) or "input" not in test_case or "expected_output" not in test_case):
                return "every test case needs input and expected_output"
    return None


def failed(question, reason):
    max_points = max_points_of(question) if isinstance(question, dict) else None
    return Grader.failed_result(max_points, f"invalid request, {reason}", attempts=0)


# runs one grading, logs one line about it (no student data) and makes sure nothing escapes as an exception
def run_grading(kind, question, student_input, student_label, fields, build_and_grade):
    started = time.perf_counter()
    try:
        problem = find_problem(question, student_input, student_label, fields)
        if(problem):
            logger.warning("%s grading refused, invalid request: %s", kind, problem)
            return failed(question, problem)

        result = build_and_grade()
    except Exception as error:
        logger.error("%s grading crashed: %s", kind, describe_error(error))
        return failed(question, f"unexpected {type(error).__name__}")

    logger.info("%s grading finished: status=%s attempts=%s needs_review=%s seconds=%.1f",
                kind, result["status"], result["attempts"], result["needs_review"], time.perf_counter() - started)
    return result


def grade_text(question: dict, answer: str) -> dict:
    return run_grading("text", question, answer, "answer", TEXT_FIELDS,
                       lambda: GeminiClient.review_text_submission(Question(*(question[field] for field in TEXT_FIELDS)), answer))


def grade_code(question: dict, code: str) -> dict:
    return run_grading("code", question, code, "code", CODE_FIELDS,
                       lambda: GeminiClient.review_code_submission(CodingQuestion(*(question[field] for field in CODE_FIELDS)), code))
