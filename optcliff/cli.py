"""Command line: python3 -m optcliff NVDA AAPL ..."""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import List, Optional

import pandas as pd

from . import cliffs, data
from .curves import curves, liquidity, window
from .expiries import Pick, explicit_expiries, pick_expiries

PROJECT = Path(__file__).resolve().parent.parent

VERDICT_CN = {"insufficient": "cliff 不足两条，无法判断",
              "strong_stop": "三线 cliff 一致 → 强 stop",
              "migrating_out": "cliff 随期限外移",
              "mixed": "cliff 不一致（无结构）"}


def _picks(a: argparse.Namespace, listed: List[date], today: date) -> List[Pick]:
    if a.expiries:
        return explicit_expiries([date.fromisoformat(s.strip()) for s in a.expiries.split(",")], today, listed)
    return pick_expiries(listed, today, [int(t) for t in a.targets.split(",")])


def run_symbol(sym: str, a: argparse.Namespace) -> None:
    snap = data.load(sym, choose=lambda listed, today: [p.expiry for p in _picks(a, listed, today)],
                     archive=a.archive or None, day=a.date,
                     strikes_for=lambda strikes, spot: window(strikes, spot, a.tiers, a.step))
    picks = _picks(a, snap.listed, snap.fetched.date())
    if not picks:
        raise ValueError("no standard monthly expiries found")
    series = [(p, curves(snap.chain, p.expiry, snap.spot, a.tiers, a.step, a.max_spread)) for p in picks]
    liq = [liquidity(snap.chain, p.expiry, snap.spot, a.tiers, a.step, a.max_spread) for p in picks]
    structs = [cliffs.analyze(series, snap.spot, side, a.align_tol, a.min_prob) for side in "CP"]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    step = f"_step{a.step:g}" if a.step else ""
    exps = "_" + "-".join(p.expiry.strftime("%y%m%d") for p in picks) if a.expiries else ""
    stem = str(out / f"{snap.symbol}_{snap.fetched.date().isoformat()}{step}{exps}")  # not with_suffix: BRK.B has a dot
    table = pd.concat([df.assign(symbol=snap.symbol, expiry=p.expiry.isoformat(), dte=p.dte) for p, df in series],
                      ignore_index=True)
    table[["symbol", "expiry", "dte"] + [c for c in table.columns if c not in ("symbol", "expiry", "dte")]] \
        .to_csv(stem + ".csv", index=False, float_format="%.6g")
    cliffs.table(structs, snap.symbol, snap.spot).to_csv(stem + "_cliffs.csv", index=False, float_format="%.6g")
    if not a.no_plot:
        from .plot import plot  # matplotlib only when charting
        plot(snap, series, stem + ".png", structs)

    print(f"{snap.symbol} 现价 {snap.spot:.2f} · 到期 " + " · ".join(f"{p.expiry}（{p.dte}d）" for p in picks))
    for p, l in zip(picks, liq):
        note = "" if l["quotes"] and l["usable"] / l["quotes"] >= 0.8 else " ⚠ 有效报价不足，结果可能不准"
        print(f"  {p.expiry} 报价 {l['usable']}/{l['quotes']} 可用 · 中位相对价差 {l['median_rel_spread']:.1%}{note}")
    for s in structs:
        name = "call 上沿" if s.side == "C" else "put 下沿"
        parts = []
        for (p, c), r in zip(s.cliffs, s.migration):
            if c:
                parts.append(f"{p.expiry.strftime('%m/%d')} @ {c.strike:g}（{c.prob:.0%}→{c.prob_beyond:.0%}"
                             + (f"，迁移比 {r:.3g}" if r else "") + "）")
            else:
                parts.append(f"{p.expiry.strftime('%m/%d')} 无")
        verdict = VERDICT_CN[s.verdict]
        if s.verdict == "migrating_out":
            verdict += "（向上，长牛标的特征）" if s.side == "C" else "（向下）"
        print(f"  {name} cliff：" + " · ".join(parts) + f" → {verdict}")
    print(f"→ {stem}.csv / {stem}_cliffs.csv" + ("" if a.no_plot else f" / {stem}.png"))


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="optcliff", description="期权价差概率曲线：Unusual Whales 取数 + 画图")
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--expiries", help="YYYY-MM-DD,... (default: big monthlies near --targets days)")
    ap.add_argument("--targets", default="30,90,180", help="target days to expiry (default 30,90,180)")
    ap.add_argument("--date", type=date.fromisoformat, help="as of a past day's close, YYYY-MM-DD (default: now)")
    ap.add_argument("-n", "--tiers", type=int, default=10, help="strikes above and below spot (default 10)")
    ap.add_argument("--step", type=float, help="only use strikes that are multiples of this (e.g. 10)")
    ap.add_argument("--max-spread", type=float, default=0.15,
                    help="drop quotes with (ask-bid)/mid above this (validity condition, default 0.15; 0 disables)")
    ap.add_argument("--min-prob", type=float, default=0.10,
                    help="cliff detection: prob at the cliff strike must still be at least this (default 0.10)")
    ap.add_argument("--align-tol", type=float, default=0.02,
                    help="cliffs within this fraction of spot count as aligned (default 0.02)")
    ap.add_argument("--out", default=str(PROJECT / "out"))
    ap.add_argument("--archive", default=str(PROJECT / "data" / "snapshots"),
                    help="keep raw API responses here ('' to disable)")
    ap.add_argument("--no-plot", action="store_true")
    a = ap.parse_args(argv)
    if a.tiers < 1 or (a.step is not None and a.step <= 0):
        ap.error("--tiers must be >= 1 and --step > 0")
    if a.max_spread <= 0:
        a.max_spread = None  # disabled

    failed = 0
    for sym in a.symbols:
        try:
            run_symbol(sym, a)
        except Exception as exc:  # keep going through the list
            failed += 1
            print(f"{sym}: 失败 — {exc}", file=sys.stderr)
    return 1 if failed == len(a.symbols) else 0
