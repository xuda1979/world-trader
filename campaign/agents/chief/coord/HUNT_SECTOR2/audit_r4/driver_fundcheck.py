import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_SECTOR2/audit_r4")
import cit_ag
cit_ag.DATA = "/Users/daxu/software/world-trader/tools/quant/data"
ROOT = "/Users/daxu/software/world-trader"  # fundamental_check builds paths from ROOT global
exec(open("/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CIT_AG/fundamental_check.py").read())
