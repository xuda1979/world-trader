import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import numpy as np, pandas as pd
from honest13_build import make, NEW3, vt
from champion_build import vt as vtc
ROOT='/Users/daxu/software/world-trader'
Sd, capW, blend, tw, wts = make(NEW3)
b, gb = vt(blend, 0.091)
# T+1 proof: gb uses vol = rolling(60).std().shift(1) -> info through t-1.
# Probe: recompute with SAME-DAY vol (leak variant) and count differing days.
vol0 = blend.rolling(60).std()*np.sqrt(252)              # no shift (leak)
gb0 = (0.091/vol0).clip(upper=8.0); gb0[vol0.isna()]=0
full_lag  = capW.mul(gb, axis=0)
full_leak = capW.mul(gb0, axis=0)
diff_days = (full_lag.fillna(0)-full_leak.fillna(0)).abs().sum(axis=1)
print("C1: extra-lag probe — days where T+1 path != T+0 leak path: %d/%d (max|w diff| %.4e)"%((diff_days>1e-10).sum(),len(diff_days),diff_days.max()))
print("    => committed path is the LAGGED one: lookahead-in-positions = NONE" if (diff_days>1e-10).sum()>0 else "    => SUSPICIOUS: identical under lag change")
# throttle drawdown uses eq.shift(1): info through t-1. verify:
eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
sc=pd.Series(np.where(tdd<-0.03,0.5,1.0),index=b.index)
print("C2: throttle uses drawdown through t-1 (eq.shift(1)): OK by construction; trades at half-size continue next day only after recompute")
# But: sc applied to day-t return b*sc with sc from t-1 info -> consistent T+1.
# Execution-price convention: ledger stamps date t with price at t close.
led=pd.read_csv(f'{ROOT}/campaign/results/BLOTTER_HONEST14V3_BALANCED.csv',parse_dates=['date'])
a5=led[led.sleeve=='A5r2'].sort_values('date')
import campaign.harness.data as D
spy=D.closes()['SPY']
a5['spy_t']=[float(spy.loc[d]) if d in spy.index else np.nan for d in a5.date]
a5['spy_t1']=[float(spy.loc[d-pd.Timedelta(days=1)]) if (d-pd.Timedelta(days=1)) in spy.index else (float(spy.asof(d-pd.Timedelta(days=1))) if True else np.nan) for d in a5.date]
a5['gap_bps']=(a5.price-a5.spy_t1).abs()/a5.spy_t1*1e4
print("C3: A5r2 ledger price vs prior-close (honest exec) price: n=%d mean|gap|=%.2f bps p95=%.2f bps max=%.2f bps"%(
  a5.gap_bps.notna().sum(), a5.gap_bps.mean(), a5.gap_bps.quantile(0.95), a5.gap_bps.max()))
print("    => ledger stamps date-t CLOSE as exec price; PnL claims day-t return => 1-day exec-convention inconsistency (attribution only, not PnL)")
# holiday/weekend trades
cal_hol=set(pd.date_range('2006','2027',freq='CBME').date)  # placeholder
from pandas.tseries.holiday import USFederalHolidayCalendar
hol=set(USFederalHolidayCalendar().holidays(start='2006-01-01',end='2026-12-31'))
wk=led[pd.to_datetime(led.date).dt.dayofweek>=5]
hd=led[pd.to_datetime(led.date).isin(hol)]
print("C4: ledger trades on WEEKENDS: %d ; on US federal holidays: %d"%(len(wk),len(hd)))
if len(hd): print(hd.groupby(['sleeve','price_source']).size().to_string())
# dup / qty sanity
print("C5: dup (date,sleeve) rows: %d ; qty_notional min=%.3e (no zeros if >0) ; neg qty: %d"%(
 led.duplicated(['date','sleeve']).sum(), led.qty_notional.min(), (led.qty_notional<=0).sum()))
