"""Cover graphics for Substack, LinkedIn and link previews.

One programme splits, like light through a prism, into seven legal answers. Line ends are the
real extensions for the worked example (40-day contractor delay first, 55-day employer delay
starting 10 days later on a parallel path), computed by the model.

Run: python src/experiments/make_covers.py  -> outputs/v2/figures/covers/
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "experiments"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.path import Path as MPath

from cdx.doctrines import DOCTRINES
from make_figures import CON, EMP, OP, OP_NAME, RULES7, two_path

OUT = ROOT / "outputs" / "v2" / "figures" / "covers"
BG, FG, SUB = "#12161b", "#f3f4f1", "#9ba4ad"
BRIGHT = {"effective_cause": "#3fb5ad", "as_planned_impact": "#a9b6c2", "overlap_concurrency": "#f0b429",
          "city_inn": "#5cc26a", "first_in_time": "#e36aa6", "nec4_prospective": "#9b8cf2",
          "contractual_exclusion": "#d29a7f"}
EMP_B, CON_B = "#5b8fe6", "#f07a35"
AUTHOR = "Charles Gava"

SIZES = {  # name: (width px, height px, layout)
    "substack_cover_1456x1048": (1456, 1048, "stack"),
    "linkedin_square_1200x1200": (1200, 1200, "stack"),
    "wide_1920x1080": (1920, 1080, "side"),
    "link_preview_1200x630": (1200, 630, "side"),
}


def answers():
    g = two_path(10.0, 55.0)
    return {d: DOCTRINES[d](g).eot for d in RULES7}


def prism(ax, x0, y0, w, h, scale_text=1.0, labels=True):
    """Draw the programme bars on the left and seven curves fanning to their extensions."""
    eot = answers()
    order = sorted(RULES7, key=lambda d: -eot[d])
    # input: the two delays
    bar_w = w * 0.20
    yc = y0 + h * 0.5
    ax.add_patch(FancyBboxPatch((x0, yc + h * 0.035), bar_w * 40 / 55, h * 0.05, boxstyle="round,pad=0,rounding_size=4",
                                color=CON_B, lw=0, mutation_aspect=1))
    ax.add_patch(FancyBboxPatch((x0 + bar_w * 10 / 55 * 0.6, yc - h * 0.085), bar_w, h * 0.05,
                                boxstyle="round,pad=0,rounding_size=4", color=EMP_B, lw=0))
    if labels:
        ax.text(x0, yc + h * 0.115, "contractor 40 days", color=CON_B, fontsize=12 * scale_text, fontweight="bold",
                family="Avenir Next")
        ax.text(x0, yc - h * 0.16, "employer 55 days", color=EMP_B, fontsize=12 * scale_text, fontweight="bold",
                family="Avenir Next")
    # focal point
    fx = x0 + bar_w * 1.25
    ax.scatter([fx], [yc], s=60 * scale_text, color=FG, zorder=5)
    # seven rays
    xs_end0 = fx + w * 0.10
    span = (x0 + w) - xs_end0
    n = len(order)
    for k, d in enumerate(order):
        yy = y0 + h * (0.92 - 0.84 * k / (n - 1))
        xe = xs_end0 + span * (eot[d] / 60.0) * 0.78
        verts = [(fx, yc), (fx + (xs_end0 - fx) * 0.75, yc), (xs_end0 - (xs_end0 - fx) * 0.2, yy), (xs_end0, yy)]
        ax.add_patch(PathPatch(MPath(verts, [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4]),
                               fc="none", ec=BRIGHT[d], lw=3.2 * scale_text, capstyle="round"))
        ax.plot([xs_end0, xe], [yy, yy], color=BRIGHT[d], lw=3.2 * scale_text, solid_capstyle="round")
        ax.scatter([xe], [yy], s=46 * scale_text, color=BRIGHT[d], zorder=5)
        if labels:
            ax.text(xe + w * 0.018, yy, f"{eot[d]:.0f} days", color=BRIGHT[d], fontsize=13 * scale_text,
                    va="center", fontweight="bold", family="Avenir Next")
            ax.text(xs_end0 + w * 0.005, yy + h * 0.022, OP_NAME[d], color=SUB, fontsize=10 * scale_text, va="bottom",
                    family="Avenir Next")


def cover(name, W, H, layout):
    dpi = 100
    fig = plt.figure(figsize=(W / dpi, H / dpi), dpi=dpi)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    s = min(W, H) / 1000
    pad = 0.065 * min(W, H)
    if layout == "side":
        tx, ty = pad, H - pad
        ax.text(tx, ty, "CONCURRENT DELAY  ·  LAW  ·  EXPLAINABLE AI", color=SUB, fontsize=15 * s * 1.3,
                fontweight="bold", va="top", family="Avenir Next")
        ax.text(tx, ty - 0.10 * H, "One Schedule,\nMany Laws", color=FG, fontsize=64 * s * 1.25, fontweight="bold",
                va="top", family="Avenir Next", linespacing=1.0)
        ax.text(tx, ty - 0.47 * H, "Same delays. Seven legal answers.\nWhat SHAP gets wrong, and what\nexplainable AI should do instead.",
                color=SUB, fontsize=21 * s * 1.25, va="top", family="Avenir Next", linespacing=1.35)
        ax.text(tx, pad, AUTHOR, color=FG, fontsize=20 * s * 1.25, fontweight="bold", va="bottom", family="Avenir Next")
        prism(ax, W * 0.47, H * 0.14, W * 0.47, H * 0.72, scale_text=s * 1.25, labels=W >= 1500)
    else:
        tx, ty = pad, H - pad
        ax.text(tx, ty, "CONCURRENT DELAY  ·  LAW  ·  EXPLAINABLE AI", color=SUB, fontsize=17 * s,
                fontweight="bold", va="top", family="Avenir Next")
        ax.text(tx, ty - 0.065 * H, "One Schedule,\nMany Laws", color=FG, fontsize=80 * s, fontweight="bold",
                va="top", family="Avenir Next", linespacing=1.0)
        ax.text(tx, ty - 0.335 * H, "Same delays. Seven legal answers.", color=SUB, fontsize=27 * s, va="top",
                family="Avenir Next")
        prism(ax, pad, H * 0.11, W - 2 * pad, H * 0.44, scale_text=s * 1.05, labels=True)
        ax.text(tx, pad * 0.75, AUTHOR, color=FG, fontsize=22 * s, fontweight="bold", va="bottom", family="Avenir Next")
        ax.text(W - pad, pad * 0.75, "gavacharles.github.io/concurrent-delay-map", color=SUB, fontsize=15 * s,
                va="bottom", ha="right", family="Menlo")
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.png", dpi=dpi, facecolor=BG)
    plt.close(fig)


def main():
    for name, (W, H, layout) in SIZES.items():
        cover(name, W, H, layout)
        print("wrote", name)


if __name__ == "__main__":
    main()
