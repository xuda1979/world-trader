import sys; sys.path.insert(0,'.')
from libb import *
exec(open('p1.py').read().split("if __name__")[0])
champ=F.load_champion()
import libb
for lb,skip in [(5,0),(5,1),(10,0),(21,0),(21,1)]:
    net,posv,g0=run(lb=lb,skip=skip)
    st=F.full_stats(net); h1,h2=F.halves_sr(net)
    fg=F.flatten_gates(net); corr,nn=F.corr_to(net,champ)
    pl_p,pl_real=libb.book_position_lag_p(posv,rets[rets.index>=st['first']],n=200)
    yr=(1+net).groupby(net.index.year).prod()-1
    print(f"lb{lb}_sk{skip}: SR {st['sr']:+.3f} ann_geo {st['ann_geo']*100:+.1f}% MDD {st['mdd']*100:.1f}% negy {st['negy']} worst {st['worst']*100:.1f}% | H1 {h1:+.2f} H2 {h2:+.2f} | poslag_p {pl_p:.3f} | ac1 {fg['ac1']:+.3f} uniqR {fg['uniqR']:.3f} | corr {corr:+.3f}(n={nn})")
