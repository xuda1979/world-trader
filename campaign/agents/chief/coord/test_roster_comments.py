#!/usr/bin/env python3
# TDD for AGENTS.txt comment-line parsing (standup 2026-09-07 17:5x).
# REAL FAILURE: CIO appended a comment line
#   "# +HUNT_TIMESFM (CIO add 2026-09-07): Google TimesFM 3.0 forecasting sleeves"
# to AGENTS.txt at 17:44 (after the R4 wave launch). Every roster consumer reads
# the file line-by-line and skips only EMPTY lines; fleet_keeper.py is worse -
# whole-file .split() explodes the comment into ~8 bogus "agents". The next
# freed fleet slot would launch a claude proc whose agent name is the entire
# comment string (launch_agent_chief.sh <garbage> 4, --dangerously-skip-
# permissions), and fleet_keeper's alive()/done() would pgrep that garbage.
# Contract:
#   R1. launch_all.sh: a comment line launches NOTHING (no stub invocation,
#       no launcher.log "launch" for it); the real role after it still launches.
#   R2. fleet_keeper.py: roster() parses line-wise, drops blank+comment lines,
#       returns exactly the real role names.
#   R3. monitor_v4.sh: ONE_SHOT snapshot prints no comment-derived row.
#   R4. standup.sh: same, with ROOT overridable for sandboxing.
# Run: python3 campaign/agents/chief/coord/test_roster_comments.py
import os
import re
import subprocess
import sys
import tempfile

COORD = os.path.dirname(os.path.abspath(__file__))
COMMENT = ("# +HUNT_TIMESFM (CIO add 2026-09-07): "
           "Google TimesFM 3.0 forecasting sleeves")


def make_tree():
    tdir = tempfile.mkdtemp(prefix='roster_tdd_')
    coord = os.path.join(tdir, 'coord')
    os.makedirs(os.path.join(coord, 'logs'))
    os.makedirs(os.path.join(coord, 'Z_READY'))
    with open(os.path.join(coord, 'Z_READY', 'FINDINGS.md'), 'w') as f:
        f.write('old round\n')
    with open(os.path.join(coord, 'AGENTS.txt'), 'w') as f:
        f.write(COMMENT + '\n')
        f.write('\n')
        f.write('Z_READY\n')
    stub = os.path.join(coord, 'launch_agent_chief.sh')
    with open(stub, 'w') as f:
        f.write('#!/bin/sh\necho "STUB-LAUNCHED $1 $2" '
                '>> "$ROOT/logs/stub_invocations.txt"\n')
    os.chmod(stub, 0o755)
    proc = os.path.join(tdir, 'proc_check.sh')
    with open(proc, 'w') as f:
        f.write('#!/bin/sh\nexit 1\n')
    os.chmod(proc, 0o755)
    cnt = os.path.join(tdir, 'count_check.sh')
    with open(cnt, 'w') as f:
        f.write('#!/bin/sh\necho 0\n')
    os.chmod(cnt, 0o755)
    return coord


def run_launch_all(coord):
    env = dict(os.environ)
    env['ROOT'] = coord
    env['ROUND'] = '4'
    env['PROC_CHECK'] = os.path.join(os.path.dirname(coord), 'proc_check.sh')
    env['COUNT_CHECK'] = os.path.join(os.path.dirname(coord), 'count_check.sh')
    env['STAGGER'] = '0'
    return subprocess.run(['bash', os.path.join(COORD, 'launch_all.sh')],
                          env=env, capture_output=True, text=True, timeout=120)


def launched(coord):
    p = os.path.join(coord, 'logs', 'stub_invocations.txt')
    if not os.path.exists(p):
        return []
    return [l.split()[1] for l in open(p).read().splitlines() if l.strip()]


