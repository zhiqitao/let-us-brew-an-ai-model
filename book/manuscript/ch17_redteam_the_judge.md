# 17. Red-Team the Judge

We built a judge and argued it is the instrument we stake the book on. Chapter 6
showed how we test it (mutation testing) and that it caught a bug. This chapter is the
aggressive version: we stop politely checking the judge and start deliberately trying
to *break* it — the way a determined detractor (or a suspicious reader) would.

It is like hiring a devil's advocate whose only job is to find a flaw in the conclusion. We want to know how confident we can be in any number our judge produces —
and the only way to find out is to attack it.

There is a reason to be particularly aggressive here, and it goes to the heart of the
book. Our whole method is built on trusting measurements: we claim the model is
surface-tied, non-compositional, that it forgets under sequential training. Every one
of those claims passes through the judge. So if the judge is broken in even one
respect, every conclusion in the book could be subtly wrong. Red-teaming the judge is
not a single chapter's task; it is the standing obligation of the whole experiment. And
it is an *unbounded* one — we can never prove the judge is perfect, only that we have
tried hard to break it and failed.

## The attack surface

A judge that executes generated code is attacked through the code it is given. We
enumerate the ways a candidate could slip through:

- **hardcoded outputs** — a program that ignores the input and returns a fixed answer
  that happens to match one test,
- **mutation variants** — operator flips, wrong variables, off-by-one, missing
  edge-cases (the mutation suite from Chapter 6),
- **weak test cases** — if the hidden tests are too few or too narrow, a wrong program
  can pass,
- **boundary failures** — behavior at zero, negatives, or large values that the tests
  don't probe,
- **resource abuse** — programs that loop forever or consume too much,
- **unsupported syntax** — smuggling in a construct the sandbox should reject,
- **ambiguous specifications** — a prompt the model could reasonably read two ways,
- **evaluator inconsistencies** — the same program scored differently in two runs.

This list is a map of the ways the judge could be fooled — and each entry is a place
we must probe. The point of enumerating the surface is that skepticism is only useful
when it is specific. "The judge might be wrong" is not actionable. "The judge might
let a hardcoded-output program pass if the tests are too narrow" is a concrete thing
we can check.

## What we found

The mutation suite is the sharpest tool here. We generated deliberately-broken
variants of the reference solution and ran them through the judge against that
operation's hidden tests, then measured how many the tests *kill*. The measured
result, across all 16 operations, is honest and **partial**:

- **35 mutants generated, 29 killed, 6 survived** — an overall kill rate of **0.829**.
- **Positive control passed:** the correct reference program was *accepted* by the
  judge for every operation. This rules out the failure mode of a
  reject-everything evaluator — it genuinely distinguishes correct programs from most
  broken ones.
- **Six mutants survived**: `max_of` (`>`→`>=`), `min_of` (`<`→`<=`), `abs_of`
  (`<`→`<=`), `cond_abs_max` (`>`→`>=`), `sum_of_abs` (`<`→`<=`), and `max_add`
  (`>`→`>=`).

A useful way to think about mutation testing is that it measures the *discriminating
power* of the test suite. A suite that passes for a correct program and fails for an
incorrect one is a good suite. A suite that passes for both is not testing anything.

### Classifying the six survivors

At first glance six survivors look like six test-suite defects. But every one of them is
the same kind of change: a **strict comparison flipped to a non-strict one** (`>`→`>=` or
`<`→`<=`) in a function that returns a max/min/absolute-value. Over the integer domain
these are **semantically equivalent** to the reference. Be careful with the wording here:
the predicates differ — `a >= b` is True and `a > b` is False when `a == b` — but the
*enclosing max/min function* returns the same value in both cases, because at the tie the
equal branch and the (now-reached) outer branch yield the same number. We built a small
equivalence check and confirmed it matched on the bounded integer domain we enumerated
(and, for these tie-only mutants, a short case analysis establishes the equivalence over
the integer domain: the operator differs only at equality, and both branches return equal
values there). So they are *not* six missed defects; they are six tie-breaking
equivalences.

This is the important nuance worth spelling out: *a surviving **equivalent**
mutant is not a missed error.* The mutation score therefore does **not** mean "the test
suite has six confirmed defects." It means:

