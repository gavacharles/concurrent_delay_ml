"""Legal doctrines on concurrent delay as attribution operators on a DelayGame.

Every operator returns an Outcome with
  eot          -- extension of time (days) granted to the contractor
  compensable  -- days of prolongation for which the contractor recovers money
  ld_days      -- net delay the contractor bears (liquidated damages exposure)

Party-level quantities (E = employer events, C = contractor events, N = E u C):
  vE, vC, vN  -- delay to completion from E alone, C alone, both
  sole_E      -- vN - vC : delay that would not have happened but for E
  overlap     -- vE + vC - vN : days either party alone would have caused ("concurrent" days)

These are modelling choices about contested law. Each operator documents the
reading of authority it encodes; see docs/study_redesign_v2.md section 2.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Callable, Dict, List, Sequence

from .game import CONTRACTOR, EMPLOYER, EXCUSABLE, DelayEvent, DelayGame


@dataclass(frozen=True)
class Outcome:
    doctrine: str
    eot: float
    compensable: float
    net_delay: float

    @property
    def ld_days(self) -> float:
        return self.net_delay - self.eot


@dataclass(frozen=True)
class PartyValues:
    vE: float               # excusable events (employer + neutral) alone
    vC: float               # contractor events alone
    vN: float               # all events
    sole_money: Optional[float] = None  # but-for delay of the employer's own events (money)

    @property
    def sole_E(self) -> float:
        return self.vN - self.vC

    @property
    def sole_C(self) -> float:
        return self.vN - self.vE

    @property
    def overlap(self) -> float:
        return self.vE + self.vC - self.vN


def party_values(game: DelayGame) -> PartyValues:
    """'E' side = all excusable events (employer and neutral): they earn time. Money is limited to
    the but-for delay of the employer's own events (`sole_money`)."""
    exc, emp = game.excusable(), game.party(EMPLOYER)
    vE, vC, vN = game.v(exc), game.v(game.party(CONTRACTOR)), game.v(game.all)
    money = vN - game.v(game.all - emp) if emp != exc else vN - vC
    return PartyValues(vE, vC, vN, money)


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _money(pv: PartyValues, eot: float) -> float:
    # Money needs but-for causation (Keating 9-105, adopted in Thomas Barnes para 118;
    # SCL Protocol separability) and cannot exceed the time actually granted.
    return _clip(min(pv.sole_E if pv.sole_money is None else pv.sole_money, eot), 0.0, pv.vN)


# --- operators -----------------------------------------------------------------

def but_for(game: DelayGame) -> Outcome:
    """Control: contractor gets only the delay that would not have occurred but for E."""
    pv = party_values(game)
    return Outcome("but_for", pv.sole_E, _money(pv, pv.sole_E), pv.vN)


def as_planned_impact(game: DelayGame) -> Outcome:
    """'Effective cause' tested prospectively on the as-planned programme, ignoring chronology.

    EOT = delay E alone would cause (capped at the actual net delay). Contractor
    concurrency never reduces the EOT (Malmaison), and timing is irrelevant.
    """
    pv = party_values(game)
    eot = min(pv.vE, pv.vN)
    return Outcome("as_planned_impact", eot, _money(pv, eot), pv.vN)


def _chronological(game: DelayGame, groups: List[List[DelayEvent]]) -> float:
    """Walk event groups in time order. Inside a group containing both parties the
    employer gets its full stand-alone effect relative to the progress so far
    (Malmaison within true concurrency); otherwise employer events get only the
    actual further delay they add to the already-delayed position."""
    prefix = frozenset()
    eot = 0.0
    for g in groups:
        ids = frozenset(e.id for e in g)
        e_ids = frozenset(e.id for e in g if e.party in EXCUSABLE)
        base = game.v(prefix)
        if e_ids:
            e_gain = game.v(prefix | e_ids) - base
            if len(e_ids) < len(ids):          # both parties in the group: true concurrency
                eot += min(e_gain, game.v(prefix | ids) - base)
            else:
                eot += e_gain
        prefix = prefix | ids
    return eot


def same_day_groups(events: Sequence[DelayEvent]) -> List[List[DelayEvent]]:
    groups: Dict[float, List[DelayEvent]] = {}
    for e in events:
        groups.setdefault(e.start, []).append(e)
    return [groups[k] for k in sorted(groups)]


