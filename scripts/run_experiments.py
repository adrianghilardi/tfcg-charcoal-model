"""Run baseline, validate archived outputs, and execute controlled experiments.

Usage: python scripts/run_experiments.py --source ORIGINAL_FOLDER --output NEW_DIR
The default calendar is InRaster/cosecha24.tif supplied by the author.
"""
from pathlib import Path
import sys,argparse,json,hashlib,csv,time,platform,importlib.metadata
from dataclasses import replace,asdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np,pandas as pd
from tfcg_charcoal.core import SCENARIOS,parameter_draws,simulate
from tfcg_charcoal.landscape import prepare,eligibility

def run():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--schedule',type=Path)
    ap.add_argument('--reconstruct-calendar-2038',action='store_true')
    ap.add_argument('--seed',type=int,default=20260917)
    ap.add_argument('--realizations',type=int,default=100)
    ap.add_argument('--baseline-only',action='store_true')
    ap.add_argument('--corrected-only',action='store_true',help='Skip legacy scenario experiments; retain archived baseline verification.')
    a=ap.parse_args();out=a.output.resolve();src=a.source.resolve()
    if out==src or out.is_relative_to(src):raise ValueError('Output must be outside the supplied source folder.')
    if out.exists() and any(out.iterdir()):raise FileExistsError('Use a new output directory.')
    out.mkdir(parents=True,exist_ok=True)
    schedule=a.schedule or src/'InRaster/cosecha24.tif'
    landscape,meta=prepare(src,schedule,a.reconstruct_calendar_2038)
    (out/'landscape.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
    parameters=[];annual=[];summary=[];checks={};clock=time.monotonic()
    def experiment(label,p,growth,bounded):
        t0=time.monotonic();draws=parameter_draws(p,a.seed,bounded)
        result,diagnostics=simulate(landscape['initial'],landscape['reporting_mask'],landscape['scheduled_year'],eligibility(landscape,p),p,draws,mode=growth)
        folder=out/label;folder.mkdir()
        np.savez_compressed(folder/'results.npz',totals=result,diagnostics=diagnostics,**draws)
        params=asdict(p)|{'experiment':label,'growth':growth,'bounded':bounded,'seed':a.seed,'rng':'NumPy PCG64, independent SeedSequence streams for K, q and kiln yield','initial_biomass_mc':False}
        (folder/'configuration.json').write_text(json.dumps(params,indent=2),encoding='utf8')
        parameters.append(params)
        ny=p.rotation_years*p.rotations
        for j in range(p.realizations):
            for t in range(ny):
                annual.append([label,p.name,j+1,p.start_year+t,t//p.rotation_years+1,*result[j,t].tolist(),*diagnostics[j,t].tolist(),draws['k_ha'][j],draws['q'][j],draws['yield_pct'][j,t]])
        for r in range(p.rotations):
            window=result[:,r*p.rotation_years:(r+1)*p.rotation_years,:]
            for i,quantity in enumerate(['standing_biomass','harvest','charcoal']):
                means=window[:,:,i].mean(axis=1)
                summary.append([label,p.name,r+1,quantity,float(means.mean()),float(np.quantile(means,.025)),float(np.quantile(means,.975)),float(window[:,:,i].sum(axis=1).mean()) if i else None])
        checks[label]={'elapsed_seconds':time.monotonic()-t0,'q_outside_0_1':int(np.count_nonzero((draws['q']<=0)|(draws['q']>=1))),'nonpositive_K':int(np.count_nonzero(draws['k_ha']<=0)),'invalid_yields':int(np.count_nonzero((draws['yield_pct']<0)|(draws['yield_pct']>100))),'max_missing_fmu_cells':int(diagnostics[:,:,0].max()),'max_negative_fmu_cells':int(diagnostics[:,:,1].max()),'years_with_negative_net_growth':int(np.count_nonzero(diagnostics[:,:,2]<-1e-6)),'first_rotation_means':result[:,:24,:].mean(axis=(0,1)).tolist(),'last_rotation_means':result[:,-24:,:].mean(axis=(0,1)).tolist()}
        print(label,json.dumps(checks[label]),flush=True)
        return result
    result=experiment('supplied_baseline',SCENARIOS['supplied'],'legacy',False)
    comparison={}
    for i,name in enumerate(['AmountFMUBiomMC','HarvestedBiomassMC','PotentialCharcoalMC']):
        old=pd.read_csv(src/'MC/Table'/f'{name}.csv').iloc[:,1:3].to_numpy(float).T
        comparison[name]={'maximum_absolute_difference_mg':float(np.max(np.abs(result[:,:,i]-old))),'values_compared':int(old.size),'passed_at_absolute_tolerance_1e-7':bool(np.allclose(result[:,:,i],old,rtol=0,atol=1e-7))}
    (out/'archive_comparison.json').write_text(json.dumps(comparison,indent=2),encoding='utf8')
    if not all(c['passed_at_absolute_tolerance_1e-7'] for c in comparison.values()):raise RuntimeError('Archived baseline comparison failed; inspect calendar and source versions.')
    if not a.baseline_only:
        for name in ['reference','conservative','intensive']:
            p=replace(SCENARIOS[name],realizations=a.realizations)
            if not a.corrected_only:
                experiment(f'legacy_unbounded_{name}',p,'legacy',False)
                experiment(f'legacy_bounded_{name}',p,'legacy',True)
            experiment(f'corrected_bounded_{name}',p,'corrected',True)
        for name in ['conservative','intensive']:
            rules=SCENARIOS[name];p=replace(SCENARIOS['reference'],name=name,realizations=a.realizations,water_buffer_m=rules.water_buffer_m,max_slope_deg=rules.max_slope_deg,min_biomass_mg_cell=rules.min_biomass_mg_cell,retained_pct=rules.retained_pct)
            experiment(f'corrected_management_only_{name}',p,'corrected',True)
        p=replace(SCENARIOS['reference'],name='no_harvest',realizations=a.realizations,retained_pct=100)
        experiment('corrected_no_harvest',p,'corrected',True)
    with (out/'annual_results.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.writer(f);w.writerow(['experiment','scenario','realization','year','rotation','standing_biomass_mg','harvest_mg','charcoal_mg','missing_fmu_cells','negative_fmu_cells','net_growth_mg','K_mg_ha','q','yield_pct']);w.writerows(annual)
    with (out/'rotation_summary.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.writer(f);w.writerow(['experiment','scenario','rotation','quantity','annual_or_stock_mean_mg','realization_mean_q025_mg','realization_mean_q975_mg','rotation_flow_total_mean_mg']);w.writerows(summary)
    manifest={'python':sys.version,'platform':platform.platform(),'packages':{p:importlib.metadata.version(p) for p in ['numpy','pandas','rasterio','scipy','matplotlib']},'seed':a.seed,'elapsed_seconds':time.monotonic()-clock,'experiments':parameters,'checks':checks,'source_model_sha256':hashlib.sha256((src/'models/ModUlaya_Fun_frost.egoml').read_bytes()).hexdigest(),'outputs':{p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print('COMPLETE',out,flush=True)

if __name__=='__main__':run()
