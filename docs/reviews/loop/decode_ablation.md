# Decode / Termination Ablation — is composition 0.000 an artifact?

**Question (external review):** the book's central result is composition
**0.000** on held-out composites. Is that a generation/decoding/extraction
artifact (the model emits *something*, but NUL-padding or a short `max_new`
truncates it into invalid Python), or a genuine failure of the model?

- Checkpoint: `artifacts/checkpoints/stage4_exposure.pt` (884,224 params, loaded, NOT retrained)
- Tokenizer: reconstructed_matched (run_composition_exposure corpus), 291 tokens — the EXACT vocab the checkpoint was trained with
- **Tokenizer provenance warning:** the on-disk `artifacts/tokenizer/comp_tok.json` (gitignored) was overwritten by a later experiment and differs from the training vocab at **75/291** indices. Evaluating with that file collapses BOTH held-out and exposed sets to 0.000 under every setting — see the appendix (`artifacts/manifests/decode_ablation_disk_tok.json`). That is a tokenizer-clobber artifact, a different failure class from the decode question asked here.
- Split: identical to `scripts/run_composition_exposure.py`, seed 0 — 120 held-out composites (max_add, double_first, len_minus_one), 120 exposed composites (abs_add, sub_abs, sum_of_abs) as control, 1400 primitive+exposed train tasks (unused here).
- Extraction for every setting: decode -> NUL-truncate -> `.strip()`, exactly
  as `src/eval/evaluator_runner.generate_code` does. An alternative
  extraction (delete every NUL, keep all other content) is also scored —
  see "Extraction variants".

## Settings

| setting | T | max_new | source run | note |
|---|---|---|---|---|
| greedy_max64 | 0.0 | 64 | greedy_max256 | prefix of one run (token stream held fixed) |
| greedy_max128 | 0.0 | 128 | greedy_max256 | prefix of one run (token stream held fixed) |
| greedy_max256 | 0.0 | 256 | greedy_max256 | prefix of one run (token stream held fixed) |
| sample08_max64 | 0.8 | 64 | sample08_max256 | prefix of one run (token stream held fixed) |
| sample08_max128 | 0.8 | 128 | sample08_max256 | prefix of one run (token stream held fixed) |
| sample08_max256 | 0.8 | 256 | sample08_max256 | prefix of one run (token stream held fixed) |
| book_sample08_max80 | 0.8 | 80 | book_sample08_max80 | the book's eval procedure |

## HELD-OUT composites (never seen in training) — the key table

| setting | syntax | **valid prog** | executable | **pass@1** | (a) parse | (b) allowlist | (c) 0 tests | (d) partial | (e) all |
|---|---|---|---|---|---|---|---|---|---|
| greedy_max64 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| greedy_max128 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| greedy_max256 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| sample08_max64 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| sample08_max128 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| sample08_max256 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |
| book_sample08_max80 | 0.000 | **0.000** | 0.000 | **0.000** | 120 | 0 | 0 | 0 | 0 |

## EXPOSED composites (seen in training) — control

| setting | syntax | **valid prog** | executable | **pass@1** | (a) parse | (b) allowlist | (c) 0 tests | (d) partial | (e) all |
|---|---|---|---|---|---|---|---|---|---|
| greedy_max64 | 1.000 | **1.000** | 0.667 | **0.667** | 0 | 0 | 40 | 0 | 80 |
| greedy_max128 | 0.667 | **0.667** | 0.667 | **0.667** | 40 | 0 | 0 | 0 | 80 |
| greedy_max256 | 0.667 | **0.667** | 0.667 | **0.667** | 40 | 0 | 0 | 0 | 80 |
| sample08_max64 | 0.992 | **0.992** | 0.667 | **0.667** | 1 | 0 | 39 | 0 | 80 |
| sample08_max128 | 0.800 | **0.800** | 0.667 | **0.667** | 24 | 0 | 16 | 0 | 80 |
| sample08_max256 | 0.800 | **0.800** | 0.667 | **0.667** | 24 | 0 | 16 | 0 | 80 |
| book_sample08_max80 | 0.808 | **0.767** | 0.667 | **0.667** | 23 | 5 | 12 | 0 | 80 |

## Extraction variants (is NUL-truncation hiding recoverable code?)

| setting | set | NUL-trunc valid | NUL-filter valid | NUL-trunc pass@1 | NUL-filter pass@1 | gens with content after 1st NUL |
|---|---|---|---|---|---|---|
| greedy_max64 | heldout | 0.000 | 0.000 | 0.000 | 0.000 | 0/120 |
| greedy_max64 | exposed | 1.000 | 1.000 | 0.667 | 0.667 | 0/80 |
| greedy_max128 | heldout | 0.000 | 0.000 | 0.000 | 0.000 | 0/120 |
| greedy_max128 | exposed | 0.667 | 0.667 | 0.667 | 0.667 | 0/120 |
| greedy_max256 | heldout | 0.000 | 0.000 | 0.000 | 0.000 | 0/120 |
| greedy_max256 | exposed | 0.667 | 0.667 | 0.667 | 0.667 | 0/120 |
| sample08_max64 | heldout | 0.000 | 0.000 | 0.000 | 0.000 | 0/120 |
| sample08_max64 | exposed | 0.992 | 0.992 | 0.667 | 0.667 | 0/81 |
| sample08_max128 | heldout | 0.000 | 0.000 | 0.000 | 0.000 | 0/120 |
| sample08_max128 | exposed | 0.800 | 0.800 | 0.667 | 0.667 | 0/120 |
| sample08_max256 | heldout | 0.000 | 0.000 | 0.000 | 0.000 | 0/120 |
| sample08_max256 | exposed | 0.800 | 0.800 | 0.667 | 0.667 | 0/120 |
| book_sample08_max80 | heldout | 0.000 | 0.000 | 0.000 | 0.000 | 0/120 |
| book_sample08_max80 | exposed | 0.767 | 0.767 | 0.667 | 0.667 | 0/92 |

