"""THE JUDGE — the execution-based evaluation pipeline.

Scores a generated Python program through the four-stage hierarchy (see
specs/evaluation_protocol_v0_1.md):
  1. Syntax Pass      : parses.
  2. AST/Capability   : within whitelist.
  3. Execution        : runs without error in the sandbox.
  4. Semantic         : output matches hidden tests via comparator.
"""
from src.sandbox import sandbox
from src.evaluator.comparator import semantic_equal


class Judge:
    def __init__(self, spec_version="python_capability_v0_1"):
        self.spec_version = spec_version

    def evaluate_problem(self, source, hidden_tests):
        """Evaluate one generated program against a list of hidden tests.

        hidden_tests: list of {"args": [...], "expected": ...}

        Returns a dict with per-stage booleans, per-test results, and the metric
        pass@1 (all tests passed).
        """
        result = {
            "spec_version": self.spec_version,
            "syntax_ok": False,
            "capability_ok": False,
            "execution_ok": False,
            "test_results": [],
            "tests_passed": 0,
            "tests_total": len(hidden_tests),
            "pass_at_1": False,
            "error": None,
        }

        # 1. Syntax + 2. Capability
        try:
            sandbox.validate_source(source)
            result["syntax_ok"] = True
            result["capability_ok"] = True
        except sandbox.SandboxError as e:
            result["error"] = f"validation: {e}"
            return result

        # 3 + 4. For each hidden test, execute and compare
        fname = _solve_name(source)
        for t in hidden_tests:
            tr = {"passed": False, "note": t.get("note")}
            try:
                out = sandbox.execute_function(source, t["args"])
                tr["output"] = out
                tr["expected"] = t["expected"]
                tr["passed"] = semantic_equal(out, t["expected"])
            except Exception as e:  # runtime error, timeout, etc.
                tr["error"] = f"{type(e).__name__}: {e}"
                tr["passed"] = False
            result["test_results"].append(tr)
            if tr["passed"]:
                result["tests_passed"] += 1

        result["execution_ok"] = result["tests_passed"] > 0 or len(hidden_tests) == 0
        result["pass_at_1"] = result["tests_passed"] == result["tests_total"] and result["tests_total"] > 0
        return result


def _solve_name(source):
    """The sandbox requires the function be named `solve`; use that."""
    return "solve"
