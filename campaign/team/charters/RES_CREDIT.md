# RES_CREDIT — credit spreads / surveys engines (decorrelated to equity momentum)
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Find >=1 NEW decorrelated DAILY engine from the credit/rates-spread world. The champion has
rates curves (a6r7, QAxasts) but NO clean credit-spread engine. Credit is decorrelated to equity
momentum.

## Data (verify yourself)
- FRED: hy_oas (HY OAS), baa, aaa, t10y2y, tltoeweb (alt HY), dfii10/dfii5 (TIPS real yield).
- tools/quant/data/more_etf/LQD.csv, HYG.csv, TLT.csv, JNK.csv, EMB.csv (if present).
- tools/quant/hedge_fund_strats/data_fred/ (hy_oas, baa, aaa, t10y2y).

## Ideas
- HY OAS level/change/1m z (regime), HY-TSY spread momentum (T+1 causal).
- Credit-carry (HY OAS as carry) with vol-target; credit-basis IG vs HY.
- baa-aaa quality spread, real-yield (TIPS) momentum.
- WARNING: C2 rates-flies died at 6bps; avoid anything whose turnover exceeds the edge.

## FIRST STEP
`python3 campaign/team/lib/corr_gate.py <cand.csv> 0.15` — reject if |corr| to champion >= 0.15.

## Gates (ALL, via campaign/bt/)
SR>=1.5 net; H1/H2>=0.5; <=2 neg yrs >-5%; 200x block-scramble p<0.05; |corr|<0.15 to champion;
T+1; 6.4bps/side full |dW|; flatten ac1<0.5 & uniqR>=0.08.

## Deliverable
Sleeve CSV + .meta + thin repro under campaign/team/agents/RES_CREDIT/sleeves/. REJECT-with-numbers ok.

## Done marker
Last line of FINDINGS.md exactly: RES_CREDIT DONE
