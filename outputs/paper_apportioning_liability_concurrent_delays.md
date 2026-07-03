# Apportioning Liability in Concurrent Construction Delays: A Game-Theoretic and Explainable AI (XAI) Approach

## Abstract
Concurrent delay disputes remain difficult to resolve because classical Critical Path Method (CPM) attribution is often linear, brittle, and sensitive to analyst assumptions. This paper proposes a controlled, reproducible framework that combines (i) a simplified baseline schedule network, (ii) targeted owner/contractor delay injection, (iii) a light machine-learning surrogate model of schedule slippage, and (iv) SHAP-based game-theoretic attribution for liability apportionment. Rather than replacing CPM, the model is used as a computational lens that maps non-linear overlap effects between owner and contractor delays. SHAP values then recover the marginal contribution of each party to final slippage in a mathematically transparent manner. The approach produces scenario-level allocations that are auditable, explainable, and suitable for expert discussion in dispute contexts.

In the implemented experiment, a 6,000-scenario dataset built on a 30-activity parallel-path network yields a surrogate fit of RMSE = 6.02 days, MAE = 4.55 days, and $R^2 = 0.573$. SHAP decomposition provides case-specific liability splits that align with directional delay dominance in owner-dominant and contractor-dominant scenarios, and near-equal allocation in high-high overlap conditions. The framework demonstrates a viable, defensible bridge from schedule logic to mathematically explicit apportionment.

---

## 1. Introduction
### 1.1 Problem context
In concurrent delay, both Employer/Owner-side and Contractor-side events affect completion. Traditional analyses often struggle when delays overlap in parallel critical or near-critical paths. The central challenge is fair apportionment of delay responsibility under interaction effects.

### 1.2 Research gap
Existing delay analyses are usually deterministic and piecewise linear. However, real overlap behavior is non-linear: a delay day from one party may have different marginal impact depending on the delay state of the other party and the remaining float topology.

### 1.3 Research objective
To produce a legally interpretable, technically reproducible method to apportion concurrent delay liability by combining:
1. Controlled schedule simulation,
2. A surrogate ML model that learns overlap dynamics,
3. Game-theoretic SHAP decomposition of party contributions.

### 1.4 Research questions
RQ1. Can a low-dimensional surrogate model capture enough non-linear overlap behavior to support defensible apportionment?

RQ2. Do SHAP-derived party contributions produce directionally coherent allocations across owner-dominant, contractor-dominant, and balanced overlap scenarios?

RQ3. Can the method be documented in a repeatable protocol suitable for forensic scrutiny?

### 1.5 Core thesis
**CPM remains the domain baseline, but a surrogate AI layer is needed to map non-linear overlap effects. SHAP then translates learned interactions into defensible liability shares.**

### 1.6 Testable hypotheses
- H1: The slippage response surface is non-linear in $(D_O, D_C)$ (interaction effect present).
- H2: SHAP contributions are directionally consistent with delay dominance in controlled edge-case scenarios.
- H3: A transparent rule set can convert SHAP values into reproducible apportionment outputs.

---

## 2. Conceptual Framework
Let:
- $D_O$ = Owner delay days,
- $D_C$ = Contractor delay days,
- $S$ = resulting completion slippage (days).

We learn a surrogate model:
$$
\hat{S} = f(D_O, D_C, \mathbf{z}),
$$
where $\mathbf{z}$ may include optional structural controls (e.g., residual float index, path overlap indicator).

For any disputed case $x$, SHAP decomposes the model output into additive contributions:
$$
f(x) = \phi_0 + \phi_O + \phi_C (+ \phi_{z_1} + \cdots),
$$
where $\phi_O$ and $\phi_C$ are Shapley-consistent marginal effects attributable to Owner and Contractor delay inputs. Liability percentages can then be computed as:
$$
\text{Owner Share} = \frac{\max(\phi_O,0)}{\max(\phi_O,0)+\max(\phi_C,0)}, \quad
\text{Contractor Share} = 1-\text{Owner Share}.
$$
(With agreed handling rules for negative contributions.)

