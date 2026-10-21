# SKILL_ALPHAAGB_B — locate/download/install the AlphaAGB skill + apply to research (iter 6, user-directed)

USER DIRECTIVE (verbatim): "use one agent to download and install AlphaAGB skill and use it to do research."

IMPORTANT CONTEXT: a PRIOR agent already searched "alphaAGM" (a slightly different name) and found no such
public skill; it installed junsier9/quant-alpha-research-skill as fallback (commits under
campaign/agents/loop_team/SKILL_ALPHAAGM/skill/). YOUR job is a FRESH search for the EXACT name "AlphaAGB"
(or "AlphaGB"/"AlphaGBM"/"AlphaAGB skill") that the user asked for this time. Do NOT assume the prior
negative applies. Verify independently.

## PHASE 1 — LOCATE AlphaAGB (honest, logged)
1. Check installed: /Users/daxu/.claude/skills/, /Users/daxu/.codex/skills/,
   /Users/daxu/.claude/plugins/marketplaces/ (grep -ri alphagb/alphaagb/alphagbm across them).
2. GitHub API searches (done from main session, verify/extend):
   - q=alphagb (6 repos), q=alpha-gb (37), q=alphagbm — inspect each candidate's semantic fit:
     many are Chinese AI-options-commercial or unrelated. Evaluate READMEs via raw fetch.
   - code search is auth-blocked (401) — log that honestly if hit.
3. npm registry search, PyPI (pypi.org/pypi/alphagb, /alphaagb), plain web.
4. VERDICT: does a quant research SKILL named AlphaAGB exist? If a clear legitimate skill exists
   (with SKILL.md, falsification methodology), clone it into SKILL_ALPHAAGB_B/skill/ and follow it.
   If only marketing/commercial products (AlphaGBM) or unrelated repos exist, say so explicitly and
   INSTALL THE BEST FALLBACK quant-research skill (evaluate junsier9/quant-alpha-research-skill vs
   eric554412/quant-research-os; you may reuse OR re-clone — disclose which). Never fabricate a skill.

## PHASE 2 — APPLY TO GOAL100 RESEARCH
Current champion: campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv (ann 43.6%, SR_d 3.92,
MaxDD -4.92%, 0/19 neg yrs). Builder: campaign/scripts/honest13_build.py (frozen, --verify).
Goal: ann>=80%, SR>=5, MaxDD<=7%, capital-real leverage<=1.6, profit>=0/yr.
Use the skill's methodology to propose + test 1-3 NEW engine ideas not in the dead-list
(READ campaign/GOAL100_FINAL_STATE.md "removed/failed" + all loop_team/*/FINDINGS.md dead-lists first).
Gates: SR>=0.6 (2008+), H1/H2>=0.3, <=2 neg yrs each>-5%, 200x 10d-BLOCK POSITION-LAG scramble
p<0.05 (NOT return permutation — degenerate), |corr|<0.15 to champion, ac1<0.5, uniqR>=0.08,
T+1, 6.4bps/side, borrow 0.5%/yr. Data on disk only. Log data-missing ideas as BLOCKED (fail-closed).

## PHASE 3 — REPORT
FINDINGS.md: (a) AlphaAGB search trail (exact commands+results), (b) installed (name/URL/sha) or
explain, (c) methodology as applied, (d) research results exact PASS/FAIL per gate, (e) permanent
recommendations. Do NOT modify other agents' dirs. Last line exactly: SKILL_ALPHAAGB_B DONE
