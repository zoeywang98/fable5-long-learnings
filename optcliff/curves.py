"""Probability curves from option mids, as specified:

    mid  = (bid + ask) / 2
    call: Prob(S_T > K) = (C(K) - C(K+dK)) / dK     (plotted at K)
    put:  Prob(S_T < K) = (P(K) - P(K-dK)) / dK     (plotted at K)

on n listed strikes above and below spot.
"""
from __future__ import annotations

from typing import List, Optional, Sequence

import pandas as pd

COLUMNS = ["side", "strike", "strike_pair", "dk", "bid", "ask", "mid", "bid_pair", "ask_pair", "mid_pair", "prob"]


def window(strikes: Sequence[float], spot: float, n: int, step: Optional[float] = None) -> List[float]:
    """n strikes at/below spot and n above, plus one more each side so every strike has a pair.
    With `step`, only strikes that are multiples of it are used (e.g. step=10 -> 200, 210, ...)."""
    ks = sorted(set(float(k) for k in strikes))
    if step:
        ks = [k for k in ks if abs(k / step - round(k / step)) < 1e-6]
    return [k for k in ks if k <= spot][-(n + 1):] + [k for k in ks if k > spot][:n + 1]


def curve(quotes: pd.DataFrame, strikes: Sequence[float], side: str) -> pd.DataFrame:
    """quotes: rows for one expiry and one side ("C"/"P") with strike, bid, ask."""
    q = quotes[quotes.strike.isin(strikes) & (quotes.ask > 0)].sort_values("strike")
    k, bid, ask = q.strike.tolist(), q.bid.tolist(), q.ask.tolist()
    mid = [(b + a) / 2 for b, a in zip(bid, ask)]
    rows = []
    for i in range(len(k) - 1):
        lo, hi = i, i + 1
        dk = k[hi] - k[lo]
        if side == "C":  # Prob(S_T > K) at the lower strike, paired with the next strike up
            at, pair, prob = lo, hi, (mid[lo] - mid[hi]) / dk
        else:            # Prob(S_T < K) at the upper strike, paired with the next strike down
            at, pair, prob = hi, lo, (mid[hi] - mid[lo]) / dk
        rows.append([side, k[at], k[pair], dk, bid[at], ask[at], mid[at], bid[pair], ask[pair], mid[pair], prob])
    return pd.DataFrame(rows, columns=COLUMNS)


def curves(chain: pd.DataFrame, expiry, spot: float, n: int = 10, step: Optional[float] = None) -> pd.DataFrame:
    """Call and put curves for one expiry."""
    ce = chain[chain.expiry == expiry]
    strikes = window(ce.strike.unique(), spot, n, step)
    return pd.concat([curve(ce[ce.cp == "C"], strikes, "C"), curve(ce[ce.cp == "P"], strikes, "P")],
                     ignore_index=True)
