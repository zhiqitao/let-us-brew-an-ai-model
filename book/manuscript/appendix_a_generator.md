# Appendix A — The Generator, Every Piece

Chapter 5 describes the teacher conceptually. This appendix shows the actual source,
so you can see — and reproduce — exactly how the data was made. All of this lives in
`src/data_generator/` and `src/program_generator/`, `src/nl_renderer/`,
`src/test_generator/` in the companion repository.

## The one line that ties it together

The whole generator is this single function. Given an operation and a seed, it builds
the semantic intent and then generates everything else from it:

```python
def make_task(operation, task_id, seed, id_set="letters", split="train", family=None):
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

```python
IDENTIFIER_SETS = {
    "letters": ["a", "b", "c", "x", "y"],
    "words":   ["left", "right", "first", "second", "value", "numbers", "items"],
}

def make_semantics(operation, rng, id_set="letters"):
    n = OPERATIONS[operation]                      # arity
    names = list(IDENTIFIER_SETS[id_set][:n])      # pick names from the set
    arg_type = "list" if operation in ("list_sum", "list_len", "first_element") else "int"
    args = [{"name": names[i], "type": arg_type, "role": "operand"} for i in range(n)]
    return {"operation": operation, "args": args,
            "input_types": [arg_type] * n, "output_type": arg_type}
```

## 2. The reference program

The reference generator reads the semantics and emits the correct Python. A few cases:

```python
def generate_reference(sem):
    op = sem["operation"]; names = [a["name"] for a in sem["args"]]
    if op == "add":
        return f"def solve({', '.join(names)}):\n    return {names[0]} + {names[1]}"
    if op == "list_sum":
        return (f"def solve({names[0]}):\n    total = 0\n"
                f"    for x in {names[0]}:\n        total = total + x\n"
                f"    return total")
    # ... and so on for every operation, in the same style.
```

## 3. The natural-language renderer

The renderer phrases the same semantics several ways. Each **template family** is a
function:

```python
def _a(op, names, rng):   # family "a"
    x, y = names[0], names[1]
    return (f"Write a function that takes two numbers, {x} and {y}, "
            f"and returns the sum of them.")

def _b(op, names, rng):   # family "b"
    x, y = names[0], names[1]
    return (f"Implement solve so that given {x} and {y} it returns their sum.")

def _c(op, names, rng):   # family "c"
    x, y = names
    return f"Define a function solve({x}, {y}) that returns {x} + {y}."

FAMILIES = {"add": [_a, _b, _c], "mul": [_a, _b, _c], ...}
```

The semantics is fixed; only the wording changes. That is the entire point.

## 4. The hidden tests

Tests are generated from the semantics, with deliberate edge-case coverage. The
expected value is computed by the operation itself — not copied from the reference:

```python
def generate_hidden_tests(sem, rng=None, count=8):
    op = sem["operation"]; args = sem["args"]; tests = []
    def add(*vals, note="basic"):
        tests.append({"args": list(vals), "expected": _expected(op, vals), "note": note})
    add(_rand(rng), _rand(rng), note="basic")     # ordinary
    add(0, _rand(rng), note="zero")               # zero
    add(-_rand(rng), -_rand(rng), note="negative")# negative
    add(_rand(rng, 900, 1000), _rand(rng), note="large")  # large
    # ... edge cases for the specific operation
    return tests[:count]
```

## 5. The leakage audit

Finally, the generator is checked. The audit trains a trivial classifier to see
whether the wording leaks the operation:

```python
vec = TfidfVectorizer()
X = vec.fit_transform([t["nl"]["prompt"] for t in tasks])
clf = LogisticRegression(max_iter=1000)
scores = cross_val_score(clf, X, y, cv=5)
print(f"classifier predicts operation: {scores.mean():.3f}")   # >0.9 means LEAK
```

When we ran this on the first pilot renderer, it printed **1.000** — a 100% leak —
and that finding drove the later expansion of the paraphrase families.

## How to run it

```bash
python scripts/generate_data.py --n-per-op 200   # writes pilot_train/val/test + manifest
python scripts/audit.py                          # runs the leakage audit
```

That's the teacher. It's not magic — it's a controlled generator, audited for
fairness, that makes the entire experimental program possible.
