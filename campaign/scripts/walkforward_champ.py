"""walkforward_champ.py — honest walk-forward rebalance of the 13-sleeve champion.

Answers: 'should we update the model more often, and how often?' WITHOUT breaking OOS honesty.

Mechanics (identical to rawew13v2_build except WHERE relw is fit):
- Same 13 sleeve signals (load()), same cost: 6.4bps FULL|dW| + margin on (1.6-1), same T+1 causal
  (nav.shift(1), weights at t use returns through t-1 only), same gross=1.6 daily.
- Weight refit: relw = max(is_sr_trailing, 0)^P using ONLY data strictly BEFORE each refit trade
  date (no lookahead). Between refits relw is frozen.
- Cadence: 'frozen' = the committed one-shot IS(<2017) fit (reproduces champion, as a control);
  'yearly'/'quarterly'/'monthly' = walk-forward refit at that boundary (first refit after warmup).

Trains on trailing data -> no leakage. If walk-forward >= frozen, updating helps; if <, updating
adds noise/cost and frozen is fine.
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import rawew13v2_build as b

ROOT=b.ROOT; P=b.P; GEAR=b.GEAR; RATE=b.RATE; BPS=b.BPS; NAMES=b.NAMES; PATHS=b.PATHS


def sleeves():
    df = pd.DataFrame({n: b.load(PATHS[n]).dropna() for n in NAMES})
    return df[df.index >= '2008-03-31']


def relw_from(df_trailing):
    SR = pd.Series({n: b.is_sr(df_trailing[n]) for n in NAMES})
    return np.maximum(SR.fillna(0.0), 0.0)**P


def refit_dates(df, freq):
    """Boundary dates (midnight) where weights are refit. First refit after warmup window."""
    if freq == 'frozen':
        return [pd.Timestamp('2017-01-01')]
    yrs = df.index.year
    inner = pd.Timestamp('2009-12-31')  # ensure >=1yr (2008) warmup before first refit
    if freq == 'yearly':
        dates = [pd.Timestamp(f"{y}-01-01") for y in sorted(set(yrs)) if pd.Timestamp(f"{y}-01-01") > inner]
    elif freq == 'quarterly':
        dates = [pd.Timestamp(f"{y}-{q*3-2:02d}-01") for y in sorted(set(yrs)) for q in (2,3,4)
                 if pd.Timestamp(f"{y}-{q*3-2:02d}-01") > inner]
    elif freq == 'monthly':
        dates = [pd.Timestamp(f"{y}-{m:02d}-01") for y in sorted(set(yrs)) for m in range(2,13)
                 if pd.Timestamp(f"{y}-{m:02d}-01") > inner]
    else:
        raise ValueError(freq)
    return [d for d in dates if d < df.index.max()]


def run(df, freq):
    df = df.fillna(0.0)
    relw = relw_from(df[df.index < (refit_dates(df,freq)[0])].dropna())  # first block fit on warmup only
    bounds = sorted(set(refit_dates(df, freq)) | {df.index[0], df.index[-1]})
    blocks = [pd.IntervalIndex.from_breaks(np.array([pd.Timestamp(x) for x in bounds]))[::-1]]
    # build per-block relw by refitting strictly before block start
    relw_map = {}
    for k, start in enumerate(bounds[:-1]):
        if k == 0:  # very first warmup
            relw_map[start] = relw
        else:
            relw_map[start] = relw_from(df[df.index < start].dropna())
    nav = (1+df).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0)
    Wg = []
    ts = df.index
    for i, t in enumerate(ts):
        # find active relw block
        start = max((bd for bd in bounds if bd <= t), default=ts[0])
        rw = relw_map.get(start, relw)
        w = d2.iloc[i].mul(rw)
        w = w / w.sum() * len(NAMES) * (GEAR/len(NAMES))
        Wg.append(w.values)
    Wg = pd.DataFrame(Wg, index=ts, columns=NAMES)
    port = (df.values * Wg.values).sum(axis=1)
    to = Wg.diff().abs().sum(axis=1).fillna(0.0)
    net = (pd.Series(port, index=ts)
           - to*BPS/1e4
           - np.maximum(GEAR-1,0)*RATE/252)
    return net


def stats(net):
    r=net.values; n=len(r)
    ann=(1+r).prod()**(252/n)-1; sr=r.mean()/r.std()*np.sqrt(252)
    mdd=((1+r).cumprod()/np.maximum.accumulate((1+r).cumprod())-1).min()
    return ann, sr, mdd


if __name__ == "__main__":
    df = sleeves()
    print(f"{'cadence':>9} | {'ann(geo)':>8} | {'SR_d':>5} | {'MaxDD':>7} | notes")
    order = ['frozen','yearly','quarterly','monthly']
    res={}
    for f in order:
        net = run(df, f)
        a,s,m = stats(net)
        res[f]=net
        print(f"{f:>9} | {a:8.2%} | {s:5.2f} | {m:7.2%}")
    # OOS(2017+) comparison
    print("\nOOS (2017+) only:")
    for f in order:
        net=res[f]; o=net[net.index>='2017-01-01']; a,s,m=stats(o)
        print(f"  {f:>9}: ann {a:8.2%}  SR {s:5.2f}  MaxDD {m:7.2%}")
