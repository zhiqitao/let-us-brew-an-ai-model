# 2. What Does It Mean to Learn?

We are going to use a word a lot in this book: *learned*. Before we do, we have to
be precise about what it means. "The model learned to add" is a sentence many
readers would accept. That acceptance is exactly the problem.

## An operational definition

We will not use "learning" as a philosophical term. For this book, a model
demonstrates learned capability when **all** of the following hold, to the degree
the evidence supports:

1. **Performance improves systematically during training** — the loss goes down, and
   the behavior we care about reliably improves.
2. **Performance transfers to held-out examples** — it works on instances it never
   saw, not just the ones in training.
3. **Performance survives controlled changes to superficial features** — things like
   a different variable name, a different wording, or a harmless distractor, none of
   which should change the underlying computation.
4. **Performance survives appropriately designed structural changes** — it can
   combine known pieces in a new arrangement, not just reproduce arrangements it
   already saw.
5. **Simpler explanations have been tested and rejected.** The alternatives —
   exact memorization, retrieval of a near-duplicate, a template, dataset leakage, or
   an evaluator artifact — must be ruled out to the degree the experiment supports.

This definition is deliberately limited. We do not claim to determine whether the
model "understands" programming in a philosophical sense. We ask narrower,
answerable questions: *does it generalize? to what? and can a simpler mechanism
explain the result?*

## The four-level generalization spectrum

This is the book's central conceptual framework, and we will use it to organize most
of our experiments. It is a spectrum of *how* a result could have been obtained, from
the least to the most demanding.

**Level 1 — Memorization.** The model reproduces or exploits information closely
represented in training: an exact example, an exact constant, a familiar template,
memorized wording, a near-duplicate. Question: *can the result be explained by
remembering?*

**Level 2 — Distributional generalization.** The model succeeds on new examples
drawn from essentially the same distribution. It has seen the operation and the
frontier of *which* words and values, but not these exact instances. Question: *can
it perform on unseen instances of the same task?*

**Level 3 — Surface generalization.** The underlying problem is unchanged, but
superficial properties change: new constants, new variable names, new function
names, paraphrased wording, reordered clauses, harmless distractors. Question: *does
the capability survive changes that should not alter the computation?*

**Level 4 — Structural generalization.** The model must combine known components in
structures that were not present during training. If it was trained on `A`, `B`, and
`C`, can it do `A`-inside-`B`, or `B`-and-`C`, or `A` applied to the result of `C`?
Question: *can it compose learned capabilities, or only reproduce learned
combinations?*

**A rule we will follow strictly:** never collapse these four levels into a single
"generalization" number. A model that scores 90% "in-distribution" and 0% "on new
wording" has not generalized; it has memorized the phrasing. Reporting one number
would hide exactly the thing we most want to know.

## The recurring shortcut audit

Because we refuse to trust a single number, every major experiment in this book asks
the same question:

> **How could the model have gotten this result without learning what we think it
> learned?**

The candidate shortcuts are always the same list: memorized templates, memorized
constants, memorized identifiers, memoriized function names, wording artifacts,
sentence-length artifacts, dataset imbalance, train/test leakage, near-duplicates,
reference-solution artifacts, retrieval, evaluator weaknesses, hardcoded answers,
hidden-test leakage, output-format artifacts.

Every major experimental chapter therefore contains a **shortcut audit** with six
parts: (1) the suspected shortcut, (2) why it could explain the result, (3) the
control experiment, (4) the result of that control, (5) what the control rules out,
and (6) what remains unresolved.

This audit — not the headline accuracy — is the book's signature. It is the
difference between "the model works" and "we know why the model works."
