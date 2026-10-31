# Evaluation Protocol v0.1

Status: `[DESIGN]`. Defines how the JUDGE scores a generated Python program against
hidden tests, and the metric hierarchy used throughout the book.

## 1. Evaluation hierarchy

A candidate program is scored in stages; a later stage is only meaningful if the
earlier ones pass:

1. **Syntax Pass** — the program parses as valid Python.
2. **AST / Capability Pass** — the program's AST is entirely within the whitelisted
   capability subset (see `python_capability_v0_1.md`).
3. **Execution Pass** — the program compiles and executes without error under
   restricted globals. *Recorded quantity:* the implementation records this stage as
   **executable** when the program passes at least one hidden test (or has no hidden
   tests) — `execution_ok = tests_passed > 0 or len(hidden_tests) == 0` in
   `src/evaluator/evaluator.py` — i.e. "produced at least one correct output," not
   merely "ran without error" (matching Chapter 6 and the metric below).
4. **Semantic Pass** — for each hidden test, the program's output equals the expected
   output under the semantic comparator.

## 2. Metrics

- **syntax success rate** — fraction of candidates that parse.
- **executable success rate** — fraction of candidates recorded as executable: those
  that pass **at least one hidden test** (or have no hidden tests), matching
  `execution_ok` in `src/evaluator/evaluator.py` and the book's Chapter 6 definition —
  not merely the fraction that run without error.
- **hidden-test pass rate** — fraction of individual hidden tests passed.
- **problem-level success rate (pass@1)** — fraction of problems where the single
  generated program passes **all** hidden tests under temperature-0.8 single-sample
  sampled decoding (one sample per record; `generate(temperature=0.8)` →
  `torch.multinomial` in `src/model/gpt.py`).
- **test-level success rate** — fraction of hidden tests passed overall.
- **generalization gap** — test performance minus in-distribution performance.
- **shortcut-adjusted performance** — performance after ruling out (or reporting) a
  suspected shortcut (e.g. memorization, template dependence).

**Primary metric:** `problem-level hidden-test pass@1 under temperature-0.8
single-sample sampled decoding`.

`pass@k` may be investigated later but should not become the main result: it changes
the question from "what can the model produce?" to "can sampling find a correct
answer?"

## 3. Semantic comparison

Do **not** assume string equality means correctness. The comparator must handle:

- integers, floats, booleans, strings
- lists, nested lists
- dicts, nested structures

Rules:
- floats: `abs(a-b) <= float_tolerance` (default `1e-9`)
- dicts: key-set and values compared, order-insensitive
- nested structures: recursive comparison

The comparator itself must be tested (see `tests/evaluator/test_comparator.py`).

## 4. Mutation testing (red-teaming the judge)

Start from correct reference solutions and generate mutant programs, e.g.:

- `+` → `-`; `*` → `/`; `>` → `>=`; `=` → `>`
- remove `return`
- wrong variable; swapped arguments
- off-by-one loop boundary; incorrect constant; incorrect comparison
- missing edge-case handling

Run mutants through hidden tests. **Mutation score** should approach high coverage.
If an obviously-wrong mutant passes, the test suite is weak — add tests until
important mutant classes are reliably detected.

## 5. Metric recording

Every evaluation run records, in a machine-readable experiment manifest (see
`docs/experiments/`): dataset version, evaluator version, spec version, model
config, seed, per-metric values, artifact paths, and status
(`[PLANNED] [RUNNING] [MEASURED] [FAILED] [REJECTED] [SUPERSEDED]`).
