# 15. New Words, Same Problem

Here is the sneakiest question in the book, and it's the one that should worry you
most about any machine-learning result:

> **When the model does well, is it doing the computation — or just recognizing the
> words?**

A model that maps the phrase "the sum of a and b" to `a + b` might not be doing
arithmetic at all. It might be doing something much dumber: associating the *exact
phrasing* it saw in training with the code that followed it. If that's what's
happening, then the ability isn't "addition" in the model's head — it's a fragile
reflex tied to specific words, and it'll break the moment you say the same thing a
different way.

To find out, we run the **surface-generalization** test. The logic is simple and
elegant: if you change something that *shouldn't* change the computation — the variable
names, or the wording — and the model fails, then it never really learned the
computation. It learned the phrasing.

## The setup

We trained the model on arithmetic primitives, but only with **letter names** (`a`, `b`)
and only a **subset of the wording** used to describe each operation. Then we re-asked
the *identical* task three different ways and watched whether the model's ability
survived.

## The result

| Test | **MODEL** | TEMPLATE | RETRIEVAL |
|------|-----------|----------|-----------|
| Same as training | **0.900** | 0.800 | 1.000 |
| Same computation, `a,b` → `left,right` | **0.350** | 0.800 | 0.683 |
| **Same computation, reworded** | **0.000** | 0.875 | 0.125 |

Look at what happens when we touch only the *surface*, not the math.

- **New variable names.** The model was trained on `a` and `b`. We ask the same
  question with `left` and `right` — the *identical* operation. Performance collapses
  from **0.900 to 0.350**.

- **Reworded instruction.** We say the exact same problem using a phrasing the model
  never saw during training. Performance drops to **0.000**.

## The damning comparison

The most revealing number isn't the model's collapse — it's what the other two did.

When we change the *words*, the **template baseline gets *better*, not worse** (0.875,
up from 0.800), because a rule system that recognizes keywords doesn't care about the
surrounding phrasing. The **retrieval baseline** also holds up (0.683). Only the
**learned model** falls apart — because the model learned the *specific sentences*, not
the *idea*.

So the model's 0.900 in-distribution score was largely **phrasing memorization**. It
had learned "this exact kind of sentence maps to that program." It had not learned
"take two numbers and return their sum" as something you can say any number of ways
and still mean.

## The shortcut audit

1. **Suspected cheat: phrasing memorization.**
   **Why it fits:** the model tied training phrasings to code.
   **Control:** held one whole phrasing style out of training, tested on it.
   **Result:** 0.000.
   **Ruled out:** that the model is grounded in the computation.
   **Still open:** is it the wording pattern or the new vocabulary? Need a
   surface-control to separate them.

2. **Suspected cheat: name memorization.**
   **Why it fits:** trained on `a,b`, maybe it hardwired those labels.
   **Control:** retest on `left,right`.
   **Result:** 0.350 — a big but partial drop.
   **Ruled out:** pure name-memorization (it still fails partly, but names aren't the
   whole story).

## The honest takeaway

A model that scores 0.900 on familiar phrasings and 0.000 on a rewording of the same
problem has not generalized to the *problem*. It generalized to the *phrasing*. That's
the difference between "the model works" and "the model works when I say it the way I
said it in training" — and it's the most important lesson of the generalization
chapters.
