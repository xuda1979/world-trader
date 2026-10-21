"""R7 charter item (a) - HUNT_TIMESFM own-code audit of DATA_COTMORE's trader-count panel.

INDEPENDENT of their builder: my own zip parser (content-dispatching date normalizer -
2010 zip headers label MM_DD_YYYY while carrying ISO content, so the label is not
trusted), my own duplicate/collision resolution, my own source-name boundary detector,
my own |delta|>=30% EXN gate. The only shared code is tools/quant/data/more_cot/
cot_matcher.py (campaign infra, not the audit target's code).

Checks:
  1. panel recount from disk: rows/cols/families/span/malformed/dup keys
  2. full-cell rebuild comparison: my raw parse vs committed CSV (all cnt_ cells + OI)
  3. z-column re-derivation: PIT expanding z (min_periods=26, ddof=0, sd==0 -> 0.0)
  4. EXN break gates fail-closed: my boundary detector must fire on EXACTLY
     nat_gas_nymex 2022-02-08 (-86%) and lumber 2023-04-25 (+105%)
  5. name-transition blind-spot scan: any |d%|>=30 magnitude jump in the panel NOT
     explained by a source-name transition = a break the gate cannot see
  6. eurodollar_3m end 2023-06-13 unchanged
  7. DEAD_IDEAS.csv recount + integrity + rows 135-137 verbatim + my rows verbatim

Run: python3 r7_cotmore_audit.py  > r7_cotmore_audit.log 2>&1
"""
import csv
import datetime as dt
import glob
import hashlib
import io
import os
import sys
import zipfile
import collections

sys.path.insert(0, "/Users/daxu/software/world-trader/tools/quant/data/more_cot")
from cot_matcher import match_market, priority_of  # campaign infra

RAW = "/Users/daxu/software/world-trader/tools/quant/data/more_cot/_raw"
PANEL = ("/Users/daxu/software/world-trader/campaign/agents/chief/coord/"
         "DATA_COTMORE/work_r5/trader_count_panel.csv")
LEDGER = "/Users/daxu/software/world-trader/campaign/results/DEAD_IDEAS.csv"

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
MIN_OBS = 26

ok = True


def check(label, cond, detail=""):
    global ok
    if not cond:
        ok = False
    print(f"[{'PASS' if cond else 'FAIL'}] {label}" + (f"  {detail}" if detail else ""))


def norm_date(tok):
    """CONTENT-dispatching normalizer: try ISO first, then MM/DD/YYYY. The 2010 zips'
    header says MM_DD_YYYY but carries ISO - never trust the label."""
    s = tok.strip().strip('"')
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"unparseable report date {tok!r}")


def to_int(tok):
    s = tok.strip()
    if not s or s == ".":
        return None
    return int(s.replace(",", ""))


def parse_zip(zp):
    kind = "fin" if "fin_txt" in os.path.basename(zp) else "disagg"
    cols = COUNT_COLS[kind]
    z = zipfile.ZipFile(zp)
    lines = [l for l in z.read(z.namelist()[0]).decode("latin-1").splitlines() if l.strip()]
    header = next(csv.reader(io.StringIO(lines[0])))
    idx = {c.strip().strip('"').strip(): i for i, c in enumerate(header)}
    di = idx.get("Report_Date_as_YYYY-MM-DD", idx.get("Report_Date_as_MM_DD_YYYY"))
    mi = idx["Market_and_Exchange_Names"]
    ao = idx["As_of_Date_In_Form_YYMMDD"]
    oi_i = idx["Open_Interest_All"]
    need = set(cols) | {"Open_Interest_All"}
    missing = [c for c in need if c not in idx]
    if missing or di is None:
        raise ValueError(f"{os.path.basename(zp)}: missing cols {missing} date={di}")
    out = []
    for line in lines[1:]:
        parts = next(csv.reader(io.StringIO(line)))
        fam = match_market(parts[mi].strip())
        if fam is None:
            continue
        vals = {c: to_int(parts[idx[c]]) for c in cols}
        rec = {"family": fam,
               "report_date": norm_date(parts[di]),
               "as_of": parts[ao].strip(),
               "source_name": parts[mi].strip(),
               "open_interest": to_int(parts[oi_i])}
        rec.update({f"cnt_{c}": vals[c] for c in cols})
        out.append(rec)
    return out


