# 14. The Model That Memorized Everything

We spend a lot of this book trying to catch the model cheating. So far we have found
that it is *surface-tied* and *non-compositional*. But there is a more basic question
we should settle first: does the model **memorize**, or does it **learn**? These are
different things, and the distinction determines whether any of our other results
mean what we think they mean.

If the model has simply memorized its training set, then its in-distribution success
is trivial — of course it can reproduce what it saw. If it has *learned*, then it can
apply the mapping to things it never saw. Our Stage-1 result said the model gets
~90% on the pilot's test records, which is a hint that it learned something more than
literal reproduction. But that result reused training prompt strings, so it is not by
itself evidence of transfer to a new prompt. So we test memorization explicitly, and we
are careful about what "new" means.

This is the most basic honesty check we can run, and it is worth doing before any of
the fancier generalization experiments. Because if the model were simply memorizing, it
would be absurd to write a whole book about its compositional failures — a parrot
doesn't compose anything. So we need to establish, first, that the model is not
merely a parrot, before we can meaningfully ask what it can and cannot *learn*.

## The challenge of detecting memorization

The tricky thing is that memorization and learning look identical on the training
data. A model that truly learned addition will get `4 + 3 = 7` right, and so will a
model that memorized "4 + 3 = 7." Both ace the training set. So we cannot tell them
apart by looking at training performance at all. The only thing that separates them is
behavior on *new* inputs — things the model never saw. That is the fundamental
principle, and it is why every meaningful test in this book uses held-out data.

But "new" is not one thing. Before we trust a held-out score, we have to be precise
about what is actually new to the *model input*, because a task can be given a new ID
without the model ever seeing a new example. The table below separates the three
things that all get loosely called "a new task," and it keeps prompt novelty separate
from target-program novelty (a different prompt is not the same thing as a different
program to write).

| Case | Prompt (model input) | Target program | Hidden tests | New to the model input? |
|------|----------------------|----------------|--------------|-------------------------|
| **1. New task ID, same prompt + program** | same | same | different | **No** — only the hidden-test *values* change; not a new model example |
| **2. New prompt, same target program** | different | same | same | **Yes** — new surface, same computation |
| **3. Unseen program structure** | different | different | different | **Yes** — new input AND new structure |

So "new" is not one thing. A new *task ID* that only changes the hidden-test values is
new to the *evaluator*, not to the model. A genuinely new *prompt* within a familiar
family is new to the *model input* (and is a real in-distribution generalization test). A
new *target structure* is new to the *target* as well. When the book says "the model
never saw this," we mean the model-visible prompt was new — and where that is not
verified, we flag it rather than assume it.

## Three tests

We use three complementary probes on the trained pilot model.

**Test 1 — train-prompt prefix reproduction.** Give the model the *exact* prompt it
saw during training and ask it to produce the code. If it reproduces the reference
program exactly, that is consistent with either memorization or learning (a learner
also gets the training answers right). So this alone proves nothing — but it grounds
the other two.

**Test 2 — fresh-instance generalization (task-ID probe).** Give the model a prompt it
saw in training, but with a *new task ID* that changes the hidden-test *input values*,
and ask for the program. If it produces a passing general program, it is not merely
reproducing a single stored answer for that record. **Important caveat:** this is a
task-ID-level probe, not a new-prompt test. Because the pilot reuses the same 21 prompt
strings in training and test, this does **not** establish generalization to a prompt the
model never saw (see the novelty audit in Appendix C); it shows the model produces a
general program that passes *new inputs* for a *familiar* prompt.

**Test 3 — the canary.** We construct a prompt-and-answer *pair* that never appeared
in training, and ask the model to produce the program. If the model outputs the
general program (e.g. `return a + b`), it is producing a program for an unseen pair; if it
outputs some fixed literal or garbage, it might be memorizing something else.

The canary is a sharp probe, and it is worth explaining what it does and does not
show. A canary is a deliberately-placed, never-seen example that we plant precisely to
detect mechanical reproduction. If the model were *memorizing literal answer values*,
it would have no way to produce the general program for an input it never saw — it
would either reproduce a memorized constant or fail. When it instead emits
`def solve(a,b): return a+b`, it is not reproducing a stored *value*; it is producing a
general program.

Two things the canary does **not** settle. First, it is a held-out *pair*, so it
demonstrates the model emits a general program for a prompt/pair combination we did not
train on — evidence the model does not just reproduce stored constant *values*. It is
not proof that it has "understood" the arithmetic; the model emits `return a + b`, it does
not execute the addition (Python does). What the model learns is a request-to-program
mapping. (Calling this a "canary" with its memorization connotation is really a
*held-out-probe* result, not the classic memorization canary, which instead plants a
distinctive training example and measures whether it is later reproduced.)

