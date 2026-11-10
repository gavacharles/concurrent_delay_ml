"""Package 5: back-propagated as-planned programme + explainable doctrine analysis.

Contract (PKG5 contract document, Appendix to Tender / Particular Conditions):
  FIDIC 1999 Yellow Book; laws of Uganda (1.4); Time for Completion 1099 days (1.1.3.3);
  access: road corridor at Commencement, 30% of remaining Site within 91 days, the rest in ~5 km
  sections within 546 days (2.1); delay damages 0.05% of Contract Price per day, max 10% (8.7);
  no Special Provision on concurrency (user, 2026-11-10); Employer responsible for site access and
  payment (user).

Steps
  1. Impacted programme -> logic-only network (FNET -> SNET at programme starts), level-of-effort
     activity removed.
  2. Back-propagation from the contractual completion date (27 Apr 2022): minimum date slippages that
     reproduce the impacted completion (24 Jul 2023). Each slippage = one event, classified by the
     contract's responsibility terms (cdx.backprop.RULES).
  3. Doctrine and contract-regime outcomes, delay damages exposure.
  4. Explainability:
     a. Shapley attribution of delay to completion over the events (which facts drive the overrun);
     b. ensemble of Package 5 variants (uncertain responsibility, durations, event sizes, and
        hypothetical contractor productivity delays on the driving chain) -> XGBoost + SHAP on what
        moves the extension, the money and the gap between legal readings.

Run: python src/experiments/run_package5_xai.py  -> outputs/package5/ (gitignored)
"""
from __future__ import annotations

import re
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "experiments"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

import run_real as rr
from cdx import DelayEvent, DelayGame
from cdx.backprop import LOE_PATTERN, back_propagate, classify, slippage_events, without
from cdx.contracts import evaluate_regimes
from cdx.doctrines import DOCTRINES, ENGLISH_READINGS, LABELS, party_values
from cdx.network import NetworkSchedule, Task, logic_only
from cdx.notices import apply_notice_gate

OUT = ROOT / "outputs" / "package5"
PLOTS = OUT / "plots"
SEED = 2026
CONTRACT_END = datetime(2022, 4, 28)        # end of 27 Apr 2022 (Commencement 25 Apr 2019 + 1099 days)
# Contract price is confidential: read from the gitignored local config (falls back to 0 -> damages in % only)
_CFG = Path(__file__).resolve().parents[2] / "data" / "programmes" / "package5_config.json"
CONTRACT_PRICE_UGX = __import__("json").load(open(_CFG))["contract_price_ugx"] if _CFG.exists() else 0
LD_RATE, LD_CAP = 0.0005, 0.10               # Sub-Cl. 8.7 (Appendix to Tender)
# Uganda national COVID-19 lockdowns (approximate public dates; VERIFY against project records)
LOCKDOWNS = [(datetime(2020, 3, 31), datetime(2020, 6, 3)), (datetime(2021, 6, 18), datetime(2021, 7, 30))]
EMP, CON, EMP_SOFT, CON_SOFT, INK, MUTED = rr.EMP, rr.CON, rr.EMP_SOFT, rr.CON_SOFT, rr.INK, rr.MUTED
SHOW = ["contractual_exclusion", "first_in_time", "city_inn", "effective_cause", "overlap_concurrency",
        "as_planned_impact"]
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 11, "axes.titleweight": "bold"})

# confidence that a slippage of this kind is the Employer's (access) rather than the Contractor's
CONFIDENCE = [
    (r"sub base|base|surfac|pavement", 0.95, "Section 2 pavement: programme and report tie it to land handover"),
    (r"earthwork|clearing|grubbing|subgrade|embankment", 0.75, "Embankment workfronts: access likely, sequencing possible"),
    (r"culvert|bridge|river|garbion|gabion|foundation|structure", 0.65, "Structures: access or contractor resources"),
    (r"aggregate|precast|crusher|mobili", 0.05, "Contractor's production and resources"),
]


def p_employer(name: str, wbs: str) -> tuple:
    text = f"{wbs} > {name}".lower()
    for pat, p, why in CONFIDENCE:
        if re.search(pat, text):
            return p, why
    return 0.5, "unclassified"


