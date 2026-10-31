# BOOK DESIGN — LET US BREW AN AI MODEL

Status: **AUTHORITATIVE / LOCKED (v1.0)**
This document freezes the design for the new book. It **supersedes and retires** the
older draft's general-purpose "rainbow / alignment / knowledge / tool-use" framing.
The book is not a transformer tutorial; it is a controlled empirical investigation
into what a small language model can actually learn when given **one job**.

---

## 1. Project definition

**Title:** Let us brew an AI Model
**Subtitle:** What tiny language models can actually learn when given one job
**Core thesis:** Building a small language model is relatively easy. Determining what
it actually learned is the hard part. The model is the instrument. The experiment is
the subject.

**The one task:** `NATURAL-LANGUAGE SPECIFICATION → PYTHON PROGRAM`
A model receives a natural-language description of a programming task and generates
a Python solution, which is executed against hidden tests.

This task gives us **deterministic inputs, executable outputs, objective evaluation,
synthetic data generation, controlled difficulty, hidden tests, compositional
splits, memorization tests, shortcut audits, and reproducible experiments.**

**Explicitly out of scope:** general chatbot, general agent, frontier LLM, production
coding assistant, complete Python implementation, comprehensive interpretability,
comprehensive continual-learning survey.

## 2. The central question

> How much structured programming capability can a small language model actually
> learn, and how can we tell whether it learned it rather than memorized or
> exploited a shortcut?

Secondary questions (§2 of the spec): data required? capacity required? which
generalization appears first? where does memorization dominate? new constants /
identifiers / wording? compose familiar operations in unseen combinations? how does
capability change with Python complexity? what does continual learning do to prior
capabilities? cost of each capability? how much is explained by baselines? is the
evaluator trustworthy?

## 3. Operational meaning of "learned"

A model demonstrates learned capability when (1) performance improves systematically
during training, (2) transfers to held-out examples, (3) survives controlled changes
to superficial features, (4) survives appropriately designed structural changes, and
(5) simpler explanations (memorization, retrieval, templates, leakage, evaluator
artifacts) have been tested and rejected to the degree supported by the experiment.

Prefer *capability / competence / learned behavior / generalization / structural
generalization* over *intelligence / understanding / reasoning*.

## 4. Four-level generalization taxonomy (central framework)

1. **Memorization** — reproduces info closely represented in training.
2. **Distributional generalization** — succeeds on new examples from the same
   distribution.
3. **Surface generalization** — underlying problem unchanged, superficial features
   change (constants, identifiers, wording, distractors).
4. **Structural generalization** — combines known components in structures not
   present during training.

Never collapse these into one number.

## 5. Recurring shortcut audit

Every major experiment asks: "How could the model have done this without learning
what we think it learned?" Each audit records suspected shortcut, why it could
explain the result, control experiment, result, what the control rules out, what
remains unresolved.

## 6. The experimental apparatus (4 artifacts)

- **THE WORLD** — controlled Python Capability Specification
- **THE TEACHER** — semantic dataset generator
- **THE JUDGE** — execution-based evaluator
- **THE STUDENT** — small language model

Loop: define capability → generate semantic task → reference program → NL spec →
hidden tests → train → generate → run evaluator → measure → audit → interpret →
change one variable → repeat.

## 7. Experimental discipline

**Change one variable.** Never simultaneously change model size, dataset size,
tokenizer, context, architecture, LR, duration — unless explicitly studying a
multi-variable interaction. Record hypothesis, change, control, measurement, result,
interpretation, alternative explanation, shortcut audit, decision (via a compact Lab
Notebook panel).

## 8. Capability ladder (main narrative device)

Stage 0 pipeline validation → Stage 1 basic synthetic programming → Stage 2
parameter/surface generalization → Stage 3 linguistic generalization → Stage 4
structural/compositional → Stage 5 increased Python expressivity → Stage 6
length/complexity → Stage 7 continual learning / retention. The model may stop
climbing; the stopping point is itself a result.

## 9. Book structure — seven parts, 21 chapters + 4 appendices (as implemented)

