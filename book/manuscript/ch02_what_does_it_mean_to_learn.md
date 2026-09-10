# 2. What Does It Mean to Learn?

We're going to use a word a lot in this book: *learned*. Before we do, we have to be
honest about what it means — because "the model learned to add" is a sentence people
say all the time, and it's usually hiding a big assumption.

## A simple way to think about it

Imagine a child who aces a worksheet of addition problems. Every problem is like
"4 + 3 = ?" and the child gets them all right. We'd be tempted to say "the child can
add."

But there are two very different ways to get that perfect score:

1. The child *understands addition* — show them "37 + 58" and they solve it, because
   they know how to add any two numbers.
2. The child *memorized the exact answers* — they've seen these exact problems before
   and just remember that "4 + 3 = 7," but hand them a problem they've never seen and
   they freeze.

A perfect worksheet grade can't tell these two apart. **The worksheet is a bad test.**
Only a *new* problem can.

This is the entire premise of the book in one image. Our model gets a perfect-ish
worksheet sometimes. The question is always: would it pass the *new* problem?

## What "learned" means here

So we define it narrowly and honestly. A model shows **learned capability** when, to
the degree the evidence supports:

1. **It gets better as it trains** — the loss falls, and the thing we care about
   reliably improves.
2. **It works on examples it never saw** — not just the ones in training.
3. **It survives harmless changes** — different variable names, different wording, a
   different way of saying the same instruction.
4. **It can combine things it knows** — put two learned pieces together in a new
   arrangement, not just repeat an arrangement it already saw.
5. **Simpler explanations have been ruled out.** The mundane alternatives —
   memorization, copying a near-duplicate, a template, a leaked test, a buggy
   evaluator — must be tested and rejected.

We are deliberately **not** asking whether the model "really understands" in a
philosophical sense. We're asking narrower, answerable things: does it generalize? to
what? and could a dumber mechanism explain the result?

## The four levels of generalization

![The capability ladder](figures/fig_ladder.png)

The ladder makes the four questions explicit. Each rung asks us to trust a result
a little more; we never collapse them into a single number.

This is the book's organizing idea. It is a ladder of how much we should
trust a result — from "probably just remembered" to "genuinely combined."

**Level 1 — Memorization.** The model reproduces something it saw in training: an exact
example, an exact constant, a familiar phrase, a near-duplicate. *Question: could this
just be remembering?*

**Level 2 — Same task, new examples.** The model works on a new instance of the same
kind of problem. *Question: does it work on problems it hasn't seen before?*

**Level 3 — Same problem, different surface.** The computation is identical, but the
*outer layer* changes: new numbers, new variable names, reworded instruction,
harmless distractors. *Question: does it survive changes that shouldn't matter?*

**Level 4 — New combination.** The model must combine pieces it knows into something
that never appeared in training. It learned A, B, and C separately — can it do A
*sandwiched inside* B, or A followed by C? *Question: can it put things together, or
only repeat what it already saw?*

**A rule we'll follow strictly:** never mash these four into one number. A model that
scores 90% on familiar problems and 0% on a reworded version has not "generalized" —
it memorized the phrasing. One number would hide exactly the thing we care about.

## The recurring question: "how did it cheat?"

Because we refuse to trust a single score, every experiment asks the same skeptical
question:

> **How could the model have gotten this without learning what we think it learned?**

The usual suspects are always on the table: memorized templates, memorized constants,
memorized name patterns, wording quirks, unbalanced data, train/test leakage,
near-duplicates, retrieval, a weak evaluator, hardcoded answers, hidden-test leakage.

Every major experiment therefore ends with a **shortcut audit**, six steps: (1) the
suspected cheat, (2) why it could explain the result, (3) a control test, (4) what the
control found, (5) what that rules out, and (6) what's still unresolved.

That audit — not the headline number — is the book's signature. It's the difference
between "the model works" and "we know why the model works."
