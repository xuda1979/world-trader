# C3_positioning — COT/TFF positioning + intraday micro (NEW DOMAIN)

Mission: extract alpha from trader positioning (weekly CFTC COT since 2006) + the 17-name
polygon intraday panel. Pass ALL gates.

IDEAS (in order):
1. Money-manager net positioning extremes (z-score per market over 52w) as contrarian signal
   for the UNDERLYING price (wti, brent, natgas, gold, silver, copper/copx, spx, dow, 10y, fx).
   Signal from report_date; trade next session (T+1). Only weekly position changes -> tiny turnover.
2. Spec Net positioning momentum: follow large-spec trend when z in middle, fade at extremes.
3. TFF (leveraged funds vs asset managers) spread positioning for equity idx/rates/FX futures.
4. Open-interest change z-score x price change = confirmation/divergence signals.
5. Intraday (17 names, 5-min bars 2024+): overnight-vs-intraday return decomposition,
   first-hour momentum fading — only if SR >= 1.0 on the SHORT 2024+ window is honestly
   reported with the short-window caveat (yearly gate needs >= 5 yrs — intraday sleeves can
   only qualify via documented exception; prefer COT ideas first).
6. Combine 1-4 across markets into one composite sleeve (EW of per-market books, vol-normalized).

NOTES:
- cot_tidy.csv columns: date,market,contract_code,oi,m_money_long,m_money_short,swap_long,
  swap_short,report_date,spec_net,spec_long_pct,spec_short_pct.
- Map markets to price files: WHEAT->? (no wheat price on disk: SKIP), CRUDE OIL WTI->wti,
  BRENT->brent, NATURAL GAS->natgas, GOLD->xau, SILVER->slv, COPPER->copx,
  E-MINI S&P / S&P->spx, 10Y US TREASURY->us10y, JAPANESE YEN->jpy, EUR->eur, etc.
  If no price series on disk for a market: DO NOT use it (no synthetic prices).
- Positioning data is weekly (Tuesdays, published Fri/Mon) — align carefully, avoid lookahead:
  signal at report_date t usable at t+1 session OPEN at earliest; being generous, trade close t+1.

HONESTY: All gates in GOAL100_AGENT_BRIEF.md.
