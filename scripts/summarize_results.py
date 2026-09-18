"""Build manuscript figures, Monte Carlo precision and paired comparisons."""
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
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9,'legend.fontsize':8,'pdf.fonttype':42})
    for kind in ['combined','management']:
        fig,axs=plt.subplots(3,1,figsize=(6.5,7.4),sharex=True)
        for s,col,ls in zip(scenarios,colors,['-','--',':']):
            name='combined_'+s if kind=='combined' or s=='reference' else 'management_'+s
            vals=get(a.main,name)['totals'];years=np.arange(2015,2015+vals.shape[1])
            for q,ax in enumerate(axs):
                lo,hi=np.quantile(vals[:,:,q],[.025,.975],axis=0)
                ax.fill_between(years,lo,hi,color=col,alpha=.10,linewidth=0)
                ax.plot(years,vals[:,:,q].mean(axis=0),color=col,ls=ls,lw=1.5,label=s.title())
        if kind=='management':
            vals=get(a.main,'no_harvest')['totals']
            axs[0].plot(years,vals[:,:,0].mean(axis=0),color='#555555',ls='-.',lw=1.2,label='No harvest')
        for i,ax in enumerate(axs):
            ax.set_title(['(a) Standing biomass after growth','(b) Annual wood harvest','(c) Potential charcoal production'][i],loc='left',fontsize=10)
            ax.set_ylabel(['Mg','Mg yr$^{-1}$','Mg yr$^{-1}$'][i]);ax.set_ylim(bottom=0)
            for x in [2038.5,2062.5]:ax.axvline(x,color='#aaaaaa',ls='--',lw=.7)
            ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',color='#e3e3e3',lw=.5)
            ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
        axs[0].legend(ncol=4 if kind=='management' else 3,loc='lower left',bbox_to_anchor=(0,1.16),frameon=False)
        axs[-1].set_xlabel('Scenario year');axs[-1].set_xlim(2015,2086)
        fig.subplots_adjust(left=.14,right=.98,top=.91,bottom=.08,hspace=.42)
        save(fig,'figure_'+kind)
    summary=[];paired=[];distributions={}
    ref=get(a.main,'combined_reference')
    for folder in sorted(a.main.iterdir()):
        if not (folder/'results.npz').exists():continue
        d=get(a.main,folder.name);x=d['totals'];n,ny,_=x.shape
        means=x.reshape(n,ny//24,24,3).mean(axis=2)
        distributions[folder.name]={k:{'mean':float(d[k].mean()),'sd':float(d[k].std(ddof=1)),'min':float(d[k].min()),'max':float(d[k].max())} for k in ['k_ha','q','yield_pct']}
        for r in range(ny//24):
            for q,quantity in enumerate(['standing_biomass','harvest','charcoal']):
                v=means[:,r,q];summary.append([folder.name,r+1,quantity,n,v.mean(),np.quantile(v,.025),np.quantile(v,.975),v.std(ddof=1)/np.sqrt(n)])
        if folder.name.startswith('management_'):
            assert all(np.array_equal(d[k],ref[k]) for k in ['k_ha','q','yield_pct'])
            delta=means-ref['totals'].reshape(n,3,24,3).mean(axis=2)
            for r in range(3):
                for q,quantity in enumerate(['standing_biomass','harvest','charcoal']):
                    v=delta[:,r,q];paired.append([folder.name,r+1,quantity,v.mean(),np.quantile(v,.025),np.quantile(v,.975),float(np.mean(v>0)),v.std(ddof=1)/np.sqrt(n)])
    for name,header,rows in [('precision_summary.csv',['experiment','rotation','quantity','realizations','mean','q025','q975','monte_carlo_standard_error'],summary),('paired_management_differences.csv',['experiment','rotation','quantity','mean_difference','q025_difference','q975_difference','fraction_positive','monte_carlo_standard_error'],paired)]:
        with (a.output/name).open('w',newline='',encoding='utf8') as f:w=csv.writer(f);w.writerow(header);w.writerows(rows)
    (a.output/'sampled_distributions.json').write_text(json.dumps(distributions,indent=2),encoding='utf8')
    provenance={p.parent.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(a.main.glob('*/results.npz'))}
    (a.output/'figure_inputs.json').write_text(json.dumps(provenance,indent=2),encoding='utf8')
    print('Figures and summaries:',a.output)

if __name__=='__main__':main()
