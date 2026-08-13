"""Download + parse CFTC Commitments of Traders — disaggregated
futures-and-options combined (free, no API key).

Sources (browser UA required — CFTC 403s urllib's default, like Stooq):
  2006-2016:  https://www.cftc.gov/files/dea/history/com_disagg_txt_hist_2006_2016.zip
  2017+ per-year: https://www.cftc.gov/files/dea/history/com_disagg_txt_YYYY.zip
  Current week:  https://www.cftc.gov/dea/newcot/deacom.txt

Rows are one contract per weekly report. We keep the fields needed for
positioning signals:
  report_date, contract_code, market, oi, m_money_long, m_money_short
  (+ swap / prod merc totals for completeness), spec_net = MM net.

Usage:  python tools/quant/hedge_fund_strats/download_cot.py
"""

import argparse
import csv
import io
import os
import zipfile

import requests

BASE = "https://www.cftc.gov/files/dea/history"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

# New format (2017+, header row): name, YYMMDD, YYYY-MM-DD, contract_code,
# market_code, region, commodity, then positions...
NEW_HEADER = "Market_and_Exchange_Names"
# Old format (2006-2016, no header): name, YYMMDD, contract_code, market_code,
# region, commodity, then positions...
OLD = {"date_idx": 1, "code_idx": 2}


def fetch(url, out_dir, name):
    """Download url -> out_dir/name (cached)."""
    path = os.path.join(out_dir, name)
    if os.path.exists(path):
        print(f"  cached {name}")
        return path
    resp = requests.get(url, headers=UA, timeout=180)
    resp.raise_for_status()
    with open(path, "wb") as fh:
        fh.write(resp.content)
    print(f"  downloaded {name} ({len(resp.content) // 1024} KB)")
    return path


def parse_lines(lines):
    """Yield dicts for each data row; handles new (header) and old formats."""
    rows = csv.reader(lines)
    first = next(rows)
    if first and first[0].startswith("Market_and_Exchange_Names"):
        hdr = first
        col = {name: i for i, name in enumerate(hdr)}
        d_idx, iso_idx, code_idx = col["As_of_Date_In_Form_YYMMDD"], \
            col["Report_Date_as_YYYY-MM-DD"], col["CFTC_Contract_Market_Code"]
        mm_l, mm_s = col["M_Money_Positions_Long_All"], col["M_Money_Positions_Short_All"]
        oi = col["Open_Interest_All"]
        sw_l, sw_s = col["Swap_Positions_Long_All"], col["Swap__Positions_Short_All"]
        rows = list(rows)
    else:
        # old format: 0 name, 1 YYMMDD, 2 code, 3 mkt, 4 region, 5 commodity,
        # 6 OI, 7 prodL, 8 prodS, 9 swapL, 10 swapS, 11 MML, 12 MMS, ...
        d_idx, iso_idx, code_idx = 1, None, 2
        mm_l, mm_s, oi, sw_l, sw_s = 11, 12, 6, 9, 10
        rows = [first] + list(rows)
    for r in rows:
        if len(r) <= max(d_idx, code_idx, mm_l, mm_s):
            continue
        try:
            date = r[d_idx].strip()
            if iso_idx is not None:
                out = {"date": r[iso_idx]}
            else:
                out = {"date": f"20{date[0:2]}-{date[2:4]}-{date[4:6]}"}
            out.update({
                "market": r[0],
                "contract_code": r[code_idx].strip(),
                "oi": float(r[oi].strip()),
                "m_money_long": float(r[mm_l].strip()),
                "m_money_short": float(r[mm_s].strip()),
                "swap_long": float(r[sw_l].strip()),
                "swap_short": float(r[sw_s].strip()),
            })
            yield out
        except (ValueError, IndexError):
            continue


