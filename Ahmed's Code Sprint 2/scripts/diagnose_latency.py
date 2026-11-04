# for importing
import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

# Times the slow parts one by one, with long timeouts, to see where the 20 seconds go:
#   1. Gemini: one tiny prompt, then the real injection check and the real grading prompt of a sample question
#   2. Judge0: a batch of 7 trivial test cases, three times
# Run it from the project root: python scripts/diagnose_latency.py
import time

from fairgrade import judge0_client
from fairgrade.gemini_client import GeminiClient
from fairgrade.prompt_generator import PromptGenerator
from fairgrade.time_budget import Deadline
from samples.sample_text_questions import tests as text_tests

sys.stdout.reconfigure(encoding="utf-8")

print(f"model: {GeminiClient.gemini_model}")


def time_model(label, prompt):
    started = time.perf_counter()
    try:
        reply = GeminiClient.send_request(prompt, timeout=60)
        outcome = f"ok, {len(reply)} characters"
    except Exception as error:
        outcome = f"failed, {type(error).__name__}: {' '.join(str(error).split())[:120]}"
    print(f"gemini {label:<18} {time.perf_counter() - started:5.1f} s  {outcome}")


time_model("tiny prompt", "Answer with the single character 0.")

sample = text_tests[0]
prompts = PromptGenerator(sample.question, sample.test_answer)
time_model("injection check", prompts.check_prompt_injection())
time_model("text grading", prompts.get_text_grading_prompt())

print()
tests = [(str(number), str(number)) for number in range(7)]
code = "print(input())"
for run in range(1, 4):
    started = time.perf_counter()
    try:
        statuses = judge0_client.run_tests(71, code, tests, Deadline(60))
        outcome = f"ok, {statuses.count('Accepted')} of {len(statuses)} accepted"
    except Exception as error:
        outcome = f"failed, {error}"
    print(f"judge0 batch of 7 (run {run}) {time.perf_counter() - started:5.1f} s  {outcome}")
