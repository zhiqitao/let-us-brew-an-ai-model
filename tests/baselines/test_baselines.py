"""Tests for the baselines (template + retrieval)."""
from src.baselines.template.baseline import template_baseline_generate, detect_operation
from src.baselines.retrieval.baseline import RetrievalBaseline
from src.evaluator.evaluator import Judge
from src.data_generator.generator import make_task

j = Judge()


def test_template_detects_operations():
    assert detect_operation("return the sum of a and b") == "add"
    assert detect_operation("the difference") == "sub"
    assert detect_operation("the product") == "mul"
    assert detect_operation("the maximum") == "max_of"
    assert detect_operation("the length of a list") == "list_len"


def test_template_baseline_generates_runnable_code_on_recognized_op():
    t = make_task("add", "t1", seed=1)
    cand = template_baseline_generate(t)
    r = j.evaluate_problem(cand, t["hidden_tests"])
    assert r["pass_at_1"]  # recognized -> correct program


def test_template_baseline_stub_on_unknown():
    t = {"nl": {"prompt": "some totally unrecognizable phrasing zzqx"}, "semantics": {"operation": "add", "args": [{"name": "a","type":"int"},{"name":"b","type":"int"}]}}
    cand = template_baseline_generate(t)
    assert "return 0" in cand


def test_retrieval_baseline_returns_something():
    tasks = [make_task("add", f"a{i}", seed=i) for i in range(5)]
    rb = RetrievalBaseline(tasks)
    out = rb.baseline_generate(tasks[3])
    assert out is not None and "def solve" in out
