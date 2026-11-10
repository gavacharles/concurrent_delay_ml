# One Schedule, Many Laws

*Concurrent delay, the rise of SHAP, and why explainable AI should explain rather than apportion*

<!-- HERO: outputs/v2/figures/seven_answers.mp4 (or seven_answers_still.png). Caption: "One set of facts, seven legal answers." -->

---

Take a simple project. Two parallel streams of work run to completion. The contractor's façade package slips by 40 days. Ten days after that slip begins, the employer issues a variation that holds up the services fit-out by 55 days. The project finishes 55 days late.

How much extra time does the contractor get, and how much of the prolongation cost can it recover? It depends on where you are and what you signed:

- **England:** 55 days of time but no money for the concurrent period, as long as the employer's delay actually pushed completion out.
- **Scotland (City Inn):** around 35 days. With no dominant cause, the concurrent days can be apportioned.
- **Strict first in time:** 15 days. The employer is credited only with what it added on top.
- **A Cyden-style clause:** 15 days, because concurrent delay earns nothing.

Same facts, several defensible answers. That isn't sloppy analysis. The law itself gives different answers. This piece covers three things:
1. how the law got here;
2. how researchers have started using SHAP and Shapley values on the problem;
3. why explainable AI is more useful when it *explains the decision* than when it *makes the split*.

## 1. How the law got here

<!-- FIGURE: outputs/v2/figures/law_timeline.png (video: law_timeline.mp4). Link: https://gavacharles.github.io/concurrent-delay-map/#case-law -->

**1999–2009: time, not money.** *Henry Boot v Malmaison* (1999) gave the contractor an extension for the period of delay caused by the employer's event, even though its own delay was running at the same time. *Royal Brompton v Hammond* (2001) added a condition: an employer event with no effect on the completion date earns nothing. The first SCL Delay and Disruption Protocol (2002) took a broad view of concurrency, covering delays whose effects are felt at the same time.

**2010–2016: actual delay against apportionment.** Scotland and England split.
- *City Inn v Shepherd* (2010): the Inner House held that where no cause is dominant, the delay may be apportioned fairly and reasonably.
- *Walter Lilly v Mackay* (2012): called City Inn "inapplicable within this jurisdiction".
- *De Beers v Atos* (2010): restated time without money.
- *Adyard v SD Marine* (2011) and *Saga Cruises v Fincantieri* (2016): tightened the English test. Both causes must *in fact* delay completion, felt at the same time, and notional delay doesn't count. Saga's phrase is "a concurrency actually affecting the completion date as then scheduled".

**2017–2024: contracting out, time against money.** The standard forms divided:
- FIDIC 2017 (Sub-Clause 8.5) leaves concurrency to the parties' Special Provisions;
- NEC4 assesses compensation events prospectively, with time and money together;
- JCT 2024 stays silent.

In the courts:
- *North Midland v Cyden Homes* (2018): upheld a clause that excludes concurrent delay altogether.
- *Thomas Barnes v Blackburn with Darwen* (2022): the most recent English authority. It awarded 119 days of extension but only 27 days of prolongation money.

The law didn't converge on one fair split. It settled on *different* answers, each a deliberate choice about who carries overlapping delay.

## 2. How delay is analysed, and where SHAP came in

Forensic delay analysis rests on established methods: as-planned vs as-built, impacted as-planned, time impact analysis, windows, and collapsed as-built. The SCL Protocol describes them, and tribunals weigh the expert's choice of method (*Thomas Barnes*, para 110). Each method answers a causation question about the programme. None of them says, on its own, how the law allocates overlapping delay.

Recently, researchers have turned to game theory and machine learning:
- **Shapley values:** a fair-division idea from cooperative game theory. Each player gets its average marginal contribution across every order in which the players could join. Huynh, Lucko and Eid (*JCEM*, 2023) apply it to concurrent delay.
- **SHAP:** the explainable-AI version of the same idea. You train a model to predict project slippage from employer and contractor delays, then use SHAP to split each prediction between them. My own first version of this study did exactly that.

It looks rigorous. The maths is elegant, the attributions add up, and the chart is persuasive. But reading SHAP or Shapley values directly as liability shares runs into four problems:

1. **Wrong baseline.** SHAP measures each factor against the *average* scenario in the data. Legal causation asks what would have happened *but for* the event, against the planned or contractual completion date. In my first version this produced a balanced 20/20 scenario that put 100% of liability on the contractor, and the result flipped to the employer when the network changed slightly.
2. **One split where the law has several.** A Shapley split is one answer. English law, Scots law and the standard forms have each chosen differently, so a single split either quietly picks one of those choices or invents one no court applies.
3. **No sense of order.** Shapley averages over every order in which events could happen. The English cases care very much about which delay came first and whether the later one *actually* added delay. In fact you can prove that the two-party Shapley split is simply a first-in-time rule, averaged over both possible orders.
4. **Circular validation.** The method is usually checked against itself, or against other heuristics scored as if Shapley were the truth.

