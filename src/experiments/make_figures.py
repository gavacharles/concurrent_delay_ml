"""Publication and social figures + animations, in one visual language.

Public (committed):        outputs/v2/figures/
Derived from Package 5:    outputs/package5/figures/   (gitignored; anonymised labels)

Run: python src/experiments/make_figures.py
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "experiments"))

import imageio_ffmpeg
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch, Rectangle

from cdx import DelayEvent, DelayGame, Schedule
from cdx.cases import CASES
from cdx.doctrines import DOCTRINES

plt.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()

PUB = ROOT / "outputs" / "v2" / "figures"
PRIV = ROOT / "outputs" / "package5" / "figures"
LAW = json.load(open(ROOT / "docs" / "law_timeline.json"))

# --- visual language --------------------------------------------------------------------------
INK, MUTED, RULE, PAPER, GRID = "#1b1f24", "#5b6470", "#d6d9d1", "#f6f6f3", "#e8eae4"
EMP, EMP_SOFT, CON, CON_SOFT, NEU = "#2456a6", "#c9d7f0", "#d25a14", "#f6d9c6", "#8a8f96"
GOOD, BAD, BAD_SOFT, GOOD_SOFT = "#1d7a4f", "#b3261e", "#f6d5d3", "#d3ecdf"
OP = {  # one colour per legal rule
    "effective_cause": "#0f5c5c", "first_in_time": "#a23b72", "overlap_concurrency": "#c98a00",
    "as_planned_impact": "#7d8a96", "city_inn": "#2e7d32", "contractual_exclusion": "#6d4c41",
    "nec4_prospective": "#5c4d9a", "none": "#b8bcc2",
}
OP_NAME = {
    "effective_cause": "Actual-delay test (England)", "first_in_time": "Strict sequence",
    "overlap_concurrency": "Overlapping windows", "as_planned_impact": "As-planned impact",
    "city_inn": "Apportionment (Scotland)", "contractual_exclusion": "Excluded by contract (Cyden)",
    "nec4_prospective": "NEC4 prospective", "none": "No rule / parties choose",
}
RULES7 = ["effective_cause", "as_planned_impact", "overlap_concurrency", "city_inn", "first_in_time",
          "nec4_prospective", "contractual_exclusion"]
LANES = {"england": ("England & Wales", 4.8), "scotland": ("Scotland", 2.4), "forms": ("Guidance &\nstandard forms", 0.0)}
SYM = "DejaVu Sans"   # font with ✓ ✗ ● ◐ ○ ★
STATUS = {"verified": "judgment read", "quoted": "via later judgments", "secondary": "secondary source",
          "commentary": "commentary / form", "form": "standard form"}


def tint(c, amount):
    """Mix a colour with white (alpha would be overridden by artists' own alpha)."""
    r, g, b = matplotlib.colors.to_rgb(c)
    return (r + (1 - r) * amount, g + (1 - g) * amount, b + (1 - b) * amount)


def style(bg="white"):
    plt.rcParams.update({
        "font.family": "Avenir Next", "font.size": 10.5, "axes.titlesize": 13, "axes.titleweight": "bold",
        "axes.titlelocation": "left", "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
        "text.color": INK, "figure.facecolor": bg, "axes.facecolor": bg, "savefig.facecolor": bg,
        "legend.frameon": False,
    })


def save(fig, path, **kw):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=kw.pop("dpi", 220), bbox_inches=kw.pop("bbox", "tight"), **kw)
    plt.close(fig)


def two_path(e_start, e_days, c_start=0.0, c_days=40.0):
    s = Schedule({"A": 400.0, "B": 400.0})
    return DelayGame(s, [DelayEvent("C", "C", "B", c_days, c_start), DelayEvent("E", "E", "A", e_days, e_start)])


# --- 1. evolution of the law: static timeline ---------------------------------------------------

def _timeline_axes(ax, x0=1994.6, x1=2025.5):
    ax.set_xlim(x0, x1)
    ax.set_ylim(-1.75, 6.95)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xticks(range(1999, 2026, 2))
    ax.tick_params(axis="x", labelsize=9.5)
    for key, (label, y) in LANES.items():
        ax.plot([1998, x1], [y, y], color=GRID, lw=6, zorder=0, solid_capstyle="butt")
        ax.text(x0 + 0.1, y, label.upper(), fontsize=9, color=MUTED, fontweight="bold", va="center")


def _layout():
    """Positions for every event: x (with same-year jitter) and label level per lane."""
    levels = [0.55, -0.55, 1.12, -1.12]
    # hand placement where the cycle would collide (1 = up, -1 = down, 2 = up high, -2 = down low)
    fixed = {"Henry Boot v Malmaison": 1, "Royal Brompton v Hammond": -1, "De Beers v Atos": 2,
             "Adyard v SD Marine": -1, "Walter Lilly v Mackay": 1, "Saga Cruises v Fincantieri": -1,
             "North Midland v Cyden Homes": 2, "Thomas Barnes v Blackburn": -1, "John Doyle v Laing": 1,
             "City Inn (Outer House)": -1, "City Inn (Inner House)": 1, "FIDIC 1999 suite": 1,
             "SCL Protocol, 1st ed.": -1, "SCL Protocol, 2nd ed.": 2, "NEC4 (clause 63.5)": -2,
             "FIDIC 2017, Sub-Cl. 8.5": 1, "JCT 2024": -1}
    lvl = {1: 0.55, -1: -0.55, 2: 1.12, -2: -1.12}
    pos = []
    by_lane = {}
    for i, ev in enumerate(LAW):
        by_lane.setdefault(ev["lane"], []).append(i)
    for lane, idx in by_lane.items():
        idx = sorted(idx, key=lambda i: LAW[i]["year"])
        seen = {}
        for k, i in enumerate(idx):
            ev = LAW[i]
            n = seen.get(ev["year"], 0)
            seen[ev["year"]] = n + 1
            m = sum(1 for j in idx if LAW[j]["year"] == ev["year"])
            x = ev["year"] + (n - (m - 1) / 2) * 1.25
            pos.append((i, x, LANES[lane][1], lvl[fixed[ev["short"]]] if ev["short"] in fixed else levels[k % len(levels)]))
    return sorted(pos)


