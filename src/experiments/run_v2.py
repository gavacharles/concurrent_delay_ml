"""v2 experiments: E1 doctrinal fidelity, E2 explainable divergence model, E3 timing phase diagram,
plus an animation of how each doctrine's EOT moves as the employer event slides in time.

Run:  python src/experiments/run_v2.py   (outputs -> outputs/v2/)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FuncAnimation, PillowWriter

from cdx import DelayEvent, DelayGame, LABELS, Schedule, evaluate_all
from cdx.cases import CASES, COURT_OPERATOR
from cdx.synth import EX_ANTE, features, random_game

OUT = ROOT / "outputs" / "v2"
PLOTS = OUT / "plots"
SEED = 2026

ORDER = ["but_for", "contractual_exclusion", "first_in_time", "nec4_prospective", "city_inn", "symmetric_shapley",
         "effective_cause", "overlap_concurrency", "as_planned_impact"]
COLORS = {
    "but_for": "#9e9e9e", "contractual_exclusion": "#6d4c41", "first_in_time": "#d1495b",
    "city_inn": "#2e7d32", "symmetric_shapley": "#8e7cc3", "overlap_concurrency": "#1f6fb2",
    "as_planned_impact": "#f2a541", "effective_cause": "#0b3d91", "nec4_prospective": "#7a7a2e",
}
ENGLISH = ["first_in_time", "effective_cause", "overlap_concurrency", "as_planned_impact"]


# --- E1 --------------------------------------------------------------------------------

def e1_fidelity() -> pd.DataFrame:
    rows = []
    for key, case in CASES.items():
        res = evaluate_all(case.game())
        for d in ORDER:
            o = res[d]
            match = abs(o.eot - case.court_eot) < 1e-6 and (
                case.court_compensable is None or abs(o.compensable - case.court_compensable) < 1e-6)
            rows.append({"case": key, "case_name": case.name, "citation": case.citation, "doctrine": d,
                         "eot": o.eot, "compensable": o.compensable, "court_eot": case.court_eot,
                         "court_compensable": case.court_compensable, "reproduces_court": match,
                         "court_operator": COURT_OPERATOR[key] == d, "law_verified": case.law_verified, "facts_verified": case.facts_verified})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "e1_fidelity.csv", index=False)

    piv = df.pivot(index="doctrine", columns="case", values="reproduces_court").loc[ORDER, list(CASES)]
    eot = df.pivot(index="doctrine", columns="case", values="eot").loc[ORDER, list(CASES)]
    comp = df.pivot(index="doctrine", columns="case", values="compensable").loc[ORDER, list(CASES)]
    fig, ax = plt.subplots(figsize=(14, 5.6))
    ax.imshow(piv.values.astype(float), cmap=matplotlib.colors.ListedColormap(["#f6d5d8", "#cfe8d3"]),
              aspect="auto", vmin=0, vmax=1)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            ax.text(j, i, f"{eot.values[i, j]:g} / {comp.values[i, j]:g}",
                    ha="center", va="center", fontsize=8.5,
                    fontweight="bold" if piv.values[i, j] else "normal")
    ax.set_xticks(range(len(CASES)))
    short = {k: c.name.split(" v ")[0].replace("Henry Boot", "Malmaison").replace("North Midland", "Cyden")
             for k, c in CASES.items()}
    ax.set_xticklabels([f"{short[k]}{'' if CASES[k].facts_verified else ' *'}\ncourt {CASES[k].court_eot:g}"
                        + (f" / {CASES[k].court_compensable:g}" if CASES[k].court_compensable is not None else "")
                        for k in CASES], fontsize=8)
    ax.set_yticks(range(len(ORDER)))
    ax.set_yticklabels([LABELS[d] for d in ORDER], fontsize=8.5)
    ax.set_title("E1  Each rule against each case: extension / paid days (green = reproduces the court)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(PLOTS / "e1_fidelity_matrix.png", dpi=180)
    plt.close(fig)
    return df


# --- E2 --------------------------------------------------------------------------------

def e2_divergence(n: int = 6000):
    rng = np.random.default_rng(SEED)
    rows = []
    for _ in range(n):
        g = random_game(rng)
        res = evaluate_all(g)
        f = features(g)
        eng = [res[d].eot for d in ENGLISH]
        f.update({f"eot_{d}": res[d].eot for d in ORDER})
        f["net_delay"] = res["but_for"].net_delay
        f["compensable"] = res["overlap_concurrency"].compensable
        f["english_spread"] = max(eng) - min(eng)
        f["scotland_minus_england"] = res["city_inn"].eot - res["effective_cause"].eot
        rows.append(f)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "e2_divergence_dataset.csv", index=False)

    feats = [c for c in df.columns if not c.startswith("eot_") and c not in
             ("net_delay", "compensable", "english_spread", "scotland_minus_england")]
    summary = {
        "configurations": len(df),
        "with_any_net_delay": float((df.net_delay > 0).mean()),
        "english_doctrines_disagree": float((df.english_spread > 1e-6).mean()),
        "english_disagree_given_delay": float((df.english_spread[df.net_delay > 0] > 1e-6).mean()),
        "median_spread_when_disagree_days": float(df.english_spread[df.english_spread > 1e-6].median()),
        "scotland_differs_from_overlap": float((df.scotland_minus_england.abs() > 1e-6).mean()),
    }

    import shap
    from sklearn.metrics import r2_score
    from sklearn.model_selection import train_test_split
    from xgboost import XGBRegressor

    results = {}
    for target in ("english_spread", "scotland_minus_england"):
        X, y = df[feats], df[target]
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=SEED)
        m = XGBRegressor(n_estimators=500, max_depth=5, learning_rate=0.05, subsample=0.9,
                         colsample_bytree=0.9, random_state=SEED)
        m.fit(Xtr, ytr)
        r2 = r2_score(yte, m.predict(Xte))
        sv = shap.TreeExplainer(m)(Xte)
        results[target] = {"r2_test": r2}
        imp = pd.DataFrame({"feature": feats, "mean_abs_shap": np.abs(sv.values).mean(0)}) \
            .sort_values("mean_abs_shap", ascending=False)
        imp.to_csv(OUT / f"e2_shap_importance_{target}.csv", index=False)

        plt.figure()
        shap.plots.beeswarm(sv, max_display=12, show=False)
        plt.title(f"E2  What drives {'English-doctrine spread' if target == 'english_spread' else 'City Inn − overlap EOT'}"
                  f"  (test R² = {r2:.2f})", fontsize=10)
        plt.tight_layout()
        plt.savefig(PLOTS / f"e2_shap_beeswarm_{target}.png", dpi=180)
        plt.close("all")

        top = imp.feature.iloc[0]
        plt.figure()
        shap.plots.scatter(sv[:, top], color=sv[:, "series_coupling"] if top != "series_coupling" else None,
                           show=False)
        plt.title(f"E2  SHAP dependence: {top} ({target})", fontsize=10)
        plt.tight_layout()
        plt.savefig(PLOTS / f"e2_shap_dependence_{target}.png", dpi=180)
        plt.close("all")

    from sklearn.metrics import roc_auc_score
    from xgboost import XGBClassifier
    yb = (df.english_spread > 7).astype(int)
    Xtr, Xte, ytr, yte = train_test_split(df[EX_ANTE], yb, test_size=0.25, random_state=SEED, stratify=yb)
    clf = XGBClassifier(n_estimators=400, max_depth=4, learning_rate=0.05, random_state=SEED).fit(Xtr, ytr)
    results["exante_screen"] = {"r2_test": roc_auc_score(yte, clf.predict_proba(Xte)[:, 1])}
    svc = shap.TreeExplainer(clf)(Xte)
    plt.figure()
    shap.plots.beeswarm(svc, max_display=12, show=False)
    plt.title(f"E2  Ex-ante screen: will the English readings differ by >7 days? (AUC {results['exante_screen']['r2_test']:.2f})",
              fontsize=10)
    plt.tight_layout()
    plt.savefig(PLOTS / "e2_shap_exante_screen.png", dpi=180)
    plt.close("all")
    pd.Series({**summary, **{f"r2_{k}": v["r2_test"] for k, v in results.items()}}).to_csv(
        OUT / "e2_summary.csv", header=["value"])
    return df, summary, results


# --- E3 + animation ----------------------------------------------------------------------

C_DAYS, C_START = 40.0, 0.0


def two_path_game(e_start: float, e_days: float, c_days: float = C_DAYS) -> DelayGame:
    s = Schedule({"A": 200.0, "B": 200.0})
    return DelayGame(s, [DelayEvent("C", "C", "B", c_days, C_START), DelayEvent("E", "E", "A", e_days, e_start)])


def e3_phase():
    lags = np.arange(-60, 121, 2.0)
    mags = np.arange(2, 81, 2.0)
    grids = {d: np.zeros((len(mags), len(lags))) for d in ORDER}
    for i, m in enumerate(mags):
        for j, lag in enumerate(lags):
            res = evaluate_all(two_path_game(lag, m))
            for d in ORDER:
                grids[d][i, j] = res[d].eot
    show = ["first_in_time", "overlap_concurrency", "as_planned_impact", "city_inn", "contractual_exclusion"]
    fig, axes = plt.subplots(1, len(show), figsize=(18, 4.2), sharey=True)
    short = {"first_in_time": "First-in-time\n(Adyard / Saga)", "overlap_concurrency": "Overlap concurrency\n(SCL / Thomas Barnes)",
             "as_planned_impact": "As-planned impact\n(prospective)", "city_inn": "City Inn\n(Scotland, τ = 0.75)",
             "contractual_exclusion": "Contractual exclusion\n(Cyden clause)"}
    for ax, d in zip(axes, show):
        im = ax.imshow(grids[d], origin="lower", aspect="auto", cmap="viridis", vmin=0, vmax=mags.max(),
                       extent=[lags[0], lags[-1], mags[0], mags[-1]])
        ax.axvline(C_START, color="w", lw=0.8, ls=":")
        ax.axvline(C_START + C_DAYS, color="w", lw=0.8, ls=":")
        ax.axhline(C_DAYS, color="w", lw=0.8, ls="--")
        ax.set_title(short[d], fontsize=9.5)
    axes[0].set_ylabel("employer delay (days)")
    fig.supxlabel("day the employer delay starts  (contractor delay: 40 days, day 0–40, dotted lines; dashed = equal size)",
                  fontsize=9)
    fig.colorbar(im, ax=axes, shrink=0.85, label="EOT (days)")
    fig.suptitle("E3  Same facts, different law: extension of time by timing and size of the employer delay",
                 fontsize=11, y=1.02)
    fig.savefig(PLOTS / "e3_timing_phase_diagram.png", dpi=170, bbox_inches="tight")
    plt.close(fig)
    pd.DataFrame({d: g.ravel() for d, g in grids.items()}).assign(
        e_days=np.repeat(mags, len(lags)), e_start=np.tile(lags, len(mags))
    ).to_csv(OUT / "e3_phase_grid.csv", index=False)


def animate_timing(e_days: float = 55.0):
    lags = np.concatenate([np.arange(-50, 101, 2.0), np.arange(100, -51, -2.0)])
    show = ["contractual_exclusion", "first_in_time", "city_inn", "overlap_concurrency", "as_planned_impact"]
    fig, (ax_g, ax_b) = plt.subplots(2, 1, figsize=(8.5, 6.2), gridspec_kw={"height_ratios": [1, 1.5]})

    def draw(k):
        lag = lags[k]
        res = evaluate_all(two_path_game(lag, e_days))
        ax_g.clear()
        ax_g.barh(1, C_DAYS, left=C_START, color="#d1495b", height=0.5)
        ax_g.barh(0, e_days, left=lag, color="#1f6fb2", height=0.5)
        ax_g.text(C_START + 1, 1, f"Contractor {C_DAYS:.0f}d", va="center", color="w", fontsize=8)
        ax_g.text(lag + 1, 0, f"Employer {e_days:.0f}d", va="center", color="w", fontsize=8)
        ax_g.set_xlim(-55, 160)
        ax_g.set_yticks([])
        ax_g.set_xlabel("project day the delaying effect is felt")
        net = res["but_for"].net_delay
        ax_g.set_title(f"Net delay to completion: {net:.0f} days   |   but-for employer days: "
                       f"{res['but_for'].eot:.0f}", fontsize=9)
        ax_b.clear()
        vals = [res[d].eot for d in show]
        ax_b.barh(range(len(show)), vals, color=[COLORS[d] for d in show])
        for i, v in enumerate(vals):
            ax_b.text(v + 0.8, i, f"{v:.1f}d", va="center", fontsize=8.5)
        ax_b.set_yticks(range(len(show)))
        ax_b.set_yticklabels([LABELS[d] for d in show], fontsize=8.5)
        ax_b.set_xlim(0, e_days + 10)
        ax_b.set_xlabel("extension of time granted (days)")
        fig.suptitle("One set of facts, five legal answers", fontsize=11, fontweight="bold")
        fig.tight_layout()

    anim = FuncAnimation(fig, draw, frames=len(lags), interval=90)
    anim.save(PLOTS / "anim_doctrine_timing.gif", writer=PillowWriter(fps=11))
    plt.close(fig)


def main():
    PLOTS.mkdir(parents=True, exist_ok=True)
    fid = e1_fidelity()
    print("E1 fidelity (court operator rows):")
    print(fid[fid.court_operator][["case", "doctrine", "eot", "compensable", "court_eot", "court_compensable",
                                   "reproduces_court"]].to_string(index=False))
    print("\nE1 operators reproducing each case:")
    print(fid[fid.reproduces_court].groupby("case").doctrine.apply(list).to_string())
    _, summary, results = e2_divergence()
    print("\nE2 summary:", {k: round(v, 3) for k, v in summary.items()})
    print("E2 surrogate R2:", {k: round(v["r2_test"], 3) for k, v in results.items()})
    e3_phase()
    animate_timing()
    print("\nWrote", OUT)


if __name__ == "__main__":
    main()
