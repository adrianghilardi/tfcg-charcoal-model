"""Run the Python-only Ulaya Mbuyuni scenario ensemble from checked inputs."""
from pathlib import Path
import sys,argparse,json,hashlib,csv,time,platform,importlib.metadata,re
from dataclasses import asdict,fields
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from tfcg_charcoal.core import Parameters,parameter_draws,simulate
from tfcg_charcoal.landscape import prepare,eligibility

def run():
    root=Path(__file__).resolve().parents[1]
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,default=root/'data',help='Folder containing the five InRaster TIFFs (default: repository data folder).')
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--config',type=Path,default=root/'config/main_1000.json')
    ap.add_argument('--seed',type=int,default=20260917)
    ap.add_argument('--realizations',type=int,help='Override the configured realization count for a smoke run.')
    ap.add_argument('--experiments',nargs='+',help='Run only these experiment labels from the configuration.')
    a=ap.parse_args();out=a.output.resolve();src=a.source.resolve()
    if out==src or out.is_relative_to(src):raise ValueError('Output must be outside the input bundle.')
    if out.exists() and any(out.iterdir()):raise FileExistsError('Use a new output directory.')
    configurations=json.loads(a.config.read_text(encoding='utf8'))
    if not isinstance(configurations,list) or not configurations:raise ValueError('Expected a nonempty scenario list.')
    if a.experiments:
        selected=set(a.experiments)
        configurations=[row for row in configurations if isinstance(row,dict) and row.get('experiment') in selected]
        missing=selected-{row['experiment'] for row in configurations}
        if missing:raise ValueError(f'Unknown experiments: {sorted(missing)}')
    allowed={f.name for f in fields(Parameters)}
    labels=set()
    for row in configurations:
        if not isinstance(row,dict) or 'experiment' not in row:
            raise ValueError('Each configuration needs an experiment name.')
        unknown=set(row)-allowed-{'experiment'}
        if unknown:raise ValueError(f'Unknown configuration fields: {sorted(unknown)}')
        if not re.fullmatch(r'[A-Za-z0-9_-]+',str(row['experiment'])):
            raise ValueError(f'Invalid experiment name: {row["experiment"]}')
        if row['experiment'] in labels:raise ValueError(f'Duplicate experiment: {row["experiment"]}')
        labels.add(row['experiment'])
    landscape,meta=prepare(src)
    out.mkdir(parents=True,exist_ok=True)
    (out/'landscape.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
    parameters=[];annual=[];summary=[];checks={};clock=time.monotonic()
    for row in configurations:
        label=row['experiment']
        p=Parameters(**{k:v for k,v in row.items() if k in allowed})
        if a.realizations is not None:
            p=Parameters(**(asdict(p)|{'realizations':a.realizations}))
        t0=time.monotonic();draws=parameter_draws(p,a.seed)
        result,diagnostics=simulate(landscape['initial'],landscape['reporting_mask'],landscape['scheduled_year'],eligibility(landscape,p),p,draws,cell_area_ha=meta['cell_area_ha'])
        folder=out/label;folder.mkdir()
        np.savez_compressed(folder/'results.npz',totals=result,diagnostics=diagnostics,**draws)
        params=asdict(p)|{'experiment':label,'seed':a.seed,'rng':'NumPy PCG64, independent SeedSequence streams for K, q and kiln yield','initial_biomass_mc':False}
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
        checks[label]={'elapsed_seconds':time.monotonic()-t0,'q_outside_0_1':int(np.count_nonzero((draws['q']<=0)|(draws['q']>=1))),'nonpositive_K':int(np.count_nonzero(draws['k_ha']<=0)),'invalid_yields':int(np.count_nonzero((draws['yield_pct']<0)|(draws['yield_pct']>100))),'max_missing_fmu_cells':int(diagnostics[:,:,0].max()),'max_negative_fmu_cells':int(diagnostics[:,:,1].max()),'years_with_negative_net_growth':int(np.count_nonzero(diagnostics[:,:,2]<-1e-6)),'first_rotation_means':result[:,:p.rotation_years,:].mean(axis=(0,1)).tolist(),'last_rotation_means':result[:,-p.rotation_years:,:].mean(axis=(0,1)).tolist()}
        print(label,json.dumps(checks[label]),flush=True)
    with (out/'annual_results.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.writer(f);w.writerow(['experiment','scenario','realization','year','rotation','standing_biomass_mg','harvest_mg','charcoal_mg','missing_fmu_cells','negative_fmu_cells','net_growth_mg','K_mg_ha','q','yield_pct']);w.writerows(annual)
    with (out/'rotation_summary.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.writer(f);w.writerow(['experiment','scenario','rotation','quantity','annual_or_stock_mean_mg','realization_mean_q025_mg','realization_mean_q975_mg','rotation_flow_total_mean_mg']);w.writerows(summary)
    manifest={'python':sys.version,'platform':platform.platform(),'packages':{p:importlib.metadata.version(p) for p in ['numpy','rasterio','scipy','matplotlib']},'seed':a.seed,'elapsed_seconds':time.monotonic()-clock,'experiments':parameters,'checks':checks,'configuration_sha256':hashlib.sha256(a.config.read_bytes()).hexdigest(),'outputs':{p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print('COMPLETE',out,flush=True)

if __name__=='__main__':run()
