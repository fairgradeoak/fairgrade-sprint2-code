class SampleCodeQuestion:
    """One test case for the coding-question grader.

    question        the CodingQuestion being asked
    test_answer     a student's submitted code to send to the grader
    expected_score  the score a human grader would give that code (0 to question.max_points),
                    used as the reference when measuring how accurate the model is
    category        optional label for slicing results later: correct, alternate_method, minor_bug,
                    edge_case_bug, off_by_one, wrong_logic, hardcoded_output (fails some tests),
                    hardcoded_visible_tests (passes every test), syntax_error, compile_error,
                    infinite_loop, runtime_error or no_answer
    """
    def __init__(self, question, test_answer, expected_score, category=None):
        if(expected_score < 0 or expected_score > question.max_points):
            raise ValueError(f"expected_score {expected_score} is outside 0 to {question.max_points} for question: {question.question_text}")

        self.question = question
        self.test_answer = test_answer
        self.expected_score = expected_score
        self.category = category

    def __str__(self):
        return f"""Category: {self.category}
Question: {self.question.question_text}
Test code:
{self.test_answer}
Expected score: {self.expected_score} / {self.question.max_points}
"""
