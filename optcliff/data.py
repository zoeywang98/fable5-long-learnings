"""Fetch option chains from Unusual Whales and parse them into one table."""
from __future__ import annotations

import gzip
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Union

import pandas as pd

from . import uw
from .uw import ET


@dataclass
class Snapshot:
    symbol: str
    spot: float
    fetched: datetime                # US/Eastern
    last_trade: Optional[datetime]   # underlying's last trade, US/Eastern
    listed: List[date]               # every listed expiry
    chain: pd.DataFrame              # expiry, strike, cp, bid, ask, iv, oi, volume (fetched expiries only)
    historical: bool = False         # quotes are a past day's close (fetched = that day 16:00)


def _eastern(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    ts = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return ts.astimezone(ET).replace(tzinfo=None) if ts.tzinfo and ET else ts.replace(tzinfo=None)


def parse(bundle: dict) -> Snapshot:
    sym = bundle["symbol"]
    root = sym.replace(".", "")  # OCC roots drop the dot: BRK.B -> BRKB
    rows = []
    for exp_rows in bundle["contracts"].values():
        for c in exp_rows:
            p = uw.occ(c.get("option_symbol"))
            if not p or p[0] != root:
                continue
            rows.append({"expiry": p[1], "strike": p[3], "cp": p[2],
                         "bid": float(c.get("nbbo_bid") or 0), "ask": float(c.get("nbbo_ask") or 0),
                         "iv": float(c.get("implied_volatility") or 0),
                         "oi": float(c.get("open_interest") or 0), "volume": float(c.get("volume") or 0)})
    if not rows:
        raise ValueError(f"no option quotes for {sym}")
    state = bundle["state"]
    return Snapshot(symbol=sym, spot=float(state.get("close") or 0),
                    fetched=_eastern(bundle["fetched_at"]), last_trade=_eastern(state.get("tape_time")),
                    listed=sorted({date.fromisoformat(r.get("expires") or r["expiry"]) for r in bundle["breakdown"]}),
                    chain=pd.DataFrame(rows), historical=bool(bundle.get("historical")))


def save(bundle: dict, root: Union[str, Path]) -> Path:
    stamp = bundle["fetched_at"][:19].replace("-", "").replace(":", "").replace("T", "-")
    prefix = "hist-" if bundle.get("historical") else ""
    path = Path(root) / bundle["symbol"] / f"{prefix}{stamp}.json.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt") as f:
        json.dump(bundle, f)
    return path


def load(symbol: str, choose: Callable[[List[date], date], List[date]],
         archive: Optional[Union[str, Path]] = None, day: Optional[date] = None,
         strikes_for: Optional[Callable[[Sequence[float], float], List[float]]] = None) -> Snapshot:
    """Fetch the chosen expiries for `symbol` (live, or as they closed on a past `day`);
    optionally keep the raw response under `archive`."""
    if day is not None:
        bundle = uw.fetch_history_bundle(symbol, day, choose, strikes_for)
    else:
        bundle = uw.fetch_bundle(symbol.upper(), choose)
    if archive:
        save(bundle, archive)
    return parse(bundle)