def _draw_event(ax, ev, x, y, lev, alpha=1.0, show_rule=True):
    c = OP[ev["operator"]]
    filled = ev["status"] in ("verified",)
    half = ev["status"] in ("quoted",)
    ax.plot([x, x], [y, y + lev * 0.8], color=c, lw=1, alpha=0.6 * alpha, zorder=1)
    face = c if filled else (tint(c, 0.62) if half else "white")
    ax.scatter([x], [y], s=110, color=face, edgecolor=c, linewidth=2.2, zorder=3, alpha=alpha)
    ty = y + lev
    va = "bottom" if lev > 0 else "top"
    t1 = ax.text(x, ty, ev["short"], fontsize=8.6, fontweight="bold", ha="center", va=va, alpha=alpha, color=INK)
    t2 = None
    if show_rule:
        t2 = ax.text(x, ty + (-0.13 if lev > 0 else 0.13) * (-1), "", fontsize=7.6, ha="center", va=va,
                     color=c, alpha=alpha)
        off = 0.24
        t2.set_position((x, ty - off if lev < 0 else ty + off))
        t2.set_text(f"{ev['year']} · {ev['rule']}")
    return t1, t2


def fig_law_timeline():
    style()
    fig, ax = plt.subplots(figsize=(17, 9.5))
    _timeline_axes(ax)
    for i, x, y, lev in _layout():
        _draw_event(ax, LAW[i], x, y, lev)
    eras = [(1998.6, 2009.6, "Building the rule: time, not money"),
            (2009.6, 2016.8, "Actual delay vs apportionment"),
            (2016.8, 2025.4, "Contracting out · time vs money")]
    for a, b, lab in eras:
        ax.plot([a + 0.15, b - 0.15], [6.55, 6.55], color=RULE, lw=3, solid_capstyle="round")
        ax.text((a + b) / 2, 6.63, lab, ha="center", va="bottom", fontsize=9.5, color=MUTED, style="italic")
    ops = ["effective_cause", "city_inn", "contractual_exclusion", "overlap_concurrency", "nec4_prospective", "none"]
    h1 = [Line2D([], [], marker="o", ls="", color=OP[o], markersize=9, label=OP_NAME[o]) for o in ops]
    h2 = [Line2D([], [], marker="o", ls="", markerfacecolor=MUTED, markeredgecolor=MUTED, markersize=9, label="judgment read"),
          Line2D([], [], marker="o", ls="", markerfacecolor=tint(MUTED, 0.62),
                 markeredgecolor=MUTED, mew=2, markersize=9, label="known via later judgments"),
          Line2D([], [], marker="o", ls="", markerfacecolor="white", markeredgecolor=MUTED, mew=2, markersize=9,
                 label="secondary source / commentary")]
    leg1 = ax.legend(handles=h1, loc="upper left", bbox_to_anchor=(0, -0.07), ncol=6, fontsize=8.6,
                     title="Which rule it supports", title_fontsize=8.6, alignment="left")
    ax.add_artist(leg1)
    ax.legend(handles=h2, loc="upper left", bbox_to_anchor=(0, -0.15), ncol=3, fontsize=8.6,
              title="How it was checked", title_fontsize=8.6, alignment="left")
    ax.set_title("How the law on concurrent delay evolved, 1999–2024", pad=26, fontsize=15)
    save(fig, PUB / "law_timeline.png")


# --- 2. evolution of the law: animation --------------------------------------------------------

def anim_law_timeline(fps=24, seconds=26):
    style()
    fig = plt.figure(figsize=(16, 9))
    ax = fig.add_axes([0.04, 0.33, 0.93, 0.58])
    cap = fig.add_axes([0.04, 0.03, 0.93, 0.22])
    cap.axis("off")
    _timeline_axes(ax)
    fig.text(0.04, 0.95, "How the law on concurrent delay evolved", fontsize=20, fontweight="bold")
    fig.text(0.04, 0.917, "England & Wales · Scotland · SCL Protocol · FIDIC · NEC4 · JCT", fontsize=11.5, color=MUTED)
    layout = _layout()
    artists = []
    for i, x, y, lev in layout:
        t1, t2 = _draw_event(ax, LAW[i], x, y, lev, alpha=0.0)
        dots = [a for a in ax.collections[-1:]] + ax.lines[-1:]
        artists.append((i, x, t1, t2, ax.collections[-1], ax.lines[-1]))
    now = ax.axvline(1998, color=INK, lw=1.2, alpha=0.5)
    year_txt = ax.text(1998, 6.3, "", fontsize=12, fontweight="bold", ha="left", color=INK)
    head = cap.text(0, 0.93, "", fontsize=14, fontweight="bold", va="top")
    sub = cap.text(0, 0.68, "", fontsize=10.5, color=MUTED, va="top")
    body = cap.text(0, 0.47, "", fontsize=12, va="top", wrap=True)
    bar = cap.add_patch(Rectangle((-0.012, 0.0), 0.004, 0.95, color=INK, transform=cap.transAxes, clip_on=False))
    frames = fps * seconds
    hold = fps * 3
    t_years = np.concatenate([np.linspace(1998, 2025, frames - hold), np.full(hold, 2025)])

    def update(k):
        yr = t_years[k]
        now.set_xdata([yr, yr])
        year_txt.set_position((min(yr, 2023.6) + 0.15, 6.3))
        year_txt.set_text(f"{int(yr)}")
        latest = None
        for i, x, t1, t2, sc, ln in artists:
            a = float(np.clip((yr - x) / 0.6 + 0.0, 0, 1)) if yr >= x else 0.0
            for art in (t1, t2, sc, ln):
                if art is not None:
                    art.set_alpha(a if art is not ln else 0.6 * a)
            if yr >= x and (latest is None or (LAW[i]["year"], x) >= (LAW[latest[0]]["year"], latest[1])):
                latest = (i, x)
        if latest:
            ev = LAW[latest[0]]
            head.set_text(f"{ev['year']}  ·  {ev['short']}")
            head.set_color(OP[ev["operator"]] if ev["operator"] != "none" else INK)
            bar.set_color(head.get_color())
            pin = f"  ·  {ev['pinpoint']}" if ev.get("pinpoint") else ""
            sub.set_text(f"{ev['cite']}{pin}  ·  {STATUS[ev['status']]}")
            body.set_text("\n".join(textwrap.wrap(ev["holding"], 150)))
        return []

    anim = FuncAnimation(fig, update, frames=frames, interval=1000 / fps)
    anim.save(PUB / "law_timeline.mp4", writer=FFMpegWriter(fps=fps, bitrate=4000), dpi=120)
    plt.close(fig)


