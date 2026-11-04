# for importing
import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

# Shows which sample answers the needs_review triggers flag, using the saved results of run_samples.py (text) and
# run_code_samples.py (code). It applies the same rules the grader uses (fairgrade.grader.trigger_reasons) to the
# confidence, criteria scores, grade and tests passed stored in each row, so it needs no Gemini and no Judge0.
# For every file it prints the answers flagged, how many answers are flagged, and which FAIL rows (the model's grade
# was more than 10% of the maximum away from the expected score) are flagged and which are missed.
# Run it from the project root, after at least one run of each runner:
#   python scripts/analyze_review.py                 uses the newest text and code results in results/
#   python scripts/analyze_review.py results/text_results_2026-10-30_1.csv     uses the file(s) you name
import csv
import json

from fairgrade.grader import trigger_reasons

sys.stdout.reconfigure(encoding="utf-8")

RESULTS_DIR = root / "results"


def newest(prefix):
    files = sorted(RESULTS_DIR.glob(f"{prefix}_*.csv"), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def reasons_for(row, is_code):
    """The reasons the grader's triggers give for one saved row (empty when it is not flagged)."""
    scores = [float(entry["score"]) for entry in json.loads(row["rubric_breakdown"])]
    fraction = round(float(row["model_grade"]) / float(row["max_points"]), 4)
    passed = total = None
    if(is_code):
        passed, total = (int(part) for part in row["tests_passed"].split("/")) if row["tests_passed"] else (0, 0)   # (0, 0) = no tests ran
    return trigger_reasons(float(row["confidence"]), scores, fraction, passed, total)


def analyze(path, is_code):
    rows = [row for row in read_rows(path) if row["status"] == "graded" and row["model_grade"] != ""]
    print(f"\n=== {'code' if is_code else 'text'} samples: {path.name} ({len(rows)} graded) ===")

    flagged, missed_failures, caught_failures = [], [], []
    for row in rows:
        reasons = reasons_for(row, is_code)
        if(reasons):
            flagged.append((row, reasons))
        if(row["passed"] == "FAIL"):
            (caught_failures if reasons else missed_failures).append(row)

    print(f"\nFlagged for review: {len(flagged)} of {len(rows)} ({len(flagged) / max(len(rows), 1):.0%})")
    for row, reasons in flagged:
        tests = f" tests {row['tests_passed']}" if is_code else ""
        print(f"  {int(row['test_number']):>2} {row['category']:<28} expected {row['expected_score']:<5} got {row['model_grade']:<5}{tests}  <- {'; '.join(reasons)}")

    failures = len(caught_failures) + len(missed_failures)
    print(f"\nFailures (grade off by more than 10%): {failures}, flagged {len(caught_failures)}, missed {len(missed_failures)}")
    for row in caught_failures:
        print(f"  flagged  {int(row['test_number']):>2} {row['category']:<28} expected {row['expected_score']:<5} got {row['model_grade']}")
    for row in missed_failures:
        print(f"  MISSED   {int(row['test_number']):>2} {row['category']:<28} expected {row['expected_score']:<5} got {row['model_grade']}")


def main():
    named = [Path(argument) for argument in sys.argv[1:]]
    if(named):
        for path in named:
            analyze(path, is_code=path.name.startswith("code"))
        return

    text_file, code_file = newest("text_results"), newest("code_results")
    if(text_file is None and code_file is None):
        print("No results found in results/. Run scripts/run_samples.py and scripts/run_code_samples.py first.")
        return
    if(text_file):
        analyze(text_file, is_code=False)
    if(code_file):
        analyze(code_file, is_code=True)


main()
