#!/usr/bin/env python3
# TDD for fleet_keeper.py exit rule (standup 2026-09-07 17:0x).
# REAL FAILURE 2026-09-07 17:09: 16/20 agents ROUND 3 DONE, 4 alive mid-round
# (429 backoff) -> old pending = [a for a in AGENTS if not done(a) and not alive(a)]
# was EMPTY, so the keeper logged "nothing pending, exiting" and DIED while the
# fleet was still in flight. Any of those 4 agents burning its last retry would
# then strand with no supervisor until a human noticed.
# Coordination must fail CLOSED: the ONLY safe exit is every agent done.
#   K1. agent alive but NOT done -> keeper must NOT exit (and must not launch it)
#   K2. every agent done -> keeper exits (behavior preserved)
#   K3. agent neither alive nor done -> to_launch contains it, keeper stays
# Run: python3 campaign/agents/chief/coord/test_fleet_keeper_supervise.py
import os
import sys

COORD = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(COORD, 'fleet_keeper.py')).read()


def make_plan():
    """Return plan(agents, is_done, is_alive) extracted via targeted exec."""
    lines = []
    keep = False
    for line in src.splitlines():
        if line.startswith('def plan('):
            keep = True
        elif line.startswith(('def ', 'while ')):
            keep = False
        if keep:
            lines.append(line)
    body = '\n'.join(lines)
    ns = {}
    exec(compile(body, 'fleet_keeper.plan', 'exec'), ns)
    return ns['plan']


def main():
    failures = []
    plan = make_plan()
    # K1: 3 done, 1 alive mid-round -> supervise, do not relaunch the live one
    agents = ['A_DONE', 'B_DONE', 'C_DONE', 'D_LIVE']
    exhausted, to_launch = plan(agents, lambda a: a != 'D_LIVE',
                                lambda a: a == 'D_LIVE')
    if exhausted is not False:
        failures.append('K1 FAILED: alive mid-round agent made keeper exit '
                        '(strands it if it dies on its last retry)')
    elif to_launch:
        failures.append('K1 FAILED: keeper would double-launch a LIVE agent: %r'
                        % to_launch)
    else:
        print('K1 ok: alive-but-not-done keeps the keeper supervising, no relaunch')
    # K2: all done -> exit
    exhausted, to_launch = plan(agents, lambda a: True, lambda a: False)
    if exhausted is not True or to_launch:
        failures.append('K2 FAILED: all-done fleet did not produce a clean exit')
    else:
        print('K2 ok: all agents done -> keeper exits')
    # K3: dead mid-round agent -> relaunch it, keep supervising
    exhausted, to_launch = plan(agents, lambda a: a.startswith(('A_', 'B_', 'C_')),
                                lambda a: False)
    if exhausted is not False:
        failures.append('K3 FAILED: dead not-done agent not seen as work to do')
    elif to_launch != ['D_LIVE']:
        failures.append('K3 FAILED: expected to_launch [D_LIVE], got %r' % to_launch)
    else:
        print('K3 ok: dead not-done agent queued for relaunch')
    if failures:
        print('\n'.join(failures))
        sys.exit(1)
    print('ALL PASS')


if __name__ == '__main__':
    main()
