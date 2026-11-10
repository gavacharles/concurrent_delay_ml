"""Case library for the doctrinal-fidelity suite.

Each case is a two-path reconstruction. `law_verified` / `facts_verified` record whether the
legal statement and the dates/durations were checked against the judgment text (National
Archives Find Case Law, 2026-11-10). Where a magnitude is an assumption or is worked back
from the outcome, `notes` says so. Passing a case shows consistency with the court's
reasoning, not an independent prediction of quantum.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence

from .game import DelayEvent, DelayGame
from .schedule import Schedule


@dataclass
class Case:
    key: str
    name: str
    citation: str
    court_eot: float
    court_compensable: Optional[float]
    events: Sequence[DelayEvent]
    path_a: float = 1000.0
    path_b: float = 1000.0
    jurisdiction: str = "England & Wales"
    day0: str = ""
    source: str = ""
    notes: str = ""
    law_verified: bool = False
    facts_verified: bool = False

    def game(self) -> DelayGame:
        return DelayGame(Schedule({"A": self.path_a, "B": self.path_b}), self.events)


def _E(i, act, days, start, w=1.0):
    return DelayEvent(i, "E", act, days, start, w)


def _C(i, act, days, start, w=1.0):
    return DelayEvent(i, "C", act, days, start, w)


CASES: Dict[str, Case] = {c.key: c for c in [
    Case(
        key="malmaison", name="Henry Boot v Malmaison", citation="(1999) 70 Con LR 32",
        court_eot=10, court_compensable=0,
        events=[_E("E1", "A", 10, 50), _C("C1", "B", 10, 50)],
        source="Dyson J para 13 as quoted in Walter Lilly para 367 and Adyard para 276: time for the period of "
               "delay caused by the relevant event despite a concurrent contractor cause; no money.",
        notes="Principle verified through later judgments quoting it; magnitudes illustrative.",
        law_verified=True,
    ),
    Case(
        key="adyard", name="Adyard v SD Marine", citation="[2011] EWHC 848 (Comm)",
        court_eot=0, court_compensable=0, day0="31 Mar 2009",
        events=[_C("C_progress", "B", 183, 0), _E("E_MCA", "A", 124, 81)],
        source="Paras 153 (delayed by at least 6 months by 31 Mar 2009), 185 (20 Jun 2009 letter), 210 (124 days "
               "claimed, Hull 11), 279 (concurrency test), 293-299 (no actual delay; claim fails).",
        notes="Contractor delay = 6 months from the Walker report date; employer event = the 124-day claim from the "
              "20 Jun 2009 letter. Both magnitudes are the parties' figures, not findings.",
        law_verified=True, facts_verified=True,
    ),
    Case(
        key="saga", name="Saga Cruises v Fincantieri", citation="[2016] EWHC 1875 (Comm)",
        court_eot=0, court_compensable=0, day0="2 Mar 2012 (reset SCD, para 233)",
        events=[_C("C_yard", "B", 14, -1), _E("E_stair", "A", 9, 0)],
        source="Paras 233 (SCD 2 Mar 2012), 287 (Yard delay 2-16 Mar), 310-313 (aft stair tower to 10/11 Mar), "
               "251 (concurrency must actually affect completion as then scheduled), 326(iv).",
        notes="The Yard's items were already late at the SCD; encoded as starting the day before (assumption).",
        law_verified=True, facts_verified=True,
    ),
    Case(
        key="walter_lilly", name="Walter Lilly v Mackay", citation="[2012] EWHC 1773 (TCC)",
        court_eot=507, court_compensable=507, day0="16 Feb 2007 (BLDA's extended date, para 387)",
        events=[_E("E_DMW", "A", 507, 0), _C("C_plaster", "B", 60, 30)],
        path_b=900.0,
        source="Paras 370 (City Inn inapplicable; full extension), 459 (contractor's plaster/lift issues had no "
               "impact), 457-460 (EOT to 7 Jul 2008), 658 (prolongation recovered).",
        notes="Contractor issue size illustrative (60 days on a path with float); 507 days = 16 Feb 2007 to 7 Jul 2008.",
        law_verified=True, facts_verified=True,
    ),
    Case(
        key="thomas_barnes", name="Thomas Barnes v Blackburn with Darwen", citation="[2022] EWHC 2598 (TCC)",
        court_eot=119, court_compensable=27, day0="23 Sep 2014",
        events=[_C("C_roof", "B", 92, 0), _E("E_AI18", "A", 119, 23)],
        source="Paras 118, 123, 129, 140, 148, 157.",
        notes="Dates from the judgment; contractor magnitude worked back (119 - 27 = 92).",
        law_verified=True, facts_verified=True,
    ),
    Case(
        key="city_inn", name="City Inn v Shepherd", citation="[2010] CSIH 68",
        court_eot=12.5, court_compensable=None, jurisdiction="Scotland",
        events=[_E("E1", "A", 20, 40), _C("C1", "B", 15, 45)],
        source="Secondary source only (2011 practitioner guide supplied by the user; judgment text not read): "
               "architect 4 weeks + adjudicator 5 weeks = 9 weeks, upheld by Lord Drummond Young (2007) and the "
               "Inner House (2010). Majority's five propositions: delay is a question of fact decided by common "
               "sense; a critical path analysis is not essential; a dominant cause governs; with no dominant cause, "
               "apportion fairly and reasonably. Lord Carloway rejected apportionment: look at the relevant "
               "event in isolation (equivalent to the as-planned impact rule).",
        notes="The guide gives no breakdown of the concurrent periods, so magnitudes stay illustrative and "
              "court_eot is the equal-culpability apportionment, testing mechanics only.",
    ),
    Case(
        key="cyden", name="North Midland v Cyden Homes", citation="[2018] EWCA Civ 1744",
        court_eot=0, court_compensable=0,
        events=[_E("E1", "A", 10, 50), _C("C1", "B", 10, 50)],
        source="Para 6 (clause 2.25.1.3(b) wording), 22-23, 36, 39 (clause enforceable). No delay facts in the "
               "judgment (para 9).",
        notes="Clause verified; Malmaison facts used to show its effect.",
        law_verified=True,
    ),
]}

# The operator a court's reasoning corresponds to.
COURT_OPERATOR = {
    "malmaison": "effective_cause",
    "adyard": "effective_cause",
    "saga": "effective_cause",
    "walter_lilly": "effective_cause",
    "thomas_barnes": "effective_cause",
    "city_inn": "city_inn",
    "cyden": "contractual_exclusion",
}
