"""CPM schedule as a deterministic structural causal model.

Activities are nodes with durations, logic links are finish-to-start edges.
The structural equations are the forward-pass recursions
    ES(n) = max(EF(p) for p in preds(n)),  EF(n) = ES(n) + d(n)
so intervening on a duration (a delay event) propagates causally to FINISH.
"""
from __future__ import annotations

from typing import Dict, Iterable, Mapping, Optional, Tuple

import networkx as nx

START, FINISH = "START", "FINISH"


class Schedule:
    def __init__(self, durations: Mapping[str, float], links: Iterable[Tuple[str, str]] = ()):
        if START in durations or FINISH in durations:
            raise ValueError(f"{START}/{FINISH} are reserved node names")
        self.durations: Dict[str, float] = {k: float(v) for k, v in durations.items()}
        g = nx.DiGraph()
        g.add_nodes_from(self.durations)
        for a, b in links:
            if a not in self.durations or b not in self.durations:
                raise ValueError(f"link {a}->{b} references an unknown activity")
            g.add_edge(a, b)
        for n in self.durations:
            if g.in_degree(n) == 0:
                g.add_edge(START, n)
            if g.out_degree(n) == 0:
                g.add_edge(n, FINISH)
        if not nx.is_directed_acyclic_graph(g):
            raise ValueError("schedule logic contains a cycle")
        self.graph = g
        self._order = list(nx.topological_sort(g))
        self._preds = {n: list(g.predecessors(n)) for n in self._order}
        self._succs = {n: list(g.successors(n)) for n in self._order}
        self.planned_finish = self.finish()

    def _dur(self, n: str, extra: Mapping[str, float]) -> float:
        if n == START or n == FINISH:
            return 0.0
        return self.durations[n] + extra.get(n, 0.0)

    def forward(self, extra: Optional[Mapping[str, float]] = None) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Early start / early finish with `extra` days added to activity durations."""
        extra = extra or {}
        es: Dict[str, float] = {}
        ef: Dict[str, float] = {}
        for n in self._order:
            es[n] = max((ef[p] for p in self._preds[n]), default=0.0)
            ef[n] = es[n] + self._dur(n, extra)
        return es, ef

    def finish(self, extra: Optional[Mapping[str, float]] = None) -> float:
        return self.forward(extra)[1][FINISH]

    def total_float(self, extra: Optional[Mapping[str, float]] = None) -> Dict[str, float]:
        extra = extra or {}
        es, ef = self.forward(extra)
        end = ef[FINISH]
        ls: Dict[str, float] = {}
        for n in reversed(self._order):
            lf = min((ls[s] for s in self._succs[n]), default=end)
            ls[n] = lf - self._dur(n, extra)
        return {n: ls[n] - es[n] for n in self.durations}

    def critical_activities(self, extra: Optional[Mapping[str, float]] = None, tol: float = 1e-9):
        return [n for n, f in self.total_float(extra).items() if f <= tol]

    def on_same_chain(self, a: str, b: str) -> bool:
        """True when a and b are in series (one is a logical ancestor of the other)."""
        return a == b or nx.has_path(self.graph, a, b) or nx.has_path(self.graph, b, a)