# --- 3. one set of facts, seven answers ---------------------------------------------------------

def _caption_seven(g, s):
    e0, e1, c0, c1 = s, s + 55, 0, 40
    if s < 0:
        return "The employer's delay starts first, so every chronological rule credits it in full."
    if s <= c1:
        return ("The contractor's delay starts first and the two overlap. The employer's delay still pushes completion "
                "out by 15 days, so the actual-delay test gives all 55 days. Strict sequence gives only the extra 15.")
    return ("The delays no longer overlap. Overlapping windows falls back to chronology, while the actual-delay "
            "test still sees the employer's delay adding 15 days, so it gives 55.")


def anim_seven_answers(fps=24):
    style()
    fig = plt.figure(figsize=(16, 9))
    axg = fig.add_axes([0.25, 0.70, 0.70, 0.17])
    axb = fig.add_axes([0.25, 0.17, 0.70, 0.46])
    fig.text(0.04, 0.95, "One set of facts, seven legal answers", fontsize=20, fontweight="bold")
    fig.text(0.04, 0.915, "A 40-day contractor delay and a 55-day employer delay on parallel paths. "
             "Drag the employer's delay through time and watch the extension change.", fontsize=11.5, color=MUTED)
    cap = fig.text(0.04, 0.06, "", fontsize=12.5, wrap=True)
    sched = np.concatenate([np.linspace(-60, 140, fps * 9), np.full(fps * 2, 140), np.linspace(140, 10, fps * 5),
                            np.full(fps * 3, 10)])

    def draw(k):
        s = float(sched[k])
        g = two_path(s, 55.0)
        axg.clear()
        axg.set_xlim(-70, 200)
        axg.set_ylim(-0.6, 1.6)
        axg.set_yticks([0, 1])
        axg.set_yticklabels(["Employer\n(variation)", "Contractor\n(façade)"], fontsize=10)
        lo, hi = max(s, 0), min(s + 55, 40)
        if hi > lo:
            axg.add_patch(Rectangle((lo, -0.45), hi - lo, 1.9, facecolor="none", hatch="////", edgecolor=RULE, lw=0))
            axg.text((lo + hi) / 2, 1.5, "felt at the same time", ha="center", fontsize=9, color=MUTED)
        axg.barh(1, 40, left=0, color=CON, height=0.55)
        axg.barh(0, 55, left=s, color=EMP, height=0.55)
        axg.set_xlabel("project day the delaying effect is felt", fontsize=9.5)
        axg.spines["left"].set_visible(False)
        axb.clear()
        net = DOCTRINES["but_for"](g).net_delay
        for i, d in enumerate(RULES7):
            o = DOCTRINES[d](g)
            axb.barh(i, o.eot, color=OP[d], height=0.62)
            axb.barh(i, o.compensable, color="white", height=0.18, alpha=0.9)
            axb.text(o.eot + 1.2, i, f"{o.eot:.0f} days" + (f"  ({o.compensable:.0f} paid)" if o.compensable else ""),
                     va="center", fontsize=10.5)
        axb.set_yticks(range(len(RULES7)))
        axb.set_yticklabels([OP_NAME[d] + (" *" if d == "effective_cause" else "") for d in RULES7], fontsize=11)
        axb.invert_yaxis()
        axb.set_xlim(0, 80)
        axb.axvline(net, color=INK, lw=1, ls=":")
        axb.text(net, -0.85, f"project {net:.0f} days late", fontsize=9, color=MUTED, ha="center")
        axb.set_xlabel("extension of time (days)   ·   white stripe = paid days", fontsize=9.5)
        axb.spines["left"].set_visible(False)
        cap.set_text("\n".join(textwrap.wrap(_caption_seven(g, s), 150)) +
                     "\n* the only rule that reproduces all five English cases tested")
        return []

    anim = FuncAnimation(fig, draw, frames=len(sched), interval=1000 / fps)
    anim.save(PUB / "seven_answers.mp4", writer=FFMpegWriter(fps=fps, bitrate=4000), dpi=120)
    draw(int(fps * 3.6))
    save(fig, PUB / "seven_answers_still.png", dpi=180)


# --- 4. the cliff edge ---------------------------------------------------------------------------

