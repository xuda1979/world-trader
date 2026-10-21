# SKILL_ALPHAAGM — independent skill-acquisition + research agent (user-directed, iter 5)

USER DIRECTIVE: "download alphaAGM skill and use it to do research."

## PHASE 1 — LOCATE alphaAGM (honest search, every step logged with URLs/commands)
1. Check installed sources: /Users/daxu/.claude/skills/, /Users/daxu/.claude/plugins/marketplaces/
   (claude-plugins-official, superpowers-marketplace manifests), /Users/daxu/.codex/skills/.
2. Search GitHub API: repos q=alphaagm, q=alpha-agm, q=alphaAGM in:name,description; also code
   search if available. Search npm registry (npm search alphaagm), PyPI (pip index/pip download),
   and plain web (curl a search engine if reachable).
3. VERDICT: does a skill named alphaAGM exist ANYWHERE public? If YES: download it (git clone or
   raw fetch) into campaign/agents/loop_team/SKILL_ALPHAAGM/skill/, read its SKILL.md, and follow it.
   If NO (current coordinator probing found 0 GitHub repos, not in either marketplace): WRITE THAT
   EXPLICITLY in FINDINGS.md ("alphaAGM NOT FOUND — searched X, Y, Z") and proceed to fallback:
4. FALLBACK (closest legitimate skills, pick ONE, install, disclose the substitution):
   - github.com/junsier9/quant-alpha-research-skill  (fail-closed staged alpha research skill)
   - github.com/eric554412/quant-research-os         (13-skill quant research OS)
   - github.com/aresbit/quant-trade-skill            (Jane-Street-style QT knowledge skill)
   Evaluate their READMEs, choose the best fit for EQUITY/asset-class alpha research with
   falsification gates, clone into skill/, and read it fully.

## PHASE 2 — APPLY THE SKILL TO GOAL100 RESEARCH
Use the skill's methodology (its stages/checklists/falsification protocol) on our live goal:
- Current champion: campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv (14 engines, ann 43.6%,
  SR_d 3.92, MaxDD -4.92%, 0/19 neg yrs). Builder: campaign/scripts/honest13_build.py (--verify).
- Goal set: ann>=80%, SR>=5, MaxDD<=7%, capital-real leverage<=1.6, profit>=0 every year.
- The campaign's honest-ceiling analysis says SR>=5 + ann>=80 at lev<=1.6 is INFEASIBLE on current
  engines; it needs ~2 more decorrelated engines with SR>=1.5, corr<0.1.
- YOUR RESEARCH TARGET: follow the skill's process to propose AND test 1-3 new engine ideas we
  have NOT run (check campaign/GOAL100_FINAL_STATE.md "removed/failed" list and
  campaign/agents/loop_team/*/FINDINGS.md first — do not re-run dead ideas).
- Gates (campaign honesty contract): SR>=0.6 (2008+), H1/H2>=0.3, <=2 neg yrs each >-5%, 200x
  10d-BLOCK POSITION-LAG scramble p<0.05 (return-permutation is DEGENERATE — do not use),
  |corr|<0.15 to the champion, ac1<0.5, uniqR>=0.08, T+1 execution, 6bps/side costs,
  borrow 0.5%/yr. Data on disk only; check tools/quant/data/, alphaportfolio_replication/data/.
- A skill that suggests ideas we lack data for => log as UNRUN (data-missing), do not fake.

## PHASE 3 — REPORT
FINDINGS.md must contain: (a) alphaAGM search trail (exact queries + results),
(b) what was actually installed (name, URL, commit sha) or NOT FOUND + fallback chosen + why,
(c) the skill's methodology summary as applied, (d) research results with exact numbers and
PASS/FAIL per gate, (e) what the skill recommends that this campaign should adopt permanently.
Scratch code under skill/ and scratch/. Last line exactly: SKILL_ALPHAAGM DONE
