#!/usr/bin/env python3
# TDD lock for launch_all.sh idempotency guards (coordinator standup 2026-09-07).
# The shipped script (guards added after two real failures) must, against a SANDBOX
# root with a stub launch_agent_chief.sh that records invocations:
#   P1. skip a role whose per-role FINDINGS.md ends with "ROUND <round> DONE"
#   P1c. skip the 13 combined roles when the space-joined COMBINED dir FINDINGS.md
#        ends with the marker (per-role file never exists for them; a per-role-only
#        check relaunched 3 completed roles at 01:17 on 2026-09-07)
#   P2. skip a role with a live launcher (PROC_CHECK seam rc 0)
#   P3. launch roles with neither marker nor live proc
#   P4. ROUND env changes the marker that counts as done
#   P5. single-instance lock held -> a second instance launches NOTHING (real
#       failure 01:17: a launcher running while guards were rewritten misfired and
#       re-ran 3 DONE combined roles)
#   P6. stale lock (older than LOCK_TTL_SECS) -> instance takes over (else a
#       kill -9'd launcher wedges the fleet forever)
# Run: python3 campaign/agents/chief/coord/test_launch_all_plan.py
import os, subprocess, sys, tempfile, shutil, time

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'launch_all.sh')
COMBINED = ("HUNT_CRYPTO2 HUNT_CMDT2 HUNT_MACRO2 HUNT_FXCARRY2 HUNT_SECTOR2 "
            "HUNT_CREDIT2 CAMP_SHORT CAMP_BORROW CAMP_COST DATA_FREDMORE "
            "DATA_ETF_MORE AUDIT_FWBUGS AUDIT_RECON")

def make_tree(roles_done_r1=(), combined_done=True):
    tdir = tempfile.mkdtemp(prefix='launchall_tdd_')
    coord = os.path.join(tdir, 'coord')
    os.makedirs(os.path.join(coord, 'logs'))
    for a in ('HUNT_COT2', 'HUNT_INTERNATIONAL2', 'Z_READY'):
        os.makedirs(os.path.join(coord, a), exist_ok=True)
    for a in roles_done_r1:
        with open(os.path.join(coord, a, 'FINDINGS.md'), 'w') as f:
            f.write('work\n\nROUND 1 DONE\n')
    if combined_done:
        os.makedirs(os.path.join(coord, COMBINED), exist_ok=True)
        with open(os.path.join(coord, COMBINED, 'FINDINGS.md'), 'w') as f:
            f.write('combined round-1 record\n\nROUND 1 DONE\n')
    with open(os.path.join(coord, 'AGENTS.txt'), 'w') as f:
        f.write('HUNT_COT2\nHUNT_INTERNATIONAL2\n' + COMBINED.replace(' ', '\n') + '\nZ_READY\n')
    # stub launcher: records "launched <agent> <round>" and exits 0 (script backgrounds nothing)
    stub = os.path.join(coord, 'launch_agent_chief.sh')
    with open(stub, 'w') as f:
        f.write('#!/bin/sh\necho "STUB-LAUNCHED $1 $2" >> "$ROOT/logs/stub_invocations.txt"\n')
    os.chmod(stub, 0o755)
    # PROC_CHECK stub: rc 0 (alive) for names in the alive-file, rc 1 otherwise
    alive_file = os.path.join(tdir, 'alive.txt')
    open(alive_file, 'w').close()
    proc = os.path.join(tdir, 'proc_check.sh')
    with open(proc, 'w') as f:
        f.write('#!/bin/sh\ngrep -qx "$1" "$0.alive" || exit 1\n')
        # simpler: check membership
    with open(proc, 'w') as f:
        f.write('#!/bin/sh\n')
        f.write(f'grep -qxF "$1" "{alive_file}"\n')
    os.chmod(proc, 0o755)
    return coord, alive_file

def run(coord, round_n, alive_file, alive=()):
    with open(alive_file, 'w') as f:
        for a in alive:
            f.write(a + '\n')
    env = dict(os.environ)
    env['ROOT'] = coord
    env['ROUND'] = str(round_n)
    env['PROC_CHECK'] = os.path.join(os.path.dirname(alive_file), 'proc_check.sh')
    env['STAGGER'] = '0'
    return subprocess.run(['bash', SCRIPT], env=env, capture_output=True, text=True, timeout=120)

def launched(coord):
    p = os.path.join(coord, 'logs', 'stub_invocations.txt')
    if not os.path.exists(p):
        return []
    return [line.split()[1] for line in open(p).read().splitlines() if line.strip()]

