import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import pandas as pd
FF = "/Users/daxu/software/world-trader/tools/quant/data/ff_factors"

def _parse(path, key_line):
    with open(path) as fh:
        lines = fh.readlines()
    start = next(i for i, l in enumerate(lines) if key_line in l)
    df = pd.read_csv(path, skiprows=start, index_col=0)
    idx = pd.to_datetime(df.index.astype(str).str.strip(), format="%Y%m%d", errors="coerce")
    df.index = idx
    df = df[df.index.notna()]
    df = df[df.index <= pd.Timestamp.today()]
    return df / 100.0

def ff_factors():
    return _parse(f"{FF}/F-F_Research_Data_Factors_daily.csv", ",Mkt-RF")

def ff_mom():
    return _parse(f"{FF}/F-F_Momentum_Factor_daily.csv", ",Mom")
