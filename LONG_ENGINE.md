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

### Validity conditions

- **Wide spreads make the calculation inaccurate.** Only run this on **option-active names** (tight bid–ask, liquid chains).
- When comparing the three expiry curves, if the **cliffs climb higher with longer expiry**, you MUST anchor the analysis on major settlement dates: **quad-witching (四巫日), 1-month, 3-month, 6-month**. Only major option settlement dates are meaningful; minor weeklies are not.

### Signal

Three expiry curves whose cliffs **migrate upward with maturity** (short < mid < long), on an option-active name, anchored to major settlement dates — this is the signature of a **long-bull candidate (长牛标的)**.

---

## Core Principle

A **Cliff** is where the market begins refusing to pay for higher-price worlds.

**Good Tail Jaggedness** is evidence that the market continues paying attention to those worlds anyway.

The strongest stocks repeatedly force the market to move that boundary higher while keeping the upside tail alive.