def anim_cliff_edge(fps=24):
    style()
    Ls = np.arange(0, 81, 1.0)
    rows = []
    for L in Ls:
        g = two_path(10.0, L, c_start=0.0, c_days=40.0)
        rows.append({d: DOCTRINES[d](g).eot for d in ("effective_cause", "first_in_time", "as_planned_impact")})
    R = pd.DataFrame(rows, index=Ls)
    fig = plt.figure(figsize=(16, 9))
    ax = fig.add_axes([0.07, 0.14, 0.62, 0.7])
    side = fig.add_axes([0.73, 0.14, 0.24, 0.7])
    side.axis("off")
    fig.text(0.04, 0.95, "The cliff edge in the actual-delay test", fontsize=20, fontweight="bold")
    fig.text(0.04, 0.915, "The contractor's 40-day delay comes first. The employer's delay starts on day 10 "
             "on a parallel path and grows.", fontsize=11.5, color=MUTED)
    frames = len(Ls) + fps * 3

    def draw(k):
        j = min(k, len(Ls) - 1)
        ax.clear()
        for d, ls in (("as_planned_impact", "--"), ("first_in_time", ":"), ("effective_cause", "-")):
            ax.plot(Ls[: j + 1], R[d].values[: j + 1], ls=ls, lw=3 if d == "effective_cause" else 2, color=OP[d],
                    label=OP_NAME[d], drawstyle="steps-post" if d == "effective_cause" else "default")
        ax.set_xlim(0, 80)
        ax.set_ylim(-3, 85)
        ax.axvline(40, color=RULE, lw=1)
        ax.text(40.5, 80, "employer delay = contractor delay", fontsize=9, color=MUTED)
        ax.set_xlabel("employer delay (days)")
        ax.set_ylabel("extension of time (days)")
        ax.legend(loc="upper left", fontsize=11)
        if j >= 41:
            ax.annotate("one more day of employer delay\n= 41 days of extension", xy=(41, 41), xytext=(50, 18),
                        fontsize=11, arrowprops=dict(arrowstyle="->", color=INK))
        side.clear()
        side.axis("off")
        L = Ls[j]
        side.text(0, 0.95, f"Employer delay: {L:.0f} days", fontsize=15, fontweight="bold")
        side.text(0, 0.86, f"Actual-delay test: {R.effective_cause.values[j]:.0f} days", fontsize=13, color=OP["effective_cause"])
        side.text(0, 0.80, f"Strict sequence: {R.first_in_time.values[j]:.0f} days", fontsize=13, color=OP["first_in_time"])
        side.text(0, 0.74, f"As-planned impact: {R.as_planned_impact.values[j]:.0f} days", fontsize=13, color=OP["as_planned_impact"])
        msg = ("Until the employer's delay is longer than the contractor's, it adds no actual delay to completion "
               "as then scheduled, so it earns nothing (Adyard, Saga). The moment it adds even one day, it is an "
               "effective cause and the contractor's concurrent delay no longer reduces the extension "
               "(Malmaison, Thomas Barnes).")
        side.text(0, 0.62, "\n".join(textwrap.wrap(msg, 44)), fontsize=11, va="top", color=INK)
        return []

    anim = FuncAnimation(fig, draw, frames=frames, interval=1000 / fps * 2.2)
    anim.save(PUB / "cliff_edge.mp4", writer=FFMpegWriter(fps=fps // 2, bitrate=3500), dpi=120)
    draw(frames - 1)
    save(fig, PUB / "cliff_edge_still.png", dpi=180)


# --- 5. static paper figures ------------------------------------------------------------------

def fig_fidelity():
    style()
    order = ["malmaison", "adyard", "saga", "walter_lilly", "thomas_barnes", "city_inn", "cyden"]
    rules = RULES7
    fig, ax = plt.subplots(figsize=(14.5, 5.8))
    ax.set_xlim(-3.4, len(rules))
    short = {"malmaison": "Malmaison (1999)", "adyard": "Adyard (2011)", "saga": "Saga Cruises (2016)",
             "walter_lilly": "Walter Lilly (2012)", "thomas_barnes": "Thomas Barnes (2022)",
             "city_inn": "City Inn (2010)", "cyden": "Cyden Homes (2018)"}
    ax.set_ylim(len(order), -1.2)
    ax.axis("off")
    for j, d in enumerate(rules):
        ax.text(j + 0.5, -0.45, "\n".join(textwrap.wrap(OP_NAME[d], 14)), ha="center", va="center", fontsize=9.5,
                fontweight="bold", color=OP[d])
    ax.text(-0.75, -0.45, "Court\n(ext. / paid)", ha="center", va="center", fontsize=9.5, fontweight="bold")
    for i, k in enumerate(order):
        c = CASES[k]
        g = c.game()
        mark = "●" if c.facts_verified else ("◐" if c.law_verified else "○")
        ax.text(-3.35, i + 0.5, mark, va="center", fontsize=11, family=SYM, color=INK)
        ax.text(-3.1, i + 0.5, short[k], va="center", fontsize=10.5)
        court = f"{c.court_eot:g}" + (f" / {c.court_compensable:g}" if c.court_compensable is not None else "")
        ax.text(-0.75, i + 0.5, court, ha="center", va="center", fontsize=10.5, family="Menlo", fontweight="bold")
        for j, d in enumerate(rules):
            o = DOCTRINES[d](g)
            ok = abs(o.eot - c.court_eot) < 1e-6 and (c.court_compensable is None or abs(o.compensable - c.court_compensable) < 1e-6)
            ax.add_patch(FancyBboxPatch((j + 0.06, i + 0.08), 0.88, 0.84, boxstyle="round,pad=0,rounding_size=0.06",
                                        facecolor=GOOD_SOFT if ok else "#f4f4f2", edgecolor="none"))
            ax.text(j + 0.5, i + 0.5, ("✓ " if ok else "") + f"{o.eot:g} / {o.compensable:g}", ha="center",
                    va="center", fontsize=9.5, family=SYM, color=GOOD if ok else MUTED,
                    fontweight="bold" if ok else "normal")
    ax.axhline(5, xmin=0, xmax=1, color=RULE, lw=1)
    ax.text(-3.35, len(order) + 0.35, "●  facts and law checked against the judgment     ◐  law checked, facts "
            "illustrative     ○  secondary source", fontsize=9, color=MUTED, va="top", family=SYM)
    ax.set_title("Which rule reproduces which decision? (extension / paid days)", fontsize=14)
    save(fig, PUB / "fidelity_matrix.png")


def fig_money_vs_time():
    style()
    order = ["thomas_barnes", "adyard", "saga", "malmaison"]
    eng = ["first_in_time", "effective_cause", "overlap_concurrency", "as_planned_impact"]
    fig, ax = plt.subplots(figsize=(11, 4.4))
    for i, k in enumerate(order):
        g = CASES[k].game()
        t = [DOCTRINES[d](g).eot for d in eng]
        m = [DOCTRINES[d](g).compensable for d in eng]
        y = i
        ax.plot([min(t), max(t)], [y + 0.12, y + 0.12], color=EMP, lw=7, alpha=0.35, solid_capstyle="round")
        ax.scatter(t, [y + 0.12] * 4, color=[OP[d] for d in eng], s=55, zorder=3)
        ax.plot([min(m), max(m) + 0.01], [y - 0.16, y - 0.16], color=INK, lw=7, alpha=0.8, solid_capstyle="round")
        ax.text(max(t) + 3, y + 0.12, f"time: {min(t):g}–{max(t):g} days", va="center", fontsize=10, color=EMP)
        ax.text(max(m) + 3, y - 0.16, f"money: {max(m):g} days, every reading", va="center", fontsize=10)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([CASES[k].name.split(" v ")[0] for k in order], fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel("days")
    ax.set_xlim(-5, 175)
    ax.set_title("Across the English readings, time diverges but money converges (Proposition 1)")
    ax.legend(handles=[Line2D([], [], marker="o", ls="", color=OP[d], label=OP_NAME[d]) for d in eng],
              loc="lower right", fontsize=9)
    save(fig, PUB / "money_vs_time.png")


def fig_synthetic():
    style()
    df = pd.read_csv(ROOT / "outputs" / "v2" / "e2_divergence_dataset.csv")
    d = df[df.net_delay > 0]
    thr = [0.5, 7, 14, 30]
    share = [(d.english_spread > t).mean() * 100 for t in thr]
    from sklearn.metrics import roc_auc_score, roc_curve
    from sklearn.model_selection import train_test_split
    from xgboost import XGBClassifier
    from cdx.synth import EX_ANTE
    yb = (df.english_spread > 7).astype(int)
    Xtr, Xte, ytr, yte = train_test_split(df[EX_ANTE], yb, test_size=0.25, random_state=2026, stratify=yb)
    p = XGBClassifier(n_estimators=400, max_depth=4, learning_rate=0.05, random_state=2026).fit(Xtr, ytr).predict_proba(Xte)[:, 1]
    fpr, tpr, _ = roc_curve(yte, p)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw={"width_ratios": [1.3, 1]})
    a1.bar(range(4), share, color=[OP["effective_cause"]] * 4, alpha=0.85, width=0.6)
    for i, v in enumerate(share):
        a1.text(i, v + 1, f"{v:.0f}%", ha="center", fontsize=11, fontweight="bold")
    a1.set_xticks(range(4))
    a1.set_xticklabels([f"> {t:g} days" if t >= 1 else "any" for t in thr])
    a1.set_ylabel("% of delayed programmes")
    a1.set_title("How often the English readings disagree")
    a1.set_ylim(0, max(share) * 1.25)
    a2.plot(fpr, tpr, color=EMP, lw=2.5)
    a2.plot([0, 1], [0, 1], color=RULE, ls="--")
    a2.fill_between(fpr, tpr, alpha=0.12, color=EMP)
    a2.set_xlabel("false positive rate")
    a2.set_ylabel("true positive rate")
    a2.set_title(f"Flagging it in advance (AUC {roc_auc_score(yte, p):.2f})")
    a2.text(0.45, 0.2, "screen uses only information\navailable before the joint\nschedule analysis", fontsize=9.5, color=MUTED)
    fig.suptitle("6,000 synthetic programmes", x=0.01, ha="left", fontsize=10, color=MUTED, y=1.02)
    save(fig, PUB / "synthetic_summary.png")


# --- 6. Package 5 (anonymised, gitignored) ----------------------------------------------------

def p5_figures():
    out = ROOT / "outputs" / "package5"
    if not (out / "notice_scenarios.csv").exists():
        print("Package 5 outputs missing; run run_package5_xai.py first")
        return None
    style()
    N = pd.read_csv(out / "notice_scenarios.csv")
    N["damages_pct"] = np.minimum(N.contractor_bears_days * 0.05, 10.0)
    fig, ax = plt.subplots(figsize=(11, 4.4))
    y = np.arange(len(N))
    ax.barh(y - 0.2, N.eot_days, height=0.36, color=EMP, label="extension (days)")
    ax.barh(y + 0.2, N.paid_days, height=0.36, color=INK, label="paid (days)")
    for i, r in N.iterrows():
        ax.text(max(r.eot_days, 5) + 6, i - 0.2, f"{r.eot_days:.0f}", va="center", fontsize=10)
        ax.text(max(r.paid_days, 5) + 6, i + 0.2, f"{r.paid_days:.0f}", va="center", fontsize=10)
        ax.text(560, i, f"damages {r.damages_pct:.1f}% of price" + ("  (cap)" if r.damages_pct >= 10 else ""),
                va="center", fontsize=10, color=BAD if r.damages_pct > 0 else GOOD)
    ax.set_yticks(y)
    ax.set_yticklabels(N.scenario, fontsize=10.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 760)
    ax.set_xlabel("days")
    ax.legend(loc="lower right", fontsize=9.5)
    ax.set_title("Real road project: the 28-day notice condition outweighs the concurrency rule")
    save(fig, PRIV / "p5_notice.png")

    tg = [("eot_gateway", "Extension"), ("paid_gateway", "Paid days"), ("ld_days_gateway", "Days the contractor carries")]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4), sharey=True)
    feats = None
    for ax, (t, title) in zip(axes, tg):
        s = pd.read_csv(out / f"shap_{t}.csv")
        if feats is None:
            feats = list(s.sort_values("mean_abs_shap", ascending=False).feature)[:8]
        s = s.set_index("feature").reindex(feats)
        ax.barh(range(len(feats)), s.mean_abs_shap, color=[EMP if "Employer" in f or "access" in f.lower()
                                                           else CON if "ontractor" in f else NEU for f in feats])
        ax.set_title(title, fontsize=12)
        ax.set_xlabel("mean |SHAP| (days)")
    axes[0].set_yticks(range(len(feats)))
    axes[0].set_yticklabels(feats, fontsize=9.5)
    axes[0].invert_yaxis()
    fig.suptitle("What the outcome turns on: explainable model over 1,500 project variants", x=0.01, ha="left",
                 fontsize=14, fontweight="bold", y=1.03)
    save(fig, PRIV / "p5_drivers.png")
    return N


