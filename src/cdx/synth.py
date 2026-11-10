"""Random schedules and delay-event configurations for the divergence experiments."""
from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np

from .game import CONTRACTOR, EMPLOYER, DelayEvent, DelayGame
from .schedule import Schedule


def random_schedule(rng: np.random.Generator, n_min: int = 12, n_max: int = 36) -> Schedule:
    """Layered random DAG: each activity links to 1-2 activities in later layers."""
    n = int(rng.integers(n_min, n_max + 1))
    n_layers = int(rng.integers(3, 8))
    layer_of = np.sort(rng.integers(0, n_layers, size=n))
    names = [f"T{i:02d}" for i in range(n)]
    durations = {nm: float(rng.integers(3, 21)) for nm in names}
    links: List[Tuple[str, str]] = []
    for i in range(n):
        later = [j for j in range(n) if layer_of[j] > layer_of[i]]
        if not later:
            continue
        k = int(rng.integers(1, 3))
        nxt = [j for j in later if layer_of[j] == min(layer_of[l] for l in later)]
        targets = set(rng.choice(nxt, size=min(k, len(nxt)), replace=False).tolist())
        if rng.random() < 0.3:
            targets.add(int(rng.choice(later)))
        links += [(names[i], names[j]) for j in targets]
    return Schedule(durations, links)


def random_events(rng: np.random.Generator, sched: Schedule, n_e=(1, 3), n_c=(1, 3)) -> List[DelayEvent]:
    es, _ = sched.forward()
    acts = list(sched.durations)
    events: List[DelayEvent] = []
    for party, (lo, hi) in ((EMPLOYER, n_e), (CONTRACTOR, n_c)):
        for k in range(int(rng.integers(lo, hi + 1))):
            a = acts[int(rng.integers(len(acts)))]
            start = es[a] + float(rng.uniform(0, sched.durations[a]))
            events.append(DelayEvent(f"{party}{k}", party, a, float(rng.integers(1, 31)), round(start, 1),
                                     float(rng.uniform(0.5, 1.5))))
    return events


def random_game(rng: np.random.Generator) -> DelayGame:
    sched = random_schedule(rng)
    return DelayGame(sched, random_events(rng, sched))


def features(game: DelayGame) -> Dict[str, float]:
    """Features describing the schedule and the event configuration (no outcome leakage:
    nothing here uses v(S) for S containing both parties)."""
    s = game.schedule
    tf = s.total_float()
    E = [e for e in game.events if e.party == EMPLOYER]
    C = [e for e in game.events if e.party == CONTRACTOR]

    def overlap_days(a, b):
        return max(0.0, min(a.end, b.end) - max(a.start, b.start))

    pairs = [(e, c) for e in E for c in C]
    return {
        "n_activities": len(s.durations),
        "critical_ratio": sum(1 for f in tf.values() if f <= 1e-9) / len(tf),
        "mean_float": float(np.mean(list(tf.values()))),
        "E_days": sum(e.days for e in E),
        "C_days": sum(c.days for c in C),
        "E_minus_C_days": sum(e.days for e in E) - sum(c.days for c in C),
        "E_min_float": min(tf[e.activity] for e in E),
        "C_min_float": min(tf[c.activity] for c in C),
        "E_stand_alone": game.v([e.id for e in E]),
        "C_stand_alone": game.v([c.id for c in C]),
        "start_gap_E_minus_C": min(e.start for e in E) - min(c.start for c in C),
        "window_overlap_days": sum(overlap_days(e, c) for e, c in pairs),
        "series_coupling": float(np.mean([s.on_same_chain(e.activity, c.activity) for e, c in pairs])),
        "culpability_ratio_C_over_E": float(np.mean([c.weight for c in C]) / np.mean([e.weight for e in E])),
        "E_first": float(min(e.start for e in E) < min(c.start for c in C)),
        "any_same_day": float(any(e.start == c.start for e, c in pairs)),
        "E_inside_C_window": float(any(c.start <= e.start and e.end <= c.end for e, c in pairs)),
        "shared_days": game.v([e.id for e in E]) + game.v([c.id for c in C]) - game.v(game.all),
        "n_events": float(len(game.events)),
    }

# features that need no joint schedule run (usable before the events are analysed together)
EX_ANTE = ["n_activities", "critical_ratio", "mean_float", "E_days", "C_days", "E_minus_C_days", "E_min_float",
           "C_min_float", "start_gap_E_minus_C", "window_overlap_days", "series_coupling",
           "culpability_ratio_C_over_E", "E_first", "any_same_day", "E_inside_C_window", "n_events"]
