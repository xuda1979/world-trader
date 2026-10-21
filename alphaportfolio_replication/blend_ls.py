"""Blend champion composite with ls L/S streams (overlap 2018-2026)."""
import pandas as pd, numpy as np, os, sys
sys.path.insert(0, os.getcwd())

def champ_monthly():
    import run_champion_fund_tilt as R
    d = pd.read_csv("data/wf_final.csv", index_col=0)
    d.index = pd.to_datetime(d.index.astype(str) + "-01") + pd.offsets.MonthEnd(0)
    return d["net"].rename("champ")

def ls_monthly(path):
    d = pd.read_csv(path, index_col=0, parse_dates=True)
    s = d[d.columns[0]].dropna()
    if s.index[0].day == 1:  # monthly already
        s.index = pd.to_datetime(s.index)
        return s.rename("ls")
    return s.resample("ME").apply(lambda x: (1+x).prod()-1).rename("ls")

def main(paths):
    champ = champ_monthly()
    for p in paths:
        try:
            ls = ls_monthly(p)
        except Exception as e:
            print(f"{p}: ERR {e}"); continue
        df = champ.to_frame().join(ls, how="inner")
        print(f"\n{p}: {len(df)}mo overlap, corr={df.champ.corr(df.ls):+.3f}")
        for w in [0.2, 0.3, 0.4]:
            r = (1-w)*df.champ + w*df.ls
            eq = np.cumprod(1+r)
            print(f"  ls {w:.0%}: SR={r.mean()/r.std()*np.sqrt(12):.3f} ret={r.mean()*12*100:+.2f}% "
                  f"DD={(eq/np.maximum.accumulate(eq)-1).min()*100:.2f}%")
        base = df.champ
        eq = np.cumprod(1+base)
        print(f"  champ only: SR={base.mean()/base.std()*np.sqrt(12):.3f} "
              f"DD={(eq/np.maximum.accumulate(eq)-1).min()*100:.2f}%")

if __name__ == "__main__":
    main(sys.argv[1:])