None of this makes SHAP a bad tool. It makes it the wrong tool *for that question*.

## 3. Explainable AI that explains instead

Instead, I separate the two questions that the SHAP-apportionment approach blends together:

- **Causation is engineering.** The critical path network becomes a causal model. Delay events are interventions, and the outcome is delay to completion beyond the contract date. It handles real MS Project programmes, and reproduces their dates exactly.
- **Attribution is law.** Each legal approach is an explicit rule on top of that model: an actual-delay test, strict sequence, overlapping windows, as-planned impact, City Inn apportionment, contractual exclusion, NEC4's prospective assessment, neutral events such as epidemics (time but no money), and notice conditions that can bar a claim altogether.

Then explainable AI does what it is good at. It explains which facts and which legal choices move the answer.

**Why bother with XAI at all?** Because it gives decision makers four things:
- **Transparency:** a tribunal can see why a number came out as it did, not just the number.
- **Auditability:** every rule is written down and tested, so an opponent can challenge the rule rather than the black box.
- **Risk before the dispute:** it shows which programmes are exposed to the choice of law, or to drafting, before anyone signs.
- **Evidence priorities:** it tells the parties which facts actually decide the case, so that's where the evidence effort goes.

## 4. What it found

**Testing the rules against the cases.** I rebuilt stylised versions of five English cases, taking the dates and figures from the judgments: *Malmaison*, *Adyard*, *Saga Cruises*, *Walter Lilly* and *Thomas Barnes*. Only one rule reproduces all five: **the employer's delay must cause actual delay to completion as then scheduled, and if it does, the contractor's concurrent delay doesn't reduce the extension.** The other rules fail in clear ways:
- a strict first-in-time rule gives *Thomas Barnes* 27 days instead of 119;
- a theoretical as-planned rule gives *Adyard* 124 days and *Saga* 9, where the courts gave nothing.

I wrote the winning rule after reading the judgments, so this is consistency, not prediction.

<!-- FIGURE: outputs/v2/figures/fidelity_matrix.png -->

**Two results you can prove:**
- **Money converges, time doesn't.** Under the English readings the money comes out the same. The argument is about time.
- **The actual-delay test has a cliff edge.** If the contractor's delay came first, an employer delay one day shorter than the contractor's earns nothing, and one day longer earns its full length.

<!-- FIGURES: outputs/v2/figures/money_vs_time.png, then cliff_edge.mp4 (or cliff_edge_still.png) -->

**When does the law matter?** Across 6,000 simulated programmes, the English readings disagree about 31% of the time. A model using only information available before the events are analysed together flags those cases with an AUC of 0.85. SHAP then shows why: how much the delay windows overlap, which came first, and whether the two delays sit on parallel paths or the same chain.

<!-- FIGURE: outputs/v2/figures/synthetic_summary.png -->

**A real project.** I tested it on a FIDIC 1999 design-and-build road contract that finished 453 days late.
- **The programme was poor as evidence.** Over half its activities were held by hard dates rather than logic, and its own interruptions didn't affect completion.
- **So I rebuilt it backwards** from the contract completion date. That gives the smallest set of slipped workfronts that explains the overrun exactly: 13 on employer site access and 3 on contractor production.
- **The doctrines then differed by only 4 days.**
- **An explainable model over 1,500 variations** of the unknowns (R² about 0.95) showed what actually decides the case:
  1. who controlled access to one pavement workfront, which drives three-quarters of the overrun;
  2. whether a 28-day notice was given. Without it, the paid days fall to zero and delay damages reach the 10% cap;
  3. only then, which concurrency rule applies.

<!-- FIGURES (anonymised; confirm you may use the project first): outputs/package5/figures/backpropagation.mp4, p5_notice.png, p5_drivers.png -->

The same tool, SHAP, now answers a different question. It doesn't tell you who should pay. It tells you what the answer turns on.

## What this is not

It isn't a machine that decides disputes. Legal causation involves judgement: what counts as "dominant", or how culpable a party was. The framework turns those judgements into visible parameters and shows how much each one moves the answer. The contract governs everything. It's a tool for experts, not a replacement for them.

**Explore it yourself:** the [Concurrent Delay Map](https://gavacharles.github.io/concurrent-delay-map/) lets you move the delays and watch each rule respond, and trace the case law since 1999 ([case-law view](https://gavacharles.github.io/concurrent-delay-map/#case-law)).

**For delay experts and construction lawyers:**
- Is the actual-delay test the right reading of English law after *Thomas Barnes*?
- Have you seen SHAP or Shapley splits used in a real expert report or a tribunal?
- How should a tribunal treat a programme whose logic can't carry a causal analysis?

---

*Ongoing research, not legal advice. The real project is anonymised. Case citations should be checked against the reported judgments.*
