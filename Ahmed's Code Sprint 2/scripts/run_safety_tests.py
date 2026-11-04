# for importing
import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

# Checks that dangerous or broken student code only fails its own tests and never crashes or hangs the grading.
# It talks to Judge0 directly (judge0_client.run_tests, the same call the grader makes, with the same limits and
# the same 11 s time slice), so it does not use any Gemini quota.
# For every case it prints the status Judge0 gave each test, how long it took, and PASS or FAIL.
#   PASS = the call returned normally, in time, and every test has the expected outcome
#   FAIL = Judge0Error (the whole call failed or ran out of time) or an unexpected status
# Needs Judge0 running. Run it from the project root: python scripts/run_safety_tests.py
import time

from fairgrade import judge0_client
from fairgrade.time_budget import Deadline

# ---------------------------------------------------------------- settings
JUDGE0_SLICE_SECONDS = 11   # the time the grader gives the test runs (GeminiClient.JUDGE0_BUDGET_SECONDS)
PAUSE_SECONDS = 3           # between cases, so leftover runs of one case do not slow the next
PAUSE_AFTER_SLOW_SECONDS = 25   # after a case that may leave many runs queued in Judge0

sys.stdout.reconfigure(encoding="utf-8")

PYTHON = 71   # Python 3
CPP = 54      # C++ (GCC)
# a correct C++ program: echoes the line it is given (every C++ test is compiled again by Judge0 before it runs)
ECHO_CPP = "#include <iostream>\n#include <string>\nint main() { std::string line; std::getline(std::cin, line); std::cout << line << std::endl; return 0; }\n"

# (name, language id, code, number of test cases, expect)
# expect "accepted": every test must be Accepted. expect "failed": every test must get any status except Accepted.
CASES = [
    ("control: correct program", PYTHON, "print(input())", 3, "accepted"),
    ("python correct, 9 tests", PYTHON, "print(input())", 9, "accepted"),
    ("c++ correct, 9 tests", CPP, ECHO_CPP, 9, "accepted"),
    ("infinite loop", PYTHON, "while True:\n    pass\n", 1, "failed"),
    ("infinite loop, 7 tests", PYTHON, "while True:\n    pass\n", 7, "failed"),
    ("python syntax error", PYTHON, "print('a'\n", 3, "failed"),
    ("c++ compile error", CPP, "int main() { return undefined_name; }\n", 3, "failed"),
    ("huge print, endless", PYTHON, "while True:\n    print('x' * 1000)\n", 1, "failed"),
    ("huge print, 50 MB at once", PYTHON, "print('x' * 50_000_000)\n", 1, "failed"),
    ("memory hog, 1 GB", PYTHON, "data = bytearray(1024 * 1024 * 1024)\nprint(len(data))\n", 1, "failed"),
]


def run_case(name, language, code, count, expect):
    # every test sends a different line, the control program echoes it back
    tests = [(f"line {number}", f"line {number}") for number in range(1, count + 1)]
    started = time.perf_counter()
    try:
        statuses = judge0_client.run_tests(language, code, tests, Deadline(JUDGE0_SLICE_SECONDS))
    except Exception as error:
        seconds = time.perf_counter() - started
        print(f"FAIL  {name:<28} {seconds:5.1f} s  the whole call failed: {error}")
        return False, seconds

    seconds = time.perf_counter() - started
    if(expect == "accepted"):
        passed = all(status == "Accepted" for status in statuses)
    else:
        passed = all(status != "Accepted" for status in statuses)

    shown = ", ".join(sorted(set(statuses)))
    print(f"{'PASS' if passed else 'FAIL'}  {name:<28} {seconds:5.1f} s  {len(statuses)} tests: {shown}")
    return passed, seconds


results = []
for number, (name, language, code, count, expect) in enumerate(CASES):
    passed, _ = run_case(name, language, code, count, expect)
    results.append(passed)
    if(number < len(CASES) - 1):
        time.sleep(PAUSE_AFTER_SLOW_SECONDS if count > 1 and expect == "failed" else PAUSE_SECONDS)

print(f"\n{sum(results)} of {len(results)} cases passed")
