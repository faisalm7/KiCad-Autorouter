"""Capture exact original paths plus bounded derived notice copies; never writes."""
from pathlib import Path
from experiments.licensed_acquisition_v1 import fetch as shared
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
COPIES={'KiCad/_licenses/creator/LICENSE':'LICENSE','KiCad/_licenses/creator/README.md':'README.md'}
def capture(root=ROOT):
    root=Path(root);source=shared.contained(root,root/'.data/expansion006/devobordo')
    plan,_,rows=shared.load(Path(__file__).absolute().parent,'v3')
    before=shared.inventory(source)
    expected={row['source_path']:{'bytes':row['bytes'],'sha256':row['sha256']} for row in rows}
    if before['files']!=expected or before['directories']!=['KiCad']:raise ValueError('exact original five-file project required')
    files={name:shared.bounded(source/shared.safe(name)) for name in expected}
    for row in rows:shared.payload(row,files[row['source_path']])
    shared.inventory(source,before)
    if sum(map(len,files.values()))!=754649:raise ValueError('original census differs')
    for name,origin in COPIES.items():files[name]=files[origin]
    if sum(map(len,files.values()))!=759859:raise ValueError('derived notice copy census differs')
    return files
# ROOT materializes this finite map with existing copy_bytes into a fresh owned
# native snapshot. No .data writes, rule/board changes, aliases or model downloads.
