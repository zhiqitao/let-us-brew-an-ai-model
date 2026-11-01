#!/usr/bin/env python3
"""md_to_latex.py -- convert the brew-book manuscript chapters to LaTeX.

Workflow (mirrors the from-token-to-fleet render pipeline):
  1. Copy all chapter figures into book/latex/figures/ (flat, dedup by name).
  2. For each chapter, rewrite image paths to the flat figures/ dir, strip the
     duplicate H1 title, and run pandoc to produce a per-chapter .tex.
  3. Emit the master book.tex that does \\frontmatter (title/copyright/toc/
     listoffigures) + \\mainmatter (8 acts as \\part) + \\appendix (A/B).
"""
import os, re, sys, glob, shutil, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LATEX = os.path.join(ROOT, "book", "latex")
MANU = os.path.join(ROOT, "book", "manuscript")
FIG = os.path.join(LATEX, "figures")
CH = os.path.join(LATEX, "chapters")
os.makedirs(FIG, exist_ok=True); os.makedirs(CH, exist_ok=True)

# The 8-act structure (BOOK_DESIGN.md §9): (part_title, [chapter filenames]).
ACTS = [
    ("The Question", [
        "ch01_let_us_brew.md", "ch02_what_does_it_mean_to_learn.md",
        "ch03_give_the_model_one_job.md"]),
    ("Build the Laboratory", [
        "ch04_build_a_world_we_can_control.md", "ch05_build_the_teacher.md",
        "ch06_build_the_judge.md", "ch07_build_the_rivals.md"]),
    ("The First Brew", [
        "ch08_the_smallest_brain.md", "ch09_the_first_brew.md",
        "ch10_does_it_actually_work.md"]),
    ("How Capability Scales", [
        "ch11_how_much_data.md", "ch12_how_much_brain.md",
        "ch13_same_data_more_diverse_data.md"]),
    ("Catching the Model Cheating", [
        "ch14_the_model_that_memorized_everything.md",
        "ch15_new_words_same_problem.md", "ch16_same_pieces_new_combination.md",
        "ch17_redteam_the_judge.md"]),
    ("Break It", [
        "ch20_what_happens_when_we_teach_it_something_new.md",
        "ch21_the_cost_of_capability.md"]),
    ("What Did We Learn?", [
        "ch22_the_capability_map.md", "ch25_conclusion.md"]),
]
APPENDIX = [
    ("An Annotated Tour of the Generator", "appendix_a_generator.md"),
    ("The Failure Ledger", "appendix_b_failure_ledger.md"),
    ("The Experiment Registry", "appendix_c_experiment_registry.md"),
    ("Glossary", "appendix_d_glossary.md"),
]

IMG_RE = re.compile(r"!\[((?:[^\[\]]|\[(?:[^\[\]]|\[[^\[\]]*\])*\])*)\]\(([^)]+)\)")
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.M)
ORD_RE = re.compile(r"^(#{2,3})\s+\d{1,2}\.\s+", re.M)


def rebalance_artifact_col(block):
    """Widen the Artifacts column of a registry-style table at the expense of narrow
    numeric columns, so long filenames fit on fewer lines."""
    # Find the colspec section (before \toprule).
    i = block.find("\\toprule")
    if i < 0:
        return block
    spec = block[:i]
    cols = re.findall(r">{\\raggedright\\arraybackslash}p\{([0-9.]+)\\linewidth\}", spec)
    if len(cols) < 5:
        return block
    fracs = [float(x) for x in cols]
    # Heuristic: the Artifacts column is the second-to-last (before Key result).
    # Widen it, shrink the narrow numeric columns (typically the 'Steps','Seed'
    # columns which are index ~3..4).
    n = len(fracs)
    art_idx = n - 2
    total = sum(fracs)
    # Give Artifacts a bigger share: 2x a typical column, capped.
    avg = total / n
    target = min(avg * 2.2, total * 0.28)
    delta = target - fracs[art_idx]
    if delta <= 0:
        return block
    # Take delta from the widest non-artifact column(s) that have room (>avg*0.6).
    # Rebuild colspec lines.
    # Split spec by > prefix to preserve each p{} line.
    parts = re.split(r"(?=>{\\raggedright\\arraybackslash}p\{[0-9.]+\\linewidth\})", spec)
    newfracs = list(fracs)
    remaining = delta
    # steal from smaller-priority narrow numeric columns (prefer index 3,4 then others)
    order = [3, 4, 2, 5, 1, 0]
    for idx in order:
        if remaining <= 0.001:
            break
        if idx >= n or idx == art_idx:
            continue
        take = min(newfracs[idx] - avg * 0.4, remaining)
        if take > 0.001:
            newfracs[idx] -= take
            remaining -= take
    newfracs[art_idx] += delta - remaining
    # Rebuild the colspec string, preserving prefix structure.
    out = []
    fiter = iter(newfracs)
    for seg in parts:
        fs = re.search(r"p\{([0-9.]+)\\linewidth\}", seg)
        if fs:
            newval = next(fiter)
            seg = re.sub(r"p\{([0-9.]+)\\linewidth\}",
                         lambda mm: "p{%.4f\\linewidth}" % newval, seg)
        out.append(seg)
    return "".join(out) + block[i:]

