# 5. Build the Teacher

We need data. But not just any data — we need data we can *trust* to be fair, and
data we can carve up to test the model honestly.

A teacher preparing worksheets for a test is the model. A bad teacher writes twenty
questions that are all the same question with different numbers — the student can
memorize one template. A good teacher writes questions that look different on the
surface but test the same idea, so a student who actually learned the idea passes
whether or not they've seen the phrasing.

Our **teacher** is that good worksheet-writer. But there's something special about the
way we build it, and it's the single most important design decision in the whole book.

## Semantic-first: start with the meaning, not a template

The naive way to generate data is to write a template and fill in a few blanks:

```
template -> sentence -> code
```

We write "add {a} and {b}" and a few code snippets, and we are done. This is fast and
easy, and it's exactly the wrong way to do it. The problem is that the sentence and
the code are generated **independently**, from a template, so there's no guarantee they
mean the same thing. We can end up with a sentence that says "add" but code that
subtracts, or a test that checks the wrong thing.

We do the opposite. We start from the **meaning** and generate everything else **from
it**:

```
SEMANTIC INTENT
   -> PROGRAM STRUCTURE
      -> REFERENCE CODE
      -> NATURAL LANGUAGE
      -> HIDDEN TESTS
```

The key insight is at the top: **one semantic record drives all three.** There is no
way for the sentence to disagree with the code or the tests, because they are all the
same meaning, rendered three ways. If we start with "the function should return
`a + b`," the sentence says "sum," the code adds, and the tests check addition — and
they can't drift apart, because they all came from the same seed.

## What a "semantic record" looks like

The meaning is captured in a small, structured object. It is not English and not code;
it is the *idea* underneath both. For an addition task it looks like this:

```json
{
  "operation": "add",
  "args": [{"name": "a", "type": "int", "role": "operand"},
           {"name": "b", "type": "int", "role": "operand"}],
  "output_type": "int"
}
```

From this single object, we generate:

1. **the reference program** — `def solve(a, b): return a + b`,
2. **the natural-language prompt** — e.g. *"Write a function that takes two numbers,
   a and b, and returns their sum"*,
3. **the hidden tests** — e.g. `{args:[-28,47], expected:19}`, `{args:[0,0], expected:0}`,
   and edge cases we'll get to.

This is the heart of the teacher. The pump is `make_task`, which takes an operation
and a seed, builds the semantics, and then calls three sub-generators that all read
that one record.

## The four sub-generators

The teacher is really four small pieces working together, all fed by the same
semantics:

**1. `make_semantics`** — builds the semantic intent: the operation plus its argument
descriptors. It pulls argument names from a controlled set (so we can vary them later),
assigns an input/output type, and tags the task with a complexity score.

**2. `generate_reference`** — turns the semantics into the ground-truth Python. This
is the correct program the grader is validated against. For `add` it emits
`def solve(a,b): return a+b`; for `list_sum` it emits a loop over the list.

**3. `render_nl`** — turns the same semantics into English, using one of several
**template families**. A template family is just a different way of phrasing the same
instruction. For addition, we have phrases like:

- *"Write a function that takes two numbers, a and b, and returns their sum."*
- *"Implement solve so that given a and b it returns their sum."*
- *"Define a function solve(a, b) that returns a + b."*

Same meaning, three different wordings. This is what gives the dataset linguistic
diversity — and, more importantly, it's what lets us later test whether the model
learned the *idea* or just one *sentence*.

**4. `generate_hidden_tests`** — generates test cases **from the semantics**, not from
the reference program's logic. It deliberately covers edge cases: ordinary values,
zero, negatives, boundary values, large magnitudes, and (where legal) empty lists. For
each it computes the expected value from the operation itself.

## Why the tests come from the meaning, not the code

This is a subtle but crucial point. If we generated the tests by looking at the
reference program, a model that memorized the reference would already know what the
tests check. By generating them from the *semantics* instead, the tests probe whether
the model independently understands the operation — whether it can produce the right
answer for inputs it could not have seen in the reference.

## Maximizing controlled diversity

A good teacher does not just produce many examples; it produces *diverse* ones while
holding the semantics fixed. We deliberately vary three things:

- **constants** — different values each task, so the model can't memorize outputs,
- **identifiers** — `a, b` vs `left, right`, so it can't tie the operation to
  particular names,
- **wording** — several template families per operation, so it sees the same idea said
  many ways.

This controlled diversity is what makes the *generalization tests* later possible.
Because we control *how* we vary the surface, we can also *hold it out* and test
whether the model generalizes. That's not an accident; it's the whole point.

## Avoiding accidental correlation

The danger in any generated dataset is **accidental correlation** — a pattern that
makes the answer trivially predictable from the surface. The classic failures:

- every addition example uses the word "total";
- every maximum example uses the variable `x`;
- every multiplication has exactly three arguments;
- every loop example is exactly one sentence long;
- every operation uses one unique wording.

If those correlations exist, a model (or a trivial classifier) can solve the task
without learning the computation. The generator is built to break them, and then — this
is the crucial part — we **check that it actually did**.

## The leakage audit

Before trusting any dataset, we ask: *can a trivial classifier predict the answer from
the surface alone?* The method is deliberately crude: train a TF-IDF + logistic
regression model on the natural-language prompts and see how well it predicts the
target operation from the words alone. If a dumb classifier succeeds, the wording is
leaking the answer.

And it caught us. On our first pilot renderer, a trivial classifier predicted the
operation from the wording with **100% accuracy**. That's a red flag, and it's a
valuable catch: it means our wording was so tied to the operation that a model which
"learned" might just be exploiting the phrasing. We recorded it as a findable artifact
(finding-001) and noted exactly what it means for the experiments that follow.

This is the teacher doing its real job. A dataset generator that only produces data is
half a tool. One that produces data **and audits it** is a laboratory instrument.

## The takeaway

The teacher is not a bulk-data tool; it is a controlled instrument. Its job is to
produce data with *controlled* diversity and *audited* cleanliness, so that when the
model succeeds we can attribute it to learning the computation — not to the data
accidentally giving away the answer.

And the reason this matters so much is the whole book's premise. Everything later —
the generalization tests, the composition test, the capability map — depends on the
data being a *fair* test. The teacher is where that fairness is built.
