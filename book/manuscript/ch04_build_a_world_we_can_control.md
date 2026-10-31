# 4. Build a World We Can Control

A model that answers natural-language questions is easy to build and hard to
evaluate. But there is one class of task where the evaluation is not a judgment call
at all: **write a program.** We write a description, the model writes code, and a computer can tell us, to a very high degree
of confidence bounded by the judge and tests, whether that code does what was asked. There
are no opinions about the answer, no ambiguous grading rubric, no "well, it's sort of
correct." Either the program returns the right thing for every test, or it does not.

That one observation is why this whole book rests on the `natural-language → Python
program` task. It gives us something few machine-learning setups have: *objective,
executable, reproducible* evaluation. But the task alone is not enough. Before we can
run any experiment, we need a world the model can live in — a world that is safe, that
is *deterministic*, and that is small enough that we can reason about everything that
happens inside it.

## Why we need a world at all

Imagine hiring someone to write code, but not fully trusting them. We would not hand them the keys to the server. We would give them a sandbox — a walled-off
room where they can work, but where the dangerous tools are simply not present.

That is exactly what we do with the model. It writes Python, and we need to run that
Python safely and deterministically, while deciding precisely what it is *allowed* to
do. The model could, in principle, write a program that reads files, connects to a
network, or deletes things. It has no reason to — but we are not relying on its good
intentions. We build a restricted world where the *disallowed constructs covered by our
validator* are rejected, not where every harmful program is made impossible: the sandbox
rejects the constructs it knows to disallow, and it is a teaching evaluator, not a
hostile-code security boundary.

The deeper reason is that a controlled world makes the *experiment* clean. If the
model's program could do anything — read a file, check the time, generate a random
number — then two runs of the same program could give different answers, and we could
never attribute a failure to "the model didn't learn this" versus "the program did
something nondeterministic." We want the world to be so constrained that **the only
source of variability is the model itself.**

## The principle: whitelist, not blocklist

The naive way to constrain a program is a blacklist: deny `import`, deny `eval`, deny
`open`. This is the instinct most people reach for first. But a blacklist is
fundamentally fragile — there is always some construct we forgot. Python has an
enormous surface area, and attackers (or, in our case, just curious models) find the
gaps. Denying a hundred things is not safety; it is a constant game of catch-up.

The robust way is the opposite: **an allowlist.** We parse the program into its
abstract syntax tree — the structured representation of the code, before it runs — and
walk through every node. If any node type is not *explicitly permitted*, we **reject
the entire program.** There is no "mostly allowed." If the model emits even one
disallowed construct, the whole thing is refused before it ever executes.

The difference is between a list of banned words and a grammar. A banned-word
list can be evaded by creative phrasing. A grammar says: these are the only forms that
exist. Anything outside the grammar is not merely suspect; it is *unparseable in our
world.* That is the philosophy of the sandbox.

This is a central design decision in the apparatus, and it
deserves to be stated plainly: **the sandbox does not try to catch bad programs. It
states upfront what is allowed, and everything else is refused.**

## The capability spec

For the pilot, we whitelist a deliberately small subset of Python — small enough that
we can hold it in our heads, large enough to express real programming:

- literals (integers, floats), variables, assignment, `return`
- arithmetic: `+ - * / // % **`
- comparisons, boolean operators
- `if / elif / else`, `for`, `while`, `break`, `continue`, `pass`
- lists, indexing, slicing, and the list methods `append`, `count`, `index`, `pop`
- a small set of built-ins — eleven in total: `abs, min, max, sum, len, range, int,
  float, round, list, sorted`
- simple `def` functions

This list is a summary; the authoritative whitelist is §5–§6 of
`python_capability_v0_1.md` and `ALLOWED_NODES`/`ALLOWED_BUILTINS` in `src/sandbox/sandbox.py`, which
agree with each other. Everything else is rejected: imports, file I/O, network,
subprocess, `eval`/`exec`, `class`, `try/except`, arbitrary attribute access (beyond
the whitelisted list methods), comprehensions, lambdas. We do not
include these because they are dangerous; we exclude them because they are not needed
for the task we are testing, and because each one we add makes the world bigger and
harder to reason about. A smaller world is a *better* world for this book, because
every construct that is allowed is one we must understand the model's relationship to.

