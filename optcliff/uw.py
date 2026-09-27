"""Unusual Whales API client (https://api.unusualwhales.com/docs).

Token: env UW_API_TOKEN, else the UW_API_TOKEN line of the dotenv file named by OPTCLIFF_ENV_FILE
(default ~/.openclaw/.env). Only that one line is read, and the token is never logged or archived.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

BASE = "https://api.unusualwhales.com"
ENV_FILE = Path(os.environ.get("OPTCLIFF_ENV_FILE", "~/.openclaw/.env")).expanduser()
PAGE = 500  # API maximum
# OCC symbol: ROOT + YYMMDD + C/P + strike*1000 (8 digits). Adjusted roots (NVDA1...) do not match.
OCC = re.compile(r"^(?P<root>[A-Z]+)(?P<ymd>\d{6})(?P<cp>[CP])(?P<strike>\d{8})$")

try:
    from zoneinfo import ZoneInfo
    ET = ZoneInfo("America/New_York")
except Exception:  # pragma: no cover
    ET = None


def occ(symbol: str):
    """(root, expiry, "C"/"P", strike) or None."""
    m = OCC.match(symbol or "")
    if not m:
        return None
    ymd = m["ymd"]
    return m["root"], date(2000 + int(ymd[:2]), int(ymd[2:4]), int(ymd[4:])), m["cp"], int(m["strike"]) / 1000.0


def token(env_file: Path = ENV_FILE) -> str:
    tok = os.environ.get("UW_API_TOKEN", "").strip()
    if not tok and env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("export "):
                line = line[len("export "):]
            if line.startswith("UW_API_TOKEN="):
                tok = line.split("=", 1)[1].strip().strip("'\"")
                break
    if not tok:
        raise ValueError(f"缺少 UW_API_TOKEN（环境变量，或 {env_file} 里的 UW_API_TOKEN=）")
    return tok


def get(path: str, tok: str, retries: int = 3, **params) -> dict:
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{BASE}{path}" + (f"?{query}" if query else "")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}", "Accept": "application/json",
                                               "User-Agent": "optcliff/0.2"})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(2 ** attempt)
                continue
            detail = exc.read()[:200].decode("utf-8", "replace")
            if exc.code in (401, 403):
                raise ValueError(f"Unusual Whales 拒绝请求（HTTP {exc.code}）：检查 token 或订阅权限。{detail}") from exc
            raise ValueError(f"Unusual Whales {path} 失败（HTTP {exc.code}）：{detail}") from exc
    raise AssertionError("unreachable")


def fetch_bundle(symbol: str, choose: Optional[Callable[[List[date], date], List[date]]] = None) -> dict:
    """Stock state + expiry list + option contracts for the chosen expiries (all when choose is None)."""
    tok = token()
    sym = symbol.upper()
    fetched = datetime.now().astimezone().isoformat(timespec="seconds")
    state = get(f"/api/stock/{sym}/stock-state", tok).get("data") or {}
    breakdown = get(f"/api/stock/{sym}/expiry-breakdown", tok).get("data") or []
    listed = sorted({date.fromisoformat(r.get("expires") or r["expiry"]) for r in breakdown})
    if not listed:
        raise ValueError(f"Unusual Whales 没有 {sym} 的期权到期日")
    today = datetime.fromisoformat(fetched).date()
    wanted = choose(listed, today) if choose else listed
    contracts: Dict[str, list] = {}
    for exp in wanted:
        rows, page = [], 0
        while True:
            chunk = get(f"/api/stock/{sym}/option-contracts", tok, expiry=exp.isoformat(),
                        limit=PAGE, page=page).get("data") or []
            rows += chunk
            if len(chunk) < PAGE:
                break
            page += 1
        contracts[exp.isoformat()] = rows
    return {"source": "uw", "symbol": sym, "fetched_at": fetched, "state": state,
            "breakdown": breakdown, "contracts": contracts}


def fetch_history_bundle(symbol: str, day: date, choose: Callable[[List[date], date], List[date]],
                         strikes_for: Callable[[Sequence[float], float], List[float]], workers: int = 8) -> dict:
    """The chain as it closed on a past `day`: contracts listed that day, that day's regular-session
    close as spot, and each selected contract's row for `day` from its daily history (NBBO bid/ask)."""
    tok = token()
    sym, d = symbol.upper(), day.isoformat()
    root = sym.replace(".", "")
    listed: Dict[date, Dict[tuple, str]] = {}
    for s in get(f"/api/stock/{sym}/option-chains", tok, date=d).get("data") or []:
        p = occ(s)
        if p and p[0] == root:
            listed.setdefault(p[1], {})[(p[2], p[3])] = s
    if not listed:
        raise ValueError(f"Unusual Whales 没有 {sym} 在 {d} 的期权链")
    bars = get(f"/api/stock/{sym}/ohlc/1d", tok, date=d).get("data") or []
    regular = [b for b in bars if b.get("date") == d and b.get("market_time") == "r"]
    if not regular:
        raise ValueError(f"{sym} 在 {d} 没有正常交易时段收盘价（非交易日？）")
    spot = float(regular[0]["close"])

    jobs = []
    for exp in choose(sorted(listed), day):
        chain = listed[exp]
        for k in strikes_for(sorted({k for _, k in chain}), spot):
            jobs += [chain[(cp, k)] for cp in "CP" if (cp, k) in chain]

    def day_row(s: str) -> Optional[dict]:
        rows = get(f"/api/option-contract/{s}/historic", tok).get("chains") or []
        row = next((r for r in rows if r.get("date") == d), None)
        return dict(row, option_symbol=s) if row else None

    contracts: Dict[str, list] = {}
    with ThreadPoolExecutor(workers) as ex:
        for row in ex.map(day_row, jobs):
            if row:
                contracts.setdefault(occ(row["option_symbol"])[1].isoformat(), []).append(row)
    close = datetime(day.year, day.month, day.day, 16, 0, tzinfo=ET).isoformat()
    return {"source": "uw", "historical": True, "symbol": sym, "fetched_at": close,
            "state": {"close": spot, "tape_time": close},
            "breakdown": [{"expires": e.isoformat()} for e in sorted(listed)], "contracts": contracts}
