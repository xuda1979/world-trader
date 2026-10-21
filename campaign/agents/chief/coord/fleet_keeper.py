#!/usr/bin/env python3
import subprocess, os, time, re, sys
ROOT = '/Users/daxu/software/world-trader/campaign/agents/chief/coord'
# Fleet-current round; a stale default here re-runs DONE rounds (09:00:41 incident).
ROUND_DEFAULT = '7'
def roster(path):
    """Line-wise roster parse; blank and #-comment lines are annotations, not
    roles. The old whole-file .split() exploded CIO's 2026-09-07 comment line
    into ~8 bogus "agents" that alive()/done() would then pgrep (TDD R2,
    test_roster_comments.py)."""
    return [s.strip() for s in open(path)
            if s.strip() and not s.strip().startswith('#')]


AGENTS = roster(os.path.join(ROOT, 'AGENTS.txt'))
COMBINED = "HUNT_CRYPTO2 HUNT_CMDT2 HUNT_MACRO2 HUNT_FXCARRY2 HUNT_SECTOR2 HUNT_CREDIT2 CAMP_SHORT CAMP_BORROW CAMP_COST DATA_FREDMORE DATA_ETF_MORE AUDIT_FWBUGS AUDIT_RECON"
def done(a, rnd):
    # Fail-closed: only the agent's OWN FINDINGS.md can mark it done. The stray
    # 13-name COMBINED dir (cwd-reset mishap, 2026-09-06) must never satisfy a
    # missing per-agent FINDINGS.md or one agent's DONE would hide all 13.
    f = os.path.join(ROOT, a, 'FINDINGS.md')
    if not os.path.exists(f):
        return False
    try:
        last = open(f, encoding='utf-8', errors='replace').read().strip().splitlines()[-1]
    except Exception:
        return False
    return last.strip() == f'ROUND {rnd} DONE'
def alive(a):
    out = subprocess.run(['pgrep', '-f', f'launch_agent_chief.sh {a} '], capture_output=True, text=True)
    if out.stdout.strip():
        return True
    out = subprocess.run(['pgrep', '-f', f'research agent {a} in the GOAL100'], capture_output=True, text=True)
    return bool(out.stdout.strip())
rnd = os.environ.get('ROUND', ROUND_DEFAULT)  # env-driven; default = fleet-current round
def plan(agents, is_done, is_alive):
    """Classify the fleet for this pass (TDD 2026-09-07 17:0x, real failure 17:09).

    The old exit rule `pending = [a for a in AGENTS if not done and not alive]`
    went EMPTY while agents were merely ALIVE mid-round, so the keeper logged
    "nothing pending, exiting" and died with the fleet in flight - any agent
    that then burned its last 429 retry was stranded unsupervised. Fail closed:
    the ONLY clean exit is every agent done; live-but-not-done keeps us
    supervising (without relaunching it, launch_all.sh skips live agents).
    Returns (exhausted, to_launch)."""
    to_launch = [a for a in agents if not is_done(a) and not is_alive(a)]
    exhausted = all(is_done(a) for a in agents)
    return exhausted, to_launch

def run_keeper_loop(rnd):
    log = open(os.path.join(ROOT, 'logs', 'fleet_keeper.log'), 'a')
    t0 = time.time()
    passes = 0
    while time.time() - t0 < 6*3600:
        exhausted, to_launch = plan(AGENTS, lambda a: done(a, rnd), alive)
        if exhausted:
            print(time.strftime('%F %T'), 'keeper: all agents done, exiting', file=log, flush=True)
            break
        if to_launch:
            print(time.strftime('%F %T'), 'keeper pass', passes, 'to_launch:', to_launch, file=log, flush=True)
        else:
            print(time.strftime('%F %T'), 'keeper pass', passes, 'supervising: agents live mid-round, no relaunch', file=log, flush=True)
        env = dict(os.environ); env['ROUND'] = rnd
        subprocess.run(['bash', os.path.join(ROOT, 'launch_all.sh')], env=env,
                       stdout=log, stderr=log, start_new_session=True)
        passes += 1
        time.sleep(1200)
    print(time.strftime('%F %T'), 'keeper: exit after', passes, 'passes', file=log, flush=True)


def status_report():
    """Report fleet state without launching anything (09:00:41 incident: a
    `status` query used to START a second keeper)."""
    for a in AGENTS:
        d = done(a, os.environ.get('ROUND', ROUND_DEFAULT))
        print('%-22s %s' % (a, 'DONE' if d else 'pending/alive'))
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ('status', 'report'):
        return status_report()
    if argv:
        print('fleet_keeper.py: unknown argument(s): %r' % (argv,),
              file=sys.stderr)
        print('usage: fleet_keeper.py [status]  (keeper loop via env ROUND)',
              file=sys.stderr)
        return 2
    run_keeper_loop(os.environ.get('ROUND', ROUND_DEFAULT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
