"""Read-only pinned ArcDice capture for an unqualified native observation.

RootMIT/README are retained. TP4056 custom-footprint origin and optional model
rights/closure remain unqualified. Capture is not managed acquisition, native
acceptance, design normalization, function proof or a routing-quality claim.
"""
from pathlib import Path
from experiments.licensed_acquisition_v1 import fetch as shared
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
SOURCE_RELATIVE='.runs/new-family-source-leads-002/source/VorosEgyes/ArcDice'
REPOSITORY='VorosEgyes/ArcDice'
COMMIT='5908d99db1ef98b5996b380c75e5aee8bb8caaa6'
DIRECTORIES=['hardware']
TOTAL_BYTES=595341
ROWS=({'source_path': 'LICENSE', 'bytes': 1067, 'sha256': '13aa5751cc47416650ad3c976d1c001f32ca3b3d49caac777ae66e819a437298', 'git_blob_sha1': '9d4599da9dcec69bb6e4c6cdc867aacbfbd77cdd'}, {'source_path': 'README.md', 'bytes': 2930, 'sha256': '876a106e288ec606cf29239d6129d07b79a134005769ba50ef0d450622c1751b', 'git_blob_sha1': '09720df73a14f8f037486dc49d815ade7312083f'}, {'source_path': 'hardware/ArcDice.kicad_pcb', 'bytes': 488060, 'sha256': '098e90725279e698f61d7f4a5f0281202ba32f655b9c430047c019783a60bf96', 'git_blob_sha1': '4efafcc2ce836ba6414e48197c305ac6fe458aa1'}, {'source_path': 'hardware/ArcDice.kicad_pro', 'bytes': 17925, 'sha256': 'be12f193331f3091ef31b9df28dc968119be56269adddcd5b2ed2921523223f6', 'git_blob_sha1': '53d28b286d88e0a1919bee83b70b2afa3f71f7ff'}, {'source_path': 'hardware/ArcDice.kicad_sch', 'bytes': 85359, 'sha256': '388bb0410c3372c2331c84b44ba8a45e10c4b34206a3b28b65cb90057129e4de', 'git_blob_sha1': 'aa3407c4d469eac8323872f13dcec2d980ceb7b3'})

def capture(root=ROOT):
    """Return all five unchanged original relative paths as immutable bytes."""
    root=Path(root).absolute();source=shared.contained(root,root/shared.safe(SOURCE_RELATIVE))
    expected={r['source_path']:{'bytes':r['bytes'],'sha256':r['sha256']} for r in ROWS}
    wanted={'schema':1,'files':expected,'directories':DIRECTORIES,'file_count':5,'bytes':TOTAL_BYTES}
    before=shared.inventory(source,wanted)
    if before['files']!=expected or before['directories']!=DIRECTORIES:
        raise ValueError('exact original five-file ArcDice source inventory required')
    files={n:shared.bounded(shared.contained(source,source/shared.safe(n))) for n in expected}
    for row in ROWS:shared.payload(row,files[row['source_path']])
    shared.inventory(source,before)
    if len(files)!=5 or sum(map(len,files.values()))!=TOTAL_BYTES:
        raise ValueError('original ArcDice source census differs')
    return files
