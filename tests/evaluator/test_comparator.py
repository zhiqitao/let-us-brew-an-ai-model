"""Tests for the semantic comparator."""
import pytest
from src.evaluator.comparator import semantic_equal, FLOAT_TOLERANCE


def test_ints():
    assert semantic_equal(5, 5)
    assert not semantic_equal(5, 6)


def test_floats_tolerance():
    assert semantic_equal(0.1 + 0.2, 0.3)  # within 1e-9
    assert not semantic_equal(0.1 + 0.2, 0.31)


def test_bools_are_bools():
    assert semantic_equal(True, True)
    # bool is not numerically equal to 1 under our rule
    assert not semantic_equal(True, 1)
    assert not semantic_equal(1, True)


def test_strings():
    assert semantic_equal("hello", "hello")
    assert not semantic_equal("hello", "world")


def test_lists():
    assert semantic_equal([1, 2, 3], [1, 2, 3])
    assert not semantic_equal([1, 2], [1, 2, 3])


def test_nested_lists():
    assert semantic_equal([1, [2, [3, 4]]], [1, [2, [3, 4]]])
    assert not semantic_equal([1, [2, 3]], [1, [2, 4]])


def test_dicts_order_insensitive():
    assert semantic_equal({"a": 1, "b": 2}, {"b": 2, "a": 1})
    assert not semantic_equal({"a": 1, "b": 2}, {"a": 1, "b": 3})


def test_none():
    assert semantic_equal(None, None)
    assert not semantic_equal(None, 0)
