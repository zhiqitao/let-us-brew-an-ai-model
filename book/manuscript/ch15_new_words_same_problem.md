# 15. New Words, Same Problem

The pilot told us the task was too easy; the composition experiment told us the
model cannot combine what it knows. But there is a more subtle question in between,
and it is arguably the one that matters most for whether we can trust any of this.

**When the model does well, is it doing the computation, or just recognizing the
wording?**

A model that maps the *words* "sum" and "a and b" to `a + b` is not necessarily doing
arithmetic. It might be doing a far dumber thing: associating the *exact phrasing* it
saw in training with the code that followed it. If that is what is happening, then
the capability is not in the model's head as "addition" — it is a fragile surface
reflex that will break the moment the phrasing changes.

To find out, we run the **surface-generalization** experiment (Level 3). The insight
is that if you change something that *should not* change the computation — the
variable names, or the words used to express the same instruction — and the model
fails, then the model never learned the computation. It learned the phrasing.

## The setup

We trained the model on pilot arithmetic primitives, but with a twist: we gave it only
**letter identifiers** (`a`, `b`) and only **some** of the wording template families.
Then we re-expressed the *identical* task three different ways and tested whether the
model's capability survived.

## The result

| Test | **MODEL** | TEMPLATE | RETRIEVAL |
|------|-----------|----------|-----------|
| In-distribution | **0.900** | 0.800 | 1.000 |
| New identifiers (`a,b` → `left,right`) | **0.350** | 0.800 | 0.683 |
| **Held-out wording** (a paraphrase family never seen) | **0.000** | 0.875 | 0.125 |

Watch what happens as we change only the *surface*, not the computation.

- **Same computation, different variable names.** The model was trained with `a` and
  `b`. We ask it the same question but with `left` and `right` — the *identical*
  operation. Performance drops from **0.900 to 0.350**.

- **Same computation, different wording.** We rephrase the instruction using a
  template family the model never saw during training. It is the exact same problem,
  just said differently. Performance drops to **0.000**.

## What this means

This is the moment the model's "capability" is revealed to be shallow. The model is
not grounded in the meaning — it is **anchored to the surface form.**

The most damning detail is the comparison against the baselines. When we change the
*words*, the **template baseline gets *better*, not worse** (0.875, up from 0.800),
because a rule system that recognizes keywords doesn't care about the surrounding
wording. The **retrieval baseline** also holds up better (0.683). Only the **learned
model** collapses — because the model learned the *specific phrasing*, not the
*concept*.

So the model's in-distribution success (0.900) was largely **phrasing memorization**.
It had learned that *this exact kind of sentence maps to that program*. It had not
learned "take two numbers and return their sum" as an abstract operation that
survives being said any number of ways.

## The shortcut audit

1. **Suspected shortcut: wording / phrasing memorization.**
   **Why it could explain it:** the model associated training phrasing with code.
   **Control:** held out a whole template family from training; tested on it.
   **Result:** 0.000.
   **What it rules out:** the claim that the model is grounded in the computation.
   **What remains:** whether the failure is *specifically* the wording pattern, or the
   new vocabulary/identifiers (a surface-control experiment separates these).

2. **Suspected shortcut: identifier memorization.**
   **Why it could explain it:** trained on `a,b`, maybe it hardwired those names.
   **Control:** retest with `left,right`.
   **Result:** 0.350 — a big but partial drop.
   **What it rules out:** pure identifier-memorization (still fails partly, so it's
   tied to the letters too, but not the whole story).

## The honest takeaway

A model that scores 0.900 in-distribution and 0.000 on a rephrasing of the same
problem has not generalized to the problem. It has generalized to the phrasing. This
is the difference between "the model works" and "the model works when I say it the
way I said it in training" — and it is the single most important lesson of the
generalization chapters.
