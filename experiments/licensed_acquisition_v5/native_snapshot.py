"""Capture exact selected original paths and derived license notices; no writes."""
from pathlib import Path
from experiments.licensed_acquisition_v1 import fetch as shared
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
COPIES={'src/_licenses/creator/LICENSE.md':'LICENSE.md','src/_licenses/creator/README.md':'README.md'}
DIRECTORIES=['src','src/footprints','src/footprints/usb_led.pretty']
def capture(root=ROOT):
    root=Path(root);source=shared.contained(root,root/'.data/expansion008/nus-usb-led')
    _,_,rows=shared.load(Path(__file__).absolute().parent,'v5')
    before=shared.inventory(source)
    expected={row['source_path']:{'bytes':row['bytes'],'sha256':row['sha256']} for row in rows}
    if before['files']!=expected or before['directories']!=DIRECTORIES:raise ValueError('exact original nine-file project required')
    files={name:shared.bounded(source/shared.safe(name)) for name in expected}
    for row in rows:shared.payload(row,files[row['source_path']])
    shared.inventory(source,before)
    if sum(map(len,files.values()))!=146916:raise ValueError('original census differs')
    for name,origin in COPIES.items():files[name]=files[origin]
    if sum(map(len,files.values()))!=156713:raise ValueError('derived notice copy census differs')
    return files
# ROOT uses existing exclusive copy_bytes into a fresh owned native snapshot.
# The original src/ paths satisfy KIPRJMOD local-footprint URI resolution.
# All copper-pour restrictions/knockout text/rules/model references remain exact.
