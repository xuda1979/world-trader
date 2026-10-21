# HUNT_CIT_AG — CIT index-flow + PCPS spot + climate on ags ETF tradables (NEW DATA, iter8)

## Goal (5-gate bar, same as campaign)
ann>=80% & SR>=5 & MaxDD<=7% & lev<=1.6 & 0 neg years. One side 6.4bps. IBKR margin 4.5% on
(gross-1). Shortability: ag ETFs DBA/CORN/WEAT/SOYB/CANE are liquid ETNs/ETFs — borrow ok but
flag any short leg as borrow 0.5% (already in bt). Realistic target: a NEW decorrelated sleeve
with net SR>=0.6 that passes all gates; report honestly if bar unreachable.

## Signals (NEW data only)
- tools/quant/data/more_cot/cit_*.csv (13 families: cit_net, cit_pct_oi, weekly Tue)
- tools/quant/data/more_fred/P*.csv (IMF PCPS spot: PWHEAMTUSDM, PMAIZMTUSDM, PSOYBUSDM,
  PCOFFOTMUSDM, PCOCOUSDM, PSUGAUSAUSDM, PCOTTINDUSDM + metals + livestock, monthly)
- tools/quant/data/noaa_climate/{oni,nao,meiv2}.csv (monthly)
- tools/quant/data/more_cot/*_cot.csv (noncomm nets for same families — in-disk prior family)

## Tradables (NEW ETFs in more_etf/)
DBA (2007+), CORN (2010+), WEAT/SOYB/CANE (2011+), MOO (2007+). Plus GSG/DBC/USO in-disk.

## Method (TDD, campaign/bt only)
1. tests/test_cit_ag.py FIRST (RED), then cit_ag.py engine.
2. Signal construction: CIT pct z-score (26w), changes, and CIT-vs-noncomm divergence;
   PCPS 63d momentum gating; ONI/NAO regime overlays. NO LOOKAHEAD: weekly COT published Fri
   15:30 ET (3-day lag convention: position effective Monday after report Tuesday).
3. bt.backtest.sleeve per tradable (target 10% vol, cap 1.6); book() = EW of passing sleeves.
4. Gates: bt.gates.run (SR, H1/H2, neg-years on OWN span + 2008+ span, scramble>=0.05),
   turnover honesty at 6.4bps/side FULL, uniq_ratio, ac1.
5. DEAD_IDEAS.csv append if dead; FINDINGS.md with exact numbers + repro.

## Honesty bars (from DEAD ledger: no re-litigating)
- cost 6.4bps/side on FULL turnover (SEC3 artifact lesson)
- T+1 + COT 3-day lag (not same-day)
- own-span AND 2008+ yearly gates; H2>=0.5*H1
- position-lag scramble p>=0.05 on the real book
Last line: HUNT_CIT_AG DONE
