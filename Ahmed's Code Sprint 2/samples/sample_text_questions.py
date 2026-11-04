# for importing
import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from fairgrade.question import Question
from samples.sample_text_question import SampleTextQuestion

# NOTE: the expected scores below are my own estimates from the rubric weights, not instructor grades.
# Replace them with human-graded scores before treating any agreement rate as a real measurement.

tests = []

# 1 - correct
tests.append(
    SampleTextQuestion(
        question=Question(
            "math101",
            "introduction to algebra",
            "Solve for x: 2x + 6 = 14. Show the value of x and explain the step used to isolate it.",
            "short answer",
            """Subtract 6 from both sides to get 2x = 8, then divide both sides by 2 to get x = 4. 
The key step is isolating x by performing inverse operations in reverse order of operations.""",
            2.0,
            [
                {"id": "c1","requirement": "Student correctly solves for x and states x = 4", "weight_fraction": 0.5},
                {"id": "c2","requirement": "Student explains the algebraic step(s) used to isolate x", "weight_fraction": 0.5},
            ]),
        test_answer="""First I subtracted 6 from both sides, giving 2x = 8. Then I divided both sides by 2,
so x = 4.""",
        expected_score=2.0,
        category="correct",
    )
)

# 2 - correct
tests.append(
    SampleTextQuestion(
        question=Question(
            "biology101",
            "introduction to cell biology",
            "What is photosynthesis and what are its two main products?",
            "short answer",
            """Photosynthesis is the process by which plants convert light energy, water, and carbon
dioxide into chemical energy. Its two main products are glucose and oxygen.""",
            2.0,
            [
                {"id": "c1", "requirement": "Student correctly defines photosynthesis as converting light energy into chemical energy using water and CO2", "weight_fraction": 0.5},
                {"id": "c2", "requirement": "Student correctly names glucose and oxygen as the two main products", "weight_fraction": 0.5},
            ]),
        test_answer="""Photosynthesis is when plants use sunlight, water, and carbon dioxide to make their own
food. It produces glucose for energy and releases oxygen as a byproduct.""",
        expected_score=2.0,
        category="correct",
    )
)

# 3 - correct
tests.append(
    SampleTextQuestion(
        question=Question(
            "cs201",
            "data structures and algorithms",
            "Explain why a hash table lookup is O(1) on average but O(n) in the worst case.",
            "short answer",
            """On average, a hash function distributes keys evenly across buckets, so each lookup
touches a small constant number of entries, giving O(1). In the worst case, many keys 
collide into the same bucket, degrading lookup to a linear scan of that bucket, O(n).""",
            5.0,
            [
                {"id": "c1", "requirement": "Explains average-case O(1) via even key distribution across buckets", "weight_fraction": 0.5},
                {"id": "c2", "requirement": "Explains worst-case O(n) via hash collisions forcing a linear scan", "weight_fraction": 0.5},
            ]),
        test_answer="""Average case is O(1) because a good hash function spreads keys evenly so each bucket
has very few entries. Worst case is O(n) because if many keys hash to the same bucket, 
you end up having to scan through all of them one by one, which is linear.""",
        expected_score=5.0,
        category="correct",
    )
)

# 4 - correct, reworded
tests.append(
    SampleTextQuestion(
        question=Question(
            "chemistry101",
            "introduction to chemical reactions",
            "What is the law of conservation of mass and why does it hold true in a chemical reaction?",
            "short answer",
            """The law of conservation of mass states that mass is neither created nor destroyed in a
chemical reaction. It holds because atoms are only rearranged into new molecules during
a reaction, not created or destroyed, so the total mass of reactants equals the total
mass of products.""",
            2.0,
            [
                {"id": "c1", "requirement": "States that mass is neither created nor destroyed in a chemical reaction", "weight_fraction": 0.5},
                {"id": "c2", "requirement": "Explains this holds because atoms are rearranged, not created/destroyed, during the reaction", "weight_fraction": 0.5},
            ]),
        test_answer="""Basically, whatever mass you start with before a reaction, you end up with the exact
same total afterward — nothing just vanishes or appears out of nowhere. That's because
a reaction doesn't destroy or make new atoms, it just shuffles the existing ones around
into different combinations.""",
        expected_score=2.0,
        category="correct_reworded",
    )
)

