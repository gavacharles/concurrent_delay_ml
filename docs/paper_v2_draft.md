# One Schedule, Many Laws: Doctrine-Conditioned Causal Attribution and Explainable AI for Concurrent Delay

*Draft v2 — 10 November 2026. Supersedes `outputs/v1/paper_apportioning_liability_concurrent_delays.md`. The case study is anonymised.*

## Abstract

Concurrent delay is decided differently depending on the governing law and the contract. English courts grant time but not money for true concurrency. Scottish courts may apportion. The SCL Delay and Disruption Protocol offers guidance, and standard forms either stay silent, refer the question to special provisions, or let the parties contract out. Existing computational work, including game-theoretic and explainable-AI approaches, produces a single "fair" apportionment and so hides this legal choice.

This paper separates causation from attribution. The construction programme is modelled as a deterministic structural causal model: delay events are interventions, and the value function *v(S)* is the delay to completion against the contractual date. Each legal approach is then written as an explicit attribution operator on *v*. The operators cover strict sequence, an actual-delay gateway, overlapping windows, as-planned impact, City Inn apportionment, contractual exclusion, NEC4 prospective assessment, and neutral events that give time but not money. A notice condition is added as a gate on the contractor's claims.

Seven formal properties are proved and property-tested:
- the money entitlement converges across the English readings;
- the rules fall into a strict ordering;
- the gateway has a cliff edge;
- windows analysis is not monotone in window length.

Tested on fact patterns checked against six judgments, only the actual-delay gateway reproduces all five English authorities (Malmaison, Adyard, Saga Cruises, Walter Lilly, Thomas Barnes).

On 6,000 synthetic programmes, the English readings disagree in 31% of delayed cases. A screen using only information available before the events are analysed together predicts disagreement with AUC 0.85. On a real FIDIC 1999 design-and-build road programme, the impacted schedule is back-propagated to the contractual completion date. This recovers 16 slippages that explain the whole 453-day overrun. The legal readings then differ by at most 4 days. An explainable surrogate over 1,500 variants (R² 0.94–0.95) shows that the outcome turns on two things: who controlled access to one pavement workfront, and whether notice of it was given in time. The choice of concurrency doctrine matters much less.

---

## 1. Introduction

Delay analysts and tribunals often reach different conclusions from the same programme. Some of that comes from method (as-planned vs as-built, windows, collapsed as-built) and some from facts. A further part, and the subject of this paper, comes from *law*: the same causal facts lead to different entitlements under different legal approaches to concurrency.

Recent work applies cooperative game theory to concurrent delay. Huynh, Lucko and Eid (2023) use Shapley values to apportion liability, and a v1 version of this study used SHAP on a machine-learning surrogate. Both produce one apportionment. That is a category error. There is no single correct split for a model to discover, because English law, Scots law and the major standard forms have made different normative choices.

**Contributions.**
1. A formal separation of *causation*, a structural causal model of the programme, from *attribution*, legal operators on that model's value function. Neutral events and notice conditions are included.
2. Seven propositions about how the operators relate, each proved for two-party games and property-tested.
3. A fidelity test against fact patterns checked against the judgments. It singles out one reading of English law, the actual-delay gateway, as the only one consistent with all five authorities tested.
4. An explainable-AI layer that explains *when the law matters*, on synthetic programmes and on a real impacted programme reconstructed by back-propagation.
5. Practical findings on a real FIDIC 1999 project: programme quality, terminal float, neutral events, and the dominance of the notice condition.

## 2. Legal background

### 2.1 England and Wales

**Malmaison.** *Henry Boot v Malmaison* (1999) 70 Con LR 32 gives the contractor an extension "for the period of delay caused by the relevant event" despite a concurrent contractor cause (Dyson J at [13], as quoted in *Walter Lilly* at [367] and *Adyard* at [276]).

**Adyard.** *Adyard v SD Marine* [2011] EWHC 848 (Comm) adopts Marrin's definition of concurrency: two or more effective causes "of approximately equal causative potency" ([277]). It holds that "there is only concurrency if both events in fact cause delay to the progress of the works and the delaying effect of the two events is felt at the same time" ([279]). It rejects notional or theoretical delay ([264]) and holds that the employer's variations caused no actual delay to a project already in "irretrievable critical delay" ([293]–[299]).

