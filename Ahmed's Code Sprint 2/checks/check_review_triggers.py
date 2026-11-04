# for importing
import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

# Checks the needs_review triggers with made-up results, so it is offline and uses no quota. Every case says what
# the grader is given (confidence, criteria scores, share of the maximum, tests passed) and which trigger must fire.
# Run it from the project root: python checks/check_review_triggers.py
from fairgrade.ai_response import AiResponse
from fairgrade.grader import Grader, trigger_reasons

sys.stdout.reconfigure(encoding="utf-8")

# (name, confidence, criteria scores, share of the maximum, tests passed, tests total, words that must be in a reason; None = no reason at all)
CASES = [
    ("text: full marks", 0.95, [1, 1, 1, 1], 1.0, None, None, None),
    ("text: zero", 0.95, [0, 0, 0, 0], 0.0, None, None, None),
    ("text: fractional scores", 0.95, [1, 0.5, 0.5, 0.5], 0.62, None, None, "fractional"),
    ("text: one criterion at 0.8", 0.95, [1, 1, 1, 0.8], 0.95, None, None, "fractional"),
    ("text: mixed scores", 0.95, [1, 0, 1, 1], 0.75, None, None, "mixed"),
    ("text: only 0 and 1, not mixed", 0.95, [0, 0, 0, 0], 0.0, None, None, None),
    ("text: low confidence", 0.6, [1, 1, 1, 1], 1.0, None, None, "low confidence"),
    ("code: all tests pass, full marks", 0.95, [1, 1, 1, 1], 1.0, 9, 9, None),
    ("code: no test passes, zero", 0.95, [0, 0, 0, 0], 0.0, 0, 9, None),
    ("code: most tests fail, high score", 0.95, [1, 1, 0.75, 0.75], 0.85, 2, 9, "tests and score disagree"),
    ("code: most tests pass, low score", 0.95, [0.5, 0.5, 0.25, 0.25], 0.4, 8, 9, "tests and score disagree"),
    ("code: all tests pass, zero (hard-coded?)", 0.95, [0, 0, 0, 0], 0.0, 7, 7, "tests and score disagree"),
    ("code: most tests fail, score 66%", 0.95, [1, 1, 0.2, 0.5, 1], 0.66, 1, 7, "tests and score disagree"),
    ("code: 5 of 7 tests pass, score 0 (hard-coded)", 0.95, [0, 0, 0, 0], 0.0, 5, 7, "tests and score disagree"),
    ("code: half the tests pass, middling score", 0.95, [0.5, 0.5, 0.5, 0.5], 0.5, 4, 8, None),
    ("code: most pass, a bug cost a little", 0.95, [1, 1, 0.75, 0.75], 0.875, 6, 7, None),
    ("code: no tests", 0.95, [1, 1, 1, 1], 1.0, 0, 0, None),
]

failures = 0
for name, confidence, scores, fraction, passed, total, expected in CASES:
    reasons = trigger_reasons(confidence, scores, fraction, passed, total)
    ok = (not reasons) if expected is None else any(expected in reason for reason in reasons)
    failures += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {name:<42} {'; '.join(reasons) or 'not flagged'}")

# the same rules through the real Grader: the Judge0 statuses of a code question reach the trigger
rubric = [{"id": "c1", "requirement": "r", "weight_fraction": 0.5}, {"id": "c2", "requirement": "r", "weight_fraction": 0.5}]
def assessment(second_score):
    return AiResponse(confidence=0.95, student_feedback="f", instructor_feedback="i", criteria_count=2,
                      rubric_breakdown=[{"criteria_id": "c1", "score": 1.0}, {"criteria_id": "c2", "score": second_score}])


for name, second_score, statuses, flagged in [("grader: text question, all met", 1.0, None, False),
                                              ("grader: text question, one criterion at 0.8", 0.8, None, True),
                                              ("grader: code, 1 of 5 tests accepted", 0.8, ["Accepted"] + ["Wrong Answer"] * 4, True),
                                              ("grader: code, 5 of 5 tests accepted", 0.8, ["Accepted"] * 5, False)]:
    result = Grader(ai_assessment=assessment(second_score), question_rubric=rubric, max_points=2, test_statuses=statuses).final_assessment()
    ok = result["needs_review"] == flagged and bool(result["review_reasons"]) == flagged
    failures += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {name:<46} {'; '.join(result['review_reasons']) or 'not flagged'}")

print(f"\n{'All triggers behave as expected.' if failures == 0 else str(failures) + ' case(s) failed.'}")
