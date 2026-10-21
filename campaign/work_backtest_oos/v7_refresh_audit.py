#!/usr/bin/env python3
"""V7 REFRESH FEASIBILITY AUDIT (read-only, 2026-09-22).

Goal: for each of the 8 STALE V7 sleeves (freshness gate RED), enumerate the FULL
raw-input dependency tree and classify each leaf:
  FRESH  = on-disk raw data current enough (<=35d) -> sleeve extendable
  REFRESHABLE = stale raw data but source endpoint ALIVE and reproducible (append-only)
  BLOCKED = source endpoint dead/blocked or vendor-substitution risk (splicing vendors forbidden)
This script READS ONLY; it writes a JSON report. No sleeve is modified here.
"""
import json, os, sys
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
TODAY = pd.Timestamp("2026-09-22")
OUT = f"{ROOT}/campaign/work_backtest_oos/v7_refresh_audit.json"

def gap(path, date_col=None):
    try:
        df = pd.read_csv(path)
        c = date_col or ("date" if "date" in df.columns else df.columns[0])
        dates = pd.to_datetime(df[c], errors="coerce")
        return int((TODAY - dates.max()).days), str(dates.max().date()), int(len(df))
    except Exception as e:
        return None, f"ERR {str(e)[:60]}", 0

HF = f"{ROOT}/tools/quant/hedge_fund_strats/data_fred"
MF = f"{ROOT}/tools/quant/data/more_fred"
FXD = f"{ROOT}/tools/quant/data/fx"
FXH = f"{ROOT}/tools/quant/data/fx_hist"
ND = f"{ROOT}/tools/quant/data/newdata"

# FRED live endpoints verified reachable 2026-09-22:
#   fredgraph.csv (id=SERIES) + api.stlouisfed.org (key in .env.local) BOTH 200.
# ECB eurofxref-hist.zip verified 200 (data through 2026-09-21).
# twelvedata / stooq / yahoo: BLOCKED from this host (prior probes).

AUDIT = {
  "brwt7.csv": {
    "generator": "agents/STRICTAUDIT_CONSTRUCTION/scratch/rebuild_exact.py",
    "deps": "12 component sleeves (E1_brwt_spread_rev15_2000, brwt10_2000, brwt5, E1_C5ng_*, "
            "A5_r2_contango_rateshock, E1_a6r7_bond2y_trend_1990, E1_QAxasts_tsmom189_2006, "
            "E1_carryv2_GLD_2006, QA_dualmom_band121, XGB1y_deploy) -> each has own raw tree",
    "leaves": {
      "harness wti.csv": f"{HF}/wti.csv",
      "harness brent.csv": f"{HF}/brent.csv",
      "harness xau.csv": f"{HF}/xau.csv",
      "harness vix.csv": f"{HF}/vix.csv",
      "harness us2y/us10y/us30y": f"{HF}/us10y.csv",
      "harness dxy.csv": f"{HF}/dxy.csv",
      "fx/ pairs (crossasset components)": f"{FXD}/EUR_USD.csv",
      "fx_hist/ (ECB, fresh 2026-09-07)": f"{FXH}/EUR_USD.csv",
    },
  },
  "crossasset_rev_L8.csv": {
    "generator": "scripts/backtest_crossasset_rev_L8.py",
    "leaves": {
      "us10y.csv": f"{HF}/us10y.csv", "us2y.csv": f"{HF}/us2y.csv",
      "dxy.csv": f"{HF}/dxy.csv", "xau.csv": f"{HF}/xau.csv",
      "wti.csv": f"{HF}/wti.csv", "brent.csv": f"{HF}/brent.csv",
      "vix.csv": f"{HF}/vix.csv",
      "fx/EUR_USD": f"{FXD}/EUR_USD.csv", "fx/GBP_USD": f"{FXD}/GBP_USD.csv",
      "fx/USD_JPY": f"{FXD}/USD_JPY.csv", "fx/USD_CHF": f"{FXD}/USD_CHF.csv",
      "fx/USD_CAD": f"{FXD}/USD_CAD.csv", "fx/AUD_USD": f"{FXD}/AUD_USD.csv",
    },
  },
  "a6_r2_pair_residmom_fm1926.csv": {
    "generator": "scripts/a6_r2_pair_residmom_fm1926.py",
    "leaves": {"(check script)": f"{ROOT}/campaign/scripts/a6_r2_pair_residmom_fm1926.py"},
  },
  "diescrack__prefix.csv": {
    "generator": "agents/chief/coord/ITER47_A5R2_VTEXT/battery_canonicalize47.py",
    "leaves": {"(check script)": f"{ROOT}/campaign/agents/chief/coord/ITER47_A5R2_VTEXT/battery_canonicalize47.py"},
  },
  "A1_carry_seasonal_v2.csv": {
    "generator": "agents/A1_trend_cta/scripts/candidate_build2.py",
    "leaves": {"(check script)": f"{ROOT}/campaign/agents/A1_trend_cta/scripts/candidate_build2.py"},
  },
  "Merger_Arb_PEAD_5pct.csv": {
    "generator": "tools/quant/hedge_fund_strats (equity pipeline)",
    "leaves": {"(check strats dir)": f"{ROOT}/tools/quant/hedge_fund_strats"},
  },
  "TREASFUT_intlcarry3_lag1_NEG.csv": {
    "generator": "campaign/scripts/HUNT_TREASFUT_round1.py",
    "leaves": {"(check script)": f"{ROOT}/campaign/scripts/HUNT_TREASFUT_round1.py"},
  },
  "RC_t102_d5mr_w21_band50_vt5.csv": {
    "generator": "team/agents/RES_CREDIT/emit_sleeve.py",
    "leaves": {"(check script)": f"{ROOT}/campaign/team/agents/RES_CREDIT/emit_sleeve.py"},
  },
}