- **Part I — The Question** (Ch1 "Let us brew", Ch2 "What does it mean to learn?",
  Ch3 "Give the model one job")
- **Part II — Build the Laboratory** (Ch4 build a world we can control, Ch5 build the
  teacher, Ch6 build the judge, Ch7 build the rivals)
- **Part III — The First Brew** (Ch8 the smallest brain, Ch9 the first brew, Ch10 does
  it actually work?)
- **Part IV — How Capability Scales** (Ch11 how much data, Ch12 how much brain, Ch13
  same data, more diverse data)
- **Part V — Catching the Model Cheating** (Ch14 memorization, Ch15 surface, Ch16
  composition, Ch17 red-team the judge)
- **Part VI — Break It** (Ch18 continual learning, Ch19 cost of capability)
- **Part VII — What Did We Learn?** (Ch20 the capability map, Ch21 the model wasn't the
  point: a conclusion)

Plus four appendices: A an annotated tour of the generator, B the failure ledger,
C the experiment registry, D glossary.

**Note on ability-ladder stages 5–6:** the originally planned Act "Give It More
Python" (increased Python expressivity / more Python, and length & complexity —
ladder stages 5 and 6) was folded into future work because no experiment measured
them; those stages are not part of the implemented book.

## 10. Core artifacts & repository layout

See `specs/` (capability spec, task schema, evaluation protocol), `src/` (model,
tokenizer, data_generator, nl_renderer, program_generator, test_generator, sandbox,
evaluator, baselines, audit, reporting), `tests/`, `configs/`, `experiments/`,
`artifacts/`, `scripts/`, `docs/`. Full tree is in §30 of the execution spec.

## 11. Evidence / status taxonomy

Evidence labels are used in exactly two places in the manuscript: the Appendix C
experiment registry and the Chapter 22 capability map. Every other quantitative claim
carries **no** per-claim in-text label; instead it is scoped in its introducing
sentence (the run, configuration, or split is named where the number appears). Never
invent numbers. Evidence levels: `[MEASURED]` `[DERIVED]` `[DESIGN]` `[HYPOTHESIS]`
`[INTERPRETATION]` `[UNKNOWN]`. Experiment status: `[PLANNED]` `[RUNNING]`
`[MEASURED]` `[FAILED]` `[REJECTED]` `[SUPERSEDED]`.

## 12. Anti-fabrication & failure policy

- Never fabricate results. Every number from an actual run.
- Preserve every failed experiment.
- A model failing to learn is NOT a project failure.
- Test the tester (evaluator must pass its own mutation/conformance suite).
- Test the teacher (leakage + diversity audit).
- Compare against simple baselines.
- Keep train/val/test semantically clean.
- Version everything.
- Do not optimize for a predetermined conclusion.
- Do not expand scope without explicit authorization.

## 13. Milestones

1. **"The lab works"** — an end-to-end trustworthy experimental loop.
2. **"The model learns something"** — loss drops, beats a meaningful baseline.
3. **"We found the generalization boundary"** — first capability matrix.
4. **"We know where the model cheats"** — a documented shortcut/failure mode.
5. **"We can draw the capability map"** — final capability boundary.

## 14. Authoritative project state

**Locked:** one primary task (NL→Python); controlled Python environment; synthetic
semantic dataset generation; objective executable evaluation; shortcut audit;
template + retrieval baselines; four-level generalization taxonomy; capability
ladder; narrow continual-learning experiment; explicit negative-result policy;
reproducibility requirements; one-variable discipline; ~10M–100M model scale;
23–24-chapter / eight-act book" is superseded by the implemented 7-part / 21-chapter
/ 4-appendix structure (see §9 above), with the later capability-ladder stages folded
into future work because no experiment measured them; laboratory built before
large-scale experimentation.

**Experimental (to be determined by runs):** exact model sizes, architecture,
tokenizer, Python capability boundaries, dataset sizes beyond pilot, training
duration, capability ceiling, generalization results, scaling laws, continual
outcome.

---

*This design was handed to Hermes as the execution specification. The book and the
software are the same project: build the laboratory first, the laboratory produces
the experiments, and the experiments determine what the book claims.*
