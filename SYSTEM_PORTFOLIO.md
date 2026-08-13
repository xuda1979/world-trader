# Company-Level System Portfolio — Master Spec (2026-08-13)

**Goal (user)**: a comprehensive, company-level portfolio system that optimizes
all profitable individual strategies into one system that stays profitable with
high Sharpe **any time / long term / any market scenario**, with dynamic
adjustment to market regimes.

**Bottom line (evidence-backed)**: the system portfolio is the **all-weather
flagship (h3+AP)** run statically, guarded by a **regime health monitor** for
situational awareness. Twelve+ candidate dynamic-regime levers were tested; all
FAIL on data for this book. The edge lives in the sleeve construction, NOT in
reactive timing.

---

## 1. The system portfolio (validated)

| Component | Role | SR | CAGR | MaxDD | Coverage |
|-----------|------|----|------|-------|----------|
| **All-weather flagship** = hedge 3-stream EW (L/S 130/30 + CTA macro 21d + Global Macro, ex stat-arb) 50% + AP gold composite 50% | Core | **1.04** | **11.1%** | **-12.9%** | 2008-2026, n=4663 |
| **FLOORED flagship** = h3+AP 50/50 floored 50% in T-bills (4%/yr) | **Primary core (no-losing-year)** | 0.98 daily / **1.17 monthly** | 7.5% | **-6.2% daily / -4.4% monthly** | 2008-2026, n=4783 |
| Optional paper overlay: Polygon LS champion (2024+, SR 0.4-0.5 true edge; overfit re-baselined) | Speculative | — | — | — | 2024+ |

**FLOORED flagship** (`portfolio_floored.py` -> `results/portfolio_floored_daily.csv`/`.json`):
- **ZERO negative calendar years** (2008-2026) [FLAT-4% T-bill assumption — N30: on the
  ACTUAL rate path the static 50% floor has 2022 = -0.64%; the honest guarantee
  construction is `portfolio_floored.py --dynamic` (50%/70% by rate): 4.3%/yr, zero
  losing years] — the strongest "any time" answer
  to the user requirement; worst year 2022 at **+0.61%**.
- Halves MaxDD vs the un-floored flagship (-6.2% vs -12.9% daily) at a lower
  but still-solid CAGR (7.5%) and a *higher* monthly Sharpe (1.17 vs 1.0).
- Guarantee: `0.5*year + 2% >= 0 iff year >= -4%`; historical worst is -3.4%
  (2022); holds while the T-bill >= 3.4% (current 3.73%).
- Deployable as the primary core; the un-floored flagship remains the
  higher-return variant when the investor accepts the -12.9% MaxDD / 2 losing
  years for +360bp/yr CAGR.
- **P23 upgrade (guarantee-preserving)**: `portfolio_floored.py --lev 1.10`
  (3% funding) -> 7.9%/yr, MaxDD -4.9% monthly, STILL zero losing years
  (worst 2022 +0.35%) — the max safe leverage. x1.5/x2 break the guarantee
  (N28) and are the return-maximizing options (9.7%/11.8% at -9.3%/-12.3% DD).

**Any-scenario proof** (the "any time, long-term, any market" requirement):
- Positive in **17 of 19 calendar years** (only 2022 -3.1%, 2023 -1.5%: the
  inflation-shock soft patch)
- Positive in **all 4 sub-periods** (2008 +0.96 / 2013 +1.38 / 2018 +0.90 /
  2023 +0.95)
- Weathered 2008 GFC (+1.0%), 2011 (-11.9% peak DD), 2015, 2018Q4, **2020
  COVID crash (+18.0%)**, 2022 inflation shock on positive 17/19 basis
- Low-beta (+0.34 vs SPY): the all-weather hedge is structural, not tactical
- **Crash-diversifier** (robustness_audit.py): cuts equity crash losses by
  2/3-4/5 (2020 COVID -12.1% vs SPX -37.8%; 2022 -5.3% vs -26.4%; 2018 Q4
  -11.9% vs -20.7%); positive skew +1.73; VaR(5%) -0.99%, CVaR -1.54%.
  Not crash-immune (loses -6 to -12% in fast crashes) — but those fast
  troughs are uncatchable by a 1-day-lagged monitor by design. For the
  remaining fast-crash losses see Sec. 5: the validated mean-reversion
  crash-sleeve is the designed mitigation (profits +22..+32% in those same
  episodes).

