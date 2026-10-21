# SKILL_ALPHAAGB_B — FINDINGS (2026-09-03, iter 6)

Agent: loop_team/SKILL_ALPHAAGB_B. Charter: fresh search for EXACT name "AlphaAGB" (+variants),
install best quant-research skill, apply it to GOAL100 research. All scratch code in `scratch/`
(p1..p9*.py, libb.py), skill clone in `skill/`. Wrote ONLY inside SKILL_ALPHAAGB_B/ (verified).

---

## (a) PHASE 1 — AlphaAGB SEARCH TRAIL (exact commands + results)

| # | Where | Exact command / query | Result |
|---|---|---|---|
| 1 | installed claude skills | `ls /Users/daxu/.claude/skills/` | **empty** |
| 2 | installed codex skills | `ls /Users/daxu/.codex/skills/` | 10 skills (apex-rd-orchestrator … s3-transfer) — **no AlphaAGB** |
| 3 | marketplaces | `ls /Users/daxu/.claude/plugins/marketplaces/` → claude-plugins-official, superpowers-marketplace; `grep -ril "alphagb\|alphaagb\|alphagbm\|alpha-gb"` across all three trees | **0 matches** |
| 4 | GitHub repos | `GET api.github.com/search/repositories?q=alphagb` | `total_count: 6` — Tinananan873/AlphaGBM (76★, "AI 驱动的智能期权分析与高频交易量化软件"), AlphaGBM-AI-Quant (35★, marketing listicle), catl-alphagbm (CATL stock analysis), man_alphagb (manning DL+Go), AlphaGBT-V, AlphaGBM-laozhang. **None is a quant research skill** |
| 5 | AlphaGBM repo inspection | `GET api.github.com/repos/Tinananan873/AlphaGBM` + `git/trees/main` | repo = **4 KB, single file README.md**, language None, topics options/greeks. It is a COMMERCIAL PRODUCT AD for an AI options-analysis SaaS — no SKILL.md, no methodology, no code |
| 6 | GitHub repos | `q=alpha-gb` | total 37 — all unrelated (steel embrittlement, GBM-AlphaMissense oncology, LightGBM CN equity repo with 0★, hackathon teams) |
| 7 | GitHub repos | `q=alphagbm` | total 4 — same AlphaGBM commercial family |
| 8 | GitHub repos | `q="alphaagb"` (quoted) | **total_count: 0** — the exact name does not exist on GitHub |
| 9 | GitHub code search | `GET api.github.com/search/code?q=alphaagb` | **401 Requires authentication** (auth-blocked, logged honestly; repo-level null above is decisive) |
| 10 | npm | `GET registry.npmjs.org/-/v1/search?text=alphagb` | `total: 0` |
| 11 | PyPI | `GET pypi.org/pypi/alphagb/json`, `pypi.org/pypi/alphaagb/json` | **404 both** |

### PHASE 1 VERDICT
**AlphaAGB DOES NOT EXIST as a public skill.** The only "AlphaGB*" on the entire public internet is
AlphaGBM — a Chinese commercial AI-options/trading PRODUCT (76★ repo containing just a README ad;
a second repo is literally a marketing article). It has no SKILL.md, no research methodology, and is
not installable as a skill. No fabricable substitute exists under the requested name. This verdict is
INDEPENDENT of and confirms the prior agent's alphaAGM null (different name, fresh queries: quoted
exact-name search returns 0; prior agent never ran `q="alphaagb"` or npm).

## (b) WHAT WAS INSTALLED (disclosed substitution, fresh clone — NOT reused from sibling dir)

- **Installed**: `github.com/junsier9/quant-alpha-research-skill`, `git clone --depth 1` into
  `SKILL_ALPHAAGB_B/skill/`. **Commit sha `c848dfe4570f289eb99dda5daba468296a7d95b0`**
  (2026-05-07 11:44:07 +0800, main). Apache-2.0. SKILL.md sha256
  `886c452af61e7e549c437b6831a61079295007635b10af5e7418188991376c94`.
