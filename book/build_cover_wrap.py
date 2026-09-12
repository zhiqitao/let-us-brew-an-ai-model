#!/usr/bin/env python3
"""Build the KDP cover wrap for 'Let Us Brew an AI Model' (6in x 9in trim).

Produces a single full-bleed PDF: back panel + spine + front panel, sized to the
KDP wrap template for the current page count. The front artwork is the existing
2:3 (6x9) fig_cover.svg, which fits the 6x9 front panel exactly.

All geometry uses a points-per-inch scale (PT=72), so font sizes are natural pt.
"""
import os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIG = os.path.join(ROOT, "book", "figures")
OUT = os.path.join(FIG, "cover_wrap.svg")
OUT_PDF = os.path.join(ROOT, "book", "let-us-brew-an-ai-model-v20261001-cover.pdf")

PT = 72.0  # points per inch

def main():
    PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 202
    TRIM_W, TRIM_H = 6.0, 9.0
    BLEED = 0.125
    SPINE = PAGES * 0.002252

    back_w = TRIM_W + BLEED
    spine_w = SPINE
    front_w = TRIM_W + BLEED
    total_w = back_w + spine_w + front_w
    total_h = TRIM_H + 2 * BLEED

    W, H = int(total_w * PT), int(total_h * PT)

    def pt(v): return f"{v*PT:.2f}"     # inches -> points

    b_ox, b_oy = BLEED + 0.35, BLEED + 0.40
    b_inner_w = TRIM_W - 0.70

    blurb_lines = [
        "tiny transformer, given exactly one job: read a plain-English",
        "programming request, write Python, and pass hidden tests. We",
        "measure where its capability ends.",
    ]
    map_lines = [
        ("L1", "Memorize - generalizes", "59/60 held-out"),
        ("L2", "New instances", "0.900"),
        ("L3", "Surface change", "0.000"),
        ("L4", "Composition", "0.000"),
    ]

    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
             f'viewBox="0 0 {W} {H}" width="{total_w:.4f}in" height="{total_h:.4f}in">')
    p.append('<defs><linearGradient id="wrapbg" x1="0" y1="0" x2="0" y2="1">'
             '<stop offset="0" stop-color="#F2EEE4"/><stop offset="1" stop-color="#E9E3D6"/>'
             '</linearGradient></defs>')
    p.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#wrapbg)"/>')

    # ---------- BACK ----------
    p.append(f'<g transform="translate({pt(b_ox)},{pt(b_oy)})">')
    p.append('<text font-family="Helvetica, Arial, sans-serif" font-weight="800" font-size="21" fill="#141414">LET US BREW AN AI MODEL</text>')
    p.append('<text y="30" font-family="Helvetica, Arial, sans-serif" font-weight="400" font-size="13" fill="#6E6E68">What tiny language models can actually learn when given one job</text>')
    p.append(f'<rect x="0" y="44" width="{pt(b_inner_w)}" height="2" fill="#1E7A6F"/>')

    # blurb (explicit y so it does not overlap the title)
    p.append('<text font-family="Helvetica, Arial, sans-serif" font-weight="400" font-size="13.5" fill="#3B3B38">')
    p.append('<tspan x="0" y="90">Building a small language model is comparatively easy.</tspan>')
    p.append('<tspan x="0" y="110">Determining what it actually learned is the hard part.</tspan>')
    p.append('<tspan x="0" y="138">This book is a controlled empirical investigation into one</tspan>')
    yb = 158
    for ln in blurb_lines:
        p.append(f'<tspan x="0" y="{yb}">{ln}</tspan>')
        yb += 20
    p.append('</text>')

    # capability map box
    box_y = 250.0
    box_h = 2.35 * PT
    p.append(f'<rect x="0" y="{box_y:.0f}" width="{pt(b_inner_w)}" height="{box_h:.0f}" rx="8" fill="#FFFFFF" stroke="#1E7A6F" stroke-width="2"/>')
    p.append(f'<text x="14" y="{box_y+30:.0f}" font-family="Helvetica, Arial, sans-serif" font-weight="800" font-size="16" fill="#1E7A6F">THE CAPABILITY MAP</text>')
    yy = box_y + 60
    for lab, name, val in map_lines:
        p.append(f'<text x="14" y="{yy:.0f}" font-family="Helvetica, Arial, sans-serif" font-weight="400" font-size="13" fill="#3B3B38">'
                 f'<tspan font-weight="700" fill="#A84C1F">{lab}</tspan>  {name} <tspan fill="#3B3B38">| {val}</tspan></text>')
        yy += 22
    p.append(f'<text x="14" y="{box_y+box_h-30:.0f}" font-family="Helvetica, Arial, sans-serif" font-weight="400" font-size="11.5" fill="#6E6E68">Including the Failure Ledger on the broken evaluator, the leaked</text>')
    p.append(f'<text x="14" y="{box_y+box_h-11:.0f}" font-family="Helvetica, Arial, sans-serif" font-weight="400" font-size="11.5" fill="#6E6E68">wording, and a task a lookup table solved.</text>')

    # footer author (lower-left)
    p.append(f'<text x="0" y="{pt(8.35)}" font-family="Helvetica, Arial, sans-serif" font-weight="800" font-size="22" fill="#141414">ZHIQI TAO</text>')
    p.append('</g>')

    # barcode zone (bottom-right of back panel)
    bx, by = b_ox + b_inner_w - 2.6, BLEED + TRIM_H - 0.75
    bw, bh = 2.4, 0.72
    p.append(f'<rect x="{pt(bx)}" y="{pt(by)}" width="{pt(bw)}" height="{pt(bh)}" fill="#FFFFFF" stroke="#B9B09E" stroke-width="1.5"/>')
    p.append(f'<text x="{pt(bx+0.18)}" y="{pt(by+0.60)}" font-family="Helvetica, Arial, sans-serif" font-weight="400" font-size="9" fill="#8A8579">ISBN 000-0-00000-00-0</text>')
    # barcode bars
    bar_x = bx + 0.18
    for i in range(24):
        bw2 = 0.018 if i % 3 == 0 else 0.008
        p.append(f'<rect x="{pt(bar_x)}" y="{pt(by+0.10)}" width="{pt(bw2)}" height="{pt(0.36)}" fill="#3B3B38"/>')
        bar_x += bw2 + 0.018

    # ---------- SPINE ----------
    sp_cx = back_w + spine_w / 2.0
    p.append(f'<rect x="{pt(back_w)}" y="0" width="{pt(spine_w)}" height="{H}" fill="#F2EEE4"/>')
    mid = H / 2.0
    p.append(f'<text font-family="Helvetica, Arial, sans-serif" font-weight="700" font-size="17" fill="#141414" '
             f'transform="rotate(-90 {pt(sp_cx)} {mid:.0f})" text-anchor="middle" x="{pt(sp_cx)}" y="{mid:.0f}">LET US BREW AN AI MODEL</text>')
    p.append(f'<text font-family="Helvetica, Arial, sans-serif" font-weight="700" font-size="13" fill="#1E7A6F" '
             f'transform="rotate(-90 {pt(sp_cx)} {H-230:.0f})" text-anchor="middle" x="{pt(sp_cx)}" y="{H-230:.0f}">ZHIQI TAO</text>')

    # ---------- FRONT ----------
    fx = total_w - front_w
    p.append(f'<image xlink:href="fig_cover.svg" x="{pt(fx)}" y="{pt(BLEED)}" width="{pt(TRIM_W)}" height="{pt(TRIM_H)}" preserveAspectRatio="none"/>')

    p.append('</svg>')
    open(OUT, "w", encoding="utf-8").write("\n".join(p))
    print("wrote", OUT)
    print(f"wrap {total_w:.3f} x {total_h:.3f} in; spine {spine_w:.3f} in; pages {PAGES}")

if __name__ == "__main__":
    main()
