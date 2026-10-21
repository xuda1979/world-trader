"""R4 audit driver: run the byte-identical copy of HUNT_CIT_AG/run_hunt.py from the
sandbox. The original script computes ROOT via HERE/../../../.. which resolves to
world-trader from loop_team/HUNT_CIT_AG but to campaign/agents from audit_r4.
Fix without touching the audited script: put campaign on sys.path so
`from bt import ...` resolves, then patch cit_ag.DATA after import (module cache
keeps the patch when run_hunt re-imports cit_ag)."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_SECTOR2/audit_r4")
import cit_ag
cit_ag.DATA = "/Users/daxu/software/world-trader/tools/quant/data"
exec(open("/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_SECTOR2/audit_r4/run_hunt.py").read())
