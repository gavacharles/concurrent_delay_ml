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
