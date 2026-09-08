# RES_BASIS — research: cross-commodity basis/spread/futures engines
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Find >=1 NEW decorrelated DAILY engine (SR >= 1.0 net, 2008+) that beats the champion+engine
blend frontier. Champion of record: campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
(ann 37.195% / SR 3.181 / MDD -6.69%). brwt (Brent-WTI) is the family's best prior; find more.

## Ideas (family-adjacent, decorrelation target)
- Crack spreads (HO-CL, RB-CL), NG calendar-cycle proxies, gold-platinum, copper-gold ratio,
  soy/crush, softs spreads — only if price data on disk (check tools/quant/data/futures/).
- If futures data absent, FRED spot pairs admissible with disclosed basis risk.
- Mechanism that worked for brwt: z-score of log spread over trailing window, pos when |z|>1.5,
  vol-target 0.08, cap 8.

## Gates (ALL required, use campaign/bt/ — not a new heredoc)
SR>=1.0 net full-window; H1>=0.5 & H2>=0.5; <=2 neg yrs each >-5%; 200x block-scramble p<0.05;
|corr|<0.15 to champion; T+1; 6.4bps/side full |dW|; flatten ac1<0.5 & uniqR>=0.08.

## Deliverable
Sleeve CSV [date,ret] + .meta + thin repro script under campaign/team/agents/RES_BASIS/sleeves/.
A REJECT with exact numbers is a valid result.

## Done marker
Last line of FINDINGS.md exactly: RES_BASIS DONE
