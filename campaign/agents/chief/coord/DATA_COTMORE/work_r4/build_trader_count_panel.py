"""R4(b) trader-count breadth panel builder — charter deliverable.

Builds a clean weekly panel of CFTC disaggregated/financial trader COUNTS (the `Traders_*`
columns the closure memo flagged as never-tested breadth data), from the in-repo raw zips.
Data deliverable ONLY: lint, PIT z-scores, manifest. NO signal hunting (HUNT_* territory).

Fail-closed policy (all test-locked):
- '.' sentinel (CFTC confidentiality suppression) -> blank, never 0, never imputed.
- hard gates: negative count, or per-category count > its side total > grand total -> LintError.
- date-column rename 2013 (MM_DD_YYYY -> YYYY-MM-DD) handled; unparseable date -> LintError.
- duplicate (family, report_date): same-name re-report -> newer as_of wins (revision);
  different-name collision (rename seam) -> matcher priority wins, collision RECORDED.
- PIT expanding z-scores: uses rows <= t only; MIN_OBS warmup -> NaN; ddof=0; blank -> blank;
  constant window -> 0.0 (measured degenerate, not inf).

Run:  python3 build_trader_count_panel.py     (from DATA_COTMORE/work_r4/)
Writes: trader_count_panel.csv (+ prints per-family lint rows for MANIFEST_R4.md).
"""
import csv
import datetime as dt
import glob
import io
import os
import sys
import zipfile

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/Users/daxu/software/world-trader/tools/quant/data/more_cot")

from cot_matcher import match_market, priority_of  # noqa: E402

RAW = "/Users/daxu/software/world-trader/tools/quant/data/more_cot/_raw"

CORE = ["Traders_Tot_All", "Traders_Tot_Rept_Long_All", "Traders_Tot_Rept_Short_All"]
DIS_CAT = ["Traders_Prod_Merc_Long_All", "Traders_Prod_Merc_Short_All",
           "Traders_Swap_Long_All", "Traders_Swap_Short_All", "Traders_Swap_Spread_All",
           "Traders_M_Money_Long_All", "Traders_M_Money_Short_All",
           "Traders_M_Money_Spread_All", "Traders_Other_Rept_Long_All",
           "Traders_Other_Rept_Short_All", "Traders_Other_Rept_Spread_All"]
FIN_CAT = ["Traders_Dealer_Long_All", "Traders_Dealer_Short_All", "Traders_Dealer_Spread_All",
           "Traders_Asset_Mgr_Long_All", "Traders_Asset_Mgr_Short_All",
           "Traders_Asset_Mgr_Spread_All", "Traders_Lev_Money_Long_All",
           "Traders_Lev_Money_Short_All", "Traders_Lev_Money_Spread_All",
           "Traders_Other_Rept_Long_All", "Traders_Other_Rept_Short_All",
           "Traders_Other_Rept_Spread_All"]
COUNT_COLS = {"disagg": CORE + DIS_CAT, "fin": CORE + FIN_CAT}

MIN_OBS = 26          # expanding-z warmup (half a year of weekly reports)
MAX_GAP_DAYS = 21     # lint gate: weekly cadence

LAST_UNMATCHED = 0
LAST_COLLISIONS = []


class LintError(ValueError):
    pass


def release_date(report_ts):
    """Next Friday STRICTLY after the report Tuesday (or holiday Monday).
    Mirrors align_daily.release_shift / lib_hunt: Tue report -> Fri release (+3d),
    Mon holiday report -> Fri (+4d). PIT-safe: never same day."""
    d = report_ts.normalize()
    shift = (4 - d.weekday()) % 7
    if shift == 0:
        shift = 7
    return d + pd.Timedelta(days=shift)


def _to_int(tok):
    """CFTC count cell -> int or None ('.' sentinel or blank = suppressed, NEVER 0)."""
    s = tok.strip()
    if not s or s == ".":
        return None
    return int(s.replace(",", ""))


