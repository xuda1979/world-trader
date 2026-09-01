# E2_eventcal — event/calendar effects not yet tried (last untested calendar class)

Tried & dead: weekday (natgas only survivor), TOM, month-of-year, FOMC drift, bid-week,
weekday x report-season. UNTESTED classes:
1. QUADRUPLE WITCHING / OPEX week: third Friday of Mar/Jun/Sep/Dec + the week before.
   SPX book (long the week before quad-witching? or short?). 20y of dates computable
   from calendar rules (no data download needed — 3rd Friday rule).
2. Options-expiration-day vol: SPX returns on 3rd Friday vs other days, 2006+ (SPY twelve panel).
3. Treasury refunding cycle: refunding announcements (Feb/May/Aug, first Wed) — proxy:
   us10y synth TR around those windows. Dates computable from rule (first business Wed).
4. Turn-of-quarter institutional flows: SPX last 3 days of Mar/Jun/Sep/Dec vs first 3 of next
   month (window dressing flows) — long-only book.
5. Holiday effects: pre-holiday drift (day before market holiday, long SPX), post-holiday.
   NYSE holiday calendar rule-based (compute, no downloads).
6. Day-of-month S&P seasonality composite: combine any 2 passing micro-effects into one book.

SPX/SPY prices: tools/quant/data/twelvedata/SPY.csv (2006-09+), spy_early 1993-2005 in data_fred
(stitch if needed — document the splice!), vix_daily 1990+.
Gates per GOAL100_AGENT_BRIEF.md (SR>=1.0 net). Log in FINDINGS.md. Last line: ROUND 1 DONE
