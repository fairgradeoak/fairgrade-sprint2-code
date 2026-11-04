# for importing
import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

# Throwaway check: do symbols like pi, squared and approx reach the model as real characters
# (not as \uXXXX escapes) in the grading prompt of every sample? Run it from the project root.

from samples.sample_text_questions import tests
from fairgrade.prompt_generator import PromptGenerator

LIVE = False  # True = also send the sample with the most symbols to Gemini (2 API calls)

sys.stdout.reconfigure(encoding="utf-8")  # so printing symbols never crashes a Windows console

problems = 0
symbol_tests = []

for number, test in enumerate(tests, start=1):
    question = test.question
    prompt = PromptGenerator(question, test.test_answer).get_text_grading_prompt()

    source = " ".join([question.subject_name, question.subject_description, question.question_text,
                       question.model_answer, test.test_answer] + [c["requirement"] for c in question.rubric])
    symbols = sorted({ch for ch in source if ord(ch) > 127})
    if not symbols:
        continue

    symbol_tests.append((test, symbols))
    missing = [ch for ch in symbols if ch not in prompt]
    escaped = "\\u" in prompt
    status = "OK" if not missing and not escaped else "PROBLEM"
    problems += status == "PROBLEM"
    print(f"{number:>2} {test.category:<28} {status:<8} symbols: {' '.join(symbols)}")

print(f"\n{len(symbol_tests)} of {len(tests)} samples contain non-ASCII symbols, {problems} with problems")
print("All good: symbols arrive as real characters." if problems == 0 else "Problem: symbols are being escaped (check ensure_ascii=False in get_text_grading_prompt).")

if symbol_tests:
    showcase = max(symbol_tests, key=lambda item: len(item[1]))[0]  # the sample with the most symbols
    prompt = PromptGenerator(showcase.question, showcase.test_answer).get_text_grading_prompt()
    data_part = prompt.split("here is the given data to grade:", 1)[1]  # skip the instructions, which contain a dash of their own
    line = next(l for l in data_part.splitlines() if any(ord(ch) > 127 for ch in l))
    print("\nWhat the model sees:", line.strip())

    if LIVE:
        from fairgrade.gemini_client import GeminiClient
        print("\nLive result:")
        print(GeminiClient.review_text_submission(showcase.question, showcase.test_answer))