**Saga Cruises.** *Saga Cruises v Fincantieri* [2016] EWHC 1875 (Comm) follows *Adyard*. It requires "a concurrency actually affecting the completion date as then scheduled" ([251]).

**Walter Lilly.** *Walter Lilly v Mackay* [2012] EWHC 1773 (TCC) holds *City Inn* "inapplicable within this jurisdiction" and confirms a full extension where a Relevant Event is an effective cause ([370]).

**De Beers.** *De Beers v Atos* [2010] EWHC 3276 (TCC) states the time-without-money rule ([177]–[178]).

**Thomas Barnes.** *Thomas Barnes v Blackburn with Darwen BC* [2022] EWHC 2598 (TCC) is the most recent authority. Counsel there agreed that the law is settled as summarised in Keating 9-105: time where the event is an effective cause, and money only on a but-for basis ([118]). The court found the roof-coverings and steel-deflection delays concurrent ([140]). It awarded 119 days' extension but only 27 days' prolongation ([148], [157]).

**Cyden.** *North Midland v Cyden Homes* [2018] EWCA Civ 1744 upholds a clause excluding concurrent delay from extensions ([6], [36], [39]). It notes that the position under unamended JCT forms "is not entirely free from doubt" ([17]).

### 2.2 Scotland

*City Inn v Shepherd Construction* [2010] CSIH 68 sets out a majority test:
- delay is a question of fact decided by common sense;
- a critical path analysis is not essential;
- a dominant cause governs;
- absent a dominant cause, the delay is apportioned fairly and reasonably.

Lord Carloway dissented on apportionment and would have looked at the relevant event in isolation. The extension awarded totalled nine weeks. *(This account comes from a secondary source; the judgment text is to be checked.)*

### 2.3 Guidance and standard forms

**SCL Protocol (2nd ed., 2017).** It treats true concurrency as rare and separates time from money. *Thomas Barnes* ([109]) records that it "is not intended to be ... a statement of the law".

**FIDIC 1999.** The 1999 forms are silent on concurrency. They give time for employer events (Sub-Clause 8.4) and time without cost for some neutral events, including epidemic and governmental action (8.4(d)). Claims must be notified within 28 days (20.1).

**Other forms.** FIDIC 2017 Sub-Clause 8.5 refers concurrency to the Special Provisions. NEC4 assesses compensation events prospectively, with time and money together (clause 63.5). JCT 2024 contains no express concurrency rule. *(Clause readings for NEC4, FIDIC 2017 and JCT 2024 are to be checked against the forms.)*

## 3. Related work

Delay-analysis methods are classified in AACE RP 29R-03 and the SCL Protocol. Game-theoretic apportionment of delay appears in Huynh, Lucko and Eid (*JCEM*, 2023; erratum 2024) and related Construction Research Congress papers. Shapley values are central to explainable AI (Rozemberczki et al., IJCAI 2022), as are causal and asymmetric variants that respect causal structure. Formal accounts of legal causation, such as the NESS test and Halpern–Pearl actual causation, inform the gateway operator.

To our knowledge, no prior work has done all three of the following:
- encoded the competing doctrines as separate operators on one causal model;
- tested them against decided cases;
- used XAI to explain where they diverge.

## 4. Framework

### 4.1 Causal model

The programme is an activity-on-node network with finish-to-start, start-to-start, finish-to-finish and start-to-finish links, lags, start- and finish-no-earlier-than constraints, actual dates, working calendars and summary roll-ups. Forward-pass recursions are the structural equations.

A delay event *e* = (party, activity, days, start), with party ∈ {Employer, Contractor, Neutral}, extends an activity's duration. For a set *S* of events:

> *v(S)* = max(0, finish(S) − *R*)

where *R* is the reference completion date: the programme's planned finish, or the contractual date. Using the contractual date lets terminal float absorb delay first.

Write *X* for the excusable events (Employer ∪ Neutral). Then:
- *vE* = *v(X)*, *vC* = *v(C)* and *vN* = *v(all)*;
- sole_E = *vN* − *vC*, the but-for delay of the excusable events;
- *K* = *vE* + *vC* − *vN*, the concurrent days (delay either side alone would have caused);
- the money term is *v(all)* − *v(all ∖ Employer)*.