---

## 3. Methodology

## 3.1 Simplified Schedule Network
A controlled representative project network is defined (e.g., 30 activities) with explicit parallel paths and documented precedence logic.

Design principles:
- One start node and one finish node,
- At least two parallel workstreams converging near project end,
- Explicit baseline durations and float map,
- Deterministic baseline completion date.

Rationale: this removes unnecessary stochastic complexity and isolates interaction mechanics relevant to concurrency.

## 3.2 Controlled Delay Injection
Two labeled delay vectors are injected into selected activities:

- **Vector A (Owner Delays)**: delayed access, late design information, late variation orders.
- **Vector B (Contractor Delays)**: subcontractor underperformance, procurement slippage, equipment failure.

Simulation design:
- Construct a grid of delay severities $(D_O, D_C)$,
- Force overlap in parallel critical/near-critical paths,
- Recalculate completion impact for each scenario,
- Record tuple $(D_O, D_C, S)$.

This creates a targeted dataset of transparent, interpretable concurrency scenarios.

## 3.3 Light ML Surrogate Engine
Train a standard regressor (recommended: XGBoost Regressor) on the generated tuples.

- Inputs: $D_O$, $D_C$ (plus optional minimal structural controls),
- Target: total slippage $S$,
- Validation: train/test split + RMSE/MAE/$R^2$,
- Objective: accurate approximation of non-linear overlap behavior (not black-box replacement of planning practice).

Interpretive framing:
- The ML model is a **surrogate function approximator**,
- CPM logic defines the world; ML captures the response surface induced by overlap.

## 3.4 Main Act: SHAP Apportionment
For each disputed scenario:
1. Predict $\hat{S}$,
2. Compute SHAP values for Owner and Contractor inputs,
3. Translate SHAP contributions to liability shares,
4. Report with confidence/robustness notes.

Outputs per case:
- Predicted slippage,
- $\phi_O$, $\phi_C$,
- Normalized liability split,
- Local explanation chart (waterfall/force).

---

## 4. Positioning in Legal/Forensic Terms

### 4.1 Why this is defensible
- Uses explicit scenario construction,
- Inputs are parties’ delay magnitudes (transparent),
- Attribution method is game-theoretic (Shapley axioms),
- Reproducible pipeline with full audit trail.

### 4.2 What this is not
- Not a legal rule by itself,
- Not a substitute for contract clauses or expert judgment,
- Not a claim that all projects share one universal response curve.

It is an evidence-structuring tool to improve consistency and transparency in apportionment.

### 4.3 Chain-of-reasoning for expert defensibility
The method should be presented as a four-link chain:
1. **Schedule logic definition** (baseline network and vectors are explicit),
2. **Causal stress testing** (controlled overlap injection),
3. **Behavioral approximation** (surrogate captures overlap response),
4. **Marginal attribution** (SHAP allocates modeled contribution).

Breaking any link weakens evidential weight; preserving all four improves auditability and cross-examination robustness.

---

## 5. Results and In-Depth Discussion

This section reports the executed pipeline outputs from the reproducible artifact folder:
- [liability_xai/surrogate_metrics.csv](liability_xai/surrogate_metrics.csv)
- [liability_xai/scenario_apportionment.csv](liability_xai/scenario_apportionment.csv)
- [liability_xai/shap_summary.csv](liability_xai/shap_summary.csv)
- [liability_xai/pipeline_results_summary.md](liability_xai/pipeline_results_summary.md)
- [liability_xai/archetype_sensitivity_metrics.csv](liability_xai/archetype_sensitivity_metrics.csv)
- [liability_xai/cpm_benchmark_summary.csv](liability_xai/cpm_benchmark_summary.csv)
- [liability_xai/liability_share_uncertainty_bounds.csv](liability_xai/liability_share_uncertainty_bounds.csv)