def build():
    ns, inter = rr.load()
    extra = inter.groupby("task_uid").days.sum().to_dict()
    lo0 = logic_only(ns, extra)
    loe = [u for u in lo0.leaves if re.search(LOE_PATTERN, lo0.tasks[u].name.lower())]
    lo = without(lo0, loe)
    T = float((CONTRACT_END - ns.origin).days)
    ap, slips = back_propagate(lo, T, max_iter=20)
    base_events = slippage_events(slips)
    events = covid_split(base_events, ns.origin)
    rows = []
    for s, e in zip(slips, base_events):
        party, basis = classify(s.wbs, s.name)
        pe, why = p_employer(s.name, s.wbs)
        rows.append({"event_id": e.id, "activity": s.name, "group": s.wbs.split(" > ")[-1],
                     "as_planned_start": ap.date(s.as_planned_start).date(),
                     "impacted_start": ap.date(s.impacted_start).date(), "slip_days": round(s.days, 1),
                     "party": e.party, "contract_basis": basis, "p_employer": pe, "uncertainty_note": why,
                     "covid_days": round(sum(x.days for x in events if x.id == e.id + '|N'), 1)})
    reg = pd.DataFrame(rows)
    return ns, lo, ap, T, events, reg, loe


def covid_split(events, origin):
    """Split each employer access slip: the days of the slip interval that fall inside a national
    lockdown become a neutral event (FIDIC 1999 Sub-Cl. 8.4(d): time, no money)."""
    out = []
    for e in events:
        if e.party != "E":
            out.append(e)
            continue
        a, b = e.start, e.start + e.days
        n_days, n_start = 0.0, None
        for w0, w1 in LOCKDOWNS:
            lo, hi = max(a, (w0 - origin).days), min(b, (w1 - origin).days + 1)
            if hi > lo:
                n_days += hi - lo
                n_start = lo if n_start is None else n_start
        if n_days > 0:
            out.append(DelayEvent(e.id, "E", e.activity, round(e.days - n_days, 3), e.start))
            out.append(DelayEvent(e.id + "|N", "N", e.activity, round(n_days, 3), n_start))
        else:
            out.append(e)
    return out


def ld_ugx(days: float) -> float:
    return min(days * LD_RATE, LD_CAP) * CONTRACT_PRICE_UGX


def shapley_sampled(players, value, n_perm, rng):
    phi = {p: 0.0 for p in players}
    for _ in range(n_perm):
        order = list(rng.permutation(players))
        prev, S = value(frozenset()), set()
        for p in order:
            S.add(p)
            cur = value(frozenset(S))
            phi[p] += cur - prev
            prev = cur
    return {p: v / n_perm for p, v in phi.items()}