def main():
    fails = []
    # Case A: combined DONE + per-role DONE, nobody alive, round 1 -> only Z_READY launches
    coord, alive_file = make_tree(roles_done_r1=('HUNT_COT2', 'HUNT_INTERNATIONAL2'))
    r = run(coord, 1, alive_file)
    got = launched(coord)
    if got != ['Z_READY']:
        fails.append(f'P1/P1c/P3: expected exactly [Z_READY], got {got}')
    # Case B: same tree, Z_READY alive -> nothing launches
    coord2, alive_file2 = make_tree(roles_done_r1=('HUNT_COT2', 'HUNT_INTERNATIONAL2'))
    r = run(coord2, 1, alive_file2, alive=('Z_READY',))
    got2 = launched(coord2)
    if got2 != []:
        fails.append(f'P2: live Z_READY must be skipped, got {got2}')
    # Case C: round 2 -> combined+per-role round-1 markers no longer block
    coord3, alive_file3 = make_tree(roles_done_r1=('HUNT_COT2', 'HUNT_INTERNATIONAL2'))
    r = run(coord3, 2, alive_file3)
    got3 = launched(coord3)
    if 'HUNT_COT2' not in got3 or 'HUNT_CRYPTO2' not in got3 or 'Z_READY' not in got3:
        fails.append(f'P4: round 2 must re-arm all roles, got {got3}')
    # Case D: combined marker ABSENT at round 1 -> combined roles launch (fail-open to launch
    # is correct: missing evidence means not DONE)
    coord4, alive_file4 = make_tree(roles_done_r1=('HUNT_COT2', 'HUNT_INTERNATIONAL2'), combined_done=False)
    r = run(coord4, 1, alive_file4)
    got4 = launched(coord4)
    if 'HUNT_CMDT2' not in got4:
        fails.append(f'P1c-invert: combined marker absent -> combined roles must launch, got {got4}')

    # Case E: single-instance lock held by a live instance -> second instance must
    # launch NOTHING (real failure 2026-09-07 01:17: a launcher running while the
    # guard code was being rewritten misfired and re-ran 3 DONE combined roles;
    # concurrent coordinator sessions make a second concurrent instance likely).
    coord5, alive_file5 = make_tree(roles_done_r1=('HUNT_COT2', 'HUNT_INTERNATIONAL2'))
    lock5 = os.path.join(coord5, 'logs', '.launch_all.lock')
    os.makedirs(lock5)
    with open(os.path.join(lock5, 'pid'), 'w') as f:
        f.write('999999\n')
    with open(os.path.join(lock5, 'ts'), 'w') as f:
        f.write(str(int(time.time())) + '\n')
    run(coord5, 1, alive_file5)
    got5 = launched(coord5)
    if got5 != []:
        fails.append('P5: lock held -> second instance must launch NOTHING, got %r' % (got5,))

    # Case F: stale lock (older than LOCK_TTL_SECS) -> instance proceeds (fail-open
    # to work, otherwise a kill -9'd launcher wedges the fleet forever).
    coord6, alive_file6 = make_tree(roles_done_r1=('HUNT_COT2', 'HUNT_INTERNATIONAL2'))
    lock6 = os.path.join(coord6, 'logs', '.launch_all.lock')
    os.makedirs(lock6)
    with open(os.path.join(lock6, 'pid'), 'w') as f:
        f.write('999999\n')
    with open(os.path.join(lock6, 'ts'), 'w') as f:
        f.write(str(int(time.time()) - 7200) + '\n')
    env6 = dict(os.environ)
    env6['ROOT'] = coord6
    env6['ROUND'] = '1'
    env6['PROC_CHECK'] = os.path.join(os.path.dirname(alive_file6), 'proc_check.sh')
    env6['STAGGER'] = '0'
    env6['LOCK_TTL_SECS'] = '3600'
    subprocess.run(['bash', SCRIPT], env=env6, capture_output=True, text=True, timeout=120)
    got6 = launched(coord6)
    if 'Z_READY' not in got6:
        fails.append('P6: stale lock must be taken over, got %r' % (got6,))

    if fails:
        print('FAIL:')
        for f in fails:
            print('  -', f)
        sys.exit(1)
    print('ALL GREEN: launch_all.sh idempotency guards honored (per-role+combined done markers, live-guard, ROUND re-arm)')

if __name__ == '__main__':
    main()