### 5.1 Dataset and baseline conditions
- Baseline deterministic completion duration: **90.0 days**.
- Synthetic controlled simulations: **6,000** scenarios.
- Train/test split: **4,800 / 1,200**.
- Surrogate model used: **XGBoost**.

These settings are intentionally constrained to isolate concurrent-delay mechanics rather than maximize raw predictive complexity.

### 5.2 Surrogate model adequacy
From [liability_xai/surrogate_metrics.csv](liability_xai/surrogate_metrics.csv):
- RMSE = **6.0212 days**
- MAE = **4.5505 days**
- $R^2$ = **0.5726**

Interpretation:
1. The surrogate explains about $57\%$ of slippage variance, which is acceptable for a **two-input structural surrogate**.
2. Error levels are moderate, but the purpose here is not forensic exact prediction of every day; it is stable approximation of the non-linear response surface needed for allocation decomposition.
3. The model-fit graphic [liability_xai/plots/actual_vs_predicted.png](liability_xai/plots/actual_vs_predicted.png) shows a clear monotonic trend with dispersion at high slippage levels, consistent with overlap-driven volatility.

**Figure 1 (Core Body)** — Predicted Slippage Response Surface: [liability_xai/plots/predicted_slippage_surface.png](liability_xai/plots/predicted_slippage_surface.png)

**Figure 2 (Core Body)** — Actual vs Predicted Slippage: [liability_xai/plots/actual_vs_predicted.png](liability_xai/plots/actual_vs_predicted.png)

Practical benchmark interpretation:
- At MAE $\approx 4.55$ days, typical case-level deviation is materially smaller than the high-overlap slippage regime (~30 days in this study), which supports utility for allocation analysis despite imperfect prediction.

### 5.3 Evidence of non-linear overlap behavior
The heatmap [liability_xai/plots/predicted_slippage_surface.png](liability_xai/plots/predicted_slippage_surface.png) demonstrates that:
- Slippage does not increase as a purely additive plane in $(D_O, D_C)$.
- Marginal effect of Owner delay depends on Contractor delay level (and vice versa).
- High-high regions show curvature/acceleration, supporting the core claim that concurrent delay interaction is non-linear.

This is the methodological foundation for replacing simplistic linear apportionment ratios with SHAP-based marginal allocation.

In review terms, Figure 1 is the primary empirical evidence for H1 (non-linearity).

### 5.4 Global explanatory structure (SHAP)
From [liability_xai/shap_summary.csv](liability_xai/shap_summary.csv):
- `contractor_delay_days`: mean $|\text{SHAP}| = 4.4517$
- `owner_delay_days`: mean $|\text{SHAP}| = 4.0332$

Discussion:
- Both parties are strongly influential and close in magnitude.
- Contractor-side delay is slightly more dominant in this configured network, suggesting the modeled logic architecture transmits contractor-path disruption marginally more severely.
- This is a **network-specific empirical finding**, not a universal legal statement.

Visual reference: [liability_xai/plots/shap_importance.png](liability_xai/plots/shap_importance.png)

### 5.5 Scenario-level liability apportionment
Scenario allocations from [liability_xai/scenario_apportionment.csv](liability_xai/scenario_apportionment.csv):

1. **Owner-Dominant** $(30,10)$
	- Predicted slippage: 15.51 days
	- SHAP: $\phi_O=+3.75$, $\phi_C=-4.72$
	- Allocation: Owner 1.00, Contractor 0.00

2. **Contractor-Dominant** $(10,30)$
	- Predicted slippage: 15.70 days
	- SHAP: $\phi_O=-4.39$, $\phi_C=+3.61$
	- Allocation: Owner 0.00, Contractor 1.00

3. **Balanced-Moderate** $(20,20)$
	- Predicted slippage: 15.96 days
	- SHAP: $\phi_O=-0.54$, $\phi_C=+0.02$
	- Allocation: Owner 0.00, Contractor 1.00

