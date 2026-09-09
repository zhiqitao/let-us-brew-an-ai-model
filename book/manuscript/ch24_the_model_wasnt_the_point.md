# 24. The Model Wasn't the Point

We began with a question that sounded technical: *can a small language model learn
to solve programming tasks?* The answer we got was more interesting and less about
the model than we expected.

## Where the journey started

The premise was: building a small model is relatively easy; determining what it
actually learned is the hard part. That premise turned out to be more accurate than
we had any right to expect. The model was built in an afternoon. Understanding what it
had — and had not — learned took the rest of the book.

We built a laboratory, not just a model. Four artifacts: a **controlled world** (an
AST-whitelisted Python sandbox), a **teacher** (a semantic dataset generator), a
**judge** (an execution-based, mutation-tested evaluator), and the **student** (the
model itself). The model was only one component. The experiment was the subject.

## What the laboratory produced

The experiments told a clean, coherent, honest story:

- **The model learns.** On individual operations it reliably maps natural language to
  correct Python, beating a hand-written template rule system and reaching ~90%
  in-distribution.
- **But it is surface-tied.** Change the variable names, and it drops to 0.35. Change
  the wording while keeping the computation identical, and it falls to **0.000** —
  below both baselines.
- **And it cannot compose.** Even though it knows every primitive, it scores **0.000**
  on operations that combine two things it knows.
- **Neither capacity nor data fixes it at this scale.** A ~33× larger model (up to
  29.3M) and many more examples leave the composition boundary at 0.000.

Along the way, the laboratory caught itself. The first time we evaluated the model, it
scored 0.000 — and it wasn't the model's fault. The evaluator was broken (a NUL-
padding artifact in the output made every program fail to parse). Fixing the *
tester* revealed the model's true 0.897. That moment — discovering our own instrument
was wrong before we trusted it — is as much a part of this book as any model result.

## The deeper achievement

The book's real finding is not "small models are limited." It is:

> **Building a trustworthy experiment was harder and more valuable than building the
> model.**

The model was the instrument. The experiment was the subject. The things that made
this work — the sandbox that rejects anything not explicitly allowed, the judge that
executes code and compares semantics rather than strings, the mutation suite that
red-teams the judge, the leakage audit that caught our own dataset leaking the answer,
the baselines that ask "could a simpler machine do this?", the four-level taxonomy
that refuses to collapse everything into one number — those are the actual
achievements here.

## What the reader takes away

If we take one thing from this book, it is a habit, not a fact:

> **Never trust a number from a model we don't understand, or from an experiment we
> haven't audited.**

Before we believe "the model learned to add," we have to be able to answer: remove
the memorization, the retrieval, the templates, the leakage, the evaluator artifacts —
what remains? In our case, for simple primitives, what remained was genuine
learning-within-a-surface-form. It was real, and it was narrow, and it did not
compose.

That is the honest, complete answer. We did not build a general programmer. We built
the means to ask, precisely and honestly, what a small model can and cannot learn —
and we got an answer worth having.

**Build the model. Test the model. Break the evaluator. Break the model. Audit the
data. Challenge the conclusion. Repeat.** Only then say: "This is what the model
learned."

The model was not the point. The experiment was.