def _parse_date(tok):
    """Shape-check then CALENDAR-validate. R4 session-2: prior draft accepted
    shape-valid impossible dates (2010-01-33) -> gap math on nonsense. Fail-closed."""
    s = tok.strip()
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        y, m, d = s[:4], s[5:7], s[8:]
    elif len(s) == 10 and s[2] == "/" and s[5] == "/":
        y, m, d = s[6:], s[:2], s[3:5]
    else:
        raise LintError(f"unparseable report date {tok!r}")
    try:
        dt.date(int(y), int(m), int(d))
    except ValueError:
        raise LintError(f"impossible calendar date {tok!r}") from None
    return f"{y}-{m}-{d}"


def parse_zip(zp):
    """One zip -> DataFrame of matched rows (family-level), fail-closed on integrity."""
    global LAST_UNMATCHED
    kind = "fin" if "fin_txt" in os.path.basename(zp) else "disagg"
    cols = COUNT_COLS[kind]
    z = zipfile.ZipFile(zp)
    lines = [l for l in z.read(z.namelist()[0]).decode("latin-1").splitlines() if l.strip()]
    header = next(csv.reader(io.StringIO(lines[0])))
    idx = {c.strip().strip('"').strip(): i for i, c in enumerate(header)}
    missing = [c for c in cols if c not in idx]
    if missing:
        raise LintError(f"{os.path.basename(zp)}: missing trader columns {missing}")
    if "Open_Interest_All" not in idx:
        raise LintError(f"{os.path.basename(zp)}: no Open_Interest_All")
    di = idx.get("Report_Date_as_YYYY-MM-DD",
                 idx.get("Report_Date_as_MM_DD_YYYY"))
    if di is None:
        raise LintError(f"{os.path.basename(zp)}: no report-date column")
    mi = idx["Market_and_Exchange_Names"]
    ao = idx["As_of_Date_In_Form_YYMMDD"]
    oi_i = idx["Open_Interest_All"]

    out = []
    for line in lines[1:]:
        parts = next(csv.reader(io.StringIO(line)))
        if len(parts) <= max(idx.values()):
            raise LintError(f"{os.path.basename(zp)}: short row: {line[:80]!r}")
        fam = match_market(parts[mi].strip())
        if fam is None:
            LAST_UNMATCHED += 1
            continue
        vals = {}
        for c in cols:
            try:
                vals[c] = _to_int(parts[idx[c]])
            except ValueError:
                raise LintError(f"{os.path.basename(zp)}: bad count cell {c}={parts[idx[c]]!r}")
        oi = _to_int(parts[oi_i])
        if oi is None or oi <= 0:
            raise LintError(f"{os.path.basename(zp)}: bad OI {parts[oi_i]!r}")
        # hard integrity: no negatives; nesting cat <= side total <= grand total.
        # (spread counts are cross-side entities: excluded from side nesting identity)
        tt = vals["Traders_Tot_All"]
        trl = vals["Traders_Tot_Rept_Long_All"]
        trs = vals["Traders_Tot_Rept_Short_All"]
        for name, v in vals.items():
            if v is not None and v < 0:
                raise LintError(f"negative trader count {name}={v}")
        if tt is None:
            raise LintError("Traders_Tot_All suppressed (never expected: 0% in raw)")
        for side_tot, cats in ((trl, [c for c in cols if c.endswith("_Long_All") and "Spread" not in c
                                      and c not in CORE]),
                               (trs, [c for c in cols if c.endswith("_Short_All") and "Spread" not in c
                                      and c not in CORE])):
            if side_tot is None:
                continue
            if side_tot > tt:
                raise LintError(f"side total {side_tot} > grand total {tt}")
            for c in cats:
                v = vals[c]
                if v is not None and v > side_tot:
                    raise LintError(f"{c}={v} > side total {side_tot}")
        rec = {"family": fam,
               "report_date": _parse_date(parts[di]),
               "as_of": parts[ao].strip(),
               "source_name": parts[mi].strip(),
               "format": kind,
               "open_interest": oi}
        rec.update({f"cnt_{c}": vals[c] for c in cols})
        out.append(rec)
    return pd.DataFrame(out)


