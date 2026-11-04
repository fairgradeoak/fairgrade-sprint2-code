# Runs a student's code against all test cases of a question with ONE Judge0 batch call, then collects the
# results by polling. Talks to Judge0 over its REST api directly so every call has a timeout and every
# submission has CPU, memory and output limits.
#
# Settings come from the environment (same names the judge0 python package used):
#   JUDGE0_CE_ENDPOINT      base url of Judge0, for example http://localhost:2358
#   JUDGE0_CE_AUTH_HEADERS  optional, a json object of headers to send, for example {"X-Auth-Token": "..."}

# Built-in
import json
import os
import time

# External
import requests
from dotenv import load_dotenv

# Project
from fairgrade import encoder
load_dotenv()

# limits applied to every single run (one test case)
CPU_TIME_LIMIT_SECONDS = 2         # cpu time, an infinite loop stops here (status "Time Limit Exceeded")
WALL_TIME_LIMIT_SECONDS = 5        # real time, catches programs that sleep or wait for input
MEMORY_LIMIT_KB = 128000           # about 128 MB
MAX_OUTPUT_KB = 1024               # biggest file (and so biggest output) a run may write, a huge print stops here

REQUEST_TIMEOUT_SECONDS = 5        # one http call to Judge0
POLL_WAITS_SECONDS = (1,)          # seconds to wait before each check, the last value repeats
MAX_BATCH_SIZE = 20                # Judge0's default limit of submissions per batch call

STATUS_IN_QUEUE = 1
STATUS_PROCESSING = 2


class Judge0Error(Exception):
    pass


def settings():
    endpoint = os.getenv("JUDGE0_CE_ENDPOINT")
    if(not endpoint):
        raise Judge0Error("JUDGE0_CE_ENDPOINT is not set")

    headers = {"Content-Type": "application/json"}
    raw_headers = os.getenv("JUDGE0_CE_AUTH_HEADERS")
    if(raw_headers):
        try:
            headers.update(json.loads(raw_headers))
        except ValueError:
            raise Judge0Error("JUDGE0_CE_AUTH_HEADERS is not a valid json object")

    return endpoint.rstrip("/"), headers


# language ids reach this point as int, or as the judge0 package's enum (an int subclass)
def language_number(language_id):
    return int(getattr(language_id, "value", language_id))


def request(step, method, url, headers, timeout, **kwargs):
    try:
        response = requests.request(method, url, headers=headers, timeout=timeout, **kwargs)
    except requests.RequestException as error:
        raise Judge0Error(f"{type(error).__name__} while {step} (waited up to {timeout:.0f} s)")
    if(response.status_code >= 400):
        raise Judge0Error(f"Judge0 answered http {response.status_code}")
    try:
        return response.json()
    except ValueError:
        raise Judge0Error("Judge0 answered something that is not json")


# test_cases: list of (stdin, expected_output). Returns one status description per test case, in order,
# for example "Accepted", "Wrong Answer", "Time Limit Exceeded", "Compilation Error", "Runtime Error (NZEC)".
# A program that loops forever, does not compile, crashes or prints too much only fails its own tests.
# Raises Judge0Error when Judge0 cannot be reached or does not finish inside `deadline` (a Deadline).
def run_tests(language_id, source_code, test_cases, deadline):
    if(len(test_cases) > MAX_BATCH_SIZE):
        raise Judge0Error(f"too many test cases, the limit is {MAX_BATCH_SIZE}")

    if(deadline.remaining() < 1):
        raise Judge0Error("no time left to run the test cases")

    endpoint, headers = settings()
    language = language_number(language_id)

    submissions = [{"language_id": language,
                    "source_code": encoder.encode64(source_code),
                    "stdin": encoder.encode64(stdin),
                    "expected_output": encoder.encode64(expected_output),
                    "cpu_time_limit": CPU_TIME_LIMIT_SECONDS,
                    "wall_time_limit": WALL_TIME_LIMIT_SECONDS,
                    "memory_limit": MEMORY_LIMIT_KB,
                    "max_file_size": MAX_OUTPUT_KB}
                   for stdin, expected_output in test_cases]

    batch_url = f"{endpoint}/submissions/batch?base64_encoded=true"
    try:
        created = request("sending the batch", "POST", batch_url, headers, deadline.cap(REQUEST_TIMEOUT_SECONDS),
                          json={"submissions": submissions})
    except Judge0Error as error:
        # the first call after a pause sometimes finds the connection closed. It fails at once, so one more try costs almost nothing.
        if("ConnectionError" not in str(error) or deadline.remaining() < 3):
            raise
        created = request("sending the batch", "POST", batch_url, headers, deadline.cap(REQUEST_TIMEOUT_SECONDS),
                          json={"submissions": submissions})
    tokens = [item.get("token") for item in created]
    if(len(tokens) != len(test_cases) or not all(tokens)):
        raise Judge0Error("Judge0 rejected the batch of test cases")

    poll_url = f"{endpoint}/submissions/batch?base64_encoded=true&fields=token,status&tokens={','.join(tokens)}"
    waits = list(POLL_WAITS_SECONDS)
    while True:
        wait = waits.pop(0) if len(waits) > 1 else waits[0]
        if(deadline.remaining() <= wait):
            raise Judge0Error("Judge0 did not finish the test cases in time")
        time.sleep(wait)

        results = request("collecting results", "GET", poll_url, headers, deadline.cap(REQUEST_TIMEOUT_SECONDS))["submissions"]
        by_token = {item["token"]: item["status"] for item in results}
        if(all(by_token.get(token) and by_token[token]["id"] not in (STATUS_IN_QUEUE, STATUS_PROCESSING) for token in tokens)):
            return [by_token[token]["description"] for token in tokens]
