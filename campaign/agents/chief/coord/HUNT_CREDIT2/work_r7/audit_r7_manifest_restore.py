#!/usr/bin/env python3
"""HUNT_CREDIT2 ROUND 7 (a) - independent read-only audit of DATA_ETF_MORE-R6's
more_etf/manifest.csv restore via their work_r3/manifest_r3.py build().

Claims under test (DATA_ETF_MORE/FINDINGS.md, "DATA_ORGANIZE sweep clobber +
restore" section, 2026-09-08 ~16:2x):
  C1  restored sha16 = 9b04a324ebb4db04
  C2  schema = 82 rows x 10 cols, span_class non-empty on every row
  C3  exactly 2 loud FAILs: XLC start 2018-06-19, XLRE start 2015-10-08
      (both inception_fail, status FAIL(inception))
  C4  byte-identity rests on BUILDER DETERMINISM (no pre-clobber sha pinned
      anywhere; file untracked/gitignored -> not git-recoverable)

Method: call THEIR build() with DataFrame.to_csv monkeypatched to a recorder
(READ-ONLY: nothing written to disk), byte-compare the returned frame's
re-render against the on-disk file, then re-lint all 82 series with
INDEPENDENT code (no reuse of their lint_series/classify) and diff every row.
Run from anywhere; all paths absolute. Writes only inside HUNT_CREDIT2/work_r7/.
"""
import hashlib
import json
import os
import subprocess
import sys

import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
ETC_DIR = f"{ROOT}/tools/quant/data/more_etf"
MANIFEST = f"{ETC_DIR}/manifest.csv"
ETF_MORE = f"{ROOT}/campaign/agents/chief/coord/DATA_ETF_MORE"
HERE = f"{ROOT}/campaign/agents/chief/coord/HUNT_CREDIT2/work_r7"
CLAIMED_SHA16 = "9b04a324ebb4db04"
EXPECTED_COLS = ["symbol", "start", "end", "rows", "max_gap_days",
                 "zero_ret_rows", "jump_days", "dup_dates", "span_class", "status"]

results = {"claims": {}, "details": {}}


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def check(name, ok, detail=""):
    results["claims"][name] = {"ok": bool(ok), "detail": str(detail)}
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))
    return bool(ok)


# ---------------------------------------------------------------- before-state
before_sha = sha16(MANIFEST)
before_mtime = os.path.getmtime(MANIFEST)
print(f"BEFORE: manifest sha16={before_sha} mtime={before_mtime:.0f}")

# ---------------------------------------------------- C1: restored sha matches
print("\nC1 restored sha16 == 9b04a324ebb4db04")
check("C1_restored_sha16", before_sha == CLAIMED_SHA16, f"on-disk sha16={before_sha}")

# ------------------------------- run THEIR build() read-only (suppress write)
sys.path.insert(0, f"{ETF_MORE}/work_r3")
import manifest_r3  # noqa: E402  (their module, unmodified)

writes = []
_orig_to_csv = pd.DataFrame.to_csv


def _recording_to_csv(self, path=None, *a, **kw):
    writes.append({"path": str(path), "kwargs": kw})
    return _orig_to_csv(self, None, *a, **kw) if False else None  # suppress


pd.DataFrame.to_csv = _recording_to_csv
try:
    rebuilt = manifest_r3.build()
finally:
    pd.DataFrame.to_csv = _orig_to_csv

print(f"\nTHEIR build() re-run read-only: attempted writes={len(writes)} "
      f"-> {writes}")
results["details"]["attempted_writes"] = writes
print(f"returned frame: shape={rebuilt.shape}")

# ----------------------------------------------------- after-state: untouched
after_sha = sha16(MANIFEST)
after_mtime = os.path.getmtime(MANIFEST)
check("READONLY_no_write", after_sha == before_sha and after_mtime == before_mtime,
      f"after sha16={after_sha} mtime_delta={after_mtime - before_mtime:+.6f}s")

# ------------------------------------------------------------ C2: 82x10 schema
print("\nC2 schema 82 rows x 10 cols, span_class everywhere")
shape_ok = rebuilt.shape == (82, 10)
check("C2_shape_82x10", shape_ok, f"rebuilt shape={rebuilt.shape}")
cols_ok = list(rebuilt.columns) == EXPECTED_COLS
check("C2_columns_exact", cols_ok, f"cols={list(rebuilt.columns)}")
sc_ok = (rebuilt["span_class"].astype(str).str.len() > 0).all() and set(
    rebuilt["span_class"]) <= {"pre2007", "2007plus", "inception_fail"}
check("C2_span_class_populated", sc_ok,
      f"span_class values={sorted(set(rebuilt['span_class']))}")

