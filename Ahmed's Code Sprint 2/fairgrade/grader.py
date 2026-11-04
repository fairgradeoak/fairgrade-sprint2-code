from typing import List, Dict, Optional
from pydantic import BaseModel, field_validator, model_validator

# Projeect
from fairgrade.ai_response import AiResponse

# every result, whatever happened, carries one of these in its "status" field
STATUS_GRADED = "graded"                      # the ai grade is valid
STATUS_INJECTION = "injection_flagged"        # the answer looked like a prompt injection, nothing was graded
STATUS_FAILED = "failed"                      # grading could not be completed (bad model output, api or judge0 failure)

# ---------------------------------------------------------------- review triggers
# A graded result is sent to the instructor (needs_review) when any of these fire. The numbers are shares (0 to 1).
LOW_CONFIDENCE = 0.75      # the model's own confidence is below this
# code questions: the test results and the score tell opposite stories
TESTS_MOSTLY_FAIL = 0.5    # fewer than this share of the tests passed ...
SCORE_HIGH = 0.6           # ... but the score is at least this share of the maximum
TESTS_MOSTLY_PASS = 0.7    # at least this share of the tests passed ...
SCORE_LOW = 0.5            # ... but the score is at most this share of the maximum


# ids can reach the grader as str or int depending on where they come from (model reply, database, sample data),
# so they are always compared as stripped strings
def normalize_id(criteria_id):
    return str(criteria_id).strip()


# The one and only shape of a grading result (a plain dict, never a json string). Graded, flagged and failed submissions all go through here,
# so the consumer always finds the same keys and only has to look at "status" to know what happened.
def build_result(status, max_points, grade=None, confidence=None, needs_review=True, review_reasons=None,
                 student_feedback="", instructor_feedback="", rubric_breakdown=None, attempts=1, error=None):
    result = {"status": status,
              "grade": grade,
              "max_grade": max_points,
              "confidence": confidence,
              "needs_review": needs_review,
              "review_reasons": review_reasons if review_reasons is not None else [], # why it needs review, empty when it does not
              "student_feedback": student_feedback,
              "instructor_feedback": instructor_feedback,
              "rubric_breakdown": rubric_breakdown if rubric_breakdown is not None else [],
              "attempts": attempts, # how many model requests it took (more than 1 means the model had to be re-asked)
              "error": error
              }

    return result


# The model's own confidence turned out to be useless (about 1.0 on almost every answer, even the wrong ones),
# so it is only one trigger. The others are computed from the scores and test results, never from the model:
#   mixed scores    when one criterion gets full marks and another gets none in the same answer, the model is
#                   split on the answer (the unstable grades in the repeated runs were all like this)
#   tests vs score  (code) most tests fail but the score is high, or most pass but the score is low
#   fractional      (text) a criterion scored strictly between 0 and 1: the model is unsure whether it is met
#                   (on the 30 text samples every model grade that was off by more than 10% had one of these or mixed scores)
# tests_passed and tests_total are None for a text question. The reasons only contain numbers, never the student's text.
# This is a plain function so the analysis script can apply the same rules to saved results.
def trigger_reasons(confidence, criteria_scores, score_fraction, tests_passed=None, tests_total=None):
    reasons = []

    if(confidence < LOW_CONFIDENCE):
        reasons.append(f"low confidence ({confidence})")

    if(any(score == 1 for score in criteria_scores) and any(score == 0 for score in criteria_scores)):
        reasons.append("mixed criteria scores (some fully met, some not met at all)")

    if(tests_total is None):
        if(any(0 < score < 1 for score in criteria_scores)):
            reasons.append("fractional criterion score (the model is unsure whether a criterion is met)")
    elif(tests_total > 0):
        pass_rate = tests_passed / tests_total
        if(pass_rate < TESTS_MOSTLY_FAIL and score_fraction >= SCORE_HIGH):
            reasons.append(f"tests and score disagree (only {tests_passed} of {tests_total} tests passed, but the grade is {score_fraction:.0%} of the maximum)")
        elif(pass_rate >= TESTS_MOSTLY_PASS and score_fraction <= SCORE_LOW):
            reasons.append(f"tests and score disagree ({tests_passed} of {tests_total} tests passed, but the grade is only {score_fraction:.0%} of the maximum)")

    return reasons


