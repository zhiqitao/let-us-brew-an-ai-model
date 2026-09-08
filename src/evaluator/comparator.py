"""THE JUDGE — semantic comparison.

Defines how a program's output is compared to an expected value. Does NOT assume
string equality; handles ints, floats (tolerance), booleans, strings, lists, nested
lists, dicts (order-insensitive), and nested structures.
"""
import math

FLOAT_TOLERANCE = 1e-9  # absolute, per spec v0_1


def semantic_equal(a, b, tol=FLOAT_TOLERANCE):
    """Return True if `a` and `b` are semantically equal under the comparison rule."""
    # scale down to the type-specific comparator
    return _eq(a, b, tol)


def _eq(a, b, tol):
    # numeric
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, int) and isinstance(b, int):
            return a == b
        return abs(a - b) <= tol
    # strings
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    # lists / tuples
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(_eq(x, y, tol) for x, y in zip(a, b))
    # dicts
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_eq(a[k], b[k], tol) for k in a)
    # None / other
    if a is None or b is None:
        return a is b
    return a == b


def describe(a):
    """Human-readable type string, for reporting mismatches."""
    return type(a).__name__