# ----------------------------------------------------------- C3: the 2 FAILs
print("\nC3 exactly 2 loud FAILs: XLC 2018-06-19, XLRE 2015-10-08")
fails = rebuilt[rebuilt["status"].str.startswith("FAIL")]
fail_ok = (len(fails) == 2 and set(fails["symbol"]) == {"XLC", "XLRE"}
           and fails.loc[fails.symbol == "XLC", "start"].iloc[0] == "2018-06-19"
           and fails.loc[fails.symbol == "XLRE", "start"].iloc[0] == "2015-10-08"
           and (fails["span_class"] == "inception_fail").all()
           and (fails["status"] == "FAIL(inception)").all())
check("C3_two_loud_fails", fail_ok,
      "fails=" + fails[["symbol", "start", "rows", "span_class", "status"]].to_dict(
          "records").__repr__())
status_counts = rebuilt["status"].value_counts().to_dict()
print(f"  status counts: {status_counts}")
results["details"]["status_counts"] = status_counts

# ------------------------------------- C4a: determinism -> on-disk byte parity
print("\nC4a builder determinism reproduces on-disk bytes exactly")
rendered = _orig_to_csv(rebuilt, None, index=False)
ondisk = open(MANIFEST).read()
byte_identical = rendered == ondisk
disk_sha_full = hashlib.sha256(open(MANIFEST, "rb").read()).hexdigest()
render_sha_full = hashlib.sha256(rendered.encode()).hexdigest()
check("C4a_byte_identity_via_builder", byte_identical,
      f"disk={disk_sha_full[:16]} rendered={render_sha_full[:16]} "
      f"equal={disk_sha_full == render_sha_full}")

# ------------------------------- INDEPENDENT re-lint of every on-disk series
# (my own implementation; NOT their lint_series/classify)
PRE_B, INC_B = pd.Timestamp("2007-01-01"), pd.Timestamp("2013-01-01")
REF_END = pd.Timestamp("2026-09-01")   # pinned inside their manifest_r3 run
FRESH_DAYS = 365 * 3 + 92


def my_lint(path):
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    nonpos = int((df["close"] <= 0).sum())
    s = df.set_index("date")["close"].astype(float).sort_index()
    s = s[s > 0]
    n = len(s)
    start, end = s.index[0], s.index[-1]
    dups = int(s.index.duplicated().sum())
    maxgap = int(s.index.to_series().diff().dt.days.dropna().max())
    jumps = int((s.pct_change().abs() > 0.5).sum())
    # own zero-run implementation (no cumsum trick): longest run of equal steps
    d = s.diff()
    zrun, cur = 0, 0
    for v in (d == 0).tolist():
        cur = cur + 1 if v else 0
        zrun = max(zrun, cur)
    cls = ("pre2007" if start <= PRE_B else
           "2007plus" if start <= INC_B else "inception_fail")
    if n < 250:
        st = "FAIL(short)"
    elif dups > 0:
        st = "FAIL(dup)"
    elif maxgap > 10:
        st = "FAIL(gap)"
    elif jumps > 0:
        st = "FAIL(jumps)"
    elif (REF_END - end).days > FRESH_DAYS:
        st = "FAIL(stale)"
    elif cls == "inception_fail":
        st = "FAIL(inception)"
    else:
        st = "PASS" if cls == "pre2007" else "PASS_WAIVER"
    return dict(n=n, start=str(start.date()), end=str(end.date()),
                maxgap=maxgap, zrun=zrun, jumps=jumps, dups=dups,
                span_class=cls, status=st, nonpositive=nonpos)


mine = {}
bad_files = []
for fn in sorted(os.listdir(ETC_DIR)):
    if fn.endswith(".csv") and fn != "manifest.csv":
        try:
            mine[fn[:-4]] = my_lint(f"{ETC_DIR}/{fn}")
        except Exception as e:
            bad_files.append((fn, repr(e)[:80]))

print(f"\nINDEPENDENT re-lint: {len(mine)} series linted, {len(bad_files)} unreadable")

# compare disk manifest vs my re-lint, field by field
mf = pd.read_csv(MANIFEST)
mismatches = []
for _, r in mf.iterrows():
    sym = r["symbol"]
    if sym not in mine:
        mismatches.append(f"{sym}: no on-disk csv")
        continue
    for k in ("start", "end", "span_class", "status"):
        if str(r[k]) != mine[sym][k]:
            mismatches.append(f"{sym}.{k}: manifest={r[k]} mine={mine[sym][k]}")
    for k in ("n", "maxgap", "zrun", "jumps", "dups"):
        if int(r[{"n": "rows", "maxgap": "max_gap_days", "zrun": "zero_ret_rows",
                  "jumps": "jump_days", "dups": "dup_dates"}[k]]) != mine[sym][k]:
            mismatches.append(f"{sym}.{k}: manifest={r[k]} mine={mine[sym][k]}")
