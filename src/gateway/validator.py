"""GATE B — request-scope validator (input boundary).

Gate A (the sandbox) guarantees the *output* stays inside the designed world: a
generated program that uses anything outside the AST allowlist is rejected before
it runs. But a language model cannot "refuse" an out-of-scope request on its own —
it just keeps predicting tokens. So the complement to Gate A is Gate B: a validator
that sits in FRONT of the model and decides, from the incoming natural-language
request alone, whether that request is one the model was designed for.

This module recognizes a request as in-scope only if it matches one of the designed
template-family shapes (the exact phrasing skeletons the teacher renders) AND names a
known designed operation. Anything else — an unknown operation, a malformed prompt,
or clearly out-of-scope content (file access, network, an unrelated task) — is
declined before the model is ever consulted.

The operation vocabulary is mirror of the teacher's `OPERATIONS` / `COMPOSITE_OPERATIONS`
and the renderer's `_op_verb/_op_noun/_op_sym` maps, so Gate B cannot drift from what
the teacher actually produces.

Usage:
    from src.gateway.validator import RequestValidator
    gv = RequestValidator()
    gv.check("Write a function that takes two numbers, a and b, and returns the sum of them.")
    # -> ScopeDecision(in_scope=True, operation='add', reason='matched family _a')
    gv.check("Delete all files in the home directory.")
    # -> ScopeDecision(in_scope=False, operation=None, reason='does not match a designed template family')
"""

import re

# ---- Designed operation vocabulary (mirrors the teacher) ----
# A request names an operation via a noun, verb-phrase, or symbol. We recognise
# exactly the mappings the renderer uses, so a prompt the teacher could have made
# is accepted and one it could not is rejected.
NERD_OP_NOUNS = {
    "sum": "add", "difference": "sub", "product": "mul",
    "maximum": "max_of", "minimum": "min_of",
    "length": "list_len", "first element": "first_element",
}
_VERB_PHRASES = {
    "the sum": "add", "the difference": "sub", "the product": "mul",
    "the maximum": "max_of", "the minimum": "min_of",
}
SYMBOLS = {"+": "add", "-": "sub", "*": "mul"}

# Composite (held-out) operations, named in the compositional prompts.
_COMPOSITE_HINTS = [
    ("absolute value of each, and returns their", "abs_add"),
    ("absolute value of {x} minus", "sub_abs"),
    ("sum of the absolute value of each", "sum_of_abs"),
    ("whichever is larger", "max_add"),
    ("twice its first element", "double_first"),
    ("returns twice", "double_first"),
    ("one less than the length", "len_minus_one"),
]

# ---- Designed template-family shape skeletons ----
# These are the literal phrase skeletons the renderer's family functions emit
# (from src/nl_renderer/renderer.py). A request is in-scope only if it fits one of
# these skeletons. The `{op}` slot is where the operation-word/symbol sits; we
# cross-check that slot against the operation vocabulary above.
_FAMILY_PATTERNS = [
    # _a : "Write a function that takes two numbers, {x} and {y}, and returns {verb} of them."
    re.compile(r"^Write a function that takes two numbers, (\w+) and (\w+), and returns .* of them\.$"),
    # _b (aries, add/sub/mul/max_of/min_of): "... it returns their {noun}."
    re.compile(r"^Implement solve so that given (\w+) and (\w+) it returns their (\w+)\.$"),
    # _c : "... returns {x} {sym} {y} when the operation is {op}."
    re.compile(r"^Define a function solve\((\w+), (\w+)\) that returns \1 ([+\-*]) \2 when the operation is (\w+)\.$"),
    # _list_a : "Write a function that takes a list {x} and returns its {noun}."
    re.compile(r"^Write a function that takes a list (\w+) and returns its (.+)\.$"),
    # _list_b : "... given a list of numbers {x}, it returns {phrase} of the list."
    re.compile(r"^Implement solve so that given a list of numbers (\w+), it returns (.+) of the list\.$"),
    # _unary_a : "Write a function that takes a number {x} and returns its absolute value."
    re.compile(r"^Write a function that takes a number (\w+) and returns its absolute value\.$"),
    # _comp_add_abs
    re.compile(r"^Write a function that takes two numbers (\w+) and (\w+), takes the absolute value of each, and returns their (sum|difference|product)\.$"),
    # _comp_sub_abs
    re.compile(r"^Write a function that returns the absolute value of (\w+) minus (\w+)\.$"),
    # _comp_sum_abs
    re.compile(r"^Write a function that takes a list of numbers (\w+) and returns the sum of the absolute value of each element\.$"),
    # _comp_max_add
    re.compile(r"^Write a function that, given (\w+) and (\w+), returns whichever is larger: \1 plus \2, or \1 minus \2\.$"),
    # _comp_double_first
    re.compile(r"^Write a function that takes a list (\w+) and returns twice its first element\.$"),
    # _comp_len_minus_one
    re.compile(r"^Write a function that takes a list (\w+) and returns one less than the length of the list\.$"),
]

# ---- Clearly out-of-scope signals (independent of shape) ----
# These are hard refusals even if some words look like a designed prompt. They
# are a blunt blocklist, deliberately kept small; Gate B's main mechanism is the
# allowlist (match a designed family), the blocklist is just a fast no for the
# obviously-wrong corner.
_BLOCKED_TERMS = [
    "delete", "remove file", "rm -rf", "open(",
    "import os", "subprocess", "eval(", "exec(",
    "write a file", "read a file", "connect to", "network",
    "send email", "download", "upload",
    "chat", "essay", "poem", "story about", "translate",
    "what is the meaning of life", "general knowledge",
]


