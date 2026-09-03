#!/usr/bin/env python3
"""Machine-readable DEAD-IDEA / negative-result LEDGER for GOAL100.
Parses the FINAL_STATE + loop_team FINDINGS for rejected/unrun ideas and writes
campaign/results/DEAD_IDEAS.csv — a single file to check before proposing any new engine.
(Recommendation #6 from SKILL_ALPHAAGM; avoids re-archaeology across 10 FINDINGS.md.)
"""
import pandas as pd

# Hand-curated from GOAL100_FINAL_STATE.md + loop_team FINDINGS.md (iter1-5) + newest negs.
rows = [
 # (idea, status, evidence, source)
 ("FF factor premia (HML/SMB/OP/INV)", "dead", "all negative 2008+", "HUNT_FF2"),
 ("industry/decile portfolios (L/S)", "dead", "zero-to-negative PIT", "HUNT_FUNDAMENTAL"),
 ("equal-wt betting-against-beta (BAB)", "dead", "short-highvol=shorting survivors", "HUNT_FUNDAMENTAL"),
 ("MM naive ivol", "dead", "negative", "HUNT_FUNDAMENTAL"),
 ("value/growth/profitability screens", "dead", "zero predictive power PIT", "HUNT_FUNDAMENTAL"),
 ("FX carry on 8 major pairs", "dead", "weak/decay", "HUNT_CARRYFX"),
 ("NG/oil basis (single)","dead","covered by existing sleeves","multiple"),
 ("gold-silver spread","dead","no edge","multiple"),
 ("credit as PAPER synth (H21_f5/br,A1credit)","dead","lease/synth corr 0.03, removed","FINAL_STATE"),
 ("MHX annual retrain","dead","SR0.45 vs claimed 5.20, unreproducible","FINAL_STATE"),
 ("A1inf same-close leak","dead","same-close signal leak, removed","FINAL_STATE"),
 ("XGB1y flattened-daily","dead","ac1 0.951, 211 distinct values/4684rows, removed","LOOP_XGB1YFLAT"),
 ("FOMC x natgas/gold","dead","no edge","SKILL_ALPHAAGM"),
 ("M2-gold","dead","no edge","SKILL_ALPHAAGM"),
 ("CFNAI gates","dead","no lift","SKILL_ALPHAAGM"),
 ("calendar-seasonal equity book","dead","perm-SR p0.258 > real 0.365 (fail)","SKILL_ALPHAAGM"),
 ("fx deposit-rate carry (blocked)","blocked","need PIT deposit rates (not on disk)","SKILL_ALPHAAGM"),
 ("China A-share (cn)","blocked","only ~1.6y span-insufficient","SKILL_ALPHAAGM"),
 ("NKY calendars","dead","no daily span on disk","SKILL_ALPHAAGM"),
 ("propane","blocked","data missing","SKILL_ALPHAAGM"),
 ("TIPS breakeven tradable","blocked","no tradable instrument span","SKILL_ALPHAAGM"),
 ("SR-lift vol/timing overlay (60+ variants)","dead","champion whitened, max dSR+0.035<0.15, scramble p0.085-0.115","HUNT_VOLOVERLAY"),
 # iter6 SKILL_ALPHAAGB_B (13 new)
 ("big-cap xs short-term reversal (twelve_big lb5/10/21)","dead","sign-inverted post-2008, SR -0.24..-0.02","SKILL_ALPHAAGB_B"),
 ("small-cap EXT reversal lb5","dead","MDD -90.6%, worst yr -90.1%, SR 0.24, halves fail","SKILL_ALPHAAGB_B"),
 ("xs momentum L/S big-cap (lb63/126/252)","dead","catastrophically negative SR -2.2..-1.6","SKILL_ALPHAAGB_B"),
 ("gold x macro maps (real-rate chg, DXY-trend, breakeven)","dead","no tradable daily edge, all dead; poslag p=1.0","SKILL_ALPHAAGB_B"),
 ("rates curve 2s10s slope zrev/mom","dead","SR -6.6..-4.2, flatten-artifact flag","SKILL_ALPHAAGB_B"),
 ("QQQ/SPY + XLF/SPY ratio zrev","dead","SR <=0.29","SKILL_ALPHAAGB_B"),
 ("WALCL>median SPY gate","dead","SR 0.22, poslag 1.0","SKILL_ALPHAAGB_B"),
 ("credit baa-aaa z/mom -> SPY","dead","SR <=0.21, poslag 1.0","SKILL_ALPHAAGB_B"),
 ("short-VIX MA regime timing","dead","drift not timing (always-short control 0.53 SR); untradeable spot; roll 8%/yr cuts to 0.55","SKILL_ALPHAAGB_B"),
 ("USDJPY weekday sign-maps (30-grid)","dead","best SR 0.599 <0.6 gate & best-of-30","SKILL_ALPHAAGB_B"),
 ("FX tsmom63 satellites EUR/GBP/AUD","dead","SR <=0.09","SKILL_ALPHAAGB_B"),
 ("FX Monday long (all pairs)","dead","~1.1bp/day vs 12.8bp weekly cost","SKILL_ALPHAAGB_B"),
 ("international 10y daily (au/ca/ch/ez/gb/jp/nz)","blocked","MONTHLY 2018+ only, 102 obs","SKILL_ALPHAAGB_B"),
 # iter6b wave
 ("48-industry cross-industry relative momentum (KF)","dead","mom lb21/63/126 & 12-1 all negative; best longonly SR 0.22 poslag p=0.70; R8.xml exec fidelity 45/48 industries unverified","HUNT_INDUSTRY48"),
 ("sector-basket relative momentum (SPDR pairs)","dead","all <=0.43; z-reversion w/o XLE near-miss 6/7 gates but 8/19 neg-yrs","HUNT_CROSSASSET2"),
 ("rates-curve steepener mom/rev (2s5s/2s10s/5s30s)","dead","best 2s5s SR 0.46 H2-only post-2013; ETF-DV01 execution negative","HUNT_CROSSASSET2"),
 ("credit-OAS momentum on real HYG/LQD (baa-aaa/T10YIE)","dead","best 0.27; credit cycle priced or beta-dominated","HUNT_CROSSASSET2"),
 ("BAML OAS daily as 2008+ signal","blocked","data starts 2023-09 (793 rows)","HUNT_CROSSASSET2"),
 ("xs short-term reversal on twelve_liq (raw+volnorm, ON/IC)","dead","sign-inverted as EQMOM; best zero-cost SR 0.27, full-engine best net -0.07..-2.47","HUNT_LIQREV"),
 ("overnight/intraday decomposition harvesting (twelve_big)","dead","ON-mom t+5.0 next-day-ON real but unownable at 6.4bps; honest RT SR 0.73/-0.82 vs paper 2.13; cc books SR<=0.28; weekday/IC/ONIC dead","HUNT_OVNIGHT"),
]
df = pd.DataFrame(rows, columns=["idea","status","evidence","source"])
df.to_csv("campaign/results/DEAD_IDEAS.csv", index=False)
print(f"wrote {len(df)} dead/blocked ideas to campaign/results/DEAD_IDEAS.csv")
print(df[['status','idea']].to_string(index=False))
