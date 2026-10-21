# HUNT_FF_STRATARB — GOAL100 loop parallel team

Campaign: /Users/daxu/software/world-trader
Goal (honest): Ann>=80%, SR>=5, MaxDD<=7%, leverage<=1.6, profit>=0 every year.
Current best feasible (HONEST11-L16, committed): ann 47.6%, SR_d 4.18, MaxDD -4.85%, 0/19 neg yrs, leverage mean 1.59x.
Known infeasibility: 80% at <=1.6x not reachable with current engines (needs ~2.5-3x). SR>=5 not met.

YOUR TASK: statistical-arbitrage / factor-timing daily engine on ff_factors SMB/HML/MOM/RMW/CMA + Ken French OP/INV portfolios. Need SR>=0.6 full, H1/H2>=0.3, <=2 negyrs>=-5%, |corr|<0.15 to HONEST11 blend, no flattening (uniqR>=0.5, ac1<0.3). T+1, 6bps.

RULES (honesty contract, violations=reject):
1. T+1 execution only (signal at t uses data<=t).
2. 6bps/side costs on turnover.
3. Gates for any NEW sleeve: full SR>=0.6 (better: >=1.0), H1/H2>=0.3, <=2 negyrs each>-5%, scramble 200x p>0.05, |corr|<0.15 to HONEST11 blend (read LOOP_L16 findings), NO FLATTENING (uniqR>=0.08, ac1<0.5 — run the flatten gate from campaign/audit_harness.py logic).
4. Do NOT modify other agents' dirs or committed files. Write only under campaign/agents/loop_team/HUNT_FF_STRATARB/.
5. Finish with last line exactly: HUNT_FF_STRATARB DONE
Suite your own findings to campaign/agents/loop_team/HUNT_FF_STRATARB/FINDINGS.md with exact numbers.
