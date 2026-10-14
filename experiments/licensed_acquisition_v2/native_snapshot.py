"""Capture every exact acquired PAW source path; no writes, fetches or notices added."""
from pathlib import Path
from experiments.licensed_acquisition_v1 import fetch as shared
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
RECEIPT='.runs/licensed-acquisition-005-run-001/receipt.json'
RECEIPT_SHA256='370f1c09157a7090fb725018bd7fa3ebb3d184d9163c1ee807110c674f2ac629'
def capture(root=ROOT):
    root=Path(root);source=shared.contained(root,root/'.data/expansion005/paw3395')
    _,_,rows=shared.load(root/'experiments/licensed_acquisition_v2','v2')
    receipt_path=shared.contained(root,root/RECEIPT);receipt_raw=shared.bounded(receipt_path)
    if shared.sha(receipt_raw)!=RECEIPT_SHA256:raise ValueError('fixed PAW acquisition receipt changed')
    receipt=shared.decode(receipt_raw)
    if (receipt['status']!='acquired_unqualified' or receipt['protocol_sha256']!=shared.profile('v2')['protocol_sha256']
            or receipt['original_inputs_unchanged'] is not True or receipt['acquired_files']!=14 or receipt['acquired_bytes']!=2163350):
        raise ValueError('fixed complete PAW acquisition required')
    acquired={row['source_path']:row for row in receipt['files']}
    if len(rows)!=14 or len(acquired)!=14 or set(acquired)!={row['source_path'] for row in rows}:raise ValueError('exact PAW source population required')
    expected={name:{'bytes':row['bytes'],'sha256':row['sha256']} for name,row in acquired.items()}
    before=shared.inventory(source)
    if before['files']!=expected or before['directories']!=['paw3395_pcb.pretty'] or before['bytes']!=2163350:raise ValueError('exact original14-file PAW source required')
    files={name:shared.bounded(source/shared.safe(name)) for name in expected}
    for row in rows:
        if shared.payload(row,files[row['source_path']])!=expected[row['source_path']]:raise ValueError('PAW source differs from prospective/acquired pins')
    shared.inventory(source,before)
    if shared.sha(shared.bounded(receipt_path))!=RECEIPT_SHA256:raise ValueError('PAW receipt changed during capture')
    return files
# Root-level PCB already shares its directory with exact LICENSE/README.
# All fourteen originals (including PRL/media/toolkit JSON/local footprint) stay.
