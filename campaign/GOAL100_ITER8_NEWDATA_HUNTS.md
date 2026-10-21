# GOAL100 ITER8 — NEW-DATA HUNTS (2026-09-03/04) — 4 hunts on the ~255 new series

Champion baseline unchanged: RAW-EW13@1.6x = 28.89% / SR 3.88 / -4.25% / 0 neg (REAL, sha-frozen).
Goal bar: ann>=80% | SR>=5 | MDD<=7% | lev<=1.6 | 0-neg | 6.4bps/side | IBKR margin 4.5%.

## HUNT results (all via campaign/bt, full honesty stack, TDD first)
| hunt | new data used | variants | verdict |
|---|---|---|---|
| HUNT_CIT_AG | CIT ×13, noncomm ×13, PCPS ×21, ag ETFs ×6 (NEW) | 156 + coherent-mapping retest + PCPS | NEGATIVE: best coherent 0.21; 0.705 cross-complex artifact rejected |
| HUNT_CURVES | JGB 1974+ ×15 tenors, BoE ×3, ECB-YC ×17, BIS-EER ×55 (NEW) | 56 | NEGATIVE: zero >= 0.3; best 0.261/4neg |
| HUNT_AUCTION | tauctions.csv 7852 auctions (NEW; + field-mapping BUG FIXED) | 64 | NEGATIVE: screen 0.585 = book-path artifact; honest -0.015..-0.17, scramble 0.93-0.97 |
| HUNT_MACRO2 | 14 new FRED series (WALCL/RRP/SOFR/T10Y3M/TED/NFCI×2/STLFSI4/JOLTS×2/debt-GDP/mortgage/T10YIE/EPU) | 168 | NEGATIVE for champion: best NFCIRISK gate SR 0.90 ann 5.3% standalone; blend dSR<0 at every weight |

## Bugs found & fixed this iteration (TDD)
1. ta_dl WS field mapping (totalAccepted not totalTenderAccepted) — 2 columns were 100% NULL
   in 7852 rows; fixed + regression test + re-fetch (bonus: primaryDealer/soma/fima fields).
2. HUNT_AUCTION book-path divergence (screen vs deep rebuild lag semantics) — caught in-session
   by mandatory deep-gate step; artifact killed before delivery.

## Ledger
DEAD_IDEAS 49 -> 53 (4 new dead families, each with exact evidence). No champion change —
the honest frontier remains RAW-EW13@1.6x. The 5-gate bar (ann80/SR5) remains out of reach on
the new data: the strongest new signal (NFCI-risk gate) is REAL but 1/5th the needed ann and
dilutes the champion when blended.
