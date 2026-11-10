# Chapter Draft: Predicting Concurrent Delay Vulnerability in Critical Path Networks

## 1. Introduction
Concurrent delay remains one of the most contested issues in project controls and claims analysis. This study develops a machine learning early-warning framework to estimate whether a schedule configuration is vulnerable to concurrent delay before project execution. The core idea is to combine schedule topology, float behavior, and risk-process assumptions into a predictive classifier that supports preventive planning.

## 2. Research Objective
The objective is to test whether an ensemble model can learn meaningful relationships between:
- schedule structure,
- owner and contractor risk conditions,
- and the probability of concurrent delay occurrence.

The intended contribution is a planning-stage screening capability for identifying vulnerable schedule logic before site mobilization.

## 3. Methodology

### 3.1 Synthetic schedule generation
A CPM-like synthetic schedule generator was built with layered DAG logic to represent parallel work fronts and precedence constraints. Structural descriptors were extracted, including activity count, edge density, float statistics, critical activity proportion, and baseline duration.

Implementation reference: [src/synthetic_schedule.py](../src/synthetic_schedule.py)

### 3.2 Monte Carlo risk simulation
For each generated schedule, repeated simulations injected owner-side and contractor-side delay events. Delay severity and overlap behavior were influenced by structural fragility and logic complexity. A binary target label was created to indicate whether concurrent delay conditions were met.

Implementation reference: [src/simulation.py](../src/simulation.py)

### 3.3 Dataset assembly
A supervised dataset was built from 450 schedules with 90 simulations each. This produced a large sample of schedule-outcome observations for training and evaluation.

Dataset output: [data/concurrent_delay_training_data.csv](../data/concurrent_delay_training_data.csv)

### 3.4 Model training and leakage controls
The training pipeline used grouped splitting by schedule identity to prevent cross-schedule leakage between train and test folds. Leakage-sensitive post-outcome variables were excluded from feature inputs. Probability calibration was applied and explainability was computed with SHAP.

Implementation reference: [src/train.py](../src/train.py)

Pipeline entry point: [src/run_pipeline.py](../src/run_pipeline.py)

## 4. Results

### 4.1 Predictive performance
From [model_metrics.csv](model_metrics.csv):
- Accuracy: 0.9433
- Balanced accuracy: 0.5030
- Precision: 0.0854
- Recall: 0.0138
- F1: 0.0237
- ROC AUC: 0.6183
- PR AUC: 0.0697
- Brier score: 0.0473

These results indicate modest ranking power above chance (ROC AUC > 0.5), but weak minority-event capture under imbalance.

Performance visual: [plots/evaluation_metrics.png](plots/evaluation_metrics.png)

### 4.2 Feature influence
Model-level importance and SHAP importance both show risk likelihood terms as dominant drivers, followed by structural fragility/float attributes.

Model importance table: [feature_importance.csv](feature_importance.csv)

SHAP table: [explainability_importance.csv](explainability_importance.csv)

Visuals:
- [plots/top10_model_feature_importance.png](plots/top10_model_feature_importance.png)
- [plots/top10_shap_importance.png](plots/top10_shap_importance.png)

### 4.3 Calibration quality
Calibration outputs show low-probability regime predictions with mixed local over/under-confidence across bins.

Calibration table: [calibration_curve.csv](calibration_curve.csv)

Calibration visual: [plots/calibration_curve.png](plots/calibration_curve.png)

## 5. Discussion
The framework demonstrates that schedule-risk representation can support pre-execution concurrent-delay screening. The methodological safeguards (grouped split and leakage exclusion) improve validity. However, event imbalance significantly limits recall and F1, suggesting the model currently works better as a vulnerability ranking aid than as a high-sensitivity detector.

## 6. Practical Implications
For project managers and planners, the workflow can be used to:
- stress-test schedule logic alternatives,
- detect structures with high concurrent-delay susceptibility,
- prioritize preventive redesign of float distribution and sequencing.

## 7. Limitations
- Synthetic data may not capture all real project complexities.
- Class imbalance remains a major constraint for detection sensitivity.
- External validation with real schedule-outcome data is still required.

## 8. Recommended Next Work
1. Add real schedule imports and historical claims outcomes for external validation.
2. Optimize decision thresholds for operational risk tolerance.
3. Introduce cost-sensitive learning and imbalance-aware training objectives.
4. Extend explainability to instance-level case diagnostics for claims review.

## 9. Conclusion
This study establishes a functional and reproducible baseline for concurrent-delay vulnerability prediction. The model captures non-trivial signal and provides interpretable risk drivers, but sensitivity to rare concurrent-delay events remains limited. As a result, the present system is best positioned as an early-warning screening tool, with clear pathways for advancement to production-grade decision support.
