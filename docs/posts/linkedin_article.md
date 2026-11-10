<!--
LINKEDIN ARTICLE
Cover image: outputs/v2/figures/covers/wide_1920x1080.png
Title (max 150 chars): One Schedule, Many Laws: Concurrent Delay, SHAP and What Explainable AI Should Really Do
Image placements are marked [IMAGE: ...]. LinkedIn articles accept images and embedded links, but not video
uploads in the body; link to the videos instead, or use their stills.
-->

# One Schedule, Many Laws: Concurrent Delay, SHAP and What Explainable AI Should Really Do

*Twenty-five years of case law, a fashionable AI technique, and a real road project show why the question we ask the machine matters more than the machine.*

## The same delay, seven different answers

Imagine a simple project with two parallel streams of work. The contractor's façade package slips by forty days. Ten days after that slip begins, the employer issues a variation that holds up the services fit-out by fifty-five days. The project finishes fifty-five days late. How much extra time should the contractor receive, and how much of its prolongation cost can it recover?

Most people who work on construction disputes will recognise the honest answer: it depends. In England the contractor would usually receive the full fifty-five days, but no money for the period in which its own delay was running alongside the employer's. A Scottish tribunal following *City Inn* could apportion the shared days and arrive at something nearer thirty-five. A strict "first in time" reading would credit the employer only with the fifteen days its variation added on top of the contractor's own slippage. A contract containing a clause of the kind upheld in *North Midland v Cyden Homes* would also give fifteen days, but for a quite different reason. An NEC4 prospective assessment would also give fifteen days, but would pay for every one of them.

