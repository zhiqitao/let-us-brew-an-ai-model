# 10. Does It Actually Work?

We have a trained model, a judge, and a test set. The natural question is the one
the whole book has been building toward: *does it actually work?*

And the answer, as with almost everything in this book, is **"it depends on what we mean,"** and then **"let's measure it rather than argue."** Because "works" is not a
single number. It is a question about *which* kind of capability, under *which*
conditions, measured in *which* way. The job of this chapter is to take that vague
word and replace it with something we can actually see.

## The setup

We trained a small decoder-only transformer on 1,400 generated tasks: the model reads
a natural-language specification and must produce the reference Python program. The
trained model is tiny — **884,224 parameters** (0.88M), of which 53,632 are the
embedding and 830,592 are the actual computation. It saw 1,500 gradient steps on a
batch of 16, reaching a training loss of **0.0208**.

We then asked it to solve 300 **held-out** test tasks it never saw, and scored each
generated program by executing it against that task's hidden tests. This is the
moment of truth for the whole apparatus: everything we built — the world, the
teacher, the judge, the rivals — converges on this measurement.

## One task, end to end

The cleanest way to see what the judge does is to follow one task from prompt to
verdict. Here is a real run against the pilot model.

**The request.** "Implement solve so that given a and b it returns their sum."

