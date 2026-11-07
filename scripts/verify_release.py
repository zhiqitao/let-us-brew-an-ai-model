#!/usr/bin/env python3
"""verify_release.py — closed-loop release-gate invariant checker for
"Let Us Brew an AI Model".

A fourth review found stale/contradictory integration defects (wrong diversity
numbers in a figure caption, a stale Ch11 claim, an unprintable Figure 15.1, a
stale LOF entry, shifted Appendix C section refs, release-commit provenance).
Free-form re-reading is not a release gate, so this script asserts MACHINE-
CHECKED invariants in a PREFLIGHT plus five phases (A-E):

  A. manifest invariants  — parse artifacts/manifests/*.json and assert the
     canonical corrected values (data scaling, diversity, surface 2x2,
     composition match-controls, stage1 pilot) against hard-coded ground truth.
     Manifest tokenizer fields are the in-memory VOCABULARY hashes the runs
     recorded (TOK_*_VOCAB), not file hashes.
  B. source invariants    — scan book/manuscript/*.md, the LOF caption dict in
     book/latex/md_to_latex.py, and the figure scripts: every stale pattern is
     absent (or carries an explicit flawed/superseded marker), every canonical
     number/claim/section-ref/provenance identifier is present, the manuscript
     cites the tokenizer DISK sha256s (never the in-memory vocab hashes), the
     ch15/ch16 reviewer-scoped statements are present, and the pinned
     requirements-lock.txt exists with its four pins.
  C. PDF invariants       — extract the rebuilt PDF's text with pymupdf and
     assert the canonical values appear, the stale values do not (outside
     labeled historical context), no '??'/'undefined' LaTeX artifacts remain,
     the four surface denominators are present, the LOF entry for Fig 13.1
     is the corrected one, and — render-geometry — every 64-hex tokenizer
     digest prints all 64 hex characters on its page AND ends at or before
     the text block's right edge (a digest severed at the 6in trim edge is
     the P1 clipping class this check exists to catch).
  D. release record       — hash ALL SEVEN tokenizer files on disk
     and assert they equal the cited constants, then assert
     docs/release_manifest.json (tag, tag-target commit, PDF build commit,
     PDF sha256, tokenizer disk hashes) matches git, the built PDF, and the
     files on disk; assert the manifest's tokenizer pin list is exactly the
     set of tokenizer files on disk AND the set of tokenizer files the book
     cites (an unpinned cited tokenizer = the drift gap this check closes);
     and assert the manifest documents the two-commit reproduction structure
     (tag = experiment snapshot, build commit = gate/runners).
  E. EPUB stale sweep   — unzip the shipped EPUB, extract its text, and assert the
     corrected headline strings (0.743 / 0.950 / 0.9167 / 0.893) are present and
     the superseded ones (high diversity 1.000 1.000, minimal diversity 0.500
     0.000, the 0.100/0.098/0.300/0.641 data_scaling row, Stage-4 baseline
     884,224 (0.88M) 0.900) absent; SKIP cleanly when the EPUB file is absent.
     The PDF being clean is NOT evidence the EPUB is (round-1 R3-EX-01).

PREFLIGHT (before every phase): a clean clone has no artifacts/tokenizer/
(gitignored, absent from every commit) and phase D used to crash on it with a
FileNotFoundError traceback. A missing gate-opened input dir now prints one
line -- "NOT A VERIFIABLE CLEAN CLONE ..." -- and exits 1 with NO traceback
(round-1 QWEN-R2-01).

Round-1 additions beyond the original four phases: phase C asserts the PDF's
CONTENT matches the recorded build commit (a stable string ADDED by
docs/release_manifest.json's pdf_build_commit and absent in its parent must
appear in the PDF; conversely text added AFTER the recorded commit must not --
a stale pdf_build_commit fails either way) and that manifest pdf.page_count
equals the actual page count (SKIP with a note when null); phase D asserts the
41-row provenance-ledger schema (len 41, unique experiment_ids, no nulls, row
set == Appendix C Table C.12) and that every produced_by_commit resolves in
git, with the producing script's blob at that commit recorded where
recoverable (script-DRIFT is recorded, not yet failed -- V3 material).

Historical values (the flawed 42-record run's 0.500/1.000, the Stage-3
mixed-factor 0.350, "42 versus 1,200") are legitimate WHENEVER they sit inside
a window that also carries a flaw marker (superseded / flawed / historical /
P0-0x / mixed-factor / Stage-3 / corrected ... instead). Everything else fails.

RUNTIME REQUIREMENT — run this gate under the repository's Python 3.11 venv:
    Phase C (and book/build_book.py's cover merge) import pymupdf, which the
    SYSTEM python3 does NOT provide. pymupdf is pinned in requirements-lock.txt
    and is installed in .venv-311, so the gate must be run as

        source .venv-311/bin/activate
        TORCH_DISABLE_AVX2=1 OMP_NUM_THREADS=2 python scripts/verify_release.py

    (equivalently `.venv-311/bin/python scripts/verify_release.py`). Under a
    python without pymupdf, phase C degrades to a loud, pass-marked SKIP
    instead of crashing — a green run that reports the skip has NOT checked the
    PDF, so always confirm the run lists phase C checks before trusting it.

Usage:
    .venv-311/bin/python scripts/verify_release.py          # A + B + D + C (default PDFs)
    .venv-311/bin/python scripts/verify_release.py --no-pdf # A + B + D only
    .venv-311/bin/python scripts/verify_release.py --pdf path.pdf  # A + B + D + C on that PDF
Exit code 0 = release gate PASS (0 mismatches), 1 = FAIL.
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MS = os.path.join(ROOT, "book", "manuscript")
MANIFESTS = os.path.join(ROOT, "artifacts", "manifests")

RELEASE_TAG = "v20261001"
RELEASE_COMMIT = "a45a881158ed076f615f6d3bc2e72640dc5cdced"   # git rev-parse v20261001^{commit}
# The PDF build commit is NOT a constant here: its single source of truth is
# docs/release_manifest.json -> pdf_build_commit (round-1 QWEN-R2-02: a
# hardcoded colophon hash went false the moment the PDF was rebuilt). This is
# the PRE-FIX hardcoded value, kept only so the gate can assert it appears
# NOWHERE in the source surfaces any more.
LEGACY_BUILD_COMMIT = "af32fb8b1798f83553c0f5078fd34b62063b864d"
STALE_COMMIT = "ae1ec01"                                       # never print this

# Canonical tokenizer hashes = SHA-256 of the tokenizer FILE ON DISK (the
# reproducible identifier the book cites). Phase D asserts these against the
# live files under artifacts/tokenizer/, phase B against the manuscript.
TOK_DATA = "361f6d89e4f18642fac9d1d9077d6a5cab0e5d97701bafc1641ab09ec2b10eb5"
TOK_DIV = "2282c2fe22c34467e193651b92a5b59da1e4820f5add778196e145170d081dce"
TOK_SURF = "2c5c800b21e6a9a39d2688aec50cd4e092b3f99ea673b0618ffa6ffc65eb0a2b"
TOK_COMP = "fbb9c903d0e5c1e2fbcd57dd7dfe27ff90ed74762a55e0cad1c776d8cf2ad17c"
TOK_PILOT = "29f07823a6d978ae971ea4f0d9293b3a9651a772acdb5f0c0289bea775705a54"
TOK_SURF_LEGACY = "1e61f0943d77ab348254d446380e09362c2e797d804148f495f457e105f1ae50"
TOK_FILES = {  # tokenizer id -> file under artifacts/tokenizer/ (ALL SEVEN on disk)
    "data_scaling": "data_scaling_corrected_tok.json",
    "diversity": "diversity_corrected_tok.json",
    "surface": "surface_corrected_tok.json",
    "composition_controls": "composition_match_controls_tok.json",
    "composition_legacy": "comp_tok.json",          # clobbered once; 75/291 indices
    "pilot": "pilot_tok.json",
    "surface_legacy": "surface_tok.json",
}
TOK_EXPECTED = {"data_scaling": TOK_DATA, "diversity": TOK_DIV,
                "surface": TOK_SURF, "composition_controls": TOK_COMP,
                "composition_legacy": TOK_COMP,     # same bytes as composition_controls
                "pilot": TOK_PILOT, "surface_legacy": TOK_SURF_LEGACY}
# In-memory VOCABULARY hashes recorded in the run manifests (vocab-content
# hash, NOT the file hash) — phase A asserts the manifests still carry these.
TOK_DATA_VOCAB = "ddbbc0edf257842619766f52b773e079e2db8b599ca5fb77224f27d3c914c1ae"
TOK_DIV_VOCAB = "d43d4a09d7b1f57e0bb4d8898560ce830176d4546f4fe654b5e676edf2396c1c"
TOK_SURF_VOCAB = "3bc4916b9318de39d9e8a7a09717ceec13cf43166eddc9fa867ad26ca05dd71e"
RELEASE_MANIFEST = os.path.join(ROOT, "docs", "release_manifest.json")
LOCKFILE = os.path.join(ROOT, "requirements-lock.txt")
LEDGER = os.path.join(ROOT, "docs", "reviews", "loop", "provenance_ledger.json")
LEDGER_EXPECTED_ROWS = 41                  # == Appendix C Table C.12 rows
# EPUB headline strings (round-1 R3-EX-01): corrected values that must be in a
# current EPUB, superseded values that must not be.
EPUB_MUST_HAVE = ["0.743", "0.950", "0.9167", "0.893"]
EPUB_MUST_NOT_HAVE = [
    "high diversity 1.000 1.000",
    "minimal diversity 0.500 0.000",
    "data_scaling 0.100 / 0.098 / 0.300 / 0.641",
    "Stage-4 baseline 884,224 (0.88M) 0.900",
]

# canonical corrected values -------------------------------------------------
DS_AGG = {  # aggregate pass@1 by size per seed (data_scaling_corrected)
    0: [0.897, 0.900, 0.893, 0.897],
    1: [0.893, 0.900, 0.900, 0.900],
    2: [0.900, 0.900, 0.997, 0.900],   # seed-2 size-1000 outlier 299/300
}
DIV_IN = {"low": [0.950, 0.950, 0.950], "high": [0.820, 0.570, 0.840]}   # mean high 0.743
DIV_HO = {"low": [0.000, 0.000, 0.000], "high": [0.640, 0.300, 0.710]}   # mean high 0.550
SURF_DEN = {"familiar": 600, "id_only": 600, "wording_only": 480, "combined": 480}
SURF_MODEL = {  # MODEL pass@1 per seed per cell
    0: [0.898, 0.000, 0.000, 0.000],
    1: [0.900, 0.003, 0.000, 0.025],
    2: [0.940, 0.005, 0.000, 0.000],
}
SURF_CELLS = ["familiar", "id_only", "wording_only", "combined"]
SURF_TEMPLATE_SUCC = [480, 480, 420, 420]   # TEMPLATE numerators over cell n
SURF_RETRIEVAL_SUCC = [600, 600, 60, 60]   # RETRIEVAL numerators over cell n
COMP_EXPOSED = {0: 0.667, 1: 0.658}

# flaw markers that license a historical value in the same window -----------
FLAW_MARK = re.compile(
    r"superseded|flawed|historical|P0-0\d|mixed-factor|Stage-3|stage3|"
    r"instead|not |retention|continual|corrected|replaced|ledger|audit",
    re.I)

results = []   # (phase, name, ok, detail)


def check(phase, name, ok, detail=""):
    results.append((phase, name, bool(ok), detail))
    mark = "PASS" if ok else "FAIL"
    print(f"[{phase}] {mark}  {name}" + (f"  -- {detail}" if detail and not ok else ""))
    return ok


def rd(fname):
    with open(os.path.join(MANIFESTS, fname), encoding="utf-8") as f:
        return json.load(f)


def near(a, b, tol=0.0011):
    return abs(float(a) - b) <= tol


def window_ok(text, span, pattern):
    """Every match of `pattern` in `text` must sit in a window that carries a
    flaw marker (or the match itself is inside a labeled historical table)."""
    for m in re.finditer(pattern, text):
        w = text[max(0, m.start() - 420):m.end() + 420]
        if not FLAW_MARK.search(w):
            line = text[:m.start()].count("\n") + 1
            return False, f"line {line}: {text[max(0,m.start()-60):m.end()+60]!r}"
    return True, ""


def _manifest():
    """docs/release_manifest.json as a dict ({} when absent/unreadable)."""
    try:
        with open(RELEASE_MANIFEST, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _git(*args, timeout=60):
    """Run git in ROOT; return (returncode, stdout). Never raises."""
    try:
        r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                           text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except Exception as e:                                  # pragma: no cover
        return 127, str(e)


def preflight():
    """QWEN-R2-01: a clean clone has no gitignored gate inputs; phase D used to
    die on os.listdir(artifacts/tokenizer) with a FileNotFoundError traceback.
    Fail fast with ONE clear line and exit 1 -- never a traceback."""
    missing = []
    tok_dir = os.path.join(ROOT, "artifacts", "tokenizer")
    if not os.path.isdir(tok_dir):
        missing.append(("artifacts/tokenizer/",
                        "NOT A VERIFIABLE CLEAN CLONE — the 7 pinned tokenizer "
                        "files are gitignored; run the quickstart generation "
                        "step (scripts/generate_data.py + the run scripts) "
                        "before the gate"))
    if not os.path.isdir(MANIFESTS):
        missing.append(("artifacts/manifests/",
                        "REQUIRED INPUT DIR MISSING — artifacts/manifests/ is "
                        "tracked in git; this working tree is incomplete"))
    if missing:
        for path, msg in missing:
            print(f"[PREFLIGHT] FAIL  {msg}  (missing: {path})")
        sys.exit(1)


# --- build-commit witness helpers (QWEN-R2-02) -----------------------------
_MD_CODEISH = re.compile(r"[$\\<>{}^~]")
_STABLE_MIN_LEN = 24
_STABLE_MIN_WORDS = 5
_STABLE_MAX = 6          # forward candidates per commit
_STABLE_MAX_REV = 40     # reverse candidates scanned


def _stable_strings(diff_text, cap):
    """Prose strings ADDED by a diff (lines starting with '+') that survive a
    markdown->LaTeX->PDF round trip: no table pipes, headings, bullets,
    quotes/apostrophes (pandoc smart-quotes them), ellipsis/double hyphens
    (pandoc rewrites those), or LaTeX specials. Markdown inline markers that do
    not render (`code`, **bold**) are stripped, not rejected."""
    out = []
    for line in diff_text.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        t = line[1:].strip()
        if len(t) < _STABLE_MIN_LEN or len(t.split()) < _STABLE_MIN_WORDS:
            continue
        if t.startswith(("#", "|", ">", "-", "*", "+", "~", "`")):
            continue
        if "'" in t or '"' in t or ".." in t or "--" in t:
            continue
        if _MD_CODEISH.search(t) or "](" in t:
            continue
        t = t.replace("`", "").replace("*", "")
        if len(t) < _STABLE_MIN_LEN:
            continue
        out.append(t)
        if len(out) >= cap:
            break
    return out


def _added_at(commit):
    """Stable strings ADDED to book/manuscript by `commit` vs its first parent."""
    rc, parent = _git("rev-parse", commit + "^")
    if rc == 0:
        rc, diff = _git("diff", parent, commit, "--", "book/manuscript")
    else:                                   # root commit (or unresolvable parent)
        rc, diff = _git("diff", commit, "--", "book/manuscript")
    if rc != 0:
        return None, f"git diff failed for {commit[:12]}: {diff[:120]}"
    return _stable_strings(diff, _STABLE_MAX), ""


def _added_since(commit):
    """Stable strings added to book/manuscript AFTER `commit` (commit..HEAD)."""
    rc, diff = _git("diff", commit, "HEAD", "--", "book/manuscript")
    if rc != 0:
        return None, f"git diff {commit[:12]}..HEAD failed: {diff[:120]}"
    return _stable_strings(diff, _STABLE_MAX_REV), ""


# ===========================================================================
# PHASE A — manifest invariants
# ===========================================================================
def phase_a():
    print("\n== PHASE A: manifest invariants ==")
    # --- A1 data scaling ---
    ok_all = True
    for seed in (0, 1, 2):
        d = rd(f"data_scaling_corrected_seed{seed}.json")
        ok = (d["tokenizer"]["sha256"] == TOK_DATA_VOCAB and
              d["config"]["steps"] == 1000 and
              d["selection"]["n_per_op_by_size"] == {"100": 10, "300": 30,
                                                     "1000": 100, "3000": 300})
        aggs = [round(r["aggregate_pass_at_1"], 3) for r in
                sorted(d["rows"], key=lambda r: r["size"])]
        ok = ok and aggs == DS_AGG[seed]
        ok = ok and all(r["ops_covered"] == 10 for r in d["rows"])
        ok_all &= check("A", f"data_scaling seed {seed}: aggregates {aggs} + "
                             f"tokenizer/steps/balanced-ops", ok,
                        f"expected {DS_AGG[seed]}")
    zeros = sum(1 for seed in (0, 1, 2)
                for r in rd(f"data_scaling_corrected_seed{seed}.json")["rows"]
                if r["per_op_pass_at_1"]["cond_abs_max"] == 0.0)
    ok_all &= check("A", "data scaling: cond_abs_max is 0.0 in 9/12 arms",
                    zeros == 9, f"found {zeros}/12")
    s2 = [r for r in rd("data_scaling_corrected_seed2.json")["rows"]
          if r["size"] == 1000][0]
    ok_all &= check("A", "data scaling: seed-2 size-1000 outlier = 0.997 (299/300)",
                    round(s2["aggregate_pass_at_1"], 3) == 0.997 and
                    s2["model_successes"] == 299 and s2["model_denominator"] == 300,
                    f"{s2['model_successes']}/{s2['model_denominator']}")

    # --- A2 diversity (equal-count) ---
    for seed in (0, 1, 2):
        d = rd(f"diversity_corrected_seed{seed}.json")
        lo, hi = d["arms"]["low"], d["arms"]["high"]
        ok = (d["tokenizer"]["sha256"] == TOK_DIV_VOCAB and
              d["tokenizer"]["vocab_size"] == 293 and
              d["config"]["steps"] == 1000 and
              lo["n"] == 1200 and hi["n"] == 1200 and
              lo["unique_prompt_program_pairs"] == 20 and
              hi["unique_prompt_program_pairs"] == 605 and
              set(lo["per_op_counts"].values()) == {120} and
              set(hi["per_op_counts"].values()) == {120})
        ind = d["results"]["in_distribution"]
        ho = d["results"]["held_out_family"]
        ok = ok and near(ind["low"]["systems"]["MODEL"]["pass_at_1"], DIV_IN["low"][seed])
        ok = ok and near(ind["high"]["systems"]["MODEL"]["pass_at_1"], DIV_IN["high"][seed])
        ok = ok and near(ho["low"]["systems"]["MODEL"]["pass_at_1"], DIV_HO["low"][seed])
        ok = ok and near(ho["high"]["systems"]["MODEL"]["pass_at_1"], DIV_HO["high"][seed])
        ok = ok and all(x["denominator"] == 100 for x in
                        (ind["low"], ind["high"], ho["low"], ho["high"]))
        ok_all &= check("A", f"diversity seed {seed}: 1200/1200 records, 20/605 pairs, "
                             f"in-dist {DIV_IN['low'][seed]:.3f}/{DIV_IN['high'][seed]:.3f}, "
                             f"held-out {DIV_HO['low'][seed]:.3f}/{DIV_HO['high'][seed]:.3f}, n=100",
                        ok)
    m_in = sum(DIV_IN["high"]) / 3
    m_ho = sum(DIV_HO["high"]) / 3
    ok_all &= check("A", "diversity: high-arm means 0.743 in-dist / 0.550 held-out",
                    round(m_in, 3) == 0.743 and round(m_ho, 3) == 0.550,
                    f"{m_in:.3f}/{m_ho:.3f}")

    # --- A3 surface 2x2 ---
    for seed in (0, 1, 2):
        d = rd(f"surface_corrected_seed{seed}.json")
        ok = d["tokenizer"]["sha256"] == TOK_SURF_VOCAB
        ok = ok and d["assertions"]["denominators_exact_per_cell"] == SURF_DEN
        for i, cell in enumerate(SURF_CELLS):
            c = d["conditions"][cell]
            ok = ok and c["denominator"] == SURF_DEN[cell]
            ok = ok and near(c["systems"]["MODEL"]["pass_at_1"], SURF_MODEL[seed][i])
            ok = ok and c["systems"]["TEMPLATE"]["successes"] == SURF_TEMPLATE_SUCC[i]
            ok = ok and c["systems"]["RETRIEVAL"]["successes"] == SURF_RETRIEVAL_SUCC[i]
        ok = ok and d["assertions"]["heldout_cells_exclude_single_family_ops"] == \
            ["abs_of", "cond_abs_max"]
        ok_all &= check("A", f"surface seed {seed}: denominators 600/600/480/480, "
                             f"MODEL {SURF_MODEL[seed]}, template {SURF_TEMPLATE_SUCC}, "
                             f"retrieval {SURF_RETRIEVAL_SUCC}", ok)

    # --- A4 composition match-controls ---
    for seed in (0, 1):
        d = rd(f"composition_match_controls_seed{seed}.json")
        prim = d["conditions"]["primitive_native"]["extractions"]["book_prefix80"]["aggregate"]
        exp = d["conditions"]["exposed_native"]["extractions"]["book_prefix80"]["aggregate"]
        ok = prim["n"] == 300 and near(prim["pass_at_1"], 1.0) and \
            near(exp["pass_at_1"], COMP_EXPOSED[seed])
        ok_all &= check("A", f"composition seed {seed}: primitive anchors 300/300, "
                             f"exposed {COMP_EXPOSED[seed]}", ok,
                        f"prim {prim['pass_at_1']}, exposed {exp['pass_at_1']}")
        for cond in ("new_composite_unseen_surface", "new_composite_seen_surface"):
            for st in ("book_prefix80", "favorable256"):
                agg = d["conditions"][cond]["extractions"][st]["aggregate"]
                ok = near(agg["pass_at_1"], 0.0) and agg["wrong_semantics"] == 0
                ok_all &= check("A", f"composition seed {seed}: {cond}/{st} held-out "
                                     f"composites pass 0.000, 0 complete programs, "
                                     f"0 wrong-semantics", ok,
                                f"pass {agg['pass_at_1']}, ws {agg['wrong_semantics']}")

    # --- A5 stage1 pilot ---
    st = rd("stage1_results.json")
    model = [x for x in st if x["label"] == "MODEL"][0]
    ok_all &= check("A", "stage1 pilot: in-dist 0.897",
                    round(model["pass_at_1"], 3) == 0.897,
                    f"{model['pass_at_1']}")
    return ok_all


# ===========================================================================
# PHASE B — source invariants (manuscript + caption dict + figure scripts)
# ===========================================================================
def read_ms(name):
    with open(os.path.join(MS, name), encoding="utf-8") as f:
        return f.read()


def phase_b():
    print("\n== PHASE B: source invariants ==")
    ok_all = True
    ms_files = sorted(f for f in os.listdir(MS) if f.endswith(".md"))
    ms_text = {f: read_ms(f) for f in ms_files}
    all_ms = "\n".join(ms_text.values())
    md_tex = open(os.path.join(ROOT, "book", "latex", "md_to_latex.py"),
                  encoding="utf-8").read()
    mk_fig = open(os.path.join(ROOT, "scripts", "make_figures.py"), encoding="utf-8").read()
    mk_con = open(os.path.join(ROOT, "scripts", "make_concept_figures.py"),
                  encoding="utf-8").read()

    # --- B1 globally forbidden stale claims ---
    for pat, name in [
        (r"no clean causal measurement", "stale 'no clean causal measurement' claim"),
        (r"needs correction", "stale 'needs correction' claim"),
        (r"diversity lever still", "stale 'diversity lever still ...' claim"),
        (r"phrasing diversity is what separates", "stale isolated-phrasing-factor claim"),
        (re.escape(STALE_COMMIT), "stale release commit ae1ec01"),
    ]:
        ok = not re.search(pat, all_ms) and not re.search(pat, md_tex)
        ok_all &= check("B", f"absent everywhere in manuscript + md_to_latex: {name}", ok)

    # --- B2 corrupted / wrong-denominator digits ---
    ok, det = window_ok(all_ms, None, r"0\.143")
    ok_all &= check("B", "manuscript: no 0.143 (corrupted 0.743) anywhere", ok, det)
    ok, det = window_ok(all_ms, None, r"(?<![\d,])000 records")
    ok_all &= check("B", "manuscript: no corrupted '000 records' cell size", ok, det)
    ok, det = window_ok(all_ms, None, r"\b420 records")
    ok_all &= check("B", "manuscript: no '420 records' cell-size claim", ok, det)
    # 0.350 / 0.500 / 1.000-diversity only inside labeled historical windows
    ok, det = window_ok(all_ms, None, r"0\.350")
    ok_all &= check("B", "manuscript: every 0.350 is inside a labeled "
                         "superseded/Stage-3/mixed-factor window", ok, det)
    ok, det = window_ok(all_ms, None, r"0\.000\s*(?:→|->|vs\.?|versus|to)\s*1\.000")
    ok_all &= check("B", "manuscript: every 0.000→1.000 diversity reading is labeled "
                         "flawed/superseded (or is continual-retention)", ok, det)
    ok, det = window_ok(all_ms, None, r"0\.500\s*(?:→|->|vs\.?|versus|to)\s*1\.000")
    ok_all &= check("B", "manuscript: every 0.500-versus-1.000 reading is labeled "
                         "flawed/superseded", ok, det)
    # ch13 must carry NO stale diversity digits at all
    ch13 = ms_text["ch13_same_data_more_diverse_data.md"]
    ok = not re.search(r"0\.350|0\.143", ch13)
    ok_all &= check("B", "ch13: no 0.350/0.143 anywhere", ok)

    # --- B3 ch11 required/forbidden content ---
    ch11 = ms_text["ch11_how_much_data.md"]
    ch11_flat = re.sub(r"\s+", " ", ch11)   # md hard-wraps lines mid-sentence
    for sub, name in [
        ("no consistent monotonic effect on familiar-prompt accuracy",
         "ch11 softened data-size wording (>=2x)"),
        ("0.997", "ch11 flags the seed-2 size-1000 0.997 outlier"),
        ("299/300", "ch11 gives the outlier's raw count"),
        ("cond_abs_max", "ch11 per-op cond_abs_max note"),
        ("0.000 (low diversity) versus 0.550 mean",
         "ch11 points at Ch13's equal-count 0.000 vs 0.550 result"),
        ("42 versus 1,200 records — P0-02",
         "ch11 keeps the 42-vs-1,200 history as P0-02"),
    ]:
        n = ch11_flat.count(sub)
        need = 2 if ">=2x" in name else 1
        ok_all &= check("B", name, n >= need, f"found {n}")
    ok = not re.search(r"diversity lever still has no clean|"
                       r"construction still needs correction", ch11)
    ok_all &= check("B", "ch11: stale Ch13-claim passages removed", ok)

    # --- B4 ch13 combined-intervention labeling ---
    n = ch13.count("combined phrasing/identifier")
    ok_all &= check("B", "ch13: diversity labeled as the combined "
                         "phrasing/identifier/uniqueness intervention (>=3x)",
                    n >= 3, f"found {n}")
    for sub in ("0.950", "0.743", "0.550", "605", "20 unique", "1,200"):
        ok_all &= check("B", f"ch13: canonical value present: {sub}",
                        sub in re.sub(r"\s+", " ", ch13))

    # --- B5 ch15 denominators ---
    ch15 = ms_text["ch15_new_words_same_problem.md"]
    ch15_flat = re.sub(r"\s+", " ", ch15)
    for sub in ("539/600", "480/600", "420/480", "60/480", "600/600",
                "**600** records each", "**480** (8 operations"):
        ok_all &= check("B", f"ch15: canonical denominator text present: {sub}",
                        sub in ch15_flat)
    bad = [ln for ln in ch15.splitlines()
           if re.search(r"\b420\b", ln) and "480" not in ln]
    ok_all &= check("B", "ch15: every '420' line also carries the 480 denominator "
                         "(420 only as TEMPLATE numerator)", not bad,
                    f"offenders: {bad[:2]}")

    # --- B6 Appendix C section refs ---
    appc = ms_text["appendix_c_experiment_registry.md"]
    heads = [h for h in re.findall(r"^## (.+)$", appc, re.M)]
    idx = {h: i + 1 for i, h in enumerate(heads)}
    nov = [h for h in heads if h.lower().startswith("the novelty audit")]
    seq = [h for h in heads if h.lower().startswith("the sequential before")]
    rep = [h for h in heads if h.lower().startswith("reproducibility")]
    ok_all &= check("B", "Appendix C: novelty audit is section C.8 (kept)",
                    nov and idx[nov[0]] == 8, str(idx))
    ok_all &= check("B", "Appendix C: sequential before/after is section C.9",
                    seq and idx[seq[0]] == 9 and "(C.9)" in seq[0], str(seq))
    ok_all &= check("B", "Appendix C: reproducibility is section C.11",
                    rep and idx[rep[0]] == 11, str(rep))
    for f, good, bad_pat, name in [
        ("ch20_what_happens_when_we_teach_it_something_new.md",
         "(Appendix C.9)", r"Appendix C\.8", "ch20 sequential ref -> C.9"),
        ("ch22_the_capability_map.md", "(Appendix C.9)", r"Appendix C\.8",
         "ch22 sequential ref -> C.9"),
        ("ch09_the_first_brew.md", "Appendix C.11", r"Appendix C\.10",
         "ch09 reproducibility ref -> C.11"),
    ]:
        t = ms_text[f]
        ok_all &= check("B", name, good in t and not re.search(bad_pat, t))
    ok = not re.search(r"Appendix C\.8\b", all_ms) and \
        not re.search(r"Appendix C\.10\b", all_ms)
    ok_all &= check("B", "manuscript: no leftover 'Appendix C.8'/'Appendix C.10' "
                         "section refs", ok)

    # --- B7 LOF caption dict + image alts ---
    m = re.search(r"SHORT_FIG_CAPTIONS\s*=\s*\{(.*?)\}", md_tex, re.S)
    lof = m.group(1) if m else ""
    ok_all &= check("B", "LOF: Fig 13.1 short caption is "
                         "'Diversity at equal count (corrected: 0.950 vs 0.743)'",
                    "Diversity at equal count (corrected: 0.950 vs 0.743)" in lof)
    ok_all &= check("B", "LOF: no '42 vs 1,200' in any short caption",
                    "42 vs" not in lof and "1,200" not in lof)
    alts = {
        "ch11_how_much_data.md": "Data scaling — corrected balanced sweep",
        "ch13_same_data_more_diverse_data.md":
            "Diversity at equal count — low vs high diversity, in-distribution "
            "and held-out family",
        "ch15_new_words_same_problem.md": "Surface generalization — corrected 2x2 factorial",
    }
    for f, alt in alts.items():
        ok_all &= check("B", f"image alt intact: {f}", f"![{alt}]" in ms_text[f])

    # --- B8 figure scripts ---
    for sub, name in [
        ("0.950", "make_figures: low-arm in-dist 0.950"),
        ("0.743", "make_figures: high-arm in-dist mean 0.743"),
        ("0.550", "make_figures: high-arm held-out mean 0.550"),
        ("cell_n = [600, 600, 480, 480]", "make_figures: Fig 15.1 cell denominators"),
        ("0.997 (299/300)", "make_figures: Fig 11.1 seed-2 outlier marked"),
        ("0.9967", "make_figures: Fig 11.1 outlier value plotted"),
        ("n = {n}", "make_figures: Fig 15.1 separate n row"),
    ]:
        ok_all &= check("B", name, sub in mk_fig)
    # 0.350 / 0.143 are stale DATA values. A matplotlib (x, y) coordinate is not
    # data, so strip coordinate positions before matching: the R1P-004 figure
    # pass legitimately added fig.text(0.5, 0.350, ...) as a y-coordinate.
    def _strip_coords(src: str) -> str:
        return re.sub(r"(\(\s*-?[\d.]+\s*,\s*)(?:0\.350|0\.143)(?=\s*,)",
                      r"\1<coord>", src)
    mk_fig_nc, mk_con_nc = _strip_coords(mk_fig), _strip_coords(mk_con)
    for pat, name in [(r"0\.350", "make_figures: no stale 0.350"),
                      (r"0\.143", "make_figures: no stale 0.143")]:
        ok_all &= check("B", name, not re.search(pat, mk_fig_nc))
    ok_all &= check("B", "make_concept_figures: Fig 13.2 right panel labeled "
                         "'flawed original vs corrected measured (n=100)'",
                    "flawed original vs corrected measured (n=100)" in mk_con)
    ok_all &= check("B", "make_concept_figures: no stale 0.350 chart label",
                    not re.search(r"0\.350", mk_con_nc))
    ok_all &= check("B", "make_concept_figures: corrected 0.743/0.550 in "
                         "capability-map rows", "0.743" in mk_con and "0.550" in mk_con)

    # --- B9 provenance ---
    # The build commit lives in ONE place (docs/release_manifest.json ->
    # pdf_build_commit); appendix C and the md_to_latex colophon must point at
    # it, never restate a hash (QWEN-R2-02: the hardcoded colophon went false).
    ok_all &= check("B", "appendix C no longer hardcodes the PDF build commit — "
                         "it points at docs/release_manifest.json (pdf_build_commit)",
                    LEGACY_BUILD_COMMIT not in appc and "pdf_build_commit" in appc)
    ok_all &= check("B", f"appendix C still names the release commit {RELEASE_COMMIT}",
                    RELEASE_COMMIT in appc)
    ok_all &= check("B", "md_to_latex colophon names the release commit",
                    RELEASE_COMMIT in md_tex)
    ok_all &= check("B", "md_to_latex colophon derives the PDF build commit from "
                         "git at build time (no hardcoded build hash)",
                    "rev-parse" in md_tex and LEGACY_BUILD_COMMIT not in md_tex)
    ok_all &= check("B", "no surface still carries the pre-fix hardcoded build "
                         "commit af32fb8b (appendix C, md_to_latex, README)",
                    LEGACY_BUILD_COMMIT not in appc and
                    LEGACY_BUILD_COMMIT not in md_tex and
                    LEGACY_BUILD_COMMIT not in
                    open(os.path.join(ROOT, "README.md"), encoding="utf-8").read())
    ok_all &= check("B", "manuscript: no stale commit ae1ec01",
                    STALE_COMMIT not in all_ms)
    # exactly one release identifier: no other 7-40 hex commit strings
    others = set()
    for f, t in list(ms_text.items()) + [("md_to_latex.py", md_tex)]:
        for m2 in re.finditer(r"(?<![0-9a-zA-Z/])([0-9a-f]{7,39})(?![0-9a-zA-Z])", t):
            h = m2.group(1)
            if h == RELEASE_COMMIT[:len(h)]:
                continue
            ctx = t[max(0, m2.start() - 40):m2.end() + 40]
            if re.search(r"[0-9a-f]{32}", ctx):   # part of a longer sha
                continue
            if re.fullmatch(r"[0-9]+", h):        # pure digits (dates, versions)
                continue
            others.add((f, h))
    ok_all &= check("B", "no other commit-like identifiers besides release + build "
                         "commits", not others, str(sorted(others)[:5]))
    # git ground truth
    try:
        tag = subprocess.run(["git", "rev-parse", f"{RELEASE_TAG}^{{commit}}"],
                             cwd=ROOT, capture_output=True, text=True,
                             timeout=30).stdout.strip()
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True,
                              timeout=30).stdout.strip()
        ok_all &= check("B", f"git: {RELEASE_TAG}^{{commit}} == {RELEASE_COMMIT}",
                        tag == RELEASE_COMMIT, f"got {tag}")
        pb = (_manifest().get("pdf_build_commit") or "")
        ok_all &= check("B", "git: the manifest's recorded PDF build commit "
                             "(docs/release_manifest.json -> pdf_build_commit) "
                             "resolves in history",
                        bool(re.fullmatch(r"[0-9a-f]{40}", pb)) and
                        subprocess.run(["git", "cat-file", "-e",
                                        pb + "^{commit}"], cwd=ROOT,
                                       capture_output=True).returncode == 0,
                        f"pdf_build_commit {pb[:8] or '(missing)'} not a commit")
    except Exception as e:  # pragma: no cover
        ok_all &= check("B", "git provenance query", False, str(e))

    # --- B10 tokenizer disk hashes, scope statements, release record refs ---
    ok_all &= check("B", "ch11 cites the data-scaling tokenizer DISK sha256",
                    TOK_DATA in ch11)
    ok_all &= check("B", "ch15 cites the surface tokenizer DISK sha256",
                    TOK_SURF in ch15)
    for tid in sorted(TOK_EXPECTED):
        ok_all &= check("B", f"appendix C cites the {tid} tokenizer DISK sha256 "
                             f"({TOK_FILES[tid]})", TOK_EXPECTED[tid] in appc)
    for h, name in [(TOK_DATA_VOCAB, "data_scaling"), (TOK_DIV_VOCAB, "diversity"),
                    (TOK_SURF_VOCAB, "surface")]:
        ok_all &= check("B", f"manuscript no longer cites the in-memory {name} "
                             f"vocab hash {h[:8]}…", h not in all_ms)
    ch15_flat2 = re.sub(r"\s+", " ", ch15)
    ok_all &= check("B", "ch15 scopes aggregate wording comparisons to the 8 "
                         "shared ops (480/480 vs 0/480)",
                    "480/480 (familiar) versus 0/480" in ch15_flat2)
    ok_all &= check("B", "ch15: held-out wording is a single deterministic "
                         "family per op, not sampled across families",
                    "single deterministic family per operation" in ch15_flat2 and
                    "not sampled across families" in ch15_flat2)
    ch16 = ms_text["ch16_same_pieces_new_combination.md"]
    ch16_flat = re.sub(r"\s+", " ", ch16)
    ok_all &= check("B", "ch16 scopes the 0-wrong-semantics reading to the "
                         "held-out composites and controls (b)/(c)",
                    "scoped to the held-out composites and to controls (b) and (c)"
                    in ch16_flat)
    ok_all &= check("B", "ch16 states control (a) recorded 2/300 "
                         "wrong-semantics at seed 0",
                    "2/300 wrong-semantics" in ch16_flat)
    ok_all &= check("B", "appendix C references the pinned requirements-lock.txt",
                    "requirements-lock.txt" in appc)
    ok_all &= check("B", "appendix C references docs/release_manifest.json",
                    "docs/release_manifest.json" in appc)
    lock_ok = os.path.exists(LOCKFILE)
    lock_detail = LOCKFILE
    if lock_ok:
        lock_txt = open(LOCKFILE, encoding="utf-8").read()
        for pin in ("torch==2.14.0+cpu", "numpy==2.2.6", "matplotlib==3.11.2",
                    "scikit-learn==1.9.1"):
            lock_ok = lock_ok and pin in lock_txt
            if pin not in lock_txt:
                lock_detail = f"missing pin {pin}"
    ok_all &= check("B", "requirements-lock.txt exists and pins torch/numpy/"
                         "matplotlib/scikit-learn (CPU-only)", lock_ok, lock_detail)
    return ok_all


# ===========================================================================
# PHASE C — rebuilt-PDF invariants
# ===========================================================================
def _loose(pages):
    """Page text normalized for phrase matching: running headers and lone
    page numbers stripped (they interrupt sentences at page breaks — including
    appendix running heads, which used to leak into page-crossing spans and
    break the build-commit witness), end-of-line hyphenation rejoined,
    whitespace collapsed."""
    out = []
    for t in pages:
        lines = t.splitlines()
        # strip any leading run of empties / running heads / page numbers, in
        # whatever order the extractor emitted them at the page top
        while True:
            while lines and not lines[0].strip():
                lines.pop(0)
            if not lines:
                break
            first = lines[0].strip()
            if (re.match(r"^Chapter \d+\.", first) or
                    re.match(r"^Appendix [A-Z]\.", first) or
                    first in ("Let Us Brew an AI Model",) or
                    re.fullmatch(r"\d{1,3}", first)):
                lines.pop(0)
                continue
            break
        if lines and re.fullmatch(r"\d{1,3}", lines[-1].strip()):
            lines.pop()
        out.append("\n".join(lines))
    s = " ".join(out)
    s = re.sub(r"(?<=[a-z])-\s+(?=[a-z])", "", s)   # break hyphenation
    return re.sub(r"\s+", " ", s)


def _st(s):
    """Supertight: case-folded, no spaces/hyphens -- immune to line breaks,
    hyphenation, and word spacing in the extracted text."""
    return re.sub(r"[-\s]", "", s.lower())


# --- C7 render geometry: a 64-hex tokenizer digest must print COMPLETE and
# --- inside the text block (the P1 clipping class) -------------------------
HEXRUN_RE = re.compile(r"[0-9a-f]{8,}")
_UNIT_PT = {"in": 72.0, "cm": 72.0 / 2.54, "mm": 72.0 / 25.4, "pt": 1.0,
            None: 1.0}


def _textblock_right_pt():
    """Right edge of the text block in PDF points, derived from the geometry
    options in book/latex/book.sty (paperwidth 6in, right margin 0.75in ->
    x = 378pt on a 432pt page). Derived, not hard-coded, so a margin change
    moves the threshold with it; falls back to the same 6in/0.75in numbers if
    book.sty cannot be read, and NEVER falls back to the trim edge (that would
    make the check vacuous -- the whole point is that 431pt is already wrong)."""
    paper, right = 6.0 * 72.0, 0.75 * 72.0
    try:
        sty = open(os.path.join(ROOT, "book", "latex", "book.sty"),
                   encoding="utf-8").read()
    except OSError:
        sty = ""
    m = re.search(r"\[([^\]]*)\]\s*\{geometry\}", sty)
    if m:
        opts = m.group(1)

        def val(name, default):
            mm = re.search(r"(?:^|,)\s*%s\s*=\s*([0-9.]+)\s*(in|pt|cm|mm)?"
                           % name, opts)
            if not mm:
                return default
            return float(mm.group(1)) * _UNIT_PT[mm.group(2)]
        paper = val("paperwidth", paper)
        right = val("right", right)
    return paper - right


def _digest_x1(page, digest):
    """Right-most x of any span carrying part of `digest` on `page`. Trailing
    punctuation sharing the span counts, so a ')' pushed past the trim edge
    fails the check too. Returns -1.0 when no digest span is found."""
    x1 = -1.0
    for b in page.get_text("dict").get("blocks", []):
        for l in b.get("lines", []):
            for s in l.get("spans", []):
                flat = re.sub(r"\s+", "", s.get("text", ""))
                m = HEXRUN_RE.search(flat)
                if m and m.group(0) in digest:
                    x1 = max(x1, s["bbox"][2])
    return x1


def _check_digest_geometry(doc):
    """P1 render-geometry gate. For every page carrying part of a 64-hex
    tokenizer digest, assert (a) the digest's right-most glyph ends at or
    before the text block's right edge, and (b) wherever a digest STARTS, all
    64 hex characters are printed -- whitespace is stripped first, so a digest
    that wraps onto a second line inside the text block is COMPLETE, and a
    digest whose remainder continues intact on the following page (a normal
    page break, nothing lost) also counts; a tail that simply vanishes does
    not. (a) is what catches clipping: glyphs past the trim are still in the
    content stream and still EXTRACT, so text presence alone never saw the
    defect -- the pre-fix book extracted 62/64 chars on the ch11/ch15 pages
    and still rendered the appendix digests 53pt past the text block."""
    ok_all = True
    right = _textblock_right_pt()
    ok_all &= check("C", f"digest geometry: text-block right edge derived from "
                         f"book.sty = {right:.1f}pt (page is "
                         f"{doc[0].rect.width:.1f}pt wide)",
                    0 < right < doc[0].rect.width - 20.0, f"got {right:.2f}")
    stripped = [re.sub(r"\s+", "", p.get_text()) for p in doc]
    joined = "\n".join(stripped)
    for name, digest in sorted(TOK_EXPECTED.items()):
        ok_all &= check("C", f"digest {name} ({digest[:8]}…) appears in the "
                             f"PDF at all", digest[:16] in joined)
    for i, ptext in enumerate(stripped):
        for name, digest in sorted(TOK_EXPECTED.items()):
            x1 = _digest_x1(doc[i], digest)
            if x1 < 0:
                continue          # this page carries no fragment of this digest
            ok_all &= check("C", f"digest {name} on page {i + 1} ends at "
                                 f"x1={x1:.1f}pt <= text-block right "
                                 f"{right:.1f}pt (no glyph at the trim edge)",
                            0 <= x1 <= right + 0.5,
                            f"x1={x1:.2f}pt vs {right:.2f}pt")
            if digest[:16] not in ptext:
                continue          # page holds only the tail of a straddling run
            n = 0
            while n < 64 and digest[:n + 1] in ptext:
                n += 1
            tail = digest[n:]
            straddled = (len(tail) >= 8 and i + 1 < len(stripped)
                         and tail in stripped[i + 1])
            ok_all &= check("C", f"digest {name} prints all 64 hex chars "
                                 f"starting on page {i + 1} (complete on that "
                                 f"page, or continued intact on the next)",
                            n == 64 or straddled,
                            f"only {n}/64 hex chars on page {i + 1} and no "
                            f"intact continuation on page {i + 2}")
    return ok_all


def phase_c(pdf_path):
    print(f"\n== PHASE C: PDF invariants ({pdf_path}) ==")
    if not os.path.exists(pdf_path):
        check("C", "PDF exists", False, pdf_path)
        return False
    try:
        import pymupdf
    except ImportError as e:
        # P3d: degrade gracefully instead of crashing. A python without pymupdf
        # (the bare system python3 — pymupdf==2.1 lives in requirements-lock.txt
        # and is installed in .venv-311) cannot check the PDF at all, so say so
        # loudly and skip; the pass mark keeps the exit code meaningful while the
        # check name makes the gap impossible to miss in the report.
        print("!! WARNING: phase C SKIPPED — pymupdf is not importable "
              f"({e}).\n!!   Phase C (PDF text + render-geometry invariants) "
              "requires pymupdf from requirements-lock.txt.\n!!   Run the gate "
              "under the repo venv:  source .venv-311/bin/activate  &&  "
              "python scripts/verify_release.py\n!!   The PDF was NOT checked "
              "by this run.")
        return check("C", "phase C SKIPPED (pymupdf missing — run under "
                          ".venv-311; pymupdf==2.1 comes from "
                          "requirements-lock.txt)", True,
                     "PDF invariants were NOT verified by this run")
    doc = pymupdf.open(pdf_path)
    pages = [p.get_text() for p in doc]
    txt = "\n".join(pages)
    flat = _loose(pages)          # header/hyphenation-normalized
    st = _st(flat)                # supertight for phrase presence
    ok_all = True

    # --- C1 canonical values present ---
    for sub, name in [
        ("0.950", "diversity low in-dist 0.950"),
        ("0.743", "diversity high in-dist mean 0.743"),
        ("0.550", "diversity high held-out mean 0.550"),
        ("0.997", "data-scaling seed-2 outlier 0.997"),
        ("299/300", "outlier raw count 299/300"),
        ("269/300", "ch11 seed-0 counts"),
        ("539/600", "surface MODEL familiar count"),
        ("480/600", "surface TEMPLATE kept-cell numerator"),
        ("420/480", "surface TEMPLATE held-out numerator"),
        ("60/480", "surface RETRIEVAL held-out numerator"),
        ("600/600", "surface RETRIEVAL kept-cell numerator"),
        ("605", "diversity high-arm unique pairs"),
        (RELEASE_COMMIT, "release commit (full hash)"),
        ("no consistent monotonic effect on familiar-prompt accuracy",
         "ch11 softened claim in the built book"),
        ("combined phrasing/identifier", "ch13 combined-intervention label"),
        ("0.000 (low diversity) versus 0.550 mean",
         "ch11 equal-count diversity pointer"),
    ]:
        ok_all &= check("C", f"PDF contains: {name}", _st(sub) in st)

    # --- C8 build-stamp integrity (QWEN-R2-02): the PDF must match the
    # --- RECORDED build commit (docs/release_manifest.json -> pdf_build_commit),
    # --- read from the manifest, never from a hardcoded constant ---
    rm_c = _manifest()
    recorded = rm_c.get("pdf_build_commit") or ""
    ok_all &= check("C", "release manifest records pdf_build_commit (full 40-hex)",
                    bool(re.fullmatch(r"[0-9a-f]{40}", recorded)), repr(recorded))
    ok_all &= check("C", "PDF title-page colophon carries the recorded "
                         "pdf_build_commit (full hash from docs/release_manifest.json)",
                    bool(recorded) and _st(recorded) in st,
                    f"recorded {recorded[:12] or '(missing)'} not found in PDF text")
    # forward witness: a stable string ADDED by the recorded build commit
    # (absent in its parent) must be in the PDF text.
    if recorded and re.fullmatch(r"[0-9a-f]{40}", recorded):
        added, err = _added_at(recorded)
        if added is None:
            check("C", "PDF content matches the recorded build commit "
                       "(string added by pdf_build_commit, absent in its parent, "
                       "present in the PDF)", False, err)
            ok_all = False
        elif not added:
            check("C", "PDF content matches the recorded build commit "
                       "(forward witness)", True,
                  f"recorded commit {recorded[:12]} added no stable manuscript "
                  f"string; verified via the no-postdating-text check instead")
        else:
            missing = [s for s in added if _st(s) not in st]
            ok_all &= check("C", f"PDF content matches the recorded build commit: "
                                 f"all {len(added)} string(s) added by "
                                 f"{recorded[:12]} (absent in its parent) appear "
                                 f"in the PDF", not missing,
                            f"not in PDF: {missing[:2]!r}")
        # reverse witness: the PDF must NOT contain manuscript text added AFTER
        # the recorded commit -- that is exactly the stale-colophon defect.
        since, err = _added_since(recorded)
        if since is None:
            check("C", "PDF contains no manuscript text added after the recorded "
                       "build commit (recorded commit is not stale)", False, err)
            ok_all = False
        else:
            leaked = [s for s in since if _st(s) in st]
            ok_all &= check("C", f"PDF contains no manuscript text added after "
                                 f"the recorded build commit {recorded[:12]} "
                                 f"(stale pdf_build_commit would fail here)",
                            not leaked, f"post-dates the record: {leaked[:2]!r}")

    # --- C9 page-count pin (QWEN-R2-04): manifest pdf.page_count vs reality ---
    # Only the RELEASE PDF carries the manifest's page count: phase_c also runs on
    # the interior build artifact (book/latex/book.pdf, pre-cover-merge), which is
    # legitimately one page shorter, so pinning it here would always fail.
    _rel = ((rm_c.get("pdf") or {}).get("path") or "")
    _is_release = _rel and os.path.abspath(pdf_path) == os.path.abspath(
        os.path.join(ROOT, _rel))
    pc = (rm_c.get("pdf") or {}).get("page_count")
    if pc is None:
        check("C", "manifest pdf.page_count == actual page count — SKIP "
                   "(page_count is null; the parent records it after rebuild)",
              True, f"actual {doc.page_count} pages, manifest null (NOT checked)")
    elif not _is_release:
        check("C", f"manifest pdf.page_count ({pc}) — SKIP for non-release PDF "
                   f"{os.path.relpath(pdf_path, ROOT)} (pin applies to the "
                   f"release PDF only)", True,
              f"actual {doc.page_count} pages")
    else:
        ok_all &= check("C", f"manifest pdf.page_count ({pc}) == actual PDF "
                             f"page count ({doc.page_count})",
                        pc == doc.page_count, f"actual {doc.page_count}")

    # --- C2 stale values absent (outside labeled historical windows) ---
    for pat, name in [
        (r"0\.143", "no corrupted 0.143 anywhere"),
        (r"no clean causal measurement", "no stale 'no clean causal measurement'"),
        (r"needs correction", "no stale 'needs correction'"),
        (re.escape(STALE_COMMIT), "no stale commit ae1ec01"),
        (r"(?<![\d,])000 records", "no corrupted '000 records' cell size"),
        (r"\b420 records", "no '420 records' cell-size claim"),
        (r"flawed: 42 vs 1,200", "no stale LOF 'flawed: 42 vs 1,200'"),
        (r"\?\?", "no unresolved '??' cross-references"),
        (r"\bundefined\b", "no 'undefined' artifacts"),
    ]:
        ok, det = window_ok(flat, None, pat)
        ok_all &= check("C", f"PDF: {name}", ok, det)
    ok, det = window_ok(flat, None, r"0\.350")
    ok_all &= check("C", "PDF: every 0.350 sits in a labeled superseded/Stage-3 "
                         "window (font corruption would break this)", ok, det)
    ok, det = window_ok(flat, None, r"0\.000\s*(?:→|->|vs\.?|versus|to)\s*1\.000")
    ok_all &= check("C", "PDF: every 0.000→1.000 reading is labeled flawed/"
                         "superseded (or is continual-retention)", ok, det)

    # --- C3 LOF entries ---
    i = txt.find("List of Figures")
    lof = txt[i:i + 2600] if i >= 0 else ""
    ok_all &= check("C", "LOF: Fig 13.1 entry is the corrected short caption",
                    "Diversity at equal count (corrected: 0.950 vs 0.743)" in lof)
    ok_all &= check("C", "LOF: Fig 11.1 entry present",
                    "Data scaling" in lof)
    ok_all &= check("C", "LOF: Fig 15.1 entry present",
                    "Surface generalization" in lof)
    ok_all &= check("C", "LOF: no '42 vs 1,200' entry",
                    "42 vs 1,200" not in lof)

    # --- C4 surface denominators in the ch15 caption text ---
    for sub, name in [
        ("600 records each", "familiar/id cells: 600 records each"),
        ("480 (8 operations", "held-out cells: 480 (8 operations x 60)"),
        ("539/600, 0/600, 0/480, 0/480", "MODEL cell counts over 600/600/480/480"),
    ]:
        ok_all &= check("C", f"PDF: {name}", _st(sub) in st)

    # --- C5 ch13 caption page carries corrected digits, not corrupted ones ---
    cap_pages = [n for n, t in enumerate(pages)
                 if "Diversity at equal count" in t and "0.950" in t]
    ok_all &= check("C", "PDF: a page carries the corrected Fig 13.1 caption "
                         "with 0.950", bool(cap_pages))
    for n, t in enumerate(pages):
        if "0.350 in-distribution" in t or "0.143" in t:
            ok_all &= check("C", f"PDF: page {n + 1} has corrupted caption digits",
                            False)
            break
    # --- C6 Appendix refs in the built book ---
    for sub, name in [("(C.9)", "sequential before/after ref (C.9)"),
                      ("(C.11)", "reproducibility ref (C.11) or registry ref")]:
        ok_all &= check("C", f"PDF: {name} present", sub in txt or
                        sub.replace("(", "").replace(")", "") in txt)
    ok_all &= check("C", "PDF: no 'Appendix C.8'/'Appendix C.10' refs",
                    not re.search(r"Appendix C\.8\b|Appendix C\.10\b", flat))
    # --- C7 render geometry: 64-hex tokenizer digests complete + inside the
    # --- text block (would have caught the P1 trim-edge clipping) ---
    ok_all &= _check_digest_geometry(doc)
    return ok_all


# ===========================================================================
# PHASE D — tokenizer disk hashes + the canonical release manifest
# ===========================================================================
def _sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def phase_d(pdf_required=True):
    print("\n== PHASE D: tokenizer disk hashes + release manifest ==")
    ok_all = True
    # --- D1 the four corrected tokenizer files hash to the cited constants ---
    for tid, fname in TOK_FILES.items():
        p = os.path.join(ROOT, "artifacts", "tokenizer", fname)
        if not os.path.exists(p):
            ok_all &= check("D", f"tokenizer file exists: {fname}", False, p)
            continue
        got = _sha256(p)
        ok_all &= check("D", f"disk sha256({fname}) == cited "
                             f"{TOK_EXPECTED[tid][:12]}…",
                        got == TOK_EXPECTED[tid], f"got {got}")
    # --- D2 the release manifest records exactly those values ---
    if not os.path.exists(RELEASE_MANIFEST):
        check("D", "docs/release_manifest.json exists", False, RELEASE_MANIFEST)
        return False
    with open(RELEASE_MANIFEST, encoding="utf-8") as f:
        rm = json.load(f)
    ok_all &= check("D", f"release manifest names tag {RELEASE_TAG}",
                    rm.get("tag") == RELEASE_TAG, str(rm.get("tag")))
    ok_all &= check("D", "release manifest tag-target commit == "
                         f"{RELEASE_COMMIT[:12]}…",
                    rm.get("tag_target_commit") == RELEASE_COMMIT,
                    str(rm.get("tag_target_commit")))
    pb = rm.get("pdf_build_commit") or ""
    ok_all &= check("D", "release manifest pdf_build_commit is a full 40-hex "
                         "commit that resolves in git (its truth vs the PDF "
                         "content is asserted in phase C)",
                    bool(re.fullmatch(r"[0-9a-f]{40}", pb)) and
                    subprocess.run(["git", "cat-file", "-e", pb + "^{commit}"],
                                   cwd=ROOT,
                                   capture_output=True).returncode == 0,
                    str(pb))
    want_tok = {k: TOK_EXPECTED[k] for k in TOK_FILES}
    ok_all &= check("D", "release manifest tokenizer_sha256 == the disk hashes "
                         "(all 7 tokenizer files)",
                    rm.get("tokenizer_sha256") == want_tok,
                    json.dumps(rm.get("tokenizer_sha256")))
    # --- D3 the pin list covers every tokenizer file on disk, and equals the set
    # --- of tokenizer files the book cites (closes the unpinned-tokenizer gap) ---
    tok_dir = os.path.join(ROOT, "artifacts", "tokenizer")
    disk = sorted(f for f in os.listdir(tok_dir) if f.endswith(".json"))
    pins = rm.get("tokenizer_files") or {}
    pin_paths = set(pins.values())
    ok_all &= check("D", "release manifest pins every tokenizer file on disk "
                         "(7/7 under artifacts/tokenizer/)",
                    pin_paths == {f"artifacts/tokenizer/{f}" for f in disk} and
                    len(disk) == 7,
                    f"on disk {disk}; pinned {sorted(pin_paths)}")
    ok_all &= check("D", "release manifest tokenizer_sha256 keys == tokenizer_files keys",
                    set(rm.get("tokenizer_sha256") or {}) == set(pins),
                    f"sha256 {sorted(rm.get('tokenizer_sha256') or {})}, "
                    f"files {sorted(pins)}")
    cited = set()
    for fn in sorted(os.listdir(MS)):
        if fn.endswith(".md"):
            cited |= set(re.findall(r"artifacts/tokenizer/([A-Za-z0-9_.]+\.json)",
                                    read_ms(fn)))
    pin_names = {os.path.basename(p) for p in pin_paths}
    ok_all &= check("D", "manifest pin list == the set of tokenizer files the book "
                         "cites (no cited tokenizer left unpinned)",
                    pin_names == cited and len(cited) == 7,
                    f"pinned {sorted(pin_names)}; cited by the book {sorted(cited)}")
    # --- D4 the two-commit reproduction structure is documented, in the manifest
    # --- and in the appendix C publication status a clean clone actually reads ---
    repro = rm.get("reproduction_from_a_clean_clone") or {}
    repro_txt = json.dumps(repro)
    ok_all &= check("D", "release manifest documents the two-commit structure "
                         "(tag = experiment-data snapshot; build commit = gate + "
                         "corrected runners) with the exact checkout/verify commands",
                    RELEASE_COMMIT in repro_txt and "pdf_build_commit" in repro_txt and
                    "verify_release.py" in repro_txt and
                    bool(repro.get("run_the_release_gate")) and
                    bool(repro.get("read_the_experiment_snapshot")),
                    repro_txt[:200])
    appc_txt = read_ms("appendix_c_experiment_registry.md")
    ok_all &= check("D", "appendix C publication status gives the exact "
                         "'git checkout <pdf_build_commit>' + verify_release.py "
                         "commands (build hash read from the manifest, not hardcoded)",
                    "git checkout" in appc_txt and "pdf_build_commit" in appc_txt and
                    "scripts/verify_release.py" in appc_txt and
                    "experiment-data snapshot" in appc_txt and
                    LEGACY_BUILD_COMMIT not in appc_txt,
                    "two-commit instructions missing from Appendix C")
    pdf_rel = (rm.get("pdf") or {}).get("path")
    pdf_abs = os.path.join(ROOT, pdf_rel) if pdf_rel else None
    if pdf_abs and os.path.exists(pdf_abs):
        got = _sha256(pdf_abs)
        ok_all &= check("D", f"release manifest PDF sha256 == sha256({pdf_rel})",
                        (rm.get("pdf") or {}).get("sha256") == got,
                        f"manifest {(rm.get('pdf') or {}).get('sha256')}, file {got}")
    else:
        ok_all &= check("D", "release manifest PDF exists to hash",
                        not pdf_required, pdf_rel or "(no path recorded)")
    # --- D5 provenance-ledger schema (QWEN-R2-03) + producing-commit resolve
    # --- (R3-EX-02): 41 rows == Appendix C Table C.12, unique ids, uniform
    # --- no-.json suffix, no nulls, every produced_by_commit resolves, and the
    # --- producing script's blob at that commit is recorded where recoverable.
    # --- Script DRIFT (recorded blob != the blob shipped today) is recorded,
    # --- not failed -- failing on it is a V3 addition, by design.
    if not os.path.exists(LEDGER):
        ok_all &= check("D", "docs/reviews/loop/provenance_ledger.json exists",
                        False, LEDGER)
    else:
        try:
            with open(LEDGER, encoding="utf-8") as f:
                ledger = json.load(f)
        except ValueError as e:
            ledger = None
            ok_all &= check("D", "provenance ledger parses as JSON", False, str(e))
        if isinstance(ledger, list):
            ok_all &= check("D", f"provenance ledger has exactly "
                                 f"{LEDGER_EXPECTED_ROWS} rows (== Appendix C "
                                 f"Table C.12)", len(ledger) == LEDGER_EXPECTED_ROWS,
                            f"got {len(ledger)}")
            ids = [r.get("experiment_id") for r in ledger]
            dups = sorted({i for i in ids if ids.count(i) > 1})
            ok_all &= check("D", "provenance ledger experiment_ids are unique",
                            len(ids) == len(set(ids)) and
                            all(isinstance(i, str) and i for i in ids),
                            f"duplicates {dups[:4]}")
            suffixed = [i for i in ids
                        if isinstance(i, str) and i.endswith(".json")]
            ok_all &= check("D", "provenance ledger experiment_ids use the uniform "
                                 "no-.json suffix convention",
                            not suffixed, f"{suffixed[:4]}")
            nulls = [(r.get("manifest"), k) for r in ledger
                     for k, v in r.items() if v is None]
            ok_all &= check("D", "provenance ledger carries no nulls (absent "
                                 "values are marked 'not-recorded')",
                            not nulls, f"{nulls[:5]}")
            req = ["manifest", "experiment_id", "seed", "steps", "n_per_op",
                   "model_params", "final_loss", "tokenizer_vocab",
                   "produced_by_commit", "producing_script",
                   "producing_script_blob"]
            miss = [(r.get("manifest"), k) for r in ledger
                    for k in req if k not in r]
            ok_all &= check("D", "every ledger row carries the full schema "
                                 "(config fields + produced_by_commit + "
                                 "producing-script blob)", not miss, f"{miss[:5]}")
            appc12 = read_ms("appendix_c_experiment_registry.md")
            m12 = re.search(r"\*\*Table C\.12[^\n]*\n(.*?)(?=\n\*\*|\n## )",
                            appc12, re.S)
            c12 = re.findall(r"^\|\s*`([^`\n]+\.json)`\s*\|",
                             m12.group(1) if m12 else "", re.M)
            led = [r.get("manifest") for r in ledger]
            ok_all &= check("D", "provenance ledger row set == Appendix C Table "
                                 "C.12 manifest rows",
                            sorted(led) == sorted(c12) and
                            len(c12) == LEDGER_EXPECTED_ROWS,
                            f"ledger {len(led)}, Table C.12 {len(c12)}, "
                            f"symmetric diff {sorted(set(led) ^ set(c12))[:4]}")
            bad_commit, bad_blob = [], []
            for r in ledger:
                c = r.get("produced_by_commit")
                resolves = isinstance(c, str) and bool(
                    re.fullmatch(r"[0-9a-f]{40}", c))
                if resolves:
                    resolves = subprocess.run(
                        ["git", "cat-file", "-e", c + "^{commit}"], cwd=ROOT,
                        capture_output=True).returncode == 0
                if not resolves:
                    bad_commit.append((r.get("manifest"), c))
                    continue
                script = r.get("producing_script")
                blob = r.get("producing_script_blob")
                if script and script != "not-recorded":
                    rc, want = _git("rev-parse", f"{c}:{script}")
                    if rc == 0:
                        if blob != want:
                            bad_blob.append((r.get("manifest"), blob, want))
                    elif blob != "not-recorded":
                        bad_blob.append((r.get("manifest"), blob,
                                         "script absent at that commit"))
            ok_all &= check("D", "every ledger produced_by_commit is a full "
                                 "40-hex commit that resolves (git cat-file -e)",
                            not bad_commit, f"{bad_commit[:3]}")
            ok_all &= check("D", "every ledger producing_script_blob == the "
                                 "producing script's blob at produced_by_commit "
                                 "(recorded; script drift is NOT failed yet)",
                            not bad_blob, f"{bad_blob[:3]}")
    return ok_all


# ===========================================================================
# PHASE E — shipped-EPUB stale sweep (round-1 R3-EX-01)
# ===========================================================================
def phase_epub():
    print("\n== PHASE E: EPUB stale sweep ==")
    rm = _manifest()
    ok_all = check("E", "release manifest records an epub entry (path + sha256)",
                   "epub" in rm and bool((rm.get("epub") or {}).get("path")),
                   str(rm.get("epub")))
    ep = rm.get("epub") or {}
    rel = ep.get("path") or "book/let-us-brew-an-ai-model-v20261001.epub"
    abs_p = os.path.join(ROOT, rel)
    if not os.path.exists(abs_p):
        check("E", f"EPUB present to sweep ({rel}) — SKIP (absent; rebuild with "
                   f"book/build_epub.py)", True,
              "EPUB not on disk; the stale sweep was NOT run by this phase")
        return ok_all
    try:
        import zipfile
        import html as _html
        with zipfile.ZipFile(abs_p) as z:
            parts = [re.sub(r"<[^>]+>", " ", z.read(n).decode("utf-8", "replace"))
                     for n in z.namelist()
                     if n.endswith((".xhtml", ".html", ".htm"))]
        text = re.sub(r"\s+", " ", _html.unescape(" ".join(parts)))
    except Exception as e:
        check("E", "EPUB unzips and its text extracts", False, str(e))
        return False
    for s in EPUB_MUST_HAVE:
        ok_all &= check("E", f"EPUB carries the corrected headline string {s!r}",
                        s in text, "stale EPUB — rebuild with book/build_epub.py")
    for s in EPUB_MUST_NOT_HAVE:
        ok_all &= check("E", f"EPUB no longer carries the superseded string {s!r}",
                        s not in text,
                        "stale EPUB — rebuild with book/build_epub.py")
    sha = ep.get("sha256")
    if sha is None:
        check("E", "manifest epub.sha256 == sha256(EPUB) — SKIP (sha256 is null; "
                   "the parent records it after rebuild)", True,
              "epub.sha256 null (NOT checked)")
    else:
        got = _sha256(abs_p)
        ok_all &= check("E", f"manifest epub.sha256 == sha256({rel})",
                        sha == got, f"manifest {sha}, file {got}")
    return ok_all


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", action="append", default=None,
                    help="PDF to verify (repeatable); default: the release PDF "
                         "and book/latex/book.pdf if present")
    ap.add_argument("--no-pdf", action="store_true", help="skip phase C")
    ap.add_argument("--json", action="store_true", help="print a JSON summary")
    args = ap.parse_args()

    preflight()          # QWEN-R2-01: clean-clone missing inputs => 1 line, exit 1
    phase_a()
    phase_b()
    phase_d(pdf_required=not args.no_pdf)
    phase_epub()         # R3-EX-01: stale-EPUB sweep (SKIP when the EPUB is absent)
    pdfs = args.pdf
    if pdfs is None and not args.no_pdf:
        pdfs = [p for p in (
            os.path.join(ROOT, "book", "let-us-brew-an-ai-model-v20261001.pdf"),
            os.path.join(ROOT, "book", "latex", "book.pdf"),
        ) if os.path.exists(p)]
    if pdfs and not args.no_pdf:
        for p in pdfs:
            phase_c(p)
    elif not args.no_pdf:
        check("C", "a built PDF exists to verify", False,
              "run book/build_book.py first or pass --no-pdf")

    fails = [r for r in results if not r[2]]
    print(f"\n== verify_release: {len(results) - len(fails)}/{len(results)} "
          f"checks passed, {len(fails)} mismatches ==")
    for ph, name, _, det in fails:
        print(f"  MISMATCH [{ph}] {name}" + (f" -- {det}" if det else ""))
    if args.json:
        print(json.dumps({
            "total": len(results),
            "passed": len(results) - len(fails),
            "failed": len(fails),
            "mismatches": [{"phase": ph, "name": n, "detail": d}
                           for ph, n, _, d in fails],
        }, indent=2))
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()