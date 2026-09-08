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

## The shortcut audit, and the honest boundary

This is the subtle part. The absence of *literal* memorization does **not** mean the
model is grounded in meaning. Exactly the opposite mechanism is at work. Our Stage-3
experiment showed that if you change the *surface form* — the variable names or the
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