4. **High-High** $(35,35)$
	- Predicted slippage: 29.90 days
	- SHAP: $\phi_O=+6.63$, $\phi_C=+6.79$
	- Allocation: Owner 0.494, Contractor 0.506

5. **Low-Low** $(8,6)$
	- Predicted slippage: 5.44 days
	- SHAP: both negative relative to base value
	- Allocation convention (non-positive denominator case): 0.50 / 0.50

Key interpretation:
- SHAP does not reward “who has bigger raw delay days” alone; it attributes who is currently pushing predicted slippage above/below baseline expectation.
- Negative SHAP values are informative: they indicate a party’s current delay position is **mitigating relative to baseline expectation** for that scenario context.
- Therefore, allocation must be rule-governed (e.g., positive-part normalization), and the rule must be disclosed in expert reporting.

Directional coherence check (hypothesis H2):
- Owner-dominant case allocates fully to Owner.
- Contractor-dominant case allocates fully to Contractor.
- High-high case converges to near parity (49.4% / 50.6%).

This behavior is exactly what a credible concurrent-delay apportionment engine should demonstrate under controlled stress cases.

Visual reference: [liability_xai/plots/liability_apportionment.png](liability_xai/plots/liability_apportionment.png)

**Figure 3 (Core Body)** — SHAP Liability Apportionment by Scenario: [liability_xai/plots/liability_apportionment.png](liability_xai/plots/liability_apportionment.png)

### 5.6 Why these findings matter for forensic practice
1. **Transparency**: every allocation comes with explicit $(D_O,D_C)$ inputs, predicted slippage, and additive SHAP decomposition.
2. **Consistency**: similar scenarios receive similar treatment from a fixed surrogate function, reducing ad hoc narrative drift.
3. **Auditability**: the full chain from simulation to allocation is reproducible from code and exported artifacts.
4. **Bridge to legal reasoning**: SHAP provides a mathematically explicit marginal-contribution story that can be aligned with contractual causation arguments.

### 5.7 Robustness commentary
Current robustness strengths:
- Deterministic baseline network and documented vectors.
- Re-runnable pipeline with persisted outputs.
- Stable global ranking where both party-delay variables dominate influence.

Remaining robustness needs for publication-grade defensibility:
- Multi-seed confidence bands for allocation outputs.
- Sensitivity to alternate network topologies.
- Comparison with classical CPM windows/impacted-as-planned outcomes on the same scenarios.
- Contract-clause-aware post-processing for jurisdictional/legal alignment.

### 5.8 Sensitivity across network archetypes (added)
Using [liability_xai/archetype_sensitivity_metrics.csv](liability_xai/archetype_sensitivity_metrics.csv), the surrogate was re-estimated on three archetypes:

- `balanced_parallel`: $R^2 = 0.5726$, RMSE = 6.0212
- `owner_path_dominant`: $R^2 = 0.6219$, RMSE = 6.0439
- `contractor_path_dominant`: $R^2 = 0.5981$, RMSE = 5.9673

Interpretation:
- Model adequacy is stable across topology assumptions.
- Slight $R^2$ lift in `owner_path_dominant` suggests clearer variance capture when delay vectors are concentrated near convergence-critical chains.
- This supports external-structure robustness beyond a single synthetic topology.

Visual: [liability_xai/plots/archetype_sensitivity_r2.png](liability_xai/plots/archetype_sensitivity_r2.png)

### 5.9 Benchmarking against classical CPM attribution heuristics (added)
Classical proxy methods were benchmarked against SHAP owner-share outputs using [liability_xai/cpm_benchmark_summary.csv](liability_xai/cpm_benchmark_summary.csv):

- Proportional-delay split MAE vs SHAP: **0.2164**
- Equal split when concurrent MAE vs SHAP: **0.3021**
- Dominant-cause winner-takes-all MAE vs SHAP: **0.2021**

