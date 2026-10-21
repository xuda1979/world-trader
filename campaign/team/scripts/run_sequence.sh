#!/bin/bash
# Orchestrate the team pipeline IN ORDER: data -> research -> infra/QA -> accept.
# Why: research consumes what data produces; QA audits only what research produced (per the
# strategy: "run data agents first, research consumes, QA audits after"). Also respects the
# ai-devops rate-limit rule (batches <=5) so 17 agents never fire at t=0.
# Usage: bash run_sequence.sh             # full pipeline (all phases)
#        bash run_sequence.sh data        # just the data phase
#        bash run_sequence.sh research    # just the research phase
#        bash run_sequence.sh audit       # just infra+QA phase
ROOT="/Users/daxu/software/world-trader"
cd "$ROOT"
TEAM=campaign/team

phase_data()    { bash "$TEAM/scripts/launch.sh" DATA_PULL DATA_ORGANIZE DATA_CLEAN DATA_MERGE DATA_MAESTRO; }
phase_research(){ bash "$TEAM/scripts/launch.sh" RES_BASIS RES_CALENDAR RES_META RES_VOL RES_CREDIT \
                                                        RES_CARRY RES_REVERSAL RES_STATARB; }
phase_audit()   { bash "$TEAM/scripts/launch.sh" INFRA_STRUCTURE INFRA_REFACTOR QA_TESTS QA_AUDIT; }

case "${1:-all}" in
  data)     phase_data;;
  research) phase_research;;
  audit)    phase_audit;;
  all)      echo "[seq] 1/3 data ->"; phase_data
            echo "[seq] 2/3 research ->"; phase_research
            echo "[seq] 3/3 audit ->"; phase_audit
            echo "[seq] pipeline complete";;
  *) echo "usage: $0 [all|data|research|audit]"; exit 1;;
esac