### 4.2 Operators

| Operator | Time rule | Basis |
|---|---|---|
| Strict sequence | Chronological marginal contributions; only same-day events concurrent | Commentators' reading |
| **Actual-delay gateway** | An excusable event qualifies only if it adds actual delay given the events before it; a qualifying event is credited with its own effect | *Adyard* [279]–[299]; *Saga* [251]; *Walter Lilly* [370]; *Thomas Barnes* [118], [148] |
| Overlapping windows | Events with overlapping effect windows are concurrent (Malmaison inside the group) | Broad reading of "felt at the same time" |
| As-planned impact | min(*vE*, *vN*); timing ignored | Theoretical delay; cf. Lord Carloway |
| City Inn | Dominant cause (share ≥ τ) takes the period; otherwise *K* is apportioned by culpability | *City Inn* majority |
| Contractual exclusion | sole_E | *Cyden* |
| NEC4 prospective | Strict sequence; paid = time | Clause 63.5 (reading to verify) |
| Windows analysis | Chronology across fixed windows; Malmaison within each window | Practice |

**Money.** Under every operator except NEC4, money is min(money term, EOT). This follows Keating 9-105 and *De Beers* [177]–[178].

**Notice gate.** An excusable event without timely notice is reassigned to the contractor.

**Contract regimes.** These map a form and its governing law to an operator, or to a range of operators.

## 5. Formal properties

These hold for two-party games, with *K* ≥ 0 where stated. Proofs are in `docs/formal_results.md`, and property tests run on 1,500 random games.

- **P1 (money convergence).** With *K* ≥ 0, every English, Scottish and exclusion operator pays exactly sole_E. *Interpretation:* the dispute is about time.
- **P2 (ordering).** Exclusion = sole_E ≤ strict sequence ≤ gateway ≤ as-planned; strict sequence ≤ overlap ≤ as-planned; City Inn lies in [sole_E, *vE*]. The gateway and overlap operators cannot be ordered against each other.
- **P3.** The symmetric Shapley value equals the strict-sequence extension averaged over both possible orders.
- **P4 (cliff edge).** Under the gateway, one extra day of employer delay can move the extension by the contractor's whole delay plus one day.
- **P5.** Windows analysis is not monotone in window length.
- **P6.** Windows analysis spans the range from strict sequence (window → 0) to as-planned impact (one window covering everything).
- **P7.** NEC4 pays for the time it grants, including concurrent periods.

## 6. Fidelity test against decided cases

Each case is a two-path reconstruction. Dates and magnitudes are taken from the judgments where they are stated (Find Case Law, read 10 November 2026). Where a figure is a party's claim or is worked back from the outcome, the case file says so.

| Case | Court | Strict | **Gateway** | Overlap | As-planned | City Inn | Exclusion |
|---|---|---|---|---|---|---|---|
| Malmaison | 10 / 0 | ✓ | **✓** | ✓ | ✓ | ✗ (5) | ✗ (0) |
| Adyard | 0 / 0 | ✓ | **✓** | ✗ (124) | ✗ (124) | ✗ (62) | ✓ |
| Saga Cruises | 0 / 0 | ✓ | **✓** | ✗ (9) | ✗ (9) | ✗ (4.5) | ✓ |
| Walter Lilly | 507 / 507 | ✓ | **✓** | ✓ | ✓ | ✓ | ✓ |
| Thomas Barnes | 119 / 27 | ✗ (27) | **✓** | ✓ | ✓ | ✗ (73) | ✗ (27) |

Cells show the extension and paid days for the court, and ✓ or ✗ (with the extension in brackets) for each operator.

The gateway is the only operator that reproduces all five English cases. It was formulated from the judgments' own language, so this shows internal consistency, not out-of-sample prediction. The overlap and as-planned readings fail exactly where the courts insisted on actual delay. The strict reading fails *Thomas Barnes*.

## 7. Synthetic experiments

We generated 6,000 random layered networks (12–36 activities) with one to three events per party.

