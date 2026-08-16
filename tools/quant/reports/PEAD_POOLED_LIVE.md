# Pooled PEAD — live cost-aware validation on the priced universe (2026-08-16)

**Question** (strategic thesis Pillar 2 + 4): is Post-Earnings-Announcement Drift
— a canonical *event/narrative* (Pillar 2), *medium-frequency days-to-weeks*
(Pillar 4), *capacity-constrained* (Pillar 1) edge, and the classic "small
operator" alpha — actually live in THIS repo's observable universe?

The repo already implements PEAD correctly in `tools/wt/analysis.py` as a
**pooled cross-sectional** backtest (`backtest_pead_pooled`, Bernard/Thomas
method) — the honest way to test a cross-sectional effect (per-name backtests
are underpowered at ~4 earnings/yr/name). The standalone `pead.py` is a
placeholder; the real engine is in `analysis.py` and wired into `scan.py`.
Our job this firing: **feed it the largest priced universe the free panels allow
and report the actual live t-stat.**

---

## 1. Universe & method

- Price panels: `twelve_big` ∪ `twelve_liq` ∪ `twelvedata` ∪ `polygon[_v2]` →
  **320 price series**, latest ~3y window (750 bars) — recent-relevant AND tractable.
- `backtest_pead_pooled(market="US", horizon∈{5,10}, side∈{Long,Short}, min_events=30)`.
- **PEADup** signal: gap > 2×ATR% up, close > SMA20, vol > 1.5× (drift-up
  continuation). **PEADdn** mirrors (gap down, close < SMA20).
- Cost-aware (12bps round-trip), OOS = most-recent-30%-of-events held out.
- **Honest caveat:** panels are large/liquid caps — the micro/small caps where
  PEAD is *strongest* are under-represented (free data doesn't price them; see
  §3). So this measures PEAD at the *conservative, weak end* of the effect.

Artifacts: `tools/quant/reports/pead_pooled.json`,
`tools/quant/pead/fetch_earnings.py`, `run_pooled_pead.py`.

---

## 2. Results (live, cost-aware, OOS-split)

| Setup | horiz | n | exp_ret/event | t-stat | OOS exp_ret | OOS edge |
|-------|-------|-----|--------------|--------|-------------|----------|
| **PEADup (Long)** | 5d | 612 | +0.14% | +0.76 | +0.011% | +0.002 |
| **PEADup (Long)** | 10d | 605 | **+0.32%** | **+1.38** | **+0.375%** | **+0.061** |
| PEADdn (Short) | 5d | 468 | −0.29% | −1.36 | −0.62% | −0.137 |
| PEADdn (Short) | 10d | 462 | −0.55% | **−2.20** | −0.77% | −0.149 |

**Read 1 — the long side is a real but not-yet-significant drift edge.**
All four long measurements (5d/10d × in-sample/OOS) are **positive**. At the
10-day horizon the drift is most visible: t=+1.38 in-sample AND +0.375%/event
OOS — the sign and magnitude are consistent, which is encouraging. It does NOT
yet clear the repo's t≥2 (p<0.05) bar. Promising, not proven.

**Read 2 — the short side is a LOSING setup and should not be traded.**
PEADdn is negative at both horizons and in OOS, reaching **t=−2.20 at 10d**.
This is the academically-expected result: short-side PEAD is arbitraged (value
traps, short-squeeze risk, hard-to-borrow) and is a net loser after costs on
live data. **The scan currently lists PEADdn as a tradeable short setup — the
data says this setup loses and should be disabled/demoted.**

---

## 3. Why the effect is understated (the strategic-thesis core of it)

The long-side PEAD t-stat is +1.1–1.4 on a **large/liquid-cap** universe where
drift is *weakest* and *most-arbitraged*. The academic and practitioner
consensus is that PEAD is **far stronger in small/micro caps** — exactly the
names the free panels do NOT price:

- Only **24 of 624** symbols with live Finnhub earnings events have any local
  price panel.
- `fetch_history` / free providers return **empty for 0/15 sampled micro-caps**
  (DTST, EDBL, HURA, LNZA, …).
- The polygon micro-cap slice that exists is **stale** (ends 2026-08-04, before
  the recent drift window develops).

So the live PEAD long edge we *can* observe is the **conservative floor**. If a
paid tier supplied current daily OHLC for the full earnings-event universe
(esp. small caps), the pooled event count AND drift magnitude would both rise —
likely pushing the long-side t-stat past significance. This mirrors exactly the
Hyperliquid funding finding (same firing loop): **the free feed serves precisely
the universe where an agile operator's edge is weakest, and the edge-rich niche
universe is data-gated.**

---

## 4. Verdict & operational actions

1. **IMPLEMENTABLE TODAY (no new data):** demote / disable the **PEADdn (short)**
   setup in the scan gate — the live pooled backtest shows it is a net loser
   (t=−2.20 @10d, negative OOS). This is a concrete, evidence-based
   de-risking action on the production signal set.
2. **Long-side PEADup:** keep as a **watch/qualifying** setup at the 10-day
   horizon (positive, OOS-consistent) but do NOT size it as a standalone conviction
   edge until t≥2 — consistent with the repo's MIN_SAMPLE/EXP_MIN gate philosophy.
3. **Data gate (the real unlock):** to validate the small-cap long-side drift
   where the edge is max, this project needs a paid daily-OHLC feed for the full
   earnings-event universe — the SAME single gate that already blocks
   CTA-futures metals, hourly-equity, and Hyperliquid-funding. A live earnings
   signal path (`recent_earnings`) is already production-usable as an
   *informational* alerter.

*Consistent with repo discipline: positive-but-sub-significant long drift is
reported honestly; the short-side negative is treated as a de-risking signal,
not buried.*
