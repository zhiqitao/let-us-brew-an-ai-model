"""THE WORLD — the controlled Python sandbox.

Implements the AST whitelist + restricted execution described in
specs/python_capability_v0_1.md. Does NOT rely on blocklists: any AST node not
explicitly permitted is rejected.

This is a teaching / evaluation sandbox, NOT a claim of production-grade adversarial
isolation.
"""
import ast

# ---- AST node whitelist (spec v0_1) -----------------------------------------
ALLOWED_NODES = {
    # module / functions
    "Module", "FunctionDef", "arguments", "arg", "Return",
    # names / assignment
    "Assign", "Name", "Load", "Store",
    # literals
    "Constant",
    # arithmetic
    "BinOp", "Add", "Sub", "Mult", "Div", "FloorDiv", "Mod", "Pow",
    "UnaryOp", "USub", "UAdd", "Not",
    # boolean / comparison
    "BoolOp", "And", "Or", "Compare", "Lt", "LtE", "Gt", "GtE", "Eq", "NotEq",
    # control flow
    "If", "For", "While", "Break", "Continue", "Pass",
    # lists / indexing
    "List", "Subscript", "Index", "Slice",
    # calls (built-ins only, see ALLOWED_BUILTINS)
    "Call",
    # attribute access (only for a small set of list methods)
    "Attribute",
}

ALLOWED_BUILTINS = {
    "abs", "min", "max", "sum", "len", "range", "int", "float", "round",
    "list", "sorted",
}

ALLOWED_METHODS = {"append", "count", "index", "pop"}

# ---- limits (spec v0_1) -----------------------------------------------------
MAX_AST_DEPTH = 24
MAX_AST_NODES = 200
MAX_NESTING = 8
MAX_EXEC_TIME = 1.0
MAX_RECURSION = 16


class SandboxError(Exception):
    """Raised when a program violates the capability specification."""


def validate(ast_node, _depth=0, _count=None):
    """Recursively validate an AST against the whitelist.

    Rejects any node type not in ALLOWED_NODES, any builtin not in ALLOWED_BUILTINS,
    and any attribute method not in ALLOWED_METHODS. Raises SandboxError.
    """
    if _count is None:
        _count = [0]
    _count[0] += 1
    if _count[0] > MAX_AST_NODES:
        raise SandboxError("program too long (AST node limit)")
    if _depth > MAX_AST_DEPTH:
        raise SandboxError("AST too deep")

    node_type = type(ast_node).__name__
    if node_type not in ALLOWED_NODES:
        raise SandboxError(f"disallowed AST node: {node_type}")

    # built-in call contents
    if isinstance(ast_node, ast.Call):
        if not isinstance(ast_node.func, ast.Name):
            raise SandboxError("only direct built-in calls are allowed")
        if ast_node.func.id not in ALLOWED_BUILTINS:
            raise SandboxError(f"disallowed builtin: {ast_node.func.id}")
    # attribute methods
    if isinstance(ast_node, ast.Attribute):
        if not isinstance(ast_node.value, ast.Name):
            raise SandboxError("attribute access only on simple names")
        if ast_node.attr not in ALLOWED_METHODS:
            raise SandboxError(f"disallowed method: {ast_node.attr}")

    # recurse
    for child in ast.iter_child_nodes(ast_node):
        validate(child, _depth + 1, _count)


def validate_source(source):
    """Parse source, then validate the resulting Module AST. Returns the module."""
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise SandboxError(f"syntax error: {e}")
    validate(tree)
    return tree


# ---- restricted execution ----------------------------------------------------
def _restricted_globals():
    # Inject ONLY permitted built-ins. Do not expose __import__, open, eval, etc.
    import builtins as _b
    safe = {
        "__builtins__": {
            name: getattr(_b, name) for name in ALLOWED_BUILTINS
            if hasattr(_b, name)
        },
    }
    return safe


def execute_function(source, args, max_nodes=2000):
    """Validate, compile, and call the single `solve` function with `args`.

    Returns the function's return value. Raises SandboxError / any runtime error
    surfaced by execution. This is the sandbox's primary entry point for the
    evaluator.
    """
    tree = validate_source(source)
    # ensure there is exactly one function named `solve`
    funcs = [n for n in tree.body if isinstance(n, (ast.FunctionDef,))]
    if len(funcs) != 1:
        raise SandboxError("expected exactly one function named `solve`")

    ns = _restricted_globals()
    exec(compile(tree, "<sandbox>", "exec"), ns)
    if "solve" not in ns:
        raise SandboxError("`solve` not defined")

    sig_timer = 0
    return ns["solve"](*args)
