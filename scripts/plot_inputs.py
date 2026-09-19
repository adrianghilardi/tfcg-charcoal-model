"""Plot initial biomass and the supplied first-rotation harvest calendar."""
from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np, rasterio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tfcg_charcoal.landscape import INPUT_FILES,prepare

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[1]/'data');p.add_argument('--output',type=Path,required=True);p.add_argument('--start-year',type=int,default=2015);a=p.parse_args()
land,meta=prepare(a.source)
mask=land['reporting_full_mask'];rr,cc=np.where(mask)
r0,r1=max(0,rr.min()-8),min(mask.shape[0],rr.max()+9);c0,c1=max(0,cc.min()-8),min(mask.shape[1],cc.max()+9)
with rasterio.open(a.source/INPUT_FILES['biomass']) as d:
    b=d.read(1,masked=True).astype(float).filled(np.nan);tr=d.transform
extent=[(tr.c+c0*tr.a)/1000,(tr.c+c1*tr.a)/1000,(tr.f+r1*tr.e)/1000,(tr.f+r0*tr.e)/1000]
calendar=np.full(mask.shape,np.nan);calendar[land['reserve_mask']]=land['scheduled_year'];calendar[~mask|(calendar<a.start_year)]=np.nan
b[~mask]=np.nan
fig,axs=plt.subplots(1,2,figsize=(6.5,4.3),sharex=True,sharey=True)
for ax,data,cmap,label,title in zip(axs,[b,calendar],['YlGn','viridis'],['Initial biomass (Mg ha$^{-1}$)','Scheduled harvest year'],['(a) Reporting domain','(b) Harvest calendar']):
    im=ax.imshow(data[r0:r1,c0:c1],extent=extent,cmap=cmap,interpolation='nearest')
    ax.set_title(title,fontsize=10);ax.set_xlabel('Easting (km)',fontsize=9);ax.tick_params(labelsize=8)
    bar=fig.colorbar(im,ax=ax,orientation='horizontal',pad=.16,fraction=.07);bar.set_label(label,fontsize=9);bar.ax.tick_params(labelsize=8)
axs[0].set_ylabel('Northing (km)',fontsize=9)
fig.subplots_adjust(left=.12,right=.98,top=.90,bottom=.12,wspace=.18)
a.output.mkdir(parents=True,exist_ok=True)
fig.savefig(a.output/'figure_inputs.png',dpi=300,facecolor='white');fig.savefig(a.output/'figure_inputs.pdf',metadata={'CreationDate':None,'ModDate':None});plt.close(fig)
