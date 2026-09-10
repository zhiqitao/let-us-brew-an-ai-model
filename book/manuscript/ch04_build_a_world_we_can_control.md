# 4. Build a World We Can Control

A model that answers natural-language questions is easy to build and hard to
evaluate. But there is one class of task where the evaluation is not a judgment call
at all: **write a program.** We write a description, the model writes code, and a computer can tell us, with certainty, whether that code does what was asked. There
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
intentions. We are building a world where those actions are *impossible*, not just
discouraged.

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

This is the single most important design decision in the whole apparatus, and it
deserves to be stated plainly: **the sandbox does not try to catch bad programs. It
states upfront what is allowed, and everything else is refused.**

## The capability spec

For the pilot, we whitelist a deliberately small subset of Python — small enough that
we can hold it in our heads, large enough to express real programming:

- literals (integers, floats), variables, assignment, `return`
- arithmetic: `+ - * / // % **`
- comparisons, boolean operators
- `if / elif / else`, `for`, `while`, `break`, `continue`, `pass`
- lists, indexing, slicing
- a small set of built-ins: `abs, min, max, sum, len, range, int, float, round`
- simple `def` functions

Everything else is rejected: imports, file I/O, network, subprocess, `eval`/`exec`,
`class`, `try/except`, arbitrary attribute access, comprehensions, lambdas. We do not
include these because they are dangerous; we exclude them because they are not needed
for the task we are testing, and because each one we add makes the world bigger and
harder to reason about. A smaller world is a *better* world for this book, because
every construct that is allowed is one we must understand the model's relationship to.

We also version this spec (`python_capability_v0_1`) so that later, when we give the
model *more* Python (Chapter 18), we can point to exactly what grew. Versioning the
world is what lets us claim, later, that a change in behavior was caused by a change
in the world, and not by something else that drifted.

## Resource and determinism policy

Beyond what is allowed syntactically, we also control *how* the program may run. This
is the second half of making the world trustworthy:

- maximum AST depth and node count (a program can only be so complex),
- maximum nesting,
- a hard execution timeout (a program that loops forever is a failed program),
- recursion protection,
- float-comparison tolerance (because `0.1 + 0.2` is not exactly `0.3`),
- **no randomness, no time, no environment access.**

That last point is the quiet heart of the whole design. A program with the same input
must always produce the same output. If it does not, the experiment is contaminated.
We cannot tell whether a failure means "the model didn't learn this" or "the program
rolled the dice." By making the world deterministic, we eliminate that ambiguity
entirely. The book's every later claim rests on this.

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

We build a conformance suite of 31 cases: programs that use each allowed construct and
must pass, plus programs that use each disallowed construct (`import`, `eval`, `class`,
`try`, comprehensions, lambdas, arbitrary attribute access) and must all be rejected.
A sandbox that only permits things is easy; a sandbox that also *correctly refuses*
everything outside its grammar is the real achievement — and that is what we verify
before we trust a single number it produces.

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

A language model has no notion of refusal. It is not a system that decides whether a
request is in scope; it is a next-token predictor. Hand it a request outside its
designed job and it does not politely decline — it simply keeps predicting tokens and
produces whatever the weights trend toward, often a confident near-program or
garbage. So "it only does its one job" can never be a property of the model's own
intent. It has to be a property of the wiring around it.

That gives us **two independent gates**, and this chapter (so far) has really only
built one of them:

**Gate A — the output gate (the sandbox).** Already described above: the AST allowlist
rejects any generated program that uses a construct outside the whitelist, before it
runs. This guarantees that even if the model *tries* to emit `import os` or `eval()`,
the program is refused. Gate A is airtight on what the model *produces*.

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

Why do we need both? Because each covers a failure the other cannot:

- **Gate A alone** would let the model be *asked* for anything — including a task it
  was never trained for — and only then catch the malformed result. The model would
  churn, and our whole experiment would trust that an out-of-scope query produced a
  rejected program rather than a plausible-looking-but-wrong one.
- **Gate B alone** would let the model *produce* anything within an in-scope request,
  including a program that escapes its world, because nothing would constrain the
  output.

Only together do they close the loop: Gate B ensures the model is never *asked* for
something outside its job, and Gate A ensures it can never *produce* something outside
its world. That is the only way to make "this model does exactly one thing" a true
statement, rather than an optimistic description.

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

| Our gate | Production analogue | How it works | Soft or hard? |
|---|---|---|---|
| **Gate B** (input) | **Input classifier / guardrail** | A separate model or ruleset scores the incoming prompt and blocks disallowed categories *before* the main model sees it (e.g. Llama Guard, NeMo guardrails). | **Hard** — a different mechanism in front, not the model deciding |
| **Gate B** (input) | **Structured-input schema** | The API declares the request's allowed shape (JSON schema); a request outside it is invalid by construction. | **Hard** — rejected at the boundary |
| **Gate B** (input) | **Function/tool signatures** | The model can only call registered functions with typed signatures; off-scope actions simply aren't callable. | **Hard** |
| **Gate A** (output) | **Constrained decoding / JSON mode** | The decoder only ever emits tokens that keep the output inside the declared structure, so the model physically cannot produce an unparseable or off-schema completion. | **Hard** — enforced by the decoder, not the model |
| **Gate A** (output) | **Output filter / sandbox** | A post-hoc check (or a walled-off execution environment) rejects or neutralizes anything that slipped through. | **Hard** |

The thread running through the right-hand column is the book's point: every reliable
enforcement mechanism is **hard and external**, and none of them is "the model chose
to behave." Even a frontier model that appears to refuse is doing so because RLHF
shaped it to *tend* toward refusal — which is a soft, jailbreakable behavior, not a
bound. The dependable version of "it only does what it was designed for" is the wiring
we build around it, exactly as our sandbox and our validator are.
