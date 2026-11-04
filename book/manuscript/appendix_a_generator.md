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
FAMILIES = {
    # three families each:
    "add": [_a, _b, _c], "sub": [_a, _b, _c], "mul": [_a, _b, _c],
    # two families each:
    "max_of": [_a, _b], "min_of": [_a, _b],
    "list_sum": [_list_a, _list_b], "list_len": [_list_a, _list_b],
    "first_element": [_list_a, _list_b],
    # singletons — exactly one family each:
    "abs_of": [_unary_a], "cond_abs_max": [_a],
    # composites: one family each, and held out of training entirely
    # (composition split only):
    "abs_add": [_comp_add_abs], "sub_abs": [_comp_sub_abs],
    "sum_of_abs": [_comp_sum_abs], "max_add": [_comp_max_add],
    "double_first": [_comp_double_first], "len_minus_one": [_comp_len_minus_one],
}
```

The semantics is fixed; only the wording changes. That is the entire point.

Cardinality is visible in that dict, and it is deliberately uneven: three families for
`add`/`sub`/`mul`, two for the other primitives, and exactly one for the singletons
`abs_of` and `cond_abs_max` (and for every composite). A singleton has no held-out
family to offer — which is why Chapter 15's held-out-wording cells cover 8 operations
and 480 records rather than 10 and 600 (Chapter 5 introduces this cardinality with the
teacher; Appendix D defines "held-out family").

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

## 6. From prompt to tokens: the actual tokenizer

The generator stops at text. The training pipeline turns that text into ids with the
tokenizer in `src/tokenizer/tokenizer.py` — and it is worth showing here, because it is
**not** BPE (Chapter 8 and Appendix D carry the correction): the vocabulary is the 256
character tokens plus the most frequent whole words of the corpus, and encoding is a
greedy longest match.

```
def train_tokenizer(texts, min_vocab=128, max_vocab=512, save_path=None):
    # character alphabet first, so nothing is ever out-of-vocabulary
    vocab = {chr(c) for c in range(256)}
    words = Counter()
    for t in texts:
        for w in t.split():
            words[w] += 1
    for w, _ in words.most_common(max_vocab - len(vocab)):
        vocab.add(w)
    vocab = sorted(vocab)[:max_vocab]
    return Tokenizer(vocab)

class Tokenizer:
    def encode(self, text):
        # greedy longest match over the vocabulary (deterministic), window <= 24
        ...
```

Worked example, from an actual run of that code on three rendered addition prompts
(`max_vocab=300`): the vocabulary came out **283 tokens — all 256 characters plus the
frequent whole words** — and encoding

```
"Write a function that takes two numbers, a and b and returns the sum of them."
```

produced **31 tokens**:

```
['Write', ' ', 'a', ' ', 'function', ' ', 'that', ' ', 'takes', ' ', 'two',
 ' ', 'numbers,', ' ', 'a', ' ', 'and', ' ', 'b', ' ', 'and', ' ', 'returns',
 ' ', 'the', ' ', 'sum', ' ', 'of', ' ', 'them.']
```

Whole words are taken whole when they are in the vocabulary (`function`, `numbers,`),
single characters otherwise; `decode(encode(x)) == x` exactly. Two consequences the
book relies on: the tokenizer is deterministic (same corpus, same vocabulary), and its
vocabulary is trained on the *training* text only in the corrected experiments
(Chapter 15 states this for its fixed tokenizer), so evaluation never leaks vocabulary
from held-out prompts.

## 7. Split construction: the invariants

Splits are assigned *after* generation, by `scripts/generate_data.py`, and the
following invariants are what make a split claim checkable rather than a promise:

1. **One record, one split.** Every record carries its own `split` field, and each
   record lands in exactly one of `train` / `val` / `test` — splits are disjoint by
   `task_id`.
2. **Per-operation 70/15/15, by sorted `task_id`.** Within each operation the records
   are sorted by `task_id`; the first 15% go to `val`, the next 15% to `test`, the rest
   to `train` (with at least one record per non-empty split). So every operation appears
   in every split with the same distribution — the pilot's splits are *not*
   operation-disjoint.
3. **Operation holdout is a different mechanism.** The composites come from
   `generate_compositional`, a separate path, and never enter the pilot's train split;
   that — not the 70/15/15 cut — is what makes the composition split a holdout.
4. **The manifest records the split's own provenance:** `dataset_version`, `seed`,
   `n_per_op`, the per-split counts, and the operation list, so the split can be
   re-derived instead of merely trusted.
5. **Regeneration is deterministic.** `make_task` seeds its RNG from the record's
   seed, so the same seed rebuilds the same record — a split can be reproduced, not
   just read.
6. **Hidden tests never enter training.** They are evaluator-only artifacts
   (Appendix D, "Hidden tests"), so no split's training data contains a test's expected
   values.
7. **Records are disjoint; prompt strings need not be.** The pilot reuses the same 21
   prompt strings across train/val/test, so "held out" there means held-out *records*
   (and fresh hidden-test values), not held-out prompts — the surface and composition
   splits hold out prompt wording and operation families instead (Appendix D,
   "Train/val/test split"). A split claim therefore has to name its novelty axis, and
   these invariants are what the novelty audit checks.

## How to run it

```
python scripts/generate_data.py --n-per-op 200
# writes pilot_train/val/test + manifest
python scripts/audit.py
# runs the leakage audit
```

That's the teacher. It's not magic — it's a controlled generator, audited for
fairness, that makes the entire experimental program possible.