> The evaluator rejected 29 of 35 generated mutants and accepted all 16 reference
> controls. The six survivors are all strict→non-strict tie-breaking mutations that are
> equivalent to the reference over the integer domain, so they do not quantify test-suite
> defects. They do show the tests do not *distinguish* a `>` from a `>=` at a tie — but
> since the two behave identically here, that is not a correctness gap.

So the honest conclusion is to report **three distinct measurements**, each with its own
denominator:

- **Raw rejection fraction:** 29 / 35 = **0.829** — the share of all 35 generated mutants
  that the suite rejected.
- **Equivalence-adjusted mutation score:** 29 / (35 − 6) = 29 / 29 = **1.000** — the share
  of *non-equivalent* mutants rejected, after excluding the six tie-breaking equivalents
  from the denominator. (A survivor that is equivalent is not a test-suite defect, so it is
  excluded from the adjusted denominator rather than merely relabeled in plain prose.)
- **Reference-control acceptance:** 16 / 16 = **1.000** — the suite accepted every correct
  reference program.

We report these three separately. The raw score is *not* the same as the adjusted score:
0.829 and 1.000 measure different things. Neither is a proportion of "all possible error
classes covered," and neither is a proof that the test suite is complete. (The reference
controls rule out reject-everything behavior on those 16 correct programs; they do not
prove the tests catch every possible false-negative for *other* alternative correct
programs.)

And the judge's honesty was validated the hard way: it reported the model at 0.000 on
our very first evaluation, and that was a *judge bug*, not a model failure. Once we
fixed the judge, the model's true 0.897 emerged. A judge that can be wrong — and we
proved ours was — must be red-teamed before its numbers are trusted.

## A concrete example: the judge learns a new test

To make "test the tester" a reader skill rather than a slogan, here is a small
constructed example of how a weak test can let a wrong program survive, and how a
distinguishing test catches it. (This is a teaching illustration of the principle, **not**
a record of a real finding from the experiment — the measured mutation report in the
section above is the actual data.)

Suppose the task is to compute `a + b`, and the reference is:

```
def solve(a, b):
    return a + b
```

Now consider a mutant that flips the operator to subtraction:

```
def solve(a, b):
    return a - b
```

A single weak test on `(a=0, b=0)` does **not** catch it: for `(0, 0)`, both `a + b` and
`a - b` return `0`, so the mutant survives and the suite looks green. But a
distinguishing test on `(a=2, b=3)` — where the reference returns `5` and the mutant
returns `-1` — catches it. The point is that a test must be *discriminating*: it has to
separate the correct program from the specific wrong ones, not merely produce a pass
for whatever got written. That is exactly what the measured mutation suite is designed
to probe, and why its 0.829 raw rejection fraction (29/35, with the six survivors all
tie-equivalent) is a real, quantified measure of the suite's discriminating power rather
than a claim that it is exhaustive.

## The honest framing

Red-teaming the judge is not a formality; it is the difference between "we ran a
number" and "we know the number means something." The specific lessons:

- **Strengthen tests until wrong programs fail.** The mutation score is the measure.
  Our raw rejection fraction is 29/35 = 0.829; the equivalence-adjusted score — after
  excluding the six tie-equivalent survivors from the denominator — is 29/29 = 1.000.
  Those are two different numbers, and we report them separately: 0.829 is what the
  suite *caught* of everything we broke, and 1.000 is the adjusted share after
  accounting for survivors that were not actually bugs. What the score does *not* do is
  prove the tests discriminate every possible error class; it quantifies the ones we
  chose to generate.
- **Trust the judge less than the tests.** The judge is a pipeline; the *hidden tests*
  are what actually catch errors. We do not claim the tests distinguish every
  conceivable wrong program — the reference controls only prove they accept all 16
  correct programs and catch the other 29 non-equivalent mutants. An *alternative*
  correct program that differs from the reference in some unseen way is a different
  question we did not test.
- **Attack our own instrument deliberately.** The adversarial habit — "how could this
  number be wrong?" — is what keeps the whole experiment honest.

A judge that has been red-teamed is one we can believe. A judge we've only used is one
we cannot.

And there is a final lesson that reaches beyond judges. Every measurement instrument —
in science, in engineering, in daily life — can fail in ways its designer did not
anticipate. The discipline of attacking our own apparatus is the same discipline that
makes a result worth believing. It is not paranoia; it is the price of a claim we can
stand behind. The book's whole credibility rests on having paid it, and having
recorded that we paid it, rather than merely asserting that we are trustworthy.
