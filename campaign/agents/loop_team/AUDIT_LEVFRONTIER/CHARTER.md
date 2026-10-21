# AUDIT_LEVFRONTIER — exact feasibility frontier at capital-real <=1.6x, honest financing (iter 6)

CONTEXT: user's 5 goals = ann>=80%, SR>=5, MaxDD<=7%, capital-real leverage<=1.6, profit>=0/yr.
Multiple audits show the V3 champion = 43.6%/3.92 at 3.48x mean GROSS (91% of days >1.6x, margin
financing UNCHARGED). At the goal's own 1.6x cap it degenerates to ~17-20%/yr. SR is scale-invariant
~4.0. This AUDIT answers QUANTITATIVELY: what lever combination is even mathematically possible, and
what EXACT engine specs hunters need to hit. READ-ONLY except your dir.

## TASKS (all from committed files + builders; use campaign/scripts/honest13_build.py --verify and
independent rebuild; do NOT modify build files)
1. RECOMPUTE the honest frontier at capital-real gross <=1.6x with margin financing charged at
   IBKR-style call rate (use 4.5%/yr as base case, sweep 3-6%) on (gross-1), borrow 0.5%/yr, 6.4bps/side
   on turnover. Show ann/SR/DD/neg-yrs for: V3 BAL/SAFE/AGGR capped at 1.6x, V2, POOL11. Confirm the
   ~17-20% ceiling with exact numbers.
2. INVERSE target: solve for the per-engine specs required to hit ann>=80% AND SR>=5 at 1.6x with
   DD<=7%. Model the blend as sqrt-of-squares of N independent engines each SR=s, per-engine wt w,
   vol-targeted 10% each. Give a TABLE: with N=4/6/8/10 equal new engines of SR 1/1.5/2 (corr 0 to the
   existing pool, corr 0 to each other), what ann/SR/DD results at 1.6x? THIS is the concrete ask for
   every hunter. (Use the existing champion pool as the "old" engines; new engines get slot >>0.10.)
3. STATE the minimum NEW-ENGINE bar: how many engines, at what SR and corr, actually reach SR>=5 and
   ann>=80% under 1.6x + honest financing? If infeasible even with PERFECT new engines (SR bounding),
   say so with proof (e.g. ann = SR*vol*lev_effective; show the SR needed for 80% at 1.6x and 10-15% vol).
4. VERIFY the cost/borrow/shortability model end-to-end on the lowest-leverage honest build you can
   assemble from committed sleeves (list sleeves, lev, ann, SR, negyrs). Flag any remaining accounting gap.
5. RECOMMEND: the single most promising concrete build configuration (which sleeves at what slot cap
   under 1.6x) that the coordinator should emit, even if below 80%, as the new honest champion.

## REPORT
FINDINGS.md: exact numbers per task, the required-specs TABLE (this is the coordinator's hunting
target), a recommendation. Wrote only in this dir (you may create scratch/). Last line exactly:
AUDIT_LEVFRONTIER DONE