def fix_wide_tables(tex_path):
    """Wrap wide pandoc longtables in \\small and make filename-like tokens breakable
    so the narrower 6x9 text block does not overflow. A table with many columns (or
    columns summing to a large fraction of \\linewidth) gets a \\small group, and long
    `<name>.json` / `<name>.pt` tokens in table cells get an \\allowbreak before the
    extension so they can split at the period."""
    tex = open(tex_path, encoding="utf-8").read()
    tbl_re = re.compile(
        r"(\\begin\{longtable\}.*?\\end\{longtable\})", re.S)
    def repl(m):
        block = m.group(1)
        spec = block.split("\\toprule")[0]
        fracs = [float(x) for x in re.findall(r"p\{([0-9.]+)\\linewidth\}", spec)]
        ncols = len(fracs)
        # A plain left-aligned colspec (e.g. @{}llll@{}) has no explicit widths;
        # if it has several columns its natural width overflows a 6x9 page, so
        # convert it to scaled p-columns.
        plain_l = re.fullmatch(r"\s*\\begin\{longtable\}\[?\]?\{@?\{\}\{?[^}]*\}\}?\s*", spec) is None
        n_l = spec.count("l@") + spec.count("@{}l") + spec.count("l}, ")  # rough
        # Detect a run of plain 'l' (or 'r'/'c') column letters in the colspec.
        plain_letters = re.findall(r"([lcr])\s*@?\{?\}?\,?\s*", spec)
        n_plain = len(re.findall(r"[lcr](?:\s*@?\s*|\s*,)", spec)) - 2  # minus the @{} bookends approximate
        # Simpler: count column letters inside the longtable's own braces. The colspec
        # lives in the second brace group of \begin{longtable}[...]{...}; but the
        # colspec itself may contain @{} groups, so capture greedily up to the matching
        # final brace by balancing on the @{} tokens.
        lt_re = re.compile(r"\\begin\{longtable\}(\[[^\]]*\])?\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}")
        lt_m = lt_re.search(block)
        colspec = lt_m.group(2) if lt_m else spec
        n_plain_letters = len(re.findall(r"[lcr]", colspec))
        uses_plain = "p{" not in colspec and n_plain_letters >= 2
        if uses_plain and n_plain_letters >= 4:
            # Convert plain letters to p-columns summing to ~0.84, giving the first
            # column (usually the label/ID column) a wider share so its entries fit on
            # one line.
            n = n_plain_letters
            first_w = 0.30 if n >= 4 else 0.84 / n
            rest = (0.84 - first_w) / (n - 1) if n > 1 else 0.0
            widths = [first_w] + [rest] * (n - 1)
            new_cols = "".join(">{\\raggedright\\arraybackslash}p{%.4f\\linewidth}" % w for w in widths)
            block = block.replace(colspec, new_cols)
            # re-read fracs after conversion
            fracs = [float(x) for x in re.findall(r"p{([0-9.]+)\\linewidth}", block.split("\\toprule")[0])]
            ncols = len(fracs)
        wide = (ncols >= 7) or (sum(fracs) >= 0.70 and ncols >= 5) or (sum(fracs) >= 0.90)
        if not wide:
            return block
        # <name>.ext  ->  <name>\allowbreak.ext  (split at the period)
        block = re.sub(
            r"([A-Za-z0-9_]+)[.](json|pt|py|txt|npz)",
            lambda m: m.group(1) + "\\allowbreak." + m.group(2), block)
        # Arrow cells (e.g. the registry's 'final loss 5.84→0.0208.') hold an
        # unbreakable 'a→b' token wider than the cell, so it protrudes past the
        # right text edge. Let the cell break on either side of the arrow.
        block = re.sub(r"(?<!\\allowbreak)(→)(?!\\allowbreak)",
                       r"\1\\allowbreak ", block)
        block = re.sub(r"(?<!\\allowbreak )(→)", r"\\allowbreak \1", block)
        # For the experiment-registry-type table the Artifacts column (holding the
        # long manifest/checkpoint filenames) needs more width than the narrow
        # numeric columns. Rebalance the colspec: shrink the short numeric columns
        # and give the widest-content columns (those whose body contains ".json"/
        # ".pt", i.e. the Artifacts column) a larger share. We do this by
        # widening the column that appears just before the Key result column.
        block = rebalance_artifact_col(block)
        # Scale the relative column widths so the whole table (columns + the
        # inter-column \\tabcolsep padding) fits the text block. N p-columns of
        # width w_i*\\linewidth occupy sum(w_i)*\\linewidth + 2(N+1)\\tabcolsep.
        # Leave a little slack so long unbreakable cells don't nudge the last
        # column past the right margin.
        fracs2 = [float(x) for x in re.findall(r"p\{([0-9.]+)\\linewidth\}", block)]
        if fracs2:
            target = 0.84   # fractions may sum to ~0.84; leave room for inter-column padding
            s = sum(fracs2)
            if s > target:
                scale = target / s
                block = re.sub(
                    r"p\{([0-9.]+)\\linewidth\}",
                    lambda m: "p{%.4f\\linewidth}" % (float(m.group(1)) * scale),
                    block)
        return "\\begingroup\\footnotesize\n" + block + "\\endgroup"
    new = tbl_re.sub(repl, tex)
    if new != tex:
        open(tex_path, "w", encoding="utf-8").write(new)
        return True
    return False

