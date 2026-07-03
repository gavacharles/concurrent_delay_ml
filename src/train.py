from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple
import importlib

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.inspection import permutation_importance


LEAKAGE_COLUMNS = {
    "owner_cp_delay",
    "contractor_cp_delay",
    "total_cp_delay",
    "owner_delay_share",
}


def _build_model(random_state: int = 42):
    """Use XGBoost if available, otherwise RandomForest."""
    try:
        xgb_module = importlib.import_module("xgboost")
        XGBClassifier = getattr(xgb_module, "XGBClassifier")

        return XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=random_state,
            eval_metric="logloss",
        )
    except Exception:
        return RandomForestClassifier(
            n_estimators=400,
            max_depth=18,
            min_samples_leaf=1,
            class_weight="balanced_subsample",
            random_state=random_state,
            n_jobs=-1,
        )


def _select_threshold(y_true: pd.Series, p_prob: np.ndarray) -> float:
    prevalence = float(np.clip(y_true.mean(), 0.01, 0.99))
    threshold = float(np.quantile(p_prob, 1.0 - prevalence))
    threshold = min(threshold, 0.20)
    return float(np.clip(threshold, 0.01, 0.95))


def _build_calibration_table(y_true: pd.Series, p_prob: np.ndarray, n_bins: int = 10) -> pd.DataFrame:
    df = pd.DataFrame({"y": y_true.to_numpy().astype(int), "p": p_prob})
    df["bin"] = pd.qcut(df["p"], q=min(n_bins, len(df)), duplicates="drop")
    table = (
        df.groupby("bin", observed=False)
        .agg(
            n=("y", "size"),
            mean_pred=("p", "mean"),
            observed_rate=("y", "mean"),
        )
        .reset_index(drop=True)
    )
    table["calibration_gap"] = table["mean_pred"] - table["observed_rate"]
    return table


def _build_explainability(
    estimator: object,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    random_state: int,
    force_shap: bool = True,
) -> pd.DataFrame:
    try:
        shap_module = importlib.import_module("shap")
        TreeExplainer = getattr(shap_module, "TreeExplainer")
        sample_n = min(1000, len(X_test))
        X_sample = X_test.sample(n=sample_n, random_state=random_state)

        explainer = TreeExplainer(estimator)
        shap_values = explainer.shap_values(X_sample)

        if isinstance(shap_values, list):
            shap_arr = np.array(shap_values[1])
        elif getattr(shap_values, "ndim", 0) == 3:
            shap_arr = np.array(shap_values[:, :, 1])
        else:
            shap_arr = np.array(shap_values)

        values = np.mean(np.abs(shap_arr), axis=0)
        return (
            pd.DataFrame(
                {
                    "feature": X_sample.columns,
                    "importance": values,
                    "method": "shap_mean_abs",
                }
            )
            .sort_values("importance", ascending=False)
            .reset_index(drop=True)
        )
    except Exception as exc:
        if force_shap:
            raise RuntimeError(
                "SHAP explainability is forced but failed. "
                "Check SHAP compatibility with the estimator/environment."
            ) from exc

        perm = permutation_importance(
            estimator,
            X_test,
            y_test,
            n_repeats=8,
            random_state=random_state,
            n_jobs=-1,
            scoring="average_precision",
        )
        return (
            pd.DataFrame(
                {
                    "feature": X_test.columns,
                    "importance": perm.importances_mean,
                    "importance_std": perm.importances_std,
                    "method": "permutation_avg_precision",
                }
            )
            .sort_values("importance", ascending=False)
            .reset_index(drop=True)
        )


def train_and_evaluate(
    df: pd.DataFrame,
    random_state: int = 42,
) -> Tuple[object, Dict[str, float], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    target = "concurrent_delay"
    drop_cols = {"schedule_id", target, *LEAKAGE_COLUMNS}
    feature_cols = [c for c in df.columns if c not in drop_cols]

    X = df[feature_cols].copy()
    y = df[target].astype(int)
    groups = df["schedule_id"].astype(int)

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=random_state)
    train_idx, test_idx = next(splitter.split(X, y, groups=groups))

    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

    # Split training fold into fit/calibration folds by schedule groups.
    train_groups = groups.iloc[train_idx]
    calib_split = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=random_state)
    fit_rel_idx, calib_rel_idx = next(calib_split.split(X_train, y_train, groups=train_groups))

    X_fit, y_fit = X_train.iloc[fit_rel_idx], y_train.iloc[fit_rel_idx]
    X_cal, y_cal = X_train.iloc[calib_rel_idx], y_train.iloc[calib_rel_idx]

    base_model = _build_model(random_state=random_state)
    base_model.fit(X_fit, y_fit)

    cal_method = "isotonic" if y_cal.sum() >= 30 else "sigmoid"
    model = CalibratedClassifierCV(estimator=base_model, method=cal_method, cv="prefit")
    model.fit(X_cal, y_cal)

    train_prob = model.predict_proba(X_train)[:, 1]
    threshold = _select_threshold(y_train, train_prob)

    p_prob = model.predict_proba(X_test)[:, 1]
    p = (p_prob >= threshold).astype(int)

    metrics = {
        "accuracy": float(accuracy_score(y_test, p)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, p)),
        "precision": float(precision_score(y_test, p, zero_division=0)),
        "recall": float(recall_score(y_test, p, zero_division=0)),
        "f1": float(f1_score(y_test, p, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, p_prob)),
        "pr_auc": float(average_precision_score(y_test, p_prob)),
        "brier": float(brier_score_loss(y_test, p_prob)),
        "log_loss": float(log_loss(y_test, p_prob, labels=[0, 1])),
        "calibration_method": cal_method,
        "decision_threshold": float(threshold),
        "n_train": float(len(train_idx)),
        "n_test": float(len(test_idx)),
        "n_train_schedules": float(groups.iloc[train_idx].nunique()),
        "n_test_schedules": float(groups.iloc[test_idx].nunique()),
        "positive_rate_test": float(y_test.mean()),
    }

    calibration_table = _build_calibration_table(y_test, p_prob, n_bins=10)

    # unified importance extraction
    if hasattr(base_model, "feature_importances_"):
        importances = base_model.feature_importances_
    else:
        importances = np.zeros(len(feature_cols), dtype=float)

    imp_df = (
        pd.DataFrame({"feature": feature_cols, "importance": importances})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )

    explain_df = _build_explainability(
        base_model,
        X_test,
        y_test,
        random_state=random_state,
        force_shap=True,
    )

    return model, metrics, imp_df, calibration_table, explain_df


def save_training_outputs(
    metrics: Dict[str, float],
    importance_df: pd.DataFrame,
    calibration_df: pd.DataFrame,
    explain_df: pd.DataFrame,
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    pd.DataFrame([metrics]).to_csv(out_dir / "model_metrics.csv", index=False)
    importance_df.to_csv(out_dir / "feature_importance.csv", index=False)
    calibration_df.to_csv(out_dir / "calibration_curve.csv", index=False)
    explain_df.to_csv(out_dir / "explainability_importance.csv", index=False)
