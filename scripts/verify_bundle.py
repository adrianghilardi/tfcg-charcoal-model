"""Verify all files in an extracted case-study bundle before running."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('folder',type=Path);a=p.parse_args()
m=json.loads((a.folder/'bundle_manifest.json').read_text(encoding='utf8'))
for r in m['files']:
    f=(a.folder/r['path']).resolve()
    if not f.is_relative_to(a.folder.resolve()):raise ValueError('Manifest path escapes bundle.')
    if hashlib.sha256(f.read_bytes()).hexdigest()!=r['sha256']:raise ValueError(f'Checksum mismatch: {f}')
print(f'PASS: {len(m["files"])} checksummed files')
