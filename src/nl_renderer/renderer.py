"""THE TEACHER — natural-language renderer.

Renders a semantic intent into a natural-language specification for the model.
Supports MULTIPLE paraphrase/template families so we can test surface generalization
and audit wording leakage. The same semantics must map to many wordings.
"""
import random


# Each template family is a function(sem, names) -> NL prompt. We keep multiple
# families per operation so a task can be rendered in lots of ways.
def _a(op, names, rng):
    x, y = names[0], names[1]
    return (f"Write a function that takes two numbers, {x} and {y}, "
            f"and returns {_op_verb(op)} of them.")


def _b(op, names, rng):
    x, y = names[0], names[1]
    return (f"Implement solve so that given {x} and {y} it returns "
            f"their {_op_noun(op)}.")


def _c(op, names, rng):
    x, y = names
    return (f"Define a function solve({x}, {y}) that returns {x} {_op_sym(op)} {y} "
            f"when the operation is {_op_name(op)}.")


def _list_a(op, names, rng):
    x = names[0]
    return f"Write a function that takes a list {x} and returns its {_op_noun(op)}."


def _list_b(op, names, rng):
    x = names[0]
    return (f"Implement solve so that given a list of numbers {x}, "
            f"it returns {_op_phrase(op)} of the list.")


def _unary_a(op, names, rng):
    x = names[0]
    return f"Write a function that takes a number {x} and returns its absolute value."


def _comp_add_abs(op, names, rng):
    x, y = names[0], names[1]
    return (f"Write a function that takes two numbers {x} and {y}, takes the absolute "
            f"value of each, and returns their sum.")


def _comp_sub_abs(op, names, rng):
    x, y = names[0], names[1]
    return f"Write a function that returns the absolute value of {x} minus {y}."


def _comp_sum_abs(op, names, rng):
    x = names[0]
    return (f"Write a function that takes a list of numbers {x} and returns the sum "
            f"of the absolute value of each element.")


def _comp_max_add(op, names, rng):
    x, y = names[0], names[1]
    return (f"Write a function that, given {x} and {y}, returns whichever is larger: "
            f"{x} plus {y}, or {x} minus {y}.")


def _comp_double_first(op, names, rng):
    x = names[0]
    return f"Write a function that takes a list {x} and returns twice its first element."


def _comp_len_minus_one(op, names, rng):
    x = names[0]
    return f"Write a function that takes a list {x} and returns one less than its length."


FAMILIES = {
    "add": [_a, _b, _c],
    "sub": [_a, _b, _c],
    "mul": [_a, _b, _c],
    "max_of": [_a, _b],
    "min_of": [_a, _b],
    "abs_of": [_unary_a],
    "list_sum": [_list_a, _list_b],
    "list_len": [_list_a, _list_b],
    "first_element": [_list_a, _list_b],
    "cond_abs_max": [_a],
    # composite (held out of training; only for compositional test split)
    "abs_add": [_comp_add_abs],
    "sub_abs": [_comp_sub_abs],
    "sum_of_abs": [_comp_sum_abs],
    "max_add": [_comp_max_add],
    "double_first": [_comp_double_first],
    "len_minus_one": [_comp_len_minus_one],
}


def _op_verb(op):
    return {"add": "the sum", "sub": "the difference", "mul": "the product",
            "max_of": "the maximum", "min_of": "the minimum"}.get(op, op)


def _op_noun(op):
    return {"add": "sum", "sub": "difference", "mul": "product",
            "max_of": "maximum", "min_of": "minimum",
            "list_sum": "sum", "list_len": "length",
            "first_element": "first element"}.get(op, op)


def _op_sym(op):
    return {"add": "+", "sub": "-", "mul": "*"}.get(op, op)


def _op_name(op):
    return op


def _op_phrase(op):
    return {"list_sum": "the sum", "list_len": "the length",
            "first_element": "the first element"}.get(op, op)


def render_nl(sem, family=None, rng=None):
    """Return a natural-language prompt for a semantic intent.

    `family` selects a specific template family (a function); if None, a random one
    is chosen (for diversity). Returns (prompt, family_name).
    """
    if rng is None:
        rng = random.Random()
    op = sem["operation"]
    fams = FAMILIES.get(op, [_a])
    fam = family if family is not None else rng.choice(fams)
    names = [a["name"] for a in sem.get("args", [])]
    prompt = fam(op, names, rng)
    return prompt, getattr(fam, "__name__", "family")
