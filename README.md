# concurrent_delay_ml

Python code, experiments, tests and documents for research on concurrent delay in construction: a causal model of a construction programme, with legal approaches to concurrency written as attribution rules on top of it.

## Repository layout

```
src/
  cdx/                    the package
    schedule.py           simple CPM network (finish-to-start links)
    network.py            real programmes from MS Project (MSPDI XML): SS/FF/SF links, lags,
                          constraints, calendars, interruptions; logic-only conversion; health checks
    game.py               delay events (employer / contractor / neutral) and the delay value function
    doctrines.py          attribution rules (actual-delay test, strict sequence, overlapping windows,
                          as-planned impact, City Inn, contractual exclusion, NEC4, windows analysis)
    contracts.py          contract regimes (JCT, Cyden clause, Scots law, NEC4, FIDIC 1999/2017)
    notices.py            notice condition (claims barred for late notice)
    backprop.py           back-propagation of an impacted programme to a completion date
    cases.py              stylised case library used by the fidelity tests
    synth.py              random programmes and event sets for synthetic experiments
  experiments/
    run_v2.py             case fidelity, synthetic divergence model (XGBoost + SHAP), phase maps
    run_real.py           study of a real impacted programme                  (needs local inputs)
    run_package5_xai.py   back-propagation and XAI ensemble on that programme (needs local inputs)
    make_figures.py       figures, MP4 animations, carousel
    make_covers.py        cover graphics
  liability_xai_pipeline.py, run_pipeline.py, simulation.py, synthetic_schedule.py, features.py, train.py
                          v1 pipelines (kept for reproducibility; outputs in outputs/v1/)
tests/                    unit, property and case-fidelity tests (pytest)
explorer/                 interactive pages (HTML) and the case-law page template
site/                     build script for the public site (site/build_site.py -> site/dist/)
docs/                     study design, formal results, paper draft, case-law data (law_timeline.json), posts
outputs/
  v1/                     archived v1 results
  v2/                     synthetic and case results, figures, animations, covers
data/                     generated training data; local inputs go in data/programmes/ (not tracked)
```

## Setup

Python 3.9 or later.

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Reading MS Project `.mpp` files also needs Java and [MPXJ](https://www.mpxj.org/) (`pip install mpxj`). Convert a programme to MSPDI XML with MPXJ's converter, then load it with `cdx.network.load_mspdi`.

## Running

```
python -m pytest tests                     # full test suite
python src/experiments/run_v2.py           # writes outputs/v2/
python src/experiments/make_figures.py     # writes outputs/v2/figures/ (MP4 needs imageio-ffmpeg)
python src/experiments/make_covers.py      # writes outputs/v2/figures/covers/
python site/build_site.py                  # writes site/dist/index.html
```

`run_real.py` and `run_package5_xai.py` need a project programme, a contract and a small config file in `data/programmes/`. Those inputs are confidential and are not in the repository.

## What is not tracked

`.gitignore` excludes `data/programmes/` (project programmes, contract and config), plus `outputs/real/` and `outputs/package5/`, which are derived from those inputs. Do not commit them.

## Public site

`site/build_site.py` combines `explorer/concurrent_delay_explorer.html`, `explorer/law_timeline_template.html` and `docs/law_timeline.json` into one static page. The built page is published from the separate repository [concurrent-delay-map](https://github.com/gavacharles/concurrent-delay-map). To update it, rebuild and copy `site/dist/` there.
