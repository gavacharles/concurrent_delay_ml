"""General CPM network for real programmes (MS Project / MSPDI XML).

Supports FS/SS/FF/SF links with lags, start-no-earlier-than / finish-no-earlier-than
constraints, actual starts, per-task working calendars and summary roll-ups. Time is in
days from the project start; a task's working day runs 08:00-17:00 (8 working hours).

Exposes the same interface as cdx.schedule.Schedule (durations, finish(extra),
planned_finish, total_float(), on_same_chain()) so DelayGame and every doctrine operator
run on it unchanged.
"""
from __future__ import annotations

import bisect
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import networkx as nx

NS = {"m": "http://schemas.microsoft.com/project"}
LINK_TYPES = {"0": "FF", "1": "FS", "2": "SF", "3": "SS"}


class Calendar:
    """Working time on a day axis: every day works except listed non-working spans [a, b)."""

    def __init__(self, name: str = "24/7", nonworking: Sequence[Tuple[float, float]] = ()):
        self.name = name
        spans = sorted((float(a), float(b)) for a, b in nonworking if b > a)
        merged: List[List[float]] = []
        for a, b in spans:
            if merged and a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        self.spans = [tuple(s) for s in merged]
        self._starts = [s[0] for s in self.spans]

    def next_working(self, t: float) -> float:
        i = bisect.bisect_right(self._starts, t) - 1
        if i >= 0 and self.spans[i][0] <= t < self.spans[i][1]:
            return self.spans[i][1]
        return t

    def add(self, t: float, d: float) -> float:
        """Finish of `d` working days starting at t."""
        t = self.next_working(t)
        remaining = d
        i = bisect.bisect_right(self._starts, t)
        while i < len(self.spans) and remaining > 0:
            a, b = self.spans[i]
            if t + remaining <= a:
                break
            remaining -= a - t
            t = b
            i += 1
        return t + remaining

    def sub(self, t: float, d: float) -> float:
        """Latest start such that add(start, d) <= t (used for FF/SF/FNET)."""
        remaining = d
        i = bisect.bisect_left(self._starts, t) - 1
        while i >= 0 and remaining > 0:
            a, b = self.spans[i]
            if b <= t - remaining:
                break
            if t > b:
                remaining -= t - b
            t = a
            i -= 1
        return t - remaining


ALWAYS = Calendar()


@dataclass
class Task:
    uid: str
    name: str
    duration: float = 0.0
    calendar: Calendar = ALWAYS
    snet: Optional[float] = None       # start no earlier than
    fnet: Optional[float] = None       # finish no earlier than
    actual_start: Optional[float] = None
    children: List[str] = field(default_factory=list)  # leaf descendants if summary
    wbs_path: str = ""
    ms_start: Optional[float] = None   # MS Project's own dates, for validation
    ms_finish: Optional[float] = None
    critical: bool = False

    @property
    def summary(self) -> bool:
        return bool(self.children)


