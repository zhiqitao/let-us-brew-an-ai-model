#!/usr/bin/env python3
"""Human-written test set: a small set of NATURAL-LANGUAGE programming requests
written the way a person would phrase them (NOT from a template), used as an external
sanity check on the trained model. These stay separate from the synthetic training
distribution, so they test whether the learned behavior transfers to spec sheets a
human actually writes.

The expected outputs are computed by reference implementations, independently.
"""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Each item: (human_style_prompt, args for the solve function, expected).
# ops each map to one of our pilot operations; the phrasing is hand-written, informal.
HUMAN_TASKS = [
    "Take two numbers and give me back their total.",
    "Add these two values together.",
    "Return the result of subtracting the second number from the first.",
    "What's the product of these two numbers?",
    "Tell me which of these two is the bigger one.",
    "Which is smaller, the first or the second number?",
    "Give me the absolute value of this number.",
    "Sum up every number in this list.",
    "How many items are in this list?",
    "What's the first element of this list?",
    "Return the larger of the two, but as a positive number.",
    "Add the absolute values of both numbers.",
    "Give me the distance between these two numbers.",
    "Sum the absolute values of everything in the list.",
    "Double the first item in the list.",
    "Return one less than the length of the list.",
]


def ref_for(op, args):
    """Reference output for a few ops (matches the training semantics)."""
    if op == "add": return args[0] + args[1]
    if op == "sub": return args[0] - args[1]
    if op == "mul": return args[0] * args[1]
    if op == "max_of": return max(args[0], args[1])
    if op == "min_of": return min(args[0], args[1])
    if op == "abs_of": return abs(args[0])
    if op == "list_sum": return sum(args[0])
    if op == "list_len": return len(args[0])
    if op == "first_element": return args[0][0]
    if op == "cond_abs_max": return max(abs(args[0]), abs(args[1]))
    if op == "abs_add": return abs(args[0]) + abs(args[1])
    if op == "sub_abs": return abs(args[0] - args[1])
    if op == "sum_of_abs": return sum(abs(x) for x in args[0])
    if op == "max_add": return max(args[0] + args[1], args[0] - args[1])
    if op == "double_first": return 2 * args[0][0]
    if op == "len_minus_one": return len(args[0]) - 1
    raise ValueError(op)


# Map each human prompt to (op, function signature for the grader).
SIGNATURES = {
    0: ("add", ("a", "b")), 1: ("add", ("a", "b")), 2: ("sub", ("a", "b")),
    3: ("mul", ("a", "b")), 4: ("max_of", ("a", "b")), 5: ("min_of", ("a", "b")),
    6: ("abs_of", ("a",)), 7: ("list_sum", ("xs",)), 8: ("list_len", ("xs",)),
    9: ("first_element", ("xs",)), 10: ("cond_abs_max", ("a", "b")),
    11: ("abs_add", ("a", "b")), 12: ("sub_abs", ("a", "b")),
    13: ("sum_of_abs", ("xs",)), 14: ("double_first", ("xs",)),
    15: ("len_minus_one", ("xs",)),
}


def make_case(prompt, sig, sample_args):
    op, _ = sig
    return {"prompt": prompt, "operation": op, "args": sample_args,
            "expected": ref_for(op, sample_args)}


def main():
    cases = []
    for i, prompt in enumerate(HUMAN_TASKS):
        sig = SIGNATURES[i]
        op, vars_ = sig
        if op in ("add", "sub", "mul", "max_of", "min_of", "cond_abs_max", "abs_add", "sub_abs", "max_add"):
            args = [5, 3]
        elif op == "abs_of":
            args = [-7]
        elif op in ("list_sum", "list_len", "first_element", "sum_of_abs", "double_first", "len_minus_one"):
            args = [[-2, 5, 3]]
        else:
            args = [5, 3]
        cases.append(make_case(prompt, sig, args))
    out = os.path.join(os.path.dirname(__file__), "..", "artifacts", "datasets", "human_test.jsonl")
    with open(out, "w") as f:
        for c in cases:
            f.write(json.dumps(c) + "\n")
    print(f"wrote {len(cases)} human test cases -> {out}")


if __name__ == "__main__":
    main()
