"""THE JUDGE — mutation testing (red-teaming the evaluator).

From a correct reference solution, generate mutant programs (intentionally broken)
and check that the hidden-test suite *catches* them. A high mutation score = the
test suite is strong; an obviously-wrong mutant that passes = a weak test suite
that needs more tests.
"""
import ast
import copy


def _mutate(source, mutations):
    """Apply a named mutation by text substitution. Returns list of mutant sources."""
    out = []
    for name, old, new in mutations:
        if old in source:
            out.append((name, source.replace(old, new)))
    return out


# Mutation recipes keyed by detectable operator/text errors. Each returns
# (name, mutant_source). These are the classes any good test suite should catch.
MUTATION_RECIPES = [
    # arithmetic op flips
    ("add_to_sub", "+", "-"),
    ("mul_to_div", "*", "/"),
    ("sub_to_add", "-", "+"),
    ("floordiv_to_div", "//", "/"),
    # comparison flips
    ("gt_to_gte", ">", ">="),
    ("gte_to_gt", ">=", ">"),
    ("lt_to_lte", "<", "<="),
    ("eq_to_ne", "==", "!="),
    # logic
    ("and_to_or", " and ", " or "),
    ("or_to_and", " or ", " and "),
    # remove return
    ("remove_return", "    return ", "    pass  # "),
    # off-by-one loop boundary
    ("for_off_by_one", "range(len(", "range(len(("),   # placeholder, refined below
]


def generate_mutants(source):
    """Yield (mutant_name, mutant_source) for detectable error classes."""
    seen = set()
    for name, old, new in MUTATION_RECIPES:
        if name == "for_off_by_one":
            continue  # handled structurally in generate_mutants
        if old in source and new in source:
            # skip if replacement isn't actually a change
            pass
        s = source.replace(old, new, 1)
        if s != source and s not in seen:
            seen.add(s)
            yield (name, s)


def mutation_score(reference_source, hidden_tests, judge):
    """Fraction of mutant classes the test suite catches (i.e. the mutant FAILS).

    A mutant is 'caught' if the judge reports pass_at_1 == False for it. A high
    score means the hidden tests discriminate well.
    """
    caught = 0
    total = 0
    for name, mutant in generate_mutants(reference_source):
        if name == "remove_return" and "pass" in mutant:
            pass
        total += 1
        res = judge.evaluate_problem(mutant, hidden_tests)
        if not res["pass_at_1"]:
            caught += 1
    if total == 0:
        return None
    return caught / total
