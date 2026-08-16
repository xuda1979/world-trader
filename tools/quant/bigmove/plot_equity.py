"""Plot bigmove equity curves (per threshold) vs SPY benchmark."""
import sys, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.join(ROOT, "tools/quant/reports")

eq = pd.read_csv(os.path.join(OUT, "bigmove_equity_by_threshold.csv"), parse_dates=["date"]).set_index("date")

# SPY benchmark (total return proxy from close series)
spy_path = os.path.join(ROOT, "tools/quant/data/twelve_big", "SPY.csv")
spy = pd.read_csv(spy_path, parse_dates=["date"]).set_index("date")["close"]
spy = spy.reindex(eq.index).dropna()
spy_eq = spy / spy.iloc[0]

plt.figure(figsize=(12, 7))
for c in ["0.7", "0.8", "0.9"]:
    if c in eq.columns:
        s = eq[c].dropna()
        plt.plot(s.index, s.values, label=f"bigmove thr>={c}")
plt.plot(spy_eq.index, spy_eq.values, label="SPY (buy&hold)", color="black", lw=2, alpha=0.8)
plt.yscale("log")
plt.title("bigmove next-day >=5% strategy — daily-equal-weighted equity (log scale,\n no-look-ahead walk-forward 2018-2026) vs SPY")
plt.legend()
plt.grid(True, which="both", alpha=0.3)
plt.tight_layout()
out_png = os.path.join(OUT, "bigmove_equity_vs_spy.png")
plt.savefig(out_png, dpi=110)
print("saved ->", out_png)
