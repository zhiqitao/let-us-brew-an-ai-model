"""Tests for the Judge evaluation pipeline."""
import pytest
from src.evaluator.evaluator import Judge

j = Judge()
GOOD = "def solve(a, b):\n    return a + b"
TESTS = [{"args": (2, 3), "expected": 5, "note": "basic"},
         {"args": (-1, 5), "expected": 4, "note": "negative"},
         {"args": (0, 0), "expected": 0, "note": "zero"},
         {"args": (100, 200), "expected": 300, "note": "large"}]


def test_correct_passes_all():
    r = j.evaluate_problem(GOOD, TESTS)
    assert r["syntax_ok"]
    assert r["capability_ok"]
    assert r["tests_passed"] == 4
    assert r["pass_at_1"]


def test_wrong_program_fails():
    bad = "def solve(a, b):\n    return a - b"
    r = j.evaluate_problem(bad, TESTS)
    assert not r["pass_at_1"]
    assert r["tests_passed"] < 4


def test_syntax_failure_detected():
    r = j.evaluate_problem("def solve(a,b):\n return a +", TESTS)
    assert not r["syntax_ok"]
    assert not r["pass_at_1"]


def test_disallowed_construct_fails():
    r = j.evaluate_problem("def solve(a,b):\n    return __import__('os').getcwd()", TESTS)
    assert not r["syntax_ok"]
    assert not r["pass_at_1"]


def test_assignment_not_semantic_equality():
    # output equal by value even if types differ in representation
    src = "def solve(xs):\n    return [x for x in xs]"  # listcomp — should be rejected
    r = j.evaluate_problem(src, [{"args": ([1, 2],), "expected": [1, 2]}])
    assert not r["pass_at_1"]
