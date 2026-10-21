"""d05: verify the structural arithmetic that makes capital-diluting sleeves unable to
clear V2 8c (dAnn>0 HARD) against this champion, and check the blend mechanic itself."""
import os, sys, json
import numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign")
import emfx_lib as L
from bt.metrics import ann_geo, sharpe_d, max_dd, neg_years
CH=L.champion()
cs=L.stats(CH)
print("champion: ann %.4f%% SR %.3f vol %.4f%% MDD %.4f%% negy %d"%(
    cs["ann"]*100, cs["sr"], cs["vol"]*100, cs["mdd"]*100, cs["neg_years"]))
print("\nderivation check: dAnn ~= (1-w)*(ann_s - ann_c) + variance term")
for wc in (0.975, 0.95, 0.90):
    for label, ann_s in (("zero-return flat", 0.0), ("C2 net (real)", None)):
        pass
net2 = pd.read_csv(os.path.join(HERE,"nets","C2_BRL_CARRY_MED.csv"),parse_dates=["date"]).set_index("date")["ret"]
flat = pd.Series(0.0, index=CH.index)
for nm, s in (("flat(0%)", flat), ("C2(real)", net2), ("champ-itself", CH)):
    ann_s = ann_geo(s) if s.abs().sum()>0 else 0.0
    for wc in (0.975, 0.95, 0.90):
        b = wc*CH + (1-wc)*s
        d = ann_geo(b) - cs["ann"]
        pred = (1-wc)*(ann_s - cs["ann"])
        print("  %-14s w_sleeve=%.3f  dAnn=%+.4f pp  (1-w)(as-ac)=%+.4f pp  resid=%+.4f"%(nm,1-wc,d*100,pred*100,(d-pred)*100))
print("\n=> a capital-diluting sleeve clears 8c only if ann_s > champion ann (%.2f%%) [or a big variance gift]."%(cs["ann"]*100))
print("   best sleeve ann in this hunt: %.2f%% (C2). Gap: %.2f pp."%(
    L.stats(net2)["ann"]*100, (cs["ann"]-L.stats(net2)["ann"])*100))
print("\ntruncation/causality already verified: max abs dev 0.0 on every candidate (rebuild on 70%% sample).")