class NetworkSchedule:
    def __init__(self, tasks: Mapping[str, Task], links: Sequence[Tuple[str, str, str, float]],
                 origin: Optional[datetime] = None, name: str = ""):
        self.tasks: Dict[str, Task] = dict(tasks)
        self.origin = origin
        self.name = name
        self.leaves = [u for u, t in self.tasks.items() if not t.summary]
        self.durations: Dict[str, float] = {u: self.tasks[u].duration for u in self.leaves}
        # links into a summary apply to each of its leaves
        expanded = []
        for p, s, typ, lag in links:
            targets = self.tasks[s].children if self.tasks[s].summary else [s]
            expanded += [(p, c, typ, lag) for c in targets]
        self.links = expanded
        g = nx.DiGraph()
        g.add_nodes_from(self.tasks)
        for p, s, typ, lag in self.links:
            g.add_edge(p, s)
        for u, t in self.tasks.items():
            for c in t.children:
                g.add_edge(c, u)
        if not nx.is_directed_acyclic_graph(g):
            raise ValueError("programme logic contains a cycle")
        self.graph = g
        self._order = list(nx.topological_sort(g))
        self._preds: Dict[str, List[Tuple[str, str, float]]] = {u: [] for u in self.tasks}
        for p, s, typ, lag in self.links:
            self._preds[s].append((p, typ, lag))
        self._leaf_graph = nx.DiGraph()
        self._leaf_graph.add_nodes_from(self.leaves)
        for p, s, _, _ in self.links:
            for a in (self.tasks[p].children or [p]):
                self._leaf_graph.add_edge(a, s)
        self.planned_finish = self.finish()

    # --- forward pass ----------------------------------------------------------------
    def forward(self, extra: Optional[Mapping[str, float]] = None):
        extra = extra or {}
        es: Dict[str, float] = {}
        ef: Dict[str, float] = {}
        for u in self._order:
            t = self.tasks[u]
            if t.summary:
                es[u] = min(es[c] for c in t.children)
                ef[u] = max(ef[c] for c in t.children)
                continue
            d = t.duration + extra.get(u, 0.0)
            cal = t.calendar
            if t.actual_start is not None:
                start = t.actual_start
            else:
                start = 0.0
                if t.snet is not None:
                    start = max(start, t.snet)
                if t.fnet is not None:
                    start = max(start, cal.sub(t.fnet, d))
                for p, typ, lag in self._preds[u]:
                    if typ == "FS":
                        start = max(start, ef[p] + lag)
                    elif typ == "SS":
                        start = max(start, es[p] + lag)
                    elif typ == "FF":
                        start = max(start, cal.sub(ef[p] + lag, d))
                    else:  # SF
                        start = max(start, cal.sub(es[p] + lag, d))
                start = cal.next_working(start)
            es[u] = start
            ef[u] = cal.add(start, d) if d > 0 else start
        return es, ef

    def finish(self, extra: Optional[Mapping[str, float]] = None) -> float:
        _, ef = self.forward(extra)
        return max(ef[u] for u in self.leaves)

    def total_float(self, extra: Optional[Mapping[str, float]] = None, probe: float = 1.0) -> Dict[str, float]:
        """Float by delay probing on the 24/7 approximation of each link: the largest extra
        duration (searched by bisection up to 2000 days) that does not move completion."""
        base = self.finish(extra)
        out = {}
        for u in self.leaves:
            lo, hi = 0.0, 2000.0
            e = dict(extra or {})
            e[u] = e.get(u, 0.0) + hi
            if self.finish(e) <= base + 1e-6:
                out[u] = hi
                continue
            while hi - lo > probe:
                mid = (lo + hi) / 2
                e[u] = (extra or {}).get(u, 0.0) + mid
                if self.finish(e) <= base + 1e-6:
                    lo = mid
                else:
                    hi = mid
            out[u] = lo
        return out

    def on_same_chain(self, a: str, b: str) -> bool:
        g = self._leaf_graph
        return a == b or nx.has_path(g, a, b) or nx.has_path(g, b, a)

    def date(self, t: float) -> datetime:
        return self.origin + timedelta(days=math.floor(t)) if self.origin else None


# --- MSPDI loader -------------------------------------------------------------------------

def _g(e, tag):
    x = e.find("m:" + tag, NS) if e is not None else None
    return x.text if x is not None else None


def _hours(iso_dur: Optional[str]) -> float:
    if not iso_dur:
        return 0.0
    m = re.match(r"PT(\d+)H(\d+)M(\d+)S", iso_dur)
    return int(m.group(1)) + int(m.group(2)) / 60 + int(m.group(3)) / 3600 if m else 0.0


