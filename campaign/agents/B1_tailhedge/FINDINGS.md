# B1_tailhedge — Round 1 FINDINGS

**Mission**: tail-risk overlays that compress the LEFT TAIL of a high-return blend (DD/ann 0.34 -> 0.16, ann>=25%). Reproduce reference blend, then overlay de-risking / flight-to-safety / put-replication / protective-put sleeves. T+1, 6bps/side, trailing-only, all gates or reject.

## 0. Reference blend reproduced
14 daily sleeves (XGB1y_deploy is monthly-only in xgb_horizons, dropped) + EW + vol-target 22% (expanding ewm63, shift-1, clip 5), applied 6bps.
- **BASELINE (aligned 2008+): ann 42.1%, vol 19.3%, SR 2.18, MaxDD -19.1%, DD/ann 0.453.** No negative years (worst +5.9% in unaligned series). Charter's 50% baseline not exactly reproduced (XGB1y_deploy daily missing) but the DD structure is representative.

**Key structural fact**: the blend's deep drawdowns (2024-07/-19.1%, 2022-01/-18.9%, 2011-08/-18.4%, 2015-08/-17.5%, 2018-10/-17.3%, 2025-03/-16.1%, 2026-03/-15.0%) occur at **avg VIX 14-33, many at LOW/MODERATE VIX** (2024 avgvix 19, 2015 avgvix 20, 2018 avgvix 21). They are diffuse *internal-sleeve* grind-downs (50-60% up-days within the episode), **not** market-crash event. This is why market-crash hedges cannot compress them.

## 1. VIX level/term crash gate (de-risk blend when trailing VIX high; Idea 1)
- Hard-off when trailing(shift1) VIX>thr, re-engage below thr-4, floor in {0,0.3,0.5}. Tested thr in {25,30,35,40}.
- **VERDICT: FAIL — counterproductive.** De-risking at high VIX *worsens* MaxDD (thr30 floor0: MaxDD went -19.1% -> **-25.8%**, DD/ann 0.815) and cuts ann. The blend holds sleeves that *profit* in stress (gold AP_gold, bond trend, tsmom); turning them off during VIX spikes kills exactly the diversifying carry)Skip. Best (thr40 floor0.5): ann 36.5%, MaxDD -19.1%, DD/ann 0.522 — no improvement.

## 2. Realized-vol accelerator + drawdown throttle (Idea 2)
- Step down gross when trailing realized vol > mult*long-run vol OR trailing drawdown < -thr, hysteresis. Grid vol_win {21,63}, mult {1.2,1.3,1.5}, dd_thr {0.05,0.08}, floor clip 0.15.
- **VERDICT: FAIL — cuts return proportionally; DD/ann ~flat or worse.** (21,1.2,0.05): ann 24.0% (was 36%), MaxDD -12.7%, DD/ann 0.531 (was 0.526). (21,1.5,0.08): ann 28.6%, MaxDD -16.6%, DD/ann 0.581. A trailing-drawdown feedback gate even self-defeats: scaling by drawdown keeps the scaled curve from ever crossing threshold, gate never fires (0 triggers).

## 3. Flight-to-safety: long gold+10y-Treasury when credit spread (BAA-AAA z) widens (Idea 3)
- Overlay = long xau + short-duration 10y (dur 6) when trailing spread z > thr, weights {0.1-0.3}. Spread available 1986+, real 2008+.
- **VERDICT: FAIL — badly worse.** Standalone SR ~0.1; combined MaxDD *explodes* (zt0.5: **-41.9%**, zt1.5 gw0.15: **-46.1%**, up to -69% at higher weights). The blend ALREADY owns gold and treasury sleeves; adding more on credit stress just concentrates the same factor and adds vol with no return. 8-9/19 negative years standalone.

## 4. Put-replication / convexity via VIX (Idea 4)
- (a) VIX-z continuous short-SPX: k*max(0, z(VIX, trailing 22/60/120)). Standalone SR max **0.18**, H1 negative, fails scramble. Bleeds (long-VIX carry).
- (b) Gamma: short SPX by depth of trailing blend drawdown (deeper drawdown -> more protection), k {0.3-1.0}. Standalone SR **0.45** (fails >=0.6), fails scramble (~7-74% pctile), and combined MaxDD stays **-19.2%** (unchanged).
- **VERDICT: FAIL.** Convexity-on-VIX does not reduce this blend's MaxDD because the tail is not a VIX event.

## 5. Protective put on blend — VIX-gated short SPX (Idea 5)
- **Binary combo crash-gate (BEST candidate):** short SPX size 0.3 when trailing(shift1) VIX>18 AND trailing(shift1) SPX 5d momentum<0. Standalone: **SR 0.58-0.67, H1 0.60/H2 0.75, 0-1 negative years (worst +0.0%)** — passes FULL/halves/yearly. **FAILS the signal-scramble gate: real SR > only 8.5th pctile of 200 shuffles** (sparse binary on/off -> time-order adds little, ~50% of days inactive). Combined: ann 42.1->44.4%, but MaxDD (-19.1% -> **-20.7%**) and DD/ann (0.453->0.467) do NOT improve. Corr 0.70 to L_S_130_30 (it's just beta-timing equity).
- Pure VIX-gated short-SPX (no mom condition): standalone SR up to 0.68 but worst year -5.7% (fails yearly <=2, each >-5%).
- **VERDICT: FAIL (scramble gate + no MaxDD compression).** Best true insurance candidate; still NOT MaxDD-compressing and not scramble-robust.

## 6. Other
- SPX trend-short overlay (short SPX when below trailing 20/50/100/200d MA): standalone SR 0.30-0.37, and combined MaxDD WORSENS (-19.1% -> up to -23%). Confirms blend is not simply equity-beta.

## COMBINED BOTTOM LINE (honest)
**No idea in the charter produces a sleeve passing ALL gates AND compressing the reproduced blend's MaxDD. No sleeve is saved (per contract).** Root cause: the reproduced/coordinator blend's drawdowns are diffuse internal-sleeve losses in low-moderate VIX regimes, NOT market-crash events; the blend already carries the defensive sleeves (gold, bonds, tsmom) that crash-hedges would add. Market-crash overlays (SPX-short, VIX gates, FTS) therefore either add vol without DD reduction, worsen DD (factor concentration / missed V-recoveries), or fail the scramble honesty gate (sparse binary hedge). DD/ann 0.34->0.16 at ann>=25% is not achievable on this diffuse blend via tail overlays; it would require redesigning the blend's constituent risk (outside this agent's tail-hedge mandate).
Best informational insurance candidate for coordinator: **B1_crashoverlay_repro.py** (combo VIX>18 + SPX 5d mom<0 short-SPX) — adds +2.3pp ann standalone (SR~0.6), but adds ~1.6pp MaxDD and fails scramble; NOT gate-valid.

## Lookahead traps documented
- Never use same-day VIX/SPX/credit; all signals shift(1) (A5 prior finding 2.30->1.13 honest).
- VIX-futures carry cannot be synthesized from FRED VIX *level* alone; long-VIX proxy bleeds.
- Sparse binary crash gates systematically fail the signal-scramble gate (ordering adds little) — an honesty trap for hedges.

## 7-... (ideas exhausted in round 1)
All 5 charter ideas tested; all rejected with numbers above. Repro: campaign/scripts/B1_crashoverlay_repro.py. No sleeves saved in B1_tailhedge/sleeves/.

ROUND 1 DONE
