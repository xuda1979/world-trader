#!/usr/bin/env python3
"""DATA_FREDMORE R6 independent verifier — fraud-catch cross-verification.

Own code: re-derives every checkable number in DATA_ETF_MORE R5 (bench pack) and
DATA_COTMORE R5 (trader_count_panel + PCR freeze) from raw artifacts, plus the
charter-(b) FRED health census for the CAMP_COST lane (DFF n=26,363 / SOFR n=2,198
through 2026-09-03 pinned by CAMP_BORROW/work_r5/fred_{dff,sofr}.csv).
NO imports of either agent's modules. Exit 0 = all checks PASS; nonzero = fail-closed.
"""
import csv
import hashlib
import json
import os
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

import urllib.request

ROOT = "/Users/daxu/software/world-trader"
AG = f"{ROOT}/campaign/agents/chief/coord"
DATA = f"{ROOT}/tools/quant/data"

FAILS = []
N_OK = 0


def check(name, ok, detail=""):
    global N_OK
    if ok:
        N_OK += 1
        print(f"  ok  {name} {detail}")
    else:
        FAILS.append(name)
        print(f" FAIL {name} {detail}")
    return ok


def sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def read_keyvals(path, delim="="):
    out = {}
    with open(path) as f:
        for line in f:
            if delim in line:
                k, v = line.split(delim, 1)
                out[k.strip()] = v.strip()
    return out


# ============================================================ A. DATA_ETF_MORE
print("== A. DATA_ETF_MORE R5 claims (bench pack) ==")

print("A1. §7c trio pins byte-identical (claimed d35d72808dcc9fc3/603cb2a56afd5616/"
      "d7f3b5cd4616f0f4)")
