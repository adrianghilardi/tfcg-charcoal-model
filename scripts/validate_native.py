from pathlib import Path
from dataclasses import replace
import sys,json
import argparse
ap=argparse.ArgumentParser(description="Compare four native runs with Python using the same native draws.")
ap.add_argument('--source',type=Path,required=True);ap.add_argument('--runs',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
args=ap.parse_args();S=args.source;ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np,pandas as pd
from tfcg_charcoal.core import *
from tfcg_charcoal.landscape import prepare,eligibility
land,meta=prepare(S,S/'InRaster/cosecha24.tif');report={}
for label,p,mode in [
    ('authoritative_native_baseline',SCENARIOS['supplied'],'legacy'),
    ('native_intensive_legacy',replace(SCENARIOS['intensive'],realizations=1,k_sd=0,q_sd=0,yield_sd_pct=0),'legacy'),
    ('native_intensive_corrected',replace(SCENARIOS['intensive'],realizations=1,k_sd=0,q_sd=0,yield_sd_pct=0),'corrected'),
    ('native_reference_stochastic',replace(SCENARIOS['reference'],realizations=3),'legacy'),
]:
    run=args.runs/label;folder=run/'BaseScenario';names=['AmountFMUBiomMC','HarvestedBiomasMC','PotentialCharcoalMC']
    if not all((folder/'Table'/f'{n}.csv').exists() for n in names):raise FileNotFoundError(f'Incomplete native run: {run}')
    native=np.stack([pd.read_csv(folder/'Table'/f'{n}.csv').iloc[:,1:1+p.realizations].to_numpy(float).T for n in names],axis=2)
    q=pd.read_csv(folder/'Temp_table'/f'Coef{p.realizations:02d}.csv').iloc[:,1].to_numpy(float)
    k=pd.read_csv(folder/'Temp_table'/f'k{p.realizations:02d}.csv').iloc[:,1].to_numpy(float)*16
    yields=np.divide(native[:,:,2],native[:,:,1],out=np.zeros(native.shape[:2]),where=native[:,:,1]!=0)*100
    draws={'q':q,'k_ha':k,'yield_pct':yields}
    python,diag=simulate(land['initial'],land['reporting_mask'],land['scheduled_year'],eligibility(land,p),p,draws,mode=mode)
    delta=np.nanmax(np.abs(python-native),axis=(0,1))
    report[label]={'values_compared':int(native.size),'max_abs_error_mg':delta.tolist(),'atol_mg':1e-5,'passed':bool(np.allclose(python,native,rtol=0,atol=1e-5)),'native_q':q.tolist(),'native_K':k.tolist()}
    np.savez_compressed(run/'native_draws_and_outputs.npz',totals=native,**draws)
args.output.parent.mkdir(parents=True,exist_ok=True)
assert all(x['passed'] for x in report.values()), report
args.output.write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
