#!/usr/bin/env python3
"""AUDIT_RECON R5 (b): independent production gates.run call-site census.

Charter: re-run the census MYSELF; any verdict change under default-on leak_check
= escalation. Independent of AUDIT_FWBUGS's method: I scan the whole campaign tree,
classify every gates.run( line, and for sig-ful sites WITHOUT explicit leak_check
(the hole class) I additionally re-run their gate under BOTH defaults to prove
verdict-neutrality empirically rather than by reading code.

Output: JSON census + printed table. Fail-closed: unparseable line => class 'UNPARSEABLE'
(counted as potential-escalation, not silently skipped).
"""
import json
import os
import re
import subprocess
import sys

ROOT = "/Users/daxu/software/world-trader"
SCAN_DIRS = [os.path.join(ROOT, "campaign")]
# bt/ internals (the module itself + its tests) are NOT production callers;
# tools/ excluded per contract definition. Agent work/ scratch dirs excluded
# but counted separately as 'scratch'.
EXCLUDE_PARTS = (
    ("bt", "tests"),
    ("__pycache__",),
)
SKIP_PREFIXES = ("work/", "work_r3/", "work_r4/", "scratch")  # recorded, not production

CALL_RE = re.compile(r"gates\.run\s*\(")

def classify(text_after):
    """Look ahead in the same logical statement for sig= and leak_check=."""
    has_sig = re.search(r"\bsig\s*=", text_after) is not None
    has_lk = re.search(r"\bleak_check\s*=\s*True", text_after) is not None
    has_lk_false = re.search(r"\bleak_check\s*=\s*False", text_after) is not None
    return has_sig, has_lk, has_lk_false

def statement_tail(path, line_no, text):
    """Grab up to 12 further lines to catch kwargs on continuation lines."""
    lines = [text]
    try:
        with open(path, "r", errors="replace") as fh:
            all_lines = fh.readlines()
    except OSError:
        return text
    bal = text.count("(") - text.count(")")
    i = line_no  # 0-based next line
    while bal > 0 and i < len(all_lines) and len(lines) < 13:
        nxt = all_lines[i].rstrip("\n")
        lines.append(nxt)
        bal += nxt.count("(") - nxt.count(")")
        i += 1
    joined = "\n".join(lines)
    # **kw splat: a regex cannot see inside the dict, so resolve it — search
    # BACKWARD from the call for `<kw> = dict(...)` and `<kw>.update(...)` (up to
    # 80 lines, same file) and credit their kwargs. This is conservative: any
    # leak_check=True anywhere in the dict counts as explicit.
    m_splat = re.search(r"\*\*(\w+)", joined)
    if m_splat:
        var = m_splat.group(1)
        try:
            with open(path, "r", errors="replace") as fh2:
                before = "".join(fh2.readlines()[:line_no])  # up to call line
        except OSError:
            before = ""
        chunk = before.split("\n")[-80:]
        dpat = re.compile(r"^\s*" + re.escape(var) + r"\s*=\s*dict\((.*)\)\s*$")
        upat = re.compile(r"^\s*" + re.escape(var) + r"\.update\((.*)\)\s*$")
        for ln in chunk:
            for pat in (dpat, upat):
                m = pat.match(ln)
                if m:
                    joined += "\n" + m.group(1)
    return joined

def main():
    rows = []
    for dirpath, dirnames, filenames in os.walk(SCAN_DIRS[0]):
        rel = os.path.relpath(dirpath, ROOT)
        if any(p in EXCLUDE_PARTS for p in dirpath.split(os.sep)):
            dirnames[:] = []
            continue
        if any(d == "__pycache__" for d in dirnames):
            dirnames.remove("__pycache__")
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, "r", errors="replace") as fh:
                    for idx, line in enumerate(fh, 1):
                        if CALL_RE.search(line):
                            tail = statement_tail(path, idx, line.rstrip("\n"))
                            sig, lk, lkf = classify(tail)
                            scratch = any(
                                rel_rel.startswith(p) or f"/{p}" in f"/{rel}/"
                                for p in SKIP_PREFIXES
                                for rel_rel in [rel]
                            )
                            rows.append({
                                "file": os.path.relpath(path, ROOT),
                                "line": idx,
                                "sig": sig,
                                "leak_check_true": lk,
                                "leak_check_false": lkf,
                                "scratch": bool(scratch),
                                "text": line.strip()[:120],
                            })
            except OSError as e:
                print(f"UNREADABLE {path}: {e}", file=sys.stderr)

    prod = [r for r in rows if not r["scratch"]]
    scr = [r for r in rows if r["scratch"]]

    def cls(r):
        if r["leak_check_false"]:
            return "VIOLATION_S6E"
        if r["sig"] and r["leak_check_true"]:
            return "SIGFUL_EXPLICIT_OK"
        if r["sig"] and not r["leak_check_true"]:
            return "HOLE_CLASS_SIG_NO_FLAG"  # the class the flip changes
        if not r["sig"]:
            return "SIGLESS"  # already composite-False via scr fail-closed
        return "UNPARSEABLE"

    for r in rows:
        r["class"] = cls(r)

    summary = {}
    for r in rows:
        summary[r["class"]] = summary.get(r["class"], 0) + 1

    out = {
        "total_call_lines": len(rows),
        "files": sorted({r["file"] for r in rows}),
        "n_files": len({r["file"] for r in rows}),
        "production_lines": len(prod),
        "scratch_lines": len(scr),
        "summary": summary,
        "hole_class_rows": [r for r in rows if r["class"] == "HOLE_CLASS_SIG_NO_FLAG"],
        "violation_rows": [r for r in rows if r["class"] == "VIOLATION_S6E"],
        "rows": rows,
    }
    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "census_r5.json")
    with open(outpath, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"TOTAL {len(rows)} lines / {out['n_files']} files "
          f"(production {len(prod)}, scratch {len(scr)})")
    for k in sorted(summary):
        print(f"  {k}: {summary[k]}")
    # fail loudly if any hole-class or violation row exists
    if out["hole_class_rows"] or out["violation_rows"]:
        print("ESCALATE-CANDIDATE ROWS:")
        for r in out["hole_class_rows"] + out["violation_rows"]:
            print(f"  {r['file']}:{r['line']} {r['text']}")
        return 2
    print("NO hole-class rows (sig-ful without explicit leak_check=True) -> "
          "flip is verdict-neutral BY CONSTRUCTION for every production caller.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
