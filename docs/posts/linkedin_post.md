<!-- MEDIA: document post (carousel): outputs/package5/figures/linkedin_carousel.pdf
     Alternative: video post with outputs/v2/figures/law_timeline.mp4 or seven_answers.mp4.
     First comment: link to the Substack piece and the map: https://gavacharles.github.io/concurrent-delay-map/ -->

Can AI tell us who pays for concurrent delay? I think we've been asking it the wrong question. 👇

① The law never agreed on one answer.
1999 Malmaison: time for the contractor, even if it was also late.
2010 City Inn: Scotland apportions. 2012 Walter Lilly: England refuses.
2011–16 Adyard, Saga: the employer's delay must actually push completion out.
2018 Cyden: you can contract out.
2022 Thomas Barnes: 119 days of time, only 27 days of money.

② The new trend: use SHAP or Shapley values to "split" the delay. Train a model, attribute the slippage between employer and contractor, and call that the liability share. I did this too. Four problems:
– it measures against the average project, not the contract date;
– it gives one split where the law has several;
– it ignores which delay came first (the two-party Shapley split is just first-in-time averaged over both orders);
– it's checked against itself.

③ So use XAI to explain, not to apportion.
Model the programme once, as a causal model. Write each legal approach as an explicit rule. Then use SHAP to show what moves the answer.

What came out:
→ Only one rule reproduces five English cases (facts checked against the judgments): actual delay first, then no reduction for concurrency.
→ Money converges across the English readings. Time doesn't, and it has a cliff edge.
→ On a real FIDIC 1999 road project, the doctrines differed by 4 days. What decided it was who controlled site access and whether a 28-day notice was given.

Why XAI? Transparency for tribunals, rules an opponent can audit, and knowing where the evidence matters.

Try it yourself: move the delays and watch seven legal rules respond, then trace 25 years of case law 👉 gavacharles.github.io/concurrent-delay-map

Carousel below. Challenge welcome.

#ConstructionLaw #ConcurrentDelay #DelayAnalysis #ExplainableAI #SHAP #FIDIC