def main():
    report = {"generated": str(TODAY.date()), "sleeves": {}}
    for s, info in AUDIT.items():
        rows = {}
        for name, path in info["leaves"].items():
            g, last, n = gap(path)
            if g is None and os.path.isdir(path):
                rows[name] = {"status": "DIR", "path": path}
            elif g is None:
                rows[name] = {"status": "ERR", "detail": last}
            else:
                status = "FRESH" if g <= 35 else "STALE-ON-DISK"
                rows[name] = {"gap_days": g, "last": last, "rows": n, "status": status}
        report["sleeves"][s] = {"generator": info.get("generator", "?"),
                                "deps_note": info.get("deps", ""), "leaves": rows}
    with open(OUT, "w") as f:
        json.dump(report, f, indent=1)
    print(f"refresh audit -> {OUT}")
    for s, r in report["sleeves"].items():
        n_stale = sum(1 for v in r["leaves"].values() if v.get("status") == "STALE-ON-DISK")
        n_fresh = sum(1 for v in r["leaves"].values() if v.get("status") == "FRESH")
        print(f"  {s:<38} leaves: {n_fresh} fresh / {n_stale} stale-on-disk")
    return 0

if __name__ == "__main__":
    sys.exit(main())

# ---- POST-AUDIT VERIFICATION (appended 2026-09-22, same session) ----
# Live endpoint verification results (all probed fresh this session):
#  - FRED API + fredgraph: 200 OK, key working. Overlap byte-checks vs on-disk:
#    DGS10/DGS2/DGS30/T10Y2Y/VIXCLS/DCOILWTICO/DCOILBRENTEU max|diff|=0.0000 (identical source).
#    tbill3m.csv IDENTIFIED as TB3MS monthly (319 rows, maxdiff 0.0 vs TB3MS).
#  - ECB eurofxref-hist.zip: 200 OK, data through 2026-09-21 (ECB reference rates).
#  - TwelveData API: 200 OK with .env.local key, SPY daily through 2026-09-21.
#  - Monthly series refresh delta confirmed: UNRATE has 2026-08 obs, M2SL 2026-07,
#    CPIAUCSL 2026-08, PALLFNFINDEXM 2026-07 -> monthly files extendable by 1-2 vintages.
#  - TEDRATE: DISCONTINUED by FRED (last 2022-01-21) - dead source, but data_fred_new
#    TEDRATE.csv is historical-only input to r7_charter engines; no refresh possible nor needed.
