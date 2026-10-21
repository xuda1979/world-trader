"""HUNT_FXMICRO lib: daily-OHLC FX microstructure engines on the 8 tradable twelvedata pairs.

DATA: /Users/daxu/software/world-trader/tools/quant/data/fx/{AUD_USD,EUR_GBP,EUR_USD,GBP_USD,
      NZD_USD,USD_CAD,USD_CHF,USD_JPY}.csv  [date,open,high,low,close,vol], 2019-04..2026-08.
HONESTY (charter): T+1 (signal at t uses data<=t, PnL t->t+1), 6bps/side on one-side turnover,
no flattening, PIT yields for accrual (monthly FRED -> last confirmed value at decision date).
Orientation convention: LOCAL_PER_USD quotes (USD_JPY etc.) used as-is; USD_LOC (AUD_USD etc.)
inverted so every series = local-per-USD: price UP = local ccy UP vs USD (or EUR for EUR_GBP).
PnL is booked on USD-neutral L/S books: long local = hold local vs USD.
NOTE: EUR_GBP quotes EUR per GBP -> local=GBP. USD_LOC pairs inverted -> local=USD?? NO:
inverting USD_CAD (CAD per USD) gives USD per CAD -> 'local' = CAD. Same for USD_CHF (CHF),
USD_JPY (JPY). So all 8 series become QUOTE-per-BASE with base=the ccy we are long when price up:
  AUD_USD->long AUD, EUR_GBP->long GBP(as quote EUR? careful) ...
For PnL in USD terms we keep it simple: r_t = pct_change of the quoted series (already USD-value
of 1 unit of the FIRST ccy for *_USD pairs and for USD_* pairs after inversion the series is
USD-value of 1 unit of the SECOND ccy). Long/short sign flips accordingly; books are
dollar-neutral so only the DIRECTION matters and it is consistent per-pair.
"""
import numpy as np, pandas as pd, sys
ROOT='/Users/daxu/software/world-trader'
sys.path.insert(0,ROOT)
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr, scramble_pval
FXD=f'{ROOT}/tools/quant/data/fx'
FRED=f'{ROOT}/tools/quant/hedge_fund_strats/data_fred'
COST=6.0/1e4
PAIRS=['AUD_USD','EUR_GBP','EUR_USD','GBP_USD','NZD_USD','USD_CAD','USD_CHF','USD_JPY']

def load_px(drop_weekend=True):
    """dict pair -> OHLC df on weekdays only (spot FX closed Sat/Sun; Sat rows are stale
    weekly artifacts: |SatClose-FriClose| med 2.3bp << daily 25bp)."""
    out={}
    for p in PAIRS:
        df=pd.read_csv(f'{FXD}/{p}.csv',index_col=0,parse_dates=True)
        if drop_weekend: df=df[df.index.dayofweek<5]
        df=df[~df.index.duplicated(keep='last')].sort_index()
        out[p]=df
    return out

def bt_longshort(pos_d, px_close, vt_ann=0.10, decision='daily', cost_bps=6.0):
    """Honest T+1 backtest.
    pos_d: DataFrame (dates x pairs) of DESIRED positions (units of risk, sign only) computed
           from data up to and INCLUDING row date t (no lookahead within the day).
    px_close: DataFrame aligned closes.
    decision: 'daily' -> trade every day t for t->t+1; 'weekly' -> positions decided at first
           trading day of each ISO week, held through the week (still T+1: Monday decision
           earns Monday->Tuesday move).
    Costs: 6bps x one-side turnover |pos_t - pos_{t-1}| summed over pairs.
    Returns (net_daily_before_vt, turnover) on the decision calendar (weekdays)."""
    sig=pos_d.shift(1)                       # T+1: position decided from info<=t earns t->t+1
    if decision=='weekly':
        iso=pd.Index(sig.index).isocalendar()
        wk=(iso['year'].astype(int).astype(str)+iso['week'].astype(int).astype(str)).values
        newwk=pd.Series(np.r_[True,wk[1:]!=wk[:-1]],index=sig.index)
        sig=sig.where(newwk).ffill()
    px2=px_close.reindex(sig.index)
    ret=px2.pct_change()
    gross=(sig*ret).sum(axis=1, min_count=1)
    turn=sig.diff().abs().sum(axis=1).fillna(0.0)
    net=gross-turn*cost_bps/1e4
    return net.dropna(how='all'), turn.reindex(net.index).fillna(0)

