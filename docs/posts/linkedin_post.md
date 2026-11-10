Same programme. Same delays. Up to seven different legal answers.

Concurrent delay comes out differently depending on the law and the contract:
- England (Malmaison, Walter Lilly, Thomas Barnes): time but no money.
- Scotland (City Inn): if no cause is dominant, the delay can be apportioned.
- A Cyden-style clause: concurrency can be contracted out.
- NEC4: prospective assessment pays for the time it grants.

So I stopped asking AI for "the fair split". There isn't one. Instead I model the programme once, as a causal model, and write each legal approach as an explicit rule on top of it.

What I found:

→ I tested each rule against stylised versions of five English cases, using facts and dates checked against the judgments. Only one rule reproduces all five: the employer's delay must cause actual delay to completion "as then scheduled" (Saga, para 251), and if it does, the contractor's concurrent delay doesn't reduce the extension. A strict first-in-time rule fails Thomas Barnes. A theoretical as-planned impact fails Adyard and Saga. (I wrote the rule after reading the judgments, so this shows consistency, not prediction.)

→ Under those English readings, the money comes out the same. The argument is about time.

→ The rule has a cliff edge. One extra day of employer delay can move the extension by the whole of the contractor's delay.

→ On 6,000 simulated programmes, the English readings disagree about 31% of the time. A model can flag the risky cases before the events are analysed together (AUC 0.85).

→ On a real FIDIC 1999 road programme, which I rebuilt backwards from the contract completion date, the doctrines differed by only 4 days. What decided the outcome was who controlled access to one workfront, and whether a 28-day notice was given. One missed notice moved delay damages to the 10% cap.

The XAI doesn't decide who is liable. It shows what the answer turns on.

Work in progress. Challenge welcome from delay experts and construction lawyers.

#ConstructionLaw #ConcurrentDelay #DelayAnalysis #ExplainableAI #FIDIC #SCLProtocol