# 5 - correct, reworded
tests.append(
    SampleTextQuestion(
        question=Question(
            "history101",
            "modern world history",
            "What was the primary economic cause of the Industrial Revolution's rapid spread across Britain?",
            "short answer",
            """The primary economic cause was the availability of capital and access to raw materials
like coal and iron, combined with a large labor force displaced from agriculture, which
together made factory-based mass production profitable and scalable.""",
            2.0,
            [
                {"id": "c1", "requirement": "Identifies access to capital and raw materials (coal/iron) as a key driver", "weight_fraction": 0.5},
                {"id": "c2", "requirement": "Identifies the availability of a displaced agricultural labor force as a key driver", "weight_fraction": 0.5},
            ]),
        test_answer="""Britain had a ton of money to invest along with plenty of coal and iron just sitting 
there ready to use, and on top of that, so many people had left farm work that there 
were tons of workers available for the new factories. Put those together and you get 
an economy built for cheap, large-scale production.""",
        expected_score=2.0,
        category="correct_reworded",
    )
)

# 6 - correct, reworded
tests.append(
    SampleTextQuestion(
        question=Question(
            "economics101",
            "principles of microeconomics",
            "Explain the concept of opportunity cost.",
            "short answer",
            """Opportunity cost is the value of the next best alternative that is given up when a
choice is made. It represents what you sacrifice in order to pursue a different option.""",
            2.0,
            [
                {"id": "c1", "requirement": "Defines opportunity cost as the value of the next best alternative forgone", "weight_fraction": 1.0},
            ]),
        test_answer="""It's basically what you're giving up by picking one thing over another. If you had 
several options and chose one, opportunity cost is the benefit of whichever other 
option would have been your best choice instead.""",
        expected_score=2.0,
        category="correct_reworded",
    )
)

# 7 - missing criteria (never says what a higher specific heat capacity implies)
tests.append(
    SampleTextQuestion(
        question=Question(
            "physics102",
            "introduction to molecular physics",
            "Define specific heat capacity and what it affects when it increases.",
            "short answer",
            """Specific heat capacity defines how much heat one kilogram of material can absorb in 
Joules before its temperature rises by a single degree Celsius. If a material has 
higher specific heat capacity, this means it requires more heat to raise its temperature.""",
            2.0,
            [
                {"id": "c1", "requirement": "Student explains what specific heat capacity is, using accurate units", "weight_fraction": 0.5},
                {"id": "c2", "requirement": "Student explains what having higher specific heat capacity implies", "weight_fraction": 0.5},
            ]),
        test_answer="""Specific heat capacity is how much heat energy in Joules is needed to raise one
kilogram of a substance by one degree Celsius.""",
        expected_score=1.0,
        category="missing_criteria",
    )
)

# 8 - missing criteria (correct final answer, no explanation of the steps)
tests.append(
    SampleTextQuestion(
        question=Question(
            "math101",
            "introduction to algebra",
            "Solve for x: 3x - 4 = 11. Show the value of x and explain the step used to isolate it.",
            "short answer",
            """Add 4 to both sides to get 3x = 15, then divide both sides by 3 to get x = 5. The key
step is isolating x through inverse operations.""",
            2.0,
            [
                {"id": "c1", "requirement": "Student correctly solves for x and states x = 5", "weight_fraction": 0.5},
                {"id": "c2", "requirement": "Student explains the algebraic step(s) used to isolate x", "weight_fraction": 0.5},
            ]),
        test_answer="x = 5",
        expected_score=1.0,
        category="missing_criteria",
    )
)

