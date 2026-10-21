# A3_xs_quality LOG
r1 (2026-08-28): engine.py written + self-tested; ideas 1-5 run, all gates FAILED, none saved.
Details+numbers in FINDINGS.md. Scripts: idea1_profitability.py, idea2_investment.py,
idea3_composite.py, idea4_lowvol.py, idea5_riskprem.py. Tool calls used: ~25/100.
r2 executed Fri Aug 28 21:41:57 CST 2026: 1 sleeve saved (QA_dualmom_band121 SR 0.89). See LOG_r2.log + FINDINGS.md
r4 executed Sun Aug 30 2026: 4 ideas (vt15 re-vol, mom-LO quintile vt15, PIT stat-sector-mom, earnings-mom proxy) — 0 saved, all gates honest. Details in FINDINGS.md. Scripts: r4lib.py, r4_idea0_vt15.py, r4_idea1_momlong.py, r4_idea2_sectmom.py, r4_idea2_scan.py, r4_idea2_best_scramble.py, r4_idea3_earnmom.py.
# r6 (2026-08-30): r6lib built + verified vs r2lib (corr 1.000 on dualmom repro). Stale-position bug caught pre-verdict. Idea1 wd-mom: LO SR 0.85 corr .64 FAIL; L/S -0.28; hedged max 0.58. Idea2 beta-rot: 0.58-0.73 but corr .45-.52 FAIL. Idea3 vol-shock: best corrected SR 0.685 corr .344, plateau 6/6, scramble p=0.185 FAIL. Idea4 dispersion retime: charter rule SR 0.56, inverse 0.70/corr_old .734 FAIL both conditions. 0 saves. ROUND r6 DONE
## r7 (2026-08-31) FRED macro engines — 1 SAVE
- r7lib.py: FRED loaders + library-corr scan + cost-inclusive circular scramble on custom panels
- idea1 commodity z-MR: 9 cells all SR -0.2..-0.3 FAIL (sign-flip +0.26)
- idea2 rate value: 16 runs FAIL (|SR|<=0.41, no sign/horizon works)
- idea3 credit pct gate: 24 runs FAIL (best 0.25; always-long carry 0.33 — gate inert)
- idea4 CPI momentum: FAIL (0.53, H1 0.22; +trend degrades to 0.13-0.19)
- idea5 breadth: charter SPX-gate FAIL; FORK to 5-leg per-leg TSMOM PASS
- SAVED QA_xasts_tsmom189: SR 1.06, H1 0.97/H2 1.14, 1 negYr (-3.6%), corr_champ 0.033,
  lib max 0.175, scramble p=0.000, plateau 7-9/9. Honest attribution: VIX-regime leg
  dominates (VIX-alone 1.08, no-VIX 0.25). Script + CSV + meta saved.