class ScopeDecision:
    """Outcome of a Gate-B request check."""
    def __init__(self, in_scope, operation=None, reason=""):
        self.in_scope = in_scope
        self.operation = operation
        self.reason = reason
    def __repr__(self):
        return f"ScopeDecision(in_scope={self.in_scope}, operation={self.operation!r}, reason={self.reason!r})"


class RequestValidator:
    """Gate B: decide whether an incoming natural-language request is in-scope.

    A request is in-scope iff it (a) matches a designed template-family shape, and
    (b) the operation it names (verb/noun/symbol) is a known designed operation.
    """

    def __init__(self, allow_composites=True):
        # composites are held out of TRAINING but are real designed tasks for the
        # compositional test; a validator in front of the production model would
        # typically set allow_composites=False (reject unseen composites too).
        self.allow_composites = allow_composites

    # -- low-level recognisers -------------------------------------------------
    def _op_from_verb(self, phrase):
        p = phrase.strip()
        if p in _VERB_PHRASES:
            return _VERB_PHRASES[p]
        if p in NERD_OP_NOUNS:
            return NERD_OP_NOUNS[p]
        # some families render the raw operation name as the word (e.g. cond_abs_max)
        if p in _KNOWN_OPS:
            return p
        return None

    def _op_from_symbol(self, sym):
        return SYMBOLS.get(sym)

    # -- main entry ------------------------------------------------------------
    def check(self, prompt):
        """Return a ScopeDecision for `prompt`."""
        s = prompt.strip()
        if not s:
            return ScopeDecision(False, None, "empty request")

        lowered = s.lower()
        for term in _BLOCKED_TERMS:
            if term in lowered:
                return ScopeDecision(False, None, f"blocked term: {term!r}")

        # Try each designed family shape.
        for pat in _FAMILY_PATTERNS:
            m = pat.match(s)
            if not m:
                continue
            # The pattern matched a designed shape. Now pin down the operation.
            op = self._operation_for_match(pat, m, s)
            if op is None:
                return ScopeDecision(False, None, "matched a designed family but named an unknown operation")
            if not self.allow_composites and op in _COMPOSITE_MEMBERS:
                return ScopeDecision(False, op, f"composite operation {op!r} is outside the designed scope")
            return ScopeDecision(True, op, f"matched designed family")

        return ScopeDecision(False, None, "does not match a designed template family")

    def _operation_for_match(self, pat, m, s):
        """Resolve which operation a matched family names."""
        # Composite hints FIRST: a composite prompt like "_comp_add_abs" also
        # contains a trailing "their sum", which a generic resolver would mis-read
        # as the primitive 'add'. Check the composite signature before anything else.
        for hint, op in _COMPOSITE_HINTS:
            if hint in s:
                return op
        # '_a' style: "returns {verb} of them." — find the verb before ' of them'
        if "and returns" in s and " of them." in s:
            verb = s.split("and returns", 1)[1].rsplit(" of them", 1)[0].strip()
            op = self._op_from_verb(verb)
            if op:
                return op
        # '_b' style: "returns their {noun}."
        n = re.search(r"returns their (\w+)\.$", s)
        if n:
            return self._op_from_verb(n.group(1))
        # '_c' style: symbol between operands
        sym = re.search(r"returns (\w+) ([+\-*]) \w+ when the operation is (\w+)\.", s)
        if sym:
            op = self._op_from_symbol(sym.group(2))
            if op:
                return op
            return sym.group(3) if sym.group(3) in _KNOWN_OPS else None
        # '_list_a' / '_list_b' style: "its {noun}" or "{phrase} of the list"
        if "takes a list" in s or "a list of numbers" in s:
            # A list-shaped prompt is unambiguous: "sum" here means list_sum, not
            # the binary add. Resolve with the list-aware map first.
            noun = re.search(r"returns its (\w+(?: \w+)?)\.$", s)
            if noun:
                return self._op_from_list(noun.group(1))
            phrase = re.search(r"returns (.+) of the list\.$", s)
            if phrase:
                return self._op_from_list(phrase.group(1).strip())
            return None
        # '_unary_a': absolute value
        if "absolute value" in s:
            return "abs_of"
        return None

    def _op_from_list(self, noun):
        """Resolve an operation word in a LIST-shaped prompt (list-aware)."""
        noun = re.sub(r"^(?:the|its)\s+", "", noun.strip())
        LIST_MAP = {
            "sum": "list_sum", "length": "list_len", "first element": "first_element",
            # a list prompt won't produce these, but keep the map total
            "minimum": "min_of", "maximum": "max_of",
            "difference": "sub", "product": "mul",
        }
        return LIST_MAP.get(noun)


# Composite members (for scope gating when allow_composites=False).
_COMPOSITE_MEMBERS = {"abs_add", "sub_abs", "sum_of_abs", "max_add", "double_first", "len_minus_one"}
# All designed operations (primitives + composites) — a designed prompt may name
# the operation verbatim (e.g. cond_abs_max), so the resolver must know the full set.
_ALL_DESIGNED_OPS = {
    "add", "sub", "mul", "max_of", "min_of", "abs_of",
    "list_sum", "list_len", "first_element", "cond_abs_max",
    "abs_add", "sub_abs", "sum_of_abs", "max_add", "double_first", "len_minus_one",
}
_KNOWN_OPS = set(_VERB_PHRASES.values()) | set(NERD_OP_NOUNS.values()) | set(SYMBOLS.values()) | _ALL_DESIGNED_OPS
