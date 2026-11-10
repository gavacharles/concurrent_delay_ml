# One Schedule, Many Laws

*Why "AI for concurrent delay" should stop looking for the fair answer, and what it found when it did*

---

Take a simple project. Two parallel streams of work run to completion. The contractor's façade package slips by 40 days. Ten days after that slip begins, the employer issues a variation that holds up the services fit-out by 55 days. The project finishes 55 days late.

How much extra time does the contractor get, and how much of the prolongation cost can it recover? That depends on where you are and what you signed:

- **Strict first in time:** 15 days. The employer is credited only with the delay it added on top of a position the contractor had already lost.
- **Scotland (City Inn):** around 35 days. With no dominant cause, the concurrent days can be apportioned.
- **England:** 55 days of time but no money for the concurrent period, as long as the employer's delay actually pushed completion out.
- **A Cyden-style clause:** 15 days again, for a different reason.

Same facts, several defensible answers. That's not sloppy analysis. It's the law.

## Stop asking AI for the fair split

Much current work on AI for delay analysis trains a model and then uses Shapley values or SHAP to split the delay between the parties. My earlier version did the same, and it had two problems.

**First, it asked the wrong question.** There is no single fair split. English law, Scots law, the SCL Protocol and the standard forms have each made a *normative choice* about overlapping causes. A model that outputs one split either quietly picks one of those choices or invents one no court applies.

**Second, the baseline was wrong.** SHAP measures against the *average* scenario. Legal causation asks what would have happened *but for* the event, against the planned or contractual completion date.

## Model the programme once, then write the law as rules

1. **Causation is engineering.** The critical path network becomes a causal model. Delay events are interventions, and the outcome is delay to completion beyond the contract date.
2. **Attribution is law.** Each legal approach is an explicit rule that turns those causal facts into time and money. The rules cover a strict sequence, an actual-delay test, overlapping windows, as-planned impact, City Inn apportionment, contractual exclusion and NEC4's prospective assessment. They also cover neutral events such as epidemics, which give time but no money, and notice conditions that can bar a claim altogether.

None of these rules claims to be *the* answer. The framework makes the choice explicit and testable.

## Testing the rules against the cases

I rebuilt stylised versions of five English cases, taking the dates and figures from the judgments themselves: *Malmaison*, *Adyard*, *Saga Cruises*, *Walter Lilly* and *Thomas Barnes*. Then I asked each rule to reproduce what the court decided.

Reading the judgments corrected me.

- **Adyard** (para 279) says "there is only concurrency if both events in fact cause delay ... and the delaying effect of the two events is felt at the same time".
- **Saga** (para 251) requires "a concurrency actually affecting the completion date as then scheduled".
- **Both** reject notional or theoretical delay.
- **Thomas Barnes** granted 119 days' extension but only 27 days' prolongation ([148], [157]). The contractor's roof-coverings delay began first. The employer's steel problem followed three weeks later and ran longer.

Only one rule reproduces all five cases. **The employer's delay must cause actual delay to completion as then scheduled. If it does, the contractor's concurrent delay doesn't reduce the extension.** The other rules fail in clear ways:
- a strict first-in-time rule gives *Thomas Barnes* 27 days instead of 119;
- a theoretical "as-planned impact" rule gives *Adyard* 124 days and *Saga* 9, where the courts gave nothing.

I wrote the winning rule after reading the judgments, so this shows consistency with them, not prediction.

Three properties follow, and they can be proved:
1. **The money comes out the same under every English reading.** Under these readings the argument is about time.
2. **The actual-delay test has a cliff edge.** If the contractor's delay came first, an employer delay one day shorter than the contractor's earns nothing, and one day longer earns its full length.
3. **Windows analysis isn't monotone.** Shorter windows can give *more* time, depending on where the window boundaries fall.

## When does the law matter?

This is where explainable AI earns its place: not deciding liability, but showing what the answer turns on.

- **Simulated programmes.** Across 6,000 of them, the English readings disagree about 31% of the time. A model using only information available before the events are analysed together flags those cases with an AUC of 0.85.
- **A real project.** The real test was a FIDIC 1999 design-and-build road contract with a 453-day overrun. Its impacted MS Project programme was poor as evidence: over half the activities were held by hard dates, and many had no logic at all. Its own interruptions didn't affect completion. So I rebuilt it *backwards* from the contract completion date. That gives the smallest set of slipped workfronts that explains the overrun exactly: 13 on employer site access and 3 on contractor production.

On that evidence, **the doctrines differed by only 4 days.** An explainable model over 1,500 variations of the unknowns, with an R² of about 0.95, showed what actually decides the case:

1. **Who controlled access to one pavement workfront.** It drives three-quarters of the overrun.
2. **Whether a 28-day notice was given.** Without it, the paid days fall to zero and delay damages reach the 10% cap.
3. **Only then, which concurrency rule applies.**

COVID lockdowns, which give time but no money under FIDIC 1999, didn't reduce the paid days. Each lockdown came while site access was already late.

## What this is not

It isn't a machine that decides disputes. Legal causation involves judgement: what counts as "dominant", or how culpable a party was. The framework turns those judgements into visible parameters and shows how much each one moves the answer. The contract governs everything, and this is a tool for experts, not a replacement for them.

## Where this sits

Shapley values have been applied to concurrent delay before (Huynh, Lucko and Eid, *JCEM*, 2023). As far as I can find, nobody has encoded the competing doctrines as separate rules on one causal model, tested them against decided cases, and used explainable AI to map where the law matters on a real programme. If you know of work that does, I'd like to hear about it.

**For delay experts and construction lawyers:**
- Is the actual-delay test the right reading of English law after *Thomas Barnes*?
- How would you formalise "dominant cause" in *City Inn*?
- How should a tribunal treat a programme whose logic can't carry a causal analysis?

---

*Ongoing research, not legal advice. The real project is anonymised. Case citations should be checked against the reported judgments.*
