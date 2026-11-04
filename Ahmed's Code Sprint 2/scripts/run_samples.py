# for importing
import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

# Runs every SampleQuestion in `tests` (sample_text_questions.py) through the real grading pipeline
# (GeminiClient.review_text_submission, which uses PromptGenerator) and writes one CSV row per test.
# Run it from the project root: python run_samples.py
import csv
import json
import time
from collections import defaultdict
from datetime import datetime

from fairgrade.gemini_client import GeminiClient
from fairgrade.log_config import setup_logging

# add the word arabic to run the Arabic samples instead: python scripts/run_samples.py arabic
ARABIC = "arabic" in sys.argv[1:]
if ARABIC:
    from samples.sample_arabic import text_tests as tests
else:
    from samples.sample_text_questions import tests

# ---------------------------------------------------------------- settings
SLEEP_SECONDS = 10         # pause between tests (each test makes 2 API calls); raise it if you hit rate limits
TOLERANCE_FRACTION = 0.10  # a test passes when |model grade - expected score| <= 10% of the question's max_points
MAX_ATTEMPTS = 2           # tries per test: a failed call or an unusable reply is retried
RETRY_WAIT_SECONDS = 60    # wait before a retry
ONLY_TESTS = None          # e.g. [13, 14, 15] to run only those tests (numbered 1-30 as in sample_questions.py)

# one column per criterion score (c1_score, c2_score...), because needs_review depends on them: it is true when some
# criteria are fully met and others not met at all in the same answer
MAX_CRITERIA = max(len(test.question.rubric) for test in tests)
CRITERIA_COLUMNS = [f"c{number}_score" for number in range(1, MAX_CRITERIA + 1)]

COLUMNS = ["test_number", "category", "subject", "question", "student_answer", "max_points", "expected_score",
           "model_grade", "difference", "confidence", "needs_review", "review_reasons", *CRITERIA_COLUMNS, "rubric_breakdown", "student_feedback",
           "instructor_feedback", "status", "error", "model_attempts", "attempts", "passed"]

sys.stdout.reconfigure(encoding="utf-8")  # so printing symbols never crashes a Windows console
setup_logging()


RESULTS_DIR = root / "results"  # results, created on the first run


def next_output_file(prefix):
    """results/<prefix>_YYYY-MM-DD_N.csv, where N is 1 for the first file of the day and counts up."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    today = f"{datetime.now():%Y-%m-%d}"
    taken = [int(path.stem.rsplit("_", 1)[1]) for path in RESULTS_DIR.glob(f"{prefix}_{today}_*.csv")
             if path.stem.rsplit("_", 1)[1].isdigit()]
    return RESULTS_DIR / f"{prefix}_{today}_{max(taken, default=0) + 1}.csv"


def short(text, limit=300):
    return " ".join(str(text).split())[:limit]


def grade_one(test):
    """Run one sample through the pipeline. Returns (result, attempts); result["status"] is
    graded, injection_flagged, failed (the client gave up after its own retries and sent it to review)
    or error (an unexpected exception reached this runner)."""
    last_error = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            # the client always returns one dict shape, its "status" field is graded, injection_flagged or failed
            return GeminiClient.review_text_submission(test.question, test.test_answer), attempt
        except Exception as error:  # API error, rate limit, malformed JSON, failed validation...
            last_error = f"{type(error).__name__}: {short(error)}"
            if attempt < MAX_ATTEMPTS:
                print(f"   attempt {attempt} failed ({last_error[:80]}), waiting {RETRY_WAIT_SECONDS}s")
                time.sleep(RETRY_WAIT_SECONDS)
    return {"status": "error", "error": last_error}, MAX_ATTEMPTS


def blank(value):
    return "" if value is None else value


def build_row(number, test, result, attempts):
    grade = result.get("grade")
    max_points = test.question.max_points
    passed = grade is not None and abs(grade - test.expected_score) <= TOLERANCE_FRACTION * max_points + 1e-9
    row = {
        "test_number": number,
        "category": test.category,
        "subject": test.question.subject_name,
        "question": test.question.question_text,
        "student_answer": test.test_answer,
        "max_points": max_points,
        "expected_score": test.expected_score,
        "model_grade": "" if grade is None else grade,
        "difference": "" if grade is None else round(grade - test.expected_score, 2),
        "confidence": blank(result.get("confidence")),
        "needs_review": blank(result.get("needs_review")),
        "review_reasons": "; ".join(result.get("review_reasons") or []),
        "rubric_breakdown": json.dumps(result["rubric_breakdown"], ensure_ascii=False) if "rubric_breakdown" in result else "",
        "student_feedback": result.get("student_feedback", ""),
        "instructor_feedback": result.get("instructor_feedback", ""),
        "status": result["status"],
        "error": blank(result.get("error")),
        "model_attempts": blank(result.get("attempts")),  # model requests the client needed (1 = no retry)
        "attempts": attempts,
        "passed": "PASS" if passed else "FAIL",
    }
    # the score the model gave each criterion, in its own column
    for entry in result.get("rubric_breakdown") or []:
        row[f"{entry['criteria_id']}_score"] = entry["score"]
    return row


def main():
    selected = [(n, t) for n, t in enumerate(tests, start=1) if ONLY_TESTS is None or n in ONLY_TESTS]
    output_file = next_output_file("arabic_text_results" if ARABIC else "text_results")
    rows = []
    print(f"Running {len(selected)} of {len(tests)} samples, results will be written to {output_file}\n")

    # utf-8 with BOM so Excel on Windows shows symbols like pi correctly; rows are written one by one,
    # so an interrupted run keeps everything finished so far
    with open(output_file, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        try:
            for position, (number, test) in enumerate(selected):
                result, attempts = grade_one(test)
                row = build_row(number, test, result, attempts)
                rows.append(row)
                writer.writerow(row)
                file.flush()

                got = row["model_grade"] if row["model_grade"] != "" else result["status"]
                print(f"{number:>2}/{len(tests)} {test.category:<28} expected {test.expected_score:<4} got {got!s:<17} {row['passed']}")
                if position < len(selected) - 1:
                    time.sleep(SLEEP_SECONDS)
        except KeyboardInterrupt:
            print("\nInterrupted, keeping the rows written so far.")

    summarize(rows, output_file)


def summarize(rows, output_file):
    if not rows:
        return
    passed = sum(r["passed"] == "PASS" for r in rows)
    graded = [r for r in rows if r["status"] == "graded"]
    print(f"\nPassed {passed} of {len(rows)} ({passed / len(rows):.0%}), tolerance {TOLERANCE_FRACTION:.0%} of max_points")
    if graded:
        error = sum(abs(r["difference"]) for r in graded) / len(graded)
        print(f"Mean absolute error on graded tests: {error:.2f} points | needs_review: {sum(bool(r['needs_review']) for r in graded)} of {len(graded)}")
    retried = sum(r["model_attempts"] not in ("", 1) for r in rows)
    print(f"Injection flagged: {sum(r['status'] == 'injection_flagged' for r in rows)} | failed (sent to review): {sum(r['status'] == 'failed' for r in rows)} | errors: {sum(r['status'] == 'error' for r in rows)} | needed a model retry: {retried}")

    by_category = defaultdict(lambda: [0, 0])
    for r in rows:
        by_category[r["category"]][0] += r["passed"] == "PASS"
        by_category[r["category"]][1] += 1
    print("\nBy category:")
    for category, (ok, total) in sorted(by_category.items(), key=lambda item: item[1][0] / item[1][1]):
        print(f"  {category:<28} {ok}/{total}")
    print(f"\nResults saved to {output_file}")


main()
