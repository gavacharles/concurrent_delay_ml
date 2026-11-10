"""Back-propagating an impacted programme to an as-planned one.

A backward CPM pass from the contractual completion date gives, for every activity, the
latest start that still meets that date. Where the impacted programme holds an activity
later than this (a start-no-earlier-than date), the difference is the minimum slippage that
must have been introduced for the programme to overrun. Each slippage becomes a causal
event on a zero-duration "workfront available" activity, so that

    as-planned programme + all events  ==  impacted programme.

This is a minimum-change reconstruction: it assumes durations and logic are unchanged and
moves only the dates that have to move. It is not the original baseline, which is unknown.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .game import DelayEvent
from .network import NetworkSchedule, Task


def backward(ns: NetworkSchedule, target: float, extra: Optional[Dict[str, float]] = None
             ) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Late start / late finish for every leaf so that all leaves finish by `target`
    (calendar time treated as continuous; checked afterwards by a forward pass)."""
    extra = extra or {}
    inf = float("inf")
    lf_b = {u: inf for u in ns.tasks}
    ls_b = {u: inf for u in ns.tasks}
    for u in ns.leaves:
        lf_b[u] = target
    LS: Dict[str, float] = {}
    LF: Dict[str, float] = {}
    for u in reversed(ns._order):
        t = ns.tasks[u]
        if t.summary:
            for c in t.children:
                lf_b[c] = min(lf_b[c], lf_b[u])
                ls_b[c] = min(ls_b[c], ls_b[u])
            continue
        d = t.duration + extra.get(u, 0.0)
        LF[u] = min(lf_b[u], ls_b[u] + d)
        LS[u] = LF[u] - d
        for p, typ, lag in ns._preds[u]:
            if typ == "FS":
                lf_b[p] = min(lf_b[p], LS[u] - lag)
            elif typ == "SS":
                ls_b[p] = min(ls_b[p], LS[u] - lag)
            elif typ == "FF":
                lf_b[p] = min(lf_b[p], LF[u] - lag)
            else:  # SF
                ls_b[p] = min(ls_b[p], LF[u] - lag)
    return LS, LF


@dataclass
class Slippage:
    task: str
    name: str
    wbs: str
    impacted_start: float
    as_planned_start: float

    @property
    def days(self) -> float:
        return self.impacted_start - self.as_planned_start


def back_propagate(ns: NetworkSchedule, target: float, max_iter: int = 8, tol: float = 0.01,
                   earliest: float = 0.0) -> Tuple[NetworkSchedule, List[Slippage]]:
    """Return the as-planned network (with a zero-duration 'workfront' activity in front of every
    moved activity) and the list of slippages. `ns` should be the logic-only impacted network."""
    snet = {u: ns.tasks[u].snet for u in ns.leaves if ns.tasks[u].snet is not None}

    def reconstruct(aim: float) -> Dict[str, float]:
        moved: Dict[str, float] = {}
        cur = ns
        for _ in range(max_iter):
            LS, _ = backward(cur, aim)
            changed = False
            for u, s in snet.items():
                new = max(earliest, min(moved.get(u, s), LS[u]))
                if s - new > tol and new < moved.get(u, s) - tol:
                    moved[u] = new
                    changed = True
            cur = _with_workfronts(ns, moved)
            if not changed:
                break
        return moved

    # The backward pass ignores working calendars (e.g. rain-season non-working periods), so
    # bisect on the aim: the latest aim whose reconstruction still finishes by the target.
    lo_aim, hi_aim = target - 400.0, target
    best = reconstruct(lo_aim)
    if _with_workfronts(ns, reconstruct(hi_aim)).finish() <= target + tol:
        best = reconstruct(hi_aim)
    else:
        for _ in range(18):
            mid = (lo_aim + hi_aim) / 2
            m = reconstruct(mid)
            if _with_workfronts(ns, m).finish() <= target + tol:
                lo_aim, best = mid, m
            else:
                hi_aim = mid
    moved = best
    cur = _with_workfronts(ns, moved)
    slips = [Slippage(u, ns.tasks[u].name, ns.tasks[u].wbs_path, snet[u], moved[u]) for u in moved]
    slips.sort(key=lambda s: s.as_planned_start)
    return cur, slips


def _with_workfronts(ns: NetworkSchedule, moved: Dict[str, float]) -> NetworkSchedule:
    tasks = {u: Task(**{**t.__dict__}) for u, t in ns.tasks.items()}
    links = list(ns.links)
    for u, start in moved.items():
        tasks[u].snet = None
        w = f"WF_{u}"
        tasks[w] = Task(w, f"Workfront available: {ns.tasks[u].name}", 0.0, snet=start,
                        wbs_path=ns.tasks[u].wbs_path)
        links.append((w, u, "FS", 0.0))
    return NetworkSchedule(tasks, links, origin=ns.origin, name=ns.name + " (as-planned, back-propagated)")


# --- responsibility under the Package 5 contract ---------------------------------------------

RULES = [
    # (pattern on "wbs > name", party, basis)
    (r"land acquisition", "E", "Sub-Cl. 2.1 + Appendix: Employer gives access/possession (all remaining Site within 546 days)"),
    (r"design approved|approval", "E", "Engineer's review period (Employer side)"),
    (r"design|survey|investigation|submitted", "C", "Design and Build: Contractor's design"),
    (r"mobili|camp|crusher|aggregate|precast|plant", "C", "Contractor's resources and production"),
    (r"utilit", "U", "Utility relocation: responsibility depends on the Particular Conditions (uncertain)"),
    (r"physical works|section|road|drain|culvert|structure|bridge|embankment|subgrade|sub base|base|surfac|"
     r"kerb|marker|backfill|backing|concrete|excavation", "E",
     "Workfront start held by a date: treated as Site access under Sub-Cl. 2.1 (report section 6 links the "
     "programme dates to land handover)"),
]


def classify(wbs: str, name: str) -> Tuple[str, str]:
    # drop the project root (its title contains 'Design and Build') before matching
    path = " > ".join(wbs.split(" > ")[1:])
    text = f"{path} > {name}".lower()
    for pat, party, basis in RULES:
        if re.search(pat, text):
            return party, basis
    return "U", "No rule matched (uncertain)"


def slippage_events(slips: List[Slippage]) -> List[DelayEvent]:
    out = []
    for s in slips:
        party, _ = classify(s.wbs, s.name)
        out.append(DelayEvent(f"S_{s.task}", party if party in ("E", "C") else "E", f"WF_{s.task}",
                              round(s.days, 3), round(s.as_planned_start, 3)))
    return out


def without(ns: NetworkSchedule, drop) -> NetworkSchedule:
    """Copy of the network without the given leaf activities (e.g. level-of-effort tasks)."""
    drop = set(drop)
    tasks = {}
    for u, t in ns.tasks.items():
        if u in drop:
            continue
        nt = Task(**{**t.__dict__})
        if t.summary:
            nt.children = [c for c in t.children if c not in drop]
            if not nt.children:
                continue
        tasks[u] = nt
    links = [(p, s, ty, l) for p, s, ty, l in ns.links if p in tasks and s in tasks]
    return NetworkSchedule(tasks, links, origin=ns.origin, name=ns.name)


LOE_PATTERN = r"environmental, social|level of effort|supervision|management"
