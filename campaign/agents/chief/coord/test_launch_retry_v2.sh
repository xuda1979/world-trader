#!/bin/bash
TDD v2 regression test for launch_agent_chief.sh retry classification (standup 2026-09-06).
Contract: an attempt is retried ONLY when IT failed, judged on ITS OWN output.
 v2A) SUCCESS whose text merely MENTIONS 429 -> exactly 1 invocation (no wasteful re-run).
 v2B) NON-429 API error then success -> exactly 2 invocations (must be retried).
 v2C) genuine 429 then success -> exactly 2 invocations (regression guard, v1 contract).
set -u
ROOT=$/Users/daxu/software/world-trader
LAUNCHER=$ROOT/campaign/agents/chief/coord/launch_agent_chief.sh
FAILS=0
run_case() {
  local name=$1 expect=$2 line1=$3 line2=$4
  local T STUB C i n
  T=$(mktemp -d)
  STUB=$T/fakebin_claude
  C=$T/count
  : > $C
  mkdir -p $T/logs
  {
    echo #!/bin/bash
    echo # n=0
    echo # [ -f $C ] && n=$(cat $C
    echo # n=$((n+1))
    echo # echo "n" > $C
    echo # if [ "$n" -eq 1 ]; then
    echo #   echo """@line1"""
    echo # else
    echo #   echo """@line2"""
    echo # fi
    echo # exit 0
  } > $STUB
  chmod +x $STUB
  CLAUDE_BIN=$STUB LOG_DIR=$T/logs MAXTRY=4 bash $LAUNCHER TDD_RETRY_V2 1 >/dev/null 2>&1
  for i in $(seq 1 150); do
    grep -q "TDD_RETRY_V2 round 1 end" $T/logs/TDD_RETRY_V2.log 2>/dev/null && break
    sleep 1
  done
  sleep 1
  n=$(cat $C 2>/dev/null)
  n=$${n:-0}
  rm -rf $T
  if [ "$n" -eq $expect ]; then
    echo "PASS [$name]: calls=$n expected=$expect"
  else
    echo "FAIL [$name]: calls=$n expected=$expect"
    FAILS=$((FAILS+1))
  fi
}
run_case v2A-success-prose-mentions-429 1 "Round complete: audited the campaign 429 handling; findings appended." "stub success"
run_case v2B-api-error-500-then-success 2 "API Error: 500 overloaded_error" "stub success"
run_case v2C-real-429-then-success 2 "API Error: Request rejected (429) - rate limit" "stub success"
if [ "$FAILS" -eq 0 ]; then
  echo ALL v2 CASES PASS
  exit 0
fi
echo "$FAILS v2 case(s) FAILED"
exit 1
