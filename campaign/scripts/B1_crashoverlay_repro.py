"""B1_tailhedge crash-overlay reproduction (INFORMATIONAL — does NOT pass all gates).
Overlay: short SPX, size 0.3, when trailing(shift1) VIX>18 AND trailing(shift1) SPX 5d momentum<0.
6bps/side on turnover. T+1.
FULL window standalone SR ~0.58-0.67 across variants; FAILS scramble gate (sparse binary -> real SR
 ~8th pctile of scrambled). Adding to reference blend does NOT compress MaxDD (diffuse blend has no
market-crash drawdown signature). Reproduced for coordinator's reference only.
"""
import pandas as pd, numpy as np, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
from harness.data import fred

def build(blend_path="/tmp/blend.csv", thr=18, mom=5, size=0.3):
    blend = pd.read_csv(blend_path, index_col=0, parse_dates=True)["blend"]
    vix = fred("vix"); spx = fred("spx"); spxr = spx.pct_change()
    df = pd.concat([blend, spxr, vix], axis=1, keys=["b", "sr", "v"]).dropna()
    df = df[df.index >= pd.Timestamp("2008-01-01")]
    b, sr, v = df["b"], df["sr"], df["v"]
    sig = ((v.shift(1) > thr) & (spx.pct_change(mom).shift(1).reindex(sr.index) < 0)).astype(int).values * size
    sig_s = pd.Series(sig, index=sr.index)
    poslag = sig_s.shift(1).fillna(0)
    ov = sr * poslag - np.abs(sig_s.diff()).fillna(0) * 6 / 1e4
    return b, ov

if __name__ == "__main__":
    b, ov = build()
    srf = ov.mean() / ov.std() * np.sqrt(252)
    tot = b + ov
    eq = (1 + tot).cumprod(); mdd = (eq / eq.cummax() - 1).min()
    print(f"overlay standalone SR={srf:.2f} ann={ov.mean()*252*100:.1f}% MaxDD={((1+ov).cumprod()/(1+ov).cumprod().cummax()-1).min()*100:.1f}%")
    print(f"BLEND ann={b.mean()*252*100:.1f}% MaxDD={((1+b).cumprod()/(1+b).cumprod().cummax()-1).min()*100:.1f}%")
    print(f"BLEND+OVERLAY ann={tot.mean()*252*100:.1f}% MaxDD={mdd*100:.1f}% DD/ann={abs(mdd)/(tot.mean()*252):.3f}")
