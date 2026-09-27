"""Cliff detection and cross-expiry structure (LONG_ENGINE.md, Layer 4 / Rule Set 2).

A cliff is where the probability curve collapses, not where it is merely steep:
an ATM curve always falls fastest in absolute terms, so the detector scores each
adjacent out-of-the-money pair by its RELATIVE drop (prob falls to what fraction
of itself) and keeps only pairs whose starting prob is still meaningful
(>= min_before). The cliff strike is the last level the market still pays for.

Cross-expiry (short/mid/long):
    Migration Ratio = Current Cliff / Previous Cliff        (Layer 4)
    all cliffs within align_tol of each other -> strong stop
    cliffs strictly climbing with maturity    -> long-bull signature (calls)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import pandas as pd

from .expiries import Pick

VERDICTS = ("insufficient", "strong_stop", "migrating_out", "mixed")


@dataclass(frozen=True)
class Cliff:
    side: str           # "C" (upside boundary) / "P" (downside boundary)
    strike: float       # last strike the market still pays for
    beyond: float       # first strike past the collapse
    prob: float         # prob at `strike`
    prob_beyond: float  # prob at `beyond`
    drop: float         # prob - prob_beyond
    rel_drop: float     # drop / prob, the collapse score in [0, 1]


def find_cliff(curve: pd.DataFrame, side: str, spot: float,
               min_before: float = 0.10) -> Optional[Cliff]:
    """Steepest relative collapse on the OTM side of one expiry's curve, or None."""
    d = curve[curve.side == side].sort_values("strike")
    k, p = d.strike.tolist(), d.prob.tolist()
    cands = []
    for lo in range(len(k) - 1):
        hi = lo + 1
        if side == "C":  # upside: prob falls moving up through strikes >= spot
            at, past = lo, hi
            if k[at] < spot:
                continue
        else:            # downside: prob falls moving down through strikes <= spot
            at, past = hi, lo
            if k[at] > spot:
                continue
        if p[at] >= min_before and p[at] > p[past]:
            drop = p[at] - p[past]
            cands.append(Cliff(side, k[at], k[past], p[at], p[past], drop, drop / p[at]))
    return max(cands, key=lambda c: c.rel_drop) if cands else None


@dataclass(frozen=True)
class Structure:
    side: str
    cliffs: List[Tuple[Pick, Optional[Cliff]]]   # one entry per expiry, in order
    migration: List[Optional[float]]             # cliff[i].strike / previous found cliff
    verdict: str                                 # one of VERDICTS


def analyze(series: Sequence[Tuple[Pick, pd.DataFrame]], spot: float, side: str,
            align_tol: float = 0.02, min_before: float = 0.10) -> Structure:
    """Cliff per expiry plus migration ratios and the cross-expiry verdict.

    The effective tolerance is max(align_tol * spot, the strike grid step at the
    cliffs): the ladder cannot resolve differences finer than one strike apart.

    strong_stop:    every found cliff within the tolerance of the others
    migrating_out:  each later cliff beyond the previous by at least the tolerance
                    (higher for calls, lower for puts) -> long-bull signature on calls
    mixed:          cliffs found but neither aligned nor monotonic
    insufficient:   fewer than two expiries produced a cliff
    """
    cliffs = [(pick, find_cliff(df, side, spot, min_before)) for pick, df in series]
    migration: List[Optional[float]] = []
    prev = None
    for _, c in cliffs:
        migration.append(c.strike / prev if c and prev else None)
        if c:
            prev = c.strike
    found = [c for _, c in cliffs if c]
    ks = [c.strike for c in found]
    if len(ks) < 2:
        verdict = "insufficient"
    else:
        tol = max(align_tol * spot, max(abs(c.beyond - c.strike) for c in found))
        out = 1 if side == "C" else -1
        if max(ks) - min(ks) <= tol:
            verdict = "strong_stop"
        elif all((b - a) * out >= tol for a, b in zip(ks, ks[1:])):
            verdict = "migrating_out"
        else:
            verdict = "mixed"
    return Structure(side, cliffs, migration, verdict)


def table(structures: Sequence[Structure], symbol: str, spot: float) -> pd.DataFrame:
    """Flat per-expiry rows (both sides) for CSV output."""
    rows = []
    for s in structures:
        for (pick, c), ratio in zip(s.cliffs, s.migration):
            rows.append({"symbol": symbol, "spot": spot, "side": s.side, "label": pick.label,
                         "expiry": pick.expiry.isoformat(), "dte": pick.dte,
                         "cliff": c.strike if c else None, "beyond": c.beyond if c else None,
                         "prob": c.prob if c else None, "prob_beyond": c.prob_beyond if c else None,
                         "rel_drop": c.rel_drop if c else None, "migration_ratio": ratio,
                         "verdict": s.verdict})
    return pd.DataFrame(rows)
