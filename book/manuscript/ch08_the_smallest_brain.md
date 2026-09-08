# 8. The Smallest Brain

Now the student. Everything so far — the world, the teacher, the judge, the rivals —
exists to ask one question about this thing. So let's meet it.

Meet the model: a small, deliberately plain decoder-only transformer. It's not fancy,
and that's the point. Just like a chemistry lab uses simple glassware so you can see
exactly what's happening, we use a simple, transparent model so we can understand
exactly what it's doing. A 20-layer exotic architecture would be a black box; a clean,
standard transformer is one we can reason about.

## What it is

The student is a deliberately simple, transparent **decoder-only transformer**. The
goal is not novelty; the goal is that we can understand exactly what it is doing. A
20-layer exotic architecture would be a black box; a clean, standard transformer is
one we can reason about.

For the pilot, the configuration is small and honest:

- vocabulary: ~291 tokens (a compact BPE trained on the task corpus),
- hidden dimension: 128,
- layers: 4,
- attention heads: 4,
- context length: 128,
- GELU activation, Pre-LayerNorm, AdamW optimizer.

## The honest parameter count

A common mistake is to quote just a round "10M parameters." We refuse to hide the
important part. The model has **884,224** parameters, of which only **830,592** are
the actual computation. The other **53,632** are the **embedding** — and the
embedding is often the silent dominant term in a tiny model. If you don't separate
them, "0.9M parameters" can mislead: a big fraction might just be storing the
vocabulary, not doing any computation.

So we always report the split: embedding vs. non-embedding.

## The architecture smoke test

Before we train it for real, we run an **architecture smoke test** — a tiny, fast check
that the model's forward and backward passes work, that the parameter count is what we
expect, and that the initial loss is sensible (roughly the log of the vocabulary, since
a fresh random model's best guess is uniform).

This is the same discipline as the very first smoke test, but one level up: we are not
checking "does the loop run?" anymore, we are checking "does *this model* construct and
train correctly?" A 20-second check here prevents discovering a shape bug hours into a
real run.

## Why it's small

The book deliberately keeps the pilot model tiny. This is not modesty; it is method. A
small model is fast to train (so we can iterate on the *experiment*, not wait for the
model), transparent (so a failure is a learning-system problem, not an architecture
mystery), and it makes the *boundary* more visible — a small model that fails to
compose tells us something cleaner than a large model that does something

partly and noisily. We scale it up later precisely to test whether capacity matters,
but the baseline has to be small and legible.

## The configuration is a starting point, not a fact

Crucially, none of these numbers are immutable. The exact architecture is an
experimental variable. Every architectural choice requires a reason, and the question
is never "what architectures can we try?" — it is "what scientific decision does this
comparison enable?" For the pilot, the answer is: this size is fast enough and small
enough to be legible, which is what Stage 0–1 needs.
