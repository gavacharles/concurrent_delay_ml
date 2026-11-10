"""Real-programme study: Package 5 road upgrading (impacted MS Project programme).\n\nContract: FIDIC 1999 Yellow Book, no Special Provision on concurrency; Employer responsible for site\naccess and payment (confirmed by the user, 2026-11-10). Governing law assumed to be Uganda.

Inputs (kept out of git; see data/programmes/):
  package5.mspdi.xml          MS Project file converted with MPXJ
  package5_splits.json        task interruptions extracted with MPXJ
  work program.pdf            Contractor's work programme report (27 Aug 2022)

What is documented vs assumed
  - Network, durations, links, constraints, interruptions: from the programme (engine reproduces
    MS Project's dates for every activity).
  - Employer event: Section 2 pavement works held to start no earlier than 21 Aug 2022 (programme);
    the report (section 6) expects all land by 30 Sep 2022 -> a 40-day land-access delay.
  - Contractor event: HYPOTHETICAL. The programme records no contractor delay on the driving path,
    so a contractor plant/aggregate readiness delay is assumed and swept over size and timing.

Run: python src/experiments/run_real.py   -> outputs/real/ (gitignored: derived from the programme)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

from cdx import DelayEvent, DelayGame
from cdx.contracts import evaluate_regimes
from cdx.doctrines import DOCTRINES, ENGLISH_READINGS, LABELS, party_values, windows_analysis
from cdx.network import NetworkSchedule, Task, load_mspdi, logic_only, programme_health

DATA = ROOT / "data" / "programmes"
OUT = ROOT / "outputs" / "real"
PLOTS = OUT / "plots"
SEED = 2026
SUB_BASE = "466"                      # driving chain starts here (SNET 21 Aug 2022)
LAND_DATE, LAND_EXPECTED = datetime(2022, 8, 21), datetime(2022, 9, 30)
C_DAYS, C_FELT = 30, datetime(2022, 8, 1)   # hypothetical contractor readiness delay
EMP, CON, EMP_SOFT, CON_SOFT, INK, MUTED, GRID = ("#2456a6", "#d25a14", "#c9d7f0", "#f6d9c6", "#1b1f24",
                                                  "#5b6470", "#e8eae4")
SHOW = ["contractual_exclusion", "first_in_time", "nec4_prospective", "city_inn", "effective_cause",
        "overlap_concurrency", "as_planned_impact"]
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 11, "axes.titleweight": "bold", "axes.edgecolor": MUTED})


def load():
    ns = load_mspdi(str(DATA / "package5.mspdi.xml"), "Package 5")
    splits = json.load(open(DATA / "package5_splits.json"))
    rows = []
    for uid, r in splits.items():
        for (a0, b0), (a1, b1) in zip(r, r[1:]):
            rows.append({"task_uid": uid, "activity": ns.tasks[uid].name, "interrupted_from": b0[:10],
                         "resumed": a1[:10],
                         "days": (datetime.fromisoformat(a1[:10]) - datetime.fromisoformat(b0[:10])).days - 1})
    return ns, pd.DataFrame(rows)


def with_access_activities(lo: NetworkSchedule, target: str) -> NetworkSchedule:
    """Replace the target's start constraint by two zero-duration 'ready' activities that
    precede it: employer land access and contractor plant/aggregate readiness. Baseline dates
    are unchanged; each party's delay becomes a causal event on its own activity."""
    t = lo.tasks[target]
    tasks = {u: Task(**{**x.__dict__}) for u, x in lo.tasks.items()}
    tasks[target].snet = None
    tasks["LAND_S2"] = Task("LAND_S2", "Land access, Section 2 (employer)", 0.0, snet=t.snet)
    tasks["PLANT_S2"] = Task("PLANT_S2", "Plant and aggregate ready (contractor)", 0.0, snet=t.snet)
    links = list(lo.links) + [("LAND_S2", target, "FS", 0.0), ("PLANT_S2", target, "FS", 0.0)]
    return NetworkSchedule(tasks, links, origin=lo.origin, name="Package 5 (analysis model)")


def day(ns, dt):
    return float((dt - ns.origin).days)