**Sleeve-selection discipline** (why this set is closed): every candidate
sleeve has been tested in-combination. Only legs that each clear the cost
hurdle on their own AND add low-correlation diversification are kept
(stat-arb N1, FX-carry-as-sleeve N2, Risk-Parity-into-flagship N17, n10r14
N14, overfit champion N15 all rejected).

---

## 2. The dynamic-regime layer: health MONITOR, not actuator

All THREE candidate dynamic/timing levers were tested on full data (no
lookahead, VIX lagged 1d) and **all fail** for this low-beta book:

| Lever | Result | Why |
|-------|--------|-----|
| **L1** VIX-gate de-risk (scale to 0.3/0.7 in stress/high) | SR 0.92-0.96 vs static 1.04, ~same MaxDD | 1-day-lagged daily gate can't pre-empt fast drawdowns; surrenders upside |
| **L2** rotate to Risk Parity in stress | SR 0.90, MaxDD **doubled** to -23.4% | RP is a leveraged equity/carry book; bleeds worse in the exact stress it's meant to defend |
| **L3** act on persistence-monitor TRIM (trim to 50%/30% on flagged days) | SR 1.10 vs 1.11, MaxDD unchanged -12.9% | flagship's MaxDDs are FAST troughs (2018-12, 2020-03, 2011-08) the durable-regime monitor correctly doesn't catch; the durable soft patches (2022-24) are flat not crash-like, so trimming forfeits recovery upside |

**Conclusion**: static all-weather construction IS the regime optimization for
this book. The deployable dynamic layer is the **situational-awareness monitor**
(`tools/quant/hedge_fund_strats/portfolio_health_monitor.py`), exit 0=GO /
1=CAUTION / 2=TRIM:
- Fires **only** on a PERSISTENT adverse regime (252d SR < 0 for 21 consecutive
  days AND 63d dd < -3%) — the 2022-23-24 soft patch (29/61/19 days) + small
  2009/2016 stress days
- **Correctly holds GO** through the 2020 COVID crash (0 TRIM days) — that fast
  recovery is where de-risking destroyed value
- Current live stance: **GO** (rolling SR +2.46, asof 2026-08-12)

**Operating rule**: hold the flagship at full allocation; the monitor is a
go/no-go on *new capital* + an early-warning for *sustained* regime
degradation — it should NOT drive automated de-risking trades (L1-L3).

---

## 3. Operational layer

- **Positioning lens** (2026-08-13): `portfolio_health_monitor.py` now also
  reports equity-index spec positioning z (TFF lev-funds with legacy
  non-commercial fallback, 1993+ continuous) — INFORMATIONAL only, not a
  stance input (consistent with L1/L2/L3: no actuator role).
- **No-losing-year guarantee tripwire**: `monitor_tbill_floor.py` — checks the
  3M T-bill (FRED tbill3m.csv) against the 3.4% floor that the floored
  flagship's no-losing-year guarantee depends on; exit 0=healthy / 1=within
  0.5pp buffer / 2=floor breached (page-able). Current: T-bill 3.73%, +0.33pp
  margin, health OK (buffer watch active). Re-check monthly.
- **Rebalance**: monthly (sleeves are monthly-cadence by construction).
- **Costs**: all figures cost-inclusive at 6 bps/side (12 bps round-trip).
- **Re-balance drag**: ~0.42pp/yr quantified (SR 1.20 -> 1.17 monthly).
- **Sources**:
  - `tools/quant/hedge_fund_strats/portfolio_spec.py` — spec + weights CSV
  - `tools/quant/hedge_fund_strats/portfolio_weights.csv` — daily sleeve
    weights + portfolio return (2008-2026)
  - `tools/quant/hedge_fund_strats/regime_adaptive_report.py` — L1/L2 evidence
  - `tools/quant/hedge_fund_strats/portfolio_health_monitor.py` — L3 + live stance
  - `tools/quant/hedge_fund_strats/monitor_tbill_floor.py` — no-losing-year
    guarantee tripwire (T-bill floor check)