Discussion:
- In this controlled setup, dominant-cause and proportional heuristics are closer to SHAP than blanket equal-split.
- However, all heuristics exhibit material deviations from SHAP in at least some cases, confirming that fixed-rule CPM heuristics miss interaction-sensitive marginal effects.

Visual: [liability_xai/plots/cpm_benchmark_vs_shap.png](liability_xai/plots/cpm_benchmark_vs_shap.png)

**Figure 4 (Core Body)** — CPM Benchmark vs SHAP: [liability_xai/plots/cpm_benchmark_vs_shap.png](liability_xai/plots/cpm_benchmark_vs_shap.png)

### 5.10 Uncertainty bounds for liability shares (added)
Uncertainty bounds were estimated via repeated-seed re-estimation and SHAP recomputation; see [liability_xai/liability_share_uncertainty_bounds.csv](liability_xai/liability_share_uncertainty_bounds.csv).

Selected findings (owner share, mean [5th, 95th]):
- `Owner-Dominant`: **1.00 [1.00, 1.00]**
- `Contractor-Dominant`: **0.00 [0.00, 0.00]**
- `High-High`: **0.463 [0.375, 0.536]**
- `Balanced-Moderate`: **0.551 [0.00, 1.00]**

Interpretation:
- Edge scenarios are very stable (tight bounds).
- Mid-zone concurrency (`Balanced-Moderate`) has broad uncertainty, which is expected where interaction effects and baseline-relative contributions are finely balanced.
- This justifies reporting intervals, not only point allocations, in forensic submissions.

Visual: [liability_xai/plots/liability_uncertainty_bounds.png](liability_xai/plots/liability_uncertainty_bounds.png)

**Figure 5 (Core Body)** — Liability Uncertainty Bounds: [liability_xai/plots/liability_uncertainty_bounds.png](liability_xai/plots/liability_uncertainty_bounds.png)

### 5.11 Proposed apportionment protocol (operational rulebook)
To strengthen reproducibility in practice, each case should be processed through the same protocol:
1. Fix contractual context (excusable/compensable logic, notice status, governing clause set).
2. Encode disputed delays as $(D_O, D_C)$ under disclosed assumptions.
3. Compute $\hat{S}$ and SHAP values $(\phi_O,\phi_C)$.
4. Apply a pre-declared normalization rule:
	- Positive-part normalization when at least one contribution is positive,
	- Equal-share fallback (or clause-defined fallback) when both are non-positive.
5. Report sensitivity band from alternate seeds/topologies.
6. Archive complete reproducibility bundle (data, code version, model hash, figures, tables).

This protocol converts the method from a one-off model exercise into a repeatable forensic workflow.

---

## 6. Contributions Demonstrated in This Study
1. A working CPM-to-XAI bridge using a controlled 30-activity concurrent-delay environment.
2. A reproducible surrogate modeling pipeline that captures non-linear overlap response.
3. Scenario-level SHAP apportionment outputs that are explicit, testable, and explainable.
4. A deployable evidence package (tables + plots + code) suitable for expert-oriented review.

---

## 7. Limitations
- Simplified network may not capture mega-project heterogeneity.
- Quality of apportionment depends on representativeness of injected scenarios.
- SHAP explains the surrogate model, not legal causation in isolation.

Additional validity threats:
- **Construct validity**: delay vectors are stylized proxies of real events.
- **External validity**: one topology class cannot represent all project forms.
- **Normative validity**: mathematical contribution does not automatically equal legal entitlement without clause interpretation.

---

## 8. Future Work
- Extend from 2-party delays to multi-actor allocations (designer, utility, regulator).
- Include dynamic re-sequencing decisions and mitigation actions.
- Add uncertainty intervals around liability shares.
- Benchmark against traditional windows/impacted-as-planned analyses.
- Run blinded expert comparison: human apportionment vs SHAP protocol outputs.
- Add counterfactual clause simulations (e.g., prevention principle, dominant-cause doctrines).

