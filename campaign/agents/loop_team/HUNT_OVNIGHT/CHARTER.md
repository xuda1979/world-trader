# HUNT_OVNIGHT — overnight / gap-fade & intraday seasonality on liquid panel (iter 6)

PREMISE: The champion is built on TSMOM/carry/cross-asset daily CLOSE-to-CLOSE returns. NO sleeve
uses the OPEN vs CLOSE decomposition. Overnight (close-to-open) and intraday (open-to-close) returns
have well-documented regime differences (overnight drift in equities, gap-fade in commodity/ETF). A
decorrelated overnight/gap engine gives corr<0.15 potential. This hunts it on the 298-name twelve_big
panel (2006-2026, full OHLCV).

READ FIRST: campaign/results/DEAD_IDEAS.csv, campaign/GOAL100_FINAL_STATE.md.

## DATA
- tools/quant/data/twelve_big/ (298 names, columns date,open,high,low,close,vol; 2006-09..2026-08).
- oi_t = open_t/close_{t-1} - 1 (overnight); ic_t = close_t/open_t - 1 (intraday).
- Universe rows where both open_t and close_{t-1} valid.

## IDEA SLATE (signal at t close, trade t+1; T+1 VERIFIED; vt10 trailing expanding cap 3)
1. CROSS-SECTIONAL overnight-gap continuation: names with strong overnight moves yesterday keep
   moving next day (L/S), vs gap-FADE (contrarian). Try lb on overnight then trade next close.
2. Intraday-reversal cross-sectional: names with strong intraday realize (close>open big) revert
   next day.
3. Overnight-minus-intraday spread book: long names high (overnight - intraday), short names low.
4. Time-of-week x overnight: overnight return seasonality by weekday.
State mechanism BEFORE coding; drift-control (always-long/always-short) where a single asset.

## GATES
SR_d>=0.6 (2008+), H1/H2>=0.3, <=2 neg yrs each>-5%, 200x 10d-block POSITION-LAG scramble p<0.05,
|corr|<0.15 to GOAL100_HONEST14V3_BALANCED, ac1<0.5, uniqR>=0.08, T+1, 6.4bps/side, borrow 0.5%/yr.
twelve_big are real large caps: instrument=US equity, price path = twelve_big/NAME.csv open&close.

## DELIVER
sleeves/*.csv+meta + repro .py + FINDINGS.md gate cards + trade-record note (instruments+price).
Last line exactly: HUNT_OVNIGHT DONE
