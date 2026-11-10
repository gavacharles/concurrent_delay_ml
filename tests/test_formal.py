"""Property tests for the propositions in docs/formal_results.md (two-party games)."""
import numpy as np
import pytest

from cdx import DelayEvent, DelayGame, Schedule
from cdx.doctrines import (as_planned_impact, city_inn, contractual_exclusion, effective_cause,
                           first_in_time, nec4_prospective, overlap_concurrency, party_values,
                           symmetric_shapley, windows_analysis)

TOL = 1e-9


def two_party(rng):
    """One employer and one contractor event on parallel paths or one chain, with float."""
    series = rng.random() < 0.35
    fa, fb = int(rng.integers(0, 25)), int(rng.integers(0, 25))
    if series:
        s = Schedule({"A": 100 - fa, "B": 100, "Z": 200}, [("A", "B")])
    else:
        s = Schedule({"A": 200 - fa, "B": 200 - fb, "Z": 200})
    e_start, c_start = int(rng.integers(0, 120)), int(rng.integers(0, 120))
    if rng.random() < 0.15:
        c_start = e_start
    ev = [DelayEvent("E", "E", "A", float(rng.integers(0, 80)), e_start, float(rng.uniform(0.5, 2))),
          DelayEvent("C", "C", "B", float(rng.integers(0, 80)), c_start, float(rng.uniform(0.5, 2)))]
    return DelayGame(s, ev)


GAMES = [two_party(np.random.default_rng(s)) for s in range(1500)]
SUBADDITIVE = [g for g in GAMES if party_values(g).overlap >= -TOL]


def test_enough_cases_of_each_kind():
    assert len(SUBADDITIVE) > 500 and len(GAMES) - len(SUBADDITIVE) > 20


@pytest.mark.parametrize("op", [first_in_time, effective_cause, overlap_concurrency, as_planned_impact,
                                city_inn, contractual_exclusion])
def test_P1_money_is_the_but_for_delay(op):
    for g in SUBADDITIVE:
        assert op(g).compensable == pytest.approx(party_values(g).sole_E)


def test_P1_fails_without_subadditivity():
    """With float interaction (K < 0) the as-planned rule pays less than the but-for delay."""
    bad = [g for g in GAMES if party_values(g).overlap < -TOL
           and as_planned_impact(g).compensable < party_values(g).sole_E - TOL]
    assert bad


def test_P2_ordering():
    for g in SUBADDITIVE:
        pv = party_values(g)
        cy, fit, ec = contractual_exclusion(g).eot, first_in_time(g).eot, effective_cause(g).eot
        ov, ap, ci = overlap_concurrency(g).eot, as_planned_impact(g).eot, city_inn(g).eot
        assert cy == pytest.approx(pv.sole_E)
        assert cy <= fit + TOL <= ec + 2 * TOL <= ap + 3 * TOL
        assert fit <= ov + TOL <= ap + 2 * TOL
        assert pv.sole_E - TOL <= ci <= ap + TOL


def test_P2_gateway_and_overlap_are_incomparable():
    s = Schedule({"A": 200, "B": 200})
    saga_like = DelayGame(s, [DelayEvent("C", "C", "B", 14, -1), DelayEvent("E", "E", "A", 9, 0)])
    late_big = DelayGame(s, [DelayEvent("C", "C", "B", 10, 0), DelayEvent("E", "E", "A", 30, 50)])
    assert overlap_concurrency(saga_like).eot > effective_cause(saga_like).eot
    assert effective_cause(late_big).eot > overlap_concurrency(late_big).eot


def test_P3_shapley_is_strict_sequence_averaged_over_orders():
    for g in GAMES:
        pv = party_values(g)
        assert symmetric_shapley(g).eot == pytest.approx(min(max(0.5 * (pv.vE + pv.sole_E), 0), pv.vN))


@pytest.mark.parametrize("c", [5, 14, 40, 92])
def test_P4_gateway_cliff(c):
    s = Schedule({"A": 300, "B": 300})
    game = lambda e: DelayGame(s, [DelayEvent("C", "C", "B", c, 0), DelayEvent("E", "E", "A", e, 1)])
    assert effective_cause(game(c)).eot == 0
    assert effective_cause(game(c + 1)).eot == c + 1     # one extra day moves the answer by c + 1


def test_P5_windows_not_monotone_in_length():
    s = Schedule({"A": 200, "B": 200})
    g = DelayGame(s, [DelayEvent("C", "C", "B", 10, 25), DelayEvent("E", "E", "A", 10, 35)])
    assert windows_analysis(g, 20).eot == 10   # [20, 40): same window, concurrent
    assert windows_analysis(g, 30).eot == 0    # [0, 30) and [30, 60): sequential


def test_P6_windows_endpoints():
    for g in GAMES[:300]:
        assert windows_analysis(g, 1e6, offset=-1e5).eot == pytest.approx(as_planned_impact(g).eot)
        assert windows_analysis(g, 1e-3).eot == pytest.approx(first_in_time(g).eot)


def test_P7_nec4_pays_whatever_time_it_grants():
    for g in GAMES:
        o = nec4_prospective(g)
        assert o.compensable == pytest.approx(o.eot)
        assert o.eot == pytest.approx(first_in_time(g).eot)


def test_neutral_event_gives_time_not_money():
    s = Schedule({"A": 200, "B": 200})
    g = DelayGame(s, [DelayEvent("N", "N", "A", 20, 0), DelayEvent("E", "E", "B", 10, 0)])
    for op in (effective_cause, first_in_time, overlap_concurrency, as_planned_impact, city_inn):
        o = op(g)
        assert o.eot == pytest.approx(20)
        assert o.compensable == pytest.approx(0)   # employer's 10 days are wholly inside the neutral 20


def test_neutral_with_employer_beyond_it_pays_the_excess():
    s = Schedule({"A": 200, "B": 200})
    g = DelayGame(s, [DelayEvent("N", "N", "A", 20, 0), DelayEvent("E", "E", "B", 35, 0)])
    o = effective_cause(g)
    assert o.eot == pytest.approx(35) and o.compensable == pytest.approx(15)


def test_notice_gate_moves_barred_events_to_contractor():
    from cdx.notices import apply_notice_gate
    s = Schedule({"A": 200, "B": 200})
    ev = [DelayEvent("E1", "E", "A", 30, 0), DelayEvent("C1", "C", "B", 10, 0)]
    g = DelayGame(s, apply_notice_gate(ev, ["E1"]))
    assert effective_cause(g).eot == 0 and effective_cause(g).ld_days == 30
