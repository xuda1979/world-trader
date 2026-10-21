#!/usr/bin/env python3
# TDD for fleet_keeper.py COMBINED fallback (standup 2026-09-07 14:2x).
# REAL RISK: done() falls back to a single stray dir literally named with the
# concatenation of 13 agent names (created by a shell cwd-reset mishap on
# 2026-09-06 22:00). Any agent appending "ROUND 3 DONE" to that file would make
# done() true for EVERY COMBINED agent lacking its own FINDINGS.md -> keeper
# silently never launches them. Coordination must fail CLOSED: an agent without
# its own FINDINGS.md is pending, regardless of any shared/stray file.
#   C1. agent without own FINDINGS.md + stray COMBINED file ending ROUND 3 DONE
#       -> done() is False (must launch)
#   C2. agent without own FINDINGS.md, no stray file -> done() is False (unchanged)
#   C3. agent with own FINDINGS.md ending ROUND 3 DONE -> done() is True (unchanged)
# Run: python3 campaign/agents/chief/coord/test_fleet_keeper_combined.py
import os
import shutil
import sys
import tempfile

COORD = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(COORD, 'fleet_keeper.py')).read()


def make_done(tmp_coord, combined_dir_name=''):
    """Return a done(a, rnd) bound to a temp coord tree, via targeted exec."""
    lines = []
    keep = False
    for line in src.splitlines():
        if line.startswith('def done('):
            keep = True
        elif line.startswith('def '):
            keep = False
        if keep:
            lines.append(line)
    body = '\n'.join(lines)
    body = body.replace(
        "ROOT = '/Users/daxu/software/world-trader/campaign/agents/chief/coord'",
        "ROOT = %r" % tmp_coord)
    body = body.replace(
        'COMBINED = "HUNT_CRYPTO2 HUNT_CMDT2 HUNT_MACRO2 HUNT_FXCARRY2 HUNT_SECTOR2 '
        'HUNT_CREDIT2 CAMP_SHORT CAMP_BORROW CAMP_COST DATA_FREDMORE DATA_ETF_MORE '
        'AUDIT_FWBUGS AUDIT_RECON"',
        'COMBINED = %r' % combined_dir_name)
    ns = {'os': os, 'ROOT': tmp_coord, 'COMBINED': combined_dir_name}
    exec(compile(body, 'fleet_keeper.done', 'exec'), ns)
    return ns['done']


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(text)


def main():
    COMBINED = ('HUNT_CRYPTO2 HUNT_CMDT2 HUNT_MACRO2 HUNT_FXCARRY2 HUNT_SECTOR2 '
                'HUNT_CREDIT2 CAMP_SHORT CAMP_BORROW CAMP_COST DATA_FREDMORE '
                'DATA_ETF_MORE AUDIT_FWBUGS AUDIT_RECON')
    failures = []
    # C1: stray COMBINED dir says ROUND 3 DONE; agent has NO own FINDINGS.md
    tdir = tempfile.mkdtemp(prefix='keeper_c1_')
    write(os.path.join(tdir, COMBINED.replace(' ', ' '), 'FINDINGS.md'),
          'x\nROUND 3 DONE\n')
    done = make_done(tdir, COMBINED)
    if done('AUDIT_FWBUGS', '3') is not False:
        failures.append('C1 FAILED: stray COMBINED ROUND 3 DONE marks a '
                        'FINDINGS-less agent done (fail-open)')
    else:
        print('C1 ok: stray COMBINED file cannot satisfy a missing FINDINGS.md')
    shutil.rmtree(tdir, ignore_errors=True)
    # C2: no stray file, no own file -> pending
    tdir2 = tempfile.mkdtemp(prefix='keeper_c2_')
    if make_done(tdir2, COMBINED)('AUDIT_FWBUGS', '3') is not False:
        failures.append('C2 FAILED: missing FINDINGS.md reported done')
    else:
        print('C2 ok: missing FINDINGS.md -> pending')
    shutil.rmtree(tdir2, ignore_errors=True)
    # C3: own FINDINGS.md ending ROUND 3 DONE -> done (behavior preserved)
    tdir3 = tempfile.mkdtemp(prefix='keeper_c3_')
    write(os.path.join(tdir3, 'AUDIT_FWBUGS', 'FINDINGS.md'),
          'work\nROUND 3 DONE\n')
    if make_done(tdir3, COMBINED)('AUDIT_FWBUGS', '3') is not True:
        failures.append('C3 FAILED: own ROUND 3 DONE not recognized')
    else:
        print('C3 ok: own FINDINGS.md ROUND 3 DONE -> done')
    shutil.rmtree(tdir3, ignore_errors=True)
    if failures:
        print('\n'.join(failures))
        sys.exit(1)
    print('ALL PASS')


if __name__ == '__main__':
    main()
