"""THE TEACHER — hidden-test generator.

Given a semantic intent, generate an independent set of hidden tests. Tests must
cover ordinary, zero, negative, boundary, repeated, large, and edge cases. They are
generated from the SEMANTICS (not by copying the reference program), so a model that
merely memorizes the reference still can't predict the exact test suite.
"""
import random

EDGE_NOTES = ["basic", "zero", "negative", "large", "boundary"]


def _rand_int(rng, lo=-100, hi=100):
    return rng.randint(lo, hi)


def generate_hidden_tests(sem, rng=None, count=8):
    """Generate a list of {"args": [...], "expected": ..., "note": ...} tests."""
    if rng is None:
        rng = random.Random()
    op = sem["operation"]
    args = sem.get("args", [])
    n = len(args)
    tests = []

    def add(*vals, note="basic"):
        tests.append({"args": list(vals), "expected": _expected(op, vals), "note": note})

    if op in ("add", "sub", "mul", "max_of", "min_of", "cond_abs_max"):
        # ordinary
        a = _rand_int(rng); b = _rand_int(rng)
        add(a, b, note="basic")
        # zero
        add(0, _rand_int(rng), note="zero")
        add(_rand_int(rng), 0, note="zero")
        # negative
        add(-_rand_int(rng, 1, 50), -_rand_int(rng, 1, 50), note="negative")
        # boundary: equal, and large magnitude
        add(7, 7, note="boundary-equal")
        add(0, 0, note="boundary-zero")
        add(_rand_int(rng, 900, 1000), _rand_int(rng, 900, 1000), note="large")
        add(-_rand_int(rng, 900, 1000), -_rand_int(rng, 900, 1000), note="large-negative")
        # one more random
        add(_rand_int(rng), _rand_int(rng), note="random")

    elif op in ("list_sum", "list_len", "first_element"):
        xs = [_rand_int(rng) for _ in range(rng.randint(1, 6))]
        # empty where semantically legal
        if op == "list_sum":
            add([], note="empty")
        if op == "list_len":
            add([], note="empty")
        add(xs, note="basic")
        add([0, 0, 0], note="zeros")
        add([-_rand_int(rng, 1, 9) for _ in range(3)], note="negative")
        add([_rand_int(rng, 100, 999) for _ in range(4)], note="large")
        add([5], note="single")
        add(0 if False else xs, note="reuse")

    elif op == "abs_of":
        add(_rand_int(rng), note="basic")
        add(0, note="zero")
        add(-_rand_int(rng, 1, 50), note="negative")
        add(-_rand_int(rng, 900, 999), note="large-negative")

    # cap count
    return tests[:count]


def _expected(op, vals):
    """Compute expected output from the semantics (not the reference program)."""
    if op == "add":
        return vals[0] + vals[1]
    if op == "sub":
        return vals[0] - vals[1]
    if op == "mul":
        return vals[0] * vals[1]
    if op == "max_of":
        return max(vals[0], vals[1])
    if op == "min_of":
        return min(vals[0], vals[1])
    if op == "cond_abs_max":
        return max(abs(vals[0]), abs(vals[1]))
    if op == "abs_of":
        return abs(vals[0])
    if op == "list_sum":
        return sum(vals[0])
    if op == "list_len":
        return len(vals[0])
    if op == "first_element":
        return vals[0][0]
    raise ValueError(f"unsupported operation: {op}")
