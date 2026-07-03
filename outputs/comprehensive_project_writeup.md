# Comprehensive Project Write-Up

## Project Title
**A Machine Learning Approach to Predicting Concurrent Delay Vulnerability in Critical Path Networks**

## 1) Plain-English Objective
The goal was to build an **early-warning model** that can estimate whether a schedule setup is vulnerable to concurrent delay (owner and contractor delay pressure happening together) **before execution starts**.

In simple terms: we wanted to know if schedule structure + risk assumptions can signal future delay disputes early.

---

## 2) Step-by-Step: What Was Done

### Step 1 — Built synthetic CPM-like schedules
- A schedule generator was implemented in [src/synthetic_schedule.py](../src/synthetic_schedule.py).
- Networks are generated as layered DAGs (directed acyclic graphs) to mimic realistic parallel work fronts.
- CPM descriptors were computed, including:
  - `critical_ratio`
  - `float_density_lt5`
  - `float_mean`, `float_std`
  - `density`, `n_edges`, `n_activities`
  - `project_duration_baseline`

### Step 2 — Simulated owner/contractor risk events (Monte Carlo)
- Simulation logic lives in [src/simulation.py](../src/simulation.py).
- For each schedule, random owner and contractor risk events were injected.
- Delay magnitudes were influenced by structural fragility and logic complexity.
- The binary target `concurrent_delay` was generated.

### Step 3 — Created training dataset
- Dataset assembly was done in [src/features.py](../src/features.py).
- Run configuration produced:
  - **450 schedules**
  - **90 simulations per schedule**
  - Total records around **40,500**
- Output dataset: [data/concurrent_delay_training_data.csv](../data/concurrent_delay_training_data.csv)

### Step 4 — Trained leakage-safe ensemble classifier
- Training pipeline is in [src/train.py](../src/train.py).
- Leakage-sensitive fields were excluded from model inputs (`owner_cp_delay`, `contractor_cp_delay`, `total_cp_delay`, `owner_delay_share`).
- Split strategy used **grouped train/test** by `schedule_id` so one schedule cannot leak into both train and test.
- Probability calibration was added using `CalibratedClassifierCV`.

### Step 5 — Added explainability
- SHAP was forced and executed on the underlying tree model.
- Explainability output now uses `shap_mean_abs` in:
  - [explainability_importance.csv](explainability_importance.csv)

### Step 6 — Produced metrics and visuals
- Main outputs:
  - [model_metrics.csv](model_metrics.csv)
  - [feature_importance.csv](feature_importance.csv)
  - [calibration_curve.csv](calibration_curve.csv)
  - [explainability_importance.csv](explainability_importance.csv)
- Plots generated in [plots](plots):
  - [evaluation_metrics.png](plots/evaluation_metrics.png)
  - [top10_model_feature_importance.png](plots/top10_model_feature_importance.png)
  - [top10_shap_importance.png](plots/top10_shap_importance.png)
  - [calibration_curve.png](plots/calibration_curve.png)

---

## 3) Results

### 3.1 Core model metrics
From [model_metrics.csv](model_metrics.csv):

- Accuracy: **0.9433**
- Balanced Accuracy: **0.5030**
- Precision: **0.0854**
- Recall: **0.0138**
- F1: **0.0237**
- ROC AUC: **0.6183**
- PR AUC: **0.0697**
- Brier Score: **0.0473**
- Log Loss: **0.1953**
- Decision Threshold: **0.10**
- Test positive rate: **0.0500**

Visual summary: [evaluation_metrics.png](plots/evaluation_metrics.png)

### 3.2 Model importance (training model perspective)
Top model importances from [feature_importance.csv](feature_importance.csv):
1. `owner_event_prob`
2. `contractor_event_prob`
3. `logic_complexity`
4. `std_duration`
5. `critical_ratio`

Visual: [top10_model_feature_importance.png](plots/top10_model_feature_importance.png)

### 3.3 SHAP explainability (prediction behavior perspective)
Top SHAP drivers from [explainability_importance.csv](explainability_importance.csv):
1. `owner_event_prob`
2. `contractor_event_prob`
3. `critical_ratio`
4. `float_density_lt5`
5. `low_float_density`

Visual: [top10_shap_importance.png](plots/top10_shap_importance.png)

### 3.4 Calibration behavior
From [calibration_curve.csv](calibration_curve.csv), predicted probabilities are in a low range (roughly 0.016 to 0.090 bin means), with mixed under/over confidence by bin.

Visual: [calibration_curve.png](plots/calibration_curve.png)

---

## 4) Easy Interpretation of Results

### What is working well
- The system is now **methodologically robust**:
  - leakage controls are in place,
  - grouped split prevents schedule duplication bias,
  - calibration and SHAP are integrated.
- The model captures useful signal above random (`ROC AUC > 0.5`).
- Feature patterns are consistent with domain logic:
  - risk probabilities dominate,
  - schedule fragility/float structure contributes meaningful signal.

### What remains weak
- Minority event detection is still difficult:
  - low recall and low F1 indicate many concurrent-delay cases are still missed.
- Strong class imbalance (positive rate ~5%) limits classifier sensitivity.

### Why accuracy is high but recall is low
With rare positives, a model can score high accuracy by predicting mostly negatives. So in this domain, **recall, PR AUC, and calibration** are more informative than accuracy alone.

---

## 5) Visualisation Guide (How to Read the Figures)

1. [evaluation_metrics.png](plots/evaluation_metrics.png)
   - Compare imbalance-sensitive metrics (`recall`, `f1`, `pr_auc`) against `accuracy`.
2. [top10_model_feature_importance.png](plots/top10_model_feature_importance.png)
   - Shows which variables the tree model used most for splitting.
3. [top10_shap_importance.png](plots/top10_shap_importance.png)
   - Shows which variables most changed predictions in absolute SHAP magnitude.
4. [calibration_curve.png](plots/calibration_curve.png)
   - If curve is on the diagonal, probabilities are well-calibrated.

---

## 6) Practical Meaning for Project Managers

This prototype already supports a pre-construction screening workflow:
- Input: schedule structure + risk assumptions.
- Output: probability of concurrent delay vulnerability.
- Decision use: identify weak logic structures early, then improve float resilience and sequencing before mobilization.

Even with modest discrimination, this is valuable as a **risk triage tool** (not yet a final decision oracle).

---

## 7) Technical Caveats and Next Improvements

1. Increase realism of synthetic generator using template archetypes (buildings, roads, utilities).
2. Improve minority detection with:
   - cost-sensitive learning,
   - focal loss (if boosted model path is used),
   - probability threshold optimization by risk tolerance.
3. Add external validation with real historical schedules/case outcomes.
4. Add uncertainty intervals around predicted risk (bootstrap).
5. Add scenario dashboard for interactive stress testing.

---

## 8) Reproducibility

- Main runner: [src/run_pipeline.py](../src/run_pipeline.py)
- Full methodology code:
  - [src/synthetic_schedule.py](../src/synthetic_schedule.py)
  - [src/simulation.py](../src/simulation.py)
  - [src/features.py](../src/features.py)
  - [src/train.py](../src/train.py)

This write-up corresponds to the latest generated files in [outputs](.).
