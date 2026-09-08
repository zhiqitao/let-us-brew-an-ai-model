# 16. Same Pieces, New Combination

This is the experiment this book was always heading toward.

Everything so far measured whether the model learned a *single* operation. It did —
in-distribution, reliably, ~90% of the time. But learning one operation is not the
same as being able to **combine** operations you know into something you have never
seen. That combination is the heart of programming, and arguably of "capability"
itself. A model that can add and can take absolute values but cannot return the sum
of the absolute values of two numbers does not yet have compositional capability —
it has two separate, unrelated reflexes.

So we constructed the experiment that isolates that exact ability.

## The compositional split

We trained the model on **primitives only** — `add`, `sub`, `mul`, `max_of`,
`min_of`, `abs_of`, `list_sum`, `list_len`, `first_element`, and one composite —
1,400 tasks in total. The model saw no composite operation of any kind.

Then we built a **hold-out set of composite operations**, each of which composes two
of those primitives but never appeared during training:

| composite | primitives it composes |
|-----------|------------------------|
| `abs_add` | `abs` then `add` |
| `sub_abs` | `sub` then `abs` |
| `sum_of_abs` | `abs` over a list sum |
| `max_add` | `max(add, sub)` |
| `double_first` | index then `mul` |
| `len_minus_one` | `len` then `sub` |

Crucially, the model *knew every primitive involved* — it scored ~90% on each of
them. The only new thing was the **combination**.

## The result

| Candidate | In-distribution | **Compositional (held-out)** |
|-----------|-----------------|------------------------------|
| **MODEL** | **0.900** | **0.000** |
| TEMPLATE | 0.800 | 0.000 |
| RETRIEVAL | 1.000 | 0.000 |

The model scored **0.000** on compositional generalization. Not "partly" — zero.

And it is not a fluke of the evaluator. We inspected what the model actually
generated for a composite prompt. For `abs_add` — "take the absolute value of each
and return their sum" — it produced:

```
def solve(a, b):
    return a - b
```

which is not even the right primitives. For others it emitted malformed fragments or
reverted to a single memorized primitive pattern. It did not say "I know abs, I know
add, therefore I can do abs_add." It had no such compositional ability at all.

## The audit: is this a fair test?

We must rule out the possibility that this 0.000 is an evaluator artifact or an
unfair split. The evidence that it is *fair* is decisive: **the baseline systems also
scored 0.000.** Retrieval got 0.000 because no composite exists in the training set —
there is literally nothing to retrieve. The template rule system got 0.000 because it
has no composite rule. So the 0.000 is not a sign the task is impossible or wrongly
scored; it is a sign that the *only* way to get a composite answer is to genuinely
compose it — and the model cannot.

## What this teaches

This is as clean a measurement as this book produced, and it is the answer to our
central question at this scale:

> **A ~0.9M-parameter model can learn individual primitives to ~90% accuracy, but it
> cannot compose them into structures it never saw during training. Compositional
> generalization fails completely — even when every component is well learned.**

That is a real capability boundary, and it is *not* the same as "the model is bad."
The model is genuinely good at the single operations. The boundary is specifically
about **combination**.

The natural next question — and we answer it in Chapter 12 — is whether this is a
capacity problem (would a bigger model fix it?) or a structural/data problem (does
the model need to see *combinations* of the right kind during training?). That
distinction is the difference between "we need a bigger machine" and "we need a
different kind of data." As we'll see, at this scale it is not capacity.
