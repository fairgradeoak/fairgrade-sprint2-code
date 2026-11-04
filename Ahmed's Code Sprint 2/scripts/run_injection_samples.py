# for importing
import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

# Runs every SampleInjectionCase in `tests` (sample_injection_cases.py) through the real injection check
# (PromptGenerator.check_prompt_injection + GeminiClient.check_injection, with its retries) and writes one
# CSV row per case. Only the injection check runs, nothing is graded, so each case makes a single Gemini call.
# Run it from the project root: python scripts/run_injection_samples.py
import csv
import time
from collections import defaultdict
from datetime import datetime

from fairgrade.gemini_client import GeminiClient, GradingError
from fairgrade.log_config import setup_logging
from fairgrade.prompt_generator import PromptGenerator

# add the word arabic to run the Arabic samples instead: python scripts/run_injection_samples.py arabic
ARABIC = "arabic" in sys.argv[1:]
if ARABIC:
    from samples.sample_arabic import injection_tests as tests
else:
    from samples.sample_injection_cases import tests

# ---------------------------------------------------------------- settings
SLEEP_SECONDS = 5          # pause between cases (one API call each); raise it if you hit rate limits
ONLY_TESTS = None          # e.g. [8, 9] to run only those cases (numbered 1-15 as in sample_injection_cases.py)

COLUMNS = ["test_number", "category", "kind", "question_type", "student_answer", "expected", "got",
           "model_attempts", "status", "error", "passed"]

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


def label(is_injection):
    return "injection" if is_injection else "not injection"


def check_one(test):
    """Run one case through the injection check. Returns (flagged or None, attempts, status, error);
    status is ok, failed (the client gave up after its own retries, the submission would go to review)
    or error (an unexpected exception)."""
    try:
        flagged, attempts = GeminiClient.check_injection(PromptGenerator(test.question, test.test_answer))
        return flagged, attempts, "ok", ""
    except GradingError as error:
        return None, error.attempts, "failed", short(error)
    except Exception as error:  # anything unexpected
        return None, 0, "error", f"{type(error).__name__}: {short(error)}"


def build_row(number, test, flagged, attempts, status, error):
    return {
        "test_number": number,
        "category": test.category,
        "kind": "malicious" if test.expected_injection else "benign",
        "question_type": "code" if hasattr(test.question, "language_id") else "text",
        "student_answer": test.test_answer,
        "expected": label(test.expected_injection),
        "got": "" if flagged is None else label(flagged),
        "model_attempts": attempts,
        "status": status,
        "error": error,
        "passed": "PASS" if flagged is not None and flagged == test.expected_injection else "FAIL",
    }


def main():
    selected = [(n, t) for n, t in enumerate(tests, start=1) if ONLY_TESTS is None or n in ONLY_TESTS]
    output_file = next_output_file("arabic_injection_results" if ARABIC else "injection_results")
    rows = []
    print(f"Running {len(selected)} of {len(tests)} injection cases, results will be written to {output_file}\n")

    # utf-8 with BOM so Excel on Windows shows non-english text correctly; rows are written one by one,
    # so an interrupted run keeps everything finished so far
    with open(output_file, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        try:
            for position, (number, test) in enumerate(selected):
                row = build_row(number, test, *check_one(test))
                rows.append(row)
                writer.writerow(row)
                file.flush()

                print(f"{number:>2}/{len(tests)} {test.category:<30} expected {row['expected']:<14} got {row['got'] or row['status']:<14} {row['passed']}")
                if position < len(selected) - 1:
                    time.sleep(SLEEP_SECONDS)
        except KeyboardInterrupt:
            print("\nInterrupted, keeping the rows written so far.")

    summarize(rows, output_file)


def summarize(rows, output_file):
    if not rows:
        return
    passed = sum(r["passed"] == "PASS" for r in rows)
    benign = [r for r in rows if r["kind"] == "benign"]
    malicious = [r for r in rows if r["kind"] == "malicious"]
    false_positives = [r for r in benign if r["got"] == "injection"]
    false_negatives = [r for r in malicious if r["got"] == "not injection"]
    unanswered = [r for r in rows if r["status"] != "ok"]

    print(f"\nPassed {passed} of {len(rows)} ({passed / len(rows):.0%})")
    print(f"False positives (normal submissions flagged): {len(false_positives)} of {len(benign)}")
    print(f"False negatives (injections missed, the dangerous kind): {len(false_negatives)} of {len(malicious)}")
    print(f"No verdict (failed or error, would go to instructor review): {len(unanswered)}")
    print(f"Needed a model retry: {sum(r['model_attempts'] not in ('', 0, 1) for r in rows)}")

    for title, group in (("Wrongly flagged", false_positives), ("Missed", false_negatives)):
        if group:
            print(f"\n{title}:")
            for r in group:
                print(f"  {r['test_number']:>2} {r['category']}")

    by_category = defaultdict(lambda: [0, 0])
    for r in rows:
        by_category[r["category"]][0] += r["passed"] == "PASS"
        by_category[r["category"]][1] += 1
    print("\nBy category:")
    for category, (ok, total) in sorted(by_category.items(), key=lambda item: item[1][0] / item[1][1]):
        print(f"  {category:<30} {ok}/{total}")
    print(f"\nResults saved to {output_file}")


main()