def scenario(net, e_days=None, c_days=C_DAYS, c_felt=C_FELT, cache=None):
    e_days = (LAND_EXPECTED - LAND_DATE).days if e_days is None else e_days
    ev = [DelayEvent("E_land", "E", "LAND_S2", float(e_days), day(net, LAND_DATE)),
          DelayEvent("C_plant", "C", "PLANT_S2", float(c_days), day(net, c_felt))]
    return DelayGame(net, ev, cache=cache)


def split_bars(ax, res, net_delay, keys):
    for i, d in enumerate(keys):
        o = res[d]
        ax.barh(i, o.compensable, color=EMP)
        ax.barh(i, o.eot - o.compensable, left=o.compensable, color=EMP_SOFT, edgecolor=EMP, lw=0.8)
        ax.barh(i, net_delay - o.eot, left=o.eot, color=CON_SOFT, edgecolor=CON, lw=0.8)
        ax.text(net_delay + 1, i, f"EOT {o.eot:.0f}d · paid {o.compensable:.0f}d", va="center", fontsize=8.5)
    ax.set_yticks(range(len(keys)))
    ax.set_yticklabels([LABELS[d] for d in keys], fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlim(0, net_delay * 1.45)
    ax.legend(handles=[Patch(color=EMP, label="extension, paid"),
                       Patch(facecolor=EMP_SOFT, edgecolor=EMP, label="extension, time only"),
                       Patch(facecolor=CON_SOFT, edgecolor=CON, label="contractor's own delay")],
              loc="upper center", bbox_to_anchor=(0.4, -0.13), ncol=3, frameon=False, fontsize=8.5)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    ns, inter = load()
    L = []

    # --- 1. engine validation, programme health, interruption criticality --------------------
    extra = inter.groupby("task_uid").days.sum().to_dict()
    es, ef = ns.forward(extra)
    match = sum(1 for u, t in ns.tasks.items() if not t.summary
                and abs(es[u] - t.ms_start) < 0.05 and abs(ef[u] - t.ms_finish) < 0.05)
    lo = logic_only(ns, extra)
    inter["completion_effect_days"] = [lo.finish({r.task_uid: r.days}) - lo.finish() for r in inter.itertuples()]
    inter.to_csv(OUT / "interruptions.csv", index=False)
    h = programme_health(ns)
    pd.Series(h).to_csv(OUT / "programme_health.csv", header=["value"])
    L += [f"Engine reproduces MS Project start and finish for {match}/{len(ns.leaves)} activities.",
          f"Completion {ns.date(ns.finish(extra) - 1e-6).date()}; driven by Sub base start-no-earlier-than "
          f"{LAND_DATE.date()} -> base -> prime coat -> surfacing -> lined ditches -> handover.",
          f"The {len(inter)} interruptions change completion by {inter.completion_effect_days.abs().max():.0f} days "
          f"(none is on the driving path in the logic-only model)."]

    checks = [("No predecessor", h["no_predecessor_pct"]), ("No successor", h["no_successor_pct"]),
              ("Hard date constraints", h["hard_constraints_pct"]), ("Links with lags", h["links_with_lag_pct"]),
              ("Non finish-to-start links", h["non_FS_links_pct"]), ("Activities > 44 days", h["long_activities_gt_44d_pct"])]
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.barh(range(len(checks)), [v for _, v in checks], color=[CON if v > 5 else EMP for _, v in checks])
    ax.axvline(5, color=INK, lw=1, ls="--")
    ax.text(5.5, len(checks) - 0.4, "5% guide", fontsize=8, color=INK)
    for i, (_, v) in enumerate(checks):
        ax.text(v + 1, i, f"{v:.0f}%", va="center", fontsize=8.5)
    ax.set_yticks(range(len(checks)))
    ax.set_yticklabels([k for k, _ in checks], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("% of activities (links for the two link checks)")
    ax.set_title("Package 5 programme: is it fit for a causal delay analysis?", loc="left")
    fig.tight_layout()
    fig.savefig(PLOTS / "real_programme_health.png", dpi=180)
    plt.close(fig)

    # --- 2. the scenario: documented land delay + hypothetical contractor delay ----------------
    net = with_access_activities(lo, SUB_BASE)
    assert abs(net.finish() - lo.finish()) < 1e-6, "access activities must not change the baseline"
    g = scenario(net)
    pv = party_values(g)
    res = {k: f(g) for k, f in DOCTRINES.items()}
    base_end = net.date(net.planned_finish - 1e-6).date()
    L += [f"Scenario: land {LAND_DATE.date()} -> {LAND_EXPECTED.date()} (+{pv.vE:.0f} d at completion); contractor plant/"
          f"aggregate readiness +{C_DAYS} d felt from {C_FELT.date()} (hypothetical) -> +{pv.vC:.0f} d. "
          f"Both: +{pv.vN:.0f} d (completion {base_end} -> {net.date(net.planned_finish + pv.vN - 1e-6).date()}).",
          "Outcomes: " + "; ".join(f"{LABELS[d].split(' (')[0]} {res[d].eot:.0f}/{res[d].compensable:.0f}" for d in SHOW)]
    fig, ax = plt.subplots(figsize=(9, 4))
    split_bars(ax, res, pv.vN, SHOW)
    ax.set_title(f"Package 5: {pv.vN:.0f} days of delay to completion, seven legal answers", loc="left")
    ax.set_xlabel("days")
    fig.tight_layout()
    fig.savefig(PLOTS / "real_doctrine_split.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    reg = pd.DataFrame(evaluate_regimes(g)).T
    reg.to_csv(OUT / "contract_regimes.csv")

    # --- 3. phase map on the real network: contractor size x timing ----------------------------
    sizes = np.arange(0, 91, 3)
    felt = np.arange(-150, 61, 5)
    cache = {}
    S = np.zeros((len(sizes), len(felt)))
    G = np.zeros_like(S)
    for i, c in enumerate(sizes):
        for j, off in enumerate(felt):
            gg = scenario(net, c_days=c, c_felt=LAND_DATE + pd.Timedelta(days=int(off)), cache=None)
            eng = [DOCTRINES[d](gg).eot for d in ENGLISH_READINGS]
            S[i, j] = max(eng) - min(eng)
            G[i, j] = DOCTRINES["effective_cause"](gg).eot
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    ext = [felt[0], felt[-1], sizes[0], sizes[-1]]
    im0 = axes[0].imshow(S, origin="lower", aspect="auto", extent=ext, cmap="Purples", vmin=0)
    axes[0].set_title("Gap between the English readings (days)", loc="left", fontsize=10)
    fig.colorbar(im0, ax=axes[0], shrink=0.85)
    im1 = axes[1].imshow(G, origin="lower", aspect="auto", extent=ext, cmap="Blues", vmin=0)
    axes[1].set_title("Extension under the actual-delay gateway (days)", loc="left", fontsize=10)
    fig.colorbar(im1, ax=axes[1], shrink=0.85)
    for ax in axes:
        ax.axvline(0, color=INK, lw=0.8, ls=":")
        ax.axhline(40, color=INK, lw=0.8, ls="--")
        ax.plot((C_FELT - LAND_DATE).days, C_DAYS, "o", mfc="none", mec=CON, ms=9, mew=2)
        ax.set_xlabel("contractor delay felt (days relative to 21 Aug 2022 land date)")
    axes[0].set_ylabel("contractor delay (days)")
    fig.suptitle("Package 5: where the law changes the answer (land delay fixed at 40 days; ring = scenario)",
                 fontsize=10.5, x=0.02, ha="left")
    fig.tight_layout()
    fig.savefig(PLOTS / "real_phase_map.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    L += [f"Phase map: English readings disagree on {100 * (S > 0.5).mean():.0f}% of contractor size/timing combinations; "
          f"max gap {S.max():.0f} d. Gateway cliff (contractor delay felt first): contractor 39 d -> EOT {G[sizes == 39][0][0]:.0f} d; "
          f"contractor 42 d -> EOT {G[sizes == 42][0][0]:.0f} d."]

    # --- 4. windows analysis -------------------------------------------------------------------
    lengths = np.arange(7, 184, 7)
    W = [[windows_analysis(g, float(Lw), float(o)).eot for o in np.arange(0, Lw, 1)] for Lw in lengths]
    share40 = [np.mean(np.array(w) > 39.5) for w in W]
    fig, ax = plt.subplots(figsize=(8.5, 3.2))
    ax.bar(lengths, share40, width=5, color=EMP)
    ax.set_ylim(0, 1)
    ax.set_xlabel("window length (days)")
    ax.set_ylabel("share of window start dates\ngiving the full 40 days")
    ax.set_title("Windows analysis: the same facts give 10 or 40 days depending on where the windows fall", loc="left",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(PLOTS / "real_windows.png", dpi=180)
    plt.close(fig)
    L += [f"Windows: 30-day windows give the full 40 d for {100 * share40[3]:.0f}% of possible start dates "
          f"(10 d otherwise); 91-day windows {100 * share40[12]:.0f}%."]

    # --- 5. duration uncertainty -----------------------------------------------------------------
    rng = np.random.default_rng(SEED)
    mc = []
    for _ in range(300):
        tasks = {u: Task(**{**t.__dict__}) for u, t in net.tasks.items()}
        for u, t in tasks.items():
            if not t.summary and t.duration > 0:
                t.duration *= rng.triangular(0.9, 1.0, 1.25)
        sched = NetworkSchedule(tasks, net.links, origin=net.origin)
        gg = scenario(sched, e_days=40 * rng.triangular(0.75, 1, 1.25), c_days=C_DAYS * rng.triangular(0.6, 1, 1.6))
        row = {d: DOCTRINES[d](gg).eot for d in SHOW}
        row["net"] = party_values(gg).vN
        mc.append(row)
    M = pd.DataFrame(mc)
    M.to_csv(OUT / "monte_carlo.csv", index=False)
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    for i, d in enumerate(SHOW):
        q = M[d].quantile([.05, .25, .5, .75, .95]).values
        ax.plot([q[0], q[4]], [i, i], color=MUTED, lw=1)
        ax.plot([q[1], q[3]], [i, i], color=EMP, lw=6, solid_capstyle="butt")
        ax.plot(q[2], i, "o", color=INK, ms=4)
    ax.set_yticks(range(len(SHOW)))
    ax.set_yticklabels([LABELS[d] for d in SHOW], fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlabel("extension of time (days): 50% band, 90% whiskers, median")
    ax.set_title("Uncertain durations and event sizes vs the choice of law", loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(PLOTS / "real_uncertainty.png", dpi=180)
    plt.close(fig)
    eng_spread = M[ENGLISH_READINGS if set(ENGLISH_READINGS) <= set(M) else SHOW].max(1) - \
        M[[d for d in ENGLISH_READINGS if d in M]].min(1)
    L += [f"Monte Carlo (300): P(English readings differ by >10 d) = {(eng_spread > 10).mean():.2f}; "
          + "; ".join(f"{d} {M[d].quantile(.05):.0f}-{M[d].quantile(.95):.0f}" for d in SHOW)
          + f". Gateway is two-peaked: P(EOT < 5 d) = {(M.effective_cause < 5).mean():.2f}, "
          f"P(EOT > 30 d) = {(M.effective_cause > 30).mean():.2f}."]

    # --- 6. XAI: where in this programme the choice of law matters -------------------------------
    import shap
    from sklearn.metrics import r2_score, roc_auc_score
    from sklearn.model_selection import train_test_split
    from xgboost import XGBClassifier, XGBRegressor
    tf = lo.total_float(probe=2.0)
    es0, ef0 = lo.forward()
    acts = [u for u in lo.leaves if lo.tasks[u].duration > 0 and tf[u] <= 400]
    rng = np.random.default_rng(SEED + 1)
    rows = []
    for _ in range(3000):
        a, b = rng.choice(acts, 2, replace=False)
        de, dc = float(rng.integers(5, 121)), float(rng.integers(5, 121))
        se, sc = round(es0[a] + rng.uniform(0, lo.tasks[a].duration)), round(es0[b] + rng.uniform(0, lo.tasks[b].duration))
        gg = DelayGame(lo, [DelayEvent("E", "E", a, de, se), DelayEvent("C", "C", b, dc, sc)])
        out = {d: DOCTRINES[d](gg).eot for d in ENGLISH_READINGS}
        p = party_values(gg)
        rows.append({"E_activity": a, "E_float": min(tf[a], 400), "C_float": min(tf[b], 400), "E_days": de, "C_days": dc,
                     "E_stand_alone": p.vE, "C_stand_alone": p.vC, "shared_days": p.overlap,
                     "start_gap_E_minus_C": se - sc,
                     "windows_overlap": float(max(0, min(se + de, sc + dc) - max(se, sc))),
                     "same_chain": float(lo.on_same_chain(a, b)), "E_first": float(se < sc),
                     "net_delay": p.vN, "english_spread": max(out.values()) - min(out.values())})
    D = pd.DataFrame(rows)
    D = D[D.net_delay > 0].reset_index(drop=True)
    D.to_csv(OUT / "hypothetical_pairs.csv", index=False)
    yb = (D.english_spread > 7).astype(int)
    if len(D) < 200 or yb.sum() < 30:
        L += [f"Activities with total float <= 400 d: {len(acts)} of {len(lo.leaves)}. Only {len(D)} of 3000 sampled "
              f"event pairs delay completion and {int(yb.sum())} split the English readings by >7 d: too little signal "
              f"for the divergence model on this programme (open ends, date constraints, SS-only chains)."]
        (OUT / "summary.txt").write_text("\n".join(L) + "\n")
        print("\n".join(L))
        print(reg[[c for c in ["label", "eot_lo", "eot_central", "eot_hi", "paid_lo", "paid_central", "paid_hi"] if c in reg]].to_string())
        return
    full = ["E_float", "C_float", "E_days", "C_days", "E_stand_alone", "C_stand_alone", "shared_days",
            "start_gap_E_minus_C", "windows_overlap", "same_chain", "E_first"]
    exante = ["E_float", "C_float", "E_days", "C_days", "start_gap_E_minus_C", "windows_overlap", "same_chain", "E_first"]
    Xtr, Xte, ytr, yte = train_test_split(D[full], D.english_spread, test_size=0.25, random_state=SEED)
    m = XGBRegressor(n_estimators=500, max_depth=5, learning_rate=0.05, subsample=0.9, random_state=SEED).fit(Xtr, ytr)
    r2 = r2_score(yte, m.predict(Xte))
    yb = (D.english_spread > 7).astype(int)
    Xtr2, Xte2, ytr2, yte2 = train_test_split(D[exante], yb, test_size=0.25, random_state=SEED, stratify=yb)
    clf = XGBClassifier(n_estimators=400, max_depth=4, learning_rate=0.05, random_state=SEED).fit(Xtr2, ytr2)
    auc = roc_auc_score(yte2, clf.predict_proba(Xte2)[:, 1])
    sv = shap.TreeExplainer(m)(Xte)
    plt.figure()
    shap.plots.beeswarm(sv, max_display=11, show=False)
    plt.title(f"Package 5: what makes the English readings disagree (test R² {r2:.2f})", fontsize=10)
    plt.tight_layout()
    plt.savefig(PLOTS / "real_shap_divergence.png", dpi=180)
    plt.close("all")
    pd.DataFrame({"feature": full, "mean_abs_shap": np.abs(sv.values).mean(0)}).sort_values(
        "mean_abs_shap", ascending=False).to_csv(OUT / "shap_importance.csv", index=False)
    L += [f"Activities with total float <= 400 d: {len(acts)} of {len(lo.leaves)}. "
          f"XAI on the real network: {len(D)} delaying event pairs among them; English readings differ by >7 d in "
          f"{100 * yb.mean():.0f}%. Explanatory model R² {r2:.2f}; ex-ante screening AUC {auc:.2f}."]

    (OUT / "summary.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    print("\nContract regimes (scenario):")
    print(reg[[c for c in ["label", "eot_lo", "eot_central", "eot_hi", "paid_lo", "paid_central", "paid_hi"] if c in reg]].to_string())


if __name__ == "__main__":
    main()