def _calendar_from(cal_el, origin: datetime) -> Calendar:
    spans = []
    for x in cal_el.findall("m:Exceptions/m:Exception", NS):
        if _g(x, "DayWorking") == "1":
            continue
        tp = x.find("m:TimePeriod", NS)
        a = datetime.fromisoformat(_g(tp, "FromDate")[:10])
        b = datetime.fromisoformat(_g(tp, "ToDate")[:10]) + timedelta(days=1)
        spans.append(((a - origin).days, (b - origin).days))
    # working weekdays: anything with DayWorking=0 for a weekday becomes recurring non-working
    off = {int(_g(w, "DayType")) for w in cal_el.findall("m:WeekDays/m:WeekDay", NS)
           if _g(w, "DayType") != "0" and _g(w, "DayWorking") == "0"}
    if off:
        for k in range(-60, 4000):
            day = origin + timedelta(days=k)
            if (day.isoweekday() % 7) + 1 in off:  # MSPDI: 1 = Sunday
                spans.append((k, k + 1))
    return Calendar(_g(cal_el, "Name") or "", spans)


def load_mspdi(path: str, name: str = "") -> NetworkSchedule:
    root = ET.parse(path).getroot()
    origin = datetime.fromisoformat(_g(root, "StartDate")[:10])
    mpd = float(_g(root, "MinutesPerDay") or 480)
    hours_per_day = mpd / 60

    def to_day(iso: Optional[str], is_finish: bool = False) -> Optional[float]:
        if not iso:
            return None
        dt = datetime.fromisoformat(iso)
        days = (dt.date() - origin.date()).days
        h = dt.hour + dt.minute / 60
        worked = min(max(h - 8, 0), 4) + min(max(h - 13, 0), 4)  # 08-12, 13-17
        return days + worked / hours_per_day

    cals = {_g(c, "UID"): _calendar_from(c, origin) for c in root.findall("m:Calendars/m:Calendar", NS)}
    proj_cal = _g(root, "CalendarUID")
    raw = root.findall("m:Tasks/m:Task", NS)
    tasks: Dict[str, Task] = {}
    stack: List[Tuple[int, str]] = []
    parent: Dict[str, Optional[str]] = {}
    for t in raw:
        uid, lvl = _g(t, "UID"), int(_g(t, "OutlineLevel") or 0)
        if lvl == 0:
            continue  # project summary row
        while stack and stack[-1][0] >= lvl:
            stack.pop()
        parent[uid] = stack[-1][1] if stack else None
        stack.append((lvl, uid))
        cal_uid = _g(t, "CalendarUID")
        cal = cals.get(proj_cal if cal_uid in (None, "-1") else cal_uid, ALWAYS)
        ctype, cdate = _g(t, "ConstraintType"), _g(t, "ConstraintDate")
        tasks[uid] = Task(
            uid=uid, name=(_g(t, "Name") or "").strip(),
            duration=_hours(_g(t, "Duration")) / hours_per_day,
            calendar=cal,
            snet=to_day(cdate) if ctype == "4" else None,
            fnet=to_day(cdate) if ctype == "6" else None,
            actual_start=to_day(_g(t, "ActualStart")),
            ms_start=to_day(_g(t, "Start")), ms_finish=to_day(_g(t, "Finish")),
            critical=_g(t, "Critical") == "1",
        )
        if _g(t, "Summary") == "1":
            tasks[uid].children = ["__summary__"]  # placeholder, filled below
    for uid in tasks:
        if tasks[uid].children == ["__summary__"]:
            tasks[uid].children = []
    for uid, p in parent.items():
        names, q = [], p
        while q:
            names.append(tasks[q].name)
            q = parent.get(q)
        tasks[uid].wbs_path = " > ".join(reversed(names))

    def leaf_descendants(u):
        kids = [c for c, p in parent.items() if p == u]
        out = []
        for k in kids:
            out += leaf_descendants(k) if any(pp == k for pp in parent.values()) else [k]
        return out

    for t in raw:
        uid = _g(t, "UID")
        if uid in tasks and _g(t, "Summary") == "1":
            tasks[uid].children = leaf_descendants(uid)
    tasks = {u: t for u, t in tasks.items() if not (t.summary is False and _is_empty_summary(raw, u))}
    links = []
    for t in raw:
        s = _g(t, "UID")
        if s not in tasks:
            continue
        for l in t.findall("m:PredecessorLink", NS):
            p = _g(l, "PredecessorUID")
            if p in tasks:
                links.append((p, s, LINK_TYPES[_g(l, "Type")], int(_g(l, "LinkLag") or 0) / 600 / hours_per_day))
    return NetworkSchedule(tasks, links, origin=origin, name=name or (_g(root, "Title") or ""))


