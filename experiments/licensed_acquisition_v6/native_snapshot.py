"""Read-only exact clock capture; complete hierarchy and notice copies retained."""
from pathlib import Path
from experiments.licensed_acquisition_v1 import fetch as shared
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
COPIES={'hardware/_licenses/creator/LICENSE-HARDWARE':'LICENSE-HARDWARE','hardware/_licenses/creator/README.md':'README.md'}
DIRECTORIES=['hardware']
def capture(root=ROOT):
    root=Path(root);source=shared.contained(root,root/'.data/expansion009/als311-clock')
    _,_,rows=shared.load(Path(__file__).absolute().parent,'v6');before=shared.inventory(source)
    expected={r['source_path']:{'bytes':r['bytes'],'sha256':r['sha256']} for r in rows}
    if before['files']!=expected or before['directories']!=DIRECTORIES:raise ValueError('exact original ten-file clock project required')
    files={n:shared.bounded(source/shared.safe(n)) for n in expected}
    for row in rows:shared.payload(row,files[row['source_path']])
    shared.inventory(source,before)
    if len(files)!=10 or sum(map(len,files.values()))!=741742:raise ValueError('original clock census differs')
    for dest,origin in COPIES.items():files[dest]=files[origin]
    if len(files)!=12 or sum(map(len,files.values()))!=753605:raise ValueError('notice copy census differs')
    return files
# ROOT materializes with shared copy_bytes in a fresh owned native snapshot.
# Original hardware/NOTICE remains besidePCB/pro; all5SCH, model/customFP
# declarations, project rules, geometry and original root notices remain exact.
