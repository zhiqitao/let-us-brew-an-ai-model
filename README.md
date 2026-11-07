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

### Release gate

`scripts/verify_release.py` is the closed-loop release gate (manifest, source,
built-PDF, and release-record invariants). **Run it under the repository's
Python 3.11 venv** — its PDF phase extracts the built book with `pymupdf`, which
the bare system `python3` does not provide (`pymupdf==2.1` is pinned in
`requirements-lock.txt` and installed in `.venv-311`):

```bash
source .venv-311/bin/activate
TORCH_DISABLE_AVX2=1 OMP_NUM_THREADS=2 python scripts/verify_release.py
# rebuild the PDF first if needed:  python book/build_book.py
```

**Which commit to check out:** the release tag `v20261001` (commit `a45a881`) is the
experiment-data snapshot the book's numbers cite, but it predates this gate — a clean
clone must check out the PDF build commit (`af32fb8b`) or later to find
`scripts/verify_release.py` and the corrected run scripts:

```bash
git checkout af32fb8b
source .venv-311/bin/activate
TORCH_DISABLE_AVX2=1 OMP_NUM_THREADS=2 python scripts/verify_release.py
```

Both roles are recorded in `docs/release_manifest.json` (`tag_target_commit`,
`pdf_build_commit`, `reproduction_from_a_clean_clone`).

Without `pymupdf` the gate does not crash: the PDF phase prints a warning and is
skipped, so a green run over a python that lacks it has **not** checked the PDF —
confirm the report lists the phase C checks before trusting it.

## Status

The project follows a strict experimental protocol: **change one variable**, never
fabricate results, preserve failures, test the tester, and compare against simple
baselines. Evidence levels are `[MEASURED]` / `[DERIVED]` / `[DESIGN]` / `[HYPOTHESIS]` /
`[INTERPRETATION]` / `[UNKNOWN]`.