extra = set(mine) - set(mf["symbol"])
if extra:
    mismatches.append(f"csvs on disk not in manifest: {sorted(extra)}")
np_bad = {s: v["nonpositive"] for s, v in mine.items() if v["nonpositive"]}

check("DISK_MATCHES_INDEPENDENT_RELINT", not mismatches,
      f"{len(mismatches)} mismatches" + (f": {mismatches[:10]}" if mismatches else ""))
check("NO_NONPOSITIVE_CLOSES", not np_bad, f"{np_bad}" if np_bad else "all closes >0")
check("NO_UNREADABLE_CSVS", not bad_files, f"{bad_files}" if bad_files else "")

# ------------------------------------------------- R4 spot-facts (their claim)
print("\nR4 spot-facts claimed by DATA_ETF_MORE (HYG 4883 / ENOR 3676 / EIS 4640 / "
      "TUR 4641 / EPHE 4008 / COPX 4121, all PASS_WAIVER)")
spot = {s: (int(mf.loc[mf.symbol == s, "rows"].iloc[0]),
            mf.loc[mf.symbol == s, "status"].iloc[0]) for s in
        ["HYG", "ENOR", "EIS", "TUR", "EPHE", "COPX"]}
spot_ok = (spot == {"HYG": (4883, "PASS_WAIVER"), "ENOR": (3676, "PASS_WAIVER"),
                    "EIS": (4640, "PASS_WAIVER"), "TUR": (4641, "PASS_WAIVER"),
                    "EPHE": (4008, "PASS_WAIVER"), "COPX": (4121, "PASS_WAIVER")})
check("R4_SPOTFACTS", spot_ok, str(spot))

# ------------------------------------------------------ C4b: recoverability
print("\nC4b pre-clobber recoverability: untracked? pinned sha anywhere?")
gi = subprocess.run(["git", "check-ignore", "-v", MANIFEST], cwd=ROOT,
                    capture_output=True, text=True).stdout.strip()
tracked = subprocess.run(["git", "ls-files", "--error-unmatch", MANIFEST], cwd=ROOT,
                         capture_output=True, text=True)
gitlog = subprocess.run(["git", "log", "--all", "--oneline", "--",
                         "tools/quant/data/more_etf/manifest.csv"], cwd=ROOT,
                        capture_output=True, text=True).stdout.strip()
print(f"  check-ignore: {gi}")
print(f"  git ls-files (untracked => nonzero rc): rc={tracked.returncode}")
print(f"  git log --all -- <manifest>: {'(empty)' if not gitlog else gitlog}")
check("C4b_untracked_not_git_recoverable",
      tracked.returncode != 0 and not gitlog and "tools/quant/data/" in gi,
      f"ignored_by={gi.split(':')[0] if gi else '?'}")

# grep the coord tree + campaign for any pinned sha16 of the pre-clobber manifest
grep = subprocess.run(
    ["grep", "-rniE", r"more_etf/manifest", f"{ROOT}/campaign/agents/chief/coord",
     "--include=*.md", "--include=*.json", "--include=*.log"],
    capture_output=True, text=True)
hits = [l for l in grep.stdout.splitlines()]
shaish = [l for l in hits if "9b04a324" in l or "13a9c9cf" in l]
print(f"  coord grep 'more_etf/manifest': {len(hits)} hits, "
      f"{len(shaish)} carry a sha16 (9b04a324 restored / 13a9c9cf foreign-schema)")
for l in shaish[:6]:
    print(f"    {l.strip()[:150]}")
results["details"]["coord_grep_hits"] = len(hits)
results["details"]["coord_grep_shaish"] = shaish[:20]

# any manifest backups on disk under tools/quant/data?
baks = subprocess.run(["find", f"{ROOT}/tools/quant/data", "-maxdepth", "2",
                       "-name", "*manifest*"], capture_output=True, text=True).stdout
print("  manifest-like files under tools/quant/data:")
for l in baks.strip().splitlines():
    p = l.strip()
    if p:
        print(f"    {p}  sha16={sha16(p)} rows={sum(1 for _ in open(p))}")

results["details"]["before_after_sha16"] = [before_sha, after_sha]
results["details"]["rebuilt_rows"] = int(len(rebuilt))
results["details"]["mismatches"] = mismatches
results["details"]["spot"] = {k: list(v) for k, v in spot.items()}
results["details"]["waiver_rows"] = rebuilt[rebuilt.status == "PASS_WAIVER"][
    ["symbol", "start", "end", "rows"]].to_dict("records")

out = f"{HERE}/audit_r7_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=1, default=str)
n_fail = sum(1 for v in results["claims"].values() if not v["ok"])
print(f"\nAUDIT SUMMARY: {len(results['claims'])} checks, {n_fail} FAIL -> {out}")
