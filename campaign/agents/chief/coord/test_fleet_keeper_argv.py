#!/usr/bin/env python3
# TDD for fleet_keeper.py argv handling (standup 2026-09-08 09:3x).
# REAL FAILURE 2026-09-08 09:00:41: a session ran `python3 fleet_keeper.py status`
# expecting a status report; fleet_keeper.py has NO argv handling, so argv was
# ignored and a SECOND keeper loop started with ROUND defaulting to '4' (stale).
# Its launch_all pass re-launched HUNT_COT2 (DONE R5) as round 4; the marker flip
# hid R5 DONE from the keeper and cost a duplicate R5 relaunch (pass 14, 09:20:53).
# Coordination must fail CLOSED on unexpected argv:
#   A1. `fleet_keeper.py status` reports fleet state and EXITS 0 - never loops
#   A2. `fleet_keeper.py <unknown>` exits non-zero - never loops
#   A3. no args -> loop path; unset ROUND defaults to fleet-CURRENT round (7;
#       bumped 5->7 at the 18:30 standup 2026-09-08 as r6 drained, alongside the
#       fleet_keeper.py ROUND_DEFAULT bump - keep the two pins in lockstep)
#   A4. ROUND env wins over ROUND_DEFAULT
# Run: python3 campaign/agents/chief/coord/test_fleet_keeper_argv.py
import os
import sys

COORD = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(COORD, 'fleet_keeper.py')).read()


def make_ns():
    lines = []
    for line in src.splitlines():
        if line.startswith('if __name__'):
            break
        lines.append(line)
    body = chr(10).join(lines)
    ns = dict()
    exec(compile(body, 'fleet_keeper.py', 'exec'), ns)
    return ns


class LoopStarted(AssertionError):
    pass


def main():
    failures = []
    # A0 FIRST, before ANY exec: against the old guard-less source, exec'ing the
    # module body would START THE REAL KEEPER LOOP (this is the incident itself).
    # Static checks must therefore gate the exec, and a failed A0 must exit
    # before make_ns() is ever called.
    if 'if __name__' not in src:
        print('A0 FAILED: no __main__ guard in fleet_keeper.py - '
              'exec would start the real loop; refusing to exec. RED.')
        sys.exit(1)
    if 'sys.argv' not in src:
        print('A0 FAILED: fleet_keeper.py never reads sys.argv - '
              'any argv silently ignored (09:00:41 incident class). RED.')
        sys.exit(1)
    if 'def main(' not in src:
        print('A0 FAILED: fleet_keeper.py has no main() entrypoint - '
              'nothing to invoke safely. RED.')
        sys.exit(1)
    print('A0 ok: __main__ guard + sys.argv + main() all present')
    ns = make_ns()

    def fail_loop(round_val=None):
        raise LoopStarted('keeper LOOP started under non-loop argv')

    if 'main' not in ns:
        failures.append('A1 FAILED: no main() in fleet_keeper.py')
    else:
        try:
            ns['run_keeper_loop'] = fail_loop
            rc = ns['main'](['status'])
            if rc != 0:
                failures.append('A1 FAILED: status should exit 0, got %r' % rc)
            else:
                print('A1 ok: status reports and exits 0 without looping')
        except LoopStarted as exc:
            failures.append('A1 FAILED: %s' % exc)

    ns['run_keeper_loop'] = fail_loop
    try:
        rc = ns['main'](['bananas'])
        if rc == 0:
            failures.append('A2 FAILED: unknown argv exited 0')
        else:
            print('A2 ok: unknown argv exits non-zero (%r)' % rc)
    except LoopStarted as exc:
        failures.append('A2 FAILED: %s' % exc)

    captured = dict()
    def fake_loop(round_val):
        captured['round'] = round_val
    ns['run_keeper_loop'] = fake_loop
    backup = os.environ.pop('ROUND', None)
    try:
        rc = ns['main']([])
        if rc != 0:
            failures.append('A3 FAILED: bare invocation should exit 0, got %r' % rc)
        elif captured.get('round') != '7':
            failures.append('A3 FAILED: bare keeper ROUND=%r (expected 7)'
                            % captured.get('round'))
        else:
            print('A3 ok: bare keeper defaults to fleet-current ROUND 7')
    finally:
        if backup is not None:
            os.environ['ROUND'] = backup

    os.environ['ROUND'] = '6'
    captured.clear()
    try:
        rc = ns['main']([])
        if captured.get('round') != '6':
            failures.append('A4 FAILED: ROUND=6 env not honored, got %r'
                            % captured.get('round'))
        else:
            print('A4 ok: ROUND env wins over ROUND_DEFAULT')
    finally:
        os.environ.pop('ROUND', None)

    if failures:
        print(chr(10).join(failures))
        sys.exit(1)
    print('ALL PASS')


if __name__ == '__main__':
    main()