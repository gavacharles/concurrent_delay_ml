from __future__ import annotations

from pathlib import Path

from features import build_dataset, save_dataset
from train import save_training_outputs, train_and_evaluate


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    data_path = root / "data" / "concurrent_delay_training_data.csv"
    out_dir = root / "outputs" / "v1"

    print("[1/3] Building synthetic Monte Carlo dataset...")
    df = build_dataset(n_schedules=450, sims_per_schedule=90, seed=2026)
    save_dataset(df, data_path)
    print(f"Saved dataset: {data_path}")

    print("[2/3] Training ensemble model...")
    _, metrics, importance, calibration, explainability = train_and_evaluate(df)

    print("[3/3] Writing outputs...")
    save_training_outputs(metrics, importance, calibration, explainability, out_dir)

    print("Done.")
    print("Metrics:", metrics)
    print("Top features:")
    print(importance.head(10).to_string(index=False))
    print("Top explainability features:")
    print(explainability.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