# 9 - missing criteria (defines photosynthesis and names glucose, never mentions oxygen)
# c1 fully met (1.0) + c2 half met (0.5 x 0.5 x 2.0 = 0.5) = 1.5; this half credit is a judgment call, confirm with a human grader
tests.append(
    SampleTextQuestion(
        question=Question(
            "biology101",
            "introduction to cell biology",
            "What is photosynthesis and what are its two main products?",
            "short answer",
            """Photosynthesis is the process by which plants convert light energy, water, and carbon
dioxide into chemical energy. Its two main products are glucose and oxygen.""",
            2.0,
            [
                {"id": "c1", "requirement": "Student correctly defines photosynthesis as converting light energy into chemical energy using water and CO2", "weight_fraction": 0.5},
                {"id": "c2", "requirement": "Student correctly names glucose and oxygen as the two main products", "weight_fraction": 0.5},
            ]),
        test_answer="""Photosynthesis is the process where plants use sunlight, water, and CO2 to produce
glucose, which they use for energy.""",
        expected_score=1.5,
        category="missing_criteria",
    )
)

# 10 - wrong (confuses chemical reactions with mass-energy conversion)
tests.append(
    SampleTextQuestion(
        question=Question(
            "chemistry101",
            "introduction to chemical reactions",
            "What is the law of conservation of mass and why does it hold true in a chemical reaction?",
            "short answer",
            """The law of conservation of mass states that mass is neither created nor destroyed in a 
chemical reaction. It holds because atoms are only rearranged into new molecules during 
a reaction, not created or destroyed, so the total mass of reactants equals the total 
mass of products.""",
            2.0,
            [
                {"id": "c1", "requirement": "States that mass is neither created nor destroyed in a chemical reaction", "weight_fraction": 0.5},
                {"id": "c2", "requirement": "Explains this holds because atoms are rearranged, not created/destroyed, during the reaction", "weight_fraction": 0.5},
            ]),
        test_answer="""The law of conservation of mass means that mass can increase or decrease during a 
reaction depending on how much energy is released, since energy and mass can convert 
into each other in any normal chemical reaction.""",
        expected_score=0.0,
        category="wrong",
    )
)

# 11 - wrong (blames arrays and resizing instead of even distribution and collisions)
tests.append(
    SampleTextQuestion(
        question=Question(
            "cs201",
            "data structures and algorithms",
            "Explain why a hash table lookup is O(1) on average but O(n) in the worst case.",
            "short answer",
            """On average, a hash function distributes keys evenly across buckets, so each lookup 
touches a small constant number of entries, giving O(1). In the worst case, many keys 
collide into the same bucket, degrading lookup to a linear scan of that bucket, O(n).""",
            5.0,
            [
                {"id": "c1", "requirement": "Explains average-case O(1) via even key distribution across buckets", "weight_fraction": 0.5},
                {"id": "c2", "requirement": "Explains worst-case O(n) via hash collisions forcing a linear scan", "weight_fraction": 0.5},
            ]),
        test_answer="""A hash table is O(1) because it's an array, and arrays are always O(1) for any 
operation. It becomes O(n) in the worst case if the array runs out of space and needs 
to be resized.""",
        expected_score=0.0,
        category="wrong",
    )
)

# 12 - wrong (invents a royal decree)
tests.append(
    SampleTextQuestion(
        question=Question(
            "history101",
            "modern world history",
            "What was the primary economic cause of the Industrial Revolution's rapid spread across Britain?",
            "short answer",
            """The primary economic cause was the availability of capital and access to raw materials 
like coal and iron, combined with a large labor force displaced from agriculture, which 
together made factory-based mass production profitable and scalable.""",
            2.0,
            [
                {"id": "c1","requirement": "Identifies access to capital and raw materials (coal/iron) as a key driver", "weight_fraction": 0.5},
                {"id": "c2","requirement": "Identifies the availability of a displaced agricultural labor force as a key driver", "weight_fraction": 0.5},
            ]),
        test_answer="""It mainly spread because Britain's king ordered all cities to build factories as part 
of a royal decree, and this government mandate forced the rapid industrialization 
across the whole country.""",
        expected_score=0.0,
        category="wrong",
    )
)


# ======================================================================
# Tests 13-30: trickier cases. Each new question is defined once and
# reused by the tests that follow it. Categories:
#   correct_terse, correct_verbose, poorly_organized, correct_wrong_justification,
#   alternate_method, ambiguous_partial, contradiction, missing_criteria, no_answer, wrong
# Expected scores marked "judgment call" are the ones to settle with a human grader first.
# ======================================================================

