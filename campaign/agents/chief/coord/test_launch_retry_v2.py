#!/usr/bin/env python3
# TDD v2 for launch_agent_chief.sh retry classification (coordinator standup 2026-09-06).
# Contract: an attempt is retried ONLY when IT failed, judged on ITS OWN output.
#  v2A: SUCCESS whose text merely MENTIONS 429 -> exactly 1 invocation (no wasteful re-run).
#  v2B: NON-429 API error then success -> exactly 2 invocations (must be retried).
#  v2C: genuine 429 then success -> exactly 2 invocations (regression guard, v1 contract).
import os
import subprocess
import sys
import tempfile
import time

LAUNCHER = '/Users/daxu/software/world-trader/campaign/agents/chief/coord/launch_agent_chief.sh'
AGENT = 'TDD_RETRY_V2'


def make_stub(tdir, outputs):
    count = os.path.join(tdir, 'count')
    stub = os.path.join(tdir, 'fakebin_claude')
    body = []
    body.append('#!/usr/bin/env python3')
    body.append('import sys')
    body.append('COUNT = ' + repr(count))
    body.append('OUTPUTS = ' + repr(outputs))
    body.append('try:')
    body.append('    n = int(open(COUNT).read().strip() or 0)')
    body.append('except Exception:')
    body.append('    n = 0')
    body.append('n = n + 1')
    body.append('open(COUNT, "w").write(str(n))')
    body.append('idx = min(n - 1, len(OUTPUTS) - 1)')
    body.append('print(OUTPUTS[idx])')
    with open(stub, 'w') as fh:
        fh.write(chr(10).join(body) + chr(10))
    os.chmod(stub, 0o755)
    return stub


def run_case(name, expect, outputs):
    tdir = tempfile.mkdtemp()
    stub = make_stub(tdir, outputs)
    logs = os.path.join(tdir, 'logs')
    os.makedirs(logs, exist_ok=True)
    env = dict(os.environ)
    env['CLAUDE_BIN'] = stub
    env['LOG_DIR'] = logs
    env['MAXTRY'] = '4'
    subprocess.run(['bash', LAUNCHER, AGENT, '1'], env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logf = os.path.join(logs, AGENT + '.log')
    for _ in range(200):
        if os.path.exists(logf):
            with open(logf, errors='replace') as fh:
                txt = fh.read()
            if AGENT + ' round 1 end' in txt:
                break
        time.sleep(1)
    time.sleep(1)
    countf = os.path.join(tdir, 'count')
    n = 0
    if os.path.exists(countf):
        with open(countf) as fh:
            raw = fh.read().strip()
        if raw:
            n = int(raw)
    ok = n == expect
    tag = 'PASS' if ok else 'FAIL'
    print(tag + ' [' + name + ']: calls=' + str(n) + ' expected=' + str(expect))
    return 0 if ok else 1


def main():
    fails = 0
    fails += run_case(
        'v2A-success-prose-mentions-429', 1,
        ['Round complete: audited the campaign 429 handling; findings appended.'])
    fails += run_case(
        'v2B-api-error-500-then-success', 2,
        ['API Error: 500 overloaded_error', 'stub success'])
    fails += run_case(
        'v2C-real-429-then-success', 2,
        ['API Error: Request rejected (429) - rate limit', 'stub success'])
    if fails == 0:
        print('ALL v2 CASES PASS')
        return 0
    print(str(fails) + ' v2 case(s) FAILED')
    return 1


if __name__ == '__main__':
    sys.exit(main())