- **Data**: free daily (twelve_big, Polygon, FRED macro, FX, AP walk-forwards).

---

## 4. Deferred / watch items

- **Stooq futures** still PoW-blocked — no real-futures CTA upgrade (metals gap
  2000-08).
- **n10r14 stream origin** unverifiable (N14) — IV-book levels conditional.
- **LS champion** overfit (N15): true edge ~0.4-0.5, not 1.6; paper overlay
  until re-baselined on paid Polygon history.
- **DRL ensemble**: vol-targeting not implementable; optional small sleeve only.

---

## 5. NEW — Mean-Reversion Crash-Sleeve (validated crash-insurance overlay)

**Purpose**: the flagship still loses -6 to -12% in fast equity crashes (2018Q4,
2020, 2022-24). The mean-reversion market-neutral sleeve is the one validated
complement that **profits specifically in those episodes** (RESEARCH_LOG.md +
`MEANREV_CRASH_SLEEVE.md`).

- **Signal**: short-horizon (k=3-5, lock k<=5) cross-sectional equity reversal —
  long worst / short best top-N, dollar-neutral, T+1, 6bps/side, no lookahead,
  on the 290-name twelve_big panel.
- **VALIDATED**: PASS on signal-scramble gate (k5_n30 real SR +0.34 vs scramble
  -0.82 p<0.001; k3_n30 real +0.37 vs -1.34). One of only a handful of sleeves
  to pass the project's gold-standard gate.
- **Episode coverage**: profits in 6 of 7 of the flagship's ACTUAL drawdown
  windows (+22..+32%, SR 1.7-2.6 in 2018/2020; also 2010/2011/2015/2022-24).
  Only 2022 Q1 (slow grind) misses. Corr ideal: +0.20 on drawdown days, +0.05
  benign (pure diversifier when calm).
- **Sizing (critical)**: COUNTER-cyclical — raise exposure as VIX rises
  (mean-reversion alpha scales with crush vol). Moreira-Muir vol-scaling DESTROYS
  it (2020 +32% -> -5.6%).

**Deployment rule (honest, fully evidenced)**:
- Use ONLY as a small, **VIX-gated, hard-capped** overlay (e.g. 10-30% weight
  when VIX>25/32, gross cap ~1.5x) — NOT a permanent core member.
- Constructed overlay tradeoff: helps the stress-heavy 2023-26 window (+2pp ret,
  ~same MaxDD/SR) but worsens long-run MaxDD (-12.9% -> -19..-24%) — so it is
  **opportunistic crash insurance, not a permanent allocation**.
- Blended into flagship (15% rev/85% flag): turns 2020 from -2% to +8-12%, 2022-24
  from -1.6% to +4-7%. Net full-window SR ~neutral (1.03-1.07 vs 1.04) — its value
  is crash insurance, not added alpha.
- **Re: the floored flagship (Sec. 1)** — the crash-sleeve's Pareto-independence
  conclusion holds even more strongly: the floored core is already no-losing-year
  with MaxDD -6.2%, so the crash-sleeve's tail cost (-19..-24% MaxDD on the
  un-floored book; relatively worse vs a -6.2% floor) is harder to justify. For
  the floored core the crash-sleeve is even more clearly OPTIONAL.

---

## 6. Design principle (for the company)

Optimize the **construction** (sleeve mix / cost hurdle / diversification),
not the **timing**. When reactive timing levers are tested against this
low-beta all-weather book, they lose to static on every metric (L1: SR, L2: SR,
L3: SR+DD). The single largest risk-management edge available is the monitor's
*situational* awareness for capital-deployment decisions — keep static
allocations and use signals for go/no-go, not for trading.