_PLACES = {}


def anon(label: str) -> str:
    """Replace place names in activity labels (e.g. 'X-Y Road(25km)') with neutral section letters."""
    import re
    def sub(m):
        key = m.group(0)
        _PLACES.setdefault(key, f"Road section {chr(65 + len(_PLACES))}")
        return _PLACES[key]
    return re.sub(r"[A-Z][A-Za-z]+(?:-[A-Z][A-Za-z]+)+ Road ?(?:\(\d+\s*km\)?)?|[A-Z][a-z]+ Road ?\(\d+\s*km\)?",
                  sub, label)


def anim_backprop(fps=24):
    out = ROOT / "outputs" / "package5"
    reg_path = out / "event_register.csv"
    if not reg_path.exists():
        return
    import run_package5_xai as p5
    ns, lo, ap, T, events, reg, loe = p5.build()
    g = DelayGame(ap, events, reference=T)
    order = list(reg.sort_values("slip_days", ascending=False).event_id)
    base = lambda i: i.split("|")[0]
    style()
    r = reg.sort_values("as_planned_start").reset_index(drop=True)
    fig = plt.figure(figsize=(16, 9))
    ax = fig.add_axes([0.25, 0.12, 0.72, 0.68])
    fig.text(0.04, 0.95, "Rebuilding a real programme backwards from the contract date", fontsize=20, fontweight="bold")
    fig.text(0.04, 0.915, "Each workfront moves back to the latest start that still meets the contractual completion. "
             "The completion marker shows how late the project is with the remaining slips.", fontsize=11.5, color=MUTED)
    status = fig.text(0.04, 0.85, "", fontsize=14, fontweight="bold")
    to_dt = lambda d: pd.Timestamp(d)
    steps = len(order)
    per = int(fps * 1.1)
    frames = per * steps + fps * 4
    T_end = pd.Timestamp(ap.date(T - 1e-6))

    def state(k):
        n_done = min(k // per, steps)
        frac = min(1.0, (k % per) / (per * 0.7)) if n_done < steps else 1.0
        return n_done, frac

    def draw(k):
        n_done, frac = state(k)
        done = set(order[:n_done])
        moving = order[n_done] if n_done < steps else None
        remaining = [e.id for e in events if base(e.id) not in done and base(e.id) != moving]
        late = g.v(remaining + ([e.id for e in events if base(e.id) == moving] if moving and frac < 1 else []))
        ax.clear()
        for i, x in r.iterrows():
            a, b = to_dt(x.as_planned_start), to_dt(x.impacted_start)
            if x.event_id in done:
                cur = a
            elif x.event_id == moving:
                cur = b - (b - a) * frac
            else:
                cur = b
            c = EMP if x.party == "E" else CON
            ax.plot([a, b], [i, i], color=GRID, lw=6, solid_capstyle="butt")
            ax.plot([a, cur], [i, i], color=c, lw=6, solid_capstyle="butt", alpha=0.25)
            ax.plot(cur, i, "o", color=c, ms=8)
            if x.event_id == moving:
                ax.text(b, i - 0.45, f"−{x.slip_days:.0f} d", fontsize=9.5, color=c, fontweight="bold")
        end = T_end + pd.Timedelta(days=late)
        ax.axvline(T_end, color=GOOD, lw=1.5, ls="--")
        ax.text(T_end - pd.Timedelta(days=12), -1.3, "contract completion", color=GOOD, fontsize=9.5, ha="right",
                va="center")
        ax.axvline(end, color=BAD, lw=2)
        ax.text(end + pd.Timedelta(days=12), -1.3, f"completion +{late:.0f} days", color=BAD, fontsize=10,
                ha="left", va="center", fontweight="bold")
        ax.set_yticks(range(len(r)))
        ax.set_yticklabels([f"{anon(a)[:26].rstrip('(')} · {gr[:20]}" for a, gr in zip(r.activity, r.group)], fontsize=9)
        ax.set_ylim(len(r) + 0.6, -1.8)
        ax.set_xlim(pd.Timestamp(2019, 3, 1), pd.Timestamp(2023, 10, 1))
        ax.legend(handles=[Patch(color=EMP, label="Employer: site access"), Patch(color=CON, label="Contractor: production")],
                  loc="lower left", fontsize=10)
        status.set_text(f"Delay to completion: {late:.0f} days" + ("   ·   reconstruction complete" if n_done >= steps else ""))
        return []

    anim = FuncAnimation(fig, draw, frames=frames, interval=1000 / fps)
    anim.save(PRIV / "backpropagation.mp4", writer=FFMpegWriter(fps=fps, bitrate=4000), dpi=120)


# --- 7. LinkedIn carousel (portrait, 1080x1350) ------------------------------------------------

def carousel(N):
    style(bg=PAPER)
    W, H = 7.2, 9.0
    pages = []

    def page(title, kicker=None):
        fig = plt.figure(figsize=(W, H))
        fig.patch.set_facecolor(PAPER)
        if kicker:
            fig.text(0.07, 0.93, kicker.upper(), fontsize=10, color=MUTED, fontweight="bold")
        fig.text(0.07, 0.885, "\n".join(textwrap.wrap(title, 30)), fontsize=24, fontweight="bold", va="top")
        fig.text(0.07, 0.03, "One schedule, many laws · concurrent delay + explainable AI", fontsize=8.5, color=MUTED)
        pages.append(fig)
        return fig

    f = page("Same delays. Different law. Different answer.", "Concurrent delay")
    f.text(0.07, 0.62, "\n".join(textwrap.wrap(
        "England, Scotland, the SCL Protocol, FIDIC and NEC4 each decide concurrent delay differently. "
        "I modelled one programme once and wrote each legal approach as a rule on top of it.", 40)),
        fontsize=14, va="top", color=INK)
    f.text(0.07, 0.30, "Swipe →", fontsize=16, color=EMP, fontweight="bold")

    f = page("One set of facts, seven answers", "The problem")
    ax = f.add_axes([0.38, 0.18, 0.55, 0.55])
    g = two_path(10.0, 55.0)
    for i, d in enumerate(RULES7):
        o = DOCTRINES[d](g)
        ax.barh(i, o.eot, color=OP[d], height=0.6)
        ax.text(o.eot + 1, i, f"{o.eot:.0f}", va="center", fontsize=11, fontweight="bold")
    ax.set_yticks(range(7))
    ax.set_yticklabels([OP_NAME[d] for d in RULES7], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlim(0, 70)
    ax.set_xlabel("days of extension")
    ax.spines["left"].set_visible(False)
    f.text(0.07, 0.78, "40-day contractor delay first, then a 55-day employer delay.", fontsize=11.5, color=MUTED)

    f = page("25 years of case law in one picture", "Evolution of the law")
    ax = f.add_axes([0.07, 0.08, 0.86, 0.72])
    ax.axis("off")
    evs = sorted(LAW, key=lambda e: (e["year"], e["lane"]))
    n = len(evs)
    for i, ev in enumerate(evs):
        y = 1 - i / (n - 1)
        c = OP[ev["operator"]]
        ax.plot([0.13, 0.13], [0, 1], color=GRID, lw=3, zorder=0)
        ax.scatter([0.13], [y], s=60, color=c if ev["status"] in ("verified", "quoted") else PAPER, edgecolor=c, lw=2, zorder=2)
        ax.text(0.0, y, str(ev["year"]), fontsize=9.5, va="center", color=MUTED, family="Menlo")
        ax.text(0.18, y, ev["short"], fontsize=10, va="center", fontweight="bold")
        ax.text(0.66, y, ev["rule"], fontsize=9, va="center", color=c)
    ax.set_ylim(-0.04, 1.04)
    ax.set_xlim(0, 1)

    f = page("SHAP answers a different question", "Existing practice")
    ax = f.add_axes([0.07, 0.12, 0.86, 0.66])
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.0, 0.97, "SHAP used as the apportionment", fontsize=13, fontweight="bold", color=BAD, va="top")
    for k, t in enumerate(["Measures against the average project, not the contract date",
                           "Gives one split; the law has several",
                           "Ignores which delay came first",
                           "Checked against itself"]):
        ax.text(0.0, 0.86 - k * 0.085, "\u2717", fontsize=12, va="top", family=SYM, color=BAD)
        ax.text(0.05, 0.86 - k * 0.085, t, fontsize=12, va="top")
    ax.text(0.0, 0.47, "XAI used as the explanation", fontsize=13, fontweight="bold", color=GOOD, va="top")
    for k, t in enumerate(["Causal model of the programme, measured to the contract date",
                           "Each legal approach written as an explicit rule",
                           "Tested against decided cases",
                           "SHAP explains what moves the answer"]):
        ax.text(0.0, 0.36 - k * 0.085, "\u2713", fontsize=12, va="top", family=SYM, color=GOOD)
        ax.text(0.05, 0.36 - k * 0.085, t, fontsize=12, va="top")

    f = page("Only one rule fits all five English cases", "What the cases decide")
    ax = f.add_axes([0.07, 0.15, 0.86, 0.6])
    ax.axis("off")
    cases = ["malmaison", "adyard", "saga", "walter_lilly", "thomas_barnes"]
    rules = ["effective_cause", "first_in_time", "overlap_concurrency", "as_planned_impact"]
    for j, d in enumerate(rules):
        ax.text(j + 1.5, -0.6, "\n".join(textwrap.wrap(OP_NAME[d], 11)), ha="center", fontsize=9, fontweight="bold", color=OP[d])
    for i, k in enumerate(cases):
        c = CASES[k]
        ax.text(0, i, c.name.split(" v ")[0].replace("Henry Boot", "Malmaison"), fontsize=10.5, va="center")
        for j, d in enumerate(rules):
            o = DOCTRINES[d](c.game())
            ok = abs(o.eot - c.court_eot) < 1e-6 and (c.court_compensable is None or abs(o.compensable - c.court_compensable) < 1e-6)
            ax.text(j + 1.5, i, "✓" if ok else "✗", ha="center", va="center", fontsize=18, color=GOOD if ok else BAD,
                    family=SYM)
    ax.set_xlim(0, 5)
    ax.set_ylim(len(cases) - 0.3, -1.2)
    f.text(0.07, 0.10, "\n".join(textwrap.wrap("Actual-delay test: the employer's delay must actually push completion "
                                               "out as then scheduled. If it does, concurrent contractor delay doesn't cut "
                                               "the extension.", 58)), fontsize=10.5, color=INK)

    f = page("Time diverges. Money converges.", "A result you can prove")
    ax = f.add_axes([0.12, 0.2, 0.8, 0.5])
    g = CASES["thomas_barnes"].game()
    eng = ["first_in_time", "effective_cause", "overlap_concurrency", "as_planned_impact"]
    for i, d in enumerate(eng):
        o = DOCTRINES[d](g)
        ax.barh(i, o.eot, color=OP[d], height=0.55)
        ax.barh(i, o.compensable, color=INK, height=0.2)
        ax.text(o.eot + 2, i, f"{o.eot:.0f} time · {o.compensable:.0f} paid", va="center", fontsize=10)
    ax.set_yticks(range(4))
    ax.set_yticklabels([OP_NAME[d] for d in eng], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlim(0, 175)
    ax.spines["left"].set_visible(False)
    f.text(0.07, 0.76, "Thomas Barnes facts: every English reading pays 27 days.", fontsize=11.5, color=MUTED)

    f = page("The cliff edge", "A result you can prove")
    ax = f.add_axes([0.12, 0.2, 0.8, 0.5])
    Ls = np.arange(0, 81)
    ax.step(Ls, [DOCTRINES["effective_cause"](two_path(10, L)).eot for L in Ls], where="post", color=OP["effective_cause"], lw=3)
    ax.plot(Ls, [DOCTRINES["first_in_time"](two_path(10, L)).eot for L in Ls], color=OP["first_in_time"], ls=":", lw=2)
    ax.set_xlabel("employer delay (days); contractor's 40-day delay came first")
    ax.set_ylabel("extension (days)")
    ax.annotate("one extra day\n= 41 days", xy=(41, 41), xytext=(52, 15), arrowprops=dict(arrowstyle="->"), fontsize=10.5)
    f.text(0.07, 0.76, "Small measurement differences near the threshold swing the answer.", fontsize=11.5, color=MUTED)

    if N is not None:
        f = page("On a real project, notice beat doctrine", "Real road programme (anonymised)")
        ax = f.add_axes([0.42, 0.22, 0.5, 0.48])
        y = np.arange(len(N))
        ax.barh(y, N.eot_days, color=EMP, height=0.55)
        ax.barh(y, N.paid_days, color=INK, height=0.2)
        for i, rr in N.iterrows():
            ax.text(max(rr.eot_days, 0) + 8, i, f"{rr.eot_days:.0f} / {rr.paid_days:.0f}", va="center", fontsize=10)
        ax.set_yticks(y)
        ax.set_yticklabels(["\n".join(textwrap.wrap(s, 20)) for s in N.scenario], fontsize=9.5)
        ax.invert_yaxis()
        ax.set_xlim(0, 600)
        ax.set_xlabel("extension / paid (days)")
        ax.spines["left"].set_visible(False)
        f.text(0.07, 0.76, "\n".join(textwrap.wrap("FIDIC 1999, 453 days late. The concurrency rules differed by 4 days. "
                                                   "One missed 28-day notice took the paid days to zero.", 52)),
               fontsize=11, color=MUTED, va="top")

    f = page("What the XAI is for", "So what")
    f.text(0.07, 0.66, "\n".join(textwrap.wrap(
        "Not deciding who is liable. Showing what the answer turns on: who controlled access, whether notice "
        "was given, and only then which concurrency rule applies.", 38)), fontsize=14, va="top")
    f.text(0.07, 0.30, "Work in progress. Challenge welcome.", fontsize=13, color=EMP, fontweight="bold")

    PRIV.mkdir(parents=True, exist_ok=True)
    with PdfPages(PRIV / "linkedin_carousel.pdf") as pdf:
        for i, fig in enumerate(pages, 1):
            fig.savefig(PRIV / f"carousel_{i:02d}.png", dpi=150)
            pdf.savefig(fig)
            plt.close(fig)


def main():
    PUB.mkdir(parents=True, exist_ok=True)
    steps = [("law timeline (static)", fig_law_timeline), ("fidelity matrix", fig_fidelity),
             ("money vs time", fig_money_vs_time), ("synthetic summary", fig_synthetic),
             ("law timeline (animation)", anim_law_timeline), ("seven answers (animation)", anim_seven_answers),
             ("cliff edge (animation)", anim_cliff_edge)]
    for name, fn in steps:
        fn()
        print("done:", name)
    N = p5_figures()
    print("done: Package 5 figures")
    anim_backprop()
    print("done: back-propagation animation")
    carousel(N)
    print("done: carousel")


if __name__ == "__main__":
    main()
