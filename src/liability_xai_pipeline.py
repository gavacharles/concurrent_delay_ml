from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

try:
    from xgboost import XGBRegressor
    _HAS_XGB = True
except Exception:
    XGBRegressor = None
    _HAS_XGB = False


@dataclass
class PipelineConfig:
    seed: int = 2026
    n_samples: int = 6000
    owner_delay_max: int = 40
    contractor_delay_max: int = 40
    archetypes: Tuple[str, ...] = ("balanced_parallel", "owner_path_dominant", "contractor_path_dominant")
    uncertainty_runs: int = 10


def build_baseline_network() -> Tuple[nx.DiGraph, Dict[str, float], Dict[str, Tuple[float, float]]]:
    g = nx.DiGraph()

    activities = [f"A{i:02d}" for i in range(1, 31)]
    g.add_nodes_from(["START", *activities, "FINISH"])

    # Explicit parallel-path logic (30 activities)
    edges = [
        ("START", "A01"),
        ("A01", "A02"),
        ("A02", "A03"),
        ("A03", "A04"),
        ("A04", "A05"),
        ("A05", "A06"),
        ("A06", "A07"),
        ("A07", "A08"),
        ("A08", "A09"),
        ("A09", "A10"),
        # Parallel stream B
        ("A02", "A11"),
        ("A11", "A12"),
        ("A12", "A13"),
        ("A13", "A14"),
        ("A14", "A15"),
        ("A15", "A16"),
        ("A16", "A17"),
        ("A17", "A18"),
        ("A18", "A09"),
        # Parallel stream C
        ("A03", "A19"),
        ("A19", "A20"),
        ("A20", "A21"),
        ("A21", "A22"),
        ("A22", "A08"),
        # Parallel stream D
        ("A05", "A23"),
        ("A23", "A24"),
        ("A24", "A25"),
        ("A25", "A26"),
        ("A26", "A10"),
        # Tail and convergence
        ("A10", "A27"),
        ("A18", "A28"),
        ("A22", "A29"),
        ("A26", "A30"),
        ("A27", "FINISH"),
        ("A28", "FINISH"),
        ("A29", "FINISH"),
        ("A30", "FINISH"),
    ]
    g.add_edges_from(edges)

    durations = {"START": 0.0, "FINISH": 0.0}
    for i in range(1, 31):
        # deterministic but varied durations
        durations[f"A{i:02d}"] = float(3 + (i % 7) + (i % 3))

    # fixed positions for readable network figure
    pos = {
        "START": (0, 0),
        "A01": (1, 0), "A02": (2, 0), "A03": (3, 0), "A04": (4, 0), "A05": (5, 0),
        "A06": (6, 0), "A07": (7, 0), "A08": (8, 0), "A09": (9, 0), "A10": (10, 0),
        "A11": (3, 1.8), "A12": (4, 1.8), "A13": (5, 1.8), "A14": (6, 1.8), "A15": (7, 1.8),
        "A16": (8, 1.8), "A17": (9, 1.8), "A18": (10, 1.8),
        "A19": (4, -1.8), "A20": (5, -1.8), "A21": (6, -1.8), "A22": (7, -1.8),
        "A23": (6, -3.3), "A24": (7, -3.3), "A25": (8, -3.3), "A26": (9, -3.3),
        "A27": (11, 0), "A28": (11, 1.8), "A29": (9, -1.8), "A30": (10, -3.3),
        "FINISH": (12, 0),
    }

    return g, durations, pos


def _archetype_vectors(archetype: str) -> Tuple[List[str], List[str]]:
    if archetype == "owner_path_dominant":
        # owner vector placed closer to primary/tail convergence chain
        return ["A04", "A07", "A10", "A27", "A28"], ["A11", "A14", "A20", "A24", "A29"]
    if archetype == "contractor_path_dominant":
        # contractor vector placed closer to primary/tail convergence chain
        return ["A11", "A14", "A20", "A24", "A29"], ["A04", "A07", "A10", "A27", "A28"]

    # balanced default
    return ["A11", "A14", "A20", "A24", "A29"], ["A04", "A07", "A16", "A22", "A27"]