- **Fallback evaluation (both candidates re-checked today, per charter)**:
  - junsier9/quant-alpha-research-skill: 1★, pushed 2026-05-07; a falsification PROTOCOL
    (Stage-0 rejection-first, delay/shuffle/holdout/cost gates, fail-closed data trust,
    decision-form go/no-go reporting). Directly executable in one research slot.
  - eric554412/quant-research-os: 0★, pushed 2026-07-18; a 13-skill agent ORCHESTRATION
    architecture (ledger layer, coverage map, anti-rehash) — methodology sound but installing a
    13-skill crew for one research slot adds nothing this session; its best idea (machine-readable
    dead-idea ledger) is adopted as a recommendation in (e).
  - aresbit/quant-trade-skill: still README-404 per prior agent; skipped.
  → junsier9 wins for a falsification charter. Re-cloned fresh (verified same sha as sibling's
  clone) to keep this agent self-contained.

## (c) METHODOLOGY AS APPLIED (skill → GOAL100 contract)

1. **Orient from repo artifacts**: read GOAL100_FINAL_STATE.md (109 lines, full), champion eval,
   and ALL prior loop_team FINDINGS.md dead-lists (HUNT_FF2, HUNT_BASIS2, HUNT_CARRYFX, HUNT_FXMICRO,
   HUNT_TAIL, SKILL_ALPHAAGM + C3/D2/C5/A2/A3 findings where cited).
2. **CRITICAL GAP FOUND**: HUNT_EQMOM, HUNT_CROSSREGIME, HUNT_FF_STRATARB, HUNT_BASIS all DIED at
   API-429 in iter 4 with ZERO work (their LOG_1.log contains only the 429 error). Their charter
   slates were genuinely UNRUN: equity xs momentum/reversal on the 298-name panel, cross-asset
   macro-regime maps, FF stat-arb (covered later by FF2), commodity basis (covered later by BASIS2).
   → My Phase-2 slate = the dead agents' charters + remaining uncovered mechanisms.
3. **Research contract** (every probe): mechanism stated before coding; data verified on disk first
   (fail-closed); T+1 (`pos.shift(1)` inside `net_of`); costs 6.4bps/side on half-turn turnover;
   borrow 0.5%/yr on short notional; vol-target trailing expanding min-60d cap 3.0 (scale known at t);
   gates = SR_d>=0.6 (2008+), H1/H2>=0.3, <=2 neg yrs each >-5%, 200x BLOCK POSITION-LAG scramble
   p<0.05 (return permutation is DEGENERATE — not used), |corr|<0.15 to champion, ac1<0.5, uniqR>=0.08.
4. **Rejection-first smallest slices**; multiple-testing-aware interpretation (grids reported as
   grids, best-of-N discounted); drift-controls (always-short control) to separate timing from beta.
5. **Anti-patterns watched for**: "SR improved so alpha exists" (killed P6), "coverage passed so
   data is trustworthy" (USD_JPY looked 2007+ in the brief, is actually 2019-05+ — caught), missing
   evidence promoted to pass (none).

Champion baseline re-verified by my own loader: GOAL100_HONEST14V3_BALANCED_daily.csv, n=5086
2006-10-02..2026-08-27, SR_d 3.9228 full-span, ann_geo 43.13% (43.6%/SR 3.92 on 2008+ as claimed);
official `harness/eval.py` run: ann 36.3% arith full-span, MaxDD -4.92%, 1/21 neg yrs (2006 stub
-1.4%, disclosed pre-live). Consistent with commit message.

## (d) PHASE 2 — RESEARCH RESULTS (exact numbers; 9 probes, 0 admissible engines)

Gate key: SR(2008+)>=0.6 | H1,H2>=0.3 | negy<=2 & worst>-5% | poslag p<0.05 | |corr|<0.15 | ac1<0.5 | uniqR>=0.08.
All books: T+1, 6.4bps/side half-turn, borrow 0.5%/yr, vt10 trailing expanding cap3.

