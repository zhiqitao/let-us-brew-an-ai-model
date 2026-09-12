# Appendix C — The Experiment Registry

Every result in this book is traceable to a run, a configuration, and an artifact.
This registry is the single place to look up each one: what was tested, how it was
run, where the numbers live, and what is *not* tested. Where a cell could not be
measured we say "not tested" rather than "0" — an unmeasured quantity is not a zero.

## How the registry is organized

Each row names the experiment, the model size, the key configuration (steps, seed,
architecture), the artifact (manifest / checkpoint) that holds the record, and the
result. "Denominator" is the number of evaluation prompts used for the pass@1 score.

## Registry

| Experiment | Model | Config (steps / d / L / H / seed) | Manifest | Checkpoint | Key result |
|---|---|---|---|---|---|
| Stage 1 — pilot | 884,224 | 1500 / 128 / 8 / 4 / 0 | stage1.json | stage1.pt | in-dist 0.897; loss 5.84→0.019 |
| Stage 3 — surface | 884,224 | 1500 / 128 / 8 / 4 / 0 | stage3_surface.json | stage3_surface.pt | 0.900 in-dist; 0.350 new-IDs; 0.000 new-wording |
| Stage 4 — composition | 29,290,240 | 800 / 448 / 12 / 8 / 0 | stage4_composition.json | stage4_composition.pt | in-dist 0.897; composition 0.000 |
| Stage 4 — 6.5M | 6,551,040 | 1000 / 256 / 8 / 8 / 0 | stage4_composition_6p5m.json | stage4_6p5m.pt | in-dist ~0.9; composition 0.000 |
| Stage 4 — 10.2M | 10,195,776 | 800 / 288 / 10 / 8 / 0 | stage4_composition_10m.json | stage4_10m.pt | in-dist 0.773; composition 0.000 |
| Stage 4 — scaling sweep | — | re-eval of size ckpts | stage4_scaling.json | (size ckpts) | composition 0.000 at all sizes |
| Data scaling | 884,224 | 800 / 128 / 4 / 4 / 0 | data_scaling.json | — | in-dist 0.100→0.641 (100→3000) |
| Quantity vs diversity | 884,224 | 900 / 128 / 4 / 4 / 0 | diversity.json | — | minimal 0.500/0.000; high 1.000/1.000 |
| Memorization | 884,224 | — | memorization.json | — | 59/60 held-out; canary → general program |
| Continual learning | 884,224 | 700+700 / 128 / 4 / 4 / 0 | continual.json | — | sequential A 0.000; joint A 1.000, B 0.889 |
| Composition exposure | 884,224 | 1500 / 128 / 4 / 4 / 0 | composition_exposure_pilot.json | stage4_exposure.pt | exposed 0.667; held-out 0.000 |
| Composition diversity | 884,224 | 1500 / 128 / 4 / 4 / 0 | composition_diversity_pilot.json | stage4_compdiv_{minimal,high}_diversity_pilot.pt | exposed ~0.55-0.59; held-out 0.000 |

## Denominator and uniqueness notes

- **Surface / composition / exposure / diversity** pass@1 scores are computed over
  held-out *instances* of each operation, not the training set. The pilot used ~300
  held-out prompts; later runs used comparable held-out instance counts per operation.
- **Unique model-visible prompts** = distinct rendered prompts, not distinct task IDs.
  In the teacher, task-ID seeds change the *hidden test* values, so a new ID can
  change the tests while the prompt and reference program stay identical (see the
  caveat under "what is not tested" below).
- **Tokenizer** is trained on the combined train prompts + reference programs (min
  vocab ~128, max ~300); the same tokenizer is reused for the model in a given run.
- **Training loops** stop at a fixed step count (no early stopping from validation
  loss); the final loss is the training loss, not a held-out measure.

## What is NOT tested (explicitly)

- **Multiple seeds per size.** Each size was trained once, with one seed. We therefore
  cannot attach error bars to the 0.773–0.900 in-distribution spread in Chapter 12.
  Treat that spread as approximate, not an exact plateau.
- **Genuinely-held-out wording families.** In the surface/diversity runs, the test
  wording family and identifiers were drawn from the same family set used (at least in
  part) for training. So "surface generalizes" is strongest as a *coverage* statement;
  generalization to a *never-seen* family is untested (see Chapter 13 caveat).
- **Conditionals, indexing, loops** in the capability ladder (Chapter 19) were not
  isolated as separate operations in the primitive set we tested; they appear in
  composites but were not measured standalone.
- **Composition beyond ~30M** (and the true "structural vs above-our-ceiling" question)
  is not tested — the CPU lab becomes impractical beyond that.
- **A true replay-after-A-first** continual-learning design (vs the joint-training
  control we ran) is not tested; see the Chapter 20 caveat.
- **Mutation-testing acceptance** and a *surviving* mutant report showing the judge
  caught an error — this is a gap the book should close to fully demonstrate the
  judge's test coverage (see Chapter 17).

## How to reproduce

Each experiment's run script lives in `scripts/` (e.g. `run_continue.py`, `run_diversity.py`,
`run_composition_exposure.py`, `run_composition_diversity.py`, `run_data_scaling.py`).
To rerun, set `TORCH_DISABLE_AVX2=1` (this CPU lab needs it to avoid SIGILL) and invoke
the script with the config shown in the registry.