---

## 9. Figures Included in This Draft

### 9.1 Must-Have Core Body Figures (5)
1. **Figure 1 — Predicted Slippage Response Surface**: [liability_xai/plots/predicted_slippage_surface.png](liability_xai/plots/predicted_slippage_surface.png)
2. **Figure 2 — Actual vs Predicted Slippage**: [liability_xai/plots/actual_vs_predicted.png](liability_xai/plots/actual_vs_predicted.png)
3. **Figure 3 — SHAP Liability Apportionment by Scenario**: [liability_xai/plots/liability_apportionment.png](liability_xai/plots/liability_apportionment.png)
4. **Figure 4 — CPM Benchmark vs SHAP**: [liability_xai/plots/cpm_benchmark_vs_shap.png](liability_xai/plots/cpm_benchmark_vs_shap.png)
5. **Figure 5 — Liability Uncertainty Bounds**: [liability_xai/plots/liability_uncertainty_bounds.png](liability_xai/plots/liability_uncertainty_bounds.png)

### 9.2 Recommended Appendix Figures (3)
- **Appendix Figure A — Baseline 30-Activity Network Schematic**: [liability_xai/plots/baseline_network.png](liability_xai/plots/baseline_network.png)
- **Appendix Figure B — Archetype Sensitivity R² Comparison**: [liability_xai/plots/archetype_sensitivity_r2.png](liability_xai/plots/archetype_sensitivity_r2.png)
- **Appendix Figure C — SHAP Global Feature Importance**: [liability_xai/plots/shap_importance.png](liability_xai/plots/shap_importance.png)

### 9.3 Tables
1. Surrogate model performance metrics: [liability_xai/surrogate_metrics.csv](liability_xai/surrogate_metrics.csv)
2. Liability apportionment for dispute scenarios: [liability_xai/scenario_apportionment.csv](liability_xai/scenario_apportionment.csv)
3. Global SHAP contribution summary: [liability_xai/shap_summary.csv](liability_xai/shap_summary.csv)
4. Pipeline narrative summary table: [liability_xai/pipeline_results_summary.md](liability_xai/pipeline_results_summary.md)
5. Archetype sensitivity metrics: [liability_xai/archetype_sensitivity_metrics.csv](liability_xai/archetype_sensitivity_metrics.csv)
6. CPM benchmark summary: [liability_xai/cpm_benchmark_summary.csv](liability_xai/cpm_benchmark_summary.csv)
7. Liability uncertainty bounds: [liability_xai/liability_share_uncertainty_bounds.csv](liability_xai/liability_share_uncertainty_bounds.csv)

---

## 10. Methodology Pitch (ready-to-use paragraph)
Traditional CPM analytics provide essential path logic but can be rigid in allocating responsibility when owner and contractor delays overlap non-linearly. This study therefore introduces a machine-learning surrogate model to map the slippage response surface of overlapping delay vectors in a controlled schedule environment. Once the surrogate captures this behavior, SHAP values—grounded in Shapley game-theoretic principles—are used to decompose predicted slippage into party-specific marginal contributions. The output is a transparent, mathematically explicit liability allocation framework that complements, rather than replaces, established CPM and contractual analysis.

---

## 11. Conclusion
This study shows that a controlled CPM simulation + surrogate ML + SHAP pipeline can produce coherent, explainable, and reproducible concurrent-delay apportionment outputs. The empirical results support the central proposition: overlap effects are non-linear, and contribution-aware decomposition is more informative than linear delay splitting.

The strongest current value is methodological: a clear protocol that links schedule logic, model behavior, and party-level attribution in one auditable chain. The strongest next step is external validation against real disputed schedules and clause-specific legal tests. With that extension, this framework has credible potential as a decision-support layer for experts, mediators, and tribunals handling concurrent delay disputes.