### P1 — EQMOM charter: big-cap xs short-term reversal (twelve_big, 298 names, 274/day avg)
Vol-normalized 5/10/21d return, tercile L/S, EW within leg.
| cfg | SR | ann | MDD | negy | H1/H2 | poslag | corr | verdict |
|---|---|---|---|---|---|---|---|---|
| lb5 sk0 | **-0.239** | -2.9% | -61.2% | 17 | -0.14/-0.31 | 0.000 | +0.025 | no-go |
| lb5 sk1 | -0.023 | -0.8% | -57.4% | 11 | — | 0.000 | +0.047 | no-go |
| lb10 sk0 | +0.007 | -0.5% | -49.9% | 10 | — | 0.000 | +0.023 | no-go |
| lb21 sk0 | -0.015 | -0.7% | -34.4% | 13 | — | 0.050 | +0.020 | no-go |
(Note: p=0.000 with negative real SR = scramble book keeps costs but not the losses; the SR gate
is decisive.) **Short-term reversal is sign-INVERTED in large caps 2008+** (5d losers keep losing).

### P2 — EQMOM charter: small-cap reversal + big-cap xs momentum
- EXT panel (440 names → 117 with >=4900 rows), rev lb5: SR **+0.235**, ann +8.0%, MDD **-90.6%**,
  negy 1 (worst **-90.1%**), H1 +0.40/H2 -0.35, poslag 0.190, corr +0.016 → no-go (SR, halves, MDD fail).
- xs momentum L/S lb63: SR **-2.189** (19 negy, worst -38.6%); lb126: **-1.590**; lb252: **-2.046**.
**Post-GFC daily xs momentum on US large caps is catastrophically negative.** EQMOM charter slate now
fully executed: 0/9 configs pass.

### P3 — CROSSREGIME charter: gold macro-regime maps (xau 2007-12..2026-08)
| book | SR | negy | poslag |
|---|---|---|---|
| real-rate(DFII10) 21d-chg z-rev → gold, zwin63 | +0.194 | 7 | 1.000 |
| same zwin126 | -0.131 | 13 | 1.000 |
| DXY-inverse trend → gold lb63 / lb126 | -0.043 / -0.210 | 10 / 13 | 1.000 |
| breakeven(T10YIE) trend → gold lb63 | -0.174 | 12 | 1.000 |
| breakeven z-rev126 → gold | +0.086 | 9 | 1.000 |
All dead. **The textbook "real rates down → gold up" daily map has no tradable edge here.**

### P4 — CROSSREGIME charter: rates curve + relative-equity ratios + liquidity
- 2s10s slope (us10y-us2y, dur-8 pnl): z-rev63/126/252 SR **-6.64/-5.79/-4.81** (19 negy each;
  uniqR 0.022-0.025 flatten-flag too); slope mom63/126 SR **-4.81/-4.17**. DEAD (and the low
  uniqR/positive-ac1 makes these candidate flatten artifacts on top of no-edge).
