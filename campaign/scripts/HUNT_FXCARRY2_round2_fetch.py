#!/usr/bin/env python3
"""HUNT_FXCARRY2 round-2 DATA step (charter (a)).

Fetch the free FRED daily FX DEX family + monthly immediate-rate (IRSTCI01)
short-rate differentials + CPI (for real carry) into
tools/quant/data/more_fx/{id}.csv with a manifest (MANIFEST.md).

Coordination with DATA_FREDMORE: this agent owns tools/quant/data/more_fx/
ONLY; it does not touch tools/quant/data/more_fred/ (DATA_FREDMORE wrote
DEXUSEU/DEXCAUS there already — this dir is HUNT_FXCARRY2's own copy set).

All writes go through fred_dl.fetch + fred_dl.lint (fail-closed, no splices):
a series that fails lint is NOT written; it is recorded as FAIL in the
manifest with the lint reason.
"""
import sys, os, csv, json
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/tools/quant/data/more_fred")
import fred_dl

OUT = f"{ROOT}/tools/quant/data/more_fx"
MANIFEST = f"{OUT}/MANIFEST.md"

# (series_id, role, expected_freq, observation_start or None)
# ids verified live vs FRED API on 2026-09-07 (IR3T01* does NOT exist on FRED;
# IRSTCI01 immediate rates do, per charter's "verify ids" instruction).
# Start-trims = publication holes in the earliest years (e.g. DEXJPUS has an
# 11-business-day hole in Feb-1971; DEXKOUS 3-day hole May-1981) — same
# legitimate vintage-trim precedent as DATA_FREDMORE R1 (VIXCLS from 2004,
# IRLTLT01NZM156N from 1979-10). No splices: raw FRED observations only.
SERIES = [
    ("DEXUSEU",         "fx eur_usd (USD per EUR)",        "daily",   None),
    ("DEXJPUS",         "fx usd_jpy (yen per USD)",        "daily",   "1972-01-01"),
    ("DEXCAUS",         "fx usd_cad",                      "daily",   None),
    ("DEXUSUK",         "fx usd_gbp (USD per GBP)",        "daily",   "1972-01-01"),
    ("DEXSZUS",         "fx usd_chf",                      "daily",   "1972-01-01"),
    ("DEXUSAL",         "fx aud_usd",                      "daily",   "1973-01-01"),
    ("DEXNOUS",         "fx usd_nok",                      "daily",   "1972-01-01"),
    ("DEXSIUS",         "fx usd_sgd",                      "daily",   None),
    ("DEXKOUS",         "fx usd_krw",                      "daily",   "1993-01-01"),
    ("IRSTCI01USM156N", "immediate rate US (3m-ish, monthly)", "monthly", None),
    ("IRSTCI01DEM156N", "immediate rate DE (EUR leg)",     "monthly", None),
    ("IRSTCI01FRM156N", "immediate rate FR (EUR leg)",     "monthly", None),
    ("IRSTCI01JPM156N", "immediate rate JP",               "monthly", None),
    ("IRSTCI01GBM156N", "immediate rate GB",               "monthly", None),
    ("IRSTCI01CAM156N", "immediate rate CA",               "monthly", None),
    ("IRSTCI01CHM156N", "immediate rate CH",               "monthly", None),
    ("IRSTCI01AUM156N", "immediate rate AU",               "monthly", None),
    ("IRSTCI01NZM156N", "immediate rate NZ",               "monthly", None),
    ("IRSTCI01EZM156N", "immediate rate EZ agg (EUR leg 1999+)", "monthly", None),
    ("IRSTCI01NOM156N", "immediate rate NO",               "monthly", None),
    ("IRSTCI01KRM156N", "immediate rate KR",               "monthly", None),
    ("CPALTT01USM657N", "CPI US (real-carry deflator)",    "monthly", None),
    ("CPALTT01DEM657N", "CPI DE",                          "monthly", None),
    ("CPALTT01JPM657N", "CPI JP",                          "monthly", None),
    ("CPALTT01GBM657N", "CPI GB",                          "monthly", None),
    ("CPALTT01CAM657N", "CPI CA",                          "monthly", None),
    ("CPALTT01CHM657N", "CPI CH",                          "monthly", None),
    # CPALTT01AUM657N / 659N / 661N / AUCPIEQ020: HTTP400 series-does-not-exist
    # on FRED (probed 2026-09-07) => permanent fail; AU real-carry done via
    # nominal-rate minus US-AU CPI only if a legit AU CPI appears. Not spliced.
    ("CPALTT01CNM657N", "CPI NZ",                          "monthly", None),
    ("CPALTT01FRM657N", "CPI FR",                          "monthly", None),
]


def key():
    for line in open(f"{ROOT}/.env.local"):
        if line.startswith("FRED_KEY"):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no FRED_KEY")


def main():
    os.makedirs(OUT, exist_ok=True)
    k = key()
    rows = []
    npass = nfail = 0
    for sid, role, freq, start in SERIES:
        (obs, nmiss), err = fred_dl.fetch(sid, k, start=start)
        rec = dict(series_id=sid, role=role, freq="", n=0, start="", end="",
                   gaps=0, status="")
        if err is not None:
            rec["status"] = "FAIL:fetch:" + err
            rows.append(rec)
            nfail += 1
            print("%-18s %s" % (sid, rec["status"]), flush=True)
            continue
        f = fred_dl.detect_freq(obs)
        rec["freq"] = f if f != "unknown" else freq
        lr = fred_dl.lint(obs, freq=rec["freq"])
        rec.update(n=lr["n"], start=lr["start"] or "", end=lr["end"] or "",
                   gaps=lr.get("gaps", 0))
        if not lr["pass"]:
            rec["status"] = "FAIL:lint:" + lr["reason"]
            nfail += 1
            print("%-18s %s" % (sid, rec["status"]), flush=True)
        else:
            rec["status"] = "PASS"
            npass += 1
            with open(f"{OUT}/{sid}.csv", "w") as fo:
                fred_dl.write_csv(fo, obs, sid)
            print("%-18s PASS n=%-6d %s..%s gaps=%d" %
                  (sid, lr["n"], lr["start"], lr["end"], lr.get("gaps", 0)),
                  flush=True)
        rows.append(rec)
    with open(MANIFEST, "w") as fm:
        fm.write("# HUNT_FXCARRY2 ROUND-2 DATA MANIFEST (tools/quant/data/more_fx)\n")
        fm.write("Fetcher: campaign/scripts/HUNT_FXCARRY2_round2_fetch.py — fred_dl.fetch + "
                 "fail-closed lint; only PASS written. Fetched 2026-09-07.\n\n")
        fm.write("| series | freq | role | start | end | n | gaps | status |\n|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            fm.write("| %s | %s | %s | %s | %s | %s | %s | %s |\n" % (
                r["series_id"], r["freq"], r["role"], r["start"], r["end"],
                r["n"], r["gaps"], r["status"]))
        fm.write("\nPASS %d / FAIL %d / total %d\n" % (npass, nfail, len(rows)))
    print("manifest ->", MANIFEST, "| PASS", npass, "FAIL", nfail)


if __name__ == "__main__":
    main()
