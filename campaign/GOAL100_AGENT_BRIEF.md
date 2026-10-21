# GOAL100 CAMPAIGN BRIEF (C-series agents)

## MISSION
Goal: 20-year (2006-2026, min 2008 start OK) backtest, **ann return >= 100%**, SR >= 2,
MaxDD <= 8%, NO leverage (weights sum to 1), 6 bps one-side costs, free data, OOS mandatory.
Prior best: COORD_FINAL 43.2% ann @ MaxDD -7.5% (14 sleeves). To approach 100% we need MANY
MORE genuinely decorrelated high-SR engines (like brwt Brent-WTI SR 2.5) from NEW data domains.

## HONESTY CONTRACT (violations = sleeve rejected)
1. No lookahead: signal at t uses data <= t; trade at t+1 (T+1 execution).
2. Costs: subtract 6 bps x one-side turnover per day (harness.data.apply_cost semantics).
3. Gates (ALL required, else do NOT save — log in FINDINGS.md with exact numbers):
   a) FULL-window net SR >= 1.0 after costs (NEW engines must be strong; weaker ones won't move the frontier)
   b) param-plateau: chosen params on plateau (neighbors within 20% of peak SR)
   c) halves: H1 SR >= 0.5 AND H2 SR >= 0.5
   d) yearly: <= 2 negative years, each > -5%
   e) signal-scramble 200x: real SR > 95th pctile of scrambled
   f) NEW-DOMAIN decorrelation: |corr| < 0.15 to the CURRENT BLEND (see sleeve_pool paths below);
      if 0.15-0.35 still save but mark "corr_ok_secondary"
   g) vol-target ~10% ann using ONLY trailing expanding window (min 60d), scale clip <= 3.0
   h) economic rationale (2-3 sentences) in .meta
4. Save per contract: `campaign/scripts/{name}.py` (reproducible), sleeve CSV
   `campaign/agents/<AGENT>/sleeves/{name}.csv` [date, ret] + `{name}.csv.meta`.
5. Do not modify other agents' dirs. Log in your own LOG/FINDINGS.
6. Be honest: failed gates -> FINDINGS.md entry with numbers, next idea. Iterate quickly.

## DATA (all free, on disk; canonical paths)
- NEW: Ken French daily portfolios (1926+, % returns, -99.99=missing):
  /Users/daxu/software/world-trader/tools/quant/data/kenfrench/
    48_Industry_Portfolios_Daily.csv (VW from line 10, EW from line 26288; header row starts with ",Agric,...")
    49_Industry_Portfolios_Daily.csv, 25_Portfolios_5x5_Daily.csv,
    10_Portfolios_Prior_12_2_Daily.csv, 6_Portfolios_2x3_Daily.csv, Portfolios_Formed_on_ME_daily.csv
  Parse: read lines, find "Average Value Weighted Returns -- Daily" section, next line = header,
  then rows "YYYYMMDD, v1, v2, ...". Divide by 100. NOTE: portfolio-level returns are treated as
  tradeable via sector/size ETFs (6bps realistic). -99.99 rows must be dropped/nan-filled.
- NEW: Full US Treasury curve (FRED, daily, percent):
  /Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred/
    DGS1MO(2001+) DGS3MO DGS6MO DGS1 DGS2(1976+) DGS3 DGS5 DGS7 DGS10 DGS20 DGS30(us10y alias too)
    T10YIE(5y BE 2003+) T5YIE T5YIFP DFII10(real yield), hy_oas, baa, aaa, t10y2y
    au10y ca10y ch10y ez10y gb10y jp10y nz10y (international 10y, for cross-rate engines)
- NEW: COT / TFF positioning (weekly, 2006+):
  /Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_cot/
    cot_tidy.csv (commodities: spec_net, money_manager longs/shorts, swap, oi per market+week)
    tff_tidy.csv (financial futures: FX, equity idx, rates), legacy_tidy.csv
  ONLY trade markets whose PRICES exist on disk: wti,brent,natgas,xau(gold),slv(silver),
  copper via copx.csv (ETF), spx, dow, fx pairs (EUR_USD,GBP_USD,USD_JPY,USD_CAD,AUD_USD,NZD_USD,USD_CHF,EUR_GBP),
  10y via us10y. Signal from positioning, PnL from price series.
- Existing panels: twelve_big (298 names), twelve_extend (440), ff_factors (SMB/HML/MOM/RMW/CMA daily 1926+),
  fx 8 pairs 2007+, fred dir (50 series incl vix,dxy,wti,brent,xau,slv,natgas,copper_monthly,copx,eur,gbp,jpy,cad,cny).
- Harness: `campaign/harness/data.py` (closes(), fred(), ff_factors(), apply_cost, save_sleeve),
  gates reference: `campaign/agents/B2_highfreq/gates.py` (vol_target, full_stats, halves_sr,
  scramble_pval, run_gates) — import and reuse.
- Existing sleeves (compute corr against): /Users/daxu/software/world-trader/campaign/results/sleeve_library/*.csv
  + /Users/daxu/software/world-trader/campaign/agents/*/sleeves/*.csv (all agents incl B-series)
  + /Users/daxu/software/world-trader/campaign/results/COORD_FINAL_daily.csv (the blend).

## EVAL
python3 /Users/daxu/software/world-trader/campaign/harness/eval.py <sleeve.csv>

## COORDINATOR (daxu main session)
Monitors logs, launches further rounds with updated charters, blends sleeves, runs OOS,
reports GOAL100 frontier honestly. Do NOT touch coordinator dirs (COORD/).