def _is_empty_summary(raw, uid) -> bool:
    for t in raw:
        if _g(t, "UID") == uid:
            return _g(t, "Summary") == "1"
    return False


def logic_only(ns: NetworkSchedule, reference_extra: Optional[Mapping[str, float]] = None) -> NetworkSchedule:
    """Replace finish-no-earlier-than constraints with start-no-earlier-than at the start the
    programme shows. Pass `reference_extra` (e.g. the interruptions of an impacted programme) so
    those starts are taken from the programme as issued; removing the events then shortens the
    tasks without moving their planned starts. Delays now propagate monotonically (a longer task
    can no longer start earlier), which a causal delay analysis needs."""
    es, _ = ns.forward(reference_extra)
    tasks = {}
    for u, t in ns.tasks.items():
        nt = Task(**{**t.__dict__})
        if not t.summary and t.fnet is not None:
            nt.snet = max(t.snet or 0.0, es[u])
            nt.fnet = None
        tasks[u] = nt
    raw_links = [(p, s, typ, lag) for p, s, typ, lag in ns.links]
    out = NetworkSchedule(tasks, raw_links, origin=ns.origin, name=ns.name + " (logic-only)")
    return out


def programme_health(ns: NetworkSchedule) -> Dict[str, float]:
    """DCMA-style checks relevant to delay analysis."""
    leaves = ns.leaves
    has_pred = {s for _, s, _, _ in ns.links}
    has_succ = {a for p, _, _, _ in ns.links for a in (ns.tasks[p].children or [p])}
    n = len(leaves)
    lags = [l for *_, l in ns.links]
    return {
        "activities": n,
        "links": len(ns.links),
        "no_predecessor_pct": 100 * sum(u not in has_pred for u in leaves) / n,
        "no_successor_pct": 100 * sum(u not in has_succ for u in leaves) / n,
        "hard_constraints_pct": 100 * sum(ns.tasks[u].snet is not None or ns.tasks[u].fnet is not None for u in leaves) / n,
        "finish_constraints": sum(ns.tasks[u].fnet is not None for u in leaves),
        "links_with_lag_pct": 100 * sum(l != 0 for l in lags) / max(1, len(lags)),
        "non_FS_links_pct": 100 * sum(t != "FS" for _, _, t, _ in ns.links) / max(1, len(ns.links)),
        "long_activities_gt_44d_pct": 100 * sum(ns.tasks[u].duration > 44 for u in leaves) / n,
    }


def validate_against_ms(ns: NetworkSchedule, tol: float = 0.05) -> Dict[str, float]:
    es, ef = ns.forward()
    rows = [(u, es[u] - t.ms_start, ef[u] - t.ms_finish) for u, t in ns.tasks.items()
            if not t.summary and t.ms_start is not None]
    ok = [r for r in rows if abs(r[1]) <= tol and abs(r[2]) <= tol]
    return {"tasks": len(rows), "match": len(ok), "match_rate": len(ok) / len(rows) if rows else float("nan"),
            "max_abs_err_days": max(max(abs(r[1]), abs(r[2])) for r in rows) if rows else 0.0,
            "mismatches": [r for r in rows if r not in ok]}
