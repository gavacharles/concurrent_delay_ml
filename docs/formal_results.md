# Formal results

Setting: one employer event *E* and one contractor event *C* (or each party's events treated as one group). The value function *v* gives delay to completion against the as-planned date. It is monotone: adding events never shortens the project in the logic-only model (see note 1).

Notation:
- vE = v({E}), vC = v({C}), vN = v({E, C})
- sole_E = vN − vC (the but-for delay caused by the employer)
- K = vE + vC − vN (the concurrent days: delay either event alone would have caused)
- K ≥ 0 means *v* is subadditive. That always holds when E and C sit on parallel paths. It can fail on one chain with float, where neither event alone uses up the float but the two together do.

Rules: strict sequence (S), actual-delay gateway (G), overlapping windows (O), as-planned impact (A), City Inn (CI), contractual exclusion (X), NEC4 (N), symmetric Shapley (φ). Money for S, G, O, A, CI and X is min(sole_E, EOT).

Each proposition has a matching property test in `tests/test_formal.py`.

---

**P1 (Money convergence).** If K ≥ 0, every English, SCL, City Inn and exclusion rule pays exactly sole_E.

*Proof.* Each rule's extension satisfies EOT ≥ sole_E when K ≥ 0:
- S, G and O give either vE or sole_E (or 0, which only happens when sole_E = 0), and vE ≥ sole_E ⇔ K ≥ 0.
- A gives min(vE, vN) = vE.
- CI gives a value between sole_E and vE.
- X gives sole_E.

So money = min(sole_E, EOT) = sole_E. ∎

*Interpretation:* across the English readings, the dispute is about time, not money. The Thomas Barnes result (119 days of extension, 27 days paid) fits this. *Failure case:* when K < 0 (float interaction), the as-planned rule can pay less than the but-for delay (test `test_P1_fails_without_subadditivity`).

**P2 (Ordering).** If K ≥ 0, then:
- X = sole_E ≤ S ≤ G ≤ A
- S ≤ O ≤ A
- sole_E ≤ CI ≤ A

G and O cannot be ordered against each other.

*Proof.*
- **S ≤ G:** when E comes first or the starts are equal, both give vE (G gives 0 only when vE = 0). When C comes first, S gives sole_E, and G gives vE if sole_E > 0 and 0 otherwise. Both are ≥ sole_E.
- **G ≤ A:** G gives either vE or 0.
- **S ≤ O:** O groups more events together than S, and grouping replaces sole_E with vE ≥ sole_E.
- **G and O incomparable:**
  - Saga-type facts (C first, E inside C's window, vE ≤ vC): O = vE > 0 = G.
  - E later than C, outside its window, with vE > vC: G = vE > sole_E = O. ∎

**P3 (Shapley as averaged chronology).** With distinct start days, the two-party Shapley value is the strict-sequence extension averaged over both possible orders: φ_E = ½(vE + sole_E).

*Interpretation:* the "neutral" game-theoretic split is not neutral between legal systems. It is a first-in-time rule with no information about which event came first.

**P4 (Cliff edge).** Take C first, E later on a parallel path, and C causes c days of delay. Under G, the extension is 0 when E's delay ≤ c, and E's delay when it is ≥ c + 1. One extra day of employer delay moves the extension by c + 1 days.

*Interpretation:* the actual-delay gateway, which is the only rule that reproduces all five verified English cases, has a built-in discontinuity. Small measurement differences near the threshold produce large swings in time. That's a testable claim about where expert disagreement should cluster.

**P5 (Windows are not monotone).** With fixed calendar windows, a shorter window can give more time.

*Counterexample.* C starts on day 25 and E on day 35, with equal 10-day impacts on parallel paths. With 20-day windows both fall in the window [20, 40), so they are concurrent and EOT = 10. With 30-day windows they fall in [0, 30) and [30, 60), so they are sequential and EOT = 0.

*Interpretation:* in a windows analysis, the extension depends on where the window boundaries fall, not just on how long the windows are.

**P6 (Continuum).** Windows analysis converges to the strict sequence as the window length goes to 0 (distinct start days), and to the as-planned impact when one window covers all events. The English readings are points along this axis.

**P7 (NEC4 pays its time).** Under the prospective NEC4 reading, money always equals time, and both equal the strict-sequence extension. So NEC4 pays for concurrent periods that every English common-law reading leaves unpaid. That follows from the prospective assessment method itself.

---

Note 1. MS Project "finish no earlier than" constraints make *v* non-monotone: a longer task can start earlier. Real programmes are analysed in logic-only mode, where each such constraint becomes "start no earlier than" at the baseline start. See `cdx.network.logic_only`.
