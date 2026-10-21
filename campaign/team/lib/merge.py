"""merge.py — rows-kept (union) panel builder for the data pipeline (DATA_MERGE).

Charter contract (campaign/team/charters/DATA_MERGE.md):
- UNION join semantics: len(panel) == union of ALL input calendars. An inner join that
  silently drops NYSE-closed rows (the L16 hole) is illegal here.
- ISO dates, sorted, deduped (keep LAST value per date).
- Bounded economic ffill (max_gap_days); leading NaN stays NaN (no fake history); anything
  wider stays NaN and is DISCLOSED via gap_report, never silently filled.
- Fail-closed loader: missing file/column raises.
- Output: tools/quant/data/panel_<name>/<name>.csv + manifest.csv with a source map.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

__all__ = ["normalize", "load_series", "union_join", "fill_economic", "gap_report",
           "write_panel", "read_manifest", "build_panel", "build_vol_panel",
           "build_cboe_flow_panel", "build_sentiment_panel", "MAIN_SOURCES"]

ROOT = "/Users/daxu/software/world-trader"
DATA = os.path.join(ROOT, "tools", "quant", "data")


def normalize(s):
    """ISO DatetimeIndex, sorted, deduped keeping the LAST value per date."""
    s = pd.Series(s).dropna()
    s.index = pd.DatetimeIndex(s.index).normalize()
    s = s.sort_index()
    return s[~s.index.duplicated(keep="last")].astype(float)


def load_series(family, fname, col=None, sub=None):
    """Fail-closed CSV loader from tools/quant/data/<family>[/<sub>]/<fname>. CSVs are
    pre-normalized (normalize()). Missing file/column raises — never silent empty.

    Robustness: a bare `fname` (no '.csv' extension) is auto-suffixed, so callers need
    not remember the extension. A path that exists WITH the suffix on disk always wins;
    a truly absent file still raises (fail-closed)."""
    path = os.path.join(DATA, family, sub or "", fname)
    if not os.path.isfile(path) and not os.path.basename(fname).endswith(".csv"):
        path = path + ".csv"
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    if col is None:
        if df.shape[1] < 2:
            raise ValueError(f"{path}: need >=2 columns")
        col = df.columns[1]
    if col not in df.columns:
        raise KeyError(f"{path}: column {col!r} missing")
    s = pd.Series(pd.to_numeric(df[col], errors="coerce").values,
                  index=pd.to_datetime(df[df.columns[0]], errors="coerce"))
    out = normalize(s)
    if out.empty:
        raise ValueError(f"{path}: no usable rows")
    return out


def union_join(series_map):
    """Rows-kept outer join. len(panel) == union of all calendars (the charter property).
    Empty input raises (fail-closed)."""
    if not series_map:
        raise ValueError("union_join: empty series map")
    union = None
    for s in series_map.values():
        union = pd.DatetimeIndex(s.index) if union is None else union.union(s.index)
    panel = pd.DataFrame(index=union)
    for name, s in series_map.items():
        panel[name] = s.reindex(union)
    return panel.sort_index()


def fill_economic(s, max_gap_days=5):
    """Forward-fill holes <= max_gap_days (calendar days between known points); leading
    NaN preserved (no fake history); wider holes stay NaN (disclosed via gap_report)."""
    s = s.astype(float)
    filled = s.ffill()
    idx = s.index
    if len(idx) < 2:
        return filled
    # distance from each NaN to the PREVIOUS known value
    last_known = idx.to_series(index=idx).where(s.notna()).ffill()
    gaps = (idx - pd.DatetimeIndex(last_known)).days
    too_far = s.isna() & (pd.Series(gaps, index=idx) > max_gap_days)
    filled[too_far] = np.nan
    return filled


def gap_report(s):
    """Coverage disclosure: leading/trailing NaN counts and widest interior hole in days."""
    s = s.astype(float)
    n = len(s)
    known = s.notna().values
    if not known.any():
        return {"n": n, "leading_na": n, "trailing_na": n, "max_gap_days": -1}
    lead = int(np.argmax(known))
    tail = int(np.argmax(known[::-1]))
    interior = s.iloc[lead:n - tail] if tail else s.iloc[lead:]
    max_gap = -1
    if len(interior) > 1:
        dt = np.diff(interior.index.values).astype("timedelta64[D]").astype(int)
        max_gap = int(dt.max())
    return {"n": n, "leading_na": int(lead), "trailing_na": int(tail),
            "max_gap_days": max_gap}


def write_panel(root, name, panel, sources, max_gap_days=5):
    """Write panel_<name>/<name>.csv + manifest.csv (source map, span, gap stats)."""
    outdir = os.path.join(root, "tools", "quant", "data", f"panel_{name}")
    os.makedirs(outdir, exist_ok=True)
    df = panel.copy()
    df.index.name = "date"
    df.index = df.index.strftime("%Y-%m-%d")
    df.to_csv(os.path.join(outdir, f"{name}.csv"))
    rows = []
    for col in panel.columns:
        rep = gap_report(panel[col])
        rows.append({"column": col, "source": sources.get(col, "?"),
                     "rows": rep["n"], "first": str(panel.index[0].date()),
                     "last": str(panel.index[-1].date()),
                     "na_rows": int(panel[col].isna().sum()),
                     "leading_na": rep["leading_na"],
                     "max_gap_days": rep["max_gap_days"]})
    man = pd.DataFrame(rows)
    man.to_csv(os.path.join(outdir, "manifest.csv"), index=False)
    return outdir


def read_manifest(outdir):
    """Read a panel manifest back to a dict keyed like write_panel's rows (1 col -> dict)."""
    man = pd.read_csv(os.path.join(outdir, "manifest.csv"))
    rec = man.iloc[0] if len(man) == 1 else man
    return rec.to_dict()


