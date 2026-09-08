# 4. Build a World We Can Control

The model will produce Python. Before we trust anything it produces, we need a way to
run that Python safely and *deterministically* — and to decide, precisely, what is
allowed. This is the **sandbox**: the "world" in which the model operates.

## The principle: whitelist, not blocklist

The naive way to constrain a program is a blocklist: deny `import`, deny `eval`, deny
`open`. Blocklists are fragile — there is always some construct you forgot. The
robust way is the opposite: **an allowlist**. We parse the program to an abstract
syntax tree, and if any node type is not *explicitly permitted*, we **reject the whole
program.**

This is the key design decision. The sandbox does not try to catch "bad" programs; it
states upfront exactly what is allowed, and everything else is refused. If the model
emits even one disallowed construct — an `import`, a `class`, a `try`, a
comprehension, an `eval` — the program is rejected before it ever runs.

## What's allowed (the capability spec)

For the pilot we whitelist a deliberately small subset of Python:

- literals (integers, floats), variables, assignment, `return`
- arithmetic: `+ - * / // % **`
- comparisons, boolean operators
- `if / elif / else`, `for`, `while`, `break`, `continue`, `pass`
- lists, indexing, slicing
- a small set of built-ins: `abs, min, max, sum, len, range, int, float, round`
- simple `def` functions

Everything else is rejected: imports, file I/O, network, subprocess, `eval`/`exec`,
`class`, `try/except`, arbitrary attribute access, comprehensions, lambdas.

The crucial point is that the model is *only ever* allowed to emit this subset. This
is the controlled world, and the capability spec is versioned so we can track how it
grows across the book.

## Resource and determinism policy

Beyond what's allowed syntactically, we also control *how* the program may run:

- maximum AST depth and program length,
- maximum nesting,
- a hard execution timeout,
- recursion protection,
- float-comparison tolerance,
- **no randomness, no time, no environment access** — the world is deterministic.

A program with the same input must always produce the same output. That is what makes
the experiment clean.

## The pipeline

```
source -> parse -> AST -> whitelist validation -> compile -> restricted execution
        -> semantic comparison
```

Validation happens on the tree *before* execution, so disallowed code never runs.
Execution uses a stripped set of globals that exposes only the allowed built-ins.

## An honest caveat

This sandbox is a **teaching and evaluation** sandbox. It is deliberately strict about
the capability subset, but it is not a claim of production-grade adversarial
isolation. The distinction matters: we are not trying to secure a server against a
hostile attacker; we are trying to run generated code and measure whether it does what
we asked. The book states this limitation clearly rather than overstating what the
sandbox guarantees.

## Why this matters

The sandbox is the foundation of trust in every later result. If the sandbox leaked —
allowed something disallowed, or failed to be deterministic — every score in the book
would be suspect. That is why we test it so thoroughly, and why the very first thing
we verify is that it correctly **rejects** the constructs it must reject: imports,
`eval`, classes, `try`, comprehensions, lambdas. A sandbox that only permits is easy;
a sandbox that also correctly refuses is the real achievement.
