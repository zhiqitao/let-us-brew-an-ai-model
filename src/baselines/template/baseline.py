"""THE RIVALS — Baseline 1: template / rule system.

A deterministic system that recognizes known linguistic patterns and emits the
corresponding predefined code template. Purpose: how much of the task is solvable
WITHOUT learning?

The template is defined in terms of the SAME operations as the teacher, so it is a
sanity check on the task difficulty — not a learning model.
"""
from src.program_generator.generator import generate_reference

# Simple keyword -> operation heuristics (the "recognized patterns").
PATTERNS = [
    (("sum", "add", "plus"), "add"),
    (("difference", "subtract", "minus", "sub"), "sub"),
    (("product", "multiply", "times", "mul"), "mul"),
    (("maximum", "max of", "larger"), "max_of"),
    (("minimum", "min of", "smaller"), "min_of"),
    (("absolute",), "abs_of"),
    (("sum of the list", "list sum", "sum of a list"), "list_sum"),
    (("length", "len"), "list_len"),
    (("first element",), "first_element"),
]


def detect_operation(prompt):
    p = prompt.lower()
    for keywords, op in PATTERNS:
        if any(k in p for k in keywords):
            return op
    return None


def template_baseline_generate(task):
    """Given a task (with its semantics + prompt), emit a candidate program.

    The template baseline 'recognizes' the operation from the prompt and emits the
    reference program for that operation. If it can't recognize the pattern, it emits
    a stub that won't pass (so its performance reflects real recognition coverage).
    """
    op = detect_operation(task["nl"]["prompt"])
    if op is None:
        return "def solve(*args):\n    return 0"  # deliberately wrong -> won't pass
    # Build a semantics record whose arg names match the detected op's arity.
    sem = dict(task["semantics"])
    sem["operation"] = op
    sem["args"] = _args_for(op, sem.get("args", []))
    try:
        return generate_reference(sem)
    except ValueError:
        return "def solve(*args):\n    return 0"


def _args_for(op, orig_args):
    """Return a fresh args list with names appropriate to `op`'s arity."""
    base = [a["name"] for a in orig_args] or ["a", "b", "c", "x", "xs"]
    arity = {"add": 2, "sub": 2, "mul": 2, "max_of": 2, "min_of": 2,
             "cond_abs_max": 2, "abs_of": 1, "list_sum": 1, "list_len": 1,
             "first_element": 1,
             # composite
             "abs_add": 2, "sub_abs": 2, "max_add": 2, "sum_of_abs": 1,
             "double_first": 1, "len_minus_one": 1}.get(op, 2)
    names = (base + ["a", "b", "c", "x", "y", "xs"])[:arity]
    arg_type = "list" if op in ("list_sum", "list_len", "first_element",
                                "sum_of_abs", "double_first", "len_minus_one") else "int"
    return [{"name": names[i], "type": arg_type, "role": "operand"} for i in range(arity)]
