import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_SECTOR2/audit_r4")
import cit_ag
cit_ag.DATA = "/Users/daxu/software/world-trader/tools/quant/data"
exec(open("/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_SECTOR2/audit_r4/deep_check.py").read())