def build_panel(zips):
    """Parse zips, resolve duplicates/renames, compute PIT z-scores. Sorted by family/date."""
    global LAST_UNMATCHED, LAST_COLLISIONS
    LAST_UNMATCHED = 0
    LAST_COLLISIONS = []
    frames = [parse_zip(zp) for zp in zips]
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if df.empty:
        return df

    # duplicate resolution: (family, report_date, source_name) re-report -> newer as_of wins
    asof_key = df["as_of"].astype(int)
    df = (df.assign(_a=asof_key)
            .sort_values(["family", "report_date", "source_name", "_a"])
            .drop_duplicates(subset=["family", "report_date", "source_name"], keep="last")
            .drop(columns="_a"))

    # rename-seam collisions: different matched names, same family+date -> matcher priority
    kept = []
    for (fam, d), g in df.groupby(["family", "report_date"], sort=False):
        if len(g) == 1:
            kept.append(g.iloc[0])
            continue
        winner = min(g.itertuples(), key=lambda r: priority_of(r.source_name))
        for r in g.itertuples():
            if r.Index != winner.Index:
                LAST_COLLISIONS.append((fam, d, r.source_name, winner.source_name))
        kept.append(g.loc[winner.Index])
    panel = pd.DataFrame(kept)

    # PIT expanding z-scores per family+column
    cnt_cols = [c for c in panel.columns if c.startswith("cnt_")]
    panel = panel.sort_values(["family", "report_date"]).reset_index(drop=True)
    zs = {}
    for (fam), g in panel.groupby("family", sort=False):
        for c in cnt_cols:
            s = g[c].astype(float)  # blanks stay NaN
            mu = s.expanding(min_periods=MIN_OBS).mean()
            sd = s.expanding(min_periods=MIN_OBS).std(ddof=0)
            z = (s - mu) / sd
            # sd==0 (measured constant window) -> 0.0, not inf. Use mask on sd==0 so the
            # WARMUP rows (sd NaN while < MIN_OBS) keep NaN: where(sd>0, 0.0) zeroed them
            # because NaN > 0 is False — phantom z=0 signal during warmup (test-caught).
            z = z.mask(sd == 0, 0.0)
            z[s.isna()] = float("nan")        # blank count -> blank z
            zs[(fam, c)] = z
    zcol = pd.Series(index=panel.index, dtype=float)
    zcols = {}
    for c in cnt_cols:
        col = pd.Series(index=panel.index, dtype=float)
        for (fam, cc), z in zs.items():
            if cc == c:
                col.loc[panel.index[panel["family"] == fam]] = z
        zcols[f"z_{c[4:]}"] = col
    for k, v in zcols.items():
        panel[k] = v
    return panel


def real_zips():
    return sorted(glob.glob(os.path.join(RAW, "*.zip")))


