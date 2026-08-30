"""r4 final composite: EW{ratesLF378(vt15/leg), XAU-lf126, CU-lf3m, FF-best1-lb252-2x}
FF leg has corr 0.51 to champion at full weight; at 1/4 weight blend corr should dilute <0.3.
Gates: SR>=0.8, halves>=0.4, <=2 negyrs, worst>-6%, ann>=12%, corr<=0.3; per-component
scramble (circular shift, 200x, pre-vt component net vs its own asset) if others pass."""
import sys; sys.path.insert(0, __file__.rsplit("/",1)[0])
from r4_lib import *
from idea30_return_book import rates_lf, gold_lf, cu_lf
from idea28_ff_factortime import sleeve as ff_sleeve, monthly_positions

if __name__ == "__main__":
    comps = {"rates": rates_lf(), "xau": gold_lf(), "cu": cu_lf(),
             "ff252": ff_sleeve(monthly_positions(252), 0.20)}
    for k, v in comps.items():
        g = full_gates(v); c, n = corr_to_champ(v)
        pr(f"  comp:{k}", g, c, f"n={n}")
    df = pd.DataFrame(comps).dropna(how="all").fillna(0.0)
    start = df.ne(0).any(axis=1).idxmax()
    blend = vol_target(df.mean(axis=1), 0.15).dropna()
    blend = blend[blend.index >= start]
    g = full_gates(blend); c, n = corr_to_champ(blend)
    yr = yearly(blend)
    pr("A2-BLEND4WAY-vt15", g, c, f"n={n} {blend.index[0].date()}..{blend.index[-1].date()}")
    print("  yearly:", {int(k): round(v*100,1) for k,v in yr.items()})
