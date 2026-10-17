#!/usr/bin/env python3
"""Regression tests for HUNT_H1_TAILFACTOR work_r1/r1_engine.py.

Proves the engine's fail-closed protocol machinery BEFORE the real panel
matures (same rationale as the engine's synthetic fixtures):
  1. charter pin guard: sealed snapshot must remain a byte-identical PREFIX of
     the live panel file — append-only accrual allowed, any mutation of sealed
     rows is PROTOCOL-VIOLATION and blocks evaluation;
  2. span guard: sub-minimum panels PROTOCOL-HOLD, no gate evaluation;
  3. synthetic end-to-end determinism: consecutive runs byte-identical;
  4. output separation: synthetic runs can never clobber the real artifact.

Run: python3 test_r1_engine.py   (from work_r1/; exit 0 iff all pass)
"""
import json
import subprocess
import sys
import tempfile
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "r1_engine.py")
LIVE_PANEL = os.path.normpath(os.path.join(
    HERE, "..", "..", "..", "..", "..", "..",
    "tools", "quant", "data", "cboe_options", "H1_tailfactor_panel.csv"))

sys.path.insert(0, HERE)
import r1_engine as eng  # noqa: E402

PASS = 0
FAIL = 0


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {extra}")


def read_panel_bytes():
    with open(LIVE_PANEL, "rb") as fh:
        return fh.read()


def test_pin_guard():
    print("[1] charter pin guard (prefix immutability, fail-closed)")
    # live panel: must be PIN-OK right now
    g = eng.pin_prefix_guard(LIVE_PANEL)
    check("live panel PIN-OK", g["pin_ok"] and g["verdict"] == "PIN-OK",
          f"got {g['verdict']} sha_ok={g['sha_ok']} prefix_ok={g['prefix_ok']}")

    raw = read_panel_bytes()
    lines = raw.splitlines(keepends=True)

    with tempfile.TemporaryDirectory() as td:
        # (a) append a new accrual date -> still PIN-OK (scheduled accrual)
        p_app = os.path.join(td, "appended.csv")
        with open(p_app, "wb") as fh:
            fh.write(raw + b"2026-10-17,AAPL,0.0061,-0.12,-0.18,-1.0,12.0\n")
        g = eng.pin_prefix_guard(p_app)
        check("appended accrual stays PIN-OK", g["pin_ok"])

        # (b) mutate one digit inside a sealed row -> PROTOCOL-VIOLATION
        p_mut = os.path.join(td, "mutated.csv")
        mut = lines[:]
        l = mut[57]
        mut[57] = l[:-2] + (b"9" if l[-2:-1] != b"9" else b"8") + l[-1:]
        assert mut[57] != l
        with open(p_mut, "wb") as fh:
            fh.write(b"".join(mut))
        g = eng.pin_prefix_guard(p_mut)
        check("sealed-row mutation blocked", not g["pin_ok"]
              and g["verdict"] == "PROTOCOL-VIOLATION")

        # (c) delete a sealed row -> PROTOCOL-VIOLATION
        p_del = os.path.join(td, "deleted.csv")
        with open(p_del, "wb") as fh:
            fh.write(b"".join(lines[:100] + lines[101:]))
        g = eng.pin_prefix_guard(p_del)
        check("sealed-row deletion blocked", not g["pin_ok"]
              and g["verdict"] == "PROTOCOL-VIOLATION")

        # (d) truncation below the sealed size -> PROTOCOL-VIOLATION
        p_trunc = os.path.join(td, "truncated.csv")
        with open(p_trunc, "wb") as fh:
            fh.write(b"".join(lines[:60]))
        g = eng.pin_prefix_guard(p_trunc)
        check("truncated panel blocked", not g["pin_ok"])

        # (e) reorder two sealed rows -> PROTOCOL-VIOLATION
        p_reo = os.path.join(td, "reordered.csv")
        with open(p_reo, "wb") as fh:
            fh.write(b"".join(lines[:50] + [lines[51], lines[50]] + lines[52:]))
        g = eng.pin_prefix_guard(p_reo)
        check("sealed-row reordering blocked", not g["pin_ok"])

        # (f) full-file rewrite with identical bytes -> PIN-OK (idempotence)
        p_same = os.path.join(td, "same.csv")
        with open(p_same, "wb") as fh:
            fh.write(raw)
        g = eng.pin_prefix_guard(p_same)
        check("byte-identical copy PIN-OK", g["pin_ok"])


def run_engine(args, cwd=None):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, cwd=cwd or HERE)


def test_span_guard_hold():
    print("[2] span guard fail-closed on the real (13-date) panel")
    r = run_engine([])
    check("real run exit 0", r.returncode == 0, r.stderr[-300:])
    out = json.load(open(os.path.join(HERE, "r1_results.json")))
    check("real verdict PROTOCOL-HOLD",
          out["final_verdict"] == "PROTOCOL-HOLD" and "hold_reason" in out,
          out.get("final_verdict"))
    check("real run contains no grid", "grid" not in out and "n_grid_cells" not in out)
    check("real pin_check PIN-OK", out["pin_check"]["pin_ok"])


def test_synthetic_determinism_and_separation():
    print("[3] synthetic end-to-end determinism + artifact separation")
    syn_path = os.path.join(HERE, "r1_results_synthetic.json")
    real_path = os.path.join(HERE, "r1_results.json")
    # snapshot current artifacts
    a_syn = open(syn_path, "rb").read()
    a_real = open(real_path, "rb").read()
    r1 = run_engine(["--synthetic"])
    check("synthetic run exit 0", r1.returncode == 0, r1.stderr[-300:])
    b_syn = open(syn_path, "rb").read()
    b_real = open(real_path, "rb").read()
    check("consecutive synthetic runs byte-identical", a_syn == b_syn)
    check("synthetic run did not touch real artifact", a_real == b_real)
    s = json.loads(b_syn)
    check("synthetic span_guard EVALUATE", s["span_guard"]["verdict"] == "EVALUATE")
    check("synthetic has 30 grid cells", s.get("n_grid_cells") == 30)
    check("synthetic primary cell present",
          "a_tail_risk_off|p20_30d|L63|t1.5" in s["grid"])
    # real-mode rerun after synthetic: real artifact unchanged in verdict
    r2 = run_engine([])
    c_real = open(real_path, "rb").read()
    s2 = json.load(open(real_path))
    check("real rerun after synthetic still PROTOCOL-HOLD + PIN-OK",
          s2["final_verdict"] == "PROTOCOL-HOLD"
          and s2["pin_check"]["pin_ok"])
    check("real artifact rewrite is deterministic (same verdict+pin)",
          s2["final_verdict"] == json.loads(b_real)["final_verdict"])


def main():
    test_pin_guard()
    test_span_guard_hold()
    test_synthetic_determinism_and_separation()
    print(f"\n{PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
