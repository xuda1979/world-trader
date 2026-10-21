#!/usr/bin/env python3
# TDD for launch_all.sh MAX_CONCURRENT cap (standup 2026-09-07 02:4x).
# REAL FAILURE: round-2 wave launched 19 concurrent sessions against the GLM
# gateway's ~1-2 concurrent-slot cap -> 18/20 agents spent 01:51-02:40 in pure
# 429 backoff with ZERO round-2 output, and all would exhaust MAXTRY=8 by ~03:05.
# A concurrency-capped fleet keeper lets agents actually complete instead of
# starving each other.
#   C1. live wrappers >= MAX_CONCURRENT -> launch NOTHING more (defer)
#   C2. live wrappers <  MAX_CONCURRENT -> launch (cap not reached)
#   C3. MAX_CONCURRENT unset -> unlimited (legacy behavior preserved)
#   C4. deferred roles are logged as "defer ... (fleet at cap"
# Run: python3 campaign/agents/chief/coord/test_launch_all_cap.py
import os, subprocess, sys, tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'launch_all.sh')

def make_tree(n_ready=3):
    tdir = tempfile.mkdtemp(prefix='launchcap_tdd_')
    coord = os.path.join(tdir, 'coord')
    os.makedirs(os.path.join(coord, 'logs'))
    roles = ['R%d_READY' % i for i in range(n_ready)]
    for a in roles:
        os.makedirs(os.path.join(coord, a))
        with open(os.path.join(coord, a, 'FINDINGS.md'), 'w') as f:
            f.write('old round\n')
    with open(os.path.join(coord, 'AGENTS.txt'), 'w') as f:
        f.write('\n'.join(roles) + '\n')
    stub = os.path.join(coord, 'launch_agent_chief.sh')
    with open(stub, 'w') as f:
        f.write('#!/bin/sh\necho "STUB-LAUNCHED $1 $2" >> "$ROOT/logs/stub_invocations.txt"\n')
    os.chmod(stub, 0o755)
    proc = os.path.join(tdir, 'proc_check.sh')
    with open(proc, 'w') as f:
        f.write('#!/bin/sh\nexit 1\n')
    os.chmod(proc, 0o755)
    cnt = os.path.join(tdir, 'count.txt')
    open(cnt, 'w').write('0\n')
    count_check = os.path.join(tdir, 'count_check.sh')
    with open(count_check, 'w') as f:
        f.write('#!/bin/sh\ncat "%s"\n' % cnt)
    os.chmod(count_check, 0o755)
    return coord, count_check

def run(coord, count_check, max_concurrent):
    env = dict(os.environ)
    env['ROOT'] = coord
    env['ROUND'] = '2'
    env['PROC_CHECK'] = os.path.join(os.path.dirname(count_check), 'proc_check.sh')
    env['COUNT_CHECK'] = count_check
    env['STAGGER'] = '0'
    if max_concurrent is not None:
        env['MAX_CONCURRENT'] = str(max_concurrent)
    else:
        env.pop('MAX_CONCURRENT', None)
    return subprocess.run(['bash', SCRIPT], env=env, capture_output=True, text=True, timeout=120)

def launched(coord):
    p = os.path.join(coord, 'logs', 'stub_invocations.txt')
    if not os.path.exists(p):
        return []
    return [l.split()[1] for l in open(p).read().splitlines() if l.strip()]

def main():
    fails = []
    # C1: 5 live wrappers, cap 3 -> defer everything, log it
    # BUG FIXED 2026-09-07 03:1x (found via bash -x trace in standup): make_tree
    # returns count_check.sh, but callers wrote the count INTO it, clobbering the
    # stub with e.g. "5". Executing "5" failed -> live_count empty -> guard failed
    # OPEN and C2/C3 "passed" by the same accident. Count now goes to count.txt.
    coord, cnt = make_tree(3)
    open(os.path.join(os.path.dirname(cnt), 'count.txt'), 'w').write('5\n')
    r = run(coord, cnt, 3)
    got = launched(coord)
    if got != []:
        fails.append('C1: fleet at cap must launch NOTHING, got %r' % (got,))
    llog = open(os.path.join(coord, 'logs', 'launcher.log')).read()
    if 'defer' not in llog:
        fails.append('C4: deferred roles must be logged as defer, launcher.log=%r' % llog[-200:])

    # C2: 1 live wrapper, cap 3 -> all three launch
    coord2, cnt2 = make_tree(3)
    open(os.path.join(os.path.dirname(cnt2), 'count.txt'), 'w').write('1\n')
    run(coord2, cnt2, 3)
    got2 = launched(coord2)
    if len(got2) != 3:
        fails.append('C2: under cap all roles must launch, got %r' % (got2,))

    # C3 (REVISED 2026-09-07 12:1x standup): MAX_CONCURRENT unset -> DEFAULT CAP
    # engages (4), NOT unlimited. Real failure 2026-09-07 08:00-10:30: the round-3
    # wave ran with the cap unset (opt-in), 14 roles fired, ~10 concurrent, and 13
    # agents burned all 8 backoff attempts on 429s with zero round-3 output. A cap
    # that must be remembered every invocation is a cap that is absent exactly when
    # a storm happens. Default = 4 concurrent wrappers; explicit env still overrides.
    coord3, cnt3 = make_tree(3)
    open(os.path.join(os.path.dirname(cnt3), 'count.txt'), 'w').write('99\n')
    run(coord3, cnt3, None)
    got3 = launched(coord3)
    if got3 != []:
        fails.append('C3: unset cap must DEFAULT to 4 (99 live >= 4 -> defer all), got %r' % (got3,))

    # C3b: unset cap, 1 live wrapper -> default cap 4 not reached -> all launch
    coord3b, cnt3b = make_tree(3)
    open(os.path.join(os.path.dirname(cnt3b), 'count.txt'), 'w').write('1\n')
    run(coord3b, cnt3b, None)
    got3b = launched(coord3b)
    if len(got3b) != 3:
        fails.append('C3b: unset cap under default 4 must launch all, got %r' % (got3b,))

    # C5 (fail-closed, TDD 03:1x): COUNT_CHECK output GARBAGE (not an integer).
    # Real trigger: any stub/env corruption that makes live_count emit "" or junk.
    # Old behavior: [ "" -ge 3 ] errors false -> guard silently disabled -> LAUNCH.
    # Fail-closed contract: unparseable count must DEFER, never fail open.
    coord5, cnt5 = make_tree(3)
    open(os.path.join(os.path.dirname(cnt5), 'count.txt'), 'w').write('not-a-number\n')
    run(coord5, cnt5, 3)
    got5 = launched(coord5)
    if got5 != []:
        fails.append('C5: garbage count must DEFER (fail-closed), launched %r' % (got5,))
    llog5 = open(os.path.join(coord5, 'logs', 'launcher.log')).read()
    if 'defer' not in llog5:
        fails.append('C5b: garbage count defer must be logged, launcher.log=%r' % llog5[-200:])

    if fails:
        print('FAIL:')
        for f in fails:
            print('  -', f)
        sys.exit(1)
    print('ALL GREEN: MAX_CONCURRENT cap honored (defer at cap, launch under, unset=default4, defer logged)')

if __name__ == '__main__':
    main()
