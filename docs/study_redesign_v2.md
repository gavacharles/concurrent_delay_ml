# Study Redesign v2 — Doctrine-Conditioned Causal Attribution for Concurrent Delay

**Working title:** *One Schedule, Many Laws: A Doctrine-Conditioned Explainable-AI Framework for Concurrent Delay under English, Scottish and SCL Protocol Approaches*

Status: design draft, 2026-11-09. Supersedes the framing in `outputs/paper_apportioning_liability_concurrent_delays.md`.

---

## 1. Why the study needs reframing

The v1 study used SHAP on an ML surrogate as *the* fair apportionment. That has three problems:

1. **There is no single "correct" apportionment to learn.** Concurrent delay outcomes depend on the legal system and on the contract. English courts give the contractor time but not money for true concurrency. Scotland (City Inn) apportions. The SCL Protocol has its own rules. A single SHAP split ignores the question a tribunal actually asks.
2. **SHAP's baseline was wrong for causation.** TreeSHAP measures contributions against the *average* scenario. Legal causation asks "compared with the as-planned / no-event world" (but-for). That mismatch produced the 100/0 splits and the unstable Balanced-Moderate result.
3. **The benchmark was circular.** CPM heuristics were scored against SHAP, which was itself the thing being tested.

**v2's central idea:** keep one causal model of the schedule and treat each legal doctrine as a different, explicitly defined attribution operator applied to it. The XAI contribution then has two parts:
- (a) make each doctrine's outcome computable and auditable;
- (b) explain *when and why* the doctrines diverge, i.e. when forum, governing law or contract drafting changes the answer.

---

## 2. Legal landscape (what the model must encode)

> *Thomas Barnes* (2022) is the latest English authority, and it was verified against the full judgment on the National Archives' Find Case Law service on 2026-11-09. BAILII refuses automated access (HTTP 403). Every other citation and pinpoint still needs checking against the judgments before submission. No 3rd edition of the SCL Protocol was found.

### 2.1 England & Wales