We also version this spec (`python_capability_v0_1`) so that later, when we give the
model *more* Python (see the closing chapter's future-work note), we can point to
exactly what grew. Versioning the
world is what lets us claim, later, that a change in behavior was caused by a change
in the world, and not by something else that drifted.

## Resource and determinism policy

Beyond what is allowed syntactically, we also control *how complex* the program may
be. This is the second half of making the world trustworthy:

- maximum AST depth (24) and node count (200) — a program can only be so complex,
- float-comparison tolerance (because `0.1 + 0.2` is not exactly `0.3`),
- **no randomness, no time, no environment access.**

That last point is the quiet heart of the whole design. A program with the same input
must always produce the same output. If it does not, the experiment is contaminated.
We cannot tell whether a failure means "the model didn't learn this" or "the program
rolled the dice." By making the world deterministic, we eliminate that ambiguity
entirely. The book's every later claim rests on this.

One honesty note on that list: the spec also designs a maximum nesting depth, a hard
execution timeout (a program that loops forever is a failed program), and recursion
protection, but the shipped sandbox enforces none of the three — they exist in the
code only as unused constants, and validation checks AST depth and node count alone.
We did not enforce a runtime timeout or recursion cap, so an allowed program could
still loop or consume memory. That is exactly the resource-use qualification Gate A
carries below: the gate bounds the *shape* of allowed programs, not their resource use.

## The pipeline

```
source -> parse -> AST -> whitelist validation -> compile
        -> restricted execution -> semantic comparison
```

Validation happens on the tree *before* execution, so disallowed code never runs.
Execution uses a stripped set of globals that exposes only the allowed built-ins —
there is no `__import__`, no `open`, no `eval`. The program can only see the tools we
chose to give it.

## An honest caveat

### The whole apparatus, in one picture

![The whole apparatus](figures/fig_apparatus.png)

Here is the full loop: the teacher creates the dataset, the student reads it, the
judge grades the result, and the world encloses it all.

It is important to be clear about what this sandbox is *not*. It is a **teaching and
evaluation** sandbox — deliberately strict about the capability subset, but not a claim
of production-grade adversarial isolation. We are not trying to secure a server against
a hostile attacker; we are trying to run generated code and measure whether it does
what we asked. An attacker with time and motivation could likely find ways around a
small AST allowlist. We state this limitation plainly rather than overstating what the
sandbox guarantees, because the book's credibility depends on honest boundaries, not
on impressive-sounding claims.

## Testing the world

The sandbox is the foundation of trust in every later result. If the sandbox leaked —
allowed something disallowed, or failed to be deterministic — every score in the book
would be suspect. So the very first thing we do is not run any experiment at all. We
**test the world itself.**

We build a conformance suite of 15 cases: three programs that use allowed constructs
and must run (a plain function, a loop, a conditional), plus twelve that must be
rejected — ten disallowed constructs (`import`, `from`-import, `eval`, `class`, `open`,
`__import__`, `try`, conditional expressions, comprehensions, lambdas), a syntax error,
and a program that is not a single function. The suite is
`tests/sandbox/test_sandbox.py`, and it runs with `pytest tests/sandbox/test_sandbox.py`.
A sandbox that only permits things is easy; a sandbox that also *correctly refuses* the
disallowed constructs it knows is the real achievement — and that is what our 15-case
conformance run checks before we trust a single number it produces. (The 15 cases are a
deliberate conformance sample, not an exhaustive proof that every possible disallowed
construct is covered; we say "passed its conformance cases," not "verified everything," and
the validator's scope is the constructs it enumerates.)

This is the first instance of a discipline the book will return to again and again
(and which we will see was worth it, painfully, in Chapter 10): **before we use a tool to measure something, we verify that the tool measures what we think it does.** Here, the
tool is the world, and we refuse to run a single experiment until it passes its own
examination.

## Two gates, not one

![The two gates](figures/fig_two_gates.png)

Neither gate lives inside the model. Gate B sits on the way in, Gate A on the way out.

Everything above describes what the model is *allowed to produce*. But there is a
second, quieter question: what is the model *ever asked* to do? These are not the same
thing, and the difference is worth making sharp, because it is the difference between
"the model cannot escape" and "the model was never put in the position to."

A language model has no *built-in* notion of refusal. It is not, by default, a system
that decides whether a request is in scope; it is a next-token predictor. Hand a request
to this model outside its designed job and it does not politely decline — it simply
keeps predicting tokens and produces whatever the weights trend toward, often a
confident near-program or garbage. (Models *can* be trained to refuse, but this one was
not, so refusal here is not a property to assume.) So "it only does its one job" can
never be a property of the model's own intent here. It has to be a property of the
wiring around it.

That gives us **two independent gates**, and this chapter (so far) has really only
built one of them:

**Gate A — the output gate (the sandbox).** Already described above: the AST allowlist
rejects any generated program that uses a construct outside the whitelist, before it
runs. This means that if the model *tries* to emit `import os` or `eval()`, the command
is refused. Gate A is a hard gate on the *syntax* of what the model
*produces* — it is deterministic for the constructs it covers. Two
qualifications: it bounds the *shape* of allowed programs, not their resource use or
their adversarial resistance (an allowed program could still, in principle, loop or
consume memory), and it is not production-grade isolation. As a scoping mechanism for
this experiment it is sufficient; as a security sandbox it would not be. Anyone who wants
to try the execution steps described later should do so in a disposable, unprivileged,
resource-limited environment with no sensitive files or network access.

**Gate B — the input gate (the request validator).** This is the gate we build for the
other half. It sits *in front of* the model and decides, from the incoming
natural-language request alone, whether that request is one the model was designed
for. If not, the request is declined before the model is ever consulted.

Gate B works on the same principle as the sandbox: a **recognizer, not a rejector of
the exceptions**. It holds the set of designed template-family shapes (the exact
phrase skeletons the teacher renders) and the designed operation vocabulary. A request
is in scope only if it fits one of those shapes *and* names a known operation —
otherwise it is refused. Just as the sandbox says "these are the only forms of program
that exist," Gate B says "these are the only forms of request that exist."

**One clarification on how we used it.** Gate B was built late in the investigation,
after the diversity, memorization and surface experiments (Chapters 13–15) and the
human-written evaluations. Those evaluations
ran the model **directly, without Gate B in front of it** — precisely so that a
low score could be attributed unambiguously to the *model*, not to a request filter
that had quietly declined the caller. For the surface and human tests, the model saw
the reworded / human-phrased request and failed on its own. Had Gate B been in front,
it might well have rejected those out-of-scope phrasings (that is its job) and the
failure would have been the filter's, not the model's. So we state it clearly: the
surface and human-written failures are model failures, not Gate-B rejections. Gate B
enforces scope; it does not confound those measurements.

Why do we need both? Because each covers a failure the other cannot:

- **Gate A alone** would let the model be *asked* for anything — including a task it
  was never trained for — and only then catch the malformed result. The model would
  churn, and our whole experiment would trust that an out-of-scope query produced a
  rejected program rather than a plausible-looking-but-wrong one.
- **Gate B alone** would let the model *produce* anything within an in-scope request,
  including a program that escapes its world, because nothing would constrain the
  output.

Only together do they close the loop: Gate B ensures the model is never *asked* for
something outside its job, and Gate A rejects programs using constructs outside its
allowed syntax. Together that scopes the model to a single accepted request shape and a
single accepted program shape — a *scoping* guarantee, not proof of semantic correctness,
and not a claim that the model can never do anything unintended beyond those two scopes.

There is a deep parallel here with the book's central thesis. The model is the
instrument; the experiment is the subject. In the same way, the *boundaries* are never
the model — they are always the apparatus: the sandbox on the way out, the validator
on the way in. A model that "only does its one job" is confined by its wiring, not
by itself. That is worth stating plainly, because it is the mistake people make when
they imagine a well-behaved model as one that simply chooses to behave.

### How this maps to production systems

Our two gates are not an esoteric lab device; they are the same two ideas that real
systems use, under different names. It is worth mapping them, so the book's abstract
apparatus connects to what people actually deploy.

| Our gate | Production analogue | What it does (property) | What it does NOT establish |
|---|---|---|---|
| **Gate B** (input) | **Structured-input schema** | Declares the request's allowed shape (JSON schema); a request outside it is invalid by construction — a deterministic rule, not a model's decision | *Shape* compliance only. Schema validity is not correctness, safety, or authorization |
| **Gate B** (input) | **Function/tool signatures** | Only registered functions with typed signatures can be called; off-scope actions aren't callable | Permission for every argument or action — a declared function can still be called with a harmful argument |
| **Gate B** (input) | **Learned safety classifier (input)** | A separate learned model scores the prompt and a block action is applied to the score | Perfect semantic classification — the classifier is itself imperfect and can misclassify |
| **Gate A** (output) | **Schema-constrained decoding** | Decoder only emits tokens that keep output inside the declared structure | Correctness of values or authorization — it guarantees *structure*, not semantic correctness |
| **Gate A** (output) | **Provider JSON mode** | The provider's documented behavior for ensuring the completion is valid JSON, with incomplete-output / edge-case handling needed | Arbitrary schema adherence or semantic correctness — a provider's JSON mode ensures JSON validity (including the incomplete-output caveat), not adherence to a specific schema or correctness of values |
| **Gate A** (output) | **Prompt-only formatting request** | The model is only *asked* to format a certain way; there is no formal syntax enforcement | Valid JSON or schema compliance — a prompt saying "please use JSON" is not an API's JSON mode |
| **Gate A** (output) | **Output filter / sandbox** | A post-hoc check (or a walled-off execution environment) rejects or neutralizes what slipped through | Correctness of the content — the check is only as good as its rules |

The thread running through the "What it does NOT establish" column is the book's point:
every reliable enforcement mechanism is **external and scoped**, and none of them is
"the model chose to behave." Even a frontier model that appears to refuse is doing so
because RLHF shaped it to *tend* toward refusal — which is a soft, jailbreakable
behavior, not a bound. The dependable version of "it only does what it was designed
for" is the wiring we build around it, exactly as our sandbox and our validator are.

Three things follow. First, we deliberately do **not** assign "Low / Medium / High"
residual-risk ratings to the rows above: we have no threat model or measurement to
justify a quantitative ranking, so a color-coded risk column would be unsupported
assertion. Instead each row names *which* failure mode remains open. Second, the
distinction between a *prompt-only* request and an API's *JSON mode* is a real one:
"please use JSON" is a request the model tends to follow, whereas a provider's JSON mode
is a documented behavior with its own validity guarantee and its own incomplete-output
edge case. Neither one is "the model is forced to comply with a schema" — that is what
schema-constrained decoding does. Third, even schema-constrained decoding bounds the
*shape* of what gets through; it does not make the content correct or safe. So the
reliable layer is external and it is a *scoping* guarantee, not a *judgment* guarantee.
There is no mechanism in the table that gives semantic reliability.