circle_area_question = Question(
    "math101",
    "introduction to algebra and geometry",
    "Find the area of a circle with a radius of 3 cm. Give the formula you used and the final answer.",
    "short answer",
    "The area of a circle is A = πr². With r = 3 cm, A = π × 3² = 9π ≈ 28.27 cm².",
    5.0,
    [
        {"id": "c1", "requirement": "States a correct formula for the area of a circle (e.g. A = πr²)", "weight_fraction": 0.4},
        {"id": "c2", "requirement": "Computes the area correctly as 9π (≈ 28.27) and includes square units (cm²)", "weight_fraction": 0.6},
    ])

newton_question = Question(
    "physics101",
    "introduction to mechanics",
    "State Newton's second law and use it to find the acceleration of a 4 kg object when a net force of 20 N acts on it.",
    "short answer",
    """Newton's second law states that the net force on an object equals its mass times its acceleration (F = ma).
The acceleration is a = F / m = 20 N / 4 kg = 5 m/s².""",
    4.0,
    [
        {"id": "c1", "requirement": "States Newton's second law: net force equals mass times acceleration (F = ma)", "weight_fraction": 0.5},
        {"id": "c2", "requirement": "Calculates the acceleration as 5 m/s² with units", "weight_fraction": 0.5},
    ])

mitosis_question = Question(
    "biology102",
    "cell division",
    "Explain the difference between mitosis and meiosis in terms of the number and genetic identity of the daughter cells.",
    "short answer",
    """Mitosis produces two genetically identical diploid daughter cells.
Meiosis produces four genetically different haploid cells (gametes).""",
    4.0,
    [
        {"id": "c1", "requirement": "Describes mitosis as producing two genetically identical diploid daughter cells", "weight_fraction": 0.5},
        {"id": "c2", "requirement": "Describes meiosis as producing four genetically different haploid cells", "weight_fraction": 0.5},
    ])

ph_question = Question(
    "chemistry102",
    "acids and bases",
    "What does a pH of 3 indicate about a solution, and how does it compare with a solution of pH 5?",
    "short answer",
    """A pH of 3 indicates an acidic solution. Because the pH scale is logarithmic, a solution of pH 3 has 100 times the
hydrogen-ion concentration of a solution of pH 5, so it is 100 times more acidic.""",
    5.0,
    [
        {"id": "c1", "requirement": "States that a solution with pH 3 is acidic", "weight_fraction": 0.4},
        {"id": "c2", "requirement": "States that pH 3 is more acidic than pH 5", "weight_fraction": 0.3},
        {"id": "c3", "requirement": "Explains that the pH scale is logarithmic, so pH 3 has 100 times the hydrogen-ion concentration of pH 5", "weight_fraction": 0.3},
    ])

binary_search_question = Question(
    "cs101",
    "algorithms",
    "Why is binary search O(log n), and what must be true about the data for it to work?",
    "short answer",
    """Each comparison halves the remaining search range, so at most about log2(n) comparisons are needed, giving O(log n).
The data must be sorted.""",
    5.0,
    [
        {"id": "c1", "requirement": "Explains that each step halves the remaining search range, giving O(log n)", "weight_fraction": 0.6},
        {"id": "c2", "requirement": "States that the data must be sorted", "weight_fraction": 0.4},
    ])

ww1_question = Question(
    "history102",
    "twentieth century history",
    "What event directly triggered the outbreak of World War I in 1914, and how did the alliance system help it become a wider war?",
    "short answer",
    """The assassination of Archduke Franz Ferdinand of Austria-Hungary in Sarajevo triggered the war.
The alliance system (the Triple Entente and the Triple Alliance) pulled the major powers into what began as a regional conflict.""",
    4.0,
    [
        {"id": "c1", "requirement": "Identifies the assassination of Archduke Franz Ferdinand as the trigger", "weight_fraction": 0.5},
        {"id": "c2", "requirement": "Explains that the alliance system pulled other powers into the war", "weight_fraction": 0.5},
    ])