## Interpretation

**The 0.000 is NOT an extraction artifact.** Even with the most favorable decode we tried (greedy argmax, max_new=256, NUL-truncation) only 0.000 of held-out generations are valid programs (book setting: 0.000); sampled T=0.8 at max_new=256 gives 0.000. Longer generation and greedy decoding do not rescue the format, so the failure is upstream of extraction — the model does not emit well-formed programs at all for held-out composite prompts.

**pass@1 stays 0.000 under every setting** on held-out composites (greedy@64/128/256: 0.000/0.000/0.000; sampled@64/128/256: 0.000/0.000/0.000; book: 0.000). Combined with the 0.000 valid-program rate, the held-out failure happens BEFORE semantics can be exercised — no decode produces a program that even parses. Semantic failure is separately visible on the exposed control: pass@1 caps at 0.667 under every setting because the sum_of_abs op fails all 40 instances (at greedy@64 those are well-formed programs with wrong output), so both a generation failure (held-out) and a residual semantic failure (exposed) exist, and neither is fixable by decoding.

**Control (exposed composites — training instances, an upper bound):** under the book's own decode the exposed set scores valid-program rate 0.767 and pass@1 0.667 (greedy@256: 0.667/0.667), while held-out under the SAME decode is 0.000/0.000. The pipeline produces valid, passing programs when the composite was seen — so the pipeline is sound and the held-out failure is specific to the unseen composition, not to decoding in general.

**Failure mode (raw generations):** on the 120 held-out prompts greedy decoding produces only 3 distinct extracted programs — constant per operation, not per instance — and only 0/120 even begin with `def solve`; 120/120 collapse into NUL padding (median first-NUL token 8), and NUL is an absorbing token, so longer `max_new` just appends more NULs. Under the identical decode, 120/120 exposed prompts start with `def solve` (3 distinct programs, one per operation). The held-out failure happens at the FIRST generated tokens — before any truncation could matter.

**Verdict: the 0.000 is NOT a decode/termination/extraction artifact.** Best held-out valid-program rate across all seven settings is 0.000 (greedy_max64) and pass@1 is 0.000 everywhere (best greedy_max64 = 0.000). Greedy argmax, 3.2x longer generation (256 vs 80), and an extraction that keeps all post-NUL content change nothing, while the same pipeline scores 0.667-0.767 valid and 0.667-0.667 pass@1 on the exposed control. The failure is real: on unseen compositions the model does not emit a well-formed program at all under any decode — the breakdown is at the FIRST generated tokens, not at truncation — and on the exposed control, where programs are well-formed, pass@1 still caps at 0.667 (sum_of_abs fails 40/40 even on its own training instances). Neither the format collapse nor the residual gap is fixable by decoding. NUL-truncation discards no recoverable content: none of the 1573 NUL-containing generations had any non-NUL content after its first NUL, and the delete-all-NULs extraction yields identical numbers.

## Example generations (first held-out task)

**book_sample08_max80** — extracted program (parse_fail, 0/7 tests):

```python
def + b
```

**greedy_max256** — extracted program (parse_fail, 0/7 tests):

```python
def + b
```

## Appendix: same ablation with the clobbered on-disk tokenizer

The identical ablation scored with the tokenizer file currently on disk (`artifacts/tokenizer/comp_tok.json`, overwritten by `run_composition_diversity.py` AFTER this checkpoint was trained; 75 of 291 vocab indices differ). Every setting scores 0.000 valid-program rate on BOTH held-out and exposed sets: a tokenizer-clobber artifact that mimics — and would mask — a composition failure. Raw runs: `artifacts/raw_outputs/decode_ablation/raw_runs/disk_tok/`.

| setting | held-out valid | held-out pass@1 | exposed valid | exposed pass@1 |
|---|---|---|---|---|
| greedy_max64 | 0.000 | 0.000 | 0.000 | 0.000 |
| greedy_max128 | 0.000 | 0.000 | 0.000 | 0.000 |
| greedy_max256 | 0.000 | 0.000 | 0.000 | 0.000 |
| sample08_max64 | 0.000 | 0.000 | 0.000 | 0.000 |
| sample08_max128 | 0.000 | 0.000 | 0.000 | 0.000 |
| sample08_max256 | 0.000 | 0.000 | 0.000 | 0.000 |
| book_sample08_max80 | 0.000 | 0.000 | 0.000 | 0.000 |

---
Raw programs archived under `artifacts/raw_outputs/decode_ablation/`; machine-readable results in `artifacts/manifests/decode_ablation.json`.
