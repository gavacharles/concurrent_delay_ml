# Concurrent Delay XAI

> **v2 (branch `v2-doctrine-operators`):** *One Schedule, Many Laws*. Concurrent delay doctrines (Malmaison/effective cause, Adyard first-in-time, SCL Protocol/Thomas Barnes overlap, City Inn apportionment, Cyden exclusion) are encoded as attribution operators on a single CPM causal model, tested against stylised versions of the cases, and explained with XAI. Design: [docs/study_redesign_v2.md](docs/study_redesign_v2.md).
>
> ```
> pip install -r requirements.txt
> python -m pytest tests          # axioms, invariants, doctrinal fidelity
> python src/experiments/run_v2.py  # E1 fidelity, E2 SHAP divergence model, E3 phase diagram, animation -> outputs/v2/
> ```
> Code: `src/cdx/` (schedule, network [real MS Project programmes via MSPDI], game, doctrines, contracts, cases, synth). Formal results: [docs/formal_results.md](docs/formal_results.md). Real-programme study: `python src/experiments/run_real.py` (needs the programme files in `data/programmes/`, which are kept out of git; convert .mpp to MSPDI XML with MPXJ). v1 results are archived unchanged in `outputs/v1/`.
> Package 5 study (back-propagation, neutral events, notice gate, XAI ensemble): `python src/experiments/run_package5_xai.py` (needs the confidential programme and contract in `data/programmes/`). Paper draft: [docs/paper_v2_draft.md](docs/paper_v2_draft.md).
> Note: v1 classifier metrics in `outputs/v1/model_metrics.csv` were produced with the RandomForest fallback (xgboost not installed). With xgboost installed the same script gives balanced accuracy 0.536 and ROC AUC 0.613.

---

## v1 (archived)

# Concurrent Delay Vulnerability (ML)

## Title Concept
**A Machine Learning Approach to Predicting Concurrent Delay Vulnerability in Critical Path Networks**

## Objective
Build an early-warning system that predicts whether a project schedule configuration is vulnerable to **concurrent delay** before execution begins.

## Method Summary
1. Generate synthetic CPM-like project networks as DAGs.
2. Run Monte Carlo simulations with random Owner and Contractor risk events.
3. Extract structural + risk features.
4. Train ensemble classifiers (Random Forest, optional XGBoost) for `concurrent_delay` prediction.
5. Calibrate probabilities (isotonic/sigmoid on grouped holdout).
6. Export model performance, calibration curve, and explainability importance.

## Research-Grade Guardrails
- Leakage-sensitive outcome columns (`owner_cp_delay`, `contractor_cp_delay`, `total_cp_delay`, `owner_delay_share`) are excluded from training features.
- Train/test splitting is done by `schedule_id` groups, so simulation runs from the same schedule do not appear in both train and test.

## Project Structure
- `src/synthetic_schedule.py` - baseline schedule/network generation
- `src/simulation.py` - Monte Carlo risk injection and outcome labeling
- `src/features.py` - feature table assembly
- `src/train.py` - model training + evaluation
- `src/run_pipeline.py` - one-command end-to-end pipeline
- `requirements.txt` - dependencies

## Output Artifacts
- `outputs/model_metrics.csv`
- `outputs/feature_importance.csv`
- `outputs/calibration_curve.csv`
- `outputs/explainability_importance.csv` (SHAP if installed, else permutation importance)

## Quick Start
1. Create/activate a Python environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run:
   - `python src/run_pipeline.py`

Outputs are written to `outputs/`.

## Core Label Definition
`concurrent_delay = 1` if both Owner and Contractor contribute non-trivial critical-path delay in the same simulation run; else `0`.

This definition is configurable in `src/simulation.py`.
