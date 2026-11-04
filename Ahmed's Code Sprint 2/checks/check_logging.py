# for importing
import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

# Proves that the logs (and the "error" text of a failed result) never contain the student's answer or the model's reply.
# Every scenario puts a marker text into the student input, the model's reply or an error message, then
# runs the grading with a fake model (and fake Judge0), so it is offline and uses no quota, and checks the marker
# is in none of the log lines. Run it from the project root: python checks/check_logging.py
import json
import logging

from fairgrade import gemini_client
from fairgrade import judge0_client
import grading_api
from fairgrade.gemini_client import GeminiClient
from fairgrade.log_config import setup_logging

sys.stdout.reconfigure(encoding="utf-8")

MARKER = "ZXQ-PRIVATE-MARKER"
GOOD_REPLY = json.dumps({"confidence": 0.9, "student_feedback": f"feedback {MARKER}", "instructor_feedback": f"note {MARKER}",
                         "rubric_breakdown": [{"criteria_id": "c1", "score": 1.0}, {"criteria_id": "c2", "score": 1.0}]})

RUBRIC = [{"id": "c1", "requirement": "first", "weight_fraction": 0.5}, {"id": "c2", "requirement": "second", "weight_fraction": 0.5}]
TEXT_QUESTION = {"subject_name": "s", "subject_description": "d", "question_text": "q", "question_type": "short_answer",
                 "model_answer": "m", "max_points": 10, "rubric": RUBRIC}
CODE_QUESTION = dict(TEXT_QUESTION, question_type="coding", language_id=71, test_cases=[{"input": "1", "expected_output": "1", "hidden": False}])

GeminiClient.RETRY_WAIT_SECONDS = 0   # no waiting between attempts in this check


# the log lines of one scenario
class Collector(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


setup_logging()
collector = Collector()
logging.getLogger("fairgrade").addHandler(collector)
logging.getLogger("fairgrade").setLevel(logging.DEBUG)


def fake_model(injection_reply, grading_reply):
    def send_request(cls, prompt, timeout=10):
        reply = grading_reply if "rubric_breakdown" in prompt else injection_reply
        if(isinstance(reply, Exception)):
            raise reply
        return reply
    return classmethod(send_request)


def fake_judge0(outcome):
    def run_tests(language_id, source_code, test_cases, deadline):
        if(isinstance(outcome, Exception)):
            raise outcome
        return outcome
    return run_tests


# (name, kind, model's reply to the injection check, model's reply to the grading, judge0 outcome, student input)
SCENARIOS = [
    ("injection check answers with text", "text", f"{MARKER} 1 0", GOOD_REPLY, None, f"my answer {MARKER}"),
    ("grading reply is not json", "text", "0", f"{MARKER} this is not json", None, f"my answer {MARKER}"),
    ("grading reply has a bad id and score", "text", "0",
     json.dumps({"confidence": 0.5, "student_feedback": "a", "instructor_feedback": "b",
                 "rubric_breakdown": [{"criteria_id": MARKER, "score": MARKER}, {"criteria_id": "c2", "score": 1}]}), None, f"my answer {MARKER}"),
    ("grading reply has an extra key", "text", "0",
     json.dumps({"confidence": 0.5, "student_feedback": "a", "instructor_feedback": "b",
                 "rubric_breakdown": [{MARKER: 1, "criteria_id": "c1", "score": 1}, {"criteria_id": "c2", "score": 1}]}), None, f"my answer {MARKER}"),
    ("grading reply has the wrong number of items", "text", "0",
     json.dumps({"confidence": 0.5, "student_feedback": "a", "instructor_feedback": "b",
                 "rubric_breakdown": [{"criteria_id": "c1", "score": 1}]}), None, f"my answer {MARKER}"),
    ("the model library raises an error quoting the input", "text", RuntimeError(f"bad request for {MARKER}"), GOOD_REPLY, None, f"my answer {MARKER}"),
    ("judge0 raises an error quoting the code", "code", "0", GOOD_REPLY, RuntimeError(f"failed on {MARKER}"), f"print('{MARKER}')"),
    ("a good grading", "text", "0", GOOD_REPLY, None, f"my answer {MARKER}"),
    ("a good code grading", "code", "0", GOOD_REPLY, ["Accepted"], f"print('{MARKER}')"),
]

passed = 0
for name, kind, injection_reply, grading_reply, judge0_outcome, student_input in SCENARIOS:
    GeminiClient.send_request = fake_model(injection_reply, grading_reply)
    judge0_client.run_tests = fake_judge0(judge0_outcome)
    collector.lines.clear()

    if(kind == "text"):
        result = grading_api.grade_text(TEXT_QUESTION, student_input)
    else:
        result = grading_api.grade_code(CODE_QUESTION, student_input)

    # a graded result legitimately carries the model's feedback, a failed one must not carry any of it
    checked_result = json.dumps(result if result["status"] != "graded" else {"error": result["error"]})
    leaked_in_logs = any(MARKER in line for line in collector.lines)
    leaked_in_result = MARKER in checked_result
    ok = not leaked_in_logs and not leaked_in_result
    passed += ok

    print(f"{'PASS' if ok else 'FAIL'}  {name:<52} status={result['status']:<9} log lines={len(collector.lines)}")
    if(not ok):
        for line in collector.lines:
            print(f"      log: {line}")
        print(f"      error: {result['error']}")

print(f"\n{passed} of {len(SCENARIOS)} scenarios kept the marker out of the logs and failed results")
print("\nExample log lines from the last scenarios:")
for line in collector.lines:
    print(f"  {line}")
