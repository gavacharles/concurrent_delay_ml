# Liability Apportionment Pipeline Summary

- Baseline duration (days): 90.00
- Samples simulated: 6000
- RMSE: 6.0212
- MAE: 4.5505
- R2: 0.5726
- Archetypes tested: balanced_parallel, owner_path_dominant, contractor_path_dominant

## Scenario Apportionment (SHAP)
| scenario            |   owner_delay_days |   contractor_delay_days |   predicted_slippage_days |   base_value |   owner_shap |   contractor_shap |   owner_liability_share |   contractor_liability_share |
|:--------------------|-------------------:|------------------------:|--------------------------:|-------------:|-------------:|------------------:|------------------------:|-----------------------------:|
| Owner-Dominant      |                 30 |                      10 |                  15.9055  |      16.4868 |     3.88335  |         -4.46465  |                1        |                     0        |
| Contractor-Dominant |                 10 |                      30 |                  16.0854  |      16.4868 |    -4.19535  |          3.79391  |                0        |                     1        |
| Balanced-Moderate   |                 20 |                      20 |                  16.4425  |      16.4868 |    -0.341295 |          0.296982 |                0        |                     1        |
| High-High           |                 35 |                      35 |                  28.8401  |      16.4868 |     6.04528  |          6.30796  |                0.489368 |                     0.510632 |
| Low-Low             |                  8 |                       6 |                   5.32503 |      16.4868 |    -5.21192  |         -5.94989  |                0.5      |                     0.5      |

## CPM Benchmark Summary (MAE vs SHAP owner share)
| method         |   mae_vs_shap |
|:---------------|--------------:|
| proportional   |      0.216412 |
| equal_split    |      0.302126 |
| dominant_cause |      0.202126 |

## Liability Share Uncertainty Bounds
| scenario            |   owner_mean |   owner_p05 |   owner_p95 |   contractor_mean |   contractor_p05 |   contractor_p95 |
|:--------------------|-------------:|------------:|------------:|------------------:|-----------------:|-----------------:|
| Balanced-Moderate   |     0.550958 |    0        |     1       |          0.449042 |          0       |         1        |
| Contractor-Dominant |     0        |    0        |     0       |          1        |          1       |         1        |
| High-High           |     0.463119 |    0.375132 |     0.53647 |          0.536881 |          0.46353 |         0.624868 |
| Low-Low             |     0.5      |    0.5      |     0.5     |          0.5      |          0.5     |         0.5      |
| Owner-Dominant      |     1        |    1        |     1       |          0        |          0       |         0        |