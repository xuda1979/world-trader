# HUNT_SECTOR_FULL — sector-relative z-reversion with the COMPLETE SPDR universe (iter 7.5)

CONTEXT: HUNT_CROSSASSET2 found sector-relative REVERSION (not momentum) was the only sign of life,
its near-miss SEC3 (XLB/XLF/XLI trio) passed 6/7 gates but failed the yearly gate 8/19. It was BLOCKED
from building the XLK/XLU/XLV/XLY pairs because those ETFs were MISSING on disk. NEW DATA now provides
the FULL SPDR set with full 2006-2026 span:
  tools/quant/data/more_etf/{XLK,XLY,XLP,XLU,XLV,XLRE,XLC,KBE,KRE,ITB,XHB,SMH,IGV,XOP,XME}.csv
  + twelve_big already had XLE,XLB,XLF,XLI + twelvedata had them too.

READ FIRST: campaign/results/DEAD_IDEAS.csv (sector-pair relative MOMENTUM dead; z-reversion-with-XLE
dead; the surviving thread is industrial/tech z-reversion WITHOUT the oil-XLE leg). This expands the
SEC3 family to a broader, non-oil sector set.

## METHOD (superpowers TDD; use campaign/bt)
1. Screen cross-sectional z-reversion on the FULL non-oil sector set (tech XLK, health XLV, staples
   XLP, discretionary XLY, industrials XLI, materials XLB, financials XLF + subs KBE/KRE/ITB/XHB/SMH/
   IGV), lb 10/15/21/63, cap 1.5-3, EW across pair-books. Explicitly EXCLUDE XLE/XOP (oil, redundant
   with champion).
2. For the best candidate: gates SR>=0.6 (2008+), H1/H2>=0.3, <=2 neg yrs each>-5%, 200x position-lag
   scramble p<0.05 (campaign/bt, correct baseline), |corr|<0.15 to V3 champion, ac1<0.5, uniqR>=0.08,
   6.4bps/side + 0.5% borrow, T+1. Also test adding to RAW-EW13@1.6x at slot w<=0.10 (lev<=1.6, 0-neg
   preserved, blended SR improves).
3. REPORT whether the FULL universe fixes SEC3's yearly-gate failure (the key question) or whether the
   yearly-gate failure is intrinsic (as FXD1/HUNT_FXDEPO concluded for KRW crosses). If intrinsic, log
   as a hardened negative with the yearly breakdown.
4. Trade-record: instrument = SPDR sector ETF (more_etf/X.csv), price_source REAL. Last line:
HUNT_SECTOR_FULL DONE