def _project_completion(g: nx.DiGraph, durations: Dict[str, float]) -> float:
    topo = list(nx.topological_sort(g))
    es: Dict[str, float] = {n: 0.0 for n in topo}
    ef: Dict[str, float] = {n: 0.0 for n in topo}
    for n in topo:
        preds = list(g.predecessors(n))
        if preds:
            es[n] = max(ef[p] for p in preds)
        ef[n] = es[n] + durations.get(n, 0.0)
    return ef["FINISH"]


def _allocate_delay(total_days: float, n_targets: int, rng: np.random.Generator) -> np.ndarray:
    if total_days <= 0:
        return np.zeros(n_targets)
    weights = rng.dirichlet(np.ones(n_targets))
    return weights * total_days


def simulate_dataset(cfg: PipelineConfig, archetype: str = "balanced_parallel") -> Tuple[pd.DataFrame, float, nx.DiGraph, Dict[str, Tuple[float, float]], List[str], List[str]]:
    rng = np.random.default_rng(cfg.seed)
    g, durations_base, pos = build_baseline_network()
    owner_vector, contractor_vector = _archetype_vectors(archetype)
    baseline_finish = _project_completion(g, durations_base)

    rows = []
    for _ in range(cfg.n_samples):
        owner_days = float(rng.integers(0, cfg.owner_delay_max + 1))
        contractor_days = float(rng.integers(0, cfg.contractor_delay_max + 1))

        durations = durations_base.copy()
        owner_alloc = _allocate_delay(owner_days, len(owner_vector), rng)
        contractor_alloc = _allocate_delay(contractor_days, len(contractor_vector), rng)

        for a, d in zip(owner_vector, owner_alloc):
            durations[a] += float(d)
        for a, d in zip(contractor_vector, contractor_alloc):
            durations[a] += float(d)

        finish = _project_completion(g, durations)
        slippage = max(0.0, finish - baseline_finish)

        rows.append(
            {
                "owner_delay_days": owner_days,
                "contractor_delay_days": contractor_days,
                "project_slippage_days": slippage,
            }
        )

    return pd.DataFrame(rows), baseline_finish, g, pos, owner_vector, contractor_vector


def train_surrogate(df: pd.DataFrame, seed: int = 2026, fast: bool = False):
    X = df[["owner_delay_days", "contractor_delay_days"]]
    y = df["project_slippage_days"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed
    )

    if _HAS_XGB:
        n_estimators = 220 if fast else 450
        model = XGBRegressor(
            n_estimators=n_estimators,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=seed,
            objective="reg:squarederror",
        )
        model_used = "xgboost"
    else:
        n_estimators = 220 if fast else 450
        model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            max_depth=3,
            learning_rate=0.05,
            random_state=seed,
        )
        model_used = "gradient_boosting_fallback"
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    metrics = {
        "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
        "mae": float(mean_absolute_error(y_test, pred)),
        "r2": float(r2_score(y_test, pred)),
        "n_train": float(len(X_train)),
        "n_test": float(len(X_test)),
        "model_used": model_used,
    }
    return model, X_train, X_test, y_train, y_test, pred, metrics


