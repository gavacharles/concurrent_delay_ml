"""Notice gates: claims lost for want of notice.

FIDIC 1999 Sub-Clause 20.1: the Contractor must give notice "as soon as practicable, and not later
than 28 days after the Contractor became aware, or should have become aware, of the event or
circumstance"; otherwise the Time for Completion is not extended and no additional payment is due.
English courts treat this as a condition precedent (Obrascon Huarte Lain v Gibraltar [2014] EWHC
1028 (TCC), as commonly reported; VERIFY), subject to arguments on the prevention principle.

Modelled as a transformation: an employer or neutral event whose notice was not given in time is
treated as the Contractor's risk for both time and money.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Iterable, List

from .game import CONTRACTOR, EXCUSABLE, DelayEvent


def apply_notice_gate(events: Iterable[DelayEvent], late_or_missing: Iterable[str]) -> List[DelayEvent]:
    barred = set(late_or_missing)
    return [replace(e, party=CONTRACTOR) if (e.id in barred and e.party in EXCUSABLE) else e for e in events]
