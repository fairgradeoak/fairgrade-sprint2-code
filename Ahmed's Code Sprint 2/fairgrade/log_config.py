import logging
import os
import sys

MAX_MESSAGE_LENGTH = 300


# Last line of defence: no log line is ever longer than this, so even a mistake somewhere cannot
# write a whole answer or model reply into the logs.
class ShortenMessages(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        if(len(message) > MAX_MESSAGE_LENGTH):
            record.msg = message[:MAX_MESSAGE_LENGTH] + "..."
            record.args = None
        return True


# Call once at start up (the sample runners do). The level comes from the LOG_LEVEL environment variable, INFO by default.
# Where the logs go (console, CloudWatch...) is decided by the application that uses the grader,
# the grader itself only creates loggers named "fairgrade.*".
def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    handler.addFilter(ShortenMessages())

    logger = logging.getLogger("fairgrade")
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    logger.handlers = [handler]
    logger.propagate = False
