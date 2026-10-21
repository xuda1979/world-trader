# World Bank Pink Sheet (CMO) monthly commodity prices -- keyless, free.
#
# The estate had no broad commodity axis: EIA covers energy only, more_fred is
# macro. This adds 71 monthly commodity series back to 1960-01 (energy, metals,
# agri, softs, fertilisers) -- the longest free cross-commodity panel available
# without a key.
#
# Two traps this module exists to avoid, both found by probing the live file:
#
#  1. VINTAGE PINNING. The download link carries a version hash
#     ("...-0050012026"). Hardcoding it pins whatever vintage was current the day
#     it was written: the first probe here used a hardcoded "...-0050012025" URL
#     and silently served a file ending 2025M12 -- EIGHT MONTHS STALE.
#     resolve_xlsx_url() re-scrapes the index page every run, and lint() fails a
#     pull whose last month is not recent.
#  2. SILENT DATA LOSS. The sheet carries Excel error literals ("#VALUE!", four of
#     them in "Rice, Thai 25%"). Treating an unrecognised token as a missing
#     month is how the BCRP "Set" bug deleted every September in another family.
#     _classify() counts them as `bad` and lint() fails the series loudly.
#
# Policy on writing: every series the source publishes gets a manifest row, with
# the lint verdict recorded in its exception column. The Pink Sheet is a curated
# official publication; a series that stopped printing (Barley, last 2020-08) or
# reports sparsely (Sawnwood, Cameroon) is a property of the SOURCE, not a fetch
# failure. Silently dropping those would be the real defect. Pass --strict to
# write only verdict=ok series.
import csv
import datetime as dt
import io
import os
import re
import sys
import time
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data", "wb_commodity")
INDEX = "https://www.worldbank.org/en/research/commodity-markets"
XLSX_RE = r"https://thedocs\.worldbank\.org/[^\"<> ]+CMO-Historical-Data-Monthly\.xlsx"

NAME_ROW = 4
UNIT_ROW = 5
DATA_ROW = 6
# The sheet uses TWO "not published yet" markers: the ellipsis character
# (6,329 cells across 24 columns) and a plain ASCII "..." (84 cells, ALL in
# DAP). A full census of the file found exactly three non-numeric tokens, so
# anything that is neither is real corruption -- "#VALUE!" (4 cells, all in
# "Rice, Thai 25%"). Both sentinels map to missing; corruption fails loudly.
SENTINELS = set(["\u2026", "..."])


def _get(url, timeout=90, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url, headers=dict([("User-Agent", UA), ("Accept", "*/*")]))
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(), None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
                continue
            return None, repr(e)[:160]
    return None, "retries-exhausted"


def resolve_xlsx_url(html):
    hits = re.findall(XLSX_RE, html)
    if not hits:
        raise ValueError("no CMO-Historical-Data-Monthly.xlsx link on index page")
    return sorted(set(hits))[-1]


def month_to_iso(tok):
    # "2026M08" -> "2026-08-01"; anything else -> None.
    if len(tok) != 7 or tok[4] != "M":
        return None
    y, m = tok[:4], tok[5:]
    if not (y.isdigit() and m.isdigit()):
        return None
    mi = int(m)
    if not (1 <= mi <= 12):
        return None
    return "%s-%02d-01" % (y, mi)


def _classify(cell):
    # -> ("num", float) | ("missing", None) | ("bad", raw_token)
    if cell is None or isinstance(cell, bool):
        return ("missing", None)
    if isinstance(cell, (int, float)):
        return ("num", float(cell))
    s = str(cell).strip().replace(",", "")
    if not s or s in SENTINELS:
        return ("missing", None)
    try:
        return ("num", float(s))
    except ValueError:
        return ("bad", str(cell).strip()[:24])


def _num(cell):
    kind, v = _classify(cell)
    return v if kind == "num" else None


def parse_sheet(rows):
    # -> (updated_text, [(label, unit, pts, bad), ...])
    updated = ""
    if len(rows) > 3 and isinstance(rows[3][0], str):
        updated = rows[3][0].strip()
    names = rows[NAME_ROW] if len(rows) > NAME_ROW else []
    units = rows[UNIT_ROW] if len(rows) > UNIT_ROW else []
    cols = [j for j in range(len(names))
            if isinstance(names[j], str) and names[j].strip()]
    out = []
    for j in cols:
        label = names[j].strip()
        unit = units[j] if j < len(units) and isinstance(units[j], str) else ""
        pts, bad = [], []
        for r in rows[DATA_ROW:]:
            if not r or r[0] is None:
                continue
            iso = month_to_iso(str(r[0]).strip())
            if iso is None:
                continue
            kind, v = _classify(r[j]) if j < len(r) else ("missing", None)
            if kind == "num":
                pts.append((iso, v))
            elif kind == "bad":
                bad.append((iso, v))
        out.append((label, unit, pts, bad))
    return updated, out


