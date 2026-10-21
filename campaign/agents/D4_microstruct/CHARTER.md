# D4_microstruct — cash-market microstructure II (natgas family extension)

The champion's newest engines are natgas weekday calendars (C5). Your mission: find the
NEXT cash-market microstructure engine with a real economic story.

DATA: tools/quant/data/newdata/ (DHHNGSP natgas, DCOILWTICO, DCOILBRENTEU, DHOILNYH heating
oil, DJFUELUSGULF jet, GASREGW retail gas weekly, DEX* fx, BAMLC0A0CM OAS) + data_fred
(xau, slv, copx copper ETF, spx, dow, brent, wti, natgas dup, copper_monthly, dxy).
Also: tools/quant/data/newdata/fomc_dates.csv (119 FOMC meetings 2008-2027).

IDEAS:
1. FOMC-day vol compression -> natgas/gold straddle-proxy books (gamma-scalp proxy:
   long underlying only AFTER FOMC vol event if trailing vol contracts). Honest test:
   does post-FOMC natgas weekday premium differ from non-FOMC weeks? (calendar x event)
2. Heating-oil seasonal switch (Sep 30 heating season / refinery switchover): long HO
   Oct-Feb, or HO-WTI spread seasonal window. Document the date convention a-priori.
3. Jet fuel post-Covid regime (2020+ short window — disclose) vs HO spread.
4. Copper-gold ratio (copx/xau) as growth/fear gauge: momentum 63d -> SPX gate; and
   copper-gold ratio REVERSION at 21d.
5. Retail-gasoline (GASREGW weekly) vs WTI crack: weekly z-reversion — C5 found SR 0.75
   for a version; test the spread with the CORRECT weekly alignment + Monday-open trades.
6. Natgas bid-week dynamics: last-3-business-days-of-month natgas behavior (bid-week
   roll economics) — long/short the last week vs first week, monthly.

All gates per GOAL100_AGENT_BRIEF.md. Log in FINDINGS.md. Last line: ROUND 1 DONE
