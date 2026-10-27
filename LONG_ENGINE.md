# LONG_ENGINE.md

**Canonical specification for `claw-long`.**
This file is the single source of truth. If any other document, note, or code comment conflicts with this file, this file wins.

Source: *Olivia Signal V4.3 — Consensus Boundary, Tail Vitality & Repricing Framework*

---

## Mission

The objective is **NOT** to predict price.

The objective is to identify stocks where the option market is actively **expanding its imagination boundary** and continuously **repricing higher upside worlds**.

---

## Layer −1: Surface Integrity Check

**Purpose:** Determine whether the option surface can be trusted.

**Components:**

- Core Smoothness
- Expiry Consistency
- Strike Density
- Active Core Liquidity
- Quote Stability

**Surface Integrity Grades:**

| Grade | Reference structure |
|-------|---------------------|
| A     | MDB-type structure  |
| B     | DDOG-type structure |
| C     | NOW-type structure  |

---

## Layer 1: Consensus Boundary (Cliff)

A **Cliff** is a strike region where market willingness to pay for additional upside begins collapsing.

> **Cliff = Consensus Imagination Boundary.**

Not resistance. Not impossible. The market becomes increasingly unwilling to pay for higher-price worlds.

**Cliff Confluence:** multiple expirations collapsing in the same strike region.

---

## Layer 2: Good Tail Jaggedness

**Definition:** Surface Integrity Pass + Strong Cliff + jagged activity **only beyond the Cliff**.

Represents:

- narrative demand
- speculative demand
- tail liquidity
- positioning activity
- optionality demand

**Bad Tail Jaggedness:** jaggedness everywhere (ATM, ITM, OTM) usually reflects poor liquidity and quote instability.

---

## Layer 3: Tail Length

```
Tail Length = Highest Active Strike / Spot
```

Represents the distance of collective imagination.

---

## Layer 4: Cliff Migration

```
Migration Ratio = Current Cliff / Previous Cliff
```

---

## Event Types

### Event Type 1: Cliff Break

Spot > Consensus Boundary.

**Not Alpha by itself.**

### Event Type 2: Cliff Re-Anchoring

After a Cliff Break, a significantly higher Consensus Boundary is established.

Example: 236 Cliff → 400 Cliff.

### Event Type 3: Contest Zone

Persistent instability and disagreement across a wide strike region.

Associated with price discovery and dealer battles.

### Event Type 4: Ignition Structure

Requirements:

- Surface Integrity Pass
- Strong Consensus Boundary
- Good Tail Jaggedness
- Long Tail Length
- Cliff Migration

---

## Structure Classification

| Class       | Definition |
|-------------|------------|
| Weak        | Cliff only |
| Speculative | Tail only |
| Strong      | Cliff + Good Tail Jaggedness |
| Elite       | Surface Integrity + Cliff + Good Tail Jaggedness + Tail Length + Cliff Migration |

---

## Rule Set 1: Cliff Microstructure Attribution

When a **price-difference cliff** (a sharp collapse in adjacent call-spread value) appears, the usual causes are:

- **(a) Collar capping** — large capital is using that strike as the upper cap of a collar structure ("上沿封顶"), selling calls at that strike to finance downside protection.
- **(b) Dealer risk-control ceiling** — the strike marks a dealer's gamma/vega risk-control upper bound, so quotes above it are suppressed.
- **(c) Persistent OI structure** — large positions parked at that strike long-term (OI structure) cause calls in that region to be continuously sold and priced down.

Her original wording (为什么会出现 cliff):

- 大资金用某个行权价做 collar，把上方封顶；
- 做市商在该价位有 gamma/vega 风控上限；
- 长期挂着的大仓位（OI 结构）让这一带 call 一直被卖、价格被压低。

**Rule:** When the bid–ask spread is small, the price-difference (call-spread) curve can be used to **reverse-engineer where institutions want price to go**. A tight-spread cliff is an institutional intent signal, not noise.

---

## Rule Set 2: PM Spec — Risk-Neutral Probability Curve

### Setup

Use **three expiration periods** (option settlement dates) — short / mid / long. Example: **Feb 20 / Mar 20 / Jun 18**.

For each expiry (Feb / Mar / Jun):

1. Select a strike ladder: centered on spot, **±10 strikes** up and down.
2. For each strike, compute the call **mid = (bid + ask) / 2**.

### Probability extraction

For each strike K:

```
Prob(S_T > K) ≈ (C(K) − C(K+ΔK)) / ΔK
```

Example:

- C(200) = 6.0
- C(210) = 3.8

