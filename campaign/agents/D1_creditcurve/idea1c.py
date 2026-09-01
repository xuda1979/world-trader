import sys; sys.path.insert(0,'.')
from idea1 import build
from d1_lib import stats, halves
for (w,step,thr) in [(504,5,1.5),(378,5,1.5)]:
    net,sig=build(w,step,thr,'mom')
    s=stats(net); h1,h2=halves(net)
    print(f"w{w} s{step} thr{thr}: SR={s['sr']:.2f} mdd={s['mdd']:.1f}% negy={s['negy']} worst={s['worst']:.1f}% H1={h1:.2f} H2={h2:.2f}")
