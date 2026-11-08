# Let us brew an AI Model

**What tiny language models can actually learn when given one job.**

This is not primarily a transformer tutorial. It is a controlled empirical
investigation into what a small language model can learn when given exactly one
narrowly defined, objectively testable task:

> **natural-language specification → Python program**

The generated program is executed against hidden tests. This gives us deterministic
inputs, executable outputs, objective evaluation, synthetic data generation,
controlled difficulty, hidden tests, compositional splits, memorization tests,
shortcut audits, and archived experiment manifests.

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

Bootstrap the Python 3.11 environment first. `.venv-311` is gitignored, so a clean
clone does not ship it and `source .venv-311/bin/activate` fails until this one
command has run:

```bash
python3.11 -m venv .venv-311 && .venv-311/bin/pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements-lock.txt && .venv-311/bin/pip install -e . && .venv-311/bin/pip install pytest
```

(`pytest` is not in `requirements-lock.txt`; without this last step `make test`
exits with `No module named pytest` — `make setup` installs it too.)

```bash
make setup        # create the Python environment (.venv-311 if absent, then install into it)
make smoke        # run the end-to-end Stage 0 pipeline smoke test
make test         # run the evaluator + sandbox conformance/mutation suites
make audit        # run the dataset leakage audit
make stage1       # train + evaluate the Stage 1 pilot
make reproduce    # print the plan to regenerate a recorded manifest (--run executes)
```

### Release gate

**Generate the artifacts first:** `artifacts/tokenizer/` (and `artifacts/datasets/`)
are gitignored by design, so a virgin clone has none of the seven pinned tokenizer
files the gate preflights — run the quickstart generation step
(`python scripts/generate_data.py --n-per-op 200 --seed 0` plus the run scripts,
e.g. `python scripts/run_composition.py`, `python scripts/train.py --stage 1`)
before the gate, or its PREFLIGHT fails with
`NOT A VERIFIABLE CLEAN CLONE … run the quickstart generation step` and no other
pointer.

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
clone must be at the PDF build commit (recorded in `docs/release_manifest.json`
as `pdf_build_commit`, the single place that value lives) **or later** to find
`scripts/verify_release.py` and the corrected run scripts. HEAD already is, so
verification runs at HEAD.

The recorded pdf_build_commit is the commit the PDF was built from; check it out only to inspect that exact source state — the verification commands below run at HEAD:

```bash
git checkout HEAD   # the gate and pins live at HEAD; the build commit is recorded for provenance, and the gate asserts the PDF content matches it
source .venv-311/bin/activate
TORCH_DISABLE_AVX2=1 OMP_NUM_THREADS=2 python scripts/verify_release.py
```

(Reading `pdf_build_commit` out of the manifest *at* the build commit is deliberately
not part of the recipe: that commit's own manifest records an older value, so such a
command walks backward through history with no fixed point.)

Both roles are recorded in `docs/release_manifest.json` (`tag_target_commit`,
`pdf_build_commit`, `reproduction_from_a_clean_clone`).

Without `pymupdf` the gate does not crash: the PDF phase prints a warning and is
skipped, so a green run over a python that lacks it has **not** checked the PDF —
confirm the report lists the phase C checks before trusting it.

## Status

The project follows a strict experimental protocol: **change one variable**, never
fabricate results, preserve failures, test the tester, and compare against simple
baselines. Evidence levels are `[MEASURED]` / `[DESIGN]` / `[HYPOTHESIS]` /
`[INTERPRETATION]` / `[UNKNOWN]` / `[SUPERSEDED]`. `[SUPERSEDED]` is applied in the
book (e.g. the capability map and the glossary) to mark a value a corrected rerun
replaced. `[DERIVED]` was declared here but never applied anywhere in the book, so it
is **dropped** from the taxonomy rather than left as an unused level.