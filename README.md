# concurrent_delay_ml

Python code, experiments and outputs for research on concurrent delay in construction programmes.

The `main` branch holds the first version (v1): two pipelines on synthetic critical-path networks. The current version, a causal programme model with legal attribution rules, tests and experiments, is on the branch `v2-doctrine-operators` (pull request #1); its README describes that layout.

## Contents of `main`

| Path | What it is |
|---|---|
| `src/synthetic_schedule.py` | Synthetic CPM networks (directed acyclic graphs) |
| `src/simulation.py` | Monte Carlo owner and contractor risk events, concurrency labels |
| `src/features.py` | Feature table assembly |
| `src/train.py` | Classifier training, grouped train/test split, calibration, importance |
| `src/run_pipeline.py` | One-command run of the classification pipeline |
| `src/liability_xai_pipeline.py` | Liability-apportionment pipeline (surrogate model + SHAP) |
| `data/concurrent_delay_training_data.csv` | Generated training data (rebuilt by `run_pipeline.py`) |
| `outputs/` | Metrics, importance tables, plots and write-ups produced by the pipelines |
| `requirements.txt` | Python dependencies |

## Setup and running

```
pip install -r requirements.txt
python src/run_pipeline.py            # classification pipeline -> outputs/
python src/liability_xai_pipeline.py  # liability pipeline -> outputs/liability_xai/
```

`xgboost` and `shap` are optional for the classifier (it falls back to a random forest) but required by the liability pipeline.
