# Experiment — Judge mutation test (measured mutation report)

Status: `[MEASURED]` — real run, manifest at `artifacts/manifests/judge_mutation.json`.
Script: `scripts/run_mutation_report.py`.

## The question
The book describes mutation testing the judge, but never publishes the actual numbers.
This run fills that gap: how many mutant (deliberately-broken) reference programs does
the hidden-test suite *kill*, how many *survive*, and does it *accept* the correct
reference (a positive control, without which a reject-everything evaluator would also
score "perfect")?

## Setup
For each of the 16 operations (10 primitives + 6 composites), generate a reference
program and its mutants via the operator/comparison/logic flips in
`src/evaluator/mutations.py`. Run each mutant through the judge against that
operation's hidden tests. A mutant is **killed** if the judge rejects it (pass@1 =
False), **survived** if it passes, **invalid** if it cannot be parsed/evaluated.
Positive control: the true reference must be **accepted** for every operation.

## Result

| Aggregate | value |
|---|---|
| Operations tested | 16 |
| Mutants generated | 35 |
| Killed | 29 |
| Survived | 6 |
| Invalid | 0 |
| **Kill rate** | **0.829** |
| All reference positive-controls accepted | **yes** |

Per-operation: `add/sub/mul/list_sum/list_len/first_element/abs_add/sub_abs/
double_first/len_minus_one` all killed 100% of their mutants. The weaker spots were
`max_of` (0.5), `min_of` (0.5), `cond_abs_max` (0.5), `abs_of` (0.667),
`sum_of_abs` (0.75), `max_add` (0.75).

## Interpretation — the honest read

This is a *real* but **partial** result, and we report it as such:

1. **The judge is not a reject-everything evaluator.** Every reference program (the
   positive control) was accepted across all 16 operations. So a passing suite is not
   just "reject everything" — it genuinely distinguishes the correct reference from
   most mutants.
2. **But the judge is not complete either.** 6 of 35 mutants survived. These are
   cases where the hidden tests did not catch a specific break. The weakest operations
   (max_of, min_of, cond_abs_max, and some list/composite ops) have blind spots. The
   tests were *not* "edge-case-complete", and we should say so.
3. **Semantic caveat.** Some surviving mutants may be *equivalent* (e.g. swapping the
   two operands of `+` gives an equal program for integer addition), which should
   arguably not count against the suite. We did not build an equivalence check, so we
   report "survived" plainly rather than guess which are truly equivalent.

## What this means for the book's claims

The conclusion "the judge has been validated" is too strong on its own. The accurate
statement is: the judge accepts correct references and rejects most (82.9%) of the
deliberate error classes we generated, but it has blind spots, and we have not
exhaustively enumerated its promise. A reject-everything bug was ruled out by the
positive control; a fully-discriminating test suite was *not* demonstrated, because 6
mutants survived. We therefore describe the judge as a well-tested **heuristic**
verifier, not a proven-sound one.

## Reproduce
```bash
TORCH_DISABLE_AVX2=1 python scripts/run_mutation_report.py
```
