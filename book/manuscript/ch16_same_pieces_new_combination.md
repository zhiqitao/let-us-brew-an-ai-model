# 16. Same Pieces, New Combination

This is the experiment this whole book was building toward. Everything so far asked
whether the model learned a *single* operation. It did. But knowing one operation isn't
the same as being able to **put two operations together** into something you've never
seen. And that combination — not the individual pieces — is what we mean by
"capability."

Think of it this way. A model that can add, and can take absolute values, but cannot
return the sum of the absolute values of two numbers, does not have compositional
ability. It has two unrelated reflexes.

So we built the test that isolates exactly that.

## The split

We trained the model on **primitives only** — `add`, `sub`, `mul`, `max_of`,
`min_of`, `abs_of`, `list_sum`, `list_len`, `first_element` — 1,400 tasks. The model
saw **no combined operation at all.**

Then we built a hold-out of **composite** operations, each of which fuses two of those
primitives, and none of which appeared in training:

| composite | what it fuses |
|-----------|---------------|
| `abs_add` | `abs`, then `add` |
| `sub_abs` | `sub`, then `abs` |
| `sum_of_abs` | `abs` over a list sum |
| `max_add` | `max(add, sub)` |
| `double_first` | index, then times 2 |
| `len_minus_one` | `len`, then minus one |

The crucial fact: the model *knew every primitive involved* — it scored ~90% on each.
The only new thing was the **combination**.

## The result
![Model size and composition](figures/fig_model_size.png)

| Candidate | In-distribution | **Composition (held-out)** |
|-----------|-----------------|----------------------------|
| **MODEL** | **0.900** | **0.000** |
| TEMPLATE | 0.800 | 0.000 |
| RETRIEVAL | 1.000 | 0.000 |

The model scored **0.000** on composition. Not "poorly" — zero.

And it's not a fluke of our measuring. We looked at what it actually generated for a
composite prompt. Told to "take the absolute value of each and return their sum," it
produced:

```python
def solve(a, b):
    return a - b
```

which isn't even the right primitives. For others it emitted broken fragments or
reverted to a single memorized pattern. It never said "I know abs and I know add, so I
can do abs + abs." It had no such ability.

## Is this a fair test?

We must rule out that the 0.000 is a broken evaluator or an unfair split. The proof
it's fair is decisive: **the baseline systems also scored 0.000.** Retrieval got 0
because no composite exists in training — there's literally nothing to look up. The
template rule system got 0 because it has no composite rule. So the 0.000 doesn't mean
the test is impossible or mis-scored; it means the *only* way to answer is to genuinely
compose — and the model can't.

## What this teaches

This is as clean a measurement as this book produced:

> **A ~0.9M model can learn individual operations to ~90%, but it cannot combine them
> into structures it never saw. Compositional generalization fails completely — even
> when every ingredient is well learned.**

And crucially, this is *not* the same as "the model is bad." The model is genuinely
good at the individual operations. The boundary is specifically about **combining**
them.

The natural next question — and the reason for Chapter 12 — is whether this is a
capacity problem ("just make it bigger") or a structural/data problem ("does it need
to see combinations?"). As we'll see, at this scale, it is not capacity.
