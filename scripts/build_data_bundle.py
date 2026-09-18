"""Create a minimal, checksummed local data bundle; does not publish anything."""
from pathlib import Path
import argparse,hashlib,json,zipfile

REQUIRED=[
    'models/ModUlaya_Fun_frost.egoml',
    'InRaster/Biomas_50r0Cs.tif','InRaster/cosecha24.tif',
    'TempRaster/foresst_reserve_c.tif','TempRaster/DEM_c.tif',
    'TempRaster/rivers_c.tif','TempRaster/charcoalharvB_c.tif',
    'TempRaster/proposed_LUP_c.tif','Intables/rate_growth2.csv',
    'MC/Table/AmountFMUBiomMC.csv','MC/Table/HarvestedBiomassMC.csv','MC/Table/PotentialCharcoalMC.csv',
]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    records=[]
    for name in REQUIRED:
        f=a.source/name
        if not f.is_file():raise FileNotFoundError(f)
        records.append({'path':name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
    a.output.parent.mkdir(parents=True,exist_ok=True)
    manifest=json.dumps({'files':records,'source':'José Luis Caballero model delivery, 17 September 2026, with author-supplied cosecha24.tif','scope':'Prepared analytical inputs and archived baseline outputs; raw remote-sensing and field-data processing are not supplied.','licences':{'model':'MIT','analytical_inputs_and_outputs':'CC-BY-4.0'}},indent=2)
    with zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED) as z:
        for r in records:z.write(a.source/r['path'],r['path'])
        z.writestr('bundle_manifest.json',manifest)
        root=Path(__file__).resolve().parents[1]
        z.write(root/'LICENSE','LICENSE-MODEL.txt')
        z.write(root/'data/LICENSE.md','LICENSE-DATA.md')
    a.output.with_suffix('.manifest.json').write_text(manifest,encoding='utf8')
    print(f'{len(records)} files, {a.output.stat().st_size} archive bytes; sha256={hashlib.sha256(a.output.read_bytes()).hexdigest()}')

if __name__=='__main__':main()
