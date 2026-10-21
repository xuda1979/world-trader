# HUNT_INDUSTRY48 — Ken French 48-industry RELATIVE momentum/carry (iter 6)

GOAL: find <=2 genuinely NEW decorrelated high-SR DAILY engines to help ann>=80%/SR>=5 at lev<=1.6.
This hunts CROSS-INDUSTRY relative time-series momentum on the 48 ken-french industry portfolios —
a distinct domain from the champion (single-commodity TSMOM, rates, FX, dualmom EQUITY-L/S on 12
portfolios). HUNT_FUNDAMENTAL tested industry/decile L/S SIZE-STYLE screens (dead); we test
RELATIVE TS-momentum among the 48 industries themselves with T+1 execution via real sector ETFs.

READ FIRST (dead-lists): campaign/results/DEAD_IDEAS.csv, campaign/GOAL100_FINAL_STATE.md.
DO NOT re-run: FF factor premia, size/value/growth/profitability screens, decile L/S, BAB, ivol.

## DATA (verify fail-closed spans first)
- tools/quant/data/kenfrench/48_Industry_Portfolios_Daily.csv — VALUE-WEIGHTED daily section
  (look for "Average Value Weighted Returns -- Daily", header row starts with ",Agric,...",
  rows "YYYYMMDD, v1..v48", divide by 100; -99.99 = missing -> drop/ffill only if safe). Daily
  through 2026-06-30 (202606 CRSP).
- EXECUTION INSTRUMENT / PRICE PATH (mandatory for trade-record audit): the 48 industries trade via
  real sector/industry ETFs. On disk: twelve_big/twelve_liq may have XLE/XLK/XLF/GLD etc; if a specific
  industry has no ETF, use its VW portfolio return series as SYNTH price (label price_source=SYNTH).
  State instrument+price_source per leg in FINDINGS.md.

## IDEA SLATE (build signal at t, trade T+1 close, vt10 trailing expanding cap 3)
1. Cross-industry relative momentum: rank 48 VW industries by trailing return (lb 21/63/126), long
   top-K short bottom-K, EW, T+1. Check corr<0.15 to GOAL100_HONEST14V3_BALANCED and to dualmom.
2. Industry momentum-minus-industry CARDS: long the industry with strongest 63d + short its 20d
   lagged self (time-series component) — a hybrid.
3. Industry breadth/lead-lag: use leader industry (e.g. cyclicals) 21d return to time laggard sectors.
4. Steepener/curve N/A here — keep to industries.

## GATES (ALL required)
SR_d >= 0.6 (2008+), H1>=0.3 AND H2>=0.3, <=2 neg yrs each > -5%, 200x 10d-BLOCK POSITION-LAG
scramble p<0.05 (NOT return-roll — degenerate), |corr|<0.15 to blend, ac1<0.5, uniqR>=0.08,
T+1 verified (extra lag probe), 6.4bps/side on turnover + vol-rebalance, borrow 0.5%/yr on shorts.
If nothing passes, log exact numbers + add dead families, do NOT force a sleeve.

## DELIVER
sleeves/*.csv (+ .meta with instrument/price_path/cost) + repro .py in scratch/ + FINDINGS.md
with per-idea gate card (exact numbers) + trade-record note (instruments+prices). Wrote only in
this dir. Last line exactly: HUNT_INDUSTRY48 DONE
