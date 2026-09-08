# Python Capability Specification v0.1

Status: **DRAFT (experimental)** — `[DESIGN]`; exact boundaries are determined
experimentally and this file is versioned.

This is a **formal experimental specification**, not a new programming language. It
defines the *controlled subset* of Python the model is allowed to produce and run in
the sandbox. The environment is intentionally small so capability is measurable.

## 1. Scope

The model's job is to take a natural-language specification of a programming task
and produce a **pure function** (or a small program with a deterministic output) that
is then compiled and executed against hidden tests. Everything the model may emit is
constrainined to whitelisted AST nodes and permitted built-ins.

## 2. Versioning

- **Spec version:** `python_capability_v0_1`
- **Python version:** 3.10+ (the reference interpreter)
- **AST whitelist:** see §5
- **Changes:** any change to the allowed language bumps the version. Experiments
  record the spec version in their manifest.

## 3. Initial permitted capabilities

- integer and float literals
- arithmetic operators: `+ - * / // % **`
- variables and assignment
- `return`
- comparisons: `< <= > >= == !=`
- boolean operators: `and or not`
- selected built-ins: `abs, min, max, sum, len, range, int, float, round`
- lists: literals, indexing, slicing, `append`, `in`
- basic conditionals: `if / elif / else`
- basic loops: `for` over a range/list, `while`
- simple `def` functions (pure, no side effects)

## 4. Explicitly forbidden

- `import` / `from ... import`
- file I/O, network access, subprocess, `os`, `sys`, environment access
- `random`, `time`, `datetime` (non-determinism)
- `eval`, `exec`, `compile`, `globals`, `locals`, `getattr`, `setattr`, `open`
- `class` definitions, `try/except`, `with`
- arbitrary attribute access, comprehensions and lambdas (unless later whitelisted)
- global/persistent mutation, side effects on inputs (language is pure-function)

## 5. AST whitelist (initial)

Allowed node types (reject everything else):

```
Module, FunctionDef, arguments, arg, Return, Assign, Name, Load, Store,
Constant, BinOp, Add, Sub, Mult, Div, FloorDiv, Mod, Pow,
UnaryOp, USub, UAdd, Not,
BoolOp, And, Or, Compare, Lt, LtE, Gt, GtE, Eq, NotEq,
If, For, While, Break, Continue, Pass,
List, Subscript, Index, Slice,
Call, attribute (only for a whitelisted set, see §6)
```

## 6. Permitted built-in calls

Only these may appear as `Call.func` names:
`abs, min, max, sum, len, range, int, float, round, list, sorted`

List methods allowed on `Attribute` load: `append`, `count`, `index`, `pop`
(refinement subject to experiment).

## 7. Resource & determinism policy

- **max AST depth:** 24
- **max program length (AST nodes):** 200
- **max nesting depth (control structure):** 8
- **max execution time:** 1.0 s per test case (configurable)
- **max recursion:** disabled / depth-capped to 16
- **memory policy:** ~256 MB cap (best-effort)
- **float comparison tolerance:** `1e-9` absolute (see `evaluator/comparator.py`)
- **dictionary ordering:** order-insensitive
- **randomness:** none (no `random`/`time`)
- **side effects:** none; pure functions only

## 8. The sandbox

Do **not** rely on blocklists. Use an **AST whitelist**:

```
source -> parse -> AST -> whitelist validation -> compile -> restricted execution
        -> semantic comparison
```

If an AST node is not explicitly permitted, **reject it**. Execution uses restricted
globals (only permitted built-ins injected). The sandbox is a *teaching/evaluation*
sandbox, **not** a claim of production-grade adversarial isolation — the book states
this distinction.

## 9. Example target

```python
def add(a, b):
    return a + b

def max_of(a, b):
    if a > b:
        return a
    return b

def list_sum(xs):
    total = 0
    for x in xs:
        total = total + x
    return total
```

## 10. Policy fields (recorded per experiment)

python_version, allowed_ast_node_types, allowed_operators, allowed_builtins,
allowed_data_types, max_ast_depth, max_program_length, max_nesting_depth,
max_execution_time, memory_policy, deterministic, float_tolerance, recursion_policy,
side_effect_policy, import_policy, file_io_policy, network_policy, randomness_policy,
time_access_policy.
