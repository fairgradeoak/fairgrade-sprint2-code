# for importing
import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

PYTHON = 71   # Judge0 language id for Python 3

# Project
from fairgrade.coding_question import CodingQuestion
from samples.sample_code_question import SampleCodeQuestion

# 35 sample student submissions (5 for each of 6 Python questions, 5 more for the extra test types at the end) with the
# score a human grader would give. NOTE: the expected scores are estimates worked out from the rubric weights, not instructor
# grades. Replace them with human-graded scores before treating any agreement rate as a real measurement.
# Cases marked "judgment call" are the ones to settle with a human grader first.

# ======================================================================
# The questions (the first six are used by five submissions each; the C++ question is in the last section)
# ======================================================================

even_odd_question = CodingQuestion("cs101",
            "introduction to programming using python",
            "Write a program that takes an integer as an input and prints 'Even' if it's even or 'Odd' if it's odd",
            "coding question",
            """number = int(input(""))
if(number % 2 == 0):
    print("Even")
else:
    print("Odd")""",
            2.0,
            [
                {"id": "c1", "requirement": "Student takes an input and converts it to an integer", "weight_fraction": 0.25},
                {"id": "c2", "requirement": "Student uses an if statement to handle all possible cases", "weight_fraction": 0.25},
                {"id": "c3", "requirement": "Student uses modulo operator to determine number type", "weight_fraction": 0.25},
                {"id": "c4", "requirement": "Student prints even and odd after determining each number type", "weight_fraction": 0.25}
            ], PYTHON,
            [("2", "Even"), ("3", "Odd"), ("4", "Even"), ("11", "Odd"), ("100", "Even"), ("1", "Odd"), ("0", "Even"), ("-2", "Even"), ("-3", "Odd")])

