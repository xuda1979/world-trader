# A2_fx_carry LOG
## r1 (2026-08-28)
11 idea-variants tested end-to-end (signal -> T+1 -> 6bps -> gates). 0 passed. Details in FINDINGS.md.
Calls: fx_lib build + 9 experiment scripts. Best: blend SR 0.38 (scramble p<0.001), no save.
2026-08-28_21:37:19 A2 r2: charter 1-4 + 5 bonus ideas, ~30 configs, 0 pass (nearest: UST2 LF 378d SR1.45 yearly-fail; BLEND4 SR0.83 yearly-fail 4 soft; WTI-Brent MR scramble-fail p=0.35). Details in FINDINGS.md
2026-08-28 21:57:20 r2b: charter items 1-5 executed (ideas 12-21). Best zero-lag WTI-Brent spread MR SR 1.97 REJECTED on EIA +1d publication lag (honest SR 0.41). COT families all <0.45. No sleeves saved. See FINDINGS.md r2b.
2026-08-30 A2 r4: return-tilted charter — 8 idea families (~45 configs), 0 pass. Metals-trend 0.72 (carry unbuildable, spot data), SPX-VIX 0.52, FF-timing 0.65/corr0.51, BTC skipped (2.8y), 2s10s steepener-only 1.04 secular, blends 0.78-0.86 yearly-fail. LESSON: util.vol_target clip(0,3) voids vol-budget charters on low-vol books (UST2-LF identical at vt10/15/20). 0 sleeves saved. See FINDINGS.md r4.
