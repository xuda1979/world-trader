# SKILL_ALPHAAGM — FINDINGS (2026-09-02, iter 5)

Agent: loop_team/SKILL_ALPHAAGM. Mission (CHARTER.md): "download alphaAGM skill and use it to
do research." All scratch code in this dir: `scratch/s1..s8*.py`, `scratch/lib.py`; clones under
`skill/`. Read-only elsewhere in the repo (verified: only wrote inside SKILL_ALPHAAGM/).

---

## (a) alphaAGM SEARCH TRAIL — exact queries + results

| Step | Where | Exact command / query | Result |
|---|---|---|---|
| 1 | installed skills | `ls /Users/daxu/.claude/skills/` | **not found** (no `alphaagm`; dir empty of it) |
| 2 | marketplaces | `ls /Users/daxu/.claude/plugins/marketplaces/` → claude-plugins-official, superpowers-marketplace; `grep -ri alphaagm` across both | **0 matches** |
| 3 | codex skills | `ls /Users/daxu/.codex/skills/` → 10 skills (apex-rd-orchestrator, dataset-cleaning, hard-math-research, huanxin-*, lean-software-engineering, onlycode, quantum-eval-verifier, s3-transfer) | **no alphaAGM** |
| 4 | GitHub repos | API `search/repositories?q=alphaagm` | `total_count: 0` |
| 5 | GitHub repos | API `search/repositories?q=alpha-agm` | `total_count: 0` |
| 6 | GitHub repos | API `search/repositories?q=alphaAGM+in:name,description` | `total_count: 0` |
| 7 | GitHub repos | API `search/repositories?q=agm+alpha+in:name,description` | `total_count: 0` |
| 8 | GitHub code search | API `search/code?q=alphaAGM` | **401 Requires authentication** (attempted, blocked — logged honestly) |
| 9 | npm | `GET registry.npmjs.org/-/v1/search?text=alphaagm` | `objects: [], total: 0` |
| 10 | PyPI | `GET pypi.org/pypi/alphaagm/json` and `pypi.org/pypi/alpha-agm/json` | both `404 Not Found` |

## VERDICT (Phase 1): **alphaAGM NOT FOUND** — searched GitHub (4 query variants, 0 repos), npm (0),
PyPI (404 x2), installed skills/marketplaces (0 matches). No such public skill exists.
Code search was auth-blocked (only remaining channel, would not change repo verdict).

## (b) WHAT WAS ACTUALLY INSTALLED (disclosed substitution)

- **Chosen fallback**: `github.com/junsier9/quant-alpha-research-skill`
- **Why**: charter's 3 candidates evaluated on fit for EQUITY/asset-class alpha research with
  falsification gates. (1) junsier9: fail-closed Stage-0/falsification/promotion-gate skill —
  its falsification matrix (delay/shuffle/holdout/cost-stress/fail-closed) IS the campaign's
  honesty contract in skill form; has CI validation + recorded evals; 1 star, pushed 2026-05-07.
  (2) eric554412/quant-research-os: 13-skill pipeline, 0 stars — methodology solid (ledgers,
  anti-rehash) but it's an ORCHESTRATION architecture, not a falsification protocol; cloning all
  13 skills for one research slot adds nothing this session. (3) aresbit/quant-trade-skill:
  **README 404** (raw fetch `raw.githubusercontent.com/aresbit/quant-trade-skill/main/README.md`
  → `404: Not Found`) — repo metadata exists but default-branch README missing → failed even the
  read step. → (1) wins decisively for this charter ("falsification before promotion").
- **Install**: `git clone --depth 1` into `SKILL_ALPHAAGM/skill/`.
  **Commit sha: c848dfe4570f289eb99dda5daba468296a7d95b0** (2026-05-07 11:44:07 +0800, main).
  Apache-2.0. Contents read fully: `skills/quant-alpha-research/SKILL.md` + all 3 references
  (patterns.md, stage0_and_falsification.md, output_templates.md).
- Substitution disclosed per charter §1.3: **no skill named alphaAGM was installed because none exists.**

## (c) THE SKILL'S METHODOLOGY AS APPLIED