def first_in_time(game: DelayGame) -> Outcome:
    """Strict sequence: only events that begin on the same day are concurrent; a later
    employer event earns time only for the further delay it adds to the position already
    reached. This is a commentators' narrow reading; the verified judgments (Adyard para
    279, Saga para 249) state a 'felt at the same time' test instead."""
    pv = party_values(game)
    eot = _clip(_chronological(game, same_day_groups(game.events)), 0.0, pv.vN)
    return Outcome("first_in_time", eot, _money(pv, eot), pv.vN)


def effective_cause(game: DelayGame) -> Outcome:
    """Actual-delay gateway, then Malmaison.

    Step 1 (Adyard paras 279-295; Saga para 251 'concurrency actually affecting the completion
    date as then scheduled'): walking events in time order, an employer event (or same-day group)
    qualifies only if it causes actual further delay to completion given everything that has
    happened before it.
    Step 2 (Malmaison; Walter Lilly para 370; Thomas Barnes paras 118, 148): a qualifying employer
    event is credited with its own effect, assessed on the employer events alone, so the
    contractor's concurrent delay does not reduce the extension.

    Built from the verified judgments' wording after reading them, then tested against them.
    """
    pv = party_values(game)
    prefix, e_prefix = frozenset(), frozenset()
    eot = 0.0
    for g in same_day_groups(game.events):
        ids = frozenset(e.id for e in g)
        e_ids = frozenset(e.id for e in g if e.party in EXCUSABLE)
        if e_ids and game.v(prefix | e_ids) - game.v(prefix) > 1e-9:
            eot += game.v(e_prefix | e_ids) - game.v(e_prefix)
            e_prefix = e_prefix | e_ids
        prefix = prefix | ids
    eot = _clip(eot, 0.0, pv.vN)
    return Outcome("effective_cause", eot, _money(pv, eot), pv.vN)


def window_groups(events: Sequence[DelayEvent], length: float, offset: float = 0.0) -> List[List[DelayEvent]]:
    """Fixed calendar windows [offset + k*length, offset + (k+1)*length)."""
    import math
    groups: Dict[int, List[DelayEvent]] = {}
    for e in events:
        groups.setdefault(math.floor((e.start - offset) / length), []).append(e)
    return [groups[k] for k in sorted(groups)]


def windows_analysis(game: DelayGame, length: float, offset: float = 0.0) -> Outcome:
    """Windows (watershed) analysis: the programme is reviewed at fixed window boundaries.
    Events whose effects begin in the same window are treated as concurrent (Malmaison inside the
    window); across windows chronology governs. length -> 0 gives the strict sequence; one window
    covering everything gives the as-planned impact."""
    pv = party_values(game)
    eot = _clip(_chronological(game, window_groups(game.events, length, offset)), 0.0, pv.vN)
    return Outcome(f"windows_{length:g}", eot, _money(pv, eot), pv.vN)


def nec4_prospective(game: DelayGame) -> Outcome:
    """NEC4 ECC clause 63.5 (as amended 2019), modelling reading: each compensation event is
    assessed prospectively as the delay it causes to planned Completion on the Accepted Programme
    current at its dividing date, which already shows earlier delays. Later contractor delays
    do not reduce it. Time and money are assessed together, so the delay is also paid.
    The clause text and its treatment of concurrency need checking against the contract."""
    pv = party_values(game)
    eot = _clip(_chronological(game, same_day_groups(game.events)), 0.0, pv.vN)
    paid = eot if not game.party("N") else _money(pv, eot)  # neutral events: time only
    return Outcome("nec4_prospective", eot, paid, pv.vN)


def overlap_groups(events: Sequence[DelayEvent], tolerance: float = 0.0) -> List[List[DelayEvent]]:
    """Connected groups of events whose delay windows [start, start+days] overlap."""
    groups: List[List[DelayEvent]] = []
    end = None
    for e in sorted(events, key=lambda x: (x.start, x.id)):
        if groups and e.start <= end + tolerance:
            groups[-1].append(e)
            end = max(end, e.end)
        else:
            groups.append([e])
            end = e.end
    return groups


