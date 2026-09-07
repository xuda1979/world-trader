#!/usr/bin/env python3
import subprocess, os, time, re, sys
ROOT = '/Users/daxu/software/world-trader/campaign/agents/chief/coord'
AGENTS = open(os.path.join(ROOT, 'AGENTS.txt')).read().split()
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
t0 = time.time()
log = open(os.path.join(ROOT, 'logs', 'fleet_keeper.log'), 'a')
rnd = '3'
passes = 0
while time.time() - t0 < 6*3600:
    pending = [a for a in AGENTS if not done(a, rnd) and not alive(a)]
    if not pending:
        print(time.strftime('%F %T'), 'keeper: nothing pending, exiting', file=log, flush=True)
        break
    print(time.strftime('%F %T'), 'keeper pass', passes, 'pending:', pending, file=log, flush=True)
    env = dict(os.environ); env['ROUND'] = rnd
    subprocess.run(['bash', os.path.join(ROOT, 'launch_all.sh')], env=env,
                   stdout=log, stderr=log, start_new_session=True)
    passes += 1
    time.sleep(1200)
print(time.strftime('%F %T'), 'keeper: exit after', passes, 'passes', file=log, flush=True)
