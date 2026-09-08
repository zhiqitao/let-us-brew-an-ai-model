# 17. Red-Team the Judge

We built a judge and I argued it is the instrument we stake the book on. Chapter 6
showed how we test it (mutation testing) and that it caught a bug. This chapter is the
aggressive version: we stop politely checking the judge and start deliberately
attacking it, the way a determined adversary (or a suspicious reader) would.

The question is the one that hangs over the whole book:

> **How much confidence should we place in a number produced by our judge?**

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

## What we found

The mutation suite is the sharpest tool here. By generating deliberately-broken
variants of the reference solution and checking that the hidden tests catch them, we
measured how discriminating the tests really are. If an obviously-wrong mutant — say
`+` changed to `-` — passes our tests, the tests are too weak and must be strengthened
until important mutant classes are reliably detected.

And the judge's honesty was validated the hard way: it reported the model at 0.000 on
our very first evaluation, and that was a *judge bug*, not a model failure. Once we
fixed the judge, the model's true 0.897 emerged. A judge that can be wrong — and we
proved ours was — must be red-teamed before its numbers are trusted.

## The honest framing

Red-teaming the judge is not a formality; it is the difference between "we ran a
number" and "we know the number means something." The specific lessons:

- **Strengthen tests until wrong programs fail.** The mutation score is the measure.
- **Trust the judge less than the tests.** The judge is a pipeline; the *hidden tests*
  are what actually catch errors, so they must be numerous and edge-case-complete.
- **Attack your own instrument deliberately.** The adversarial habit — "how could this
  number be wrong?" — is what keeps the whole experiment honest.

A judge that has been red-teamed is one we can believe. A judge we've only used is
one we cannot.