def make_pos(sign_df, vol_scale=None):
    """sign_df: ±1 desired directional exposure per pair. Optionally vol-scale per pair using
    ONLY trailing 63d realized vol of that pair's daily closes (expanding min 60d)."""
    if vol_scale is None: return sign_df
    return sign_df*vol_scale

def trail_vol(px_close, lb=63, minp=60):
    rv=px_close.pct_change().rolling(lb,min_periods=minp).std()
    return rv

def accrual_series(pair, px_index, forward_proxy='y10'):
    """PIT accrual (bps/day) for holding the BASE ccy long vs QUOTE, using FRED 10y diffs.
    Interest parity: long BASE earns BASE rate minus QUOTE rate on the notional.
    proxy='y10' -> foreign10y_minus_us2y convention used by A2 r7 (approx deposit spread).
    MONTHLY FRED series -> ffill'd to daily, shifted +1 MONTH decision lag (PIT: value for
    month m only usable from the day the month printed; approximated as 1st of m+1, plus the
    ffill inside the frame means the LAST KNOWN monthly value as of decision date t)."""
    base,quote=pair.split('_')  # e.g. USD_JPY -> base USD quote JPY; AUD_USD -> base AUD quote USD
    m={'USD':'us2y','JPY':'jp10y','EUR':'ez10y','GBP':'gb10y','CAD':'ca10y',
       'AUD':'au10y','NZD':'nz10y','CHF':'ch10y'}
    # EUR_GBP: base EUR quote GBP
    def y(c):
        k=m[c]
        s=pd.read_csv(f'{FRED}/{k}.csv',index_col=0,parse_dates=True).iloc[:,0]
        s=pd.to_numeric(s,errors='coerce').dropna()
        return s
    yb=yq=None
    try: yb=y(base)
    except Exception: pass
    try: yq=y(quote)
    except Exception: pass
    if yb is None and yq is None: return pd.Series(0.0,index=px_index)
    us=y('USD') if (yb is None or yq is None) else None
    if yb is None: yb=us
    if yq is None: yq=us
    Y=pd.DataFrame({'b':yb,'q':yq}).dropna().resample('MS').last()
    diff=Y['b']-Y['q']
    # PIT: monthly print available the NEXT month start +1 day; ffill onto calendar
    pit=diff.shift(1)                       # value of month m usable from m+1
    pit=pit.reindex(pd.bdate_range(px_index.min(),px_index.max())).ffill()
    pit=pit.reindex(px_index).ffill()
    return (pit/100.0/252.0).fillna(0.0)    # per-day accrual on the LONG-BASE leg

def flip_for_quote(pairs, signs):
    """Return sign convention per pair such that +1 = long the HIGH-RATE (funding short)
    ccy under accrual. Here signs are strategy-specific; this helper documents orientation:
    series pct_change for pair P = return of holding 1 unit of the FIRST ccy (in units of 2nd).
      *_USD: first=base(AUD..), +pos = long base ccys (AUD,NZD) / long first (EUR,GBP).
      USD_*: series is 2nd-ccy per USD; pct_change = USD-value of JPY/CHF/CAD. pos=+1 on
             USD_JPY means long the FIRST ccy (USD)."""
    return signs

def flatten_gate(r, name=''):
    """campaign/audit_harness.py flatten gate (2008+ there; here full given 7y window):
    pass if ac1<0.5 AND uniq_ratio>=0.08."""
    r=r.dropna()
    ac1=float(r.autocorr(1)) if len(r)>3 else 1.0
    uq=float(r.round(10).nunique()/len(r)) if len(r)>0 else 0.0
    ok=(ac1<0.5) and (uq>=0.08)
    return dict(name=name,ac1=round(ac1,4),uniq_ratio=round(uq,4),flatten_pass=bool(ok))

def stats_full(r):
    s=full_stats(r)
    s['sr_d']=s['sr']
    m=(1+r).resample('ME').prod()-1
    s['sr_m']=float(m.mean()/m.std()*np.sqrt(12)) if len(m)>12 else np.nan
    return s
