# 8. The Smallest Brain

Now the student. Everything so far — the world, the teacher, the judge, the rivals —
exists to ask one question about this thing. So let's meet it.

Meet the model: a small, deliberately plain decoder-only transformer. It's not fancy,
and that's the point. Just like a chemistry lab uses simple glassware so we can see
exactly what's happening, we use a simple, transparent model so we can understand
exactly what it's doing. A 20-layer exotic architecture would be a black box; a clean,
standard transformer is one we can reason about.

## Why the simplest possible model

The temptation when choosing a model is to reach for the newest, most sophisticated
thing — the attention variant that promises to be smarter, the architecture that looks
impressive in a diagram. That instinct is understandable, but it fights the entire
purpose of a controlled experiment. If the model is complex and mysterious, then when
it fails, we cannot tell whether the failure is because of some fundamental limit of
learning, or because of a quirk of our exotic architecture.

So we choose the opposite. The student is a **completely standard, off-the-shelf
decoder-only transformer** — the same basic architecture that powers the big language
models, just scaled way down. Nothing clever, nothing bespoke. This is a deliberate
choice, and the reason is not modesty; it is method. A plain, well-understood model
means that when something unexpected happens, we can attribute it to *learning* rather
than to an architectural mystery. We want the model to be the simplest possible
instrument, so that the experiment — not the gadgetry — is the subject.

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

Each of these is a deliberate choice that we can justify. The context length of 128
tokens, for example, is chosen because a pilot task's prompt-plus-program fits
comfortably within it — long enough to hold a full task, short enough that the model
is not wasting capacity on irrelevant span. The 4 layers and 128-wide hidden
dimension keep it fast to train on the modest hardware available, which matters
enormously: if training takes an hour, we iterate on the *experiment*; if it takes a
day, we wait on the *model*, and the brew slows to a crawl. A small model is a fast
iteration loop, and a fast loop is what lets a scientific investigation move.

## The honest parameter count

A common mistake is to quote just a round "10M parameters." We refuse to hide the
important part. The model has **884,224** parameters, of which only **830,592** are
the actual computation. The other **53,632** are the **embedding** — and the
embedding is often the silent dominant term in a tiny model. If we do not separate them, "0.9M parameters" can mislead: a big fraction might just be storing the
vocabulary, not doing any computation.

So we always report the split: embedding vs. non-embedding.

This matters more than it might seem. At tiny scale, the ratio of vocabulary to
computation is high, which means a naive "M parameters" figure can be dominated by a
table lookup that does no learning at all. Separating the two lets us and the reader
see the *actual* computation the model brings to bear — the part that must do the
learning. It is a small discipline, but it keeps the conversation honest.

## The architecture smoke test

Before we train it for real, we run an **architecture smoke test** — a tiny, fast check
that the model's forward and backward passes work, that the parameter count is what we
expect, and that the initial loss is sensible (roughly the log of the vocabulary, since
a fresh random model's best guess is uniform).

This is the same discipline as the very first smoke test, but one level up: we are not
checking "does the loop run?" anymore, we are checking "does *this model* construct and
train correctly?" A 20-second check here prevents discovering a shape bug hours into a
real run.

The initial loss is a wonderfully informative number. A brand-new model, before it has
learned anything, predicts the next token uniformly, so its loss should be close to the
natural log of the vocabulary size — here, about log(291) ≈ 5.67. When we actually ran
it, the initial loss was **5.84**, reassuringly close. That is what a model that knows
nothing looks like, and it is the baseline every later, lower number is measured
against.

## Why it's small

The book deliberately keeps the pilot model tiny. This is not modesty; it is method. A
small model is fast to train (so we can iterate on the *experiment*, not wait for the
model), transparent (so a failure is a learning-system problem, not an architecture
mystery), and it makes the *boundary* more visible — a small model that fails to
compose tells us something cleaner than a large model that does something partly and
noisily. We scale it up later precisely to test whether capacity matters, but the
baseline has to be small and legible.

## The configuration is a starting point, not a fact

Crucially, none of these numbers are immutable. The exact architecture is an
experimental variable. Every architectural choice requires a reason, and the question
is never "what architectures can we try?" — it is "what scientific decision does this
comparison enable?" For the pilot, the answer is: this size is fast enough and small
enough to be legible, which is what Stage 0–1 needs.

This is a discipline worth holding onto. It is tempting to fixate on the "best"
architecture or the "right" parameter count as if one existed. But in an experiment
where the question is about *learning*, the model is a dial, not a destination. We
choose a configuration because it enables a specific scientific comparison — and we
change it when we want to test whether the answer changes. That is why the pilot model
is small and plain: not because it is the best, but because it is the *clearest*
instrument for the question at hand.