def benchmark_cpm_methods(apportionment: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in apportionment.iterrows():
        owner_d = float(r["owner_delay_days"])
        contractor_d = float(r["contractor_delay_days"])
        shap_owner = float(r["owner_liability_share"])

        denom = owner_d + contractor_d
        prop_owner = owner_d / denom if denom > 0 else 0.5

        if owner_d > 0 and contractor_d > 0:
            equal_owner = 0.5
        elif owner_d > 0:
            equal_owner = 1.0
        else:
            equal_owner = 0.0

        if owner_d > contractor_d:
            dominant_owner = 1.0
        elif contractor_d > owner_d:
            dominant_owner = 0.0
        else:
            dominant_owner = 0.5

        rows.append(
            {
                "scenario": r["scenario"],
                "shap_owner_share": shap_owner,
                "cpm_proportional_owner_share": prop_owner,
                "cpm_equal_split_owner_share": equal_owner,
                "cpm_dominant_cause_owner_share": dominant_owner,
                "abs_err_proportional": abs(prop_owner - shap_owner),
                "abs_err_equal_split": abs(equal_owner - shap_owner),
                "abs_err_dominant_cause": abs(dominant_owner - shap_owner),
            }
        )

    bench = pd.DataFrame(rows)
    summary = pd.DataFrame(
        {
            "method": ["proportional", "equal_split", "dominant_cause"],
            "mae_vs_shap": [
                float(bench["abs_err_proportional"].mean()),
                float(bench["abs_err_equal_split"].mean()),
                float(bench["abs_err_dominant_cause"].mean()),
            ],
        }
    )
    return bench, summary


def compute_uncertainty_bounds(
    cfg: PipelineConfig,
    scenarios: pd.DataFrame,
    archetype: str,
) -> pd.DataFrame:
    all_rows = []
    for i in range(cfg.uncertainty_runs):
        seed_i = cfg.seed + i
        cfg_i = PipelineConfig(
            seed=seed_i,
            n_samples=max(3000, cfg.n_samples // 2),
            owner_delay_max=cfg.owner_delay_max,
            contractor_delay_max=cfg.contractor_delay_max,
            archetypes=cfg.archetypes,
            uncertainty_runs=cfg.uncertainty_runs,
        )
        df_i, _, _, _, _, _ = simulate_dataset(cfg_i, archetype=archetype)
        model_i, _, X_test_i, _, _, _, _ = train_surrogate(df_i, seed=seed_i, fast=True)
        _, app_i = compute_shap_outputs(model_i, X_test_i, scenarios)

        for _, r in app_i.iterrows():
            all_rows.append(
                {
                    "run": i,
                    "scenario": r["scenario"],
                    "owner_liability_share": float(r["owner_liability_share"]),
                    "contractor_liability_share": float(r["contractor_liability_share"]),
                }
            )

    u = pd.DataFrame(all_rows)
    out = (
        u.groupby("scenario", as_index=False)
        .agg(
            owner_mean=("owner_liability_share", "mean"),
            owner_p05=("owner_liability_share", lambda x: float(np.quantile(x, 0.05))),
            owner_p95=("owner_liability_share", lambda x: float(np.quantile(x, 0.95))),
            contractor_mean=("contractor_liability_share", "mean"),
            contractor_p05=("contractor_liability_share", lambda x: float(np.quantile(x, 0.05))),
            contractor_p95=("contractor_liability_share", lambda x: float(np.quantile(x, 0.95))),
        )
        .reset_index(drop=True)
    )
    return out


def compute_shap_outputs(model: object, X_ref: pd.DataFrame, scenarios: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    explainer = shap.TreeExplainer(model)

    shap_ref = explainer.shap_values(X_ref)
    shap_ref = np.array(shap_ref)
    mean_abs = np.mean(np.abs(shap_ref), axis=0)
    summary = pd.DataFrame(
        {
            "feature": X_ref.columns,
            "mean_abs_shap": mean_abs,
        }
    ).sort_values("mean_abs_shap", ascending=False)

    shap_case = np.array(explainer.shap_values(scenarios[["owner_delay_days", "contractor_delay_days"]]))
    base_value = float(np.array(explainer.expected_value).reshape(-1)[0])

    rows = []
    for i, row in scenarios.iterrows():
        owner_phi = float(shap_case[i, 0])
        contractor_phi = float(shap_case[i, 1])
        pred = float(base_value + owner_phi + contractor_phi)

        owner_pos = max(owner_phi, 0.0)
        contractor_pos = max(contractor_phi, 0.0)
        denom = owner_pos + contractor_pos
        owner_share = owner_pos / denom if denom > 0 else 0.5
        contractor_share = contractor_pos / denom if denom > 0 else 0.5

        rows.append(
            {
                "scenario": row["scenario"],
                "owner_delay_days": float(row["owner_delay_days"]),
                "contractor_delay_days": float(row["contractor_delay_days"]),
                "predicted_slippage_days": pred,
                "base_value": base_value,
                "owner_shap": owner_phi,
                "contractor_shap": contractor_phi,
                "owner_liability_share": owner_share,
                "contractor_liability_share": contractor_share,
            }
        )

    return summary.reset_index(drop=True), pd.DataFrame(rows)


def generate_visuals(
    out_dir: Path,
    g: nx.DiGraph,
    pos: Dict[str, Tuple[float, float]],
    owner_vector: List[str],
    contractor_vector: List[str],
    model: object,
    y_test: pd.Series,
    pred_test: np.ndarray,
    shap_summary: pd.DataFrame,
    apportionment: pd.DataFrame,
    archetype_metrics: pd.DataFrame,
    uncertainty_bounds: pd.DataFrame,
    cpm_summary: pd.DataFrame,
):
    plots = out_dir / "plots"
    plots.mkdir(parents=True, exist_ok=True)

    # 1) network schematic
    plt.figure(figsize=(14, 6))
    node_colors = []
    for n in g.nodes:
        if n in owner_vector:
            node_colors.append("#4C78A8")
        elif n in contractor_vector:
            node_colors.append("#F58518")
        elif n in {"START", "FINISH"}:
            node_colors.append("#54A24B")
        else:
            node_colors.append("#B9B9B9")
    nx.draw(g, pos=pos, with_labels=True, node_size=780, font_size=7, node_color=node_colors, arrows=True)
    plt.title("Simplified 30-Activity Schedule Network\nBlue=Owner Vector, Orange=Contractor Vector")
    plt.tight_layout()
    plt.savefig(plots / "baseline_network.png", dpi=180)
    plt.close()

    # 2) response surface heatmap
    grid = np.arange(0, 41)
    xx, yy = np.meshgrid(grid, grid)
    zz_input = pd.DataFrame(
        {
            "owner_delay_days": xx.ravel(),
            "contractor_delay_days": yy.ravel(),
        }
    )
    zz = model.predict(zz_input).reshape(xx.shape)
    plt.figure(figsize=(8, 6))
    im = plt.imshow(zz, origin="lower", extent=[0, 40, 0, 40], aspect="auto", cmap="viridis")
    plt.colorbar(im, label="Predicted slippage days")
    plt.xlabel("Owner delay days")
    plt.ylabel("Contractor delay days")
    plt.title("Predicted Slippage Surface")
    plt.tight_layout()
    plt.savefig(plots / "predicted_slippage_surface.png", dpi=180)
    plt.close()

    # 3) actual vs predicted
    plt.figure(figsize=(7, 6))
    plt.scatter(y_test, pred_test, s=12, alpha=0.5, color="#4C78A8")
    lo, hi = float(min(y_test.min(), pred_test.min())), float(max(y_test.max(), pred_test.max()))
    plt.plot([lo, hi], [lo, hi], "--", color="gray")
    plt.xlabel("Actual slippage days")
    plt.ylabel("Predicted slippage days")
    plt.title("Surrogate Model Fit (Test Set)")
    plt.tight_layout()
    plt.savefig(plots / "actual_vs_predicted.png", dpi=180)
    plt.close()

    # 4) SHAP importance
    s = shap_summary.copy().head(10).iloc[::-1]
    plt.figure(figsize=(8, 4))
    plt.barh(s["feature"], s["mean_abs_shap"], color="#F58518")
    plt.xlabel("Mean |SHAP value|")
    plt.title("SHAP Feature Importance")
    plt.tight_layout()
    plt.savefig(plots / "shap_importance.png", dpi=180)
    plt.close()

    # 5) liability shares by scenario
    a = apportionment.copy()
    x = np.arange(len(a))
    plt.figure(figsize=(10, 5))
    plt.bar(x, a["owner_liability_share"], label="Owner share", color="#4C78A8")
    plt.bar(
        x,
        a["contractor_liability_share"],
        bottom=a["owner_liability_share"],
        label="Contractor share",
        color="#F58518",
    )
    plt.xticks(x, a["scenario"], rotation=15)
    plt.ylim(0, 1)
    plt.ylabel("Liability share")
    plt.title("SHAP-Based Liability Apportionment")
    plt.legend()
    plt.tight_layout()
    plt.savefig(plots / "liability_apportionment.png", dpi=180)
    plt.close()

    # 6) archetype sensitivity R2 comparison
    m = archetype_metrics.copy()
    plt.figure(figsize=(8, 4))
    plt.bar(m["archetype"], m["r2"], color="#72B7B2")
    plt.ylim(0, 1)
    plt.ylabel("R2")
    plt.title("Sensitivity Across Network Archetypes")
    plt.tight_layout()
    plt.savefig(plots / "archetype_sensitivity_r2.png", dpi=180)
    plt.close()

    # 7) uncertainty bounds for owner share
    u = uncertainty_bounds.copy()
    x = np.arange(len(u))
    y = u["owner_mean"].to_numpy()
    yerr = np.vstack([y - u["owner_p05"].to_numpy(), u["owner_p95"].to_numpy() - y])
    plt.figure(figsize=(10, 5))
    plt.errorbar(x, y, yerr=yerr, fmt="o", color="#4C78A8", capsize=4)
    plt.xticks(x, u["scenario"], rotation=15)
    plt.ylim(0, 1)
    plt.ylabel("Owner liability share")
    plt.title("Uncertainty Bounds (5th–95th percentile)")
    plt.tight_layout()
    plt.savefig(plots / "liability_uncertainty_bounds.png", dpi=180)
    plt.close()

    # 8) CPM benchmark MAE vs SHAP
    c = cpm_summary.copy()
    plt.figure(figsize=(7, 4))
    plt.bar(c["method"], c["mae_vs_shap"], color="#E45756")
    plt.ylabel("MAE vs SHAP owner share")
    plt.title("Benchmark: Classical CPM Heuristics vs SHAP")
    plt.tight_layout()
    plt.savefig(plots / "cpm_benchmark_vs_shap.png", dpi=180)
    plt.close()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "outputs" / "v1" / "liability_xai"
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = PipelineConfig()

    # Main archetype used for primary case analysis
    primary_archetype = "balanced_parallel"
    df, baseline_finish, g, pos, owner_vector, contractor_vector = simulate_dataset(cfg, archetype=primary_archetype)
    model, X_train, X_test, y_train, y_test, pred_test, metrics = train_surrogate(df, seed=cfg.seed)

    scenarios = pd.DataFrame(
        [
            {"scenario": "Owner-Dominant", "owner_delay_days": 30, "contractor_delay_days": 10},
            {"scenario": "Contractor-Dominant", "owner_delay_days": 10, "contractor_delay_days": 30},
            {"scenario": "Balanced-Moderate", "owner_delay_days": 20, "contractor_delay_days": 20},
            {"scenario": "High-High", "owner_delay_days": 35, "contractor_delay_days": 35},
            {"scenario": "Low-Low", "owner_delay_days": 8, "contractor_delay_days": 6},
        ]
    )

    shap_summary, apportionment = compute_shap_outputs(model, X_test, scenarios)

    # Sensitivity across multiple archetypes
    sensitivity_rows = []
    for archetype in cfg.archetypes:
        df_a, base_a, _, _, _, _ = simulate_dataset(cfg, archetype=archetype)
        model_a, _, X_test_a, _, y_test_a, pred_a, met_a = train_surrogate(df_a, seed=cfg.seed)
        _, app_a = compute_shap_outputs(model_a, X_test_a, scenarios)
        app_a.insert(0, "archetype", archetype)
        for _, rr in app_a.iterrows():
            sensitivity_rows.append(rr.to_dict())

        met_row = {"archetype": archetype, "baseline_duration_days": base_a, **met_a}
        sensitivity_rows.append({"_metrics_row": met_row})

    # split out metrics rows cleanly
    metrics_rows = [r["_metrics_row"] for r in sensitivity_rows if "_metrics_row" in r]
    app_rows = [r for r in sensitivity_rows if "_metrics_row" not in r]
    archetype_metrics = pd.DataFrame(metrics_rows)
    archetype_apportionment = pd.DataFrame(app_rows)

    # CPM benchmarking against SHAP
    cpm_benchmark_case, cpm_benchmark_summary = benchmark_cpm_methods(apportionment)

    # Uncertainty bounds from repeated seeds
    uncertainty_bounds = compute_uncertainty_bounds(cfg, scenarios, archetype=primary_archetype)

    # Persist results
    df.to_csv(out_dir / "simulated_delay_dataset.csv", index=False)
    pd.DataFrame([{"baseline_project_duration_days": baseline_finish, **metrics}]).to_csv(
        out_dir / "surrogate_metrics.csv", index=False
    )
    pd.DataFrame({"actual_slippage": y_test, "predicted_slippage": pred_test}).to_csv(
        out_dir / "test_predictions.csv", index=False
    )
    shap_summary.to_csv(out_dir / "shap_summary.csv", index=False)
    apportionment.to_csv(out_dir / "scenario_apportionment.csv", index=False)
    archetype_metrics.to_csv(out_dir / "archetype_sensitivity_metrics.csv", index=False)
    archetype_apportionment.to_csv(out_dir / "archetype_sensitivity_apportionment.csv", index=False)
    cpm_benchmark_case.to_csv(out_dir / "cpm_benchmark_casewise.csv", index=False)
    cpm_benchmark_summary.to_csv(out_dir / "cpm_benchmark_summary.csv", index=False)
    uncertainty_bounds.to_csv(out_dir / "liability_share_uncertainty_bounds.csv", index=False)

    generate_visuals(
        out_dir=out_dir,
        g=g,
        pos=pos,
        owner_vector=owner_vector,
        contractor_vector=contractor_vector,
        model=model,
        y_test=y_test,
        pred_test=pred_test,
        shap_summary=shap_summary,
        apportionment=apportionment,
        archetype_metrics=archetype_metrics,
        uncertainty_bounds=uncertainty_bounds,
        cpm_summary=cpm_benchmark_summary,
    )

    # quick narrative summary
    summary_lines = [
        "# Liability Apportionment Pipeline Summary",
        "",
        f"- Baseline duration (days): {baseline_finish:.2f}",
        f"- Samples simulated: {len(df)}",
        f"- RMSE: {metrics['rmse']:.4f}",
        f"- MAE: {metrics['mae']:.4f}",
        f"- R2: {metrics['r2']:.4f}",
        f"- Archetypes tested: {', '.join(cfg.archetypes)}",
        "",
        "## Scenario Apportionment (SHAP)",
        apportionment.to_markdown(index=False),
        "",
        "## CPM Benchmark Summary (MAE vs SHAP owner share)",
        cpm_benchmark_summary.to_markdown(index=False),
        "",
        "## Liability Share Uncertainty Bounds",
        uncertainty_bounds.to_markdown(index=False),
    ]
    (out_dir / "pipeline_results_summary.md").write_text("\n".join(summary_lines), encoding="utf-8")

    print("Pipeline complete.")
    print("Results folder:", out_dir)
    print("Metrics:", metrics)


if __name__ == "__main__":
    main()
