"""Pick the 'big' expiries: short ≈ 1 month, mid ≈ 3 months, long ≈ 6 months.

Only standard monthlies count (third Friday, or the Thursday before when that Friday is
an exchange holiday, e.g. Juneteenth 2026 -> Jun 18). Mid/long prefer the big cycle
months (Mar/Jun/Sep/Dec + January LEAPS). From 2026-01-20 this reproduces the spec's
own example: Feb/20, Mar/20, Jun/18.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, List, Optional, Sequence

BIG_MONTHS = {1, 3, 6, 9, 12}
LABELS = ("short", "mid", "long")


@dataclass(frozen=True)
class Pick:
    label: str
    expiry: date
    dte: int
    big: bool


def third_friday(year: int, month: int) -> date:
    d = date(year, month, 15)
    return d + timedelta(days=(4 - d.weekday()) % 7)


def monthly_expiries(listed: Iterable[date]) -> List[date]:
    have = set(listed)
    out = []
    for y, m in sorted({(d.year, d.month) for d in have}):
        f = third_friday(y, m)
        if f in have:
            out.append(f)
        elif f - timedelta(days=1) in have:  # holiday-shifted monthly
            out.append(f - timedelta(days=1))
    return out


def _label(i: int, n: int, target: int) -> str:
    return LABELS[i] if n == 3 else f"{target}d"


def pick_expiries(listed: Iterable[date], today: date,
                  targets: Sequence[int] = (30, 90, 180), min_dte: int = 7) -> List[Pick]:
    monthlies = [d for d in monthly_expiries(listed) if (d - today).days >= min_dte]
    picks: List[Pick] = []
    prev = today
    for i, t in enumerate(targets):
        cands = [d for d in monthlies if d > prev]
        if not cands:
            break
        pool = cands
        if i > 0:
            big = [d for d in cands
                   if d.month in BIG_MONTHS and 0.5 * t <= (d - today).days <= 1.75 * t]
            pool = big or cands
        best = min(pool, key=lambda d: abs((d - today).days - t))
        picks.append(Pick(_label(i, len(targets), t), best, (best - today).days,
                          best.month in BIG_MONTHS))
        prev = best
    return picks


def explicit_expiries(dates: Sequence[date], today: date,
                      listed: Optional[Iterable[date]] = None) -> List[Pick]:
    have = set(listed) if listed is not None else None
    dates = sorted(set(dates))
    picks = []
    for i, d in enumerate(dates):
        if have is not None and d not in have:
            raise ValueError(f"expiry {d} is not listed")
        dte = (d - today).days
        picks.append(Pick(_label(i, len(dates), dte), d, dte, d.month in BIG_MONTHS))
    return picks
