"""Deep-gate best: ind_bill w252 longflat QQQ (0.585, 4 neg). Scramble + 2008+ span + beta check
vs buy&hold QQQ (is it just long-QQQ drift with modest timing?)."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "campaign"))
import numpy as np, pandas as pd
import ta_eng
from bt import gates, backtest as btb
from bt.engine import lag_signal, vol_target_scale, cap_leverage

df = ta_eng.load_auctions()
s = ta_eng.indirect_share(df, "Bill")
sig = ta_eng.zgate(s, win=252, invert=False)
sig_lf = sig.where(sig > 0, 0.0)

def build(sym):
    d = pd.read_csv(os.path.join(ROOT, "tools/quant/data/more_etf", f"{sym}.csv"), parse_dates=["date"])
    px = d.set_index("date")["close"].astype(float)
    px = px[~px.index.duplicated(keep="last")].sort_index()
    return px

for sym in ("QQQ", "DIA"):
    px = build(sym)
    r = px.pct_change()
    # raw book: positions = lag(sig_lf) vol-targeted
    sig_a = sig_lf.reindex(r.index).ffill().fillna(0.0)
    scale = vol_target_scale(r).fillna(1.0)
    w = (lag_signal(sig_a) * scale).fillna(0.0)
    wc = cap_leverage(w.to_frame("w"), max_lev=1.6)
    from bt.engine import cost_turnover, borrow_cost, margin_cost
    net = (wc["w"] * r - cost_turnover(wc, 6.4) - borrow_cost(wc, 0.005)
           - margin_cost(wc["w"].abs(), 0.045, 1.6)).dropna()
    rep = gates.run(net)
    p, real = gates.scramble_positions(wc["w"], r)
    # buy & hold same span
    bh = r.reindex(net.index).dropna()
    bh_sr = bh.mean() / bh.std() * np.sqrt(252) if bh.std() > 0 else 0
    print(f"{sym}: SR={rep['sr']:.3f} neg={rep['neg_years']} worst={rep['worst']:.3f} "
          f"scramble_p={p:.3f} | B&H SR={bh_sr:.2f} | exposure={float((wc['w']>0).mean()):.2f}")

# 2008+ span strict
px = build("QQQ"); r = px.pct_change()
sig_a = sig_lf.reindex(r.index).ffill().fillna(0.0)
scale = vol_target_scale(r).fillna(1.0)
w = (lag_signal(sig_a) * scale).fillna(0.0)
wc = cap_leverage(w.to_frame("w"), max_lev=1.6)
from bt.engine import cost_turnover, borrow_cost, margin_cost
net = (wc["w"] * r - cost_turnover(wc, 6.4) - borrow_cost(wc, 0.005)
       - margin_cost(wc["w"].abs(), 0.045, 1.6)).dropna()
net08 = net[net.index >= "2008-01-01"]
rep = gates.run(net08)
print("2008+ :", f"SR={rep['sr']:.3f} neg={rep['neg_years']} worst={rep['worst']:.3f}")
yr = net08.groupby(net08.index.year).apply(lambda x: (1 + x).prod() - 1)
neg = {int(k): round(float(v), 3) for k, v in yr.items() if v < 0}
print("2008+ neg years:", neg)
