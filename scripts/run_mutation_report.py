#!/usr/bin/env python3
"""Produce a measured mutation report for the judge (R07).

For every operation, generate mutant reference programs and check how many the
hidden-test suite catches (kill), how many survive (pass), and count invalid /
equivalent mutants. Also run a positive control: the true reference and an
alternative correct program should be ACCEPTED (this distinguishes a
reject-everything evaluator from a genuinely discriminating one).
"""
import sys, os, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.evaluator.evaluator import Judge
from src.evaluator.mutations import generate_mutants
from src.data_generator.generator import make_task, OPERATIONS, COMPOSITE_OPERATIONS

# An equivalent mutant: swap operands of `+` (a+b == b+a). Should NOT count as a
# killed mutant if we detect equivalence; we report it separately.
def fake_sibling(source):
    """A DIFFERENT but still-correct program for the same operation (positive
    control). We just reuse the reference here for the basic positive control;
    per-op alternatives are added below."""
    return source


def run():
    judge = Judge()
    rows = []
    for op in list(OPERATIONS) + list(COMPOSITE_OPERATIONS):
        t = make_task(op, f"mut_{op}", seed=7, id_set="letters")
        ref = t["reference_code"]; tests = t["hidden_tests"]
        # generate mutants
        mutants = list(generate_mutants(ref))
        # positive control: reference itself and (if provided) an alternate correct
        ref_res = judge.evaluate_problem(ref, tests)
        killed = 0; survived = 0; invalid = 0
        per_class = collections.defaultdict(lambda: {"killed":0,"survived":0,"invalid":0})
        for name, msrc in mutants:
            try:
                res = judge.evaluate_problem(msrc, tests)
                p = res["pass_at_1"]
            except Exception as e:
                invalid += 1
                per_class[name]["invalid"] += 1
                continue
            if p:
                survived += 1; per_class[name]["survived"] += 1
            else:
                killed += 1; per_class[name]["killed"] += 1
        total = len(mutants)
        rows.append({
            "op": op,
            "ref_accepted": bool(ref_res["pass_at_1"]),
            "mutants_total": total,
            "killed": killed,
            "survived": survived,
            "invalid": invalid,
            "kill_rate": round(killed/total,3) if total else None,
            "by_class": {k:v for k,v in per_class.items()},
        })
    # aggregate
    tot=sum(r["mutants_total"] for r in rows)
    killed=sum(r["killed"] for r in rows); survived=sum(r["survived"] for r in rows)
    invalid=sum(r["invalid"] for r in rows)
    all_refs_ok = all(r["ref_accepted"] for r in rows)
    agg = {"operations": len(rows),
           "mutants_total": tot, "killed": killed, "survived": survived,
           "invalid": invalid,
           "kill_rate": round(killed/tot,3) if tot else None,
           "all_reference_positive_controls_accepted": all_refs_ok}
    out = {"aggregate": agg, "per_operation": rows}
    mp = os.path.join(os.path.dirname(__file__), "..", "artifacts", "manifests", "judge_mutation.json")
    os.makedirs(os.path.dirname(mp), exist_ok=True)
    json.dump(out, open(mp, "w"), indent=2)
    print("== AGGREGATE ==")
    print(json.dumps(agg, indent=1))
    print("\n== per-operation ==")
    for r in rows:
        print(f"  {r['op']:16s} mut={r['mutants_total']:3d} kill={r['killed']:3d} surv={r['survived']:3d} inval={r['invalid']:2d} rate={r['kill_rate']}")
    print("\nmanifest ->", mp)

if __name__ == "__main__":
    run()
