class SampleTextQuestion:
    """One test case for the text-question grader.

    question        the Question being asked
    test_answer     a student answer to send to the grader
    expected_score  the score a human grader would give that answer (0 to question.max_points),
                    used as the reference when measuring how accurate the model is
    category        optional label for slicing results later: correct, correct_reworded, correct_terse,
                    correct_verbose, poorly_organized, correct_wrong_justification, alternate_method,
                    ambiguous_partial, contradiction, missing_criteria, no_answer or wrong
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
Test answer: {self.test_answer}
Expected score: {self.expected_score} / {self.question.max_points}
"""
