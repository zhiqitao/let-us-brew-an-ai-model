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
    # Reuse the semantics' arg names; regenerate reference for the detected op.
    sem = dict(task["semantics"]); sem["operation"] = op
    try:
        return generate_reference(sem)
    except ValueError:
        return "def solve(*args):\n    return 0"