- QQQ/SPY ratio z-rev 21/63/126: SR -0.051/-0.230/-0.222 (poslag 1.000). DEAD.
- XLF/SPY ratio z-rev 21/63/126: SR +0.293/+0.011/-0.044. BEST 0.293 < 0.6. DEAD.
- WALCL>52w-median long-SPY gate: SR +0.216, poslag 1.000 (confirms D2's WALCL kill with my own battery).

### P5 — credit-equity map (baa-aaa spread z → SPY): zrev63 +0.212, zrev126 +0.171,
mom21 +0.178, continuous z126 +0.188 — all poslag 1.000, negy 8-10. DEAD (spread maps to SPY
carry, no timing).

### P6 — ⭐ HIGHEST-VALUE FINDING OF THE SESSION: the champion pool's QAxasts VIX leg is DRIFT, not timing
QAxasts (E1, in the 11-pool base of HONEST13V2/HONEST14V3) is a 5-leg TSMOM whose OWN meta says
"VIX-leg alone SR 1.08; drop-VIXS 0.25". Rebuilt the leg exactly (VIXCLS < MA189 → short, else long,
T+1, vt, costs+borrow):
| variant | SR | ann | MDD | negy | H1/H2 | poslag | corr |
|---|---|---|---|---|---|---|---|
| VIXSW ma126 | **1.327** | +17.2% | -18.2% | 2 (worst **-7.8%**) | 1.29/1.37 | **1.000** | +0.096 |
| VIXSW ma189 | 1.175 | +15.2% | -28.2% | 2 | 1.10/1.25 | **1.000** | +0.091 |
| VIXSW ma252 | 1.001 | +12.9% | -43.0% | 6 | 0.82/1.19 | 1.000 | +0.082 |
| ma189 + 3%/yr futures-roll haircut | 0.939 | +11.8% | -28.3% | 7 | — | 1.000 | +0.091 |
| ma189 + 8%/yr haircut | **0.546** | +6.3% | -33.2% | 12 | 0.47/0.62 | 1.000 | +0.091 |
| **drift control: ALWAYS-short-vol** (no signal) | 0.529 | +1.2% | — | — | — | — | — |
Gate card (best, ma126): SR 1.327 PASS · H1/H2 PASS · negy 2 PASS but **worst -7.8% < -5% floor FAIL** ·
**poslag p=1.000 FAIL** (random position lags BEAT the real alignment — the MA flip adds nothing
beyond VIX's negative drift) · corr +0.096 PASS · ac1 -0.053 PASS · uniqR 0.992 PASS. **5/7 gates
plus premise failure (VIX spot is untradeable; an 8%/yr roll haircut — mid-estimate for short VIX
futures — cuts SR to 0.546).** Independent proof it's drift: always-short-vol control keeps SR 0.53
of the leg's 1.01-1.33 with ZERO signal.
**Champion-dependence check (LOO diagnostic, equal-vt10 14-pool mean, honest label: DIAGNOSTIC not
deliverable):** full pool SR 3.607 / ann 28.1% → drop-QAxasts SR **3.596** / ann **28.7%** (negligible
dependence; the champion's SR does NOT lean on the VIX leg's drift — the blend's other 13 sleeves
compensate; drop-table for all 14 in scratch/p6c.py output). **No action required on the champion;
the finding is informational and a caution for any future QAxasts-weight increase.**

### P7/P8/P9 — FX weekday/momentum (USD_JPY brief-premise CORRECTED: fx/USD_JPY.csv starts **2019-05-15**, not 2007)
- USDJPY mean bp/day by dow (2019+): Mon -0.7, **Tue +7.9 (t=3.12)**, Wed +3.1, Thu +5.5 (t=1.92),
  Fri -5.5. Best of ALL 30 sign-maps (long-USD Mon-Wed, short Thu-Fri): SR **+0.599** — FAILS the 0.6
  gate by 0.001 AND is the best of 30 multiple-tested maps on a 7-year sample → no-go. Book blend
  with FX-tsmom63 satellites (EUR -0.085, GBP +0.001, AUD -0.438): SR +0.056. DEAD.
- P9 cross-pair confirmation of the Monday effect (all foreign-vs-USD pairs positive Monday:
  EUR +3.8bp t=1.86, GBP +4.7 t=2.01, AUD +7.6 t=2.69, NZD +3.9 t=1.39, CHF 0.0): gross ~5.6bp/Monday
  = 1.1bp/day avg vs 12.8bp weekly round-trip at 6.4bps/side → **dead by arithmetic** (independently
  re-derives FXMICRO's weekday kill; that's TWO sessions agreeing).

### BLOCKED (fail-closed, data-missing — logged, not faked)
- International 10y yields au/ca/ch/ez/gb/jp/nz10y: **MONTHLY, 2018+ only** (102 obs) → global rates
  momentum/carry UNTESTABLE at daily 2008+ gates (A2 hit the same wall).
- VXX/UVXY/VIXY ETN prices: absent on disk → the P6 short-vol family cannot be trade-verified.
- VIX futures term structure/roll chains: absent → roll haircut stays an assumption (3%/8% band used).
- (Prior, still standing): 5y TIPS, corporate TR indices, intraday pre-2024-12, China A-shares span.

### NEGATIVE LEDGER — new dead ideas this session (do not re-run)
Big-cap xs reversal lb5/10/21 (sk 0/1) · small-cap EXT reversal lb5 · xs momentum lb63/126/252 ·
gold×(real-rate chg zrev, DXY-inv trend, breakeven trend/zrev) · 2s10s slope zrev/mom (all windows) ·
QQQ/SPY + XLF/SPY ratio zrev · WALCL>median SPY gate · credit baa-aaa z/mom→SPY · short-VIX MA
regime timing (drift not timing; untradeable spot premise) · USDJPY weekday sign-maps (30-map grid) ·
FX tsmom63 satellites EUR/GBP/AUD · FX Monday long (sub-cost).

### (d-summary) **0 admissible engines delivered.** Champion unchanged:
GOAL100_HONEST14V3_BALANCED (ann 43.6% / SR_d 3.92 / MaxDD -4.92% / 0/19 neg yrs 2008+). Per-gate
best-of-session card (VIXSW ma126): 5/7 — FAILED scramble + worst-year floor + tradeability premise.

## Trade-record audit note (charter requirement)
No new engine was delivered (nothing passed), so there is no tradeable instrument/path to record
beyond the probes: P1/P2 would trade US equities from tools/quant/data/twelve_big & twelve_extend
(close prices); P3/P4/P5 would trade xau spot, us2y/us10y synth curve, SPY/QQQ/XLF, baa-aaa as SPY
overlay (data_fred + twelve_big); P6 would require VIX futures (NOT on disk — would NOT have been
tradeable as-built); P7-P9 would trade USD_JPY/EUR_USD/GBP_USD/AUD_USD/NZD_USD spot
(tools/quant/data/fx). Price paths = the on-disk close series cited, unmodified.

## (e) PERMANENT RECOMMENDATIONS
1. **Publish the iter-4 API-429 deaths in the coordinator standup** (EQMOM/CROSSREGIME/FF_STRATARB/
   BASIS did zero work; their slates were only partially covered by later agents). This session
   closed EQMOM+CROSSREGIME; FF_STRATARB was superseded by FF2, BASIS by BASIS2. Any future loop
   should verify sibling agents actually STARTED (LOG_1.log > 1 line) before accepting "done".
2. **Add the always-on drift control to the scramble battery**: P6 proved a book can pass SR/halves/
   corr/ac1/uniqR with poslag p=1.000 purely on asset drift (VIX short). Any single-asset timing
   sleeve should be reported next to its no-signal control (always-long / always-short) — 5-line addition.
3. **Machine-readable dead-idea ledger** (from eric554412's design, evaluated not installed): a
   `campaign/results/DEAD_IDEAS.csv` (family, data, SR, killing gate, agent) would have saved this
   session reading ~12 FINDINGS.md files; today's additions above are ready to append.
4. **Data-premise lint**: briefs say "fx 2007+", but fx/USD_JPY.csv is 2019-05+; audit data spans at
   charter-write time (one `idx.min()` per path) — two agents have now been misled (A2 monthly yields,
   my JPY span).
5. Keep V3 champion as-is; the QAxasts VIX-leg drift finding does NOT require removal (LOO: pool SR
   3.607→3.596 without it) but caps any future QAxasts weight increase.

## HONESTY NOTES
- Wrote only inside SKILL_ALPHAAGB_B/ (skill/, scratch/, sleeves/ (empty — nothing passed), FINDINGS.md).
- No sleeve delivered; champion untouched; verified byte-consistent with committed claims via
  independent loader + official eval.
- p7/p8 used USD_JPY from 2019 (data-bound, disclosed); all other probes 2008+ gates as stated.
- Scramble convention = FF2's audited position-lag battery, generalized to books
  (libb.book_position_lag_p: roll all name columns by same lag ∈[21,T-21], costs+borrow recomputed).
  For negative-SR probes p values are reported but not gate-relevant (SR gate is decisive).
- GitHub code search 401 (unauthenticated) — logged; repo-name search (0 hits for "alphaagb")
  is the decisive channel and was completed.
- groupby.apply yearly-stats trap (pandas 3.0, ALPHAAGM's self-caught bug): my yearly numbers come
  from gates/FF2 `full_stats` which produces sane values (spot-checked worst-year -90.1% EXT case
  against manual cumprod); no 10^76 explosion seen in any output used for a verdict.

SKILL_ALPHAAGB_B DONE
