"""Conformance tests for the sandbox AST whitelist + restricted execution."""
import pytest
from src.sandbox import sandbox


GOOD = "def solve(a, b):\n    return a + b"


def test_valid_program_runs():
    assert sandbox.execute_function(GOOD, (5, 10)) == 15


def test_valid_loop():
    src = "def solve(xs):\n    total = 0\n    for x in xs:\n        total = total + x\n    return total"
    assert sandbox.execute_function(src, ([1, 2, 3],)) == 6


def test_valid_conditional():
    src = "def solve(a, b):\n    if a > b:\n        return a\n    return b"
    assert sandbox.execute_function(src, (3, 7)) == 7


@pytest.mark.parametrize("bad,expect_substr", [
    ("import os", "Import"),
    ("from os import system", "Import"),
    ("def solve(a,b):\n    return eval('1+1')", "builtin"),
    ("class X:\n    pass", "ClassDef"),
    ("def solve(a,b):\n    return open('x')", "builtin"),
    ("def solve(a,b):\n    return __import__('os')", "builtin"),
    ("def solve(a,b):\n    try:\n        return a\n    except:\n        return b", "Try"),
    ("def solve(a,b):\n    return a if a > b else b", "IfExp"),
    ("def solve(xs):\n    return [x for x in xs]", "ListComp"),
    ("def solve(a,b):\n    return lambda x: x", "Lambda"),
])
def test_forbidden_constructs_rejected(bad, expect_substr):
    with pytest.raises(sandbox.SandboxError) as exc:
        sandbox.validate_source(bad)
    assert expect_substr in str(exc.value)


def test_syntax_error_rejected():
    with pytest.raises(sandbox.SandboxError):
        sandbox.validate_source("def solve(a, b):\n    return a +")


def test_non_single_function_rejected():
    with pytest.raises(sandbox.SandboxError):
        sandbox.execute_function("def foo():\n    return 1\n\ndef solve(a,b):\n    return a+b", (1, 2))