```
Prob(S_T > 200) ≈ (6.0 − 3.8) / 10 = 0.22   (22%)
```

Plot the resulting curve as price climbs strike by strike.

### Reading the curve

- **A cliff on this curve marks where the period likely ends** — that expiry's probable terminal zone for the move.
- **Continuity check:** compute the curve for short, mid, and long expiries and compare the cliffs across them.
  - If the cliffs across expiries are **consistent (aligned at the same region)** → that is a **strong stop**.
- **Puts are symmetric:** the same reverse calculation on puts gives the downside boundary for shorts.

### Cross-expiry relations (her table, original wording)

三条曲线一起看（1M / 3M / 6M，只取大交割日，如 2/20、3/20、6/18）：

| 三条曲线的关系 | 她的结论 | Meaning |
|----------------|----------|---------|
| 三条在同一位置出现 cliff | 强阻力，这轮行情大概率在此结束 | Cliffs aligned → strong resistance; this move most likely ends here |
| 远月 cliff 一个比一个高 | 长牛标的（"最棒的标的"） | Each farther expiry's cliff is higher → long-bull name ("the best name") |
| 远月 cliff 反而更低 | 短期炒作，游资拉一下（"柚子 pop up"） | Farther cliffs are lower instead → short-term hype, hot money pushing it up |
| 多个到期日 cliff 方向一致 | 不是游资，是有布局的资金 | Cliffs of several expiries move the same way → not hot money; positioned capital |
| 大交割日这种结构结束 | 指数一般会跌 | When this structure ends on a big settlement date → the index usually falls |

### Puts (看跌同理)

"我算 call 多，但 put 也许更有意义。做空都是布局好的。"某 put 出现 cliff，同到期日 put 曲线又陡起来 → put 被抢买、价格抬高 → 可以买 put。坑：大盘不好会干扰，所以她认为 put 方向更可靠。

("I compute calls more, but puts may matter more. Shorts are all pre-positioned." A put shows a cliff, then the same expiry's put curve turns steep again → puts are being bought up and their prices lifted → buying puts is indicated. Pitfall: a bad broad market interferes, which is why she considers the put direction more reliable.)

```
Prob(S_T < K) ≈ (P(K) − P(K−ΔK)) / ΔK
```

### Rolling (主力不是同一天建仓)

主力不是同一天建仓：赚了 2 月的就开 6 月的，往后滚。所以要每天自动算、持续跟踪从哪个到期日滚到哪个。

(Main money does not build in one day: having made money on February it opens June, rolling out. So compute automatically every day and keep tracking which expiry it rolls from and to.)

### Validity conditions

- **Wide spreads make the calculation inaccurate.** Only run this on **option-active names** (tight bid–ask, liquid chains). Original: 限制：买卖价差大就不准，只用于期权活跃的股票。
- When comparing the three expiry curves, if the **cliffs climb higher with longer expiry**, you MUST anchor the analysis on major settlement dates: **quad-witching (四巫日), 1-month, 3-month, 6-month**. Only major option settlement dates are meaningful; minor weeklies are not.

### Signal

Three expiry curves whose cliffs **migrate upward with maturity** (short < mid < long), on an option-active name, anchored to major settlement dates — this is the signature of a **long-bull candidate (长牛标的)**.

---

## Rule Set 3: IV / RV Regime (ZZ, 2026-10-27, original wording)

Read on the IV/RV chart with the stock price overlaid (`lengine/ivrv.py`: IV30, trailing 21-session RV, IV rank over 1 year, quad-witching ATM IV).

> iv低位向上走，rv大于iv向下走，是多头单腿ca行情。rv大于iv向上走，iv高位向上走空头行情
>
> 一轮上涨后iv超级高，然后拐头往下，rv开始往上。说明buy otm call力量用尽，随着到期都变想成sell call
>
> dark pool 期权call 结构 vanna dex都是看多的

- **IV low and rising, RV above IV and falling** → a bullish, single-leg (long) call regime.
- **RV above IV and rising, IV high and rising** → a bearish regime.
- **After a rally IV is extremely high, then turns down while RV starts rising** → the buy-OTM-call force is spent; as expiry approaches those calls effectively turn into sell calls. This holds even when dark pool, the option call structure, vanna and DEX all look bullish.

---

## Core Principle

A **Cliff** is where the market begins refusing to pay for higher-price worlds.

**Good Tail Jaggedness** is evidence that the market continues paying attention to those worlds anyway.

The strongest stocks repeatedly force the market to move that boundary higher while keeping the upside tail alive.
