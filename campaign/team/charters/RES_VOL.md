# RES_VOL — volatility / options-implied engines (new CBOE VIX term structure)
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Find >=1 NEW decorrelated DAILY engine from the volatility surface. DATA_PULL is fetching the
CBOE VIX 9d/3m/6m term structure (more_vol/) — build the term-SLOPE engine the champion lacks.
Vol is decorrelated to equity momentum (champion is momentum/style heavy).

## Data (verify yourself)
- tools/quant/data/more_vol/<SYM>.csv (VIX, VIX9D, VXV, VIX3M, VIX6M, VVIX, RVX, OVX, GVZ, SKEW).
- tools/quant/hedge_fund_strats/data_fred/vix + vxv if more_vol incomplete.

## Ideas
- VIX-term slope (VIX3M-VIX9D / contango vs backwardation) level/change.
- Vol-of-vol (VVIX), vol-of-VIX change, RVX (Russell vol), absolute-vs-implied gap.
- SKEW term / tail-hedge timing (only if survives gates).

## FIRST STEP
`python3 campaign/team/lib/corr_gate.py <cand.csv> 0.15` — reject if |corr| to champion >= 0.15.

## Gates (ALL, via campaign/bt/, not a heredoc)
SR>=1.5 net full-window; H1>=0.5 & H2>=0.5; <=2 neg yrs >-5%; 200x block-scramble p<0.05;
|corr|<0.15 to champion; T+1; 6.4bps/side full |dW|; flatten ac1<0.5 & uniqR>=0.08.

## Deliverable
Sleeve CSV + .meta + thin repro under campaign/team/agents/RES_VOL/sleeves/. REJECT-with-numbers ok.

## Done marker
Last line of FINDINGS.md exactly: RES_VOL DONE
