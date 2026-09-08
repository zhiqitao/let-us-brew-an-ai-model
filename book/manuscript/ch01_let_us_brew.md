# 1. Let Us Brew an AI Model

**Working subtitle:** What tiny language models can actually learn when given one job.

---

A tiny model appears to solve a programming problem. It reads a sentence — *"Write a
function that takes two numbers, a and b, and returns their sum."* — and produces
just the right Python:

```python
def solve(a, b):
    return a + b
```

We run the hidden tests. It passes all of them. If this were a demo, we'd celebrate
and move on.

But this book is not a demo. So instead of celebrating, we ask the question that
everything in this book hinges on:

> **Why did it answer correctly?**

Maybe it genuinely learned the mapping from the words "sum" and "a and b" to the
computation `a + b`. Or maybe it memorized the exact sentence from training. Or
maybe it recognized this as a near-duplicate of an example it saw, and copied the
reply. Or maybe a simpler machine — one that does nothing but look up the closest
training example — could have done the same thing. Or maybe the test only looked
hard to pass.

The difficult part is not making the model answer. The difficult part is **knowing
why it answered.**

## The one-job constraint

This book gives a small language model exactly one, narrowly defined, objectively
testable job:

> **natural-language specification → Python program**

A model receives a description of a programming task and generates a solution. The
program is executed against hidden tests. That single choice — *executable output +
hidden tests* — is what makes this an experiment rather than a demo, because it gives
us things an ordinary language-model toy rarely does:

- deterministic inputs
- executable outputs
- objective evaluation
- synthetic data generation
- controlled difficulty
- hidden tests
- compositional splits
- memorization tests
- shortcut audits
- reproducible experiments

## What this book is (and is not)

This is **not** a transformer tutorial, and it is **not** a guide to building a
chatbot, an agent, a coding assistant, or a frontier model. It is a controlled
empirical investigation: *how much structured programming capability can a small
language model actually learn, and how can we tell whether it learned it rather than
memorized it or exploited a shortcut?*

The model is the instrument. The experiment is the subject.

## The difficult part

A natural first reaction is: "building a small model is the hard part." It isn't.
Once the laboratory works, a ~0.9M-parameter model will reliably map a handful of
programming sentences to correct Python in-distribution. That part is almost easy.

The hard part is everything after: proving the model didn't just memorize, testing
whether it generalizes when you change the *wording* but not the *computation*,
testing whether it can *combine* two things it knows into something it never saw, and
auditing the evaluator to make sure the number it reports is trustworthy.

This book builds a laboratory, runs those experiments, and reports exactly what
happened — including the places where the model fell flat and where our own
evaluator turned out to be wrong.

The model was the instrument. The experiment was the subject. Let's brew.
