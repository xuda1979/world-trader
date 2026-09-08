# RES_ALTDATA — alt/regime engine from the NEW altlib data
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Leverage the NEW alt-data landed by DATA_ALTLIB (tools/quant/data/altlib/ — DeFi TVL/activity,
fear-greed) to build a decorrelated regime/CYCLICAL engine. Alt-data gives a distinct, hard-to-mimic
return stream that is decorrelated to price-momentum engines.

## Data (verify yourself)
- tools/quant/data/altlib/ (manifest.csv + downloaded series: DeFi TVL, user/activity, crypto
  fear-greed). Cross-check existing alt dirs (altme_fng, crypto_fg, defillama_stables, coingecko_breadth).

## Ideas
- Alt-regime risk-on/risk-off signal (breadth of alt conditions -> tilt a conservative risk asset or
  a low-beta book). Must map to a tradable instrument with a return series on disk.
- DeFi/TVL growth-rate as a cycle indicator for an equity/rates leg.
- WARNING: alt data often starts 2017+ (short span). If the series can't give a 2008+ backtest,
  it's NOT champion-eligible — disclose the true in-sample window and REJECT if < the required span.

## FIRST STEP
`python3 campaign/team/lib/corr_gate.py <cand.csv> 0.15` — reject if |corr| to champion >= 0.15.

## Gates (ALL, via campaign/bt/)
SR>=1.5 net; H1/H2>=0.5; <=2 neg yrs >-5%; 200x block-scramble p<0.05; |corr|<0.15 to champion; T+1;
6.4bps/side full |dW|; flatten ac1<0.5 & uniqR>=0.08. Fail-closed on short/incomplete alt span.

## Deliverable
Sleeve CSV + .meta + thin repro under campaign/team/agents/RES_ALTDATA/sleeves/. REJECT-with-numbers ok.

## Done marker
Last line of FINDINGS.md exactly: RES_ALTDATA DONE
