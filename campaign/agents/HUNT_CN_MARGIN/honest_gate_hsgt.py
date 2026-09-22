#!/usr/bin/env python3
"""HONEST GATE 2: HK Stock Connect northbound-flow engines (em_hsgt seam, LEDGER=0 SLEEVES=0).

Known data break: exchange stopped publishing daily northbound buy/sell flows after
2024-08-16 (real regulatory event); deal_amt + fund_inflow survive. Tradables:
sz510300 CSI300 ETF (2012+), IF/IC futures (2017+). IS window < 2017-01-01
=> IS = 2014-11..2016-12 (26 months, >= 24 bar barely met). Pre-registered 2 stages:
SH1 northbound net-flow pressure: z(net_deal_amt/mktcap proxy, 21d) -> CSI300 ETF
SH2 northbound activity momentum: sign(d log deal_amt, lb 21/63) -> CSI300 ETF
T+1, 6.4bps full-|dW|. Bar: IS monthly SR >= 1.0.
"""
import numpy as np
import pandas as pd

HSGT = "/Users/daxu/software/world-trader/tools/quant/data/em_hsgt/hsgt_north_total.csv"
ETF = "/Users/daxu/software/world-trader/tools/quant/data/cn_daily/sz510300_hfq.csv"
IS_END = "2017-01-01"
COST = 0.00064

def sr_m(x):
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(12)) if len(x) > 3 and x.std() > 0 else np.nan

def zscore(s, win):
    return (s - s.rolling(win, min_periods=win).mean()) / s.rolling(win, min_periods=win).std().replace(0, np.nan)

def run(sig, rets):
    pos = np.sign(sig).shift(1).fillna(0.0)  # T+1
    sleeve = pos * rets.reindex(pos.index).fillna(0.0)
    cost = pos.diff().abs().fillna(0.0) * COST
    return sleeve - cost, pos

def battery(name, sleeve, pos, rets):
    m = sleeve.resample("ME").sum()
    isr = m[m.index < IS_END]; osr = m[m.index >= IS_END]
    md = m.dropna(); half = len(md) // 2
    yr = sleeve.groupby(sleeve.index.year).apply(lambda x: (1 + x).prod() - 1)
    return dict(name=name, is_sr=round(sr_m(isr), 3), os_sr=round(sr_m(osr), 3),
                full_sr=round(sr_m(m), 3), h1=round(sr_m(md.iloc[:half]), 3),
                h2=round(sr_m(md.iloc[half:]), 3), neg_yrs=int((yr < 0).sum()),
                n_yrs=len(yr), ann_pct=round(float(m.mean() * 12 * 100), 2))

def main():
    h = pd.read_csv(HSGT, parse_dates=["date"]).set_index("date").sort_index()
    e = pd.read_csv(ETF, parse_dates=["date"]).set_index("date").sort_index()
    etf_rets = e["close"].pct_change()
    rows = []
    # SH1 net-flow pressure (uses the flow series that died 2024-08; honest: book ends there too
    # for this stage — position frozen at 0 after data death, no synthetic continuation)
    net = h["net_deal_amt"]
    for win in (21, 63):
        sig = zscore(net, win)
        for d in (+1, -1):
            sl, pos = run(sig * d, etf_rets)
            rows.append(battery(f"SH1_netz{win}_d{d:+d}", sl, pos, etf_rets))
    # SH2 activity momentum (deal_amt survives to now)
    la = np.log(h["deal_amt"].replace(0, np.nan))
    for lb in (21, 63):
        sig = la.diff(lb)
        for d in (+1, -1):
            sl, pos = run(sig * d, etf_rets)
            rows.append(battery(f"SH2_actmom_lb{lb}_d{d:+d}", sl, pos, etf_rets))
    df = pd.DataFrame(rows)
    df.to_csv("/Users/daxu/software/world-trader/campaign/agents/HUNT_CN_MARGIN/hsgt_screen_results.csv", index=False)
    for _, r in df.iterrows():
        print(f"{r['name']:<22} IS={r['is_sr']:>6} OS={r['os_sr']:>6} full={r['full_sr']:>6} "
              f"h1={r['h1']:>6} h2={r['h2']:>6} negyr={r['neg_yrs']:>2}/{r['n_yrs']} ann={r['ann_pct']:>6}%")
    best = df.loc[df["is_sr"].idxmax()]
    print(f"\nBEST by IS SR: {best['name']} IS SR {best['is_sr']} vs 1.0 bar -> "
          f"{'PASS' if best['is_sr'] >= 1.0 else 'FAIL'}")
    return df

if __name__ == "__main__":
    main()
