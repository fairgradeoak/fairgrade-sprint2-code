# Project
from fairgrade.coding_question import CodingQuestion
from fairgrade.gemini_client import GeminiClient

class Submission:
    @staticmethod
    def submit_question(question, answer):
        if(type(question) == CodingQuestion):
            return Submission.submit_code_question(question, answer)
        else:
            return Submission.submit_text_question(question, answer)

    @staticmethod
    def submit_text_question(question, answer):
        return GeminiClient.review_text_submission(question=question, answer=answer)
    
    @staticmethod
    def submit_code_question(code_question, submitted_code):
        return GeminiClient.review_code_submission(code_question=code_question, submitted_code=submitted_code)