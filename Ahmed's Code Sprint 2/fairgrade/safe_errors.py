from pydantic import ValidationError

MAX_LENGTH = 200


# Turns an exception into a short text that is safe to log and to return in the result's "error" field.
# Error messages can contain the data that caused them (pydantic prints the input value, a library may quote
# the reply), and here that data is the student's answer or the model's reply, which must never reach a log.
# So only these parts are used:
#   - validation errors: where the problem is and its message, never the input value
#   - Gemini api errors: the http code and status (the message too for 400 and 404, which are about our request)
#   - errors raised by this project (ValueError and TimeoutError from our own checks, Judge0Error, GradingError): their message,
#     which is written without any model or student text
#   - anything else: only the name of the error
def describe_error(error):
    name = type(error).__name__

    if(isinstance(error, ValidationError)):
        problems = [f"{'.'.join(str(part) for part in item.get('loc', ()))}: {item.get('msg', '')}" for item in error.errors()]
        detail = "; ".join(problems)
    elif(hasattr(error, "code") and hasattr(error, "status")):
        detail = f"{error.code} {error.status}"
        if(error.code in (400, 404)):
            detail += f", {getattr(error, 'message', '')}"
    elif(isinstance(error, (ValueError, TimeoutError)) or type(error).__module__.split(".")[-1] in ("gemini_client", "judge0_client")):
        detail = str(error)
    else:
        detail = ""

    text = f"{name}: {detail}" if detail else name
    return " ".join(text.split())[:MAX_LENGTH]
