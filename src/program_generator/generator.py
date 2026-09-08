"""THE TEACHER — reference-program generator.

Semantic-first: given a semantic intent dict, generate the ground-truth reference
Python program (a single pure `solve` function). See specs/task_schema_v0_1.json.
"""
import random


def generate_reference(sem, rng=None):
    """Generate reference Python source for a semantic intent.

    `sem` is the `semantics` object from the task schema. Supported operations for
    the pilot:
      add, sub, mul, max_of, min_of, abs_of, list_sum, list_len, first_element,
      cond_abs_max
    Returns the source string (a `def solve(...)` function).
    """
    op = sem["operation"]
    args = sem.get("args", [])
    names = [a["name"] for a in args]

    if op == "add":
        return f"def solve({', '.join(names)}):\n    return {names[0]} + {names[1]}"
    if op == "sub":
        return f"def solve({', '.join(names)}):\n    return {names[0]} - {names[1]}"
    if op == "mul":
        return f"def solve({', '.join(names)}):\n    return {names[0]} * {names[1]}"
    if op == "max_of":
        return (f"def solve({', '.join(names)}):\n"
                f"    if {names[0]} > {names[1]}:\n"
                f"        return {names[0]}\n"
                f"    return {names[1]}")
    if op == "min_of":
        return (f"def solve({', '.join(names)}):\n"
                f"    if {names[0]} < {names[1]}:\n"
                f"        return {names[0]}\n"
                f"    return {names[1]}")
    if op == "abs_of":
        return (f"def solve({names[0]}):\n"
                f"    if {names[0]} < 0:\n"
                f"        return -{names[0]}\n"
                f"    return {names[0]}")
    if op == "list_sum":
        return (f"def solve({names[0]}):\n"
                f"    total = 0\n"
                f"    for x in {names[0]}:\n"
                f"        total = total + x\n"
                f"    return total")
    if op == "list_len":
        return f"def solve({names[0]}):\n    return len({names[0]})"
    if op == "first_element":
        return f"def solve({names[0]}):\n    return {names[0]}[0]"
    if op == "cond_abs_max":
        # max of two numbers, but output absolute value: max(abs(a), abs(b))
        return (f"def solve({', '.join(names)}):\n"
                f"    na = abs({names[0]})\n"
                f"    nb = abs({names[1]})\n"
                f"    if na > nb:\n"
                f"        return na\n"
                f"    return nb")
    # ---- COMPOSITE operations (structural generalization tests) ----
    # Each composes two primitives. These are held OUT of training and only appear
    # in the compositional test split, so the model must COMPOSE, not retrieve.
    if op == "abs_add":
        # return abs(a) + abs(b)  (abs + add)
        return (f"def solve({', '.join(names)}):\n"
                f"    return abs({names[0]}) + abs({names[1]})")
    if op == "sub_abs":
        # return abs(a - b)  (sub then abs)
        return f"def solve({', '.join(names)}):\n    return abs({names[0]} - {names[1]})"
    if op == "sum_of_abs":
        # return sum([abs(x) for x in xs])  (abs composed over a list sum)
        return (f"def solve({names[0]}):\n"
                f"    total = 0\n"
                f"    for x in {names[0]}:\n"
                f"        if x < 0:\n"
                f"            total = total + (-x)\n"
                f"        else:\n"
                f"            total = total + x\n"
                f"    return total")
    if op == "max_add":
        # return max(a + b, a - b) using a 2-arg signature (add and sub composed
        # under max). Names: (x, y).
        return (f"def solve({', '.join(names)}):\n"
                f"    s = {names[0]} + {names[1]}\n"
                f"    d = {names[0]} - {names[1]}\n"
                f"    if s > d:\n"
                f"        return s\n"
                f"    return d")
    if op == "double_first":
        # return 2 * xs[0]  (index + mul)
        return (f"def solve({names[0]}):\n"
                f"    return 2 * {names[0]}[0]")
    if op == "len_minus_one":
        # return len(xs) - 1  (len + sub)
        return f"def solve({names[0]}):\n    return len({names[0]}) - 1"
    raise ValueError(f"unsupported operation: {op}")