def lint_panel(panel):
    """Per-family lint: cadence, span, sentinel stats. Fail-closed reasons in status."""
    rows = []
    for fam, g in panel.groupby("family"):
        g = g.sort_values("report_date")
        d = pd.to_datetime(g["report_date"])
        gaps = d.diff().dt.days.dropna()
        max_gap = int(gaps.max()) if len(gaps) else 0
        problems = []
        breaks = []
        if max_gap > MAX_GAP_DAYS:
            problems.append(f"gap {max_gap}d > {MAX_GAP_DAYS}d")
        # source-name transition + count discontinuity = universe BREAK, not a rename
        # (nat_gas NATURAL GAS->HENRY HUB 2022-02-08: TotAll 281->40). Measured, not raised:
        # the data is real, the STITCH is what lies. Flag PASS_WITH_EXN with magnitudes.
        names = g["source_name"].astype(str)
        # a boundary is the FIRST row of a new name-run (prev row has the old name);
        # row 0 has no predecessor. (ne(shift()) & ne(shift(-1)) never fires at a
        # single transition — the last old-name row fails the first clause.)
        boundary = names.ne(names.shift()) & names.shift().notna()
        for i in g.index[boundary]:
            prev = g.loc[g.index[g.index < i][-1]] if (g.index < i).any() else None
            cur = g.loc[i]
            if prev is None:
                continue
            for cc in ("Traders_Tot_All", "Open_Interest_All"):
                a = prev["open_interest"] if cc == "Open_Interest_All" else prev[f"cnt_{cc}"]
                b = cur["open_interest"] if cc == "Open_Interest_All" else cur[f"cnt_{cc}"]
                if pd.notna(a) and pd.notna(b) and a > 0 and b > 0:
                    drop = 100 * (b - a) / a
                    if abs(drop) >= 30:
                        breaks.append(
                            f"break at {cur['report_date']} {prev['source_name']}->"
                            f"{cur['source_name']}: {cc} {int(a)}->{int(b)} ({drop:+.0f}%)")
                    break
        # suppression measured over the family's OWN format columns only: the CSV
        # carries the union of disagg+fin cnt cols, and the other format's columns
        # are structurally NaN — counting them inflated missing_pct by ~15-20pp.
        own = [f"cnt_{c}" for c in COUNT_COLS[g["format"].iloc[0]]]
        n_cells = len(g) * len(own)
        n_missing = int(sum(g[c].isna().sum() for c in own))
        core_missing = int(g[[f"cnt_{c}" for c in CORE]].isna().sum().sum())
        if problems:
            status = "FAIL: " + "; ".join(problems)
        elif breaks:
            status = "PASS_WITH_EXN(break: " + "; ".join(breaks) + ")"
        else:
            status = "PASS"
        rows.append({"family": fam, "format": g["format"].iloc[0],
                     "start": g["report_date"].iloc[0], "end": g["report_date"].iloc[-1],
                     "n": len(g), "max_gap_days": max_gap,
                     "missing_cells": n_missing, "missing_pct": round(100 * n_missing / n_cells, 1),
                     "core_missing_cells": core_missing, "status": status})
    return {r["family"]: r for r in rows}


def main():
    zips = real_zips()
    panel = build_panel(zips)
    lint = lint_panel(panel)
    out_cols = (["family", "report_date", "release_date", "format", "open_interest"]
                + [c for c in panel.columns if c.startswith("cnt_")]
                + [c for c in panel.columns if c.startswith("z_")])
    panel = panel.copy()
    panel["release_date"] = pd.to_datetime(panel["report_date"]).map(release_date).dt.strftime("%Y-%m-%d")
    panel = panel.sort_values(["family", "report_date"])
    path = os.path.join(HERE, "trader_count_panel.csv")
    panel[out_cols].to_csv(path, index=False)
    print(f"wrote {path}: {len(panel)} rows x {len(out_cols)} cols, "
          f"{panel['family'].nunique()} families")
    print(f"unmatched-market rows skipped: {LAST_UNMATCHED}")
    print(f"rename collisions resolved by priority: {len(LAST_COLLISIONS)}")
    for c in LAST_COLLISIONS[:10]:
        print("  ", c)
    fails = [r for r in lint.values() if r["status"].startswith("FAIL")]
    print(f"\nlint: {len(lint)} families, {len(fails)} FAIL")
    for r in sorted(lint.values(), key=lambda x: x["family"]):
        print(f"  {r['family']:18s} {r['format']:6s} {r['start']}..{r['end']} n={r['n']:4d} "
              f"gap<={r['max_gap_days']:2d}d miss={r['missing_pct']:5.1f}% "
              f"core_miss={r['core_missing_cells']} {r['status']}")
    if fails:
        sys.exit(1)
    print("ALL FAMILIES LINT PASS")


if __name__ == "__main__":
    main()
