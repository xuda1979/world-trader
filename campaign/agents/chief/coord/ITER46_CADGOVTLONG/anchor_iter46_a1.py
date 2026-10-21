"""ITER46 A1 anchor (pre-seal, 2026-09-19 session 26).
Re-types the FROZEN ITER24 generator (driver_2026-09-19.py load_series + trend_sleeve,
rates branch) verbatim and proves it against the ITER24-saved sibling sleeve
cad_govt_10y.csv (dur 9.5) BEFORE the candidate cell is computed. Also records the
cad_govt_long.csv data vintage. No candidate computation here."""
import hashlib
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
K, CAD, VT, VCAP, SBPS, SSTART = 378, 42, 0.12, 5.0, 6.4, "2007-01-01"

def load_series(rel):
    df = pd.read_csv(ROOT + "/tools/quant/data/" + rel, index_col=0, parse_dates=True)
    col = "close" if "close" in df.columns else "value"
    s = df[col].astype(float)
    return s[~s.index.duplicated(keep="last")].sort_index()

def trend_sleeve(s, kind, dur=None):
    if kind == "rates":
        y = s / 100.0
        tr = (-dur * y.diff() + y / 252.0).dropna()
    else:
        tr = s.pct_change().dropna()
    sig = (tr.rolling(K).mean() > 0).astype(float)
    W = sig.iloc[::CAD].reindex(tr.index).ffill().fillna(0.0)
    gross = (W.shift(1) * tr)[SSTART:]
    turn = (W.shift(1) - W.shift(2)).abs()[SSTART:].fillna(0.0)
    net = (gross - turn * SBPS / 1e4).dropna()
    lev = (VT / np.sqrt(252) / net.expanding(60).std().shift(1)).clip(0, VCAP).fillna(0.0)
    return (net * lev).dropna()

def recon(regen, path):
    c = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    c = pd.to_numeric(c, errors="coerce")
    j = pd.concat([c.dropna().rename("c"), regen.rename("g")], axis=1, join="inner").dropna()
    dev = float((j.c - j.g).abs().max())
    ok = (len(j) == int(c.notna().sum())) and dev < 1e-12
    return ok, dev, len(j), int(c.notna().sum())

lines = []
for sib, dur in (("cad_govt_10y", 9.5), ("cad_govt_2y", 1.9)):
    r = trend_sleeve(load_series("dm_rates/" + sib + ".csv"), "rates", dur)
    r.index.name = "date"
    ok, dev, n, nc = recon(r, ROOT + "/campaign/agents/chief/coord/ITER24_DA/sleeves/" + sib + ".csv")
    line = "A1 sibling %s (dur=%.1f) regen-vs-ITER24-saved: ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (sib, dur, ok, dev, n, nc)
    lines.append(line); print(line)
    assert ok, "A1 sibling recon failed - fail closed: " + sib

raw = pd.read_csv(ROOT + "/tools/quant/data/dm_rates/cad_govt_long.csv", index_col=0, parse_dates=True)
s = raw["value"].astype(float)
s = s[~s.index.duplicated(keep="last")].sort_index()
isr = s[(s.index >= "2008-03-31") & (s.index < "2017-01-01")]
line = ("A1 data vintage cad_govt_long: n=%d span %s..%s first=%.2f last=%.2f ISrows=%d "
        % (len(s), str(s.index[0].date()), str(s.index[-1].date()), float(s.iloc[0]), float(s.iloc[-1]), len(isr)))
line += "FSok=%s start_ok=%s" % (str(s.index[-1] >= pd.Timestamp("2024-01-01")), str(s.index[0] <= pd.Timestamp("2008-03-31")))
lines.append(line); print(line)
with open(ROOT + "/campaign/agents/chief/coord/ITER46_CADGOVTLONG/anchor_iter46_a1.log", "w") as fh:
    fh.write(chr(10).join(lines) + chr(10))
print("A1 LOG WRITTEN")
