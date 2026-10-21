# L16_AUDIT — GOAL100 loop parallel team

Campaign: /Users/daxu/software/world-trader
Goal (honest): Ann>=80%, SR>=5, MaxDD<=7%, leverage<=1.6, profit>=0 every year.
Current best feasible (HONEST11-L16, committed): ann 47.6%, SR_d 4.18, MaxDD -4.85%, 0/19 neg yrs, leverage mean 1.59x.
Known infeasibility: 80% at <=1.6x not reachable with current engines (needs ~2.5-3x). SR>=5 not met.

YOUR TASK: adversarially re-audit GOAL100_HONEST11L16_BALANCED_daily.csv for ANY remaining bug (flattening, lookahead, calendar, cost, leverage>1.6, hidden exposure). Read LOOP_L16/FINDINGS.md + LOOP_XGB1YFLAT/FINDINGS.md. Verify the 1.59x leverage claim and 0-neg-year claim independently. Write findings.

RULES (honesty contract, violations=reject):
1. T+1 execution only (signal at t uses data<=t).
2. 6bps/side costs on turnover.
3. Gates for any NEW sleeve: full SR>=0.6 (better: >=1.0), H1/H2>=0.3, <=2 negyrs each>-5%, scramble 200x p>0.05, |corr|<0.15 to HONEST11 blend (read LOOP_L16 findings), NO FLATTENING (uniqR>=0.08, ac1<0.5 — run the flatten gate from campaign/audit_harness.py logic).
4. Do NOT modify other agents' dirs or committed files. Write only under campaign/agents/loop_team/L16_AUDIT/.
5. Finish with last line exactly: L16_AUDIT DONE
Suite your own findings to campaign/agents/loop_team/L16_AUDIT/FINDINGS.md with exact numbers.
