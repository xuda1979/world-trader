# RES_FXSTYLE — cross-sectional FX carry/momentum/value on the NEW 508-pair matrix
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Leverage the NEW data landed by DATA_FXHIST (tools/quant/data/fx_hist/ — 508 currency pairs, 1999+,
daily close) to build a decorrelated FX engine. The champion has CFX4 (4-book z-rev) but NO broad
cross-sectional FX carry/factor engine. FX carry/momentum is decorrelated to equity momentum.

## Data (verify yourself)
- tools/quant/data/fx_hist/<AAA_BBB>.csv (date,close) — 508 pairs, back to 1999. Prefer USD crosses
  and major crosses for a clean carry basket.

## Ideas
- Cross-sectional FX carry: rank pairs by interest-rate differential (proxy: 12m return or rate
  spread if derivable), long high-carry / short low-carry basket, vol-managed, T+1.
- FX momentum (12m-1m skip) and short-horizon carry-turn; combine only if decorrelated.
- Dollar-neutral construction; borrow/shortability fine for FX (fungible).

## FIRST STEP
`python3 campaign/team/lib/corr_gate.py <cand.csv> 0.15` — reject if |corr| to champion >= 0.15.

## Gates (ALL, via campaign/bt/)
SR>=1.5 net full-window; H1/H2>=0.5; <=2 neg yrs >-5%; 200x block-scramble p<0.05; |corr|<0.15 to
champion; T+1; 6.4bps/side full |dW|; flatten ac1<0.5 & uniqR>=0.08. FX fungible-short ok.

## Deliverable
Sleeve CSV + .meta + thin repro under campaign/team/agents/RES_FXSTYLE/sleeves/. REJECT-with-numbers ok.

## Done marker
Last line of FINDINGS.md exactly: RES_FXSTYLE DONE