def build_panel(name, series_map, max_gap_days=5):
    """union_join + bounded economic fill + write into tools/quant/data. Returns panel."""
    panel = union_join(series_map)
    panel = panel.apply(lambda c: fill_economic(c, max_gap_days))
    sources = {k: MAIN_SOURCES.get(k, "unknown") for k in panel.columns}
    write_panel(ROOT, name, panel, sources, max_gap_days)
    return panel


# ---- canonical source map ----------------------------------------------------
MAIN_SOURCES = {
    "spy": "twelvedata/SPY.csv", "ff_mkt": "ff_factors (Mkt-RF)",
    "ff_mom": "ff_factors (Mom)", "ff_smb": "ff_factors", "ff_hml": "ff_factors",
    "vix": "more_vol/VIX.csv", "vix9d": "more_vol/VIX9D.csv",
    "vix3m": "more_vol/VIX3M.csv", "vix6m": "more_vol/VIX6M.csv",
    "skew": "more_vol/SKEW.csv", "vvix": "more_vol/VVIX.csv",
    "spx_put": "cboe_flow/_raw/SPX_History.csv",
    "put_ratio": "cboe_flow/_raw/PUT_History.csv",
    "cnn_fg": "cnn_fg/cnn_fg.csv", "btc_etf_flow": "farside_flows/btc_etf_flows.csv",
    "eth_etf_flow": "farside_flows/eth_etf_flows.csv", "cape": "shiller_cape",
}


def _ff_daily(path, col):
    """Fama-French daily CSV (2-line header, index col) -> clean daily series."""
    df = pd.read_csv(path, skiprows=3)
    df = df[pd.to_numeric(df.iloc[:, 0], errors="coerce").notna()]
    df = df.rename(columns={df.columns[0]: "date"})
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d", errors="coerce")
    s = pd.Series(pd.to_numeric(df[col], errors="coerce").values, index=df["date"])
    return normalize(s)


def build_vol_panel():
    """panel_vol: SPY close + VIX term structure + SKEW/VVIX (RES_VOL engine input)."""
    fam = "more_vol"
    s_map = {"spy": load_series("twelvedata", "SPY.csv", "close")}
    for col, f in [("vix", "VIX.csv"), ("vix9d", "VIX9D.csv"), ("vix3m", "VIX3M.csv"),
                   ("vix6m", "VIX6M.csv"), ("skew", "SKEW.csv"), ("vvix", "VVIX.csv")]:
        try:
            s_map[col] = load_series(fam, f, "close")
        except (FileNotFoundError, KeyError, ValueError):
            s_map[col] = load_series(fam, f, col.lower())
    return build_panel("vol", s_map, max_gap_days=10)


def build_cboe_flow_panel():
    """panel_cboe_flow: SPX + CBOE total put/call ratio (RES_VOL/cboe_flow inputs)."""
    spx = load_series("cboe_flow", "SPX_History.csv", "SPX", sub="_raw")
    put = load_series("cboe_flow", "PUT_History.csv", "PUT", sub="_raw")
    return build_panel("cboe_flow", {"spx": spx, "put_ratio": put}, max_gap_days=10)


def build_sentiment_panel():
    """panel_sentiment: CNN Fear&Greed + BTC/ETH ETF flows (RES_META / flows inputs)."""
    cnn = load_series("cnn_fg", "cnn_fg.csv", "score")
    btc = load_series("farside_flows", "btc_etf_flows.csv", "total_musd")
    eth = load_series("farside_flows", "eth_etf_flows.csv", "total_musd")
    return build_panel("sentiment", {"cnn_fg": cnn, "btc_etf_flow": btc,
                                     "eth_etf_flow": eth}, max_gap_days=7)


def build_core_panel():
    """panel_core: SPY + FF3 daily factors + momentum (engine/benchmark inputs)."""
    ff = os.path.join(DATA, "ff_factors")
    s_map = {"spy": load_series("twelvedata", "SPY.csv", "close"),
             "ff_mkt": _ff_daily(os.path.join(ff, "F-F_Research_Data_Factors_daily.csv"),
                                 "Mkt-RF"),
             "ff_smb": _ff_daily(os.path.join(ff, "F-F_Research_Data_Factors_daily.csv"),
                                 "SMB"),
             "ff_hml": _ff_daily(os.path.join(ff, "F-F_Research_Data_Factors_daily.csv"),
                                 "HML"),
             "ff_mom": _ff_daily(os.path.join(ff, "F-F_Momentum_Factor_daily.csv"), "Mom")}
    return build_panel("core", s_map, max_gap_days=5)
