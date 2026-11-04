"""Expanded wording-family inventory for the CORRECTED diversity experiment (B2).

The original `src/nl_renderer/renderer.py` FAMILIES give only 1-3 phrasings per
primitive operation (21 family entries total), so the old `scripts/run_diversity.py`
"high-diversity" pool was FAMILIES x 2 identifier sets = 42 records and
`pool[:1200]` silently returned 42 — the arms were never equal-count (review
P0-02 for this experiment).

This module ADDS, without touching the existing renderer:

  * EXTRA_FAMILIES      10 additional phrasing templates per primitive
                        operation (train-eligible), on top of the existing
                        FAMILIES -> train pool of 11-13 families per op;
  * HELD_OUT_FAMILIES    2 further phrasing templates per operation that are
                        reserved EXCLUSIVELY for the held-out-family test and
                        must never appear in any training arm;
  * EXTRA_IDENTIFIER_SETS  3 additional identifier sets (greek/colors/animals)
                        so the identifier dimension has 5 sets total
                        (letters, words + these), satisfying the >=3-4 sets
                        requirement for the high-diversity arm.

Every template interpolates the identifier names, so (family, id_set) uniquely
determines the prompt, and (op, id_set) uniquely determines the program — the
equal-count arm builder can therefore hit exact unique-pair targets.

Usage: imported only by scripts/run_diversity_corrected.py.
"""

# ---------------------------------------------------------------------------
# Per-operation result phrasing (all 10 primitive operations).
# ---------------------------------------------------------------------------
_RESULT_PHRASE = {
    "add": "the sum of the two numbers",
    "sub": "the first number minus the second",
    "mul": "the product of the two numbers",
    "max_of": "the larger of the two numbers",
    "min_of": "the smaller of the two numbers",
    "cond_abs_max": "the larger of the two absolute values",
    "abs_of": "the absolute value of the number",
    "list_sum": "the total of all elements in the list",
    "list_len": "the number of elements in the list",
    "first_element": "the first element of the list",
}

_LIST_OPS = {"list_sum", "list_len", "first_element"}


def _args_desc(op, names):
    """(human description of the inputs, solve() signature) for an operation."""
    if op in _LIST_OPS:
        return f"the list {names[0]}", f"{names[0]}"
    if op == "abs_of":
        return f"the number {names[0]}", f"{names[0]}"
    return (f"the two numbers {names[0]} and {names[1]}",
            f"{names[0]}, {names[1]}")


# ---------------------------------------------------------------------------
# 10 train-eligible phrasing templates per operation.
# Each is a family function (op, names, rng) -> prompt, like the renderer's.
# ---------------------------------------------------------------------------
def t01(op, names, rng):
    desc, sig = _args_desc(op, names)
    return (f"Please write a Python function solve({sig}) which accepts {desc} "
            f"and returns {_RESULT_PHRASE[op]}.")


def t02(op, names, rng):
    desc, _ = _args_desc(op, names)
    return (f"I need a function named solve. Given {desc}, it should give back "
            f"{_RESULT_PHRASE[op]}.")


def t03(op, names, rng):
    desc, sig = _args_desc(op, names)
    return (f"Create solve({sig}): for {desc}, the answer is "
            f"{_RESULT_PHRASE[op]}.")


def t04(op, names, rng):
    desc, _ = _args_desc(op, names)
    return (f"Your task is to implement solve so that, when passed {desc}, it "
            f"produces {_RESULT_PHRASE[op]}.")


def t05(op, names, rng):
    desc, sig = _args_desc(op, names)
    return (f"Could you code up solve({sig})? It takes {desc} and hands back "
            f"{_RESULT_PHRASE[op]}.")


def t06(op, names, rng):
    desc, sig = _args_desc(op, names)
    return (f"Write the function solve({sig}) so it computes "
            f"{_RESULT_PHRASE[op]} from {desc}.")


def t07(op, names, rng):
    desc, _ = _args_desc(op, names)
    return (f"Compose a small function called solve. Input: {desc}. It should "
            f"yield {_RESULT_PHRASE[op]}.")


def t08(op, names, rng):
    desc, sig = _args_desc(op, names)
    return (f"Implement solve({sig}) such that its output for {desc} is "
            f"{_RESULT_PHRASE[op]}.")


def t09(op, names, rng):
    desc, sig = _args_desc(op, names)
    return (f"Here is what solve({sig}) must do: read {desc} and answer with "
            f"{_RESULT_PHRASE[op]}.")


def t10(op, names, rng):
    desc, sig = _args_desc(op, names)
    return (f"Define solve({sig}) to take {desc} and hand you "
            f"{_RESULT_PHRASE[op]}.")


# ---------------------------------------------------------------------------
# 2 HELD-OUT phrasing templates per operation: reserved exclusively for the
# held-out-family test; never used to train either arm.
# ---------------------------------------------------------------------------
def h01(op, names, rng):
    desc, sig = _args_desc(op, names)
    return (f"Kindly draft solve({sig}) so that from {desc} it yields "
            f"{_RESULT_PHRASE[op]}.")


def h02(op, names, rng):
    desc, sig = _args_desc(op, names)
    return (f"Suppose you are given {desc}; the function solve({sig}) should "
            f"reply with {_RESULT_PHRASE[op]}.")


_ALL_PRIMITIVE_OPS = ["add", "sub", "mul", "max_of", "min_of", "abs_of",
                      "list_sum", "list_len", "first_element", "cond_abs_max"]

# 10 train-eligible extra families per operation (on top of renderer.FAMILIES).
EXTRA_FAMILIES = {op: [t01, t02, t03, t04, t05, t06, t07, t08, t09, t10]
                  for op in _ALL_PRIMITIVE_OPS}

# 2 held-out families per operation (never trained).
HELD_OUT_FAMILIES = {op: [h01, h02] for op in _ALL_PRIMITIVE_OPS}

# 3 additional identifier sets -> 5 total with the existing letters/words.
# Valid Python identifiers; >=3 names so 2-arity operations resolve.
EXTRA_IDENTIFIER_SETS = {
    "greek": ["alpha", "beta", "gamma", "delta", "epsilon"],
    "colors": ["red", "blue", "green", "yellow", "purple"],
    "animals": ["cat", "dog", "bird", "fish", "lion"],
}

# Identifier sets used by the HIGH-diversity arm (letters is the LOW arm's
# single set; all five are familiar to the high arm).
HIGH_ID_SETS = ["letters", "words", "greek", "colors", "animals"]
LOW_ID_SET = "letters"

N_TRAIN_EXTRA = 10  # extra families per op that are train-eligible