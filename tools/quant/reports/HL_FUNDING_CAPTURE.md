# Hyperliquid Funding Capture — validation study (2026-08-16)

**Question** (strategic thesis Pillar 1+3 — *capacity-constrained DeFi structural
alpha*): is delta-neutral funding-rate capture on a DEX perp venue (Hyperliquid)
a real, durable, net-positive edge for a small-capacity operator who cannot
compete with institutional low-latency desks?

This is the **first validation backtest** of a live scanner (`tools/wt/*funding*`,
`hyperliquid_funding.py`) that only produced real-time signals — it had no
historical, cost-aware, significance-tested analysis. We do that here.

---

## 1. Data — what Hyperliquid's sandboxed mirror exposes (critical limitation)

The `/info fundingHistory` endpoint here returns **≤500 hourly funding rows per
coin** ending at a fixed 2023 cutoff, and **no perp/spot price series** for that
window. We pulled the available window for 14 coins:

| Group | Coins (window) |
|-------|----------------|
| 2023-05-12 → 06-25 | BTC ETH SOL DOGE SUI ARB OP AVAX |
| 2023-05→06-26 | LINK |
| 2023-06→08 | XRP, AAVE |
| 2023-10/11 | NEAR ADA |
| 2023-12-22 → 2024-01-12 | **WIF** (meme) |

**Consequence:** we can validate the *carry leg* (funding-persistence trading)
on a real, bounded, cost-aware basis — but **not** the `basis-drift` leg (perp
pricing converging to spot), which needs a price series we do not have. The
results below are the **carry-leg upper bound**, and are honest that basis risk
is unmeasured.

Artifacts: `tools/quant/hl_funding/data/fund_*.csv` (500 hourly funding rows ea),
`backtest_capture.py`, `backtest_portfolio.py`.

---

## 2. Mechanism — funding IS persistent (this is why the edge *could* exist)

Hourly-funding **lag-1 autocorrelation is high (0.67–0.91) across all 14 coins**.
Perp funding converges toward the basis only gradually, so extreme funding tends
to persist for many hours. A delta-neutral book that *rides* extreme funding to
reversion mechanically collects carry. This is a real structural property — and
is exactly the kind of "structural quirk that traditional financial models don't
map well to" the thesis points at. **The mechanism is real.**

Asymmetric persistence hint: after **deep-negative** funding (bottom decile),
going long collected next-6h carry positive in 9/12 coins (DOGE +0.10%, OP
+0.20%, SUI +0.23%, LINK +0.10%, WIF +0.91%), whereas after **strong-positive**
funding, shorting collected ~0 (mean-reverts fast). → tested a long-only variant.

---

## 3. Backtest — carry leg, cost-aware, null-tested

Rules (no lookahead; enter next hour after trigger):
- **R1 both-direction:** funding ≥ +e → short; ≤ −e → long; exit |funding| ≤ x.
- **R2 long-only** (motivated by §2): funding ≤ −e → long; exit funding ≥ x.
- Costs swept [15,30,60]bp round-trip (Hyperliquid perp + spot legs, taker + slip).
- **Null:** random entry/exit placement with identical position density, 1500
  shuffles, two-sided p on net carry. (Honest: at 1–30 positions/coin, this is
  the decisive test, not the headline ann-return.)

**Result — decisive NEGATIVE at these sample sizes:**

| Rule | total net | coins net>0 | coins p<0.15 |
|------|-----------|-------------|--------------|
| R1 both-direction | +19.8 | 6/14 | **1** (WIF p=0.02) |
| R2 long-only | +12.1 | 6/14 | **0** |

- **13 of 14 coins have p = 1.000** in R1 — observed net carry is *at or below
  the median random-entry null*. With 1–5 positions typical, entry costs
  dominate and nothing beats coin-flip.
- The entire positive total is driven by **WIF only**, and WIF (a memecoin,
  2023-12 launch-premium regime) had **69.6% of hours above the trigger with
  consecutive funding runs of 30–40h** — an extreme, rare, non-representative
  state. Its "significance" (p=0.02) in a sea of p=1.0 is **multiple-testing
  luck**, and it proves the opposite of a deployable edge: when carry is that
  lucrative the arb gets crowded instantly.
- R2 (long-on-negative), despite the persistence hint, is **worse** (0/14
  significant) — the hint does not clear the cost+noise bar.

---

## 4. Verdict (honest)

> **Do NOT deploy funding-capture on Hyperliquid on this evidence.** The carry
> *mechanism* is real and structurally the right sandbox for a small operator
> (capacity-constrained — mega-funds can't fit in DEX alts), but the available
> ~500-row/3-week historical window per coin is **statistically far too small**
> and **lacks a price series**, so we cannot reject "random entry + WIF luck"
> as the explanation. 13/14 coins p=1.0 is the ground truth.

**What would validate it** (and is the correct next step, gated on data):
1. **Multi-year** hourly funding + perp/spot price history for a large DEX alt
   universe (paid data tier — same gate that already blocks the CTA-futures and
   hourly-equity paths in this repo).
2. Then measure the **basis-drift leg** (the dominant unmodeled risk) and
   require walk-forward carry > costs with block-bootstrap p < 0.05 across many
   coins — the same bar the patio applies to every edge here.

**Consistency with repo discipline:** this joins the growing list of honestly
rejected / not-yet-validatable edges (hourly-equity XGB no-edge, bigmove
regime-gate backfire, reversal-blend rejection). The scan *signal* (live funding
watch) remains useful **informational** tooling, but is not a deployable alpha.

## Artifacts
- `tools/quant/hl_funding/data/fund_*.csv` — 14 coins x 500 hourly funding rows
- `tools/quant/hl_funding/backtest_capture.py` — single-coin carry backtest
- `tools/quant/hl_funding/backtest_portfolio.py` — multi-coin + null (1500 boot)
- `tools/quant/reports/hl_funding_capture.json`, `hl_funding_portfolio.json`
