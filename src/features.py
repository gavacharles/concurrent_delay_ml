from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from synthetic_schedule import ScheduleConfig, generate_synthetic_schedule, schedule_features
from simulation import RiskConfig, simulate_once


def build_dataset(
    n_schedules: int = 400,
    sims_per_schedule: int = 80,
    seed: int = 42,
    schedule_config: ScheduleConfig | None = None,
    risk_config: RiskConfig | None = None,
) -> pd.DataFrame:
    """Create supervised dataset from synthetic schedules + Monte Carlo outcomes."""
    rng = np.random.default_rng(seed)
    rows: List[Dict[str, float]] = []

    for sid in range(n_schedules):
        g = generate_synthetic_schedule(rng=rng, config=schedule_config)
        s_feat = schedule_features(g)

        for _ in range(sims_per_schedule):
            sim = simulate_once(g=g, rng=rng, base_config=risk_config)
            row = {"schedule_id": float(sid), **s_feat, **sim}
            rows.append(row)

    return pd.DataFrame(rows)


def save_dataset(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
