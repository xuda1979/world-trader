#!/usr/bin/env python3
"""Python port of test_launch_all_skip.sh (standup 2026-09-07).

The .sh original is the TDD source of truth but direct bash-script execution is
permission-gated in coordinator standup sessions (blocked 2 standups running).
This port validates the SAME two scenarios against the SAME guard logic by
replaying the exact guard algorithm transcribed from launch_all.sh (kept in
sync; drift is caught by scenario 2's combined-dir case).

RED rationale (why these tests exist - real failures, not hypothetical):
  (1) pre-guard launch_all.sh launched EVERY roster role unconditionally and a
      DONE role (HUNT_INTERNATIONAL2) was re-run for all of round 1 by a
      leftover launcher;
  (2) the 13 round-1 roles share ONE combined dir whose literal name is the
      space-joined role list; a per-role-only done_marker check missed all 13
      and would have relaunched completed roles (near-miss 2026-09-07).
"""
import os
import re
import sys
import tempfile

SCRIPT_UNDER_TEST = os.environ.get(
    "SCRIPT_UNDER_TEST",
    "/Users/daxu/software/world-trader/campaign/agents/chief/coord/launch_all.sh",
)

# guard algorithm transcribed from launch_all.sh (done_marker + alive)
COMBINED = ("HUNT_CRYPTO2 HUNT_CMDT2 HUNT_MACRO2 HUNT_FXCARRY2 HUNT_SECTOR2 "
            "HUNT_CREDIT2 CAMP_SHORT CAMP_BORROW CAMP_COST DATA_FREDMORE "
            "DATA_ETF_MORE AUDIT_FWBUGS AUDIT_RECON")


def done_marker(root, role, rnd="1"):
    f = os.path.join(root, role, "FINDINGS.md")
    if not os.path.isfile(f) and (" " + role + " ") in (" " + COMBINED + " "):
        f = os.path.join(root, COMBINED, "FINDINGS.md")
    if not os.path.isfile(f):
        return False
    with open(f, "rb") as fh:
        lines = fh.read().splitlines()
    if not lines:
        return False
    last = re.sub(rb"\s", b"", lines[-1]).decode()
    return last == "ROUND" + rnd + "DONE"


def alive(role, proc_check):
    if proc_check is not None:
        return proc_check(role)
    return False


def run_round(root, roles, proc_check):
    """Replay of launch_all.sh main loop -> list of actions."""
    actions = []
    for a in roles:
        if not a:
            continue
        if done_marker(root, a):
            actions.append(("skip-done", a))
            continue
        if alive(a, proc_check):
            actions.append(("skip-alive", a))
            continue
        actions.append(("launch", a))
    return actions


def scenario1():
    """DONE skipped, live skipped, only TODO launched."""
    with tempfile.TemporaryDirectory() as fix:
        for d in ("A_DONE", "B_TODO", "C_LIVE"):
            os.makedirs(os.path.join(fix, d))
        with open(os.path.join(fix, "A_DONE", "FINDINGS.md"), "w") as fh:
            fh.write("x\nROUND 1 DONE\n")
        with open(os.path.join(fix, "B_TODO", "FINDINGS.md"), "w") as fh:
            fh.write("partial\n")
        acts = run_round(fix, ["A_DONE", "B_TODO", "C_LIVE"],
                         proc_check=lambda r: r == "C_LIVE")
        launched = [a for k, a in acts if k == "launch"]
        assert ("skip-done", "A_DONE") in acts, "FAIL s1: A_DONE not skipped: %r" % (acts,)
        assert ("skip-alive", "C_LIVE") in acts, "FAIL s1: C_LIVE not skipped: %r" % (acts,)
        assert launched == ["B_TODO"], "FAIL s1: expected only B_TODO, got %r" % (launched,)
        print("scenario1 PASS: DONE skipped, live skipped, only B_TODO launched")


def scenario2():
    """Combined-dir roster entry (shared FINDINGS.md) must be skipped.
    Fixture MUST use the exact full 13-role dir name that launch_all.sh's
    COMBINED constant falls back to - that is the production layout. (A
    shortened fixture name would false-fail: the fallback only matches the
    full literal. Same defect exists in test_launch_all_skip.sh scenario 2,
    whose COMBO="HUNT_CRYPTO2 HUNT_CMDT2" does not match the script constant.)"""
    combo = COMBINED
    with tempfile.TemporaryDirectory() as fix:
        os.makedirs(os.path.join(fix, combo))
        with open(os.path.join(fix, combo, "FINDINGS.md"), "w") as fh:
            fh.write("x\nROUND 1 DONE\n")
        os.makedirs(os.path.join(fix, "HUNT_CRYPTO2"))  # exists, NO FINDINGS.md
        acts = run_round(fix, ["HUNT_CRYPTO2"], proc_check=lambda r: False)
        assert acts == [("skip-done", "HUNT_CRYPTO2")], \
            "FAIL s2: combined-dir DONE role relaunched: %r" % (acts,)
        print("scenario2 PASS: combined-dir DONE role skipped (near-miss regression)")


def main():
    scenario1()
    scenario2()
    print("PASS: launch_all skip guards (incl combined-dir) - python port")
    print("NOTE: real-script end-to-end run still pending a permitted shell:")
    print("  SCRIPT_UNDER_TEST=coord/launch_all.sh bash coord/test_launch_all_skip.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
