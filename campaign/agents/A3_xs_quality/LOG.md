# A3_xs_quality LOG
r1 (2026-08-28): engine.py written + self-tested; ideas 1-5 run, all gates FAILED, none saved.
Details+numbers in FINDINGS.md. Scripts: idea1_profitability.py, idea2_investment.py,
idea3_composite.py, idea4_lowvol.py, idea5_riskprem.py. Tool calls used: ~25/100.
r2 executed Fri Aug 28 21:41:57 CST 2026: 1 sleeve saved (QA_dualmom_band121 SR 0.89). See LOG_r2.log + FINDINGS.md
r4 executed Sun Aug 30 2026: 4 ideas (vt15 re-vol, mom-LO quintile vt15, PIT stat-sector-mom, earnings-mom proxy) — 0 saved, all gates honest. Details in FINDINGS.md. Scripts: r4lib.py, r4_idea0_vt15.py, r4_idea1_momlong.py, r4_idea2_sectmom.py, r4_idea2_scan.py, r4_idea2_best_scramble.py, r4_idea3_earnmom.py.
# r6 (2026-08-30): r6lib built + verified vs r2lib (corr 1.000 on dualmom repro). Stale-position bug caught pre-verdict. Idea1 wd-mom: LO SR 0.85 corr .64 FAIL; L/S -0.28; hedged max 0.58. Idea2 beta-rot: 0.58-0.73 but corr .45-.52 FAIL. Idea3 vol-shock: best corrected SR 0.685 corr .344, plateau 6/6, scramble p=0.185 FAIL. Idea4 dispersion retime: charter rule SR 0.56, inverse 0.70/corr_old .734 FAIL both conditions. 0 saves. ROUND r6 DONE
