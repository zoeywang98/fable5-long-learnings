"""Chart: call curve P(S_T > K) on the left, put curve P(S_T < K) on the right, one line per expiry."""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Union

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .data import Snapshot  # noqa: E402
from .expiries import Pick  # noqa: E402

SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
SERIES = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948")
LABEL = {"short": "短", "mid": "中", "long": "长"}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Hiragino Sans GB", "PingFang HK", "Arial Unicode MS", "DejaVu Sans"],
    "axes.unicode_minus": False,
})


def _style(ax, title: str, ylabel: str) -> None:
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(AXIS)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, labelsize=9, length=0, pad=4)
    ax.set_title(title, loc="left", fontsize=11.5, color=INK, pad=8)
    ax.set_ylabel(ylabel, fontsize=9.5, color=INK2)
    ax.set_xlabel("行权价 K", fontsize=9.5, color=INK2)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")


def plot(snap: Snapshot, series: List[Tuple[Pick, pd.DataFrame]], path: Union[str, Path]) -> Path:
    fig, (ax_c, ax_p) = plt.subplots(1, 2, figsize=(15, 6.8), dpi=110, facecolor=SURFACE)
    fig.subplots_adjust(left=0.055, right=0.985, top=0.80, bottom=0.10, wspace=0.12)
    _style(ax_c, "call：Prob(S_T > K) = (C(K) - C(K+ΔK)) / ΔK", "P(S_T > K)")
    _style(ax_p, "put：Prob(S_T < K) = (P(K) - P(K-ΔK)) / ΔK", "P(S_T < K)")
    for i, (pick, df) in enumerate(series):
        color = SERIES[i] if i < len(SERIES) else MUTED
        prefix = f"{LABEL[pick.label]} " if pick.label in LABEL else ""
        label = f"{prefix}{pick.expiry.isoformat()}（{pick.dte}d）"
        for ax, side in ((ax_c, "C"), (ax_p, "P")):
            d = df[df.side == side].sort_values("strike")
            ax.plot(d.strike, d.prob * 100, color=color, lw=2, marker="o", ms=5, mfc=color, mec=SURFACE,
                    mew=1.2, label=label, zorder=3)
    for ax in (ax_c, ax_p):
        ax.axvline(snap.spot, color=INK2, lw=1, alpha=0.6, zorder=1)
        ax.annotate(f"现价 {snap.spot:.2f}", xy=(snap.spot, 1.0), xycoords=("data", "axes fraction"),
                    xytext=(5, -13), textcoords="offset points", fontsize=9, color=INK2)
    if snap.historical:
        when = f"{snap.fetched.date().isoformat()} 收盘（历史）"
    else:
        quote = snap.last_trade.strftime("%Y-%m-%d %H:%M") if snap.last_trade else "?"
        when = f"正股最后成交 {quote} ET · 取数 {snap.fetched.strftime('%Y-%m-%d %H:%M')} ET"
    fig.text(0.055, 0.945, f"{snap.symbol} · 期权价差概率曲线", fontsize=17, fontweight="bold", color=INK)
    fig.text(0.055, 0.905, f"现价 {snap.spot:.2f} · {when} · Unusual Whales NBBO · mid = (bid+ask)/2",
             fontsize=10, color=INK2)
    fig.legend(*ax_c.get_legend_handles_labels(), loc="upper left", bbox_to_anchor=(0.05, 0.885),
               ncol=max(len(series), 1), frameon=False, fontsize=9.5, labelcolor=INK2)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)
    return path