[IMAGE: outputs/v2/figures/seven_answers_still.png. Caption: "One set of facts, seven legal answers." Animated version: https://gavacharles.github.io/concurrent-delay-map/]

None of these answers is sloppy. Each reflects a deliberate legal choice about who should carry the consequences when two causes overlap. That observation is the starting point for this article, because it changes what we should expect from artificial intelligence in delay disputes.

## How the law got here

### 1999 to 2009: time, not money

The modern English position begins with *Henry Boot v Malmaison* in 1999, where Dyson J accepted that a contractor is entitled to an extension for the period of delay caused by a relevant event, even if a contractor-caused delay was operating at the same time. Two years later *Royal Brompton Hospital v Hammond* added a qualification that later cases would sharpen: an employer event that has no effect on the completion date earns no extension at all. In 2002 the Society of Construction Law published the first edition of its Delay and Disruption Protocol. It took a broad view of concurrency, treating delays whose effects are felt at the same time as concurrent.

### 2010 to 2016: actual delay against apportionment

The decade that followed produced the sharpest divergence. In Scotland the Inner House decided *City Inn v Shepherd Construction* in 2010. The majority held that delay is a question of fact to be decided with common sense, that a critical path analysis is helpful but not essential, and that where no single cause is dominant the delay may be apportioned between the competing causes on a fair and reasonable basis.

England went the other way. In *Walter Lilly v Mackay* (2012), Akenhead J described *City Inn* as "inapplicable within this jurisdiction" and confirmed that a contractor whose delay has an effective employer cause receives a full extension. *De Beers v Atos* (2010) restated the companion rule that time does not bring money where the contractor would have suffered the same loss anyway. Then *Adyard v SD Marine* (2011) and *Saga Cruises v Fincantieri* (2016) tightened the test considerably. Concurrency, Hamblen J said in *Adyard*, exists only if both events in fact cause delay to the progress of the works and their delaying effect is felt at the same time. *Saga* required "a concurrency actually affecting the completion date as then scheduled". Notional or theoretical delay was not enough.

### 2017 to 2024: contracting out, and separating time from money

The standard forms then diverged in their own way. FIDIC's 2017 suite asks the parties to set their own concurrency rules in the Special Provisions. NEC4 assesses compensation events prospectively, so time and money travel together. The JCT forms, including the 2024 edition, remain silent, which leaves the question to bespoke amendment. The Court of Appeal's decision in *North Midland v Cyden Homes* (2018) confirmed that such an amendment works: a clause stating that concurrent delay earns no extension is enforceable, because the prevention principle can be displaced by agreement.

Most recently, *Thomas Barnes v Blackburn with Darwen* (2022) applied the settled English approach to concurrent roof-covering and steelwork delays. The contractor received 119 days of extension but recovered prolongation for only 27 days.

[IMAGE: outputs/v2/figures/law_timeline.png. Caption: "How the law on concurrent delay evolved, 1999–2024." Interactive version: https://gavacharles.github.io/concurrent-delay-map/#case-law]

The lesson of those twenty-five years is not that the law is confused. It is that the law converged on *different* answers, each one a reasoned allocation of risk.

## How delay is analysed today, and where SHAP came in

### The established toolkit

Forensic delay analysis rests on a familiar set of methods: as-planned versus as-built comparisons, impacted as-planned, time impact analysis, windows analysis and collapsed as-built. The SCL Protocol describes them, and tribunals weigh the choice an expert makes among them; *Thomas Barnes* itself observed that a manifestly inappropriate method can affect the weight given to the evidence. Each of these methods answers a causation question about the programme. None of them, on its own, tells you how the law should allocate delay that two parties caused together.

### The new wave: Shapley values and SHAP

Over the last few years researchers have turned to cooperative game theory and machine learning to fill that gap. The appeal is easy to see. The Shapley value, a classic idea in fair division, gives each player its average marginal contribution across every order in which the players could have joined. Huynh, Lucko and Eid applied it to concurrent delay in the *Journal of Construction Engineering and Management* in 2023. SHAP is the explainable-AI version of the same idea. You train a model to predict how late a project finishes from the employer's and the contractor's delays, and SHAP splits each prediction between them. My own first attempt at this research did exactly that, and the results looked persuasive: elegant mathematics, attributions that add up, clean charts.

### Why reading SHAP as a liability share goes wrong

The difficulty is not the technique. It is the question being put to it. Four problems emerged when I examined the approach closely.

The first is the baseline. SHAP measures each factor against the average scenario in the training data, whereas legal causation asks what would have happened *but for* the event, measured against the planned or contractual completion date. In my first version this mismatch produced a balanced scenario that allocated every day of liability to the contractor, and the result flipped to the employer when the programme changed only slightly.

The second is that a Shapley split is a single answer. The law, as we have seen, has several. A single split either quietly adopts one legal approach or invents an allocation that no court applies.

The third is order. Shapley values average over every possible sequence of events, while English law cares very much about which delay came first and whether the later one actually added delay. It is possible to prove that, for two parties, the Shapley split is simply a first-in-time rule averaged over both possible orders. That is a legal position, and not one any English court has adopted.

The fourth is validation. These methods are typically checked against themselves, or against other heuristics scored as if the Shapley answer were the truth.

None of this makes SHAP a poor tool. It makes it the wrong tool for apportioning liability.

## Explainable AI that explains

### Separating causation from law

The approach I have developed separates the two questions that SHAP-based apportionment blends together. Causation is treated as an engineering question. The critical path network becomes a causal model in which delay events are interventions and the outcome is delay to completion beyond the contractual date. The model handles real MS Project programmes, including start-to-start and finish-to-finish links, lags, constraints and working calendars, and reproduces their dates exactly.

Attribution is treated as a legal question. Each approach to concurrency is written as an explicit rule that sits on top of the causal model and converts its outputs into time and money: the English actual-delay test, strict sequence, overlapping windows, as-planned impact, *City Inn* apportionment, contractual exclusion and NEC4's prospective assessment. Neutral events, such as an epidemic under FIDIC 1999 Sub-Clause 8.4(d), give time without money. Notice conditions, such as the 28-day requirement in Sub-Clause 20.1, can remove an entitlement altogether.

### Why explainability matters here

Explainable AI then returns to what it does best: showing which facts and which legal choices move the answer. That matters to practitioners for four reasons. Tribunals can see why a number came out as it did, not just the number. Because every rule is written down and tested, an opponent can challenge the rule rather than a black box. Employers and contractors can see, before they sign, which programmes are exposed to the choice of law or to a drafting decision. And once a dispute begins, the parties know which facts actually decide it, which tells them where to spend their evidence budget.

## What the evidence shows

### One rule fits the English cases

I rebuilt stylised versions of five English decisions, taking the dates and figures from the judgments themselves: *Malmaison*, *Adyard*, *Saga Cruises*, *Walter Lilly* and *Thomas Barnes*. Only one rule reproduces all five outcomes. The employer's delay must cause actual delay to completion as then scheduled, and if it does, the contractor's concurrent delay does not reduce the extension. A strict first-in-time rule gives *Thomas Barnes* 27 days of extension instead of 119. A theoretical as-planned approach gives *Adyard* 124 days and *Saga* nine, where the courts awarded nothing. In fairness to the reader, I formulated the winning rule after reading those judgments, so the exercise demonstrates consistency rather than prediction.

[IMAGE: outputs/v2/figures/fidelity_matrix.png. Caption: "Which rule reproduces which decision."]

### Two results that can be proved

Two properties follow from the rules and can be proved formally. First, under every English reading the money comes out the same; the disagreement between those readings is entirely about time. Second, the actual-delay test has a cliff edge. Where the contractor's delay came first, an employer delay one day shorter than the contractor's earns nothing, while one day longer earns its entire length. Small measurement differences near that threshold can therefore swing an extension dramatically, which is a useful thing for an expert to know before cross-examination.

[IMAGE: outputs/v2/figures/cliff_edge_still.png. Caption: "One more day of employer delay can be worth the whole of the contractor's delay in extra time."]

### How often the choice of law matters

Across six thousand simulated programmes, the English readings disagree about thirty-one per cent of the time. A model that uses only information available before the events are analysed together can flag those cases in advance, with an area under the curve of 0.85. SHAP, now in its proper role, explains why: the amount of overlap between the delay windows, which delay came first, and whether the two delays sit on parallel paths or on the same chain of work.

[IMAGE: outputs/v2/figures/synthetic_summary.png]

### A real road project

The most instructive test was a real FIDIC 1999 design-and-build road contract that finished 453 days late. Its impacted MS Project programme proved weak as evidence. More than half its activities were held in place by hard dates rather than logic, and its own recorded interruptions had no effect on completion at all. I therefore rebuilt it backwards from the contractual completion date, which yields the smallest set of slipped workfronts that explains the overrun exactly: thirteen on employer site access and three on contractor production.

On that evidence the competing doctrines differed by only four days. An explainable model trained on 1,500 variations of the unknowns, with an R² of about 0.95, showed what actually decides the case. The first factor is who controlled access to a single pavement workfront, which drives three-quarters of the overrun. The second is whether a 28-day notice was given; without it, the paid days fall to zero and delay damages reach the contractual cap of ten per cent of the price. Only after those two questions does the choice of concurrency doctrine come into play. COVID-19 lockdowns, which give time but no money under the 1999 form, did not reduce the paid days, because each lockdown arrived while site access was already late.

[IMAGE (anonymised; confirm you may use the project first): outputs/package5/figures/p5_notice.png. Caption: "On a real project, the notice condition outweighed the concurrency rule."]

The same tool, SHAP, ends up answering a different question. It does not tell you who should pay. It tells you what the answer turns on.

## What this is, and what it is not

This is not a machine for deciding disputes. Legal causation involves judgement about what counts as dominant, how culpable a party was and how a clause should be construed, and the contract always governs. What the framework offers is a way of turning those judgements into visible, testable parameters and of showing how far each one moves the outcome. It is a tool for experts and tribunals, not a substitute for them.

## Explore it, and challenge it

The interactive [Concurrent Delay Map](https://gavacharles.github.io/concurrent-delay-map/) lets you move the delays and watch each legal rule respond, and its [case-law view](https://gavacharles.github.io/concurrent-delay-map/#case-law) traces the decisions discussed here, with each one marked by how carefully it has been checked.

I would particularly welcome views from delay experts and construction lawyers on three questions. Is the actual-delay test the right reading of English law after *Thomas Barnes*? Have you seen SHAP or Shapley-based splits relied on in an expert report or before a tribunal? And how should a tribunal approach a programme whose logic cannot carry a causal analysis?

*This is ongoing research and not legal advice. The real project is anonymised. Case citations should be checked against the reported judgments.*

*Charles Gava*