The skill's core (SKILL.md §Workflow + stage0_and_falsification.md), mapped to GOAL100:
1. **Orient from current repo artifacts, not memory** → read GOAL100_FINAL_STATE.md, the V3
   champion file, and ALL 10 loop_team FINDINGS.md dead-lists before proposing anything.
2. **Research contract**: mechanism → data → horizon → landing shape → fail-closed blockers,
   stated BEFORE coding.
3. **"Build the smallest Stage 0 that can reject the idea"** — rejection-first, not optimization.
4. **Falsify before optimizing**: delay (T+1), position-lag scramble, cost/funding stress,
   flatten gate, holdout/subwindow consistency; **fail-closed** on missing data.
5. **Report in DECISION FORM** (`go`/`no-go`/`blocked`/`research-only`); never collapse
   "validated" / "passed falsification" / "promotable" into one label.
6. **Anti-patterns to name in the report**: "Sharpe improved, so alpha exists", "coverage passed,
   so data is trustworthy", missing-evidence-promoted-to-pass.

Applied contract for every probe below: mechanism stated; **data reality verified FIRST from
disk (fail-closed)**; T+1 (position from t-1 info); 6bps/side on turnover; borrow 0.5%/yr on
short leg; gates = SR_d>=0.6 (2008+), H1/H2>=0.3, <=2 neg yrs each >-5%, 200x 10d-BLOCK
POSITION-LAG scramble p<0.05 (return-permutation DEGENERATE — not used, per campaign contract),
|corr|<0.15 to champion, ac1<0.5, uniqR>=0.08.

Champion baseline (recomputed by me from `campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv`,
4774 rows 2008+): SR_d 3.9397, ann(geo) 43.75%, MDD -4.92%, 0/19 neg yrs (worst +13.94%), H1
3.84 / H2 4.04, ac1 -0.073, uniqR 1.000 — matches the committed claims (43.6/3.92/-4.92).

## (d) RESEARCH RESULTS — 7 Stage-0 probes, exact numbers, PASS/FAIL per gate

Ideas selected against the dead-lists (NOT re-run: FF factor premia, industries/deciles, equal-wt
BAB, MM ivol, value/growth/profitability screens, FX carry/weekday, NG/oil basis, gold-silver,
credit as PAPER synth, FOMC x natgas/gold, M2-gold, CFNAI gates — all documented dead by prior
agents). Genuinely-not-yet-run families found: 25 FF pools as daily TRADABLE pool books (prior
agents only used long-short FACTOR spreads), seasonals, NKY calendars, propane, TIPS breakeven,
tradable LQD/HYG ETFs, SPY pre-FOMC.