for path, want in [
    (f"{DATA}/twelvedata/SPY.csv", "d35d72808dcc9fc3"),
    (f"{DATA}/more_etf/IEF.csv", "603cb2a56afd5616"),
    (f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv", "d7f3b5cd4616f0f4"),
]:
    got = sha16(path)
    check(os.path.basename(path), got == want, f"got {got}")

print("A2. candidate files exist + end fresh (claimed ends 2026-09-02/04)")
for sym in ["GLD", "SLV", "IAU", "DBC", "GSG", "UUP", "TIP"]:
    p = f"{DATA}/more_etf/{sym}.csv"
    if not check(f"{sym}.csv exists", os.path.exists(p)):
        continue
    rows = list(csv.reader(open(p)))
    end = rows[-1][0]
    check(f"{sym}.csv fresh end", end >= "2026-08-25", f"end={end} rows={len(rows)-1}")

print("A3. champion of record untouched: sha 4358dfab95679b97")
got = sha16(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
check("champion sha", got == "4358dfab95679b97", f"got {got}")

print("A4. bench_r5 manifest.csv deliverable state — RESTORED (was clobbered by the "
      "DATA_ORGANIZE 14:40 sweep when this check was written R6; owner rebuilt it "
      "byte-exact via their registered work_r5/bench_r5.py build() — rich_manifest_"
      "registry.json pin. R7 pin update, FREDMORE charter: 'update YOUR pin, not the "
      "manifest': the restored bytes equal the R6-claimed original sha.)")
mp = f"{DATA}/bench_r5/manifest.csv"
mf = open(mp, "rb").read()
hdr = mf.split(b"\n")[0].decode()
check("manifest schema RESTORED to their claimed symbol,role,... schema",
      hdr.startswith("symbol,role"), f"header now {hdr!r}")
check("claimed sha256 326afe5a28db2809 matches restored on-disk bytes",
      sha16(mp) == "326afe5a28db2809", f"on-disk now {sha16(mp)}")
check("README restamped by organize sweep (Generated: 2026-09-08 + canonical line)",
      b"DATA_ORGANIZE.md" in open(mp.replace("manifest.csv", "README.md"), "rb").read())
# reconstructed rows: reproduce THEIR build() from their script logic with my own code
print("A5. independent re-derivation of their 10 claimed manifest rows "
      "(trio 3 PIN + UUP/GLD SELECTED + 4 eligible_not_selected + TIP rejected)")

def load_px(path):
    rows = [(r[0], float(r[1])) for r in csv.reader(open(path))[1:]] if False else None
    return rows


def px(path, col="close"):
    """Price reader with header-aware column pick (SPY.csv is date,open,high,low,close,vol)."""
    rd = csv.reader(open(path))
    hdr = next(rd)
    if col in hdr:
        ci = hdr.index(col)
    else:
        ci = 1
    s = {}
    for r in rd:
        try:
            v = float(r[ci])
            if v > 0:
                s[r[0]] = v
        except (ValueError, IndexError):
            pass
    return s


def rets(pxs):
    ks = sorted(pxs)
    out = {}
    for a, b in zip(ks, ks[1:]):
        out[b] = (pxs[b] / pxs[a]) - 1.0
    return out


def pearson(x, y):
    n = len(x)
    if n < 2:
        return float("nan")
    mx = sum(x) / n
    my = sum(y) / n
    sx = sum((a - mx) ** 2 for a in x) ** 0.5
    sy = sum((a - my) ** 2 for a in y) ** 0.5
    if sx == 0 or sy == 0:
        return float("nan")
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


TRIO_FILES = [("spy", f"{DATA}/twelvedata/SPY.csv"),
              ("ief", f"{DATA}/more_etf/IEF.csv"),
              ("cta", f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv")]

# CTA is a ret curve (date,ret) - pass-through; SPY/IEF/candidates are prices.
def load_any(path, mode):
    rd = csv.reader(open(path))
    hdr = next(rd)
    ci = hdr.index("close") if "close" in hdr else (
        hdr.index("ret") if "ret" in hdr else 1)
    s = {}
    for r in rd:
        try:
            v = float(r[ci])
            s[r[0]] = v
        except (ValueError, IndexError):
            pass
    if mode == "price":
        ks = sorted(s)
        out = {}
        for a, b in zip(ks, ks[1:]):
            out[b] = s[b] / s[a] - 1.0
        return out
    return s


trio_rets = {n: load_any(p, "ret_curve" if n == "cta" else "price") for n, p in TRIO_FILES}
champ_rets = load_any(f"{ROOT}/campaign/results/"
                      "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv", "ret_curve")

EXPECT = {  # symbol: (max_corr_trio, corr_spy, corr_ief, corr_cta, corr_champ, rows)
    "UUP": (0.1833, -0.1833, -0.1480, -0.0156, 0.0028, 4911),
    "GLD": (0.2043, 0.0628, 0.2043, 0.0553, 0.0119, 5483),
    "SLV": (0.2294, None, None, None, None, None),
    "IAU": (0.2056, None, None, None, None, None),
    "GSG": (0.3705, None, None, None, None, None),
    "DBC": (0.0, None, None, None, None, None),  # placeholder, checked below
    "TIP": (0.7635, None, None, None, None, None),
}
MINC = 1008
for sym in ["UUP", "GLD", "SLV", "IAU", "GSG", "DBC", "TIP"]:
    p = f"{DATA}/more_etf/{sym}.csv"
    s = px(p)
    sr = rets(s)
    cs = {}
    nobs = {}
    for tn, tr in trio_rets.items():
        common = sorted(set(sr) & set(tr))
        if len(common) < MINC:
            cs[tn] = float("nan")
            nobs[tn] = len(common)
            continue
        cs[tn] = pearson([sr[d] for d in common], [tr[d] for d in common])
        nobs[tn] = len(common)
    cc = sorted(set(sr) & set(champ_rets))
    corr_champ = (pearson([sr[d] for d in cc], [champ_rets[d] for d in cc])
                  if len(cc) >= MINC else float("nan"))
    mx = max(abs(v) for v in cs.values() if v == v)
    rows_n = len(s)
    span_y = None
    ks = sorted(s)
    d0 = datetime.strptime(ks[0], "%Y-%m-%d")
    d1 = datetime.strptime(ks[-1], "%Y-%m-%d")
    span_y = (d1 - d0).days / 365.25
    exp = EXPECT[sym]
    if sym == "DBC":
        check(f"{sym} max_corr_trio ~0.3789", abs(mx - 0.3789) < 0.003, f"mine {mx:.4f}")
    else:
        check(f"{sym} max_corr_trio == claimed {exp[0]}", abs(mx - exp[0]) < 0.003,
              f"mine {mx:.4f}")
    if sym in ("UUP", "GLD"):
        check(f"{sym} corr_spy == claimed", abs(cs["spy"] - exp[1]) < 0.003,
              f"mine {cs['spy']:.4f}")
        check(f"{sym} corr_ief == claimed", abs(cs["ief"] - exp[2]) < 0.003,
              f"mine {cs['ief']:.4f}")
        check(f"{sym} corr_cta == claimed", abs(cs["cta"] - exp[3]) < 0.003,
              f"mine {cs['cta']:.4f}")
        check(f"{sym} corr_champion == claimed", abs(corr_champ - exp[4]) < 0.003,
              f"mine {corr_champ:.4f}")
        check(f"{sym} rows == claimed {exp[5]}", rows_n == exp[5], f"mine {rows_n}")
    if sym == "TIP":
        check("TIP control rejected for corr_ief>0.5", abs(cs["ief"] - 0.7635) < 0.003,
              f"corr_ief mine {cs['ief']:.4f} (claimed 0.7635)")
    print(f"    [{sym}] rows={rows_n} span={span_y:.1f}y max|corr|trio={mx:.4f} "
          f"corr_champ={corr_champ:.4f}")

# selection rule reproduction: rank eligible by max_corr asc, take 2, skip pair>0.7
print("A6. selection rule reproduction: UUP+GLD must be the greedy pick")
cand_maxcorr = {"UUP": None, "GLD": None, "SLV": None, "IAU": None, "GSG": None,
                "DBC": None}

def maxcorr(sym):
    s = px(f"{DATA}/more_etf/{sym}.csv")
    sr = rets(s)
    vals = []
    for tn, tr in trio_rets.items():
        common = sorted(set(sr) & set(tr))
        vals.append(abs(pearson([sr[d] for d in common], [tr[d] for d in common])))
    return max(vals)

mc = {s: maxcorr(s) for s in cand_maxcorr}
gld_iau = None
si = set(rets(px(f"{DATA}/more_etf/SLV.csv")))
ii = set(rets(px(f"{DATA}/more_etf/IAU.csv")))
g = set(rets(px(f"{DATA}/more_etf/GLD.csv")))
c_s_i = pearson([rets(px(f"{DATA}/more_etf/SLV.csv"))[d] for d in sorted(si & ii)],
                [rets(px(f"{DATA}/more_etf/IAU.csv"))[d] for d in sorted(si & ii)])
ranked = sorted(mc.items(), key=lambda kv: kv[1])
print(f"    ranked: {[(k, round(v,4)) for k,v in ranked]}")
check("SLV|IAU pair corr > 0.7 (gold-complex dup, forced skip of IAU after GLD)",
      abs(c_s_i) > 0.7, f"corr {c_s_i:.4f}")
gg = rets(px(f"{DATA}/more_etf/GLD.csv"))
iir = rets(px(f"{DATA}/more_etf/IAU.csv"))
common_gi = sorted(set(gg) & set(iir))
c_g_i2 = pearson([gg[d] for d in common_gi], [iir[d] for d in common_gi])
check("GLD|IAU pair corr > 0.7", abs(c_g_i2) > 0.7, f"corr {c_g_i2:.4f}")
gg = rets(px(f"{DATA}/more_etf/GLD.csv"))
ssr = rets(px(f"{DATA}/more_etf/SLV.csv"))
common_gs = sorted(set(gg) & set(ssr))
c_g_s2 = pearson([gg[d] for d in common_gs], [ssr[d] for d in common_gs])
check("GLD|SLV pair corr > 0.7", abs(c_g_s2) > 0.7, f"corr {c_g_s2:.4f}")
u_r = rets(px(f"{DATA}/more_etf/UUP.csv"))
g_r = rets(px(f"{DATA}/more_etf/GLD.csv"))
ug = sorted(set(u_r) & set(g_r))
c_ug = pearson([u_r[d] for d in ug], [g_r[d] for d in ug])
check("UUP|GLD pair corr <= 0.7", abs(c_ug) <= 0.7, f"corr {c_ug:.4f}")

# consumption smoke: champion SR pin via bt.beats_passive (the shared engine module;
# their claimed trio-on-champion-span: spy_bh 0.5863 / sixty_forty 0.5916 / cta -0.1097)
print("A7. consumption smoke: bt.beats_passive best_passive_sr on the champion span "
      "(their claim: spy_bh 0.5863 / sixty_forty 0.5916 / cta_trend -0.1097, "
      "best=sixty_forty)")
sys.path.insert(0, f"{ROOT}/campaign")
import pandas as pd
from bt.beats_passive import best_passive_sr
champ = pd.read_csv(f"{ROOT}/campaign/results/"
                    "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
champ["date"] = pd.to_datetime(champ["date"])
cr = champ.set_index("date")["ret"]
spy = pd.read_csv(f"{DATA}/twelvedata/SPY.csv")
spy["date"] = pd.to_datetime(spy["date"])
spy = spy.set_index("date")["close"].pct_change().dropna()
ief = pd.read_csv(f"{DATA}/more_etf/IEF.csv")
ief["date"] = pd.to_datetime(ief["date"])
ief = ief.set_index("date")["close"].pct_change().dropna()
cta = pd.read_csv(f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv")
cta["date"] = pd.to_datetime(cta["date"])
cta = cta.set_index("date")["ret"]
bp = best_passive_sr(cr, spy=spy, ief=ief, cta=cta)
print(f"    mine: {bp[1]}")
check("best passive SR == 0.5916 (sixty_forty)", abs(bp[0] - 0.5916) < 0.005,
      f"mine {bp[0]:.4f}")
srs = {k: v["sr"] for k, v in bp[1].items() if isinstance(v, dict) and "sr" in v}
print(f"    per-benchmark SRs: { {k: round(v, 4) for k, v in srs.items()} }")
check("spy_bh ~0.5863", abs(srs.get("spy_bh", 9) - 0.5863) < 0.005,
      f"mine {srs.get('spy_bh'):.4f}" if 'spy_bh' in srs else "missing")
check("sixty_forty ~0.5916", abs(srs.get("sixty_forty", 9) - 0.5916) < 0.005,
      f"mine {srs.get('sixty_forty'):.4f}" if 'sixty_forty' in srs else "missing")
check("cta_trend ~-0.1097", abs(srs.get("cta_trend", 9) - (-0.1097)) < 0.005,
      f"mine {srs.get('cta_trend'):.4f}" if 'cta_trend' in srs else "missing")

# ============================================ B. DATA_COTMORE R5 (trader panel)
print("== B. DATA_COTMORE R5 claims (trader_count_panel) ==")
P5 = f"{AG}/DATA_COTMORE/work_r5/trader_count_panel.csv"
P4 = f"{AG}/DATA_COTMORE/work_r4/trader_count_panel.csv"
print("B1. vintage pins")
check("panel sha16 == 9e2c82303acf4c24", sha16(P5) == "9e2c82303acf4c24", sha16(P5))
check("R4 panel sha16 == 02aa8f0028144d9d", sha16(P4) == "02aa8f0028144d9d", sha16(P4))
for path, want in [(f"{DATA}/more_cot/_raw/fut_disagg_txt_2026.zip", "70e18ad5a7e61745"),
                   (f"{DATA}/more_cot/_raw/fut_fin_txt_2026.zip", "7b744b8c6b241008"),
                   (f"{DATA}/more_cot/_raw/fut_disagg_txt_2026.zip.sep3.bak",
                    "3e816c649e39c016"),
                   (f"{DATA}/more_cot/_raw/fut_fin_txt_2026.zip.sep3.bak",
                    "0d3a015f09b47a05")]:
    check(os.path.basename(path), sha16(path) == want, sha16(path))

print("B2. independent structure count from MY csv reader (claimed 29051x51x35)")
fams = Counter()
n = 0
cols = None
min_d = max_d = None
rel_new = set()
with open(P5) as f:
    rd = csv.reader(f)
    cols = next(rd)
    for row in rd:
        n += 1
        fams[row[0]] += 1
        d = row[1]
        if min_d is None or d < min_d:
            min_d = d
        if max_d is None or d > max_d:
            max_d = d
        if d == "2026-09-01":
            rel_new.add(row[2])
check("rows == 29051", n == 29051, str(n))
check("cols == 51", len(cols) == 51, str(len(cols)))
check("families == 35", len(fams) == 35, str(len(fams)))
check("span 2010-01-05..2026-09-01", (min_d, max_d) == ("2010-01-05", "2026-09-01"),
      f"{min_d}..{max_d}")
check("new week 2026-09-01: 34 families", fams and max_d == "2026-09-01"
      and sum(1 for r in csv.reader(open(P5)) if len(r) > 1 and r[1] == "2026-09-01")
      == 34, f"{sum(1 for r in csv.reader(open(P5)) if len(r)>1 and r[1]=='2026-09-01')}")
check("new week release_date all 2026-09-04", rel_new == {"2026-09-04"}, str(rel_new))

print("B3. R4->R5 delta decomposition: +34 rows, pure append (0 changed cells)")
def load_panel(path):
    out = {}
    with open(path) as f:
        rd = csv.reader(f)
        hdr = next(rd)
        for row in rd:
            out[(row[0], row[1])] = row
    return hdr, out

h4, p4 = load_panel(P4)
h5, p5 = load_panel(P5)
shared = set(p4) & set(p5)
added = set(p5) - set(p4)
check("R4 keys all present in R5 (0 dropped)", not (set(p4) - set(p5)),
      f"dropped {len(set(p4)-set(p5))}")
check("added rows == 34", len(added) == 34, str(len(added)))
changed = 0
cnt_idx = [i for i, c in enumerate(h4) if c.startswith("cnt_")]
for k in shared:
    for i in cnt_idx:
        if p4[k][i] != p5[k][i]:
            changed += 1
check("changed cnt_ cells across 29017 shared rows == 0", changed == 0, str(changed))
new_fams = {k[0] for k in added}
check("eurodollar_3m +0 in delta", "eurodollar_3m" not in new_fams or
      sum(1 for k in added if k[0] == "eurodollar_3m") == 0,
      str(sum(1 for k in added if k[0] == "eurodollar_3m")))

print("B4. BREAK gate anchors byte-stable (nat_gas 2022-02-08 281->40; lumber "
      "2023-04-25 21->43)")
def tot_all(rows_map, fam, d):
    r = rows_map.get((fam, d))
    return None if r is None else float(r[5])

v_before = tot_all(p5, "nat_gas_nymex", "2022-02-01")
v_after = tot_all(p5, "nat_gas_nymex", "2022-02-08")
check("nat_gas anchor 281->40 (-86%)", (v_before, v_after) == (281.0, 40.0),
      f"{v_before}->{v_after}")
lb = tot_all(p5, "lumber", "2023-04-18")
la = tot_all(p5, "lumber", "2023-04-25")
check("lumber anchor 21->43 (+105%)", (lb, la) == (21.0, 43.0), f"{lb}->{la}")

print("B5. release-lag discipline: report Tue -> release next Friday")
def fridays(rep):
    d = datetime.strptime(rep, "%Y-%m-%d").date()
    delta = (4 - d.weekday()) % 7 or 7  # Friday=4; strictly AFTER
    return (d + timedelta(days=delta)).isoformat()

new_reps = sorted({k[1] for k in added})
ok_rel = all(p5[(f, r)][2] == fridays(r) for f in new_fams for r in new_reps
             for f in [f] if (f, r) in p5)
check("new-week release_date == next-Friday(report_date) for all 34 families", ok_rel)

print("B6. PCR freeze evidence pins (claimed remote==local 3/3, remote_rows "
      "3256/3256/2332)")
for path, want_rows in [
    (f"{DATA}/cboe_pcr/_raw/totalpc.csv", 3256),
    (f"{DATA}/cboe_pcr/_raw/equitypc.csv", 3256),
    (f"{DATA}/cboe_pcr/_raw/spxpc.csv", 2332),
]:
    if not check(os.path.basename(path) + " exists", os.path.exists(path)):
        continue
    # CBOE archive CSVs carry a 2-line preamble; data header is the first line whose
    # first cell is DATE/Date; dates are M/D/YYYY; spxpc is latin-1 with CRLF.
    data_hdr_idx = None
    with open(path, encoding="latin-1") as f:
        lines = f.readlines()
    for i, ln in enumerate(lines):
        first = ln.split(",")[0].strip().strip('"').lower()
        if first in ("date",):
            data_hdr_idx = i
            break
    check(os.path.basename(path) + " has DATE header", data_hdr_idx is not None)
    rows = []
    for ln in lines[data_hdr_idx + 1:]:
        cells = ln.split(",")
        if len(cells) >= 2 and "/" in cells[0]:
            m, d, y = cells[0].strip().split("/")
            iso = f"{y}-{int(m):02d}-{int(d):02d}"
            rows.append(iso)
    check(os.path.basename(path) + f" data rows == {want_rows - (3 if want_rows == 3256 else 2)}",
          len(rows) == want_rows - (3 if want_rows == 3256 else 2), str(len(rows)))
    check(os.path.basename(path) + " frozen at 2019-10-04",
          bool(rows) and rows[-1] == "2019-10-04", rows[-1] if rows else "none")
    with open(path, "rb") as f:
        lb = f.read()
    check(os.path.basename(path) + f" total newline count == {want_rows} "
          "(their remote_rows convention)",
          lb.count(b"\n") == want_rows, str(lb.count(b"\n")))

print("B7. MY OWN live CBOE spot-fetch (independent of their R5 probe): "
      "1 API variant + archive byte-compare, now")
import urllib.error
try:
    req = urllib.request.Request(
        "https://cdn.cboe.com/api/global/delayed_quotes/put_call_ratios/_all.json",
        headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        status = r.status
except urllib.error.HTTPError as e:
    status = e.code
check("put_call_ratios/_all.json still 403", status == 403, f"HTTP {status}")
for fname, want_nl in [("totalpc.csv", 3256), ("equitypc.csv", 3256),
                       ("spxpc.csv", 2332)]:
    url = ("https://cdn.cboe.com/resources/options/volume_and_call_put_ratios/"
           + fname)
    try:
        with urllib.request.urlopen(urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
            b = r.read()
        same = b == lb if False else None
        with open(f"{DATA}/cboe_pcr/_raw/{fname}", "rb") as f:
            lb2 = f.read()
        check(f"{fname} live byte-identical to on-disk (freeze re-verified today)",
              b == lb2, f"live n={len(b)} on-disk n={len(lb2)} "
              f"sha16={hashlib.sha256(b).hexdigest()[:16]}")
    except Exception as e:
        check(f"{fname} live fetch", False, repr(e)[:80])

# ================================= C. charter (b): FRED endpoint health census
print("== C. FRED health census for the CAMP_COST sleeve-refresh lane ==")
W5B = f"{AG}/CAMP_BORROW/work_r5"
print("C1. charter-pinned R5 freshness artifacts on disk (fetched 09-08 07:00)")
for path, want_n, want_last in [(f"{W5B}/fred_dff.csv", 26363, "2026-09-03"),
                                (f"{W5B}/fred_sofr.csv", 2198, "2026-09-03")]:
    rows = list(csv.reader(open(path)))[1:]
    check(os.path.basename(path) + f" n=={want_n}", len(rows) == want_n, str(len(rows)))
    check(os.path.basename(path) + f" last=={want_last}", rows[-1][0] == want_last,
          rows[-1][0])

print("C2. LIVE re-fetch from api.stlouisfed.org (FRED_KEY from .env.local)")
key = ""
with open(f"{ROOT}/.env.local") as f:
    for line in f:
        if line.startswith("FRED_KEY"):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
check("FRED_KEY present", bool(key))

def fred_fetch(sid, limit=5):
    url = (f"https://api.stlouisfed.org/fred/series/observations?series_id={sid}"
           f"&api_key={key}&file_type=json&sort_order=desc&limit={limit}")
    with urllib.request.urlopen(url, timeout=30) as r:
        j = json.load(r)
    obs = j["observations"]
    real = [o for o in obs if o["value"] != "."]
    return real[0]["date"], real[0]["value"], len(j["observations"])

live = {}
for sid in ["DFF", "SOFR"]:
    try:
        d, v, nf = fred_fetch(sid)
        live[sid] = (d, v)
        print(f"    {sid}: live latest obs {d} = {v}")
    except Exception as e:
        check(f"{sid} live fetch", False, repr(e)[:80])

check("DFF live end >= 2026-09-03 (refresh lane not blocked)", live["DFF"][0]
      >= "2026-09-03", live["DFF"][0])
check("SOFR live end >= 2026-09-03", live["SOFR"][0] >= "2026-09-03", live["SOFR"][0])

print("C3. on-disk refresh blockers: more_fred DFF/SOFR vintages vs live")
d_ondisk = list(csv.reader(open(f"{DATA}/more_fred/DFF.csv")))[1:]
s_ondisk = list(csv.reader(open(f"{DATA}/more_fred/SOFR.csv")))[1:]
print(f"    more_fred/DFF.csv n={len(d_ondisk)} end={d_ondisk[-1][0]} "
      f"(mtime 09-03 15:11)")
print(f"    more_fred/SOFR.csv n={len(s_ondisk)} end={s_ondisk[-1][0]} "
      f"(mtime 09-03 22:18)")
check("DFF on-disk STALE vs live (documented, NOT refreshed by me - quiet data tree)",
      d_ondisk[-1][0] < live["DFF"][0], f"{d_ondisk[-1][0]} < {live['DFF'][0]}")
check("SOFR on-disk STALE vs live (documented)", s_ondisk[-1][0] < live["SOFR"][0],
      f"{s_ondisk[-1][0]} < {live['SOFR'][0]}")

print("C4. same-date revision check: on-disk last-row value equals the live value AT "
      "THAT SAME DATE (cross-date compare removed — R6 FINDINGS caveat; a cross-date "
      "match said nothing about revisions)")
# live series keyed by date over a window long enough to cover the on-disk last date
live_by_date = {}
for sid in ["DFF", "SOFR"]:
    try:
        _d, _v, _ = fred_fetch(sid, limit=30)
        obs_all = None
        url = (f"https://api.stlouisfed.org/fred/series/observations?series_id={sid}"
               f"&api_key={key}&file_type=json&sort_order=desc&limit=30")
        with urllib.request.urlopen(url, timeout=30) as r:
            obs_all = json.load(r)["observations"]
        live_by_date[sid] = {o["date"]: o["value"] for o in obs_all
                             if o["value"] != "."}
    except Exception as e:
        check(f"{sid} same-date window fetch", False, repr(e)[:80])

_disk_last = {"DFF": d_ondisk[-1], "SOFR": s_ondisk[-1]}
for sid in ["DFF", "SOFR"]:
    drow = _disk_last[sid]
    dd, dv = drow[0], float(drow[1])
    got = live_by_date.get(sid, {}).get(dd)
    if got is None:
        check(f"{sid} C4 same-date({dd}) live value available", False,
              f"live window starts {min(live_by_date.get(sid, {'9999': ''}) or {'9999': ''})}")
    else:
        # SOFR prints fix at ~15:00 ET and can revise the same day; DFF is an exact
        # effective-rate print — same tolerance class as the old check but now the
        # comparison is genuinely same-date.
        tol = 0.011 if sid == "SOFR" else 1e-9
        check(f"{sid} C4 no revision at boundary ({dd}): disk {dv} vs live-at-{dd}",
              abs(float(got) - dv) < tol, f"{dv} vs {got}")

print("C5. wider refresh-lane census: series named by CAMP_COST/CAMP_SHORT charters")
LANE = ["DFF", "SOFR", "DJFUELUSGULF", "WTISPLC"]  # borrow-lane FRED inputs
for sid in LANE[2:]:
    try:
        d, v, _ = fred_fetch(sid)
        print(f"    {sid}: live latest obs {d} = {v}")
        check(f"{sid} live reachable", d >= "2026-01-01", d)
    except Exception as e:
        check(f"{sid} live fetch", False, repr(e)[:80])

# ============================================ D. round hygiene
print("== D. round hygiene ==")
import subprocess
try:
    with open(f"{AG}/DATA_FREDMORE/work_r6/dead_ideas_count.txt") as f:
        cnt = f.read().strip()
    check("DEAD_IDEAS rows at round start recorded", bool(cnt), cnt)
except FileNotFoundError:
    check("DEAD_IDEAS rows at round start recorded", False, "file missing")

print(f"\n=== {N_OK} PASS / {len(FAILS)} FAIL ===")
if FAILS:
    print("FAILED:", FAILS)
    sys.exit(1)
print("VERDICT: ALL CHECKS PASS")
