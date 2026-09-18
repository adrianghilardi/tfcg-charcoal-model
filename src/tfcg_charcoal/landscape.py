"""Read aligned source rasters and transparently prepare the spatial inputs."""
from pathlib import Path
import hashlib,json
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

FILES={'biomass':'InRaster/Biomas_50r0Cs.tif','reserve':'TempRaster/foresst_reserve_c.tif','dem':'TempRaster/DEM_c.tif','rivers':'TempRaster/rivers_c.tif','extra_plots':'TempRaster/charcoalharvB_c.tif'}

def slope_degrees(elevation,cell_size=25):
    """Maximum absolute slope to the eight neighbours, ignoring missing neighbours."""
    a=np.asarray(elevation,dtype=float);p=np.pad(a,1,mode='edge');maximum=np.zeros(a.shape)
    for dy in [-1,0,1]:
        for dx in [-1,0,1]:
            if not(dx or dy):continue
            other=p[1+dy:1+dy+a.shape[0],1+dx:1+dx+a.shape[1]]
            gradient=np.abs(a-other)/(cell_size*np.hypot(dx,dy))
            maximum=np.fmax(maximum,gradient)
    s=np.degrees(np.arctan(maximum)).astype(np.float32);s[~np.isfinite(a)]=np.nan
    return s

def prepare(source,schedule):
    source=Path(source);schedule=Path(schedule)
    paths={k:source/v for k,v in FILES.items()};paths['schedule']=schedule
    arrays={};meta={};geometry=None
    for k,p in paths.items():
        with rasterio.open(p) as ds:
            this=(ds.shape,ds.crs,ds.transform)
            if geometry is None:geometry=this
            if this!=geometry:raise ValueError(f'Unaligned raster: {p}')
            if ds.crs.to_epsg()!=32737 or ds.res!=(25,25):raise ValueError('Inputs require EPSG:32737 and 25 m cells.')
            arr=ds.read(1,masked=True).astype(float).filled(np.nan)
            arrays[k]=arr
            meta[k]={'relative_path':str(p.relative_to(source)) if p.is_relative_to(source) else p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'valid_cells':int(np.isfinite(arr).sum()),'nodata':ds.nodata}
    cal=arrays['schedule']
    reserve=np.isfinite(arrays['reserve']);report=reserve&np.isfinite(cal)
    slope=slope_degrees(arrays['dem'])
    dist=distance_transform_edt(~np.isfinite(arrays['rivers']),sampling=25)
    # Distances are quantized to integer metres before applying buffer rules.
    dist=np.floor(dist).astype(np.int32)
    full_calendar=np.nan_to_num(cal,nan=0)+np.isfinite(arrays['extra_plots']).astype(int)
    vector={'initial':(arrays['biomass'][reserve]/16).astype(np.float32),'reporting_mask':report[reserve],
            'scheduled_year':full_calendar[reserve].astype(np.int16),'slope':slope[reserve],'water_distance':dist[reserve],
            'reserve_mask':reserve,'reporting_full_mask':report,'slope_full':slope,'water_distance_full':dist}
    meta.update(crs='EPSG:32737',cell_size_m=25,cell_area_ha=.0625,shape=list(reserve.shape),transform=list(geometry[2]),reserve_cells=int(reserve.sum()),fmu_cells=int(report.sum()),fmu_area_ha=float(report.sum()/16),initial_fmu_biomass_mg=float(np.sum(arrays['biomass'][report]/16)))
    return vector,meta

def eligibility(land,p):
    return ~((land['water_distance']<p.water_buffer_m)|(land['slope']>p.max_slope_deg))