def fix_colspec(tex_path):
    """Rewrite pandoc's relative-width table colspecs into simple
    p{<frac>\\linewidth} columns, scaled down so the full table (columns + the
    inter-column \\tabcolsep padding) fits the text width.

    Pandoc emits: `p{(\\linewidth - 12\\tabcolsep) * \\real{0.1237}}` per column.
    The fractions sum to ~1.0 * \\linewidth, but each column also carries
    2\\tabcolsep of padding — so N columns overflow by ~2N*\\tabcolsep. We extract
    each fraction, scale it to leave room for that padding, and emit a simple
    `p{<scaled>\\linewidth}` so xelatex lays the whole table out cleanly.
    """
    tex = open(tex_path, encoding="utf-8").read()

    col_re = re.compile(
        r"p\{\\(?:linewidth|textwidth)\s*-\s*\d+\\tabcolsep\)\s*\*\s*\\real\{([0-9.]+)\}\}")

    def repl_run(match_fracs):
        # replace a whole consecutive run of pandoc colspecs
        return None

    # Find a run of pandoc colspecs and scale each fraction.
    run_re = re.compile(
        r"(?:>\{\\raggedright\\arraybackslash\}p\{\(?\s*"
        r"\\(?:linewidth|textwidth)\s*-\s*\d+\\tabcolsep\)\s*\*\s*"
        r"\\real\{([0-9.]+)\}\}\s*)+")
    pos = 0
    out = []
    while True:
        m = run_re.search(tex, pos)
        if not m:
            out.append(tex[pos:])
            break
        fracs = [float(x) for x in re.findall(r"\\real\{([0-9.]+)\}", m.group(0))]
        n = len(fracs)
        # each column carries 2\\tabcolsep padding; scale columns so the full
        # table fits the text block. (tabcolsep=4pt -> 8pt/col, ~1.8% each.)
        scale = max(0.55, min(0.95, 1.0 - 2 * n * 0.010))
        new_run = "".join(">{\\raggedright\\arraybackslash}p{%.4f\\linewidth}\n" % (f * scale)
                          for f in fracs)
        out.append(tex[pos:m.start()])
        out.append(new_run)
        pos = m.end()
    new = "".join(out)
    # Also normalize any already-simple p{<frac>\\linewidth} colspecs (in case a
    # prior pass already converted them) so they still get the same padding-safe
    # scale.
    if new == tex:
        simple_re = re.compile(r"(?:>\{\\raggedright\\arraybackslash\}p\{([0-9.]+)\\linewidth\}\s*)+")
        pos = 0; out = []
        while True:
            m = simple_re.search(new, pos)
            if not m:
                out.append(new[pos:]); break
            fracs = [float(x) for x in re.findall(r"p\{([0-9.]+)\\linewidth\}", m.group(0))]
            scale = max(0.55, min(0.95, 1.0 - 2 * len(fracs) * 0.010))
            new_run = "".join(">{\\raggedright\\arraybackslash}p{%.4f\\linewidth}\n" % (f * scale)
                              for f in fracs)
            out.append(new[pos:m.start()]); out.append(new_run); pos = m.end()
        new = "".join(out)
    if new != tex:
        open(tex_path, "w", encoding="utf-8").write(new)
        return True
    return False