def parse_tff(lines):
    """Parse Traders in Financial Futures (TFF) rows: dealer/asset-mgr/
    leveraged-fund positions (the financial-market analog of disagg)."""
    rows = csv.reader(lines)
    first = next(rows)
    if first and first[0].startswith("Market_and_Exchange_Names"):
        col = {name: i for i, name in enumerate(first)}
        iso_idx = col.get("Report_Date_as_YYYY-MM-DD",
                          col.get("Report_Date_as_MM_DD_YYYY"))
        code_idx = col["CFTC_Contract_Market_Code"]
        oi_idx = col["Open_Interest_All"]
        am_l, am_s = col["Asset_Mgr_Positions_Long_All"], col["Asset_Mgr_Positions_Short_All"]
        lf_l, lf_s = col["Lev_Money_Positions_Long_All"], col["Lev_Money_Positions_Short_All"]
        dl_l, dl_s = col["Dealer_Positions_Long_All"], col["Dealer_Positions_Short_All"]
        rows = list(rows)
    else:
        # old format: 0 name, 1 YYMMDD, 2 code, 3 mkt, 4 region, 5 commodity,
        # 6 OI, 7 dealerL, 8 dealerS, 9 amL, 10 amS, 11 lfL, 12 lfS, ...
        iso_idx, code_idx, oi_idx = None, 2, 6
        dl_l, dl_s, am_l, am_s, lf_l, lf_s = 7, 8, 9, 10, 11, 12
        rows = [first] + list(rows)
    for r in rows:
        if len(r) <= max(code_idx, oi_idx, lf_s):
            continue
        try:
            if iso_idx is not None:
                out = {"date": r[iso_idx]}
            else:
                d = r[1].strip()
                out = {"date": f"20{d[0:2]}-{d[2:4]}-{d[4:6]}"}
            out.update({
                "market": r[0],
                "contract_code": r[code_idx].strip(),
                "oi": float(r[oi_idx].strip()),
                "asset_mgr_long": float(r[am_l].strip()),
                "asset_mgr_short": float(r[am_s].strip()),
                "lev_fund_long": float(r[lf_l].strip()),
                "lev_fund_short": float(r[lf_s].strip()),
                "dealer_long": float(r[dl_l].strip()),
                "dealer_short": float(r[dl_s].strip()),
            })
            yield out
        except (ValueError, IndexError):
            continue


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data_cot"))
    args = ap.parse_args()
    zdir = os.path.join(args.out, "zips")
    os.makedirs(zdir, exist_ok=True)

    import pandas as pd

    # --- disagg commodities (COT classic) ---
    zips = [f"{BASE}/com_disagg_txt_hist_2006_2016.zip"]
    zips += [f"{BASE}/com_disagg_txt_{y}.zip" for y in range(2017, 2027)]

    all_rows = []
    for url in zips:
        name = os.path.basename(url)
        try:
            path = fetch(url, zdir, name)
        except requests.HTTPError as e:
            print(f"  SKIP {name}: {e}")
            continue
        with zipfile.ZipFile(path) as zf:
            fname = zf.namelist()[0]
            with zf.open(fname) as fh:
                text = io.TextIOWrapper(fh, encoding="latin-1")
                n = 0
                for row in parse_lines(text):
                    all_rows.append(row)
                    n += 1
                print(f"  {name}: {n} rows")

    df = pd.DataFrame(all_rows)
    df["report_date"] = pd.to_datetime(df["date"])
    df["spec_net"] = df["m_money_long"] - df["m_money_short"]
    df["spec_long_pct"] = df["m_money_long"] / df["oi"]
    df["spec_short_pct"] = df["m_money_short"] / df["oi"]
    df = df.sort_values(["contract_code", "report_date"]).drop_duplicates(
        ["contract_code", "report_date"], keep="last")
    out = os.path.join(args.out, "cot_tidy.csv")
    df.to_csv(out, index=False)
    print(f"\nsaved -> {out}: {len(df)} rows, {df['contract_code'].nunique()} "
          f"contracts, {df['report_date'].min().date()}..{df['report_date'].max().date()}")

    # --- TFF financials (equity index / rates / FX) ---
    fzips = [f"{BASE}/com_fin_txt_hist_2006_2016.zip"]
    fzips += [f"{BASE}/com_fin_txt_{y}.zip" for y in range(2010, 2027)]
    frows = []
    for url in fzips:
        name = os.path.basename(url)
        try:
            path = fetch(url, zdir, name)
        except requests.HTTPError as e:
            print(f"  SKIP {name}: {e}")
            continue
        with zipfile.ZipFile(path) as zf:
            fname = zf.namelist()[0]
            with zf.open(fname) as fh:
                text = io.TextIOWrapper(fh, encoding="latin-1")
                n = 0
                for row in parse_tff(text):
                    frows.append(row)
                    n += 1
                print(f"  {name}: {n} rows")

    tdf = pd.DataFrame(frows)
    tdf["report_date"] = pd.to_datetime(tdf["date"])
    tdf["am_net"] = tdf["asset_mgr_long"] - tdf["asset_mgr_short"]
    tdf["lf_net"] = tdf["lev_fund_long"] - tdf["lev_fund_short"]
    tdf = tdf.sort_values(["contract_code", "report_date"]).drop_duplicates(
        ["contract_code", "report_date"], keep="last")
    tout = os.path.join(args.out, "tff_tidy.csv")
    tdf.to_csv(tout, index=False)
    print(f"\nsaved -> {tout}: {len(tdf)} rows, {tdf['contract_code'].nunique()} "
          f"contracts, {tdf['report_date'].min().date()}..{tdf['report_date'].max().date()}")

    idx = tdf[tdf["market"].str.contains(
        "S&P 500|NASDAQ|DOW JONES|RUSSELL|VIX", case=False, na=False)]
    print("\nequity-index contracts (TFF):")
    for code, g in idx.groupby("contract_code"):
        g = g.sort_values("report_date")
        print(f"  {code} {g['market'].iloc[-1][:50]:50s} "
              f"{g['report_date'].min().date()}..{g['report_date'].max().date()} "
              f"({len(g)} wks)")


if __name__ == "__main__":
    main()
