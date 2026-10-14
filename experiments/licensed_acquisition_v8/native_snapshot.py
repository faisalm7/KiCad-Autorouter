"""Capture every exact acquired CP2102 source path; no writes, fetches or notices added."""
from pathlib import Path
from experiments.licensed_acquisition_v1 import fetch as shared
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
RECEIPT='.runs/licensed-acquisition-011-run-001/receipt.json'
RECEIPT_SHA256='4518d5eeefc512a60d6517096151a871d9a99cfa72bf4b2eca78bbe37c6748fd'
def capture(root=ROOT):
    root=Path(root);source=shared.contained(root,root/'.data/expansion011/cp2102-uart')
    _,_,rows=shared.load(root/'experiments/licensed_acquisition_v8','v8')
    receipt_path=shared.contained(root,root/RECEIPT);receipt_raw=shared.bounded(receipt_path)
    if shared.sha(receipt_raw)!=RECEIPT_SHA256:raise ValueError('fixed CP2102 acquisition receipt changed')
    receipt=shared.decode(receipt_raw)
    if (receipt['status']!='acquired_unqualified' or receipt['protocol_sha256']!=shared.profile('v8')['protocol_sha256']
            or receipt['original_inputs_unchanged'] is not True or receipt['acquired_files']!=5 or receipt['acquired_bytes']!=347566):
        raise ValueError('fixed complete CP2102 acquisition required')
    acquired={row['source_path']:row for row in receipt['files']}
    if len(rows)!=5 or len(acquired)!=5 or set(acquired)!={row['source_path'] for row in rows}:raise ValueError('exact CP2102 source population required')
    expected={name:{'bytes':row['bytes'],'sha256':row['sha256']} for name,row in acquired.items()}
    before=shared.inventory(source)
    if before['files']!=expected or before['directories']!=[] or before['bytes']!=347566:raise ValueError('exact original five-file CP2102 source required')
    files={name:shared.bounded(source/shared.safe(name)) for name in expected}
    for row in rows:
        if shared.payload(row,files[row['source_path']])!=expected[row['source_path']]:raise ValueError('CP2102 source differs from prospective/acquired pins')
    shared.inventory(source,before)
    if shared.sha(shared.bounded(receipt_path))!=RECEIPT_SHA256:raise ValueError('CP2102 receipt changed during capture')
    return files
# Root-level PCB already shares its directory with exact LICENSE/README.
# All five originals (PCB/project/schematic, LICENSE and README) stay exact.
