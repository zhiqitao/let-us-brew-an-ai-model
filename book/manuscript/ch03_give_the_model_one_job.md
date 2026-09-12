# 3. Give the Model One Job

Before we can run any experiment, we have to pin down the task so precisely that a
machine can carry it out and we can score it objectively. Vague tasks give vague
answers; a task with concrete inputs, runnable outputs, and hidden tests gives
crisp, checkable answers.

A well-designed exam question is the model. It's not enough to say "write a program about numbers." We need: exactly what the input is, exactly what the program should do, and
exactly how to check if it's right. That's what we're about to define.

## The task

The model receives a **natural-language specification** of a programming task and
must produce a **Python program** that solves it. That program is then executed
against hidden tests.

![The one job](figures/fig_task.png)

The contract is simple: a natural-language specification in, a program out, and a
set of hidden tests to grade it against. Everything else follows from it.

Concretely, the model sees something like:

> "Write a function that takes two numbers, a and b, and returns their sum."

and must produce:

```
def solve(a, b):
    return a + b
```

We score it by running that program against a set of hidden test cases (inputs with
expected outputs) and checking whether the program's output matches, semantically,
for every case.

## The task schema

Every task is described by a small, formal schema — the ground truth that drives
everything. The key insight is that **one semantic record generates all three**
things we need: the reference program, the natural-language spec, and the hidden
tests. That way there is no drift between "what the task is" and "how we ask for it"
and "how we test it."

The semantic core captures the operation and its arguments:

```
{
  "operation": "add",
  "args": [{"name": "a", "type": "int"}, {"name": "b", "type": "int"}],
  "output_type": "int"
}
```

From that single record, the teacher generates:
1. the reference Python (`def solve(a,b): return a+b`),
2. a natural-language specification (in one of several phrasings),
3. a set of hidden tests (ordinary, zero, negative, boundary, large cases).

## The pure-function constraint

For the pilot we constrain the generated programs to be **pure functions**. No side
effects, no file I/O, no randomness. This makes evaluation deterministic and
unambiguous: for a given input, there is one correct output. It is a deliberate
simplification, and it is exactly what makes the task cleanly measurable.

## Hidden tests

The hidden tests are the heart of evaluation. Each task carries an independent set of
test cases designed to catch real errors, not just a single happy path. For an
arithmetic task we include ordinary values, zero, negatives, boundary values, and
large-magnitude values. The tests are generated independently of the reference
program's *logic* — computed from the semantics, not copied from the solution — so
that a model that merely memorizes the reference still can't predict the exact test
suite.

It is worth being precise about what "independently" buys us and what it does not. The
tests are produced by a *separate generator* from the program, which means they are an
independent oracle guard: if the program-generator and the test-generator shared a bug,
the tests could pass a wrong program (a correlated-implementation-error problem). Because
the tests are a separate path over the same `semantics`, the oracle is decoupled from the
program generator, so a single mistake in either does not silently become a false
pass. But both ultimately derive from the same operation definition, so this is a *control
for correlated implementation bugs*, **not** a proof that the model "understands" the
operation — understanding is a different question (and the surface/composition chapters
answer it separately).

## The success criterion

For a single problem, the success criterion is:

> **Problem-level hidden-test pass@1** — did the one program the model produced pass
> *every* hidden test for that problem, under the evaluation's default
> temperature-0.8 sampled decoding?

This is deliberately strict. A program that passes 7 of 8 hidden tests *fails* the
problem. That strictness is what keeps the measurement honest: we are not measuring
"close," we are measuring "correct."

## Why this specific task

Natural-language-to-Python is a good laboratory task precisely because it has
everything a controlled experiment needs:

- **Deterministic.** Same spec, same program, same tests.
- **Executable.** We run real Python and compare real outputs.
- **Objectively scorable.** Pass/fail, no judge-subjectivity.
- **Synthetic.** We can generate as much controlled data as we want.
- **Controllable difficulty.** We can escalate from `a+b` to compounded operations.
- **Compositional splits.** We can train on pieces and test on unseen combinations.
- **Memorization tests.** We can plant canaries and check for exact reproduction.
- **Auditable.** We can inspect the exact generated program and run shortcut audits.

The model could not ask for a clearer job. Now we have to build the tools that let us
run and score it: a controlled world, a teacher, a judge, and rivals.