class Grader(BaseModel):
    ai_assessment: AiResponse # used to fetch data given by the ai
    question_rubric: List[Dict] # used to compare the ai assessment of the rubric against the real one
    max_points: float
    attempts: int = 1 # how many model requests it took to get this assessment
    test_statuses: Optional[List[str]] = None # code questions only: the Judge0 status of every test case ("Accepted", ...)

    # Every rubric criterion must be graded exactly once and nothing else may be graded. A mismatch used to be
    # skipped silently (a duplicated id counted twice, an unknown id counted as zero), now it is an error.
    @model_validator(mode="after")
    def validate_criteria_ids(self):
        expected = [normalize_id(criteria["id"]) for criteria in self.question_rubric]
        returned = [normalize_id(criteria["criteria_id"]) for criteria in self.ai_assessment.rubric_breakdown]

        if(len(expected) != len(set(expected))):
            raise ValueError(f"the rubric has duplicated criteria ids: {expected}")

        duplicated = sorted({criteria_id for criteria_id in returned if returned.count(criteria_id) > 1})
        missing = sorted(set(expected) - set(returned))
        unknown = sorted(set(returned) - set(expected))

        if(duplicated or missing or unknown):
            raise ValueError(f"criteria ids do not match the rubric, duplicated: {duplicated}, missing: {missing}, unknown: {unknown}")
        return self

    def final_assessment(self):
        reasons = self.review_reasons()
        return build_result(status=STATUS_GRADED,
                            max_points=self.max_points,
                            grade=self.calculate_score(),
                            confidence=self.ai_assessment.confidence,
                            needs_review=len(reasons) > 0,
                            review_reasons=reasons,
                            student_feedback=self.ai_assessment.student_feedback,
                            instructor_feedback=self.ai_assessment.instructor_feedback,
                            rubric_breakdown=self.ai_assessment.rubric_breakdown,
                            attempts=self.attempts)

    # the answer was flagged as a prompt injection: no grade, the instructor decides
    @staticmethod
    def injection_result(max_points):
        return build_result(status=STATUS_INJECTION,
                            max_points=max_points,
                            review_reasons=["possible prompt injection"],
                            student_feedback="Your submission was sent to your instructor for review.",
                            instructor_feedback="Possible prompt injection detected in the submission, it was not graded.")

    # grading could not be completed, the submission goes to the instructor instead of crashing or guessing a grade
    @staticmethod
    def failed_result(max_points, reason, attempts=0):
        return build_result(status=STATUS_FAILED,
                            max_points=max_points,
                            review_reasons=["automatic grading failed"],
                            student_feedback="Your submission could not be graded automatically and was sent to your instructor for review.",
                            instructor_feedback=f"Automatic grading failed: {reason}",
                            attempts=attempts,
                            error=reason)

    # the grade as a share of the maximum (0 to 1)
    def score_fraction(self):
        if(self.max_points <= 0):
            return 0.0
        return round(self.calculate_score() / self.max_points, 4)

    # The reasons this result should go to the instructor (see trigger_reasons), empty when none fires
    def review_reasons(self):
        scores = [float(criteria["score"]) for criteria in self.ai_assessment.rubric_breakdown]
        passed = total = None
        if(self.test_statuses is not None):
            total = len(self.test_statuses)
            passed = sum(1 for status in self.test_statuses if status == "Accepted")
        return trigger_reasons(self.ai_assessment.confidence, scores, self.score_fraction(), passed, total)

    def needs_review(self):
        return len(self.review_reasons()) > 0

    def calculate_score(self):
        # criterion id -> the ai's score for it (the validator above guarantees every rubric criterion is in here)
        scores = {normalize_id(criteria["criteria_id"]): float(criteria["score"])
                  for criteria in self.ai_assessment.rubric_breakdown}

        final_score = 0
        for criteria in self.question_rubric:
            final_score += float(criteria["weight_fraction"]) * scores[normalize_id(criteria["id"])]

        final_score *= self.max_points
        return(round(final_score,2))
