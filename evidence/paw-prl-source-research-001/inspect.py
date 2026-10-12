"""Read pinned source/retained PAW metadata only; no build/native/Git actions."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
COMMIT='0feeca2a807f428ad2b3fa7c1e39625cb769f02c'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=read(OUT/'source-receipt.json')
assert receipt['commit']==COMMIT and receipt['bytes']==311654
for row in receipt['files']:
 p=OUT/'source'/row['path'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
rows=[]
for folder,name in [('support-scope-review-001','pcbnew/pcbnew_jobs_handler.cpp'),('placement-area-native-failure-review-001','pcbnew/zone_filler.cpp')]:
 base=ROOT/'.runs'/folder;prior=base/'source-receipt.json';record=read(prior)
 selected=next(x for x in record['files'] if x.get('path')==name and x.get('sha256'))
 assert COMMIT in selected['url'] and sha(base/'source'/name)==selected['sha256']
 rows.append({'path':str((base/'source'/name).relative_to(ROOT)),'receipt':str(prior.relative_to(ROOT)),'receipt_sha256':sha(prior),'url':selected['url'],'sha256':selected['sha256'],'bytes':(base/'source'/name).stat().st_size})
 if name=='pcbnew/zone_filler.cpp':assert sha(OUT/'source'/name)==selected['sha256']
base=ROOT/'.runs/lipo-export-failure-research-001';meta=base/'scripting-directory.json';name='pcbnew/python/scripting/pcbnew_scripting_helpers.cpp'
entry=next(x for x in read(meta) if x['path']==name);raw=(base/'source'/name).read_bytes()
assert entry['size']==len(raw) and entry['sha']==hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() and COMMIT in entry['download_url']
rows.append({'path':str((base/'source'/name).relative_to(ROOT)),'receipt':str(meta.relative_to(ROOT)),'receipt_sha256':sha(meta),'url':entry['download_url'],'sha256':sha(base/'source'/name),'bytes':len(raw),'git_blob_sha1':entry['sha']})
(OUT/'cached-source-bindings.json').write_text(json.dumps({'files':rows,'cached_zone_filler_equals_fresh_pinned_download':True},indent=2)+'\n')
original=ROOT/'.data/expansion005/paw3395/paw3395.kicad_prl'
changed=ROOT/'.runs/paw3395-native-diagnostic-001/original-drc-input/paw3395.kicad_prl'
a,b=read(original),read(changed)
assert 'prototype_zone_fills' not in a['board'] and b['board']['prototype_zone_fills'] is False
assert a['board']['auto_track_width'] is b['board']['auto_track_width'] is True
prl=(OUT/'source/common/project/project_local_settings.cpp').read_text()
zone=(OUT/'source/pcbnew/zone_filler.cpp').read_text()
assert '"board.prototype_zone_fills", &m_PrototypeZoneFill, false' in prl
assert 'aZone->GetFillMode() == ZONE_FILL_MODE::HATCH_PATTERN' in zone and '|| !m_board->GetProject()->GetLocalSettings().m_PrototypeZoneFill' in zone
facts={'schema':1,'source_commit':COMMIT,'fresh_files':5,'fresh_bytes':311654,'source_hash_checks_passed':True,
 'prl_can_affect_copper_fill':True,'cli_refill_uses_same_zone_filler':True,'whole_prl_is_not_ui_only':True,
 'paw_original_prl_sha256':sha(original),'paw_drc_prl_sha256':sha(changed),'paw_prototype_before':'absent; pinned parameter default false','paw_prototype_after':False,'paw_prototype_effective_value_preserved_by_declared_default':True,
 'missing_false_equivalence_is_source_inference_not_native_field_observation':True,
 'source_locations':{'default':'common/project/project_local_settings.cpp:208','header':'include/project/project_local_settings.h:133','zone_fill':'pcbnew/zone_filler.cpp:2811','cli_refill':'pcbnew/pcbnew_jobs_handler.cpp:2404','headless_fill':'pcbnew/tools/zone_filler_tool.cpp:122','display_apply':'pcbnew/pcb_edit_frame.cpp:1928','migration':'common/project/project_local_settings.cpp:450'},
 'proposed_scope':'Only fixed typed PAW001 migration under pinned source/PRL before+after hashes; retain strict generic existing-PRL rejection. Do not treat PRL as inert or discard it.',
 'new_native_execution':False,'routing_or_format_qualified':False}
(OUT/'findings.json').write_text(json.dumps(facts,indent=2)+'\n')
print(json.dumps({k:facts[k] for k in ('source_hash_checks_passed','fresh_files','fresh_bytes','prl_can_affect_copper_fill','paw_prototype_effective_value_preserved_by_declared_default','new_native_execution')}))