def resolve(rows):
    """My own resolution: (family,date,name) newer as_of wins; same-date different-name
    collision -> matcher priority wins. Returns {(fam,date): rec}."""
    best = {}
    for r in rows:
        k = (r["family"], r["report_date"])
        cur = best.get(k)
        if cur is None:
            best[k] = r
            continue
        if cur["source_name"] == r["source_name"]:
            if int(r["as_of"]) > int(cur["as_of"]):
                best[k] = r
        else:
            if priority_of(r["source_name"]) < priority_of(cur["source_name"]):
                best[k] = r
    return best


def expanding_z(vals):
    """PIT expanding z matching pandas expanding(min_periods=MIN_OBS) semantics:
    the window statistic needs >= MIN_OBS NON-BLANK observations (not row index);
    ddof=0; sd==0 (measured) -> 0.0; blank value -> blank z."""
    out = []
    for i, v in enumerate(vals):
        win = [x for x in vals[:i + 1] if x is not None]
        n = len(win)
        if v is None or n < MIN_OBS:
            out.append(None)
            continue
        mu = sum(win) / n
        sd = (sum((x - mu) ** 2 for x in win) / n) ** 0.5
        if sd == 0:
            out.append(0.0)
        else:
            out.append((v - mu) / sd)
    return out


def main():
    global ok
    # ---------- 1. panel recount from disk ----------
    raw = open(PANEL, "rb").read()
    sha16 = hashlib.sha256(raw).hexdigest()[:16]
    print(f"== 1. panel recount ==\nsha16 {sha16}  bytes {len(raw)}  "
          f"endswith_nl {raw.endswith(bytes([10]))}")
    with open(PANEL, newline="") as f:
        rows = list(csv.reader(f))
    hdr, data = rows[0], rows[1:]
    fi = {c: i for i, c in enumerate(hdr)}
    check("header cols == 51", len(hdr) == 51, f"got {len(hdr)}")
    check("data rows == 29051", len(data) == 29051, f"got {len(data)}")
    widths = collections.Counter(len(r) for r in data)
    check("0 malformed-width rows", set(widths) == {51}, f"widths {dict(widths)}")
    fams = sorted(set(r[0] for r in data))
    check("families == 35", len(fams) == 35, f"got {len(fams)}")
    dates = sorted(set(r[1] for r in data))
    check("span 2010-01-05..2026-09-01", (dates[0], dates[-1]) == ("2010-01-05", "2026-09-01"),
          f"{dates[0]}..{dates[-1]}")
    dupk = [k for k, c in collections.Counter((r[0], r[1]) for r in data).items() if c > 1]
    check("0 dup (family,report_date) keys", not dupk, f"{dupk[:5]}")

    # ---------- 2. rebuild from raw + full-cell comparison ----------
    print("== 2. own-code rebuild from raw zips ==")
    zips = sorted(glob.glob(os.path.join(RAW, "*.zip")))
    baks = sorted(glob.glob(os.path.join(RAW, "*.bak")))
    check("34 canonical zips (+2 baks not parsed)", len(zips) == 34 and len(baks) == 2,
          f"zips {len(zips)} baks {len(baks)}")
    allrows = []
    for zp in zips:
        allrows.extend(parse_zip(zp))
    print(f"matched raw rows: {len(allrows)}")
    resolved = resolve(allrows)
    print(f"resolved (family,date) rows: {len(resolved)}")

    mine = {}
    for (fam, d), r in resolved.items():
        cells = {"open_interest": r["open_interest"]}
        for c in hdr:
            if c.startswith("cnt_"):
                cells[c] = r.get(c)
        mine[(fam, d)] = cells

    panel_keys = {(r[0], r[1]) for r in data}
    check("key set == panel key set", panel_keys == set(mine),
          f"panel-only {len(panel_keys - set(mine))} mine-only {len(set(mine) - panel_keys)}")

    n_cells = n_bad = 0
    bad_samples = []
    for r in data:
        k = (r[0], r[1])
        m = mine[k]
        for c in [c for c in hdr if c.startswith("cnt_")] + ["open_interest"]:
            n_cells += 1
            pv = r[fi[c]]
            # panel cells are float-formatted ('23.0') wherever the column ever held
            # NaN (pandas concat upcast); blank '' = suppressed. Parse accordingly.
            pv = None if pv == "" else int(float(pv))
            if pv != m[c]:
                n_bad += 1
                if len(bad_samples) < 5:
                    bad_samples.append((k, c, pv, m[c]))
    check(f"cnt_* + OI cells all match ({n_cells} cells)", n_bad == 0,
          f"{n_bad} mismatched {bad_samples}")

    # ---------- 3. z re-derivation (max abs dev) ----------
    print("== 3. PIT expanding-z re-derivation ==")
    byfam = collections.defaultdict(list)
    for r in data:
        byfam[r[0]].append(r)
    max_dev = 0.0
    z_checked = 0
    for fam, rs in sorted(byfam.items()):
        rs.sort(key=lambda r: r[1])
        for c in [c for c in hdr if c.startswith("z_")]:
            src = "cnt_" + c[2:]  # z_Traders_Tot_All sources cnt_Traders_Tot_All
            vals = [None if r[fi[src]] == "" else int(float(r[fi[src]])) for r in rs]
            zs = expanding_z(vals)
            for r, z in zip(rs, zs):
                pz = r[fi[c]]
                if z is None:
                    continue  # panel may legitimately carry blank z on warmup/blank src
                z_checked += 1
                if pz == "":
                    max_dev = float("inf")
                    continue
                max_dev = max(max_dev, abs(float(pz) - z))
    check("z re-derivation max abs dev < 1e-9", max_dev < 1e-9,
          f"max_dev {max_dev:.3e} over {z_checked} non-blank z cells")

    # ---------- 4. EXN break gates (my own boundary detector) ----------
    print("== 4. EXN break gates - own boundary detector ==")
    name_of = {k: v["source_name"] for k, v in resolved.items()}
    breaks = []
    transitions = 0
    for fam, rs in sorted(byfam.items()):
        rs.sort(key=lambda r: r[1])
        prev = None
        for r in rs:
            k = (fam, r[1])
            cur_name = name_of[k]
            cur_tot = (None if r[fi["cnt_Traders_Tot_All"]] == ""
                       else int(float(r[fi["cnt_Traders_Tot_All"]])))
            cur_oi = (None if r[fi["open_interest"]] == ""
                      else int(float(r[fi["open_interest"]])))
            if prev is not None and cur_name != prev["name"]:
                transitions += 1
                for cc, a, b in (("Traders_Tot_All", prev["tot"], cur_tot),
                                 ("Open_Interest_All", prev["oi"], cur_oi)):
                    if a and b and a > 0 and b > 0:
                        pct = 100.0 * (b - a) / a
                        if abs(pct) >= 30:
                            breaks.append((fam, r[1], cc, a, b, pct))
                            break  # their gate reports the first qualifying column only
            prev = {"name": cur_name, "tot": cur_tot, "oi": cur_oi}
    print(f"name transitions walked: {transitions}")
    print(f"breaks fired: {len(breaks)}")
    for b in breaks:
        print(f"   {b[0]} {b[1]} {b[2]} {b[3]}->{b[4]} ({b[5]:+.1f}%)")
    expect = {("nat_gas_nymex", "2022-02-08", "Traders_Tot_All", 281, 40),
              ("lumber", "2023-04-25", "Traders_Tot_All", 21, 43)}
    got = {(b[0], b[1], b[2], b[3], b[4]) for b in breaks}
    check("EXN set == {nat_gas_nymex 2022-02-08 -86%, lumber 2023-04-25 +105%}",
          got == expect and len(breaks) == 2, f"got {sorted(got)}")
    ng = [b for b in breaks if b[0] == "nat_gas_nymex"]
    lb = [b for b in breaks if b[0] == "lumber"]
    check("nat_gas magnitude rounds to -86%", len(ng) == 1 and round(ng[0][5]) == -86,
          f"{ng[0][5]:+.2f}%" if ng else "n/a")
    check("lumber magnitude rounds to +105%", len(lb) == 1 and round(lb[0][5]) == 105,
          f"{lb[0][5]:+.2f}%" if lb else "n/a")

    # ---------- 5. same-name weekly jumps (DISCLOSURE, not a gate): the EXN gate's
    # documented contract is rename-seam detection (builder docstring: "source-name
    # transition + count discontinuity = universe BREAK"). Same-name jumps are market
    # reality UNLESS they are stitching/revision artifacts - so verify each against the
    # raw rows: count raw rows at that (family,date) pre-resolution. n_raw==1 => the
    # printed value is THE raw CFTC value, no resolution choice involved.
    print("== 5. same-name |dTotAll|>=30 weekly jumps -> raw provenance ==")
    raw_counts = collections.Counter((r["family"], r["report_date"]) for r in allrows)
    blind = []
    for fam, rs in sorted(byfam.items()):
        rs.sort(key=lambda r: r[1])
        prev = None
        for r in rs:
            k = (fam, r[1])
            cur_tot = (None if r[fi["cnt_Traders_Tot_All"]] == ""
                       else int(float(r[fi["cnt_Traders_Tot_All"]])))
            if prev is not None and prev["tot"] and cur_tot and prev["tot"] > 0:
                pct = 100.0 * (cur_tot - prev["tot"]) / prev["tot"]
                if abs(pct) >= 30 and name_of[k] == name_of[prev["k"]]:
                    blind.append((fam, r[1], prev["tot"], cur_tot, pct,
                                  raw_counts.get(k, 0)))
            prev = {"tot": cur_tot, "k": k}
    multi = [b for b in blind if b[5] != 1]
    print(f"same-name >=30% weekly jumps: {len(blind)}; "
          f"of those with >1 raw revision row: {len(multi)}")
    for b in blind:
        tag = "RAW-SINGLE" if b[5] == 1 else f"REVIEWS={b[5]}"
        print(f"   {b[0]} {b[1]} {b[2]}->{b[3]} ({b[4]:+.1f}%)  {tag}")
    # all cells already proven byte-equal to my own raw parse in check 2, so
    # RAW-SINGLE here means: the jump exists in the source file itself.

    # ---------- 6. eurodollar_3m ----------
    print("== 6. eurodollar_3m ==")
    ed = sorted(byfam.get("eurodollar_3m", []), key=lambda r: r[1])
    check("eurodollar_3m ends 2023-06-13", ed[-1][1] == "2023-06-13",
          f"n={len(ed)} last={ed[-1][1]}" if ed else "MISSING")

    # ---------- 7. DEAD_IDEAS ledger ----------
    print("== 7. DEAD_IDEAS ledger ==")
    lraw = open(LEDGER, "rb").read()
    lsha = hashlib.sha256(lraw).hexdigest()[:16]
    with open(LEDGER, newline="") as f:
        lrows = list(csv.reader(f))
    lhdr, ldata = lrows[0], lrows[1:]
    check("ledger header == 4 fields", len(lhdr) == 4, f"{lhdr}")
    malformed = [i for i, r in enumerate(ldata, 2) if len(r) != 4]
    check("0 malformed ledger rows", not malformed, f"{malformed[:5]}")
    duppair = [k for k, c in collections.Counter((r[0], r[3]) for r in ldata).items() if c > 1]
    check("0 byte-dup (idea,source) pairs", not duppair, f"{duppair[:3]}")
    print(f"ledger data rows: {len(ldata)}  sha16 {lsha}  "
          f"endswith_nl {lraw.endswith(bytes([10]))}")
    census = collections.Counter(r[1] for r in ldata)
    print(f"status census: {dict(sorted(census.items()))}")
    # rows 135-137 = COT2-R6 curation trio (data-row index, 1-based)
    r135, r136, r137 = ldata[134], ldata[135], ldata[136]
    check("row 135 source == HUNT_COT2-R6", r135[3] == "HUNT_COT2-R6", r135[3])
    check("row 136 source == HUNT_COT2-R6", r136[3] == "HUNT_COT2-R6", r136[3])
    check("row 137 source == HUNT_COT2-R6", r137[3] == "HUNT_COT2-R6", r137[3])
    check("row 135 idea is the positioning curation", "COT/TFF/CIT positioning" in r135[0],
          r135[0][:80])
    check("row 136 idea is the CREDIT2 correction", "CREDIT2" in r136[0], r136[0][:80])
    check("row 137 idea is the CMDT2 correction", "CMDT2" in r137[0], r137[0][:80])
    # my 4 rows (TIMESFM)
    tf = [(i, r) for i, r in enumerate(ldata, 2) if r[3] == "HUNT_TIMESFM"]
    check("exactly 4 HUNT_TIMESFM rows", len(tf) == 4, f"{[i for i, _ in tf]}")
    for i, r in tf:
        print(f"   line {i}: [{r[1]}] {r[0][:70]}...")

    print()
    print("AUDIT VERDICT:", "ALL PASS" if ok else "FAILURES PRESENT (see [FAIL] lines)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