Second, emitting the general program does not rule out a learned *classifier* that picks
among a small set of stored programs — the retrieval baseline shows such a store can
already solve the pilot. A correct general program emitted for a familiar prompt is also
consistent with the model having *selected* a general program it saw many times in
training, rather than having generated it compositionally for the first time. So a passing
program is not by itself decisive evidence against program memorization. On the reworded
surface, the neural model scores **0.000** while the retrieval baseline scores **0.125** —
so on that particular evaluation the retriever is the *stronger* of the two, not the
weaker. The modest claim that does survive is: for simple *familiar* primitives (the
pilot's in-distribution split — new instances of seen prompts), the model forms a
general program-generating rule. It does not support the stronger claim that the model
"performs arithmetic" or "understands addition," nor that it is more robust to rewording
than a retriever.

## The result

On a 60-example sample:

- **Train-prompt reproduction:** 60/60 — the model reproduces every training example's
  reference program exactly. (Expected for a well-fit learner.)
- **Fresh-instance generalization (task-ID probe):** 59/60 — for a familiar prompt with a
  *new task ID / new input values*, it produces a passing general program.
- **Canary (held-out pair):** the model emits the **general program** (`def solve(a,b): return a+b`),
  not a memorized constant.

## What this tells us — a nuanced answer

For **simple primitives**, on *familiar prompts with fresh execution inputs*, the model
behaves more like a **learner than a fixed literal-retriever**:

- It reproduces training examples (expected — a learner does that too).
- It passes a task-ID probe (59/60), so for a familiar prompt it does not merely emit one
  stored answer per record; it emits a general program that, when **Python** runs it with
  fresh execution inputs, produces the correct result. The generalization to new input
  *values* is performed by the generated program, not by the model re-computing them.
- On a held-out probe it emits the general program, not a memorized literal — so it did
  not memorize *answer values*. (But emitting a general program it saw many times in
  training is also consistent with program *memorization*, so this does not by itself rule
  that out.)

So at the level of *individual records with fresh inputs*, the model is not a literal
value-parrot: it regenerates a general program for a familiar prompt. **This is real,
but narrow.** Because the pilot reuses the same prompt strings in training and test, none
of these probes demonstrates transfer to a prompt the model never saw, nor program
memorization to be absent. That genuinely-new-prompt question is what the surface and
composition holdouts answer later.

## The shortcut audit, and the honest boundary

This is the subtle part. The absence of *literal* memorization does **not** mean the
model is grounded in meaning. Exactly the opposite mechanism is at work. Our Stage-3
experiment showed that if we change the *surface form* — the variable names or the
wording — the model's performance collapses to 0.000. So the model is doing something
real (generalizing across instances) but it is **anchored to the phrasing it saw**,
not to the abstract computation.

So the refined picture is:

| | What the model does |
|---|---|
| Memorize exact answer *values*? | **No** — canary produces a general program, not a literal |
| Memorize the prompt→program mapping for a *handful* of stored programs? | **Not excluded** — retrieval baseline shows a selectable store already solves the pilot |
| Produce a general program that passes *new inputs* for a familiar prompt? | **Yes** — 59/60 on the task-ID probe |
| Ground the computation independent of wording? | **No** — collapses on new wording; see Chapter 15 |

The model is neither a literal parrot nor a mathematician. It has learned a *robust
association within a surface form* — it is not emitting memorized answer values, and it
can produce general programs for fresh inputs of a prompt it saw in training, but the
prompts it succeeds on are exactly the familiar ones, and it cannot survive being said
differently.

## The lesson

Detecting "memorization" is not a simple yes/no. The useful question is not *"did it
memorize?"* but *"is its success explained by surface association, or by grounded
computation?"* Our probes show a clear answer for this model: it escapes example-
memorization but is caught by surface-tied association (phrasing association). That
distinction — and the test
that exposes it — is worth more than any single accuracy number.

A note on vocabulary, so nothing is smuggled in: in this book "memorization" stays
reserved for Question 1 (Memorization), and Question 3 (Surface) remains a separate,
separately measured question — the two are never merged into a single evaluation, here
or in Chapter 20. We use "surface-tied association" for the second outcome precisely
so the word "memorization" is not stretched to cover it.

What this tells us is that there are at least two different outcomes here, and they
have very different implications. The model did *not* memorize
answer values — a held-out probe yields a general program, not a literal. But it also
did not demonstrate transfer to a genuinely new prompt, and its success is confined to
the phrasing it saw. So rather than placing it on a single "memorize → learn" ladder, the
honest statement is more modest: it reliably regenerates correct general programs for
familiar prompts, and we have *not* verified whether it would do the same for a prompt it
had never seen. Distinguishing Q1 memorization from Q3 surface-tiedness, and being
explicit about which one we are looking at, is part of the experiment.
