import subprocess, os
R='/Users/daxu/software/world-trader'
# was gkx_1y_deploy_monthly.csv modified after the daily CSV was created?
out = subprocess.run(['git','-C',R,'log','--all','--format=%h %ad %s','--date=iso','--','tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv'],capture_output=True,text=True)
print(out.stdout)
out = subprocess.run(['git','-C',R,'log','--all','--format=%h %ad %s','--date=iso','--','campaign/results/sleeve_library/XGB1y_deploy.csv'],capture_output=True,text=True)
print(out.stdout)