supply_demand_question = Question(
    "economics102",
    "supply and demand",
    "What happens to the equilibrium price of a good when demand increases and supply stays the same? Explain why.",
    "short answer",
    """The equilibrium price rises. At the old price, the quantity demanded exceeds the quantity supplied (a shortage),
which pushes the price up until the market clears again.""",
    5.0,
    [
        {"id": "c1", "requirement": "States that the equilibrium price increases", "weight_fraction": 0.4},
        {"id": "c2", "requirement": "Explains the mechanism: at the old price quantity demanded exceeds quantity supplied (a shortage), which pushes the price up", "weight_fraction": 0.6},
    ])

quadratic_question = Question(
    "math102",
    "algebra",
    "Solve x² - 5x + 6 = 0 and explain the method you used.",
    "short answer",
    "Factor the quadratic as (x - 2)(x - 3) = 0, so x = 2 or x = 3.",
    5.0,
    [
        {"id": "c1", "requirement": "Finds both solutions, x = 2 and x = 3", "weight_fraction": 0.6},
        {"id": "c2", "requirement": "Shows a valid method (factoring, completing the square or the quadratic formula)", "weight_fraction": 0.4},
    ])

# 13 - correct but terse
tests.append(
    SampleTextQuestion(
        question=circle_area_question,
        test_answer="A = πr² = 9π ≈ 28.27 cm²",
        expected_score=5.0,
        category="correct_terse",
    )
)

# 14 - valid alternate method (equivalent formula using the diameter)
tests.append(
    SampleTextQuestion(
        question=circle_area_question,
        test_answer="I used A = πd²/4 with d = 6 cm: π × 36 / 4 = 9π ≈ 28.27 cm².",
        expected_score=5.0,
        category="alternate_method",
    )
)

# 15 - ambiguous partial: right formula and exact value, but no decimal value and no units
# c1 full (2.0) + c2 half (0.5 x 3.0 = 1.5) = 3.5; judgment call
tests.append(
    SampleTextQuestion(
        question=circle_area_question,
        test_answer="A = πr² = π × 3² = 9π",
        expected_score=3.5,
        category="ambiguous_partial",
    )
)

# 16 - correct but verbose (extra correct material around the answer)
tests.append(
    SampleTextQuestion(
        question=newton_question,
        test_answer="""Newton's first law says an object keeps its state of motion unless a force acts on it, and the third law says every action has an equal and opposite reaction. The second law, which is the one that matters here, says the net force on an object equals its mass times its acceleration, F = ma. Rearranging gives a = F / m, so with F = 20 N and m = 4 kg the acceleration is 20 / 4 = 5 m/s², in the direction of the net force. This is also why a heavier object accelerates less under the same force.""",
        expected_score=4.0,
        category="correct_verbose",
    )
)

# 17 - correct number, wrong justification (names the third law as the second law)
# c1 fails (0), c2 met (0.5 x 4.0 = 2.0)
tests.append(
    SampleTextQuestion(
        question=newton_question,
        test_answer="Newton's second law says that every action has an equal and opposite reaction. Dividing the force by the mass, 20 / 4, gives an acceleration of 5 m/s².",
        expected_score=2.0,
        category="correct_wrong_justification",
    )
)

# 18 - correct in substance but poorly organized (meiosis first, no labels, run-on)
tests.append(
    SampleTextQuestion(
        question=mitosis_question,
        test_answer="""At the end there are four cells that each have half the chromosomes and are all different from each other, that's meiosis, and then the other process, mitosis, starts with one cell and ends with two diploid cells that are exact copies of it.""",
        expected_score=4.0,
        category="poorly_organized",
    )
)

# 19 - contradiction: four haploid cells is right, but says all four are identical
# c1 full (2.0) + c2 half (0.5 x 2.0 = 1.0) = 3.0; judgment call
tests.append(
    SampleTextQuestion(
        question=mitosis_question,
        test_answer="Mitosis produces two genetically identical diploid cells. Meiosis produces four haploid cells, and all four are genetically identical to each other.",
        expected_score=3.0,
        category="contradiction",
    )
)