def wrap_figures(tex_path):
    """Convert each pandoc `figure` environment into a single captioned figure that
    registers in the List of Figures AND works inside nested (quote/list) contexts.

    Pandoc emits:
        \\begin{figure}\\centering\\pandocbounded{\\includegraphics[...]{...}}
        \\caption{...}\\end{figure}
    We rewrite the whole block into a non-floating `\\captionof` figure (so it does
    not need outer par mode) with a single caption, avoiding duplicate captions.
    """
    tex = open(tex_path, encoding="utf-8").read()
    pat = re.compile(
        r"\\begin\{figure\}(.*?)\\end\{figure\}", re.S)
    def repl(m):
        block = m.group(1)
        # pull the includegraphics options + file
        img = re.search(r"\\includegraphics\[([^\]]*)\]\{([^}]+)\}", block)
        if not img:
            return m.group(0)
        opts, path = img.group(1), img.group(2)
        # pull the caption text
        cap = None
        c = re.search(r"\\caption\{([^}]*)\}", block)
        if c:
            cap = c.group(1).strip()
        if not cap:
            cap = re.search(r"alt=\\{([^}]*)\\}", opts).group(1).strip()
        # Short form for the List of Figures (LOF) so a long caption does not wrap
        # across several LOF lines. Registered via \captionof{figure}[short]{long}.
        short = SHORT_FIG_CAPTIONS.get(path)
        if short:
            return (
                "\\begin{center}\\begin{minipage}{\\linewidth}\\centering\\includegraphics[%s]{%s}\\\\\n"
                "\\captionof{figure}[%s]{%s}\\end{minipage}\\end{center}" % (opts, path, short, cap)
            )
        return (
            "\\begin{center}\\begin{minipage}{\\linewidth}\\centering\\includegraphics[%s]{%s}\\\\\n"
            "\\captionof{figure}{%s}\\end{minipage}\\end{center}" % (opts, path, cap)
        )
    new = pat.sub(repl, tex)
    # Handle bare inline \pandocbounded{\includegraphics[alt={Cap}]{...}} that pandoc
    # did NOT wrap in a figure env (e.g. an image inline inside a paragraph). Wrap it.
    pat2 = re.compile(
        r"\\pandocbounded\{\\includegraphics\[([^\]]*?alt=\{([^}]*)\}[^\]]*?)\]\{(figures/[^}]+)\}\}",
        re.S)
    def repl2(m):
        opts, cap, path = m.group(1), m.group(2).strip(), m.group(3)
        return (
            "\\begin{center}\\begin{minipage}{\\linewidth}\\centering\\includegraphics[%s]{%s}\\\\"
            "\\captionof{figure}{%s}\\end{minipage}\\end{center}" % (opts, path, cap)
        )
    new = pat2.sub(repl2, new)
    if new != tex:
        open(tex_path, "w", encoding="utf-8").write(new)
        return True
    return False

def fix_figure_width(tex_path):
    tex = open(tex_path, encoding="utf-8").read()
    pat = re.compile(r"\\includegraphics\[((?:[^\[\]]|\[[^\]]*\])*)\]\{(figures/[^}]+)\}")
    def repl(m):
        if "width=" in m.group(1):
            return m.group(0)
        return "\\includegraphics[%s,width=\\maxwidth{\\textwidth},keepaspectratio]{%s}" % (m.group(1), m.group(2))
    new = pat.sub(repl, tex)
    if new != tex:
        open(tex_path, "w", encoding="utf-8").write(new)
        return True
    return False

def copy_figures():
    """Copy all chapter figures into a flat dir; return {orig_rel: flat_name}.

    Figures are referenced as `figures/<name>.png` relative to book/ (the assembled
    manuscript tree), so resolve relative to book/ not book/manuscript/.
    """
    mapping = {}
    figbase = os.path.join(os.path.dirname(LATEX), "figures")  # book/figures
    for md in glob.glob(os.path.join(MANU, "*.md")) + glob.glob(os.path.join(MANU, "**", "*.md"), recursive=True):
        txt = open(md, encoding="utf-8").read()
        for m in IMG_RE.finditer(txt):
            rel = m.group(2).split("#")[0]
            if rel.startswith("http"):
                continue
            flat = os.path.basename(rel)
            # flat source dir: book/figures
            src = os.path.join(figbase, flat)
            if not os.path.exists(src):
                continue
            shutil.copy(src, os.path.join(FIG, flat))
            mapping[rel] = flat
    # front cover: not referenced in any chapter, copy explicitly
    # use the PDF (Inkscape render) -- xelatex embeds PDFs natively, but the
    # inkscape PNG is misread as "type bmp" and renders blank.
    for ext in ("fig_cover.pdf", "fig_cover.png"):
        cs = os.path.join(figbase, ext)
        if os.path.exists(cs):
            shutil.copy(cs, os.path.join(FIG, ext))
    return mapping

def chapter_title(fn):
    txt = open(os.path.join(MANU, fn), encoding="utf-8").read()
    m = TITLE_RE.search(txt)
    title = m.group(1).strip() if m else os.path.basename(fn)
    # strip a leading manual "N. " prefix if present so LaTeX owns numbering
    title = re.sub(r"^\d{1,2}\.\s*", "", title)
    return title

# Short forms for the running head (\\chapter[short]{long}). Long titles otherwise
# crowd the header line and hyphenate mid-word when wrapped.
SHORT_TITLES = {
    "What Happens When We Teach It Something New?": "Teaching It Something New",
    "The Model Wasn't the Point: A Conclusion": "The Model Wasn't the Point",
    "The Model That Memorized Everything": "The Model That Memorized",
    "The Capability Ladder Revisited": "The Capability Ladder Revisited",
    "Same Pieces, New Combination": "Same Pieces, New Combination",
    "Same Data, More Diverse Data": "Same Data, More Diverse Data",
    "Build a World We Can Control": "Build a World We Can Control",
    "What Does It Mean to Learn?": "What Does It Mean to Learn?",
    "An Annotated Tour of the Generator": "The Generator",
    "The Experiment Registry": "The Experiment Registry",
}

# Short forms for the List of Figures (LOF): a long caption otherwise wraps across
# several LOF lines (the full caption still appears beneath the figure). Registered
# via \captionof{figure}[short]{long}.
SHORT_FIG_CAPTIONS = {
    "figures/fig_model_size.png": "Model size vs composition",
    "figures/fig_diversity.png": "Diversity vs quantity",
    "figures/fig_continual.png": "Sequential vs joint training",
    "figures/fig_apparatus.png": "The whole apparatus",
}

