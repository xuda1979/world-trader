"""IDEAS 3-5: SMB timing via ME deciles; 10 prior-12-2 decile TS books; 6-portfolio 2x3
factor momentum (EW of 6 legs each with own 126d TS momentum), weekly."""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
from c1_lib import load_kf, bt, KF
from c1r2_lib import evaluate, weekly_positions

# --- IDEA 3: SMB spread timing (ME deciles small-minus-big) ---
me = load_kf(f'{KF}/Portfolios_Formed_on_ME_daily.csv', 'Average Value Weighted Returns -- Daily')
smb = me['Lo 10'] - me['Hi 10']
for w in [21, 63, 126, 252]:
    pos = np.sign(smb.rolling(w).sum())
    pos = pd.DataFrame({'smb': pos})
    net, _, _ = bt(pos, pd.DataFrame({'smb': smb}))
    evaluate(net, f'SMB sign-timing w{w}')

# --- IDEA 4: 10 prior-12-2 deciles: EW of per-decile TS momentum books (vol-scaled) ---
p12 = load_kf(f'{KF}/10_Portfolios_Prior_12_2_Daily.csv', 'Average Value Weighted Returns -- Daily')
dec = list(p12.columns)
rets_d = p12[dec]
mom_leg = {}
for look in [63, 126, 252]:
    # per-decile TS: long decile if its own trailing look ret > 0, short if < 0
    sig = np.sign(rets_d.rolling(look).sum())
    # vol-scale each leg to same risk then EW
    v = rets_d.rolling(21).std()
    w = sig * (0.10/ (v*np.sqrt(252))).clip(upper=1.0) / rets_d.shape[1]
    net, _, _ = bt(w.fillna(0), rets_d)
    evaluate(net, f'momdec TS-EW look{look} daily')
    netw, _, _ = bt(weekly_positions(w.fillna(0)), rets_d)
    evaluate(netw, f'momdec TS-EW look{look} weekly')

# winner-minus-loser vol-scaled book (Hi-Lo with per-decile vol scaling)
hi, lo = rets_d.iloc[:, -1], rets_d.iloc[:, 0]
sig = np.sign(hi.rolling(126).sum() - lo.rolling(126).sum())
pos = pd.DataFrame({'hl': sig})
net, _, _ = bt(pos, pd.DataFrame({'hl': hi - lo}))
evaluate(net, 'Hi-Lo decile 126 sign')

# --- IDEA 5: 6-portfolio 2x3 factor momentum ---
p6 = load_kf(f'{KF}/6_Portfolios_2x3_Daily.csv', 'Average Value Weighted Returns -- Daily')
legs = p6[[c for c in p6.columns if c != 'RF']][:6]
print('legs:', list(legs.columns))
for look in [126, 252]:
    sig = np.sign(legs.rolling(look).sum())
    w = sig / legs.shape[1]
    net, _, _ = bt(w.fillna(0), legs)
    evaluate(net, f'6leg factor-mom EW look{look} daily')
    netw, _, _ = bt(weekly_positions(w.fillna(0)), legs)
    evaluate(netw, f'6leg factor-mom EW look{look} weekly')