| Authority | Proposition used in the model |
|---|---|
| *Henry Boot v Malmaison* (1999) | Concurrent employer and contractor delay: the contractor gets an **extension of time (EOT)** for the employer event even though its own concurrent delay exists. Time only, no money ("Malmaison approach"). |
| *Royal Brompton Hospital v Hammond* (2001) | Concurrency is narrow. Being "concurrent" in the calendar is not enough; the events must both actually cause delay to completion. |
| *Adyard v SD Marine* [2011] EWHC 848 (Comm) | True concurrency = two or more **effective causes of roughly equal causative potency**. An employer act that occurs while the contractor is already in culpable delay may cause no *actual* delay ("first-in-time" reading). |
| *Saga Cruises v Fincantieri* [2016] EWHC 1875 (Comm) | Follows Adyard: a later event that does not affect the already-delayed completion date is not an effective cause. |
| *Walter Lilly v Mackay* [2012] EWHC 1773 (TCC) | Follows Malmaison for EOT and **rejects City Inn apportionment** in England. |
| *North Midland Building v Cyden Homes* [2018] EWCA Civ 1744 | Parties may contract out: a clause excluding concurrent delay from EOT is enforceable. The prevention principle is an implied term and can be displaced. |
| *Thomas Barnes & Sons v Blackburn with Darwen BC* [2022] EWHC 2598 (TCC), HHJ Stephen Davies. **The most recent English authority.** | Counsel agreed (para 118) that the law is "settled" as in *De Beers*, *Adyard* [277] and *Walter Lilly* [370], summarised by Keating 9-105. **Time:** EOT if the event "was an effective cause of delay". **Money:** only where the "but for" test is met. The contractor-risk roof-coverings delay and the employer-risk hub steel deflection (AI 18) were "concurrent over the period of delay" because both were on the critical path to the hub finishes (para 140). Result: EOT of **119 days** (133 days less 2 days mitigation less 12 days of contractor delay), but prolongation of **only 27 days** "net of the concurrent delay" (paras 148, 157). The judgment does not mention *Malmaison*, *Cyden* or "first-in-time". On the SCL Protocol, it is "not intended to be ... a statement of the law" (para 109). The "effective cause vs first-in-time" tension comes from **commentators** contrasting this case with *Adyard*/*Saga*. The court itself treated *Adyard* as part of the settled law. |

### 2.2 Scotland

| Authority | Proposition |
|---|---|
| *City Inn v Shepherd Construction* [2007] CSOH 190; [2010] CSIH 68 | If a dominant cause exists, it governs. If not, the EOT may be **apportioned** between the concurrent causes on a fair and reasonable basis, considering **causative significance and degree of culpability**. Lord Carloway dissented on apportionment. |
| *John Doyle v Laing Management* [2004] CSIH | Apportionment and global claims: the background to City Inn. |

### 2.3 SCL Delay and Disruption Protocol (2nd ed., Feb 2017)

- Concurrency is defined narrowly ("true concurrency" is rare). The employer and contractor events must both be effective causes of delay to **completion**, and their *effects* must be felt at the same time.
- **Time:** where true concurrency exists, the contractor's concurrent delay should not reduce the EOT (aligned with Malmaison).
- **Money:** the contractor recovers compensation only for loss it can show was caused by the employer risk event and **would not have been incurred anyway** due to its own concurrent delay (separability).
- It prefers prospective time-impact analysis during the project, and gives a menu of retrospective methods (as-planned vs as-built, windows, collapsed as-built, etc.).
- Status: guidance, not law. The contract prevails.

### 2.4 Comparators (for context and later extension)
- **US:** concurrent delay is generally excusable but non-compensable, with apportionment where delays are separable.
- **FIDIC 2017** Sub-Cl. 8.5: concurrency is assessed by rules in the Special Provisions, or "as appropriate, taking due regard of all relevant circumstances".
- **Drafting:** JCT / NEC4 have no express concurrency rule. After Cyden, bespoke exclusion clauses are common.

### 2.5 Closest technical literature
- Huynh, Lucko & Eid, "Game Theory Approach for Concurrent Delay Analysis", *JCEM* 149(3), 2023, doi:10.1061/JCEMD4.COENG-12947, plus an **erratum** in 150(4) and CRC 2022/2024 papers. These apply Shapley values to concurrent delay.
  - **Gap v2 fills:** that work produces *one* apportionment. It does not encode the competing legal doctrines, does not separate time from money, and does not model order in time or uncertainty.
- Causal Shapley values / asymmetric Shapley values from the XAI literature. They provide the tools for causally faithful and time-ordered attribution.

---

## 3. The framework

### 3.1 Causal model of the schedule
- The CPM network is treated as a **structural causal model (SCM)**. Nodes are activities, the structural equations are ES/EF recursions, and the exogenous noise is duration uncertainty.
- **Delay events** are the "players": a set N = {e₁ … eₙ}. Each has an owner (Employer / Contractor / Neutral), a start date, a duration impact, the target activities it affects, and a culpability attribute.
- **Characteristic function:** v(S) = delay to completion when only the events in S occur, measured against the as-planned date.
  - It is computed by running CPM, not by an ML model.
  - The as-planned (empty-set) baseline is what makes this a but-for test.
- **Time dimension:** events carry dates, so we can also evaluate v along the actual chronological order (needed for the first-in-time test).

### 3.2 Doctrines as attribution operators on v

| Doctrine | Operator (Employer side, E = employer events, C = contractor events) | Output |
|---|---|---|
| **Pure but-for (control)** | v(N) − v(N∖E). With N = E ∪ C this equals the SCL money rule below: but-for and separability are the same quantity. | days the employer is solely responsible for |
| **English: Malmaison / effective cause (Thomas Barnes)** | EOT = v(E) restricted to effective causes. An employer event counts if it is an *actual cause* (Halpern–Pearl): it changes completion under some admissible contingency. | EOT days (full time for concurrency) |
| **English: first-in-time (Adyard / Saga)** | Marginal contribution of each event **in chronological order**. This is the Shapley value restricted to the single real-world permutation. Later events that add no delay get 0. | EOT days |
| **Scottish: City Inn** | (i) If one event is *dominant* (its symmetric Shapley share ≥ threshold τ), it takes the period. (ii) Otherwise use a **weighted Shapley value** (Kalai–Samet), with weights = culpability. | apportioned EOT days |
| **SCL Protocol – time** | A hybrid. Events are processed in chronological order (an employer event that occurs during existing contractor delay and does not push completion further gets no EOT). Events whose effects start within a concurrency window *w* of each other are a "true concurrency" group, and inside that group the employer gets its full stand-alone effect (Malmaison). | EOT days |
| **SCL Protocol / Malmaison – money** | Compensable days = v(E ∪ C) − v(C), the employer's increment *over* what the contractor would have caused anyway (separability). | compensable days |
| **Contractual override (Cyden)** | If the contract has an exclusion clause, the EOT for concurrent periods = 0. | EOT days |
| **Symmetric causal Shapley (v1, fixed)** | Standard Shapley on v with an as-planned baseline. | descriptive split |

**Key properties to prove or demonstrate:**
- All operators coincide when there is **no overlap**.
- They diverge only in specific structural regions: parallel near-critical paths, events close together in time, high merge-bias.
- The SCL money rule and the Thomas Barnes result (119 days of EOT, 27 days of prolongation) are the same pair of quantities: EOT = min(v(E), v(N)) and money = v(E∪C) − v(C).

### 3.3 Where the ML / XAI actually comes in
v1 used ML as a surrogate for a two-input function that can be computed exactly. That is hard to defend. v2 uses ML where it adds value:

1. **Scale (surrogate).** Real schedules (P6/XER, thousands of activities, dozens of events) make the 2ⁿ coalition enumeration and Monte Carlo duration uncertainty expensive.
   - Train a graph-aware surrogate for v(S).
   - Estimate the values with KernelSHAP / permutation sampling.
   - Report the approximation error against exact enumeration on small cases (validation).
2. **Divergence explanation (the main XAI result).**
   - For thousands of synthetic schedule-plus-event configurations, compute the **doctrine gap**, e.g. Δ = EOT_CityInn − EOT_Malmaison, or EOT_first-in-time − EOT_effective-cause.
   - Train a model to predict Δ from *ex-ante* features: float distribution, path convergence, event timing gap, event location relative to the critical path, merge-bias, culpability mix.
   - Explain it with SHAP (and interaction values).
   - Output: an interpretable map of *which schedule conditions make the choice of forum or doctrine matter*.
3. **Pre-execution risk screening** (re-uses the old `concurrent_delay_ml` idea). Before the project starts, predict the exposure to doctrine-sensitive concurrency for a given baseline programme. This informs contract drafting (Cyden-style clauses) and the choice of law or seat.
4. **Uncertainty.** Duration noise gives a *distribution* of outcomes per doctrine. Report intervals and the probability that the doctrine changes the outcome.

---

## 4. Research questions & hypotheses

- **RQ1.** Can the dominant English, Scottish and SCL Protocol approaches be formalised as attribution operators on a single causal schedule model, with full fidelity to decided outcomes?
- **RQ2.** Under what structural and temporal schedule conditions do these doctrines produce materially different time and money outcomes?
- **RQ3.** Can an explainable model predict, before execution, a programme's exposure to doctrine-dependent outcomes?
- **RQ4.** How sensitive are the outcomes to duration uncertainty, and to the choice of analysis method (prospective time-impact analysis vs retrospective windows)?

Hypotheses:
- **H1:** Each operator reproduces the outcome of the stylised fact pattern of its source case (doctrinal fidelity test).
- **H2:** Doctrine divergence concentrates where (i) the employer and contractor events sit on parallel paths with low float difference, and (ii) the time gap between the events is shorter than the available float. It is near-zero elsewhere.
- **H3:** First-in-time and effective-cause diverge mainly on event *order*. City Inn and Malmaison diverge mainly on *relative magnitude*.
- **H4:** The money rule v(E∪C) − v(C) is stable across all doctrines. Divergence is primarily a *time* phenomenon.

---

## 5. Validation design (replaces the circular benchmark)

1. **Doctrinal fidelity suite.** Encode stylised fact patterns from Malmaison, Royal Brompton, Adyard, Saga Cruises, City Inn, Walter Lilly and Thomas Barnes as small networks. Use facts from the judgments only, recorded with paragraph references in `cases/*.yaml`.
   - Test: each operator reproduces the tribunal's direction of outcome (and the quantum where the judgment allows it).
   - Record cases where the operator *cannot* reproduce the outcome. Those are findings about where the formalisation breaks, not failures to hide.
2. **Axiomatic checks.** Efficiency, symmetry, null player, and the order property for first-in-time. Implement these as unit tests.
3. **Surrogate fidelity.** Compare surrogate-estimated against exact values on networks with n ≤ 12 events.
4. **Expert elicitation (optional, strong).** 5–10 delay experts or construction lawyers allocate time and money on 10 vignettes. Measure agreement with each operator (Krippendorff's α among experts, and distance to each operator).
5. **Real schedule demonstration.** One or two anonymised real or published schedules (XER/XML), if obtainable.

---

## 6. Data & experiments

| Experiment | Data | Output |
|---|---|---|
| E1 Fidelity | `cases/` stylised networks | pass/fail table per doctrine × case |
| E2 Divergence map | ~5–10k synthetic networks (archetypes: parallel paths, merge-heavy, linear, the v1 30-activity net) × event configurations | Δ distributions; SHAP explanation of Δ |
| E3 Order sensitivity | sweep of the employer–contractor time gap | phase diagram: first-in-time vs effective cause |
| E4 Uncertainty | Monte Carlo durations (triangular / PERT) | outcome intervals per doctrine; P(outcome changes) |
| E5 Ex-ante screening | features of the baseline programme only | predictive performance (AUC, calibration) + SHAP |
| E6 Scale | larger synthetic and real schedules | surrogate error vs exact; run time |

Metrics: days of EOT, compensable days, divergence |Δ|, fidelity rate, calibration (Brier), and the surrogate's attribution error.

---

## 7. Repo restructuring plan

```
src/
  schedule/        network generation, CPM engine, XER import (later)
  events/          delay-event model (party, date, impact, culpability)
  doctrines/       one module per operator + registry
    but_for.py  malmaison.py  first_in_time.py  city_inn.py  scl_protocol.py  contract_override.py
  attribution/     exact Shapley, weighted Shapley, ordered/actual-cause, sampling estimators
  surrogate/       ML surrogate for v(S) at scale
  divergence/      Δ dataset builder + explainable model (SHAP)
  experiments/     E1–E6 runners
cases/             stylised case fact patterns (YAML, with judgment para refs)
tests/             axioms + doctrinal fidelity
docs/              this design, legal notes
outputs/v1/        archive the existing results unchanged
```
- Archive the current outputs as v1.
- Add `shap` and `xgboost` to `requirements.txt` and pin versions.
- Fold the duplicate `liability_xai` repo into this one, or archive it.

## 8. Build order
1. CPM engine + event model + exact v(S) (reuse `_project_completion`).
2. Doctrine operators + axiom tests.
3. Case fact patterns + fidelity suite (E1). **Gate:** fix the operators until the fidelity suite is understood.
4. Divergence dataset + explainable model (E2, E3).
5. Uncertainty (E4), ex-ante screening (E5), scale/surrogate (E6).
6. Paper rewrite.

## 9. Contribution statement (draft)
1. The first formal, executable encoding of the competing UK concurrency doctrines (Malmaison/effective cause, first-in-time, City Inn apportionment, SCL Protocol time vs money, contractual override) as attribution operators on one causal schedule model.
2. A doctrinal-fidelity validation against decided cases, replacing self-referential benchmarks.
3. An explainable map of *when the law matters*: the schedule conditions under which jurisdiction, doctrine or drafting changes the outcome. This is usable ex ante for drafting and risk allocation.

## 10. Limits to state up front
- Legal causation contains normative judgement (e.g. "culpability", "dominant"). The operators make those choices explicit and parameterised; they do not remove them.
- English concurrency authority is mostly first instance (the CA in Cyden called the position under unamended JCT "not entirely free from doubt"). The model presents doctrines as alternatives, not as settled law.
- The contract governs. Every result is conditional on the contract terms that are encoded.
- The tool supports experts' analysis; it does not determine liability.

---

## 11. Results update (v2.1, 2026-11-10)

**Case library checked against the judgments.** Adyard, Saga Cruises, Walter Lilly, De Beers, Thomas Barnes and Cyden were read on the National Archives' Find Case Law service. City Inn could not be retrieved automatically and is still illustrative. Two corrections followed:
- Adyard para 279 *is* the "felt at the same time" test, and Saga para 251 requires "a concurrency actually affecting the completion date as then scheduled". The strict first-in-time reading is a commentators' gloss.
- Adyard para 264 and Saga para 249(iv) reject notional or theoretical delay. That counts against the as-planned impact reading.

**Actual-delay gateway.** A new rule, written from those passages: an employer event counts only if it adds actual delay given what came before it. If it does, the contractor's concurrent delay does not reduce the extension. It is the only rule that reproduces all five English cases (Malmaison, Adyard, Saga, Walter Lilly, Thomas Barnes). Because it was written after reading them, this shows consistency, not prediction.

**Formal results** (`docs/formal_results.md`, property-tested in `tests/test_formal.py`):
- money converges across the English readings;
- the rules have a strict ordering;
- the gateway has a cliff edge;
- windows analysis is not monotone in window length;
- the English readings form a continuum;
- NEC4 pays whatever time it grants.

**Contract regimes** (`cdx/contracts.py`): JCT under English law, a Cyden clause, Scots law, NEC4 clause 63.5 (reading to verify), and FIDIC 2017 Sub-Clause 8.5 both without a Special Provision (gives a range) and with one.

**Real programme: Package 5 road upgrade (Uganda), impacted MS Project file** (`src/experiments/run_real.py`; data and outputs kept out of git):
- The CPM engine reproduces MS Project's dates for 167/167 activities. It handles SS, FF and FS links, lags, constraints, calendars and the 10 task interruptions.
- **Programme fitness:**
  - 37% of activities have no predecessor and 56% have no successor;
  - 55% are held by hard date constraints, and 66% of links carry lags;
  - completion is driven by a start-no-earlier-than date (Sub base, 21 Aug 2022), not by logic;
  - finish-no-earlier-than constraints make delay non-monotone, so a logic-only model is needed;
  - none of the 10 interruptions affects completion.
- **Scenario:** a documented 40-day land-access delay (programme 21 Aug 2022 vs report 30 Sep 2022) plus a hypothetical 30-day contractor readiness delay felt earlier. The rules give 10 days (Cyden, strict sequence, NEC4), 25 (City Inn) or 40 (gateway, overlapping windows, as-planned), with 10 days paid under every rule except NEC4.
- **Windows analysis:** 30-day windows give the full 40 days for 29% of possible window start dates.
- **Uncertainty:** under duration uncertainty the gateway's outcome is two-peaked (13% of runs below 5 days, 87% above 30).
- **Divergence model:** too little signal on this programme, because almost every activity has very large float. This is a data-quality finding in its own right.

**Synthetic divergence model (E2) with richer features.** R² for the gap between English readings rose from 0.32 to 0.47. A screen using only before-the-event information predicts whether the English readings will differ by more than 7 days with AUC 0.85.

## 12. Results update (v2.2, 2026-11-10): Package 5 back-propagation, neutral events, notices

- **Contract** (PKG5 contract document): FIDIC 1999 Yellow; laws of Uganda; 1099 days; site access within 546 days; delay damages 0.05%/day capped at 10%; no concurrency Special Provision. The Employer was responsible for access and payment.
- **Back-propagation** (`cdx/backprop.py`): a backward pass from the contractual completion date, with a bisection to correct for calendars. 16 slippages (13 employer access, 3 contractor production) reproduce the 453-day overrun exactly. There are 58 days of terminal float, because the contract date falls in the rain season.
- **Outcomes:** 449–453 days of extension, 449 paid. Shapley attribution gives the employer 452 of 453 days, with Section 2 pavement access alone at 341.
- **Neutral events** (party "N": time without money; FIDIC 1999 Sub-Cl. 8.4(d)): 122 days of lockdown overlap do not reduce the paid days. Access was already late, and the terminal float absorbs the lockdown days on their own.
- **Notice gate** (`cdx/notices.py`, Sub-Cl. 20.1): with no notice for the pavement access, the extension is 191 days, 0 paid, and delay damages reach the 10% cap.
- **XAI ensemble** (1,500 variants): surrogate R² 0.95 (extension), 0.94 (paid), 0.94 (days the contractor carries). Pavement access responsibility is the top driver throughout. Screening AUC 0.84.
- **Expert survey:** dropped by decision on 2026-11-10. Validation relies on the case test, formal properties, engine reproduction and synthetic experiments.
- **Paper draft:** `docs/paper_v2_draft.md`. Posts revised in `docs/posts/`.
