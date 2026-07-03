from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import networkx as nx
import numpy as np

from synthetic_schedule import cpm_forward_backward


@dataclass
class RiskConfig:
    owner_event_prob: float = 0.26
    contractor_event_prob: float = 0.28
    owner_delay_low: int = 2
    owner_delay_high: int = 15
    contractor_delay_low: int = 2
    contractor_delay_high: int = 18
    concurrent_threshold_days: float = 6.0


def _critical_nodes(g: nx.DiGraph) -> List[str]:
    _, _, tf = cpm_forward_backward(g)
    return [n for n, f in tf.items() if n not in {"START", "FINISH"} and f <= 1e-9]


def _sample_risk_profile(rng: np.random.Generator) -> Dict[str, float]:
    return {
        "owner_event_prob": float(np.clip(rng.normal(0.26, 0.07), 0.05, 0.55)),
        "contractor_event_prob": float(np.clip(rng.normal(0.28, 0.07), 0.05, 0.60)),
    }


def simulate_once(
    g: nx.DiGraph,
    rng: np.random.Generator,
    base_config: RiskConfig | None = None,
) -> Dict[str, float]:
    """Inject owner/contractor risk events and label concurrency."""
    cfg = base_config or RiskConfig()
    sampled = _sample_risk_profile(rng)
    owner_p = sampled["owner_event_prob"]
    contractor_p = sampled["contractor_event_prob"]

    critical = _critical_nodes(g)
    if not critical:
        critical = [n for n in g.nodes if n not in {"START", "FINISH"}]

    activities = [n for n in g.nodes if n not in {"START", "FINISH"}]
    fragility = len(critical) / max(len(activities), 1)
    logic_complexity = g.number_of_edges() / max(len(activities), 1)
    _, _, tf = cpm_forward_backward(g)
    low_float_density = float(
        np.mean([tf[n] < 5.0 for n in activities]) if activities else 0.0
    )

    owner_cp_delay = 0.0
    contractor_cp_delay = 0.0

    owner_eff_p = np.clip(owner_p * (0.7 + 0.9 * fragility + 0.5 * low_float_density), 0.01, 0.98)
    contractor_eff_p = np.clip(
        contractor_p * (0.7 + 1.0 * fragility + 0.4 * low_float_density), 0.01, 0.98
    )

    owner_event = rng.random() < owner_eff_p
    contractor_event = rng.random() < contractor_eff_p

    if owner_event:
        base_owner = float(rng.integers(cfg.owner_delay_low, cfg.owner_delay_high + 1))
        owner_cp_delay = base_owner * (
            1.0 + 1.2 * fragility + 0.20 * low_float_density + 0.10 * logic_complexity
        )

    if contractor_event:
        base_contractor = float(
            rng.integers(cfg.contractor_delay_low, cfg.contractor_delay_high + 1)
        )
        contractor_cp_delay = base_contractor * (
            1.0 + 1.3 * fragility + 0.18 * low_float_density + 0.08 * logic_complexity
        )

    if owner_event and contractor_event:
        overlap_factor = 1.0 + 0.35 * fragility + 0.20 * low_float_density
        owner_cp_delay *= overlap_factor
        contractor_cp_delay *= overlap_factor

    concurrent = int(
        owner_cp_delay >= cfg.concurrent_threshold_days
        and contractor_cp_delay >= cfg.concurrent_threshold_days
    )

    total_delay = owner_cp_delay + contractor_cp_delay
    owner_share = owner_cp_delay / total_delay if total_delay > 0 else 0.0

    return {
        "owner_event_prob": owner_p,
        "contractor_event_prob": contractor_p,
        "fragility_index": float(fragility),
        "logic_complexity": float(logic_complexity),
        "low_float_density": float(low_float_density),
        "owner_cp_delay": owner_cp_delay,
        "contractor_cp_delay": contractor_cp_delay,
        "total_cp_delay": total_delay,
        "owner_delay_share": owner_share,
        "concurrent_delay": concurrent,
    }
