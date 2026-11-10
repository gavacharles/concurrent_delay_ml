"""Delay events and the cooperative game they induce on a schedule.

v(S) = delay to completion (days beyond the as-planned finish) when only the
events in S occur.  The empty coalition is the as-planned programme, so every
attribution built on v is a but-for comparison against the plan -- not against
an "average project" as in v1's TreeSHAP baseline.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from math import factorial
from typing import Callable, Dict, FrozenSet, Iterable, List, Sequence

from .schedule import Schedule

EMPLOYER, CONTRACTOR, NEUTRAL = "E", "C", "N"
EXCUSABLE = (EMPLOYER, NEUTRAL)   # earn time; only EMPLOYER events earn money


@dataclass(frozen=True)
class DelayEvent:
    id: str
    party: str          # "E" employer risk, "C" contractor risk, "N" neutral (time, no money)
    activity: str       # activity whose duration the event extends
    days: float         # extension to that activity
    start: float        # project day the event's delaying effect begins
    weight: float = 1.0  # causative significance x culpability (used by City Inn only)

    def __post_init__(self):
        if self.party not in (EMPLOYER, CONTRACTOR, NEUTRAL):
            raise ValueError(f"event {self.id}: party must be 'E', 'C' or 'N'")
        if self.days < 0:
            raise ValueError(f"event {self.id}: days must be >= 0")
        if self.weight <= 0:
            raise ValueError(f"event {self.id}: weight must be > 0")

    @property
    def end(self) -> float:
        return self.start + self.days


class DelayGame:
    def __init__(self, schedule: Schedule, events: Sequence[DelayEvent], cache: Dict = None,
                 reference: float = None):
        """`reference`: completion date that delay is measured against (e.g. the contractual
        completion date). Defaults to the programme's own planned finish; with a later reference,
        terminal float absorbs delay first."""
        ids = [e.id for e in events]
        if len(set(ids)) != len(ids):
            raise ValueError("event ids must be unique")
        for e in events:
            if e.activity not in schedule.durations:
                raise ValueError(f"event {e.id} targets unknown activity {e.activity}")
        self.schedule = schedule
        self.reference = schedule.planned_finish if reference is None else reference
        self.events: List[DelayEvent] = list(events)
        self.by_id: Dict[str, DelayEvent] = {e.id: e for e in events}
        # v(S) depends only on which events occur, not on who is responsible, so games that
        # differ only in party allocation can share one cache.
        self._cache: Dict[FrozenSet[str], float] = cache if cache is not None else {}

    @property
    def all(self) -> FrozenSet[str]:
        return frozenset(self.by_id)

    def excusable(self) -> FrozenSet[str]:
        return frozenset(e.id for e in self.events if e.party in EXCUSABLE)

    def party(self, p: str) -> FrozenSet[str]:
        return frozenset(e.id for e in self.events if e.party == p)

    def extra(self, ids: Iterable[str]) -> Dict[str, float]:
        out: Dict[str, float] = defaultdict(float)
        for i in ids:
            e = self.by_id[i]
            out[e.activity] += e.days
        return out

    def v(self, ids: Iterable[str]) -> float:
        key = frozenset(ids)
        if key not in self._cache:
            delay = self.schedule.finish(self.extra(key)) - self.reference
            self._cache[key] = max(0.0, delay)
        return self._cache[key]


def shapley(players: Sequence[str], v: Callable[[FrozenSet[str]], float]) -> Dict[str, float]:
    """Exact Shapley values by subset enumeration (fine for n <= ~16 players)."""
    players = list(players)
    n = len(players)
    if n > 16:
        raise ValueError("exact Shapley enumeration limited to 16 players; use a sampling estimator")
    phi = {p: 0.0 for p in players}
    for p in players:
        others = [q for q in players if q != p]
        for k in range(n):
            w = factorial(k) * factorial(n - k - 1) / factorial(n)
            for s in combinations(others, k):
                s = frozenset(s)
                phi[p] += w * (v(s | {p}) - v(s))
    return phi


def ordered_contributions(order: Sequence[str], v: Callable[[FrozenSet[str]], float]) -> Dict[str, float]:
    """Marginal contribution of each player when added in the given order."""
    out: Dict[str, float] = {}
    prefix: FrozenSet[str] = frozenset()
    for p in order:
        nxt = prefix | {p}
        out[p] = v(nxt) - v(prefix)
        prefix = nxt
    return out