- **How often the law matters.** The four English readings disagree in **30.8%** of configurations (32.3% of delayed ones), with a median gap of 7 days. City Inn differs from the gateway in 34.4%.
- **Explanatory model.** An XGBoost surrogate of the gap between English readings reaches R² 0.47. The leading SHAP drivers are the stand-alone contractor delay, the overlap of the delay windows, and the time gap between the events.
- **Ex-ante screen.** A classifier using only features available before a joint schedule run predicts a gap of more than 7 days with **AUC 0.85**.
- **Phase diagrams.** On two parallel paths, the readings split by *when* the employer event occurs relative to the contractor's window, and by its size relative to the contractor's delay. This matches P2 and P4.

## 8. Case study: a FIDIC 1999 design-and-build road project

**Contract.** A design-and-build road upgrading project in East Africa (about 100 km) under the FIDIC 1999 Yellow Book:
- local law (common-law based);
- Time for Completion 1,099 days, with the Section 1 structures due within 550;
- Site access in sections, completed within 546 days (Sub-Clause 2.1 and the Appendix to Tender);
- delay damages of 0.05% of the Contract Price per day, capped at 10% (200 days);
- no Special Provision on concurrency, with the employer responsible for access and payment.

The impacted MS Project programme contains 167 activities. It completes on 24 July 2023, 453 days after the contractual date.

### 8.1 Programme fitness

The engine reproduces MS Project's dates for all 167 activities. That includes 10 task interruptions extracted from the schedule data. The programme, however, is weak as evidence:
- 37% of activities have no predecessor and 56% have no successor;
- 55% are held by hard constraints;
- 66% of links carry lags;
- 71% of activities exceed 44 days.

Completion is driven by a start-no-earlier-than date on the pavement sub-base, not by logic. Finish-no-earlier-than constraints make delay non-monotone, so a longer task can start earlier. None of the 10 interruptions affects completion. The analysis therefore uses a logic-only model, in which finish constraints become start constraints at the programme's dates and the level-of-effort activity is removed.

### 8.2 Back-propagation

A backward CPM pass from the contractual date gives the latest start of each activity. Start constraints later than this are slippages. A bisection on the target corrects for working calendars that the backward pass ignores.

The contractual date falls in the programme's rain-season non-working period. A reconstruction that finishes on time therefore finishes by 28 February 2022, leaving 58 days of terminal float.

**Sixteen slippages reproduce the 453-day overrun exactly:**
- 13 on employer access workfronts, led by the Section 2 pavement sub-base (+602 days);
- 3 on contractor production (aggregate production and precast works).

This is a minimum-change reconstruction, not the lost baseline.

### 8.3 Outcomes

- **Extension:** 449–453 days across the operators.
- **Paid days:** 449.
- **Shapley attribution:** the employer accounts for 452 of 453 days, of which the pavement access alone accounts for 341.
- **COVID-19:** the part of each access slip that falls inside the national lockdowns (122 days, neutral under Sub-Clause 8.4(d)) does not reduce the paid days. Each lockdown occurred while access was already late, and the terminal float absorbs the lockdown days on their own.
- **Notice gate (Sub-Clause 20.1):**
  - without a timely notice for the pavement access, the extension falls to 191 days and paid days to 0, and delay damages reach the 10% cap;
  - without notices for the structures, paid days fall to 381.

### 8.4 Explainable ensemble

The 1,500 variants randomise five things:
- responsibility for each workfront, weighted by how likely each one is to be an access problem;
- activity durations (×0.9–1.15);
- the size (±20%) and timing (±15 days) of each slip;
- whether notice was given (a 0–40% chance of a missed notice per claim);
- a hypothetical contractor productivity delay on the pavement chain (60% of variants, 10–240 days).

| Explained quantity | Test R² | Leading SHAP drivers |
|---|---|---|
| Extension (gateway) | 0.95 | Pavement access slip ≫ total employer slippage > duration scale |
| Paid days | 0.94 | Pavement access slip > employer slippage > contractor slippage |
| Days the contractor carries | 0.94 | Pavement access slip > contractor productivity delay > contractor slippage |
| Gap between English readings | 0.65 | Pavement access slip > contractor slippage > employer slippage |

The English readings differ by more than 14 days in 96% of variants. Predicting that from features alone reaches AUC 0.84. A contractor productivity delay on the pavement chain raises the contractor's exposure steadily, from a median of about 43 days at 0–20 days of contractor delay to about 200 days at 200–220 days. But it does not remove the employer's extension, which stays at a median of 375–416 days.

## 9. Discussion