| # | Engine idea (mechanism) | Data (verified) | Result (2008+, T+1, 6bps, borrow) | Verdict |
|---|---|---|---|---|
| S1 | 25 FF size×value pools daily mom/rev rotation (long top5/short bottom5 by trailing 21d/63d return; "credit" proxy = small/value corners) | kenfrench 25_Portfolios_5x5_Daily CSV zip (202606 CRSP, 26,273 rows 1926-2026, VW daily section parsed at line 18; 0 missing cells 2008+) | **MOM5**: SR_d -1.7955, 18 neg yrs worst -39.9%, corr -0.0373. **MOM21**: SR_d -0.8017, 16 neg worst -29.6%. **MOM63**: SR_d -0.5759, 16 neg worst -31.0%, corr +0.0088. **REV5**: SR_d -1.4915. **REV21**: SR_d -0.9039. ALL SR<0, ALL negy 16-18 | **no-go** — daily-pool momentum/rev 2008+ is sign-INVERTED vs the 1926-2007 literature (5y daily reversal dominates); consistent with FF2's negative ledger, now proven at daily pool level |
| S1b | November effect: long P1 SMALL-LoBM Nov 1–Jan 31 (tax-loss-loss-rebound seasonal; long-only, T+1 calendar) | same file | SR_d **0.3645**, ann 4.27%, MDD -44.1%, **8 neg yrs worst -25.0%**, H1 0.3256 / H2 0.4029, ac1 -0.0092, uniqR 0.1187, corr to V3 **+0.0702**. Scramble p=0.2583 (600 perms; perm-SR dist mean 0.157/p95 0.530 — 3-month windows block-shifted by 10d multiples still land in Nov-Jan season, honest result) | **no-go** — 5/8 gates FAIL (SR, negy, scramble). Gate card: SR 0.3645<0.6 FAIL; H1/H2 PASS; negy 8>2 FAIL; corr PASS; ac1 PASS; uniqR PASS; scramble FAIL |
| S1b | December effect: long P25 BIG-HiBM December-only | same file | SR_d 0.4739, ann 3.31%, **5 neg yrs worst -13.0%**, uniqR 0.057 | **no-go** (negy + uniqR FAIL) |
| S1b | Turn-of-month, P1 | same file | SR_d 0.0507, ann -0.56%, 7 neg yrs | **no-go** (dead) |
| S2 | NKKEI225 calendars (FRED NIKKEI225.csv full history 1949→2026-08-31, 20,166 rows): 5 day-of-week long books + turn-of-month | newdata/NIKKEI225.csv (level only — NO OHLC ⇒ overnight split NOT runnable, disclosed) | dow0..dow4: SR_d -0.4415/-0.1574/-0.4257/-0.6200/-0.4582 (all 11-15 neg yrs). TOM: SR_d -0.0590, 11 neg yrs | **no-go** — every DOW negative 2008+; anomaly dead in this span |
| S3 | Propane winter seasonal short (Nov–Mar, heating-inventory build) | hedge_fund_strats/data_fred_new/DPROPANEMBTX.csv (8,554 rows 1992→2026-08-25; newdata copy corrupted-HTML, full-history copy found elsewhere — provenance logged) | SR_d 0.0624, ann -2.5% geo, MDD -86.3%, **12 neg yrs**, worst -32.2%; recent years -15..-25% (2021-26 ALL neg) | **no-go** — calendar seasonality gone post-2020; also NO storage/inventory data on disk (weaker premise, disclosed fail-closed) |
| S4 | TIPS-nominal breakeven RV (10y, z-rev + momentum, win 21/63/126; duration-8.5 P&L on yield diffs) | hedge_fund_strats/data_fred/DFII10.csv + DGS10.csv (5,668 common rows 2004→2026-08-27; DFII5 does NOT exist on disk — 5y variant UNRUN data-missing) | best of 6: zrev126 SR_d **-0.5431** (16 neg yrs); mom126 -0.5675; all 16-19 neg yrs | **no-go** — breakeven trended with no tradable daily reversion edge at daily granularity |
| S5 | Credit carry on REAL credit TR indices | **BLOCKED**: only OAS spreads on disk (BAMLC0A0CM etc. start 2023-08 in newdata); synth-TR approach already REMOVED from campaign (A1credit PAPER-credit); tradable LQD/HYG tested in S6 | — | **blocked (data-missing)** — no corporate TR index 2008+ on disk; logged, not faked |
| S6 | LQD/HYG tradable-ETF books (pair momentum 21/63d; single-asset trend 63d) | twelvedata LQD.csv (5,000 rows 2006-10→2026-08-31), HYG.csv (4,879 rows 2007-04→) | pair-mom21: SR_d **-1.0644** (18 neg); pair-mom63: -0.6675 (17 neg); LQD trend63: -0.1664 (11 neg); HYG trend63: -0.5205 (14 neg) | **no-go** — all four negative; tradable credit carries no daily timing edge here |
| S7 | SPY pre-FOMC drift (Lucca-Moench; hold SPY on FOMC day1+day2, T+1 calendar-known) | twelvedata SPY.csv (5,000 rows 2006→2026-08-12) + newdata/fomc_dates.csv (119 meetings 2008-2027) | **2008-2026: SR_d -0.1822, mean FOMC-day -0.71bp vs all-day +4.34bp**; 11/19 neg yrs; positive-control 2008-2015 literature window: SR **-0.143** — the anomaly does not exist in this data at close-to-close granularity (D4's FOMC-x-commodities SR 0.53 also failed; consistent) | **no-go** — with negative positive-control the mechanism is falsified at this resolution (intraday version UNRUN — see ledger) |

### Gate card, best-of-session (S1b Nov-Jan small-growth seasonal) — exact
SR_d 0.3645 → **FAIL** (needs >=0.6) · H1 0.3256 **PASS** · H2 0.4029 **PASS** · negy 8 (worst
-25.0%) → **FAIL** · corr +0.0702 **PASS** · ac1 -0.0092 **PASS** · uniqR 0.1187 **PASS** ·
position-lag scramble p 0.2583 → **FAIL**. **0 admissible engines delivered.** Nothing was added
to the champion; V3 stands exactly as committed (recomputed: SR_d 3.9397, ann 43.75%, MDD -4.92%).

### NEGATIVE LEDGER (new dead ideas this session — do not re-run)
25-pool daily momentum/reversal rotation (all windows), Nov-Jan & Dec small/value seasonals,
NKY day-of-week & TOM, propane winter short, TIPS breakeven z-rev/momentum (10y), LQD/HYG pair
momentum & trend, SPY close-to-close pre-FOMC.

### UNRUN (data-missing / resolution-missing — logged honestly, not faked)
- **Overnight/intraday session split** (true overnight edge + intraday pre-FOMC): polygon_intraday
  exists but starts 2024-12 (1.75y ≪ 2008+ gates) → data-insufficient. This is THE most promising
  falsified-at-daily-resolution lead (S7's negative positive-control is expected — the anomaly IS
  an intraday phenomenon).
- **5y TIPS (DFII5)** not on disk → 5y breakeven variant untested.
- **Corporate credit TR index 2008+** (BAML ICE indices return versions) not on disk → credit
  carry/carry-regime engines blocked.
- **China A-shares (tools/quant/data/cn, 27 files)**: only ~1.6y (2024-12→) → span-insufficient.

## (e) WHAT THIS CAMPAIGN SHOULD ADOPT PERMANENTLY (from the installed skill)

1. **Decision-form reporting with separate labels** — `validated` ≠ `passed-falsification` ≠
   `promotable`, plus `blocked`/`research-only` states. The campaign already does this informally;
   making the 4-label vocabulary mandatory in every FINDINGS.md would prevent "verified SOLID
   keep" absorbing "unverified tradeability" claims (e.g. FF2's disclosed caveat).
2. **Stage-0 rejection-first slicing** — "build the smallest Stage 0 that can REJECT the idea"
   is the right default over parameter grids; this session rejected 7 families in ~12 cheap runs
   instead of delivering one overfit near-miss.
3. **Fail-closed data-block reporting** — mark data-missing ideas `blocked` + name the exact
   missing series (done in UNRUN above) so a future data-drop instantly converts to a testable
   queue instead of re-archaeology.
4. **Anti-pattern phrases as review triggers** — e.g. "coverage passed, so rerun alpha",
   "Sharpe improved, so alpha exists" — worth a checklist line in future audit agents (AUDIT_V2
   already behaves this way; codify it).
5. **Landing-shape reasoning** (gate/veto/replacement/sleeve-activation vs global overlay) —
   maps to the campaign's slot-weight construction; already implicitly used, worth naming.
6. From eric554412's README (read for evaluation, not installed): a persistent **EDGE_MAP /
   dead-idea ledger** per campaign — GOAL100_FINAL_STATE.md serves this, but a machine-readable
   dead-idea CSV would cut the "check every prior FINDINGS.md" cost this charter imposed (I read
   10; a ledger would have been 1 file).

## HONESTY NOTES
- No new engine PASSED; champion unchanged; no files written outside SKILL_ALPHAAGM/.
- V3 champion verified from the committed CSV by my own loader: SR_d 3.9397 / ann(geo) 43.75% /
  MDD -4.92% / 0 neg yrs — consistent with the commit message.
- pandas-3.0 `groupby.apply` silently exploded yearly compounding (10^76 values) in my first
  lib.stats; **self-caught and fixed** (manual per-year loop) before any verdict relied on
  yearly stats — first-run negy numbers quoted above are the post-fix values (S1 rerun; S1b/S3
  re-executed after patch; S2/S4/S6/S7 used only SR/corr which were unaffected).
- FOMC day2 file contains scheduled 2027 dates (future meetings) — irrelevant to 2008-2026
  backtest, no leak possible (calendar known in advance by construction).
- Scramble for the calendar-seasonal book: block-shifted positions of a 3-months-on/9-off
  pattern retain seasonal overlap (perm-SR p95 0.530 > real 0.365) — reported as measured
  (p=0.2583), not forced to 0; gate FAIL recorded honestly.

SKILL_ALPHAAGM DONE
