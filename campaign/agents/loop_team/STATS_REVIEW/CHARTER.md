# STATS_REVIEW — full statistical certification of GOAL100_HONEST11FIX (reassigned slot, iter 4)
Prior slot died on API 429. The coordinator committed corrected champion
campaign/results/GOAL100_HONEST11FIX_{BALANCED,SAFE,AGGRESSIVE}_daily.csv (n=4989, 2006-10..2026-07;
comparable-span starts 2008-03-31). Your job: INDEPENDENT statistical certification with exact numbers.

Compute on BALANCED (and note SAFE/AGGR spread):
1. ann(geo), SR daily, SR monthly + 95% CI for both (block bootstrap 2000x, 10d blocks for daily;
   2000x iid for monthly)
2. MaxDD + worst 3y subwindow MaxDD (rolling 1260d) + worst 1y subwindow return
3. Negative calendar years 2008-2026 (exact count, worst year)
4. OOS 2017+ ann/SR; also OOS 2020+ and OOS 2023+ (recent-regime check)
5. Deflated Sharpe: given we tested ~hundreds of configs this campaign, apply Bailey/López de
   Prado DSR with N=500 effective trials and report whether SR_d 4.0 survives (expected: yes,
   but QUANTIFY the haircut)
6. Ljung-Box on daily returns (10 lags) — any residual autocorr artifact?
7. Skew/kurtosis, worst 5 days, VaR/CVaR 5% daily, and the 24.3-sigma single-day issue:
   what is the probability of a -14.4% day recurring (Fisher-Tippett or empirical tail) and would
   it breach MaxDD<=7% from current levels?
8. LEVERAGE accounting (capital-real): all-in gross = sum_i |scale_i,t|*global_t/N on the FIX
   construction (rebuild with honest11_build.build(0.07,0.04,0.08,REBAL=True,KEEP=True) machinery
   but capture scales yourself). Report mean/p95/max, yearly means, and the ann achievable at
   all-in gross<=1.6 (sweep TGT down) — is the goal set feasible under capital-real leverage?
9. FINAL TABLE: goal-by-goal verdict (Ann>=80, SR>=5, MaxDD<=7, lev<=1.6, profit>=0 every year)
   with the exact number achieved on the honest construction, plus the binding-definition statement.

Write FINDINGS.md with all exact numbers. UNVERIFIED stays UNVERIFIED. Last line: STATS_REVIEW DONE
