# Project
from fairgrade.submission import Submission
from samples.sample_text_questions import tests
from fairgrade.coding_question import CodingQuestion

PYTHON = 71   # Judge0 language id for Python 3

def main():
    print("Input:\n1-Text Questions 2-Coding Questions")

    # asking user for question type
    question_type = 0
    while(True):
        try:
            question_type = int(input(">"))
            if(question_type in range(1,3)):
                break
            else:
                print("Invalid Input:\n1-Text Questions 2-Coding Questions")
        except ValueError as e:
            print("Invalid Input:\n1-Text Questions 2-Coding Questions")

    
    if(question_type == 1):
        # Fetching question from text_questions.py
        # Assigning question to a variable
        print(f"Choose a question between {1} and {len(tests)}:")
        while(True):
            try:
                question_number = int(input(">"))
                if(question_number >=1 and question_number <= len(tests)):
                    break
                else:
                    print(f"Please enter a number between 1 and {len(tests)}:")
            except ValueError as e:
                print(f"Please enter a number between 1 and {len(tests)}:")

        question = tests[question_number - 1].question

        # Printing the question to the student
        print("-------------------------------------------")
        print(f"Subject: {question.subject_name}")
        print("Question:")
        print(question.question_text)

        # Asking student for answer
        print("Enter your answer:")
        answer = input(">")

        text_submission = Submission.submit_question(question, answer)

        print(text_submission)
        
    elif(question_type == 2):
        # Fetching question from coding_questions.py
        # Assigning question to a variable
        # TO DO
        question = CodingQuestion("cs101",
            "introduction to programming using python",
            "Write a program that takes an integer as an input and prints 'Positive' if it is greater than zero, 'Negative' if it is less than zero, or 'Zero' if it is equal to zero",
            "coding question",
            """number = int(input(""))
if number > 0:
    print("Positive")
elif number < 0:
    print("Negative")
else:
    print("Zero")""",
            2.0,
            [
                {"id": "c1", "requirement": "Student takes an input and converts it to an integer", "weight_fraction": 0.25},
                {"id": "c2", "requirement": "Student uses if/elif/else (or equivalent) to handle all three cases", "weight_fraction": 0.25},
                {"id": "c3", "requirement": "Student correctly compares the number against zero", "weight_fraction": 0.25},
                {"id": "c4", "requirement": "Student prints the exact expected word for each case", "weight_fraction": 0.25}
            ], PYTHON,
            [("5", "Positive"), ("-7", "Negative"), ("0", "Zero"), ("1", "Positive"), ("-1", "Negative"), ("1000", "Positive"), ("-250", "Negative")])

        # Printing the question to the student
        print("-------------------------------------------")
        print("Question:")
        print(question.question_text)

        # Asking student for answer
        print("Enter your answer:")
        answer = """
text = input("")
count = 0
for ch in text:
    if ch == "a" or ch == "e" or ch == "i" or ch == "o" or ch == "u":
        count += 1
print(count)
"""

        es = Submission.submit_question(question,answer)
        print(es)

main()