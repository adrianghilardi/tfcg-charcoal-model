from pathlib import Path
import argparse,xml.etree.ElementTree as E,json,hashlib,subprocess,time,re
P=argparse.ArgumentParser()
P.add_argument('--source',type=Path,required=True)
P.add_argument('--output',type=Path,required=True)
P.add_argument('--schedule',type=Path,required=True)
P.add_argument('--console',type=Path,default=Path(r'C:\Program Files\Dinamica EGO 8\DinamicaConsole8.exe'))
P.add_argument('--scenario',choices=['supplied','reference','conservative','intensive'],default='supplied')
P.add_argument('--realizations',type=int)
P.add_argument('--rotations',type=int)
P.add_argument('--save-maps',action='store_true')
P.add_argument('--constants',type=Path,help='JSON map from supplied output-port IDs to explicit values.')
P.add_argument('--growth',choices=['legacy','corrected'],default='legacy')
args=P.parse_args()
src=args.source.resolve();out=args.output.resolve();schedule=args.schedule.resolve()
assert src.is_dir() and schedule.is_file() and args.console.is_file()
assert out!=src and not out.is_relative_to(src),'Outputs may not be stored inside supplied source.'
if out.exists() and any(out.iterdir()):raise RuntimeError('Refusing to overwrite a nonempty run directory.')
out.mkdir(parents=True,exist_ok=True)
model=src/'models/ModUlaya_Fun_frost.egoml'
tree=E.parse(model);root=tree.getroot()
changes=[];inputs=[]
config={}
if args.scenario!='supplied':
    vals={'reference':[90,9,.82,.082,50,15,1,10,19.4,4.52],'conservative':[100,10,.75,.075,100,10,3,20,23,2.66],'intensive':[80,8,.95,.095,0,90,0,1,18.2,5.18]}[args.scenario]
    config=dict(zip(['v41','v42','v39','v40','v31','v32','v34','v33','v43','v44'],vals));config.update(v35=100,v37=3)
if args.realizations is not None:config['v35']=args.realizations
if args.rotations is not None:config['v37']=args.rotations
config['v28']='.yes' if args.save_maps else '.no'
if args.constants:config.update(json.loads(args.constants.read_text(encoding='utf8')))
if not args.save_maps:
    for parent in root.iter():
        for child in list(parent):
            if child.tag=='functor' and child.attrib.get('name')=='SaveMap':parent.remove(child)
if args.growth=='corrected':
    for f in root.iter('containerfunctor'):
        if any(p.attrib.get('id')=='v90' for p in f.findall('outputport')):
            expression=f.find("inputport[@name='expression']")
            changes.append({'alias':'growth v90','port':'expression','old':expression.text,'new':'corrected state logistic'})
            expression.text='[ if i2 <= 0 then 0 else if i2 >= t1[v1] then i2 else t1[v1] * i2 / (t2[v1] * t1[v1] + (1 - t2[v1]) * i2) ]'
            for child in list(f):
                if child.tag=='functor' and child.attrib.get('name')=='NumberMap' and child.findtext("inputport[@name='mapNumber']")=='1':f.remove(child)
for f in root.iter():
    if f.tag not in ('functor','containerfunctor'):continue
    typ=f.attrib['name'];alias=next((p.attrib['value'] for p in f.findall('property') if p.attrib['key']=='dff.functor.alias'),typ)
    for port in f.findall('outputport'):
        if port.attrib.get('id') in config:
            p=f.find("inputport[@name='constant']");old=p.text;p.text=str(config[port.attrib['id']]);changes.append({'alias':alias,'port':'constant','old':old,'new':p.text})
    for p in f.findall('inputport'):
        if 'peerid' in p.attrib:continue
        key=p.attrib['name'];text=(p.text or '').strip()
        if key not in ['filename','inputFilename'] and not(typ=='Folder' and key=='constant'):continue
        old=text.strip('"')
        if typ in ['LoadMap','LoadLookupTable']:
            if old=='../cosecha24.tif':new=schedule
            else:new=src/old.split('/Ulaya_mbuyuni/',1)[1]
            if not new.is_file():raise FileNotFoundError(new)
            inputs.append({'path':str(new),'sha256':hashlib.sha256(new.read_bytes()).hexdigest(),'original_reference':old})
        else:
            if typ=='Folder':new=out/'BaseScenario/Raster'
            elif old.startswith('../'):new=out/old[3:]
            else:raise ValueError(f'Unrecognized output path: {old}')
            assert new.resolve().is_relative_to(out)
            (new if typ=='Folder' else new.parent).mkdir(parents=True,exist_ok=True)
        p.text='"'+new.as_posix()+'"';changes.append({'alias':alias,'port':key,'old':old,'new':str(new)})
# Keep the program and all transformations with the run, including pinned inputs.
prepared=out/'prepared.egoml';E.indent(tree);tree.write(prepared,encoding='utf-8',xml_declaration=True)
cmd=[str(args.console),'-predefined-seed','-processors=1','-disable-parallel-steps','-log-level=4',str(prepared)]
author_calendar=src/'InRaster/cosecha24.tif'
calendar_verified=author_calendar.is_file() and hashlib.sha256(author_calendar.read_bytes()).digest()==hashlib.sha256(schedule.read_bytes()).digest()
meta={'source_model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'prepared_model_sha256':hashlib.sha256(prepared.read_bytes()).hexdigest(),'scenario':args.scenario,'growth':args.growth,'schedule_status':'author-supplied cosecha24.tif' if calendar_verified else 'explicit alternative calendar; see input checksum','inputs':inputs,'changes':changes,'command':cmd}
(out/'run_manifest.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
start=time.monotonic()
with (out/'native.log').open('w',encoding='utf8') as log:
    result=subprocess.run(cmd,cwd=out,stdout=log,stderr=subprocess.STDOUT)
elapsed=time.monotonic()-start
log=(out/'native.log').read_text(encoding='utf8',errors='replace')
meta.update(returncode=result.returncode,elapsed_seconds=elapsed,errors=[x for x in log.splitlines() if re.search(r'error|failed|exception',x,re.I) and 'Skip On Error' not in x])
(out/'run_manifest.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
print(json.dumps({k:meta[k] for k in ['scenario','returncode','elapsed_seconds','errors']},indent=2))
print(log[-3500:])
if result.returncode or meta['errors']:
    raise RuntimeError('Native execution failed; inspect native.log and run_manifest.json.')
