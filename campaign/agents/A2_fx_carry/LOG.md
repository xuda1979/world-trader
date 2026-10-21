# A2_fx_carry LOG
## r1 (2026-08-28)
11 idea-variants tested end-to-end (signal -> T+1 -> 6bps -> gates). 0 passed. Details in FINDINGS.md.
Calls: fx_lib build + 9 experiment scripts. Best: blend SR 0.38 (scramble p<0.001), no save.
2026-08-28_21:37:19 A2 r2: charter 1-4 + 5 bonus ideas, ~30 configs, 0 pass (nearest: UST2 LF 378d SR1.45 yearly-fail; BLEND4 SR0.83 yearly-fail 4 soft; WTI-Brent MR scramble-fail p=0.35). Details in FINDINGS.md
2026-08-28 21:57:20 r2b: charter items 1-5 executed (ideas 12-21). Best zero-lag WTI-Brent spread MR SR 1.97 REJECTED on EIA +1d publication lag (honest SR 0.41). COT families all <0.45. No sleeves saved. See FINDINGS.md r2b.
2026-08-30 A2 r4: return-tilted charter — 8 idea families (~45 configs), 0 pass. Metals-trend 0.72 (carry unbuildable, spot data), SPX-VIX 0.52, FF-timing 0.65/corr0.51, BTC skipped (2.8y), 2s10s steepener-only 1.04 secular, blends 0.78-0.86 yearly-fail. LESSON: util.vol_target clip(0,3) voids vol-budget charters on low-vol books (UST2-LF identical at vt10/15/20). 0 sleeves saved. See FINDINGS.md r4.

# Round r7 (2026-08-31) — new FRED data_fred_new (DEXJPUS/DEXUSEU/DTWEXBGS/DGS*/DFF 1990+)
Data audit: foreign yields (jp/ez/gb/ca10y) MONTHLY and start 2018 -> true multi-currency carry still
cannot be extended pre-2018 from disk; "1999-2026 carry" infeasible honestly. US side now 1990+ daily.
Scripts: r7_lib.py, idea36/36b/36c (carry+accrual family), idea37 (JPY 36y mom + carry proxies),
idea38 (FX momentum full history), idea39/41/41b (dollar-fade FX + SPY timing, 20y honest test),
idea40 (scramble robustness), idea42 (carry-trend blend), idea43 (proxy plateau, arbiter, champ corr),
idea44 (final save w/ disclosure).
SAVED: sleeves/A2_fx_carry_W11_accrual.csv (live 2018-02..2026-08; eval SR 0.82 H1 0.45/H2 1.19,
2 neg yrs worst -5.0%; charter SR>=1.0 NOT met - disclosed; all campaign-brief gates pass).
FAILED: FX momentum full-history (12 configs, best 0.31), dollar-fade FX (-0.48..-0.78) and SPY
20y (0.70, H1 0.26, p=0.05; 2016+ 1.19 was regime artifact), carry-trend gates (destroy carry),
JPY-only carry proxies (0.35), FX dollar-fade binary (0.08).
ROUND r7 DONE
