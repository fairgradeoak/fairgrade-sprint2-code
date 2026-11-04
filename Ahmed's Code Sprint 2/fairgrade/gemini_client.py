# External 
from google import genai
from google.genai import types

# Built-in
from dotenv import load_dotenv
import os
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

# Project
from fairgrade.ai_response import AiResponse
from fairgrade.prompt_generator import PromptGenerator
from fairgrade.grader import Grader
from fairgrade import judge0_client
from fairgrade.time_budget import Deadline
from fairgrade.safe_errors import describe_error

logger = logging.getLogger("fairgrade.gemini")


# raised when the model could not give a usable reply even after retrying
class GradingError(Exception):
    def __init__(self, message, attempts):
        super().__init__(message)
        self.attempts = attempts


class GeminiClient:
    # fetching environment variables
    # initializing client
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL")
    client = genai.Client(api_key=api_key)

    MAX_ATTEMPTS = 2        # model requests per step (injection check, grading) before giving up and sending it to review
    RETRY_WAIT_SECONDS = 1  # pause before asking again, grows with every failed attempt (1 s, then 2 s)

    # One grading request (injection check, test runs, grading) must finish inside GRADING_BUDGET_SECONDS, the API
    # gateway cuts requests off at 29 s. Every step takes what it needs from the same Deadline.
    GRADING_BUDGET_SECONDS = 19      # one second under the 20 s target, thread and sleep timing can overshoot slightly
    MODEL_TIMEOUT_SECONDS = 10       # longest wait for one model reply
    MIN_SDK_DEADLINE_SECONDS = 10    # Gemini rejects request deadlines shorter than 10 s
    THINKING_LEVEL = "minimal"        # the default level made this model take about 15 s even for a one-character reply
    MIN_MODEL_SECONDS = 2            # not worth asking the model with less time than this left
    JUDGE0_BUDGET_SECONDS = 11       # longest the test runs may take in total (about 1 s per test case, they run one at a time)
    GRADING_RESERVE_SECONDS = 6      # time kept free for the grading request after the test runs

    # this is the only method that directly calls the api
    @classmethod
    def send_request(cls, prompt, timeout=MODEL_TIMEOUT_SECONDS):
        # the sdk timeout is in milliseconds and Gemini refuses anything under 10 s. The call also runs in a thread
        # that is only waited for `timeout` seconds, so the real limit is `timeout` even when it is shorter than that.
        sdk_timeout = max(timeout, cls.MIN_SDK_DEADLINE_SECONDS)
        config = types.GenerateContentConfig(http_options=types.HttpOptions(timeout=int(sdk_timeout * 1000)),
                                             thinking_config=types.ThinkingConfig(thinking_level=cls.THINKING_LEVEL))
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(cls.client.models.generate_content, model=cls.gemini_model, contents=prompt, config=config)
            try:
                response = future.result(timeout=timeout)
            except FutureTimeout:
                raise TimeoutError(f"the model did not reply within {timeout:.0f} seconds")
        finally:
            executor.shutdown(wait=False)
        # .text is None when the reply was blocked or empty
        if(not response.text):
            raise ValueError("the model returned an empty reply")
        return response.text.strip()

    # Sends a prompt and passes the reply through `parse`. When the request fails (network, rate limit, empty reply)
    # or `parse` rejects the reply (bad json, failed validation), the model is asked again, up to MAX_ATTEMPTS times.
    # Returns (what parse returned, number of attempts it took). Raises GradingError when every attempt failed.
    @classmethod
    def request_with_retries(cls, prompt, parse, deadline):
        last_error = None
        attempts_made = 0
        for attempt in range(1, cls.MAX_ATTEMPTS + 1):
            timeout = deadline.cap(cls.MODEL_TIMEOUT_SECONDS)
            if(timeout < cls.MIN_MODEL_SECONDS):
                raise GradingError(f"time budget used up after {attempts_made} model attempts, last error: {last_error}", attempts_made)

            attempts_made = attempt
            try:
                return parse(cls.send_request(prompt, timeout)), attempt
            except Exception as error:
                # describe_error keeps the student's answer and the model's reply out of the message
                last_error = describe_error(error)
                logger.warning("model attempt %d/%d failed: %s", attempt, cls.MAX_ATTEMPTS, last_error)
                if(attempt < cls.MAX_ATTEMPTS):
                    time.sleep(deadline.cap(cls.RETRY_WAIT_SECONDS * attempt))

        raise GradingError(f"no usable model reply after {cls.MAX_ATTEMPTS} attempts, last error: {last_error}", attempts_made)

    # the injection check must answer exactly "0" (safe) or "1" (injection), anything else is asked again.
    # If the model keeps answering something else (for example because the submission talked it into it),
    # the submission ends up in the failed state and goes to the instructor, never silently graded.
    @staticmethod
    def parse_injection_verdict(reply):
        verdict = reply.strip()
        if(verdict not in ("0", "1")):
            raise ValueError(f"the injection check should answer 0 or 1, received {len(verdict)} characters")
        return verdict

    # returns (True when the submission was flagged as an injection, number of attempts it took)
    @classmethod
    def check_injection(cls, prompts, deadline=None):
        deadline = deadline or Deadline(cls.GRADING_BUDGET_SECONDS)
        verdict, attempts = cls.request_with_retries(prompts.check_prompt_injection(), cls.parse_injection_verdict, deadline)
        return verdict == "1", attempts

    # asks the model to grade, retrying until the reply is valid json, passes AiResponse and matches the rubric ids exactly
    @classmethod
    def grade_with_retries(cls, grading_prompt, question, deadline, test_statuses=None):
        def parse(reply):
            ai_assessment = AiResponse.from_model_reply(reply, criteria_count=len(question.rubric))
            return Grader(ai_assessment=ai_assessment, question_rubric=question.rubric, max_points=question.max_points,
                          test_statuses=test_statuses)

        grader, attempts = cls.request_with_retries(grading_prompt, parse, deadline)
        grader.attempts = attempts
        return grader.final_assessment()

    # The injection check and the grading start at the same time, so a slow model reply is waited for once and not twice.
    # The grade is only returned when the check says the submission is safe, a flagged submission is never graded.
    # If the check itself cannot be completed the submission is not graded either (GradingError, so the result is failed).
    @classmethod
    def grade_with_injection_check(cls, prompts, deadline, grade, max_points):
        pool = ThreadPoolExecutor(max_workers=2)
        try:
            injection = pool.submit(cls.check_injection, prompts, deadline)
            grading = pool.submit(grade)
            is_injection, _ = injection.result()
            if(is_injection):
                return Grader.injection_result(max_points)
            return grading.result()
        finally:
            pool.shutdown(wait=False)

    @classmethod
    def review_text_submission(cls, question, answer, deadline=None):
        deadline = deadline or Deadline(cls.GRADING_BUDGET_SECONDS)
        # object to generate prompts
        prompts = PromptGenerator(question,answer)

        try:
            return cls.grade_with_injection_check(prompts, deadline,
                                                  lambda: cls.grade_with_retries(prompts.get_text_grading_prompt(), question, deadline),
                                                  question.max_points)

        except GradingError as error:
            return Grader.failed_result(question.max_points, str(error), attempts=error.attempts)

    # a test case can be a dict {"input", "expected_output", "hidden"} (database format) or a pair (input, expected_output)
    @staticmethod
    def split_test_case(test_case):
        if(isinstance(test_case, dict)):
            return str(test_case["input"]), str(test_case["expected_output"])
        return str(test_case[0]), str(test_case[1])

    # runs every test case in judge0 (one batch call) and builds a dictionary of test cases and their status to be sent to the ai
    @classmethod
    def run_test_cases(cls, code_question, submitted_code, deadline):
        test_cases = [cls.split_test_case(test_case) for test_case in code_question.test_cases]

        # the test runs get their own slice of the budget so the grading request that follows always has time left
        judge0_deadline = Deadline(min(cls.JUDGE0_BUDGET_SECONDS, deadline.remaining() - cls.GRADING_RESERVE_SECONDS))
        # language_id is a plain judge0 integer (for example 71 for python)
        tests_status = judge0_client.run_tests(code_question.language_id, submitted_code, test_cases, judge0_deadline)

        tests_report = {}
        for i, (stdin, expected_output) in enumerate(test_cases):
            tests_report[f"test_{i + 1}"] = {
                "test_case": {
                    "input": stdin,
                    "expected_output": expected_output
                },
                "status": tests_status[i]
            }

        return tests_report

    @classmethod
    def review_code_submission(cls, code_question, submitted_code, deadline=None):
        deadline = deadline or Deadline(cls.GRADING_BUDGET_SECONDS)
        # object to generate prompts
        prompts = PromptGenerator(code_question, submitted_code)

        def grade():
            # judge0 problems (network, bad language id, too slow) are not the model's fault, so no retry here:
            # the submission goes straight to the instructor
            try:
                tests_report = cls.run_test_cases(code_question, submitted_code, deadline)
            except Exception as error:
                reason = describe_error(error)
                logger.warning("test runs failed: %s", reason)
                return Grader.failed_result(code_question.max_points, f"code execution failed, {reason}", attempts=0)

            # the status of every test goes to the grader too, which flags a grade that contradicts the tests
            test_statuses = [entry["status"] for entry in tests_report.values()]
            return cls.grade_with_retries(prompts.get_code_grading_prompt(tests_report), code_question, deadline, test_statuses)

        try:
            # the test runs happen in Judge0's sandbox while the injection check is being answered
            return cls.grade_with_injection_check(prompts, deadline, grade, code_question.max_points)

        except GradingError as error:
            return Grader.failed_result(code_question.max_points, str(error), attempts=error.attempts)
