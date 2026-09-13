# 14. The Model That Memorized Everything

We spend a lot of this book trying to catch the model cheating. So far we have found
that it is *surface-tied* and *non-compositional*. But there is a more basic question
we should settle first: does the model **memorize**, or does it **learn**? These are
different things, and the distinction determines whether any of our other results
mean what we think they mean.

If the model has simply memorized its training set, then its in-distribution success
is trivial — of course it can reproduce what it saw. If it has *learned*, then it can
apply the mapping to things it never saw. Our Stage-1 result said the model gets
~90% on *held-out* problems, which is a strong hint it learned. But "held-out" can be
a weak guarantee if the held-out problems are surface-near to training ones. So we
test memorization explicitly.

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
| **1. New task ID, same prompt + program** | same | same | different | **No** — only the evaluator's hidden-test *values* change; this is NOT a new model example |
| **2. New prompt, same target program** | different | same | same | **Yes** — a new surface, same computation; a genuinely new model input |
| **3. Unseen program structure** | different | different | different | **Yes** — new input AND new target structure (composing pieces never combined) |

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

**Test 2 — held-out generalization.** Give the model a *fresh* prompt for the same
operation, one it never saw, and ask for the program. If it passes, it has not merely
memorized the 60-prompt sample.

**Test 3 — the canary.** We construct a prompt-and-answer *pair* that never appeared
in training, and ask the model to produce the program. If the model outputs the
general program (e.g. `return a + b`), it is doing the computation. If it outputs some
fixed literal or garbage, it might be memorizing something else.

The canary is a sharp probe, and it is worth explaining what it does and does not
show. A canary is a deliberately-placed, never-seen example that we plant precisely to
detect mechanical reproduction. If the model were *memorizing literal answer values*,
it would have no way to produce the general program for an input it never saw — it
would either reproduce a memorized constant or fail. When it instead emits
`def solve(a,b): return a+b`, it is not reproducing a stored *value*; it is producing a
general program.

Two things the canary does **not** settle. First, it is a *held-out probe*, so it
demonstrates transfer to a prompt we did not train on — it is evidence the model
generalizes, not proof that it has "understood" the arithmetic. The model emits
`return a + b`; it does not execute the addition. Python does the arithmetic. What the
model learns is a request-to-program mapping (and calling it a "canary" with the
memorization connotation is really a held-out-probe result, not the classic
memorization canary, which instead plants a distinctive training example and measures
whether it is later reproduced).

Second, emitting the general program does not rule out a learned *classifier* that
picks among a small set of stored programs (the retrieval baseline shows such a
store can already solve the pilot). A memorized-then-selected correct general program
would also pass unseen inputs, so a passing program is not by itself decisive evidence
against program memorization. Still, the comparator caveat cuts the other way too, and
we want to state the direction correctly: on the reworded surface the neural model scores
**0.000** while the retrieval baseline scores **0.125** — so on that particular
evaluation the retriever is the *stronger* of the two, not the weaker. The modest claim
that does survive is: for simple *familiar* primitives (the pilot's in-distribution
split, new instances of seen prompts), the model forms a general program-generating rule.
It does not support the stronger claim that the model "performs arithmetic" or
"understands addition," nor does it support treating the neural model as more robust to
rewording than a retriever.

## The result

On a 60-example sample:

- **Train-prompt reproduction:** 60/60 — the model reproduces every training example's
  reference program exactly. (Expected for a well-fit learner.)
- **Held-out generalization:** 59/60 — it also solves essentially every *unseen*
  prompt of the same operation.
- **Canary:** the model emits the **general program** (`def solve(a,b): return a+b`),
  not a memorized constant.

## What this tells us — a nuanced answer

For **simple primitives**, the model behaves like a **learner, not a parrot**:

- It reproduces training examples (expected — a learner does that too).
- It **generalizes** to held-out prompts (59/60), so it did not simply memorize the
  60 instances.
- On a **canary** it emits the general program, not a memorized literal — so it did
  not memorize answer values.

So at the level of *individual examples*, the model is not a parrot. It has learned
something that transfers to new instances of the same operation. This is real learning
of a narrow kind, and it is worth stating clearly: the model did not merely memorize
its training set. It formed a general rule for each primitive.

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
| Memorize exact training instances? | **No** — generalizes to held-out + canary |
| Ground the computation independent of wording? | **No** — collapses on new wording |

The model is neither a parrot nor a mathematician. It has learned a *robust association
within a surface form* — it is not memorizing specific examples, but it is also not
representing "addition" in a way that survives being said differently.

## The lesson

Detecting "memorization" is not a simple yes/no. The useful question is not *"did it
memorize?"* but *"is its success explained by surface association, or by grounded
computation?"* Our probes show a clear answer for this model: it escapes example-
memorization but is caught by surface-memorization. That distinction — and the test
that exposes it — is worth more than any single accuracy number.

What this tells us is that "memorization" is not a single thing. There are at least
two kinds, and they have very different implications. The model did *not* memorize
specific training pairs — it generalizes across instances. But it *did* memorize the
surface form — it can only generalize within the phrasing it saw. So the honest
characterization is that the model's knowledge sits at a specific level of the
taxonomy: it has moved past Level 1 (reproducing exact examples) into Level 2 (new
instances of the same task), but it is firmly stuck at Level 1 with respect to the
*surface* — it cannot survive a change to the outer layer. Distinguishing these kinds
of memorization, and knowing which one we are looking at, is the whole point of the
experiment.
