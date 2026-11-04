# for importing
import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

# Asks Google which Gemini "flash" models this API key can use, then times the same small prompt on each one,
# with the default settings and with minimal thinking. A model or setting that does not work is reported and skipped.
# Run it from the project root: python scripts/diagnose_models.py
import time

from google.genai import types

from fairgrade.gemini_client import GeminiClient
from samples.sample_text_questions import tests as text_tests
from fairgrade.prompt_generator import PromptGenerator

# ---------------------------------------------------------------- settings
TIMEOUT_SECONDS = 30      # long enough to show the real duration without waiting forever
SKIP_WORDS = ("image", "tts", "audio", "live", "embedding", "robotics", "computer", "veo", "imagen", "learnlm", "gemma")

sys.stdout.reconfigure(encoding="utf-8")

sample = text_tests[0]
PROMPT = PromptGenerator(sample.question, sample.test_answer).check_prompt_injection()  # the real injection check prompt

SETTINGS = {
    "default": None,
    "thinking minimal": types.ThinkingConfig(thinking_level="minimal"),
}


def usable_models():
    names = []
    for model in GeminiClient.client.models.list():
        name = model.name.removeprefix("models/")
        actions = model.supported_actions or []
        if("flash" in name and "generateContent" in actions and not any(word in name for word in SKIP_WORDS)):
            names.append(name)
    return sorted(set(names) | {GeminiClient.gemini_model})


models = usable_models()
print(f"models found: {', '.join(models)}\n")

for model in models:
    for setting_name, thinking in SETTINGS.items():
        started = time.perf_counter()
        try:
            config = types.GenerateContentConfig(http_options=types.HttpOptions(timeout=TIMEOUT_SECONDS * 1000),
                                                 thinking_config=thinking)
            reply = GeminiClient.client.models.generate_content(model=model, contents=PROMPT, config=config).text
            outcome = f"ok, replied {str(reply).strip()[:10]!r}"
        except Exception as error:
            outcome = f"failed, {type(error).__name__}: {' '.join(str(error).split())[:90]}"
        print(f"{model:<34} {setting_name:<17} {time.perf_counter() - started:5.1f} s  {outcome}")
