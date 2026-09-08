# 5. Build the Teacher

We need data. But not just any data — we need data we can *trust* to be fair, and
data we can carve up to test the model honestly.

Think of a teacher preparing worksheets for a test. A bad teacher writes twenty
questions that are all the same question with different numbers — the student can
memorize one template. A good teacher writes questions that look different on the
surface but test the same idea, so a student who actually learned the idea passes
whether or not they've seen the phrasing.

Our **teacher** is that good worksheet-writer: it generates training data with the
right kind of controlled diversity, and it never lets the surface give away the
answer so easily that a lazy model could cheat.

## Semantic-first

The most important design decision is the direction of generation. We do **not** start
with "here's a sentence, let me write code for it." We start with the **meaning**, and
generate everything else from it — so that the reference code, the natural-language
spec, and the hidden tests all agree, because they are all the same semantic record
rendered three ways.

```
SEMANTIC INTENT
   -> PROGRAM STRUCTURE
      -> REFERENCE CODE
      -> NATURAL LANGUAGE
      -> HIDDEN TESTS
```

The semantic core is minimal for the pilot:

```json
{"operation": "add", "args": [{"name": "a", "type": "int"}, {"name": "b", "type": "int"}]}
```

From this one record, the teacher produces:
1. the ground-truth Python,
2. a natural-language prompt (in one of several phrasings),
3. a set of hidden tests.

## Maximizing controlled diversity

A good generator does not just produce many examples; it produces *diverse* ones while
keeping the semantics fixed. We deliberately vary:

- **constants** — different values, so the model can't memorize outputs,
- **identifiers** — `a,b` vs `left,right`, so it can't associate the operation with
  particular names,
- **wording** — several template families per operation, so it sees the same
  instruction said many ways.

This diversity is what later lets us run surface-generalization tests: because we
control *how* we vary the surface, we can also *hold it out* and test whether the
model generalizes.

## Avoiding accidental correlation

The danger in any generated dataset is **accidental correlation** — a pattern that
makes the answer trivially predictable from the surface. Classic examples:
every addition uses the word "total"; every maximum uses variable `x`; every loop is
exactly one sentence long. If those correlations exist, a model (or a trivial
classifier) can solve the task without learning the computation.

We deliberately break these correlations and then — crucially — **audit for them**.

## The leakage audit

Before trusting any dataset, we ask: *can a trivial classifier predict the answer from
the surface alone?* We train a TF-IDF + logistic-regression model on the natural-
language specs and see how well it predicts the target operation.

And it *caught* something. On our first pilot renderer, a trivial classifier predicted
the operation from the wording with **100% accuracy**. That is a red flag: it means
the wording leaked the answer, so a model that "succeeded" might just be exploiting
the phrasing.

This is a crucial, early win for the methodology. We did not sweep the leak under the
rug; we recorded it as a findable artifact (finding-001) and noted exactly what it
means for downstream experiments: the pilot wording is too predictable for
*generalization* experiments, so we must add many more paraphrase families and hold
them out before any surface test.

## The lesson

The teacher is not a bulk-data tool; it is a controlled instrument. Its job is to
produce data with *controlled* diversity and *audited* cleanliness, so that when the
model succeeds, we can attribute the success to learning the computation — not to the
data accidentally revealing the answer. And when the data *does* leak, we want to find
out ourselves, before the model does.