# 20 - missing the logarithmic-scale explanation (c3)
# c1 + c2 met: 5.0 x (0.4 + 0.3) = 3.5
tests.append(
    SampleTextQuestion(
        question=ph_question,
        test_answer="pH 3 is acidic, and it's more acidic than pH 5 because a lower pH means more acidic.",
        expected_score=3.5,
        category="missing_criteria",
    )
)

# 21 - no answer
tests.append(
    SampleTextQuestion(
        question=ph_question,
        test_answer="I don't know.",
        expected_score=0.0,
        category="no_answer",
    )
)

# 22 - off-topic answer (about a different subject entirely)
tests.append(
    SampleTextQuestion(
        question=ph_question,
        test_answer="The French Revolution began in 1789 when citizens stormed the Bastille in Paris.",
        expected_score=0.0,
        category="no_answer",
    )
)

# 23 - correct but terse
tests.append(
    SampleTextQuestion(
        question=binary_search_question,
        test_answer="It halves the search range every step, so O(log n), and the data has to be sorted.",
        expected_score=5.0,
        category="correct_terse",
    )
)

# 24 - right complexity and right requirement, wrong reasoning (hash function)
# c1 fails (0), c2 met (0.4 x 5.0 = 2.0)
tests.append(
    SampleTextQuestion(
        question=binary_search_question,
        test_answer="Binary search is O(log n) because it uses a hash function to jump straight to the right position. The data has to be sorted.",
        expected_score=2.0,
        category="correct_wrong_justification",
    )
)

# 25 - correct but verbose (every extra fact is accurate)
tests.append(
    SampleTextQuestion(
        question=ww1_question,
        test_answer="""On 28 June 1914 Gavrilo Princip, a Bosnian Serb nationalist, assassinated Archduke Franz Ferdinand, the heir to the Austro-Hungarian throne, in Sarajevo. Austria-Hungary blamed Serbia and declared war on it in July. Russia mobilized to support Serbia, Germany stood behind Austria-Hungary, and France, bound to Russia by alliance, was pulled in, with Britain joining soon after, so a regional dispute turned into a continent-wide war. Longer-term tensions such as militarism, imperial rivalry and nationalism had been building for decades and made the alliance system more dangerous.""",
        expected_score=4.0,
        category="correct_verbose",
    )
)

# 26 - contradiction: says the alliances spread the war, then says they had nothing to do with it
# c1 full (2.0) + c2 half (1.0) = 3.0; judgment call (a strict grader may give 2.0)
tests.append(
    SampleTextQuestion(
        question=ww1_question,
        test_answer="The war was triggered by the assassination of Archduke Franz Ferdinand in Sarajevo. The alliance system made it spread, although honestly the alliances had nothing to do with how it spread.",
        expected_score=3.0,
        category="contradiction",
    )
)

# 27 - correct in substance but poorly organized (mechanism first, conclusion last, run-on)
tests.append(
    SampleTextQuestion(
        question=supply_demand_question,
        test_answer="""Sellers notice people lining up, so they raise prices, because more people want the good than there is stock of it, and this keeps going until buyers and sellers are balanced again at a higher price, so yes, the price ends up higher.""",
        expected_score=5.0,
        category="poorly_organized",
    )
)

# 28 - wrong direction
tests.append(
    SampleTextQuestion(
        question=supply_demand_question,
        test_answer="The price falls, because when more people want a good the sellers have to compete harder for customers and lower their prices.",
        expected_score=0.0,
        category="wrong",
    )
)

# 29 - valid alternate method (quadratic formula instead of factoring)
tests.append(
    SampleTextQuestion(
        question=quadratic_question,
        test_answer="Using the quadratic formula with a = 1, b = -5, c = 6: x = (5 ± √(25 - 24)) / 2 = (5 ± 1) / 2, so x = 3 or x = 2.",
        expected_score=5.0,
        category="alternate_method",
    )
)

# 30 - ambiguous partial: both roots correct, but the "method" is guess and check
# c1 full (3.0) + c2 half (0.5 x 2.0 = 1.0) = 4.0; judgment call
tests.append(
    SampleTextQuestion(
        question=quadratic_question,
        test_answer="x = 2 and x = 3. I tried small whole numbers until the equation came out to zero.",
        expected_score=4.0,
        category="ambiguous_partial",
    )
)
