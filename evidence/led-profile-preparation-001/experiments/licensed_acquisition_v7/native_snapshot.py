"""Exact immutable LED capture and notice copies; no writes or cache fallback."""
from pathlib import Path
from experiments.licensed_acquisition_v1 import fetch as shared
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
COPIES={'_licenses/creator/LICENSE':'LICENSE','_licenses/creator/README.md':'README.md'}
DIRECTORIES=[]
def capture(root=ROOT):
    root=Path(root);source=shared.contained(root,root/'.data/expansion010/push-button-led')
    _,_,rows=shared.load(Path(__file__).absolute().parent,'v7');before=shared.inventory(source)
    expected={r['source_path']:{'bytes':r['bytes'],'sha256':r['sha256']} for r in rows}
    if before['files']!=expected or before['directories']!=DIRECTORIES:raise ValueError('exact original five-file LED project required')
    files={n:shared.bounded(source/shared.safe(n)) for n in expected}
    for row in rows:shared.payload(row,files[row['source_path']])
    shared.inventory(source,before)
    if len(files)!=5 or sum(map(len,files.values()))!=161071:raise ValueError('original LED census differs')
    for dest,origin in COPIES.items():files[dest]=files[origin]
    if len(files)!=7 or sum(map(len,files.values()))!=165201:raise ValueError('LED notice copy census differs')
    return files
# ROOT materializes with existing exclusive copy_bytes into a fresh native packet.
# OriginalPCB/pro/SCH, LICENSE/README, model references, rules/classes/fields stayexact.
