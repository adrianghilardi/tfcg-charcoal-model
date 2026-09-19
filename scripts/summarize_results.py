"""Build three-scenario figures and Monte Carlo summaries."""
from pathlib import Path
import argparse,json,csv,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--main',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    def get(folder,name):
        with np.load(folder/name/'results.npz') as z:return {k:z[k] for k in z.files}
    def save(fig,name):
        fig.savefig(a.output/(name+'.png'),dpi=300,facecolor='white')
        fig.savefig(a.output/(name+'.pdf'),metadata={'CreationDate':None,'ModDate':None})
        plt.close(fig)
    colors=['#245e88','#2f7954','#bd4d28'];scenarios=['reference','conservative','intensive']
    reference_config=json.loads((a.main/'reference'/'configuration.json').read_text(encoding='utf8'))
    start_year=reference_config['start_year']
    rotation_years=reference_config['rotation_years']
    rotations=reference_config['rotations']
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9,'legend.fontsize':8,'pdf.fonttype':42})
    required=[a.main/s/'results.npz' for s in scenarios]
    if not all(path.exists() for path in required):
        raise FileNotFoundError(f'Missing scenario result: {[str(path) for path in required if not path.exists()]}')
    fig,axs=plt.subplots(3,1,figsize=(6.5,7.4),sharex=True)
    for s,col,ls in zip(scenarios,colors,['-','--',':']):
        vals=get(a.main,s)['totals'];years=np.arange(start_year,start_year+vals.shape[1])
        for q,ax in enumerate(axs):
            lo,hi=np.quantile(vals[:,:,q],[.025,.975],axis=0)
            ax.fill_between(years,lo,hi,color=col,alpha=.10,linewidth=0)
            ax.plot(years,vals[:,:,q].mean(axis=0),color=col,ls=ls,lw=1.5,label=s.title())
    for i,ax in enumerate(axs):
        ax.set_title(['(a) Standing biomass after growth','(b) Annual wood harvest','(c) Potential charcoal production'][i],loc='left',fontsize=10)
        ax.set_ylabel(['Mg','Mg yr$^{-1}$','Mg yr$^{-1}$'][i]);ax.set_ylim(bottom=0)
        for r in range(1,rotations):ax.axvline(start_year+r*rotation_years-.5,color='#aaaaaa',ls='--',lw=.7)
        ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',color='#e3e3e3',lw=.5)
        ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
    axs[0].legend(ncol=3,loc='lower left',bbox_to_anchor=(0,1.16),frameon=False)
    axs[-1].set_xlabel('Scenario year');axs[-1].set_xlim(start_year,start_year+rotations*rotation_years-1)
    fig.subplots_adjust(left=.14,right=.98,top=.91,bottom=.08,hspace=.42)
    save(fig,'figure_scenarios')
    summary=[];distributions={}
    for scenario in scenarios:
        folder=a.main/scenario
        d=get(a.main,scenario);x=d['totals'];n,ny,_=x.shape
        config=json.loads((folder/'configuration.json').read_text(encoding='utf8'))
        if (config['start_year'],config['rotation_years'],config['rotations']) != (start_year,rotation_years,rotations):
            raise ValueError(f'Incompatible time horizon in {folder.name}')
        means=x.reshape(n,rotations,rotation_years,3).mean(axis=2)
        distributions[scenario]={k:{'mean':float(d[k].mean()),'sd':float(d[k].std(ddof=1)),'min':float(d[k].min()),'max':float(d[k].max())} for k in ['k_ha','q','yield_pct']}
        for r in range(rotations):
            for q,quantity in enumerate(['standing_biomass','harvest','charcoal']):
                v=means[:,r,q];summary.append([scenario,r+1,quantity,n,v.mean(),np.quantile(v,.025),np.quantile(v,.975),v.std(ddof=1)/np.sqrt(n)])
    with (a.output/'precision_summary.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.writer(f)
        w.writerow(['scenario','rotation','quantity','realizations','mean','q025','q975','monte_carlo_standard_error'])
        w.writerows(summary)
    (a.output/'sampled_distributions.json').write_text(json.dumps(distributions,indent=2),encoding='utf8')
    provenance={p.parent.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(a.main.glob('*/results.npz'))}
    (a.output/'result_hashes.json').write_text(json.dumps(provenance,indent=2),encoding='utf8')
    print('Figures and summaries:',a.output)

if __name__=='__main__':main()