def overlap_concurrency(game: DelayGame, tolerance: float = 0.0) -> Outcome:
    """SCL Protocol (2nd ed.) / Thomas Barnes reading: events are concurrent when their
    delaying effects are felt over the same period (overlapping windows); inside such a
    period contractor delay does not reduce the EOT, outside it chronology governs."""
    pv = party_values(game)
    eot = _clip(_chronological(game, overlap_groups(game.events, tolerance)), 0.0, pv.vN)
    return Outcome("overlap_concurrency", eot, _money(pv, eot), pv.vN)


def city_inn(game: DelayGame, dominance: float = 0.75) -> Outcome:
    """Scottish approach (City Inn v Shepherd, CSIH 2010).

    A dominant cause (party Shapley share >= `dominance`) takes the period; otherwise the
    concurrent days are apportioned by relative weight (causative significance x culpability,
    mean of event weights per party). Money is not apportioned here (open question; flagged).
    """
    pv = party_values(game)
    if pv.vN <= 0:
        return Outcome("city_inn", 0.0, 0.0, 0.0)
    phi_E = 0.5 * (pv.vE + pv.sole_E)
    phi_C = 0.5 * (pv.vC + pv.sole_C)
    share_E = phi_E / (phi_E + phi_C) if (phi_E + phi_C) > 0 else 0.5
    if share_E >= dominance:
        eot = min(pv.vE, pv.vN)
    elif share_E <= 1.0 - dominance:
        eot = pv.sole_E
    else:
        wE = _mean_weight(game, "excusable")
        wC = _mean_weight(game, CONTRACTOR)
        eot = pv.sole_E + pv.overlap * wE / (wE + wC)
    eot = _clip(eot, 0.0, pv.vN)
    return Outcome("city_inn", eot, _money(pv, eot), pv.vN)


def _mean_weight(game: DelayGame, party: str) -> float:
    ws = [e.weight for e in game.events if (e.party in EXCUSABLE if party == "excusable" else e.party == party)]
    return sum(ws) / len(ws) if ws else 1.0


def contractual_exclusion(game: DelayGame) -> Outcome:
    """North Midland v Cyden Homes: a clause excluding concurrent delay from EOT is enforceable.
    Concurrent days are not counted, so the EOT collapses to the but-for delay."""
    pv = party_values(game)
    return Outcome("contractual_exclusion", pv.sole_E, _money(pv, pv.sole_E), pv.vN)


def symmetric_shapley(game: DelayGame) -> Outcome:
    """Descriptive two-party Shapley split with an as-planned baseline (v1, corrected)."""
    pv = party_values(game)
    eot = _clip(0.5 * (pv.vE + pv.sole_E), 0.0, pv.vN)
    return Outcome("symmetric_shapley", eot, _money(pv, eot), pv.vN)


DOCTRINES: Dict[str, Callable[[DelayGame], Outcome]] = {
    "but_for": but_for,
    "first_in_time": first_in_time,
    "effective_cause": effective_cause,
    "overlap_concurrency": overlap_concurrency,
    "as_planned_impact": as_planned_impact,
    "city_inn": city_inn,
    "contractual_exclusion": contractual_exclusion,
    "nec4_prospective": nec4_prospective,
    "symmetric_shapley": symmetric_shapley,
}

LABELS = {
    "but_for": "But-for (control)",
    "first_in_time": "Strict sequence (narrow reading)",
    "effective_cause": "Actual-delay gateway (Adyard / Saga / Thomas Barnes)",
    "overlap_concurrency": "Overlapping windows (broad 'felt at the same time')",
    "as_planned_impact": "As-planned impact (theoretical delay; cf. Lord Carloway in City Inn)",
    "city_inn": "City Inn apportionment (Scotland)",
    "contractual_exclusion": "Contractual exclusion (Cyden clause)",
    "nec4_prospective": "NEC4 prospective assessment (cl. 63.5)",
    "symmetric_shapley": "Symmetric Shapley (descriptive)",
}

ENGLISH_READINGS = ["first_in_time", "effective_cause", "overlap_concurrency", "as_planned_impact"]


def evaluate_all(game: DelayGame) -> Dict[str, Outcome]:
    return {k: f(game) for k, f in DOCTRINES.items()}