def _months(start_iso, end_iso):
    y, m = int(start_iso[:4]), int(start_iso[5:7])
    ey, em = int(end_iso[:4]), int(end_iso[5:7])
    out = []
    while (y, m) <= (ey, em):
        out.append("%04d-%02d-01" % (y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def lint(pts, today, min_rows=120, max_stale_months=3, bad=None):
    # Fail-closed monthly census. Order matters: a bad cell is corruption and is
    # reported before anything else, so it can never be masked by a clean-looking
    # span. The staleness arm is what catches a re-pinned / stale download URL.
    bad = bad or []
    res = dict(n=len(pts), ok=False, reason="", gaps=0, stale_months=None, bad=len(bad))
    if bad:
        res["reason"] = "bad-cells=%d first=%s@%s" % (len(bad), bad[0][1], bad[0][0])
        return res
    if not pts:
        res["reason"] = "empty"
        return res
    dates = [p[0] for p in pts]
    if any(dates[i] >= dates[i + 1] for i in range(len(dates) - 1)):
        res["reason"] = "order/dupe"
        return res
    res["start"], res["end"] = dates[0], dates[-1]
    if any((v != v) or v <= 0.0 for _, v in pts):
        res["reason"] = "nonpositive/nan"
        return res
    if res["n"] < min_rows:
        res["reason"] = "n<min(%d<%d)" % (res["n"], min_rows)
        return res
    have = set(dates)
    miss = [m for m in _months(dates[0], dates[-1]) if m not in have]
    res["gaps"] = len(miss)
    if miss:
        res["reason"] = "month-gaps=%d first=%s" % (len(miss), miss[0])
        return res
    stale = (today.year - int(dates[-1][:4])) * 12 + (today.month - int(dates[-1][5:7]))
    res["stale_months"] = stale
    if stale > max_stale_months:
        res["reason"] = "closed=%dmo(last=%s)" % (stale, dates[-1])
        return res
    res["ok"] = True
    res["reason"] = "ok"
    return res


def slug(label):
    s = label.replace("**", "").strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def main(argv):
    strict = "--strict" in argv
    os.makedirs(OUT, exist_ok=True)
    today = dt.date.today()
    html, err = _get(INDEX, timeout=60)
    if err:
        print("FAIL index: " + err)
        return 1
    url = resolve_xlsx_url(html.decode("utf-8", "replace"))
    print("resolved: " + url, flush=True)
    blob, err = _get(url, timeout=300)
    if err:
        print("FAIL xlsx: " + err)
        return 1
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(blob), read_only=True, data_only=True)
    rows = [r for r in wb["Monthly Prices"].iter_rows(values_only=True)]
    updated, series = parse_sheet(rows)
    print("sheet says: %s  (%d series)" % (updated, len(series)), flush=True)
    clean, degraded = 0, []
    with open(os.path.join(OUT, "manifest.csv"), "w", newline="") as man:
        w = csv.writer(man)
        w.writerow(["family", "file", "date_col", "kind", "rows", "cols", "exception"])
        for label, unit, pts, bad in series:
            res = lint(pts, today, bad=bad)
            fname = slug(label) + ".csv"
            if not pts:
                degraded.append((fname, res["reason"]))
                print("SKIP %-28s %s" % (fname, res["reason"]))
                continue
            if res["ok"] or not strict:
                with open(os.path.join(OUT, fname), "w", newline="") as f:
                    f.write("date,value\n")
                    for d, v in pts:
                        f.write("%s,%s\n" % (d, repr(v)))
            w.writerow(["wb_commodity", fname, "date", "timeseries", str(res["n"]), "2",
                        "src=pinksheet unit=%s verdict=%s gaps=%d" % (unit, res["reason"], res["gaps"])])
            if res["ok"]:
                clean += 1
                print("OK   %-28s n=%-5d %s..%s" % (fname, res["n"], res["start"], res["end"]))
            else:
                degraded.append((fname, res["reason"]))
                print("DEGRADED %-24s n=%-5d %s" % (fname, res["n"], res["reason"]))
    print("wb_commodity: %d clean, %d degraded, %d total (strict=%s)"
          % (clean, len(degraded), len(series), strict))
    if degraded:
        print("degraded: " + "; ".join("%s=%s" % t for t in degraded))
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