def fix_verbatim(path):
    """Rewrite pandoc's plain \\begin{verbatim} into fancyvrb's Verbatim with
    long-line wrapping.

    fancyvrb's Verbatim supports breaklines/breakanywhere; the plain pandoc
    'verbatim' environment does not honour them reliably when redefined via
    renewenvironment, so we emit Verbatim directly with the wrapping options.
    """
    with open(path, encoding="utf-8") as f:
        t = f.read()
    t = t.replace("\\begin{verbatim}",
                  "\\needspace{6\\baselineskip}\\begin{Verbatim}[breaklines=true, breakanywhere=true, fontsize=\\small]")
    t = t.replace("\\end{verbatim}", "\\end{Verbatim}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(t)


def _strip_tok_macros(s):
    """Unwrap \\XxxTok{...} (pandoc syntax-highlighting wrappers) with
    balanced-brace scanning, returning the raw code text."""
    while True:
        m = re.search(r"\\[A-Za-z]+Tok\{", s)
        if not m:
            return s
        start = m.start(); i = m.end(); depth = 1
        while i < len(s) and depth:
            c = s[i]
            if c == "\\":
                i += 2; continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            i += 1
        s = s[:start] + s[m.end():i - 1] + s[i:]


def _unescape_code(s):
    """Undo the LaTeX escaping pandoc applies inside highlighted code spans."""
    for a, b in (("\\textgreater{}", ">"), ("\\textless{}", "<"),
                 ("\\textasciitilde{}", "~"), ("\\textasciicircum{}", "^"),
                 ("{-}", "-"), ("\\_", "_"), ("\\%", "%"), ("\\#", "#"),
                 ("\\&", "&"), ("\\$", "$"), ("\\{", "{"), ("\\}", "}"),
                 ("\\@", "@"), ("\\^", "^"), ("\\~", "~")):
        s = s.replace(a, b)
    s = s.replace("\\textbackslash{}", "\\")   # last: its output must not be re-escaped
    return s


def fix_shaded_blocks(tex_path):
    """P1-19: pandoc renders language-tagged fenced blocks as
    \\begin{Shaded}\\begin{Highlighting}[] ... \\end{Highlighting}\\end{Shaded}.
    book.sty defines Highlighting as an empty environment and the *Tok macros as
    plain text, so that block typesets as JUSTIFIED SERIF PROSE: pandoc's literal
    '[]' optional argument is printed, separate shell commands merge into one
    stretched paragraph, and tokens wrap at arbitrary spaces -- not a faithful
    listing. Rewrite such blocks into the same breaking Verbatim used for plain
    fences: strip the *Tok wrappers, unescape LaTeX specials, keep the real
    newlines, and wrap in Verbatim[breaklines,breakanywhere] so the code wraps
    with no in-band glyphs and prints exactly the source characters."""
    tex = open(tex_path, encoding="utf-8").read()
    pat = re.compile(
        r"\\begin\{Shaded\}\s*\\begin\{Highlighting\}(?:\[\])?\s*(.*?)\s*"
        r"\\end\{Highlighting\}\s*\\end\{Shaded\}", re.S)

    def repl(m):
        body = _unescape_code(_strip_tok_macros(m.group(1)))
        lines = [ln.rstrip() for ln in body.split("\n")]
        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()
        return ("\\needspace{6\\baselineskip}\\begin{Verbatim}[breaklines=true, "
                "breakanywhere=true, fontsize=\\small]\n"
                + "\n".join(lines) + "\n\\end{Verbatim}")

    new = pat.sub(repl, tex)
    if new != tex:
        open(tex_path, "w", encoding="utf-8").write(new)
        return True
    return False



def fix_result_table(tex_path):
    """Convert the small ch13 diversity result longtable (plain @{}lll@{} colspec)
    into a non-breaking centered tabular.

    The longtable sits immediately after the \\section{The measured result} heading
    and its intro paragraph. longtable's page-split machinery, interacting with the
    section's keep-with-next (\\needspace) at that page boundary, drops the heading
    and intro and misplaces the rows (clipped at the top edge). A plain tabular is a
    single unbreakable box, so heading + intro + table stay together on one page."""
    tex = open(tex_path, encoding="utf-8").read()
    pat = re.compile(
        r"\\begin\{longtable\}\[\]\{(@\{\}lll@\{\})\}(.*?)\\end\{longtable\}", re.S)

    def repl(m):
        spec, body = m.group(1), m.group(2)
        if "minimal diversity" not in body:
            return m.group(0)          # only the ch13 result table
        body = body.lstrip("\n")
        body = body.replace("\\noalign{}", "")
        body = re.sub(r"\\endhead\s*", "", body)
        body = re.sub(r"\\bottomrule\s*\\endlastfoot\s*", "", body)
        body = body.rstrip() + "\n\\bottomrule\n"
        return ("\\begin{center}\n\\begin{tabular}{%s}\n%s"
                "\\end{tabular}\n\\end{center}" % (spec, body))

    new = pat.sub(repl, tex)
    if new != tex:
        open(tex_path, "w", encoding="utf-8").write(new)
        return True
    return False


def fix_label_column(tex_path):
    """Widen the first (label) column of the ch16 result longtable whose first
    column holds the long unbreakable word 'Compositional', which overflowed 7.4pt
    into the adjacent 0.000 value column (Overfull \\hbox + text bbox collision).
    The width is taken from the last (numeric) column so the table's total width
    is unchanged."""
    tex = open(tex_path, encoding="utf-8").read()
    pat = re.compile(r"(\\begin\{longtable\}.*?\\end\{longtable\})", re.S)

    def repl(m):
        block = m.group(1)
        if "Compositional (unseen combos)" not in block:
            return block
        fracs = re.findall(r"p\{([0-9.]+)\\linewidth\}", block)
        if len(fracs) < 2:
            return block
        old0, oldlast = float(fracs[0]), float(fracs[-1])
        new0 = 0.19
        if new0 <= old0:
            return block
        newlast = oldlast - (new0 - old0)
        if newlast <= 0.05:
            return block
        first_tok = "p{%s\\linewidth}" % fracs[0]
        block = block.replace(first_tok, "p{%.4f\\linewidth}" % new0, 1)
        last_tok = "p{%s\\linewidth}" % fracs[-1]
        idx = block.rfind(last_tok)
        block = (block[:idx] + "p{%.4f\\linewidth}" % newlast
                 + block[idx + len(last_tok):])
        return block

    new = pat.sub(repl, tex)
    if new != tex:
        open(tex_path, "w", encoding="utf-8").write(new)
        return True
    return False


def breakable_texttt_paths(tex_path):
    """Allow long monospaced path/CLI tokens in \\texttt{...} to break so justified
    prose does not push a bare token past the right margin. Break opportunities are
    inserted before and after every separator/punctuation character in the token
    set below ('/', '.', '_', '-', '=', ':', ',', '(', ')'), so a token like
    ``save_path=..`` or ``torch.`` can drop its tail to the next line instead of
    protruding into the margin (previously only after '/' and '.', which left bare
    tokens such as 'torch.' or 'requirements.' unbreakable at their tail).
    \\allowbreak is zero-width: it only adds a break opportunity and never changes
    glyphs, so rendering is identical unless a break is actually taken. A break is
    never inserted between a backslash escape and its character (e.g. \\_), and any
    marker already inserted by an earlier pass is stripped and regenerated here."""
    tex = open(tex_path, encoding="utf-8").read()
    # '-' is deliberately absent: breaking at hyphens created new edge-ending
    # fragments (e.g. 'natural-') without fixing any of the flagged tokens.
    BREAK_CHARS = "/._=:,()→"

    def add_breaks(inner):
        inner = inner.replace("\\allowbreak ", "").replace("\\allowbreak", "")
        out = []
        for i, ch in enumerate(inner):
            if (i > 0 and inner[i - 1] != "\\"
                    and (inner[i - 1] in BREAK_CHARS or ch in BREAK_CHARS)):
                # trailing space terminates the \\allowbreak control word so it is
                # not absorbed into a following letter; the space is eaten as the
                # control-word delimiter and never typeset
                out.append("\\allowbreak ")
            out.append(ch)
        return "".join(out)

    def mbox_short_tokens(inner):
        """P1-19: TeX may break a line after any explicit hyphen, so an inline
        CLI flag such as ``--n-embd`` split as ``-`` / ``-n-embd`` across lines,
        and version tokens split as ``torch==`` / ``2.14.0``. Wrap every short
        space-separated token of inline code in \\mbox so it prints as one
        unbreakable run; the line then breaks at the surrounding spaces, which is
        always faithful. Tokens longer than 30 chars keep their \\allowbreak
        points (added below) so a long path/URL can still wrap instead of
        overflowing the 6x9 text block. Pandoc escapes code spaces as ``\\ ``;
        the separator (backslash included) is kept outside the mbox."""
        parts = re.split(r"(\\ | )", inner)   # separators kept in the result
        out = []
        for idx, p in enumerate(parts):
            if idx % 2 == 0 and p and len(p) <= 30 and "\\mbox" not in p:
                out.append("\\mbox{%s}" % p)
            else:
                out.append(p)
        return "".join(out)

    def repl(inner, in_tbl=False):
        # Table cells (longtable p-columns) are only ~60-90pt wide: an \mbox'd
        # token would overflow the column instead of wrapping (a 27-char run ID
        # printed straight through the next column), so inside tables keep the
        # wrap-at-\allowbreak behaviour and mbox only in prose.
        if not in_tbl:
            inner = mbox_short_tokens(inner)
        if not any(c in inner for c in BREAK_CHARS):
            return "\\texttt{%s}" % inner
        return "\\texttt{%s}" % add_breaks(inner)

    # Balanced-brace scan so spans containing {\...} (e.g. \textgreater{}) are
    # covered too; the old [^{}]* pattern silently skipped them.
    table_ranges = [(m.start(), m.end()) for m in
                    re.finditer(r"\\begin\{longtable\}.*?\\end\{longtable\}", tex, re.S)]
    out = []
    pos = 0
    while True:
        m = re.search(r"\\texttt\{", tex[pos:])
        if not m:
            out.append(tex[pos:])
            break
        start = pos + m.start()
        i = pos + m.end()
        depth = 1
        while i < len(tex) and depth:
            c = tex[i]
            if c == "\\":
                i += 2
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            i += 1
        inner = tex[pos + m.end():i - 1]
        out.append(tex[pos:start])
        out.append(repl(inner, any(a <= start < b for a, b in table_ranges)))
        pos = i
    new = "".join(out)
    if new != tex:
        open(tex_path, "w", encoding="utf-8").write(new)
        return True
    return False


def convert_chapter(fn, mapping, outbase):
    txt = open(os.path.join(MANU, fn), encoding="utf-8").read()
    # strip the H1 chapter title (book.tex supplies \chapter{title})
    txt = re.sub(TITLE_RE, "", txt, count=1)
    txt = ORD_RE.sub(r"\1 ", txt)
    def rep(m):
        alt = m.group(1); rel = m.group(2).split("#")[0]
        flat = mapping.get(rel, rel)
        return "![%s](figures/%s)" % (alt, flat)
    txt = IMG_RE.sub(rep, txt)
    md_path = os.path.join(LATEX, "_md", outbase + ".md")
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    open(md_path, "w", encoding="utf-8").write(txt)
    out = os.path.join(CH, outbase + ".tex")
    cmd = ["pandoc", md_path, "-f", "markdown+pipe_tables+fenced_code_blocks-yaml_metadata_block",
           "-t", "latex", "--top-level-division=chapter", "-o", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("pandoc fail %s: %s" % (outbase, r.stderr[-300:]))
    fix_colspec(out); fix_figure_width(out); wrap_figures(out); fix_wide_tables(out)
    fix_verbatim(out)
    fix_shaded_blocks(out)
    fix_result_table(out)
    fix_label_column(out)
    breakable_texttt_paths(out)
    if outbase == "appD":
        # P1-PROD-01 (glossary tail): the Glossary ran 4.45 pages and ended on a
        # conspicuous half-empty final page (one bullet + tail, ~55% whitespace).
        # Set the glossary body 5% tighter (leading only; the \chapter heading is
        # supplied by book.tex outside this group, so it is unaffected) so the
        # entries consolidate onto full pages. Harness-verified: last page goes
        # from 143 words / 45% fill to 242 words / 72% fill, 5 pages -> 4.
        t = open(out, encoding="utf-8").read()
        open(out, "w", encoding="utf-8").write(
            "{\\linespread{0.95}\\selectfont\n" + t + "\n}")
    return out

def main():
    mapping = copy_figures()
    print("figures copied:", len(mapping))

    chapters_out = []      # (label, title, tex_path)
    build_lines = []
    num = 0
    for part_title, fns in ACTS:
        build_lines.append("\\part{%s}" % part_title)
        for fn in fns:
            p = os.path.join(MANU, fn)
            if not os.path.exists(p):
                print("[skip]", fn); continue
            num += 1
            title = chapter_title(fn)
            short = SHORT_TITLES.get(title, title)
            base = "ch%02d" % num
            tex = convert_chapter(fn, mapping, base)
            build_lines.append("\\chapter[%s]{%s}" % (short, title))
            build_lines.append("\\label{chap:%d}" % num)
            build_lines.append("\\input{chapters/%s}" % base)
            chapters_out.append((num, title, tex))

    build_lines.append("\\appendix")
    ap = 0
    for atitle, fn in APPENDIX:
        p = os.path.join(MANU, fn)
        if not os.path.exists(p):
            print("[skip]", fn); continue
        ap += 1
        base = "app%c" % (chr(64 + ap))   # appA, appB
        tex = convert_chapter(fn, mapping, base)
        build_lines.append("\\chapter{%s}" % atitle)
        build_lines.append("\\input{chapters/%s}" % base)

    # Emit book.tex with frontmatter (title/copyright/toc/figures) + mainmatter.
    book = render_book_tex(build_lines)
    open(os.path.join(LATEX, "book.tex"), "w", encoding="utf-8").write(book)
    print("wrote book.tex; chapters:", len(chapters_out), "appendices:", ap)

def render_book_tex(build_lines):
    body = "\n".join(build_lines)
    return f"""% Auto-generated by book/latex/md_to_latex.py — do not edit by hand
\\documentclass[11pt,openany]{{book}}
% 6in x 9in trade paperback trim (matches the cover's 2:3 aspect; KDP standard).
% Page layout set in book.sty via geometry -- no paper-size option here.
\\usepackage{{book}}
\\begin{{document}}

\\begin{{titlepage}}
\\thispagestyle{{empty}}
\\centering
\\vspace*{{3cm}}
{{\\Huge\\bfseries Let Us Brew an AI Model\\par}}
\\vspace{{1.5cm}}
{{\\Large\\itshape What Tiny Language Models Can Actually Learn When Given One Job\\par}}
\\vspace{{0.8cm}}
{{\\normalsize Version 20261001\\par}}
\\vfill
{{\\large Zhiqi Tao\\par}}
\\vspace{{0.8cm}}
{{\\small\\itshape Building a small language model is relatively easy. Determining what it actually learned is the hard part.\\par}}
\\vfill
\\end{{titlepage}}

\\begin{{titlepage}}
\\thispagestyle{{empty}}
{{\\centering\\MakeUppercase{{Copyright \\textcopyright{{}} 2026 Zhiqi Tao}}\\\\[2pt] All rights reserved.\\par}}
\\vspace{{1.2cm}}
\\noindent\\textbf{{License.}} This work is licensed under a \\emph{{custom source-available}} license. The \\textbf{{book text, diagrams, and figures}} may be freely read, studied, shared, and redistributed non-commercially with attribution; \\textbf{{commercial republication or sale of the book text requires prior written approval from the author}}. The \\textbf{{code examples and the companion repository}} are provided for you to build on: you may use, adapt, and reuse the code in your own projects, including commercial ones, with attribution, and the book is not an open-source text. For permission, contact Zhiqi Tao (zhiqi.tao@gmail.com).

\\noindent\\footnotesize In short: \\emph{{read, study, and share the book text freely (non-commercially); do not sell or republish the text as a product without the author's authorisation. The code examples may be adapted and reused in your own work.}}

\\noindent\\footnotesize The work is provided ``as is'', without warranty of any kind.

\\vspace{{0.8cm}}
\\noindent\\textbf{{About the author.}} Zhiqi Tao works on AI systems, with a focus
on building and evaluating small models in controlled settings. This book grew out
of a running laboratory notebook: build a tiny model, give it one job, and find out
precisely what it can and cannot learn --- with the failure ledger as much a part of
the result as the successes.

\\vspace{{0.8cm}}
\\noindent\\footnotesize\\textbf{{Companion repository and errata.}} The code,
scripts, configurations, and checkpoints that reproduce every experiment in this
book live in the companion repository under the release tag \\texttt{{v20261001}}
(an annotated release tag on the release commit). As of this edition the repository is not yet
published at a public URL; the reproduction quick start and the exact release
identifiers are in Appendix C. An online errata address will be listed here once the
repository is public; until then, report issues to zhiqi.tao@gmail.com.
\\vfill
\\end{{titlepage}}

\\frontmatter

\\chapter*{{Preface}}
{preface_extract()}

\\clearpage
\\tableofcontents

\\clearpage
\\listoffigures

\\mainmatter

{body}

\\backmatter

\\end{{document}}
"""

def preface_extract():
    # A generated preface plus a reader contract (audience, claims, how to use).
    return r"""This book is a controlled empirical investigation into what a small language model can actually learn when it is given exactly one narrowly defined, objectively testable job.

The task: read a natural-language programming request and produce a Python program, which is then executed against hidden tests.

Along the way we build a laboratory: a controlled world (a sandbox), a teacher (a semantic data generator), a judge (an execution-based evaluator), and rivals (simple baselines). The model is the instrument. The experiment is the subject. And the honest territory includes the moments the model falls flat --- and the moment we discovered that our own measuring stick was broken, not the model.

\section*{Who this book is for}

This is an accessible experimental case study, not a build-from-scratch transformer textbook. It is written for readers who are comfortable reading (or willing to skim) Python and who want to see how to set up a small, honest evaluation of a tiny model --- and, more than that, how easily a number from such an experiment can be misread. No GPU or deep-learning background is required to follow the conceptual argument; a little Python helps with the code listings. Nothing here needs a large model or a large machine --- the whole investigation runs on a single-laptop CPU.

\section*{What the book claims (and what it does not)}

We set the scope deliberately narrow, and we repeat it throughout. All the results are measurements on \textbf{one synthetic task} (natural-language request \textrightarrow{} single Python function), \textbf{one architecture family} (a small decoder-only transformer), \textbf{one training regime} (CPU, fixed budgets), and parameter counts up to roughly 30M. We do not claim a universal law about tiny models, and we do not claim to have identified the internal cause of the limits we observe. We claim only: \emph{under this setup, here is what was measured, here is what did not move, and here is what remains open.} If a reader takes nothing else from the book, we hope it is the discipline of saying exactly what a measurement establishes and leaving the mechanism open when the controls have not identified it.

\section*{How to use the book}

\begin{itemize}
  \item \textbf{Read the body for the argument.} Each chapter opens with a concrete image before the mechanics.
  \item \textbf{Use the appendices for reproducibility.} Appendix A shows the generator; Appendix B is the failure ledger; Appendix C is the experiment registry that ties every number to a run ID, config, and artifact.
  \item \textbf{Run it yourself if you like.} The scripts, configs, and a release tag are in the companion repository (see Appendix C). On this CPU-only setup, the pilot trains in minutes; the larger models take longer.
\end{itemize}

The honest payoff is not ``small models are inadequate.'' It is a precise map of where the boundary sits under our tests --- and the many ways a promising-looking number can be an artifact of how we measured it."""

if __name__ == "__main__":
    main()
