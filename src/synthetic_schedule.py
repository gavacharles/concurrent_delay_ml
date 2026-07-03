from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import networkx as nx
import numpy as np


@dataclass
class ScheduleConfig:
    min_activities: int = 25
    max_activities: int = 80
    edge_prob: float = 0.08
    duration_low: int = 3
    duration_high: int = 20


def _ensure_single_source_sink(g: nx.DiGraph) -> nx.DiGraph:
    sources = [n for n in g.nodes if g.in_degree(n) == 0]
    sinks = [n for n in g.nodes if g.out_degree(n) == 0]

    super_source = "START"
    super_sink = "FINISH"
    g.add_node(super_source, duration=0)
    g.add_node(super_sink, duration=0)

    for s in sources:
        if s != super_source:
            g.add_edge(super_source, s)
    for t in sinks:
        if t != super_sink:
            g.add_edge(t, super_sink)

    return g


def generate_synthetic_schedule(
    rng: np.random.Generator,
    config: ScheduleConfig | None = None,
) -> nx.DiGraph:
    """Generate a synthetic CPM-style DAG with activity durations."""
    config = config or ScheduleConfig()
    n = int(rng.integers(config.min_activities, config.max_activities + 1))

    g = nx.DiGraph()
    activity_nodes = [f"A{i:03d}" for i in range(1, n + 1)]
    g.add_nodes_from(activity_nodes)

    # Layered DAG construction to create realistic parallel workstreams and float variability
    max_layers = max(4, min(10, n // 3 if n >= 12 else 4))
    n_layers = int(rng.integers(4, max_layers + 1))

    shuffled = activity_nodes.copy()
    rng.shuffle(shuffled)
    layers = [list(chunk) for chunk in np.array_split(shuffled, n_layers) if len(chunk) > 0]

    for i in range(len(layers) - 1):
        curr_layer = layers[i]
        next_layer = layers[i + 1]

        # stochastic forward links
        for u in curr_layer:
            for v in next_layer:
                if rng.random() < max(config.edge_prob, 0.15):
                    g.add_edge(u, v)

            # optional skip-layer links for richer logic
            if i + 2 < len(layers):
                for v in layers[i + 2]:
                    if rng.random() < config.edge_prob * 0.5:
                        g.add_edge(u, v)

        # enforce at least one predecessor for every next-layer activity
        for v in next_layer:
            if g.in_degree(v) == 0:
                u = curr_layer[int(rng.integers(0, len(curr_layer)))]
                g.add_edge(u, v)

        # enforce at least one successor for every current-layer activity
        for u in curr_layer:
            if g.out_degree(u) == 0:
                v = next_layer[int(rng.integers(0, len(next_layer)))]
                g.add_edge(u, v)

    for node in activity_nodes:
        g.nodes[node]["duration"] = int(
            rng.integers(config.duration_low, config.duration_high + 1)
        )

    g = _ensure_single_source_sink(g)
    return g


def cpm_forward_backward(g: nx.DiGraph) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    """Return ES, EF, float for each activity in DAG."""
    topo = list(nx.topological_sort(g))
    es: Dict[str, float] = {n: 0.0 for n in topo}
    ef: Dict[str, float] = {n: 0.0 for n in topo}

    for n in topo:
        preds = list(g.predecessors(n))
        if preds:
            es[n] = max(ef[p] for p in preds)
        ef[n] = es[n] + float(g.nodes[n].get("duration", 0.0))

    project_finish = max(ef.values())
    lf: Dict[str, float] = {n: project_finish for n in topo}
    ls: Dict[str, float] = {n: project_finish for n in topo}

    for n in reversed(topo):
        succs = list(g.successors(n))
        if succs:
            lf[n] = min(ls[s] for s in succs)
        ls[n] = lf[n] - float(g.nodes[n].get("duration", 0.0))

    total_float = {n: ls[n] - es[n] for n in topo}
    return es, ef, total_float


def schedule_features(g: nx.DiGraph) -> Dict[str, float]:
    """Structural schedule descriptors for ML."""
    es, ef, tf = cpm_forward_backward(g)
    activities = [n for n in g.nodes if n not in {"START", "FINISH"}]

    floats = np.array([tf[n] for n in activities], dtype=float)
    durations = np.array([float(g.nodes[n].get("duration", 0.0)) for n in activities], dtype=float)

    critical_count = float(np.sum(floats <= 1e-9))
    project_duration = float(max(ef.values()))

    return {
        "n_activities": float(len(activities)),
        "n_edges": float(g.number_of_edges()),
        "density": float(nx.density(g)),
        "avg_duration": float(durations.mean() if len(durations) else 0.0),
        "std_duration": float(durations.std(ddof=0) if len(durations) else 0.0),
        "project_duration_baseline": project_duration,
        "critical_ratio": float(critical_count / max(len(activities), 1)),
        "float_mean": float(floats.mean() if len(floats) else 0.0),
        "float_std": float(floats.std(ddof=0) if len(floats) else 0.0),
        "float_density_lt5": float(np.mean(floats < 5.0) if len(floats) else 0.0),
    }