sign_question = CodingQuestion("cs101",
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

factorial_question = CodingQuestion("cs101",
            "introduction to programming using python",
            "Write a program that takes a non-negative integer n as an input and prints its factorial (n!). Note that 0! = 1",
            "coding question",
            """n = int(input(""))
result = 1
for i in range(1, n + 1):
    result *= i
print(result)""",
            3.0,
            [
                {"id": "c1", "requirement": "Student takes an input and converts it to an integer", "weight_fraction": 0.2},
                {"id": "c2", "requirement": "Student initializes an accumulator variable to 1", "weight_fraction": 0.2},
                {"id": "c3", "requirement": "Student uses a loop to multiply the numbers from 1 to n", "weight_fraction": 0.3},
                {"id": "c4", "requirement": "Student handles n = 0 correctly (outputs 1)", "weight_fraction": 0.15},
                {"id": "c5", "requirement": "Student prints the final result", "weight_fraction": 0.15}
            ], PYTHON,
            [("0", "1"), ("1", "1"), ("2", "2"), ("3", "6"), ("5", "120"), ("7", "5040"), ("10", "3628800")])

digit_sum_question = CodingQuestion("cs101",
            "introduction to programming using python",
            "Write a program that takes a non-negative integer as an input and prints the sum of its digits",
            "coding question",
            """number = int(input(""))
total = 0
while number > 0:
    total += number % 10
    number //= 10
print(total)""",
            3.0,
            [
                {"id": "c1", "requirement": "Student takes an input and converts it to an integer (or iterates over its characters correctly)", "weight_fraction": 0.2},
                {"id": "c2", "requirement": "Student initializes a variable to accumulate the sum", "weight_fraction": 0.2},
                {"id": "c3", "requirement": "Student uses a loop that processes every digit of the number", "weight_fraction": 0.3},
                {"id": "c4", "requirement": "Student extracts digits correctly (e.g. using modulo and integer division, or string conversion)", "weight_fraction": 0.2},
                {"id": "c5", "requirement": "Student prints the final sum", "weight_fraction": 0.1}
            ], PYTHON,
            [("123", "6"), ("0", "0"), ("7", "7"), ("100", "1"), ("999", "27"), ("4086", "18"), ("1000000", "1")])

reverse_question = CodingQuestion("cs101",
            "introduction to programming using python",
            "Write a program that takes a string as an input and prints the string reversed",
            "coding question",
            """text = input("")
print(text[::-1])""",
            2.0,
            [
                {"id": "c1", "requirement": "Student takes a string input", "weight_fraction": 0.25},
                {"id": "c2", "requirement": "Student reverses the string correctly (slicing, loop, or reversed())", "weight_fraction": 0.5},
                {"id": "c3", "requirement": "Student prints the reversed string", "weight_fraction": 0.25}
            ], PYTHON,
            [("hello", "olleh"), ("python", "nohtyp"), ("a", "a"), ("racecar", "racecar"), ("12345", "54321"), ("abc def", "fed cba")])

vowels_question = CodingQuestion("cs101",
            "introduction to programming using python",
            "Write a program that takes a string as an input and prints the number of vowels (a, e, i, o, u) in it. The check must be case-insensitive",
            "coding question",
            """text = input("").lower()
count = 0
for ch in text:
    if ch in "aeiou":
        count += 1
print(count)""",
            3.0,
            [
                {"id": "c1", "requirement": "Student takes a string input", "weight_fraction": 0.15},
                {"id": "c2", "requirement": "Student handles upper and lower case letters (e.g. using lower() or checking both cases)", "weight_fraction": 0.25},
                {"id": "c3", "requirement": "Student loops over every character of the string", "weight_fraction": 0.25},
                {"id": "c4", "requirement": "Student correctly checks whether each character is a vowel and increments a counter", "weight_fraction": 0.25},
                {"id": "c5", "requirement": "Student prints the final count", "weight_fraction": 0.1}
            ], PYTHON,
            [("hello", "2"), ("PYTHON", "1"), ("rhythm", "0"), ("aeiou", "5"), ("AEIOU", "5"), ("Programming", "3"), ("banana", "3"), ("Hello World", "3")])

# ======================================================================
# The C++ question (used by the "more test types" section at the end)
# ======================================================================

CPP = 54   # Judge0 language id for C++ (GCC)

even_odd_cpp_question = CodingQuestion("cs101",
            "introduction to programming using C++",
            "Write a program that takes an integer as an input and prints 'Even' if it's even or 'Odd' if it's odd",
            "coding question",
            """#include <iostream>
using namespace std;

int main() {
    int number;
    cin >> number;
    if (number % 2 == 0) {
        cout << "Even" << endl;
    } else {
        cout << "Odd" << endl;
    }
    return 0;
}""",
            2.0,
            [
                {"id": "c1", "requirement": "Student reads an integer from the input", "weight_fraction": 0.25},
                {"id": "c2", "requirement": "Student uses an if statement to handle all possible cases", "weight_fraction": 0.25},
                {"id": "c3", "requirement": "Student uses modulo operator to determine number type", "weight_fraction": 0.25},
                {"id": "c4", "requirement": "Student prints even and odd after determining each number type", "weight_fraction": 0.25}
            ], CPP,
            # only 5 tests: Judge0 compiles a C++ program again for every test (about 1 s each on the 2-CPU VM), so 9 tests take about 10 s
            [("2", "Even"), ("3", "Odd"), ("11", "Odd"), ("0", "Even"), ("-3", "Odd")])

tests = []

# ======================================================================
# Even / odd
# ======================================================================

# 1 - correct
tests.append(
    SampleCodeQuestion(
        question=even_odd_question,
        test_answer="""number = int(input())
if number % 2 == 0:
    print("Even")
else:
    print("Odd")
""",
        expected_score=2.0,
        category="correct",
    )
)

# 2 - valid alternate method (modulo used as a truth value)
tests.append(
    SampleCodeQuestion(
        question=even_odd_question,
        test_answer="""number = int(input())
if number % 2:
    print("Odd")
else:
    print("Even")
""",
        expected_score=2.0,
        category="alternate_method",
    )
)

# 3 - minor bug: right logic, but prints lowercase words so every test fails
# c1-c3 met (0.75) + c4 half (0.125) = 0.875 x 2.0 = 1.75; judgment call
tests.append(
    SampleCodeQuestion(
        question=even_odd_question,
        test_answer="""number = int(input())
if number % 2 == 0:
    print("even")
else:
    print("odd")
""",
        expected_score=1.75,
        category="minor_bug",
    )
)

# 4 - wrong logic: decides by sign instead of parity (passes 4 of 9 tests by luck)
# c1 and c2 met, c3 and c4 not met: 0.5 x 2.0 = 1.0
tests.append(
    SampleCodeQuestion(
        question=even_odd_question,
        test_answer="""number = int(input())
if number > 0:
    print("Even")
else:
    print("Odd")
""",
        expected_score=1.0,
        category="wrong_logic",
    )
)

# 5 - syntax error: right logic, missing colon, so every test fails to run
# c1-c3 met, c4 half: 1.75; judgment call
tests.append(
    SampleCodeQuestion(
        question=even_odd_question,
        test_answer="""number = int(input())
if number % 2 == 0
    print("Even")
else:
    print("Odd")
""",
        expected_score=1.75,
        category="syntax_error",
    )
)

# ======================================================================
# Positive / negative / zero
# ======================================================================

# 6 - correct
tests.append(
    SampleCodeQuestion(
        question=sign_question,
        test_answer="""number = int(input())
if number > 0:
    print("Positive")
elif number < 0:
    print("Negative")
else:
    print("Zero")
""",
        expected_score=2.0,
        category="correct",
    )
)

# 7 - valid alternate method (checks zero first)
tests.append(
    SampleCodeQuestion(
        question=sign_question,
        test_answer="""number = int(input())
if number == 0:
    print("Zero")
elif number > 0:
    print("Positive")
else:
    print("Negative")
""",
        expected_score=2.0,
        category="alternate_method",
    )
)

# 8 - edge case bug: >= sends zero to the Positive branch (fails only the test for 0)
# c1 met, c2 half (the Zero branch is unreachable), c3 half (wrong boundary), c4 met: 0.75 x 2.0 = 1.5
tests.append(
    SampleCodeQuestion(
        question=sign_question,
        test_answer="""number = int(input())
if number >= 0:
    print("Positive")
elif number < 0:
    print("Negative")
else:
    print("Zero")
""",
        expected_score=1.5,
        category="edge_case_bug",
    )
)

# 9 - hardcoded output: looks up the sample inputs and defaults to Positive (passes 5 of 7 tests, solves nothing)
# no rubric criterion is met (no int conversion, no conditions, no comparison with zero)
tests.append(
    SampleCodeQuestion(
        question=sign_question,
        test_answer="""number = input()
answers = {"5": "Positive", "-7": "Negative", "0": "Zero"}
print(answers.get(number, "Positive"))
""",
        expected_score=0.0,
        category="hardcoded_output",
    )
)

# 10 - runtime error: compares the string from input() with 0 (TypeError on every test)
# c1 not met, c2 met, c3 half, c4 met: 0.625 x 2.0 = 1.25; judgment call
tests.append(
    SampleCodeQuestion(
        question=sign_question,
        test_answer="""number = input()
if number > 0:
    print("Positive")
elif number < 0:
    print("Negative")
else:
    print("Zero")
""",
        expected_score=1.25,
        category="runtime_error",
    )
)

# ======================================================================
# Factorial
# ======================================================================

# 11 - correct
tests.append(
    SampleCodeQuestion(
        question=factorial_question,
        test_answer="""n = int(input())
result = 1
for i in range(1, n + 1):
    result *= i
print(result)
""",
        expected_score=3.0,
        category="correct",
    )
)

# 12 - valid alternate method (while loop counting down)
tests.append(
    SampleCodeQuestion(
        question=factorial_question,
        test_answer="""n = int(input())
result = 1
while n > 1:
    result *= n
    n -= 1
print(result)
""",
        expected_score=3.0,
        category="alternate_method",
    )
)

# 13 - minor bug: accumulator starts at 0, so the product is always 0 (fails every test)
# c1 + c3 + c5 met: 0.65 x 3.0 = 1.95
tests.append(
    SampleCodeQuestion(
        question=factorial_question,
        test_answer="""n = int(input())
result = 0
for i in range(1, n + 1):
    result *= i
print(result)
""",
        expected_score=1.95,
        category="minor_bug",
    )
)

# 14 - off by one: range(1, n) leaves n out (passes only n = 0 and n = 1)
# c3 half (0.15), everything else met: 0.85 x 3.0 = 2.55
tests.append(
    SampleCodeQuestion(
        question=factorial_question,
        test_answer="""n = int(input())
result = 1
for i in range(1, n):
    result *= i
print(result)
""",
        expected_score=2.55,
        category="off_by_one",
    )
)

# 15 - wrong logic: adds instead of multiplying (passes n = 1 and n = 3 by coincidence)
# only c1 and c5 met: 0.35 x 3.0 = 1.05
tests.append(
    SampleCodeQuestion(
        question=factorial_question,
        test_answer="""n = int(input())
total = 0
for i in range(1, n + 1):
    total += i
print(total)
""",
        expected_score=1.05,
        category="wrong_logic",
    )
)

# ======================================================================
# Sum of digits
# ======================================================================

# 16 - correct
tests.append(
    SampleCodeQuestion(
        question=digit_sum_question,
        test_answer="""number = int(input())
total = 0
while number > 0:
    total += number % 10
    number //= 10
print(total)
""",
        expected_score=3.0,
        category="correct",
    )
)

# 17 - valid alternate method (string conversion, which the rubric allows)
tests.append(
    SampleCodeQuestion(
        question=digit_sum_question,
        test_answer="""total = 0
for ch in input():
    total += int(ch)
print(total)
""",
        expected_score=3.0,
        category="alternate_method",
    )
)

# 18 - off by one: while number > 9 skips the leading digit (passes only the test for 0)
# c3 half (0.15), everything else met: 0.85 x 3.0 = 2.55
tests.append(
    SampleCodeQuestion(
        question=digit_sum_question,
        test_answer="""number = int(input())
total = 0
while number > 9:
    total += number % 10
    number //= 10
print(total)
""",
        expected_score=2.55,
        category="off_by_one",
    )
)

# 19 - wrong logic: prints how many digits there are, not their sum
tests.append(
    SampleCodeQuestion(
        question=digit_sum_question,
        test_answer="""print(len(input()))
""",
        expected_score=0.0,
        category="wrong_logic",
    )
)

# 20 - no answer: only a comment, nothing is printed
tests.append(
    SampleCodeQuestion(
        question=digit_sum_question,
        test_answer="""# I could not figure this one out
""",
        expected_score=0.0,
        category="no_answer",
    )
)

# ======================================================================
# Reverse a string
# ======================================================================

# 21 - correct
tests.append(
    SampleCodeQuestion(
        question=reverse_question,
        test_answer="""text = input()
print(text[::-1])
""",
        expected_score=2.0,
        category="correct",
    )
)

# 22 - valid alternate method (builds the result in a loop)
tests.append(
    SampleCodeQuestion(
        question=reverse_question,
        test_answer="""text = input()
reversed_text = ""
for ch in text:
    reversed_text = ch + reversed_text
print(reversed_text)
""",
        expected_score=2.0,
        category="alternate_method",
    )
)

# 23 - minor bug: reverses correctly but prints a list like ['o', 'l', 'l', 'e', 'h'] (fails every test)
# c1 met, c2 half, c3 half: 0.625 x 2.0 = 1.25; judgment call
tests.append(
    SampleCodeQuestion(
        question=reverse_question,
        test_answer="""text = input()
print(list(reversed(text)))
""",
        expected_score=1.25,
        category="minor_bug",
    )
)

# 24 - wrong logic: sorts the characters instead of reversing them (passes only the one-letter test)
# only c1 met: 0.25 x 2.0 = 0.5
tests.append(
    SampleCodeQuestion(
        question=reverse_question,
        test_answer="""text = input()
print("".join(sorted(text)))
""",
        expected_score=0.5,
        category="wrong_logic",
    )
)

# 25 - runtime error: text[len(text) - i] is out of range on the first pass (IndexError on every test)
# close to correct: c1 met, c2 half, c3 half: 1.25; judgment call
tests.append(
    SampleCodeQuestion(
        question=reverse_question,
        test_answer="""text = input()
result = ""
for i in range(len(text)):
    result += text[len(text) - i]
print(result)
""",
        expected_score=1.25,
        category="runtime_error",
    )
)

# ======================================================================
# Count vowels
# ======================================================================

# 26 - correct
tests.append(
    SampleCodeQuestion(
        question=vowels_question,
        test_answer="""text = input().lower()
count = 0
for ch in text:
    if ch in "aeiou":
        count += 1
print(count)
""",
        expected_score=3.0,
        category="correct",
    )
)

# 27 - valid alternate method (generator expression)
tests.append(
    SampleCodeQuestion(
        question=vowels_question,
        test_answer="""text = input().lower()
print(sum(1 for ch in text if ch in "aeiou"))
""",
        expected_score=3.0,
        category="alternate_method",
    )
)

# 28 - minor bug: no case handling (fails the tests for PYTHON and AEIOU, passes the other 6)
# c2 not met: 0.75 x 3.0 = 2.25
tests.append(
    SampleCodeQuestion(
        question=vowels_question,
        test_answer="""text = input()
count = 0
for ch in text:
    if ch in "aeiou":
        count += 1
print(count)
""",
        expected_score=2.25,
        category="minor_bug",
    )
)

# 29 - wrong logic: counts the characters that are NOT vowels (passes only 'banana' by coincidence)
# the structure is right but the vowel check is inverted, so c4 is not met: 0.75 x 3.0 = 2.25; judgment call
tests.append(
    SampleCodeQuestion(
        question=vowels_question,
        test_answer="""text = input().lower()
count = 0
for ch in text:
    if ch not in "aeiou":
        count += 1
print(count)
""",
        expected_score=2.25,
        category="wrong_logic",
    )
)

# 30 - syntax error: right logic, missing colon after the for line, so every test fails to run
# c1-c4 met, c5 half: 0.95 x 3.0 = 2.85; judgment call
tests.append(
    SampleCodeQuestion(
        question=vowels_question,
        test_answer="""text = input().lower()
count = 0
for ch in text
    if ch in "aeiou":
        count += 1
print(count)
""",
        expected_score=2.85,
        category="syntax_error",
    )
)


# ======================================================================
# More test types: infinite loop, a real compile error, runtime error in C++, hard-coded answer that passes every test
# ======================================================================

# 31 - infinite loop: the loop stops when i == n, so n = 0 never stops (Time Limit Exceeded on that test); n = 1 is right
# and every other input prints a wrong product (passes only n = 1)
# c1 and c2 met (0.4), c3 half (0.15), c4 not met, c5 met (0.15): 0.7 x 3.0 = 2.1; judgment call
tests.append(
    SampleCodeQuestion(
        question=factorial_question,
        test_answer="""n = int(input())
result = 1
i = 1
while i != n:
    result *= i
    i += 1
print(result)
""",
        expected_score=2.1,
        category="infinite_loop",
    )
)

# 32 - C++ correct
tests.append(
    SampleCodeQuestion(
        question=even_odd_cpp_question,
        test_answer="""#include <iostream>
using namespace std;

int main() {
    int number;
    cin >> number;
    if (number % 2 == 0)
        cout << "Even" << endl;
    else
        cout << "Odd" << endl;
    return 0;
}
""",
        expected_score=2.0,
        category="correct",
    )
)

# 33 - compile error: right logic, missing semicolon, so the program does not compile and every test is a Compilation Error
# c1-c3 met, c4 half: 1.75 (same call as the Python syntax error in 5); judgment call
tests.append(
    SampleCodeQuestion(
        question=even_odd_cpp_question,
        test_answer="""#include <iostream>
using namespace std;

int main() {
    int number;
    cin >> number
    if (number % 2 == 0)
        cout << "Even" << endl;
    else
        cout << "Odd" << endl;
    return 0;
}
""",
        expected_score=1.75,
        category="compile_error",
    )
)

# 34 - runtime error: the odd branch reads through a null pointer, so every odd input crashes (3 of 5 tests); even inputs pass
# c1-c3 met, c4 half (the Odd output never prints): 1.75; judgment call
tests.append(
    SampleCodeQuestion(
        question=even_odd_cpp_question,
        test_answer="""#include <iostream>
using namespace std;

int main() {
    int number;
    cin >> number;
    int* label = nullptr;
    if (number % 2 == 0)
        cout << "Even" << endl;
    else
        cout << *label << endl;
    return 0;
}
""",
        expected_score=1.75,
        category="runtime_error",
    )
)

# 35 - hard-coded answer that passes every visible test: a lookup table of exactly the nine test inputs (passes 9 of 9 tests,
# solves nothing and crashes on any other number)
# no rubric criterion is met (no int conversion, no condition, no modulo, no determination of the type): 0.0; judgment call
tests.append(
    SampleCodeQuestion(
        question=even_odd_question,
        test_answer="""answers = {"2": "Even", "3": "Odd", "4": "Even", "11": "Odd", "100": "Even", "1": "Odd", "0": "Even", "-2": "Even", "-3": "Odd"}
print(answers[input()])
""",
        expected_score=0.0,
        category="hardcoded_visible_tests",
    )
)
