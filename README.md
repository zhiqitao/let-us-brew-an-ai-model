# Let us brew an AI Model

**What tiny language models can actually learn when given one job.**

This is not primarily a transformer tutorial. It is a controlled empirical
investigation into what a small language model can learn when given exactly one
narrowly defined, objectively testable task:

> **natural-language specification → Python program**

The generated program is executed against hidden tests. This gives us deterministic
inputs, executable outputs, objective evaluation, synthetic data generation,
controlled difficulty, hidden tests, compositional splits, memorization tests,
shortcut audits, and reproducible experiments.

**The model is the instrument. The experiment is the subject.**

## The laboratory

Four artifacts constitute the experimental apparatus:

- **THE WORLD** — a controlled Python Capability Specification
- **THE TEACHER** — a semantic dataset generator
- **THE JUDGE** — an execution-based evaluator
- **THE STUDENT** — a small language model

Build the laboratory first; the laboratory produces the experiments; the
experiments determine what the book claims.

## Getting started

See `design/BOOK_DESIGN.md` (the authoritative, frozen design) and
`specs/python_capability_v0_1.md` (the controlled Python environment).

```bash
make setup        # create the Python environment
make smoke        # run the end-to-end Stage 0 pipeline smoke test
make test         # run the evaluator + sandbox conformance/mutation suites
make audit        # run the dataset leakage audit
make stage1       # train + evaluate the Stage 1 pilot
make reproduce    # regenerate a recorded experiment manifest
```

## Status

The project follows a strict experimental protocol: **change one variable**, never
fabricate results, preserve failures, test the tester, and compare against simple
baselines. Evidence levels are `[MEASURED]` / `[DERIVED]` / `[DESIGN]` / `[HYPOTHESIS]` /
`[INTERPRETATION]` / `[UNKNOWN]`.
