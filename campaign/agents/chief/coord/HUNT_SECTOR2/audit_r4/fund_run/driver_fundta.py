"""R4 audit driver: HUNT_FUNDAMENTAL s_ta_backtest.py (their best IC leg, cited in
DEAD_IDEAS row 'value/growth/profitability screens' as SR +0.39 FAIL). The script
imports run_ideas2_lib which executes at import-time; sys.path points at the ORIGINAL
scratch dir so hf_engine/run_ideas2_lib load from the audited source unmodified."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
exec(open("/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_SECTOR2/audit_r4/fund_run/s_ta_backtest.py").read())