def r1_launch_all():
    coord = make_tree()
    r = run_launch_all(coord)
    got = launched(coord)
    assert got == ['Z_READY'], \
        'R1 FAILED: comment line must launch nothing, real role must still ' \
        'launch; got %r (stderr=%r)' % (got, r.stderr[-300:])
    llog = open(os.path.join(coord, 'logs', 'launcher.log')).read()
    assert 'launch ' + COMMENT not in llog, \
        'R1 FAILED: comment text logged as a launch'
    print('R1 ok: comment line launches nothing; real role after it launches')


def r2_keeper_roster():
    src = open(os.path.join(COORD, 'fleet_keeper.py')).read()
    m = re.search(r'^def roster\(.*?(?=^def |^while )', src,
                  re.M | re.S)
    assert m, 'R2 FAILED: fleet_keeper.py has no roster() function'
    # seed free vars referenced by the trailing AGENTS = roster(...) line that
    # the extraction window legitimately includes
    ns = {'os': os, 'ROOT': COORD}
    exec(compile(m.group(0), 'fleet_keeper.roster', 'exec'), ns)
    roster = ns['roster']
    fd, path = tempfile.mkstemp(suffix='.txt')
    with os.fdopen(fd, 'w') as f:
        f.write(COMMENT + '\n\n   \nZ_READY\nHUNT_COT2\n')
    try:
        got = roster(path)
    finally:
        os.unlink(path)
    assert got == ['Z_READY', 'HUNT_COT2'], \
        'R2 FAILED: roster parse must drop blank+comment lines, got %r' % (got,)
    # production file: every entry must be a clean role token (no spaces/#)
    prod = roster(os.path.join(COORD, 'AGENTS.txt'))
    bad = [a for a in prod if ' ' in a or a.startswith('#') or not a]
    assert not bad, 'R2 FAILED: production roster has junk entries: %r' % (bad,)
    assert 'HUNT_TIMESFM' in prod, \
        'R2 FAILED: CIO-added HUNT_TIMESFM missing from production roster'
    print('R2 ok: fleet_keeper roster() line-wise, comments dropped, '
          '%d production roles' % len(prod))


def r3_monitor():
    coord = make_tree()
    env = dict(os.environ)
    env['ROOT'] = coord
    env['ROUND'] = '4'
    env['ONE_SHOT'] = '1'
    r = subprocess.run(['bash', os.path.join(COORD, 'monitor_v4.sh')],
                       env=env, capture_output=True, text=True, timeout=120)
    out = r.stdout
    assert 'HUNT_TIMESFM 3.0' not in out and '+HUNT_TIMESFM' not in out, \
        'R3 FAILED: monitor printed a comment-derived row:\n%s' % out
    assert re.search(r'Z_READY\s+(DONE|RUNNING|BLOCKED)', out), \
        'R3 FAILED: real role row missing from monitor output:\n%s' % out
    print('R3 ok: monitor_v4.sh prints no comment-derived row')


def r4_standup():
    coord = make_tree()
    env = dict(os.environ)
    env['ROOT'] = coord
    r = subprocess.run(['bash', os.path.join(COORD, 'standup.sh')],
                       env=env, capture_output=True, text=True, timeout=120)
    out = r.stdout
    assert 'HUNT_TIMESFM 3.0' not in out and '+HUNT_TIMESFM' not in out, \
        'R4 FAILED: standup printed a comment-derived row:\n%s' % out
    assert 'Z_READY' in out, \
        'R4 FAILED: real role row missing from standup output:\n%s' % out
    print('R4 ok: standup.sh prints no comment-derived row (ROOT overridable)')


def main():
    failures = []
    for name, fn in (('R1', r1_launch_all), ('R2', r2_keeper_roster),
                     ('R3', r3_monitor), ('R4', r4_standup)):
        try:
            fn()
        except AssertionError as e:
            failures.append(str(e))
        except Exception as e:  # noqa: BLE001 - report and continue
            failures.append('%s errored: %r' % (name, e))
    if failures:
        print('FAIL (RED):')
        for f in failures:
            print('  -', f)
        sys.exit(1)
    print('ALL GREEN: AGENTS.txt comment lines ignored by every roster consumer')


if __name__ == '__main__':
    main()
