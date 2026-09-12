"""THE TEACHER — dataset generator (ties the teacher pieces together).

Given a semantic intent, produce a complete Task record (per specs/task_schema_v0_1.json):
  - reference_code   (from program_generator)
  - nl prompt         (from nl_renderer)
  - hidden_tests      (from test_generator)
  - metadata

Also provides `generate_dataset` which samples many semantic intents with controlled
diversity (varying constants, identifiers, wording families) and assigns splits.
"""
import json
import random

from src.program_generator.generator import generate_reference
from src.test_generator.generator import generate_hidden_tests
from src.nl_renderer.renderer import render_nl

# The operations available in the pilot, with arity and arg-types.
OPERATIONS = {
    "add": 2, "sub": 2, "mul": 2,
    "max_of": 2, "min_of": 2, "abs_of": 1,
    "list_sum": 1, "list_len": 1, "first_element": 1,
    "cond_abs_max": 2,
}

# COMPOSITE operations: each composes two primitives. These are held OUT of the
# training set and only appear in the compositional hold-out split, so the model
# must COMPOSE (Level-4 structural generalization) rather than retrieve.
COMPOSITE_OPERATIONS = {
    "abs_add": 2, "sub_abs": 2, "sum_of_abs": 1,
    "max_add": 2, "double_first": 1, "len_minus_one": 1,
}

# Identifier sets: short letter names vs verbose descriptive names. We vary these to
# control for identifier-leakage in surface-generalization experiments.
IDENTIFIER_SETS = {
    "letters": ["a", "b", "c", "x", "y"],
    "words": ["left", "right", "first", "second", "value", "numbers", "items"],
}


def make_semantics(operation, rng, id_set="letters"):
    """Build a `semantics` dict for a task (the ground truth)."""
    from src.data_generator.generator import OPERATIONS, COMPOSITE_OPERATIONS
    n = (OPERATIONS if operation in OPERATIONS else COMPOSITE_OPERATIONS)[operation]
    idents = IDENTIFIER_SETS[id_set][:n + 2]
    names = list(idents[:n])
    arg_type = "list" if operation in ("list_sum", "list_len", "first_element",
                                       "sum_of_abs", "double_first", "len_minus_one") else "int"
    args = [{"name": names[i], "type": arg_type, "role": "operand"} for i in range(n)]
    # In this task family every operation returns an int scalar. Lists appear only
    # as INPUTS (a list of ints); list_sum/list_len/first_element/double_first/
    # len_minus_one all return an int, not the list itself. So output_type is always
    # "int"; only the input types vary.
    return {
        "operation": operation,
        "args": args,
        "input_types": [arg_type] * n,
        "output_type": "int",
        "capability_tags": _tags(operation),
        "complexity": _complexity(operation),
    }


def _tags(op):
    base = ["arithmetic"] if op in ("add", "sub", "mul", "abs_of") else []
    if op in ("max_of", "min_of", "cond_abs_max"):
        base = ["comparison", "conditional"]
    if op in ("list_sum", "list_len", "first_element"):
        base = ["list", "iteration"] if op == "list_sum" else ["list"]
    return base


def _complexity(op):
    return {"add": 1, "sub": 1, "mul": 1, "abs_of": 2,
            "max_of": 2, "min_of": 2, "cond_abs_max": 3,
            "list_sum": 3, "list_len": 2, "first_element": 1}.get(op, 1)


def make_task(operation, task_id, seed, id_set="letters", split="train", family=None):
    """Produce one complete Task record."""
    rng = random.Random(seed)
    sem = make_semantics(operation, rng, id_set)
    ref = generate_reference(sem, rng)
    prompt, fam_name = render_nl(sem, family=family, rng=rng)
    tests = generate_hidden_tests(sem, rng=rng)
    return {
        "task_id": task_id,
        "semantics": sem,
        "reference_code": ref,
        "nl": {"prompt": prompt, "template_family": fam_name, "paraphrase": prompt},
        "hidden_tests": tests,
        "metadata": {
            "linguistic_template": fam_name,
            "paraphrase_family": fam_name,
            "seed": seed,
            "identifier_set": id_set,
        },
        "spec_version": "python_capability_v0_1",
        "dataset_version": "v0_1",
        "split": split,
    }


def generate_dataset(n_per_op=60, id_set="letters", seed=0):
    """Generate a flat dataset of tasks covering all pilot operations.

    `n_per_op` tasks per operation. Returns a list of Task records. Splits are
    assigned by the caller (see scripts/generate_data.py) so train/val/test stay
    semantically disjoint by operation distribution.
    """
    rng = random.Random(seed)
    tasks = []
    for op in OPERATIONS:
        for i in range(n_per_op):
            tasks.append(make_task(op, f"{op}_{i:04d}", seed + i, id_set=id_set))
    return tasks


def generate_compositional(n_per_op=40, id_set="letters", seed=1000):
    """Generate COMPOSITE (held-out) tasks for the structural-generalization split.

    These compose primitives the model was trained on, but the COMBINATION itself
    never appears in training — so the model must compose, not retrieve.
    """
    rng = random.Random(seed)
    tasks = []
    for op in COMPOSITE_OPERATIONS:
        for i in range(n_per_op):
            tasks.append(make_task(op, f"{op}_{i:04d}", seed + i, id_set=id_set))
    return tasks


def all_operation_names():
    return list(OPERATIONS) + list(COMPOSITE_OPERATIONS)


if __name__ == "__main__":
    d = generate_dataset(n_per_op=3, seed=1)
    print(f"generated {len(d)} tasks")
    for t in d[:4]:
        print(f"  op={t['semantics']['operation']:14s} nl={t['nl']['prompt'][:70]!r}")
        print(f"      ref={t['reference_code'].replace(chr(10),' | ')}  tests={len(t['hidden_tests'])}")
