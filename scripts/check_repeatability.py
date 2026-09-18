"""Compare two complete runs numerically, including their exported parameter draws."""
import argparse,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('first',type=Path);p.add_argument('second',type=Path);a=p.parse_args()
count=0;report={}
for f in a.first.glob('*/results.npz'):
    g=a.second/f.relative_to(a.first)
    if not g.exists():raise FileNotFoundError(g)
    with np.load(f) as x,np.load(g) as y:
        if set(x.files)!=set(y.files):raise AssertionError(f'Array keys differ: {f}')
        for k in x.files:
            np.testing.assert_array_equal(x[k],y[k]);count+=x[k].size
    report[f.parent.name]='identical'
print(json.dumps({'experiments':report,'array_elements_checked':count,'passed':True},indent=2))
