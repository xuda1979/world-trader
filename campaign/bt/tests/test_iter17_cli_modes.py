"""Defect cleared 2026-09-13: the builder's `--emit` mode was UNREACHABLE.

`main()` computed `mode = args[0] if args and not args[0].startswith('--') else '--verify'`,
so every long flag -- including `--emit` -- resolved to '--verify'. `--emit` therefore
silently ran the VERIFY path and never wrote anything: a re-emit invoked as documented
(after a sleeve refresh, say) would no-op and leave stale artifacts on disk while printing
a verify table that looks like success. Verified by running
`rawew13v2_build.py --emit` -> printed the verify table, not "emitted".

Fix: an explicit `parse_mode()` (tested here) plus `--emit-candidate NAME`, which writes
`campaign/results/<NAME>_{daily,weights}.csv` and CANNOT touch the champion of record.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "campaign" / "scripts"))

import rawew13v2_build as B  # noqa: E402


def test_emit_mode_is_reachable():
    assert B.parse_mode(["--emit"]) == "--emit"


def test_emit_candidate_mode_and_its_name():
    assert B.parse_mode(["--emit-candidate", "X"]) == "--emit-candidate"


def test_verify_is_the_default_and_explicit():
    assert B.parse_mode([]) == "--verify"
    assert B.parse_mode(["--verify"]) == "--verify"


def test_mode_wins_over_other_flags():
    assert B.parse_mode(["--shrink-d", "0.8", "--gear", "1.6", "--emit"]) == "--emit"
    assert B.parse_mode(["--wf-step", "YS", "--emit-candidate", "RAWEW18"]) == "--emit-candidate"


def test_emit_refuses_to_overwrite_the_champion_from_override_flags():
    """--emit writes the CHAMPION paths unconditionally. Now that --emit is reachable, a
    `--emit --gear 1.75` (the RAWEW17 stray) would silently replace the champion of record
    with a book that breaches the 1.6 cap. Refuse unless --force is explicit."""
    assert B.check_emit_safe(B.SHRINK_D, B.GEAR, None, force=False)[0] is True
    ok, why = B.check_emit_safe(0.80, B.GEAR, None, force=False)
    assert ok is False and "shrink_d" in why
    ok, why = B.check_emit_safe(B.SHRINK_D, 1.75, None, force=False)
    assert ok is False and "gear" in why
    # the REJECTED walk-forward book must not be emitted over the champion either
    ok, why = B.check_emit_safe(B.SHRINK_D, B.GEAR, B.WF_STEP_TRIED, force=False)
    assert ok is False and "wf_step" in why
    assert B.check_emit_safe(B.SHRINK_D, 1.75, None, force=True)[0] is True
