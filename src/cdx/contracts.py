"""Contract regimes: which attribution rule a standard form (plus governing law) points to.

Each regime returns an Outcome, or for FIDIC 2017 without a Special Provision a *range*
across the governing-law readings, because Sub-Clause 8.5 then leaves concurrency to the
tribunal ("as appropriate taking due regard of all relevant circumstances" per commentary).

Status of each mapping is recorded in REGIMES[...]["basis"]. Items marked VERIFY rest on
secondary commentary and must be checked against the contract text.
"""
from __future__ import annotations

from typing import Callable, Dict, Tuple

from .doctrines import (DOCTRINES, ENGLISH_READINGS, Outcome, city_inn, contractual_exclusion,
                        effective_cause, nec4_prospective)
from .game import DelayGame


def _range(game: DelayGame, keys) -> Tuple[Outcome, Outcome]:
    outs = [DOCTRINES[k](game) for k in keys]
    return min(outs, key=lambda o: o.eot), max(outs, key=lambda o: o.eot)


REGIMES: Dict[str, Dict] = {
    "jct_english": {
        "label": "JCT (unamended), English law",
        "rule": effective_cause,
        "basis": "No express concurrency term in JCT 2016/2024 (Fenwick Elliott Insight 102, 2026; VERIFY "
                 "against JCT 2024 text). English default: Walter Lilly para 370, Adyard paras 279-295, "
                 "Thomas Barnes paras 118, 148 (verified).",
    },
    "jct_cyden": {
        "label": "JCT amended with a Cyden clause",
        "rule": contractual_exclusion,
        "basis": "Clause 2.25.1.3(b) as quoted in North Midland v Cyden [2018] EWCA Civ 1744 para 6; "
                 "enforceable, paras 36, 39 (verified).",
    },
    "scots_law": {
        "label": "Scottish law (SBCC / JCT Scotland)",
        "rule": city_inn,
        "basis": "City Inn [2010] CSIH 68 apportionment (judgment text NOT yet verified).",
    },
    "nec4_ecc": {
        "label": "NEC4 ECC (prospective, clause 63.5)",
        "rule": nec4_prospective,
        "basis": "Compensation events assessed against the Accepted Programme at the dividing date; "
                 "time and money together (2019 amendment of 63.5; VERIFY clause text and practice note).",
    },
    "fidic1999_yellow_uganda": {
        "label": "FIDIC 1999 Yellow, no concurrency provision (Package 5)",
        "rule": effective_cause,
        "range": ENGLISH_READINGS,
        "basis": "1999 forms are silent on concurrency, so governing law decides. Laws of Uganda assumed "
                 "(VERIFY Appendix to Tender, Sub-Cl. 1.4); a common-law jurisdiction where English authority is "
                 "persuasive, so the actual-delay test is the central case and the English readings give the range. "
                 "Employer access failure: Sub-Cl. 2.1 gives time (8.4) plus Cost and reasonable profit; "
                 "notice within 28 days under Sub-Cl. 20.1 is a condition (not modelled). Confirmed by the user: "
                 "no Special Provision on concurrency; Employer responsible for site access and payment.",
    },
    "fidic2017_default": {
        "label": "FIDIC 2017 Sub-Cl. 8.5, no Special Provision",
        "range": ENGLISH_READINGS + ["city_inn"],
        "basis": "Sub-Cl. 8.5 refers concurrency to the Special Provisions; absent them, tribunal discretion "
                 "(commentary: Haynes Boone; Gowling WLG 2024; VERIFY wording). Modelled as the range of "
                 "governing-law readings.",
    },
    "fidic2017_sp_english": {
        "label": "FIDIC 2017 with an English-style Special Provision",
        "rule": effective_cause,
        "basis": "Special Provision adopting the actual-delay gateway; illustrative.",
    },
}


def evaluate_regimes(game: DelayGame) -> Dict[str, Dict]:
    out = {}
    for k, r in REGIMES.items():
        if "range" in r:
            lo, hi = _range(game, r["range"])
            out[k] = {"label": r["label"], "eot_lo": lo.eot, "eot_hi": hi.eot,
                      "paid_lo": lo.compensable, "paid_hi": hi.compensable, "net_delay": lo.net_delay}
            if "rule" in r:
                c = r["rule"](game)
                out[k].update({"eot_central": c.eot, "paid_central": c.compensable})
        else:
            o = r["rule"](game)
            out[k] = {"label": r["label"], "eot_lo": o.eot, "eot_hi": o.eot,
                      "paid_lo": o.compensable, "paid_hi": o.compensable, "net_delay": o.net_delay}
    return out
