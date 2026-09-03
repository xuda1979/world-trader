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
]
df = pd.DataFrame(rows, columns=["idea","status","evidence","source"])
df.to_csv("campaign/results/DEAD_IDEAS.csv", index=False)
print(f"wrote {len(df)} dead/blocked ideas to campaign/results/DEAD_IDEAS.csv")
print(df[['status','idea']].to_string(index=False))
