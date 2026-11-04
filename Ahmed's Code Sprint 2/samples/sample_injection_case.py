class SampleInjectionCase:
    """One test case for the prompt-injection check.

    question            the Question or CodingQuestion the submission was written for
    test_answer         the student answer (or code) sent to the injection check
    expected_injection  True when the submission tries to manipulate the grader, False when it is a normal
                        submission (even a wrong, empty or odd one)
    category            label for slicing results later: benign_correct, benign_wrong, benign_no_answer,
                        benign_topic_is_injection, benign_unsure_note, benign_code_comments, benign_long_answer,
                        direct_override, score_dictation, fake_system_message, delimiter_escape, fake_authority,
                        code_comment_injection, non_english_override or hidden_note_in_correct_answer
    """
    def __init__(self, question, test_answer, expected_injection, category=None):
        self.question = question
        self.test_answer = test_answer
        self.expected_injection = expected_injection
        self.category = category

    def __str__(self):
        return f"""Category: {self.category}
Question: {self.question.question_text}
Test answer: {self.test_answer}
Expected: {"injection" if self.expected_injection else "not an injection"}
"""
