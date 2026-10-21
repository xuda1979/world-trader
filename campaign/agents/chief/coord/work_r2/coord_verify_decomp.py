#!/usr/bin/env python3
"""Coordinator verification of the four-corner premise (standup 07:2x, pre-pin-update)."""
import importlib.util
import hashlib
import sys

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/bt/tests")
spec = importlib.util.spec_from_file_location(
    "t", "/Users/daxu/software/world-trader/campaign/bt/tests/test_audit_champ2_round2.py")
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
import pandas as pd
import numpy as np

PREFIX = {
    "diescrack": "/Users/daxu/software/world-trader/campaign/agents/chief/coord/CAMP_COST/sleeves/diescrack__prefix.csv",
    "dualmom": "/Users/daxu/software/world-trader/campaign/agents/chief/coord/CAMP_COST/sleeves/dualmom__prefix.csv",
    "brwt15": "/Users/daxu/software/world-trader/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt15__prefix.csv",
    "QAxasts": "/Users/daxu/software/world-trader/campaign/agents/chief/coord/CAMP_COST/sleeves/QAxasts__prefix.csv",
}


def load_any(p):
    df = pd.read_csv(p, index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)


pool_old = pd.DataFrame(
    {n: load_any(PREFIX.get(n, f"{t.ROOT}/{t.PATHS[n]}")).dropna() for n in t.PATHS})
pool_old = pool_old[pool_old.index >= "2008-03-31"]
relw_old = t._relw(pool_old)
leaky_old = t._rebuild(pool_old, relw_old, lag=False)
arch = pd.read_csv(t.ARCH, index_col=0, parse_dates=True).iloc[:, 0]
print("leaky(prefix) vs ARCH maxdev:", t._maxdev(leaky_old, arch))

causal_old = t._rebuild(pool_old, relw_old, lag=True)
champ = pd.read_csv(t.CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
print("causal(prefix) vs NEW CHAMP maxdev:", t._maxdev(causal_old, champ))
print("causal(prefix) vs ARCH maxdev:", t._maxdev(causal_old, arch))

j = pd.concat([champ.rename("c"), causal_old.rename("o")], axis=1, join="inner").dropna()
d1 = j.c - j.o
print("costfix delta: sum=%.3e maxabs=%.3e sum<0: %s" % (d1.sum(), d1.abs().max(), bool(d1.sum() < 0)))
j2 = pd.concat([causal_old.rename("c"), leaky_old.rename("l")], axis=1, join="inner").dropna()
d2 = j2.c - j2.l
print("shift delta: maxabs=%.3e" % d2.abs().max())
j3 = pd.concat([champ.rename("c"), arch.rename("a")], axis=1, join="inner").dropna()
d3 = j3.c - j3.a
print("identity |D1+D2-D3| max:", float((d1 + d2 - d3).abs().max()))
print("corr(champ, arch):", float(j3.c.corr(j3.a)))
h = hashlib.sha256(open(t.WFILE, "rb").read()).hexdigest()
print("new weights sha256:", h)
