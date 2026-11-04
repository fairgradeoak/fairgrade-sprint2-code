import time


# One grading request gets one Deadline. Every slow step (Gemini call, Judge0 call, waiting between retries)
# asks it how much time is left, so the whole request ends before the API gateway cuts it off.
class Deadline:
    def __init__(self, seconds):
        self.end = time.monotonic() + seconds

    def remaining(self):
        return max(0.0, self.end - time.monotonic())

    # the shorter of `seconds` and what is left
    def cap(self, seconds):
        return min(seconds, self.remaining())
