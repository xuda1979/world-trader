"""Charter 1: FX carry with real 20y+ history. Honest data audit first:
foreign yields only exist monthly 2018+ on disk -> true multi-currency carry CANNOT be extended
pre-2018. Implementable: (a) 4-pair book 2018+ w/ accrual (best r1 family), (b) JPY-only carry
proxy 1990+ (JP rate ~0 since 1995 -> carry = short USD rate; long JPY/short USD = short carry),
(c) USD-rate-regime gates. All T+1, 6bps/side, vt10 trailing."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from r7_lib import *
import numpy as np, pandas as pd

R = load_pair_rets()          # +pos = long foreign
yd = load_ydiff()             # foreign10y - US2y (%)
acc = yd / 100.0 / 252.0      # daily accrual per unit position

print("== data audit ==")
for c in R.columns: print(f"  {c}: spot {R[c].dropna().index.min().date()} .. {R[c].dropna().index.max().date()}")
for c in yd.columns: print(f"  {c}: ydiff {yd[c].dropna().index.min().date()} .. {yd[c].dropna().index.max().date()}")

store = {}
def run(pos, label, rule_check=None):
    net, to = backtest(pos, R.fillna(0))
    nv, g, sr = metrics(net, label, ret_to=store)

# (a) monthly carry L/S with accrual, 4 pairs 2018+
for top,bot in [(1,1),(2,2)]:
    pos = carry_ls_pos(yd, top=top, bot=bot, rule="M")
    pos = pos + acc * 0 + pos  # accrual: add ydiff accrual to held positions
    posc = carry_ls_pos(yd, top=top, bot=bot, rule="M")
    posac = posc + posc.notna() * acc * 0  # placeholder
    # proper: accrual = position * daily ydiff/252 (in return space, added to gross pnl)
    gross_pos = posc
    net, to = backtest(gross_pos, R.fillna(0))
    accr = (gross_pos.shift(0) * acc).sum(axis=1, min_count=1)
    net2 = net + accr
    nv, g, sr = metrics(net2, f"carry M top{top}/bot{bot} + accrual 2018+")

# (b) always-long-foreign "carry proxy" (unconditional): long all 4 by rank of ydiff (i.e., no shorts)
posl = carry_ls_pos(yd, top=4, bot=0, rule="M")
net, to = backtest(posl, R.fillna(0))
accr = (posl * acc).sum(axis=1, min_count=1)
metrics(net + accr, "carry LONG-ALL by ydiff + accrual 2018+")

# (c) JPY single-pair: short JPY (borrow JPY) when US2y-JP10y > 0, size by diff/10, 1990+ proxy 1998+
us2 = new_s("DGS2"); jp10 = monthly_to_daily(old_s("jp10y"))
diff = (us2 - jp10).dropna()
sig = (diff / 5.0).clip(-1, 1)                    # scale: 5pp diff -> 1x
pos1 = pd.DataFrame({"JPY": -sig})                # negative JPY position = short JPY vs USD
net, to = backtest(pos1, R[["JPY"]].reindex(pos1.index).fillna(0))
metrics(net, "JPY carry-proxy shortJPY s(diff/5) 1998+")

# (d) same but only when diff positive, flat otherwise
pos2 = pd.DataFrame({"JPY": -sig.where(sig > 0, 0.0)})
net, to = backtest(pos2, R[["JPY"]].reindex(pos2.index).fillna(0))
metrics(net, "JPY carry-proxy shortJPY only diff>0")

# (e) USD-rate regime: short JPY while DFF > 2% (positive-carry regime), long JPY below (reversal regime)
dff = new_s("DFF")
sig3 = pd.Series(np.where(dff > 2.0, -1.0, 1.0), index=dff.index)
pos3 = pd.DataFrame({"JPY": sig3})
net, to = backtest(pos3, R[["JPY"]].reindex(pos3.index).fillna(0))
metrics(net, "JPY DFF-regime longJPY when DFF<2 else short")