def perturbed(ap: NetworkSchedule, rng, scale=(0.9, 1.0, 1.15)) -> NetworkSchedule:
    tasks = {u: Task(**{**t.__dict__}) for u, t in ap.tasks.items()}
    for t in tasks.values():
        if not t.summary and t.duration > 0:
            t.duration *= rng.triangular(*scale)
    return NetworkSchedule(tasks, ap.links, origin=ap.origin)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    ns, lo, ap, T, events, reg, loe = build()
    L = []
    imp_end = lo.date(lo.finish() - 1e-6).date()
    L += [f"Contract completion 27 Apr 2022 (1099 days); impacted programme completes {imp_end} "
          f"(+{lo.finish() - T:.0f} d). Level-of-effort activity removed: {lo.tasks.get(loe[0]).name if False else loe}.",
          f"Back-propagated as-planned programme finishes {ap.date(ap.finish() - 1e-6).date()} "
          f"({T - ap.finish():.0f} d terminal float: the contract date falls in the Mar-May 2022 rain season, "
          f"when the programme's rain calendar allows no kerbing).",
          f"{len(events)} slippages reproduce the impacted completion: "
          f"{(reg.party == 'E').sum()} on Employer access workfronts ({reg.slip_days[reg.party == 'E'].sum():.0f} d summed), "
          f"{(reg.party == 'C').sum()} on Contractor production ({reg.slip_days[reg.party == 'C'].sum():.0f} d summed)."]

    # --- reconstruction chart ------------------------------------------------------------
    r = reg.sort_values("as_planned_start")
    fig, ax = plt.subplots(figsize=(10, 0.36 * len(r) + 1.5))
    for i, x in enumerate(r.itertuples()):
        a, b = pd.Timestamp(x.as_planned_start), pd.Timestamp(x.impacted_start)
        c = EMP if x.party == "E" else CON
        ax.plot([a, b], [i, i], color=c, lw=3, solid_capstyle="butt", alpha=0.85)
        ax.plot(a, i, "o", ms=4, color=c)
        ax.text(b + pd.Timedelta(days=8), i, f"+{x.slip_days:.0f} d", va="center", fontsize=7.5, color=MUTED)
    ax.axvline(pd.Timestamp(2020, 10, 22), color=INK, ls="--", lw=0.8)
    ax.text(pd.Timestamp(2020, 10, 26), -0.9, "all Site access due\n(day 546, Sub-Cl. 2.1)", fontsize=7.5, va="top")
    ax.set_yticks(range(len(r)))
    ax.set_yticklabels([f"{a[:28]} · {g[:22]}" for a, g in zip(r.activity, r.group)], fontsize=7.5)
    ax.invert_yaxis()
    ax.set_title("Back-propagated: latest start to finish on time (dot) vs programmed start (end)",
                 loc="left", fontsize=10)
    ax.legend(handles=[Patch(color=EMP, label="Employer (site access)"), Patch(color=CON, label="Contractor (production)")],
              frameon=False, fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(PLOTS / "p5_backpropagation.png", dpi=180)
    plt.close(fig)

    # --- doctrine outcomes and money ---------------------------------------------------------
    g = DelayGame(ap, events, reference=T)
    pv = party_values(g)
    res = {k: f(g) for k, f in DOCTRINES.items()}
    regimes = pd.DataFrame(evaluate_regimes(g)).T
    regimes.to_csv(OUT / "contract_regimes.csv")
    out = pd.DataFrame([{"rule": LABELS[d], "eot_days": res[d].eot, "paid_days": res[d].compensable,
                         "contractor_bears_days": res[d].ld_days,
                         "delay_damages_UGX_bn": ld_ugx(res[d].ld_days) / 1e9} for d in SHOW])
    out.to_csv(OUT / "outcomes.csv", index=False)
    L += [f"Delay beyond the contract date: {pv.vN:.0f} d; Employer events alone {pv.vE:.0f}, Contractor events alone "
          f"{pv.vC:.0f}, shared {pv.overlap:.0f}.",
          "Outcomes: " + "; ".join(f"{LABELS[d].split(' (')[0]} EOT {res[d].eot:.0f}/paid {res[d].compensable:.0f}"
                                     for d in SHOW),
          f"Delay damages exposure without any extension: {min(pv.vN, LD_CAP / LD_RATE):.0f} d -> "
          f"UGX {ld_ugx(pv.vN) / 1e9:.1f} bn (cap reached at {LD_CAP / LD_RATE:.0f} d)."]
    n_days = sum(e.days for e in events if e.party == "N")
    L += [f"COVID-19 (lockdown overlap, neutral under Sub-Cl. 8.4(d)): {n_days:.0f} d of slippage reclassified as "
          f"time-only; money under the actual-delay test {res['effective_cause'].compensable:.0f} d."]
    notice_rows = []
    pave = [e.id for e in events if e.activity == "WF_466" and e.party in ("E", "N")]
    struct = [e.id for e in events if e.party in ("E", "N") and re.search(
        r"culvert|bridge|river|foundation", ap.tasks[e.activity].wbs_path.lower() + ap.tasks[e.activity].name.lower())]
    for label, barred in [("All notices given", []), ("No notice: Section 2 pavement access", pave),
                          ("No notices: structures", struct), ("No notices at all", [e.id for e in events])]:
        gg = DelayGame(ap, apply_notice_gate(events, barred), reference=T)
        o = DOCTRINES["effective_cause"](gg)
        notice_rows.append({"scenario": label, "eot_days": o.eot, "paid_days": o.compensable,
                            "contractor_bears_days": o.ld_days, "delay_damages_UGX_bn": ld_ugx(o.ld_days) / 1e9})
    N = pd.DataFrame(notice_rows)
    N.to_csv(OUT / "notice_scenarios.csv", index=False)
    L += ["Sub-Cl. 20.1 notice scenarios (actual-delay test): " + "; ".join(
        f"{r.scenario}: EOT {r.eot_days:.0f}, paid {r.paid_days:.0f}, damages UGX {r.delay_damages_UGX_bn:.1f} bn"
        for r in N.itertuples())]
    fig, ax = plt.subplots(figsize=(9, 3.6))
    rr.split_bars(ax, res, pv.vN, SHOW)
    ax.set_title(f"Package 5 (back-propagated): {pv.vN:.0f} days late, by legal approach", loc="left")
    ax.set_xlabel("days beyond 27 Apr 2022")
    fig.tight_layout()
    fig.savefig(PLOTS / "p5_doctrines.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    # --- XAI (a): Shapley attribution of the overrun over events ------------------------------
    rng = np.random.default_rng(SEED)
    ids = [e.id for e in events]
    phi = shapley_sampled(ids, g.v, 400, rng)
    base = lambda i: i.split("|")[0]
    agg = pd.Series(phi).groupby(lambda i: base(i)).sum()
    reg["shapley_days"] = reg.event_id.map(agg).round(1)
    reg["stand_alone_days"] = [round(g.v([i for i in ids if base(i) == b]), 1) for b in reg.event_id]
    gate_value = lambda S: DOCTRINES["effective_cause"](DelayGame(ap, [e for e in events if e.id in S],
                                                                  cache=g._cache, reference=T)).eot
    phi_gate = shapley_sampled(ids, gate_value, 120, np.random.default_rng(SEED + 7))
    reg["shapley_eot_gateway"] = reg.event_id.map(pd.Series(phi_gate).groupby(lambda i: base(i)).sum()).round(1)
    reg.to_csv(OUT / "event_register.csv", index=False)
    top = reg.sort_values("shapley_days", ascending=False)
    fig, ax = plt.subplots(figsize=(9, 0.33 * len(top) + 1.4))
    y = np.arange(len(top))
    ax.barh(y, top.stand_alone_days, color="none", edgecolor=MUTED, lw=1, label="delay if it happened alone")
    ax.barh(y, top.shapley_days, height=0.55, color=[EMP if p == "E" else CON for p in top.party],
            label="Shapley share of the 453-day overrun")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{a[:28]} · {gr[:20]}" for a, gr in zip(top.activity, top.group)], fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlabel("days beyond 27 Apr 2022")
    ax.set_title("Which slippages drive the overrun (blue Employer, orange Contractor)", loc="left", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(PLOTS / "p5_event_shapley.png", dpi=180)
    plt.close(fig)
    lead = top.iloc[0]
    L += [f"Shapley: '{lead.activity}' ({lead.group}) accounts for {lead.shapley_days:.0f} of {pv.vN:.0f} d; "
          f"Employer events {top.shapley_days[top.party == 'E'].sum():.0f} d, Contractor {top.shapley_days[top.party == 'C'].sum():.0f} d."]

    # --- XAI (b): ensemble of Package 5 variants ---------------------------------------------
    es0, ef0 = ap.forward()
    chain = [u for u in ("466", "467", "468", "469", "482", "483") if u in ap.tasks]
    rows = []
    n_var = 1500
    for k in range(n_var):
        sched = perturbed(ap, rng)
        evs = []
        pmap = dict(zip(reg.event_id, reg.p_employer))
        owner = {b: ("E" if rng.random() < p else "C") for b, p in pmap.items()}
        for e in events:
            b = e.id.split("|")[0]
            party = "N" if e.party == "N" else (owner[b] if e.party in ("E", "C") and b in owner else e.party)
            if e.party == "N" and owner.get(b) == "C":
                party = "C"
            evs.append(DelayEvent(e.id, party, e.activity, e.days * rng.triangular(0.8, 1, 1.2),
                                  e.start + rng.uniform(-15, 15)))
        p_bar = rng.uniform(0, 0.4)
        barred = [e.id for e in evs if e.party in ("E", "N") and rng.random() < p_bar]
        barred_days = sum(e.days for e in evs if e.id in barred)
        evs = apply_notice_gate(evs, barred)
        c_size, c_task, c_off = 0.0, None, 0.0
        if rng.random() < 0.6:  # hypothetical contractor productivity delay on the driving chain
            c_task = chain[int(rng.integers(len(chain)))]
            c_size = float(rng.integers(10, 241))
            c_off = float(rng.uniform(0, sched.tasks[c_task].duration))
            evs.append(DelayEvent("C_prod", "C", c_task, c_size, es0[c_task] + c_off))
        gg = DelayGame(sched, evs, reference=T)
        p = party_values(gg)
        o = {d: DOCTRINES[d](gg) for d in SHOW}
        eng = [o[d].eot for d in ENGLISH_READINGS if d in o] + [DOCTRINES["first_in_time"](gg).eot]
        emp_days = sum(e.days for e in evs if e.party == "E")
        con_days = sum(e.days for e in evs if e.party == "C")
        rows.append({
            "net_delay": p.vN, "employer_alone": p.vE, "contractor_alone": p.vC, "shared_days": p.overlap,
            "employer_slip_days": emp_days, "contractor_slip_days": con_days,
            "events_reassigned_to_contractor": float(sum(1 for b, o in owner.items()
                                                         if o == "C" and dict(zip(reg.event_id, reg.party))[b] == "E")),
            "time_barred_days": barred_days,
            "covid_days": sum(e.days for e in evs if e.party == "N"),
            "pavement_access_slip": sum(e.days for e in evs if e.party in ("E", "N") and e.activity == "WF_466"),
            "productivity_delay": c_size,
            "productivity_on": {"466": 1, "467": 2, "468": 3, "469": 4, "482": 5, "483": 6}.get(c_task, 0),
            "productivity_felt_vs_land": (es0[c_task] + c_off - min(e.start for e in evs if e.activity.startswith("WF_466")))
            if c_task else 0.0,
            "duration_scale": np.mean([sched.tasks[u].duration / ap.tasks[u].duration for u in chain]),
            "eot_gateway": o["effective_cause"].eot, "paid_gateway": o["effective_cause"].compensable,
            "ld_days_gateway": o["effective_cause"].ld_days, "eot_city_inn": o["city_inn"].eot,
            "eot_cyden": o["contractual_exclusion"].eot, "paid_gateway_money": o["effective_cause"].compensable,
            "english_spread": max(eng) - min(eng),
        })
        if k == 50:
            per = (time.time() - t0) / 51
    E = pd.DataFrame(rows)
    E.to_csv(OUT / "ensemble.csv", index=False)
    L += [f"Ensemble ({n_var} variants): extension under the actual-delay test median {E.eot_gateway.median():.0f} d "
          f"(P5-P95 {E.eot_gateway.quantile(.05):.0f}-{E.eot_gateway.quantile(.95):.0f}); contractor bears "
          f"{E.ld_days_gateway.quantile(.05):.0f}-{E.ld_days_gateway.quantile(.95):.0f} d; English readings differ by "
          f">14 d in {100 * (E.english_spread > 14).mean():.0f}% of variants; City Inn below the actual-delay test by "
          f">14 d in {100 * ((E.eot_gateway - E.eot_city_inn) > 14).mean():.0f}%."]

    import shap
    from sklearn.metrics import r2_score, roc_auc_score
    from sklearn.model_selection import train_test_split
    from xgboost import XGBClassifier, XGBRegressor
    feats = ["employer_slip_days", "contractor_slip_days", "events_reassigned_to_contractor", "pavement_access_slip",
             "productivity_delay", "productivity_on", "productivity_felt_vs_land", "duration_scale",
             "time_barred_days", "covid_days"]
    nice = {"employer_slip_days": "Employer access slippage (days, summed)",
            "contractor_slip_days": "Contractor slippage (days, summed)",
            "events_reassigned_to_contractor": "Workfronts that were the Contractor's",
            "pavement_access_slip": "Section 2 pavement access slip (days)",
            "productivity_delay": "Contractor productivity delay on driving chain (days)",
            "productivity_on": "Where that delay sits (sub base ... kerbing)",
            "productivity_felt_vs_land": "When it is felt vs pavement access (days)",
            "duration_scale": "Driving-chain duration scale",
            "time_barred_days": "Days lost for late notice (Sub-Cl. 20.1)",
            "covid_days": "Lockdown days (neutral, time only)"}
    targets = [("eot_gateway", "Extension of time, actual-delay test (days)"),
               ("paid_gateway", "Paid days (prolongation), actual-delay test"),
               ("ld_days_gateway", "Days the Contractor carries (delay damages)"),
               ("english_spread", "Gap between the English readings (days)")]
    summ = {}
    for tgt, title in targets:
        Xtr, Xte, ytr, yte = train_test_split(E[feats].rename(columns=nice), E[tgt], test_size=0.25, random_state=SEED)
        m = XGBRegressor(n_estimators=600, max_depth=5, learning_rate=0.04, subsample=0.9, random_state=SEED).fit(Xtr, ytr)
        r2 = r2_score(yte, m.predict(Xte))
        sv = shap.TreeExplainer(m)(Xte)
        summ[tgt] = r2
        plt.figure()
        shap.plots.beeswarm(sv, max_display=10, show=False)
        plt.title(f"{title}\n(Package 5 ensemble, test R² {r2:.2f})", fontsize=9.5)
        plt.tight_layout()
        plt.savefig(PLOTS / f"p5_shap_{tgt}.png", dpi=180)
        plt.close("all")
        pd.DataFrame({"feature": list(nice.values()), "mean_abs_shap": np.abs(sv.values).mean(0)}).sort_values(
            "mean_abs_shap", ascending=False).to_csv(OUT / f"shap_{tgt}.csv", index=False)
    yb = (E.english_spread > 14).astype(int)
    if 20 < yb.sum() < len(yb) - 20:
        Xtr, Xte, ytr, yte = train_test_split(E[feats], yb, test_size=0.25, random_state=SEED, stratify=yb)
        auc = roc_auc_score(yte, XGBClassifier(n_estimators=400, max_depth=4, learning_rate=0.05,
                                               random_state=SEED).fit(Xtr, ytr).predict_proba(Xte)[:, 1])
    else:
        auc = float("nan")
    # tipping point: contractor productivity delay vs extension and damages
    sub = E[E.productivity_delay > 0]
    bins = pd.cut(sub.productivity_delay, np.arange(0, 250, 20))
    tip = sub.groupby(bins, observed=True).agg(eot=("eot_gateway", "median"), ld=("ld_days_gateway", "median"),
                                               spread=("english_spread", "median"))
    tip.to_csv(OUT / "tipping_point.csv")
    fig, ax = plt.subplots(figsize=(8.5, 3.4))
    xs = [i.mid for i in tip.index]
    ax.plot(xs, tip.eot, "-o", color=EMP, ms=4, label="extension (actual-delay test), median")
    ax.plot(xs, tip.ld, "-o", color=CON, ms=4, label="days the Contractor carries, median")
    ax.plot(xs, tip.spread, "--", color=MUTED, label="gap between English readings, median")
    ax.set_xlabel("hypothetical contractor productivity delay on the pavement chain (days)")
    ax.set_ylabel("days")
    ax.set_title("Package 5: how much contractor delay it takes to change the answer", loc="left", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS / "p5_tipping_point.png", dpi=180)
    plt.close(fig)
    L += ["XAI surrogate fit (test R²): " + ", ".join(f"{k} {v:.2f}" for k, v in summ.items())
          + f"; screening AUC for 'English readings differ by >14 d': {auc:.2f}."]
    for tgt, _ in targets:
        s = pd.read_csv(OUT / f"shap_{tgt}.csv").head(3)
        L += [f"Top drivers of {tgt}: " + "; ".join(f"{f} ({v:.1f})" for f, v in zip(s.feature, s.mean_abs_shap))]
    L += [f"Runtime {time.time() - t0:.0f}s."]
    (OUT / "summary.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
