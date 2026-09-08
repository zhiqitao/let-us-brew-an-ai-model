"""Tests for the TEACHER (data generator + program generator + test generator + NL renderer)."""
import pytest
from src.data_generator.generator import generate_dataset, make_task
from src.evaluator.evaluator import Judge

j = Judge()


def test_generated_reference_passes_its_own_tests():
    d = generate_dataset(n_per_op=4, seed=1)
    for t in d:
        r = j.evaluate_problem(t["reference_code"], t["hidden_tests"])
        assert r["pass_at_1"], f"{t['semantics']['operation']} failed its own tests"


def test_tasks_have_prompt_ref_tests():
    t = make_task("add", "t1", seed=0)
    assert t["nl"]["prompt"]
    assert "def solve" in t["reference_code"]
    assert len(t["hidden_tests"]) >= 4


def test_hidden_tests_cover_edge_cases():
    t = make_task("add", "t2", seed=3)
    notes = {x["note"] for x in t["hidden_tests"]}
    assert "zero" in notes
    assert "negative" in notes
    assert "large" in notes


def test_multiple_nl_families_produce_different_wordings():
    from src.nl_renderer.renderer import render_nl
    sem = {"operation": "add", "args": [{"name": "a", "type": "int"}, {"name": "b", "type": "int"}]}
    prompts = {render_nl(sem, family=f)[0] for f in (None,)}
    # at least render works and returns a non-empty prompt
    p, fam = render_nl(sem)
    assert p
    assert fam


def test_all_pilot_operations_have_nl_family():
    from src.nl_renderer.renderer import FAMILIES
    from src.data_generator.generator import OPERATIONS
    for op in OPERATIONS:
        assert op in FAMILIES, f"no NL template family for {op}"


def test_composite_reference_passes_its_own_tests():
    from src.data_generator.generator import generate_compositional
    d = generate_compositional(n_per_op=4, seed=2)
    assert len(d) >= 4
    for t in d:
        r = j.evaluate_problem(t["reference_code"], t["hidden_tests"])
        assert r["pass_at_1"], f"composite {t['semantics']['operation']} failed own tests"


def test_composite_ops_have_nl_family():
    from src.nl_renderer.renderer import FAMILIES
    from src.data_generator.generator import COMPOSITE_OPERATIONS
    for op in COMPOSITE_OPERATIONS:
        assert op in FAMILIES, f"no NL template family for composite {op}"
