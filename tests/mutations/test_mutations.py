"""Mutation-testing tests: the hidden-test suite must catch intentionally-broken
mutants of the reference solution. Low mutation score => weak tests."""
from src.evaluator.evaluator import Judge
from src.evaluator.mutations import generate_mutants, mutation_score

j = Judge()

REF = """def solve(a, b):
    return a + b"""

TESTS = [{"args": (2, 3), "expected": 5},
         {"args": (-1, 5), "expected": 4},
         {"args": (0, 0), "expected": 0},
         {"args": (7, 8), "expected": 15}]


def test_mutants_generated():
    mutants = list(generate_mutants(REF))
    assert len(mutants) >= 1


def test_mutants_are_mostly_caught():
    score = mutation_score(REF, TESTS, j)
    assert score is not None
    # our tests should catch most (add_to_sub, sub_to_add swaps etc.)
    assert score >= 0.5


def test_weak_tests_let_obvious_bug_through():
    # a single test that can't distinguish + from - on these values
    weak = [{"args": (1, 1), "expected": 2}]  # 1+1==2 and 1-1!=2, so add_to_sub caught;
    # but a test set that's too small may miss other bugs — check at least add_to_sub
    mutants = dict(generate_mutants(REF))
    if "add_to_sub" in mutants:
        r = j.evaluate_problem(mutants["add_to_sub"], weak)
        assert not r["pass_at_1"]
