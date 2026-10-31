# Appendix A — An Annotated Tour of the Generator

Chapter 5 describes the teacher conceptually. This appendix shows the actual source, so we can see — and reproduce — exactly how the data was made. All of this lives in
`src/data_generator/` and `src/program_generator/`, `src/nl_renderer/`,
`src/test_generator/` in the companion repository.

A note on what follows: this is a **condensed, annotated excerpt** of the
real generator, not a complete runnable file. Where a section repeats in the same
style for every operation, we mark it with an ellipsis (`...`). A few helpers that
would be defined elsewhere in the source — the `OPERATIONS` table, `_rand`, and
`_expected` — are used here as-is; the point is to show the *shape* of each part and
how the semantic record flows through it, not to provide every line that would appear
in a standalone module. The full, runnable source is in the repository.

## The one line that ties it together

The whole generator is this single function. Given an operation and a seed, it builds
the semantic intent and then generates everything else from it:

```
def make_task(operation, task_id, seed, id_set="letters", split="train",
              family=None):
    rng = random.Random(seed)
    sem = make_semantics(operation, rng, id_set)     # the ground truth
    ref = generate_reference(sem, rng)               # the correct Python
    prompt, fam_name = render_nl(sem, family=family, rng=rng)  # the English
    tests = generate_hidden_tests(sem, rng=rng)      # the hidden tests
    return {
        "task_id": task_id,
        "semantics": sem,
        "reference_code": ref,
        "nl": {"prompt": prompt, "template_family": fam_name},
        "hidden_tests": tests,
        "metadata": {"seed": seed, "identifier_set": id_set,
                     "paraphrase_family": fam_name},
        "spec_version": "python_capability_v0_1",
        "dataset_version": "v0_1",
        "split": split,
    }
```

That's the whole architecture in ten lines. Everything below is one of the four
building blocks it calls.

## 1. The semantics

```
IDENTIFIER_SETS = {
    "letters": ["a", "b", "c", "x", "y"],
    "words":   ["left", "right", "first", "second", "value", "numbers", "items"],
}

def make_semantics(operation, rng, id_set="letters"):
    n = OPERATIONS[operation]                      # arity
    names = list(IDENTIFIER_SETS[id_set][:n])      # pick names from the set
    arg_type = ("list" if operation in
                ("list_sum", "list_len", "first_element") else "int")
    # Every operation here returns an int scalar. Lists appear only as INPUTS
    # (a list of ints); list_sum/list_len/first_element all return an int, not
    # the list itself. So output_type is always "int"; only input_types vary.
    output_type = "int"
    args = [{"name": names[i], "type": arg_type, "role": "operand"} for i in range(n)]
    return {"operation": operation, "args": args,
            "input_types": [arg_type] * n, "output_type": output_type}
```

*This is the pilot's condensed type-dispatch excerpt, so it marks only the three
pilot list-operations as list-input. It is **not** the full dictionary* — the composite
list operations (`sum_of_abs`, `double_first`, `len_minus_one`) also take a list but are
built by the composition path, not this condensed excerpt; the shipped
`make_semantics` itself serves both `OPERATIONS` and `COMPOSITE_OPERATIONS`. For the
complete per-operation input types see the operation
dictionary in Appendix C, which lists every operation's arity, input type, and
`class`.

## 2. The reference program

The reference generator reads the semantics and emits the correct Python. A few cases:

```
def generate_reference(sem, rng=None):
    op = sem["operation"]; names = [a["name"] for a in sem["args"]]
    if op == "add":
        return (f"def solve({', '.join(names)}):\n"
                f"    return {names[0]} + {names[1]}")
    if op == "list_sum":
        return (f"def solve({names[0]}):\n    total = 0\n"
                f"    for x in {names[0]}:\n        total = total + x\n"
                f"    return total")
    # ... and so on for every operation, in the same style.
```

## 3. The natural-language renderer

The renderer phrases the same semantics several ways. Each **template family** is a
function:

```
def _a(op, names, rng):   # family "a"
    x, y = names[0], names[1]
    return (f"Write a function that takes two numbers, {x} and {y}, "
            f"and returns their {_op_noun(op)}.")

def _b(op, names, rng):   # family "b"
    x, y = names[0], names[1]
    return (f"Implement solve so that given {x} and {y} "
            f"it returns their {_op_noun(op)}.")

def _c(op, names, rng):   # family "c"
    x, y = names
    return (f"Define a function solve({x}, {y}) "
            f"that returns {x} {_op_sym(op)} {y}.")

# Each operation has its own set of families; _op_noun/_op_sym map an operation
# to the right word ("sum", "product", ...) and symbol ("+", "*", ...), so the
# same families work for every operation, not just addition.
FAMILIES = {"add": [_a, _b, _c], "mul": [_a, _b, _c], ...}
```

The semantics is fixed; only the wording changes. That is the entire point.

## 4. The hidden tests

Tests are generated from the semantics, with deliberate edge-case coverage. The
expected value is computed by the operation itself — not copied from the reference:

```
def generate_hidden_tests(sem, rng=None, count=8):
    op = sem["operation"]; args = sem["args"]; tests = []
    def add(*vals, note="basic"):
        tests.append({"args": list(vals),
                      "expected": _expected(op, vals), "note": note})
    add(_rand(rng), _rand(rng), note="basic")     # ordinary
    add(0, _rand(rng), note="zero")               # zero
    add(-_rand(rng), -_rand(rng), note="negative")# negative
    add(_rand(rng, 900, 1000), _rand(rng), note="large")  # large
    # ... edge cases for the specific operation
    return tests[:count]
```

## 5. The operation-classification audit

Finally, the generator is checked. The audit trains a trivial classifier to see whether
the wording reveals the operation. Note: the vectorizer must be fitted **inside** the
cross-validation folds, not once on the whole dataset, or the model sees the test wording
during fitting. The corrected form uses a `Pipeline`:

```
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

clf = Pipeline([
    ("vec", TfidfVectorizer()),
    ("clf", LogisticRegression(max_iter=1000)),
])
X = [t["nl"]["prompt"] for t in tasks]
y = [t["semantics"]["operation"] for t in tasks]   # the operation label each prompt maps to
scores = cross_val_score(clf, X, y, cv=5)
print(f"classifier predicts operation: {scores.mean():.3f}")   # = wording carries operation signal
```

When we first ran the equivalent diagnostic on the original pilot renderer, it printed
**1.000** — the wording perfectly predicted the operation. It is important to read this
correctly: much of that is **task signal, not leakage**. The prompt must name the
operation ("sum", "absolute value"), so a classifier can trivially recover it from the
wording; that is the task being solvable as stated, not a defect. So the high score
measures **how separable the operations are by wording** — i.e. whether the prompt reads
as a clean task spec — and we should not call it a "leakage" measure or equate it with
"overlap." The audit's real purpose is to catch the *opposite* problem — where some
*other* accidental cue (a duplicated example, a leaked hidden-test value, an identifier
that reveals the answer) drives the score. We therefore treat the vocabulary separability
as a first check and separately inspect for duplicated examples and accidental cues,
rather than reading one number as proof of leakage.

## How to run it

```
python scripts/generate_data.py --n-per-op 200   # writes pilot_train/val/test + manifest
python scripts/audit.py                          # runs the leakage audit
```

That's the teacher. It's not magic — it's a controlled generator, audited for
fairness, that makes the entire experimental program possible.