**Law vs evidence.** On synthetic programmes the choice of English reading matters in about a third of cases. On the real project, once responsibility and notice are fixed, it moves the answer by only 4 days. The XAI layer makes the hierarchy explicit. What the outcome turns on is:
1. who controlled the access that drives completion;
2. whether notice was given;
3. only then, the concurrency doctrine.

**Which English reading.** The case test supports reading English law as a two-step test: first an actual-delay gateway, then Malmaison. It does not support a pure first-in-time rule or a theoretical as-planned impact. P4 shows this test has a cliff edge, which predicts that expert disagreement will cluster near the threshold where employer and contractor delays are of similar size.

**Programme quality.** Poorly linked programmes with many constraints can make a causal analysis meaningless: the real programme's interruptions had no effect on completion, and its constraints made delay non-monotone. This supports *City Inn*'s acceptance of common-sense fact-finding when a reliable critical path cannot be built, and the SCL Protocol's emphasis on properly linked programmes.

**Forms of contract.** Under NEC4's prospective assessment, time and money are paid together for concurrent periods that English common-law readings leave unpaid (P7). FIDIC 2017 without a Special Provision leaves a range, and the case study shows how wide that range can be.

## 10. Limitations

- **Stylised cases.** The case patterns are two-path reconstructions, and the gateway was formulated after reading the judgments.
- **City Inn.** Its facts come from a secondary source.
- **Clause readings.** The NEC4, FIDIC 2017 and JCT 2024 readings need checking against the forms.
- **Reconstruction.** The case-study baseline is a minimum-change reconstruction, not the original programme.
- **Responsibility.** Allocation follows contract terms and the contractor's report, not project records.
- **Lockdowns.** The lockdown dates are approximate.
- **Notices.** The notice gate treats Sub-Clause 20.1 as a strict condition precedent, without arguments on waiver or prevention.
- **No expert validation.** No expert elicitation was possible. Validation relies on the case test, formal properties, engine reproduction of MS Project dates, and synthetic experiments.

## 11. Conclusion

Concurrent delay cannot be settled by a model that searches for the fair apportionment. Treating doctrines as operators on one causal model makes the legal choice explicit and testable. One reading of English law is consistent with the decided cases. And explainable AI becomes a tool for locating where, and how much, that choice matters. On a real project, the decisive questions were evidential and procedural, namely access and notice, rather than doctrinal.

## Code and data availability

The code (`cdx` package, experiments, tests) is in the project repository. The case-study programme and contract are confidential and are excluded from the repository. Derived outputs are reproducible with `src/experiments/run_package5_xai.py` given the files.

## References (to complete and check)

- *Adyard Abu Dhabi v SD Marine Services* [2011] EWHC 848 (Comm).
- *City Inn Ltd v Shepherd Construction Ltd* [2010] CSIH 68; [2007] CSOH 190.
- *De Beers UK Ltd v Atos Origin IT Services UK Ltd* [2010] EWHC 3276 (TCC).
- *Henry Boot Construction (UK) Ltd v Malmaison Hotel (Manchester) Ltd* (1999) 70 Con LR 32.
- *North Midland Building Ltd v Cyden Homes Ltd* [2018] EWCA Civ 1744.
- *Saga Cruises BDF Ltd v Fincantieri SpA* [2016] EWHC 1875 (Comm).
- *Thomas Barnes & Sons plc v Blackburn with Darwen BC* [2022] EWHC 2598 (TCC).
- *Walter Lilly & Co Ltd v Mackay* [2012] EWHC 1773 (TCC).
- Society of Construction Law (2017) *Delay and Disruption Protocol*, 2nd ed.
- FIDIC (1999) *Conditions of Contract for Plant and Design-Build* (Yellow Book); FIDIC (2017) Yellow/Red Books.
- Huynh, H.T., Lucko, G. and Eid, M.S. (2023) "Game theory approach for concurrent delay analysis", *J. Constr. Eng. Manage.* 149(3); erratum 150(4).
- Rozemberczki, B. et al. (2022) "The Shapley value in machine learning", *IJCAI*.
- Keating on Construction Contracts (11th ed.), para 9-105 (as quoted in *Thomas Barnes* [118]).
- AACE International RP 29R-03, *Forensic Schedule Analysis*.
