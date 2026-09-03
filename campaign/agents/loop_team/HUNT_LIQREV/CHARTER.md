# HUNT_LIQREV — short-term reversal on the LIQUIDITY-FILTERED large-cap panel (iter 6)

PREMISE: prior EQMOM tested short-term reversal on the broad 298-name twelve_big panel and found
it SIGN-INVERTED (5d losers keep losing, SR -0.24..-0.02). This hunts the ~123-name twelve_liq
LIQUIDITY-FILTERED large caps (2006-09..2026-08, full OHLCV). A more-liquid universe has cleaner
microstructure; short-term reversal may behave differently, and shortability/costs differ. Same
for overnight-vs-intraday decomposition on this liquid panel.

READ FIRST: campaign/results/DEAD_IDEAS.csv, campaign/goal100_FINAL_STATE.md, and the EQMOM
negative in SKILL_ALPHAAGB_B/FINDINGS.md (P1/P2) so you don't blindly re-run the same grid.

## DATA
- tools/quant/data/twelve_liq/ (123 names, 2006-2026, OHLCV, columns date,open,high,low,close,vol).
- Normalize by 21d RV before ranking. Universe = names with >=4900 non-null rows.

## IDEA SLATE (signal at t close, trade t+1; vt10 trailing expanding cap 3; T+1 VERIFIED)
1. Cross-sectional short-term reversal: lb 1/2/3/5/10 daily return, tercile/decile L/S, EW within
   leg, vol-normalized. (EQMOM found inversion on twelve_big; here TRY both raw and vol-norm.)
2. Overnight vs intraday: sig = overnight return (open_t/close_{t-1}-1); long names with big
   overnight PGAP continuation, short fade. Distinct mechanism.
3. Intraday-reversal: sig = close_t/open_t - 1; short strong-intraday, long weak-intraday.
4. Liquidity-aware: add simple trailing dollar-vol filter (skip low-liquidity decile).
Report sign and SR for each; if sign is same-inverted as EQMOM across the board, that is a
clean negative — log it and STOP iterating (don't burn budget).

## GATES
SR_d>=0.6 (2008+), H1/H2>=0.3, <=2 neg yrs each>-5%, 200x 10d-block POSITION-LAG scramble p<0.05,
|corr|<0.15 to GOAL100_HONEST14V3_BALANCED, ac1<0.5, uniqR>=0.08, T+1, 6.4bps/side, borrow 0.5%/yr.
Shortability: twelve_liq names are all liquid large caps (mostly shortable at 0.5%/yr base; note any
hard-to-borrow). State instrument + price path (twelve_liq/NAME.csv close) per leg for trade-record.

## DELIVER
sleeves/*.csv+meta + repro .py + FINDINGS.md gate cards + trade-record note. Last line:
HUNT_LIQREV DONE
