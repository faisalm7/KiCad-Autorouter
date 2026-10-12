"""Exact selected-public byte comparison only; no process execution."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
PUBLIC=ROOT/'evidence/pic-local-clearance-transport-001';RUN=ROOT/'.runs/pic-local-clearance-transport-001'
manifest=json.loads((PUBLIC/'files.json').read_text());copied=0;size=0
for rel,pin in manifest.items():
    raw=(PUBLIC/rel).read_bytes()
    assert len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
    if rel in ('PUBLIC_SCOPE.md','root-readback.json'):continue
    if rel.startswith('_licenses/'):source=ROOT/'.data/boards/kicad-pic-programmer'/rel
    elif rel in ('pic-local-clearance-transport-001-command.log','pic-local-clearance-transport-001-execution.json','run-pic-local-clearance-transport-001.py'):source=ROOT/'.runs'/rel
    else:source=RUN/rel
    assert raw==source.read_bytes()
    copied+=1;size+=len(raw)
readback=json.loads((PUBLIC/'root-readback.json').read_text())
audit=json.loads((OUT/'actual-audit.json').read_text())
assert readback=={'passed':True,'summary_sha256':audit['summary_sha256'],'comparison_rederived':True,'runtime_unchanged':True,'frozen_evidence_verified':70,'complete_run_files':audit['raw_run_files'],'no_native_rerun':True}
result={'passed':True,'public_manifest_sha256':hashlib.sha256((PUBLIC/'files.json').read_bytes()).hexdigest(),
    'manifest_entries':len(manifest),'total_bytes':sum(p['bytes'] for p in manifest.values()),
    'raw_copies_verified':copied,'raw_copy_bytes':size,'metadata_entries_verified_separately':{'PUBLIC_SCOPE.md':manifest['PUBLIC_SCOPE.md']['bytes'],'root-readback.json':manifest['root-readback.json']['bytes']},'root_readback_claims_match_independent_audit':True,'root_readback_copy_claim':False}
(OUT/'actual-public.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
