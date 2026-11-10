import itertools

import numpy as np
import pytest

from cdx import DelayEvent, DelayGame, Schedule, evaluate_all, ordered_contributions, shapley
from cdx.cases import CASES, COURT_OPERATOR
from cdx.doctrines import as_planned_impact, first_in_time, overlap_concurrency
from cdx.synth import random_game


def two_paths(a=100, b=100):
    return Schedule({"A": a, "B": b})


# --- schedule -------------------------------------------------------------------

def test_series_and_parallel_finish_and_float():
    s = Schedule({"X": 5, "Y": 7, "Z": 3}, [("X", "Y"), ("X", "Z")])
    assert s.planned_finish == 12
    assert s.total_float() == {"X": 0, "Y": 0, "Z": 4}
    assert s.finish({"Z": 6}) == 14


def test_cycle_rejected():
    with pytest.raises(ValueError):
        Schedule({"X": 1, "Y": 1}, [("X", "Y"), ("Y", "X")])


# --- game-theoretic axioms --------------------------------------------------------

@pytest.mark.parametrize("seed", range(20))
def test_shapley_efficiency_and_order_sums(seed):
    g = random_game(np.random.default_rng(seed))
    phi = shapley(list(g.all), g.v)
    assert sum(phi.values()) == pytest.approx(g.v(g.all) - g.v([]))
    for order in itertools.islice(itertools.permutations(g.all), 5):
        assert sum(ordered_contributions(order, g.v).values()) == pytest.approx(g.v(g.all))


def test_shapley_symmetry_and_null_player():
    s = two_paths()
    g = DelayGame(s, [DelayEvent("E", "E", "A", 10, 0), DelayEvent("C", "C", "B", 10, 0),
                      DelayEvent("N", "E", "A", 0, 0)])
    phi = shapley(list(g.all), g.v)
    assert phi["E"] == pytest.approx(phi["C"]) == pytest.approx(5)
    assert phi["N"] == pytest.approx(0)


# --- doctrine invariants -------------------------------------------------------------

@pytest.mark.parametrize("seed", range(200))
def test_outcome_bounds(seed):
    g = random_game(np.random.default_rng(seed))
    for name, o in evaluate_all(g).items():
        assert -1e-9 <= o.compensable <= o.eot + 1e-9, name
        assert o.eot <= o.net_delay + 1e-9, name


def test_doctrines_agree_without_overlap():
    g = DelayGame(two_paths(), [DelayEvent("E", "E", "A", 10, 10), DelayEvent("C", "C", "A", 10, 40)])
    eots = {k: o.eot for k, o in evaluate_all(g).items()}
    assert set(round(v, 9) for v in eots.values()) == {10.0}, eots


@pytest.mark.parametrize("seed", range(100))
def test_english_continuum_endpoints(seed):
    """Infinite concurrency tolerance collapses overlap_concurrency onto as_planned_impact."""
    g = random_game(np.random.default_rng(seed))
    assert overlap_concurrency(g, tolerance=1e9).eot == pytest.approx(as_planned_impact(g).eot)


def test_first_in_time_equals_overlap_when_windows_disjoint():
    g = DelayGame(two_paths(), [DelayEvent("C", "C", "B", 30, 0), DelayEvent("E", "E", "A", 10, 50)])
    assert first_in_time(g).eot == overlap_concurrency(g).eot == 0


# --- doctrinal fidelity --------------------------------------------------------------

@pytest.mark.parametrize("key", list(CASES))
def test_court_operator_reproduces_outcome(key):
    case = CASES[key]
    o = evaluate_all(case.game())[COURT_OPERATOR[key]]
    assert o.eot == pytest.approx(case.court_eot)
    if case.court_compensable is not None:
        assert o.compensable == pytest.approx(case.court_compensable)
