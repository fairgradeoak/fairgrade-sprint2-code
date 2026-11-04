# for importing
import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

# Times the two public entry points (grading_api.grade_text and grade_code) on real samples:
# 10 text gradings and 10 code gradings, one after the other, then prints the average and the slowest time of each
# and writes every timing to a CSV. The whole request must finish within 20 seconds.
# Needs the real Gemini key and a running Judge0. Run it from the project root: python scripts/run_timing.py
import csv
import statistics
import time
from datetime import datetime

from grading_api import grade_text, grade_code
from fairgrade.log_config import setup_logging
from samples.sample_text_questions import tests as text_tests
from samples.sample_code_questions import tests as code_tests

# ---------------------------------------------------------------- settings
COUNT = 10             # gradings per kind
SLEEP_SECONDS = 5      # pause between gradings so the model's rate limit is not the thing being measured (not timed)
LIMIT_SECONDS = 20     # the budget every grading has to stay under

sys.stdout.reconfigure(encoding="utf-8")
setup_logging()


def spread(tests, count):
    """`count` samples spread evenly over the list, so different questions and categories are timed."""
    step = max(1, len(tests) // count)
    return tests[::step][:count]


def text_question_dict(question):
    data = dict(vars(question))
    data["question_type"] = "short_answer"
    return data


def code_question_dict(question):
    data = dict(vars(question))
    data["question_type"] = "coding"
    # the samples keep test cases as (input, expected_output) pairs and the language as the judge0 enum,
    # the real database sends dicts and a plain integer
    data["language_id"] = int(getattr(data["language_id"], "value", data["language_id"]))
    data["test_cases"] = [{"input": stdin, "expected_output": expected, "hidden": False} for stdin, expected in data["test_cases"]]
    return data


def timed(grade, question, student_input):
    started = time.perf_counter()
    result = grade(question, student_input)
    return time.perf_counter() - started, result


def run(kind, grade, tests, to_dict):
    rows = []
    for number, test in enumerate(spread(tests, COUNT), start=1):
        seconds, result = timed(grade, to_dict(test.question), test.test_answer)
        print(f"{kind} {number:>2}: {seconds:5.1f} s  status={result['status']}  attempts={result['attempts']}")
        rows.append({"kind": kind, "number": number, "seconds": round(seconds, 2), "status": result["status"],
                     "attempts": result["attempts"], "error": result["error"] or ""})
        time.sleep(SLEEP_SECONDS)
    return rows


def summary(kind, rows):
    seconds = [row["seconds"] for row in rows]
    over = sum(1 for value in seconds if value > LIMIT_SECONDS)
    print(f"{kind}: average {statistics.mean(seconds):.1f} s, slowest {max(seconds):.1f} s, over {LIMIT_SECONDS} s: {over} of {len(seconds)}")


rows = run("text", grade_text, text_tests, text_question_dict) + run("code", grade_code, code_tests, code_question_dict)

print()
summary("text", [row for row in rows if row["kind"] == "text"])
summary("code", [row for row in rows if row["kind"] == "code"])

results_dir = root / "results"
results_dir.mkdir(parents=True, exist_ok=True)
output_file = results_dir / f"timing_{datetime.now():%Y-%m-%d_%H%M}.csv"
with open(output_file, "w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=["kind", "number", "seconds", "status", "attempts", "error"])
    writer.writeheader()
    writer.writerows(rows)
print(f"saved to {output_file}")