**The reference program** (the teacher's ground truth):

```
def solve(a, b):
    return a + b
```

**What the model actually produced** (greedy decoding, this checkpoint):

```
def solve(a, b):
    return a + b
```

**The hidden tests** (input/expected pairs) that the judge then runs:

| inputs | expected |
|--------|----------|
| (87, -98) | -11 |
| (0, -24) | -24 |
| (-6, 0) | -6 |

The judge runs the model's program on each pair, compares the output with the
semantic comparator, and reports **pass@1**. This task passes.

Now the informative contrast: a task the model *had not seen*. The teacher's
composite `abs_add` asks for the sum of the absolute values of two numbers
(`abs(a) + abs(b)`). The model, which knows both `abs` and `add` individually, was
fed:

> "Write a function that takes two numbers a and b, takes the absolute value of each,
> and returns their sum."

and produced:

```
def solve(a, ab
```

— a truncated, unusable fragment. Greedy decode stopped mid-token. On a genuinely
reworded surface ("Return the value obtained by adding together two numbers, denoted
p and q."), it produced:

```
def  a solve(a, b
```

again truncated. These two live examples carry the book's whole point: on a familiar
surface the model writes correct code, and on an unseen surface or a new combination
it collapses to a fragment. Nothing about the failure required the hidden tests to be
"unfair" — the judge simply ran programs that were not complete.

## What we measured: pass@1

Here is the headline result, reported as **problem-level hidden-test pass@1 under
greedy decoding** — that is, for each problem, did the single program the model
produced pass *every* hidden test?

| Candidate | syntax | executable | **pass@1** |
|-----------|--------|-----------|------------|
| **MODEL** | 0.897 | 0.897 | **0.897** |
| TEMPLATE | 1.000 | 0.900 | 0.800 |
| RETRIEVAL | 1.000 | 1.000 | **1.000** |

Three things stand out.

**First, the model genuinely learned something.** 0.897 means that ~90% of the time,
an unseen problem's natural-language spec produced a program that passed all its
hidden tests. That is not a toy result. And crucially, it **beats the hand-written
template/rule baseline** (0.800). A hard-coded pattern-matching system that
recognizes keywords like "sum" and emits a template gets 80%; our learned model gets
~90%. So the model is doing *more* than a fixed rule system can do on this task.

**Second — but retrieval does even better.** A trivial TF-IDF retriever that does
nothing but find the closest training example and reuse its program scores **1.000**.

That second fact is not a failure; it is the single most important thing this pilot
taught us. It tells us the task, as currently constructed, is **too easy to force
generalization**. When a non-learning lookup solves 100% of the test set, then the
test set is solvable by retrieval, and a model scoring 90% is not yet being tested on
whether it can generalize — only on whether it can match the surface form of a
training example.

This is exactly the "task too easy" outcome the experimental plan anticipated, and it
is scientifically useful: it tells us *how to make the next task harder.*

## The moment that broke us (and the evaluator, not the model)

There is a story behind these numbers that is more instructive than the numbers
themselves, and it is worth telling plainly. When we ran the evaluation for the very
first time, the model scored **0.000**. Not 0.897 — zero. Every single generated
program failed the syntax check.

Our first instinct, naturally, was that the model was useless. We had spent hours
building a careful apparatus and the tiny model could not even produce a parseable
program. It would have been easy to conclude "the model doesn't work" and write the
whole thing off.

But the book's own discipline — *test the tester* — demanded we ask whether the
*judge* was the problem, not the model. So we looked at what the judge actually
saw. And there it was: the generated programs were valid Python up to the end of the
program, except they had a run of **NUL bytes** (`\x00`) appended after it. The
model had learned to pad its output with a byte that means "nothing." Python's parser
correctly rejects NUL bytes — they are not valid source. The fault was in the
*extraction contract*, not the parser: we had failed to strip the padding before
handing the output to `ast.parse`. So `ast.parse` threw a syntax error on what was,
after truncation, good code, and the judge scored the model's program as a *syntax
failure*.

The fix was a single line: truncate the generated program at the first NUL byte. A
trivial change, and suddenly the model's score leapt from 0.000 to 0.897.

This is the single most important lesson of the whole book, and it is not about the
model at all. **The evaluator was broken, not the model.** We had designed every
experiment to detect shortcuts and outright cheating in the *model*, and we nearly
missed the one case where the measuring stick itself was faulty. The "test the
tester" principle — that we must verify the tool measures what we think it measures
before trusting a single number it produces — was not a formality. It just saved the
entire project from a false negative.

The reason we caught it is worth pausing on. We did not catch it because we are
clever. We caught it because we had *already* built a method for testing testers
(the mutation suite in Chapter 6), and we had written the pilot's results to a
manifest and looked at the intermediate numbers, not just the headline. Had we
grabbed the final pass@1 and moved on, we would have shipped a book claiming a tiny
model cannot write Python — a conclusion that was wrong.

## The shortcut audit

Before we trust the "0.897" number, we have to ask how the model might have gotten
there without learning.

1. **Suspected shortcut: retrieval of a near-duplicate prompt.**
   **Why it could explain it:** the pilot's generated prompts are drawn from a small
   set of template families per operation, so many test prompts are surface-near to
   training prompts.
   **Control:** we ran the retrieval baseline — 1.000. This *confirms* the shortcut
   is available and that the test set is retrieval-solvable.
   **What it rules out:** nothing yet, because the model's 0.897 is *below* the
   retrieval ceiling. It does not rule out the model partially relying on surface
   similarity.
   **What remains unresolved:** whether the model's own success is grounded in the
   *computation* or in the *surface form*. To answer that, we need the Level-3
   (surface-change) and Level-4 (composition) experiments, which we run next.

2. **Suspected shortcut: exact memorization.**
   **Why it could explain it:** the model saw 1,400 examples; maybe it memorized them.
   **Control (Ch14):** on held-out prompts it still passed 59/60, and on a *canary*
   prompt it produced the *general* program rather than a memorized literal.
   **What it rules out:** pure example-memorization.
   **What remains:** the deeper question — is the *general program* it produces
   genuinely tied to the computation, or to the particular wording?

## The honest summary

The pilot succeeded in exactly the way a pilot should: the laboratory works, the
model learns, and — perhaps most valuably — the experiment told us something
*uncomfortable but true*. The task is retrieval-solvable, and a model that beats a
template rule system yet sits below a lookup table has not yet been tested on the
thing we care about most: whether it generalizes.

And we were reminded, in the most direct way possible, that the measuring stick is as
much a subject of the experiment as the model. The instrument and the thing measured
both needed to be honest, and only one of them initially was.

That is the baseline from which every later experiment is measured. From here, we
stop making the task easier and start making it *probe* generalization.
