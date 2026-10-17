"""Preserve each actual0174Cu delivery proof; no Native or full-checker reexecution."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx
base=ROOT/'.runs/runtime-directory-017';runtime=base/'runtime';out=runtime/'.runs/production-delivery-001';outer_path=base/'production-delivery-execution-001/result.json';outer=f.read_json(outer_path)
child_path=out/'result.json';raw=child_path.read_bytes();child=f.read_json(child_path)
assert p.sha(child_path)==outer['child_receipt_sha256']=='1024f98ad198993005f59f75e848f265b991fdd000b436649556b29800ca4191'and len(raw)==outer['child_receipt_bytes']
assert outer['passed']is child['passed']is True and outer['status']==child['status']=='completed'and outer['child']==child
assert outer['process']['exit_code']==0 and not outer['process']['cancel_requested']and not outer['process']['log_truncated']
assert len(child['processes'])==6 and all(row['exit_code']==0 and not row['cancel_requested']and not row['log_truncated']for row in child['processes'])
protocol=base/'production-delivery-protocol-frozen-001.json';assert p.sha(protocol)==outer['protocol_sha256']=='8cd2e96a439ecf3e3dd78ad6e4d947a86e71ab6ef2eb58c4c07d3cf04e6e1176'
plan=f.read_json(protocol);work=Path(child['workspace']);route=f.read_json(work/'route/result.json');export=f.read_json(work/'export/export.json')
assert p.sha(work/'route/result.json')==child['route_sha256']and p.sha(work/'export/export.json')==child['export_sha256']
source=Path(route['source']);original=sx.read(source);protected=p.protected_for_record(route,original)
assert p.tree_hash(source.parent)==plan['fixture_sha256']==child['source_sha256']and len(protected)==10
assert child['checked_export']['current']is True and route['native_edge_admission_policy']=='known-named-whole-native-edge-v1'
assert child['native_edge_correction']['applied']is False and child['native_edge_correction']['reason']=='named class clearance exceeds exact inherited edge scope'
for item,data,folder in[(child['own_candidate_native'][0],route,work/'route'),(child['own_candidate_native'][1],export,work/'export/validation')]:
 candidate=Path(data['candidate']);tree=sx.read(candidate)
 assert p.sha(candidate)==data['candidate_sha256']==item['candidate_sha256']
 assert p.immutable(tree)==p.immutable(original)and all(row in p.routes(tree)for row in protected)
 assert data['native']==item['native']and [data['native'][key]for key in('opens','blocking','warnings','exclusions')]==[0,0,6,0]
 assert data['native']['ignored_checks']==plan['expected_ignored_checks']and data['schematic_parity']=='checked by final native DRC'
 assert p.sha(folder/'final-drc.json')==item['final_native_sha256']and p.sha(folder/'final-netclasses.json')==item['map_sha256']
 assert f.read_json(folder/'final-netclass-audit.json')==item['class_audit']
 assert data['metrics']==item['metrics']and data['metrics']['copper_layers']==4 and data['metrics']['zones']==3
text=(ROOT/'.runs/runtime017-production-execution-001-time.log').read_text()
nums={key:float(value)for key,value in re.findall(r'^(real|user|sys) ([0-9.]+)$',text,re.M)}
assert set(nums)=={'real','user','sys'}and max(nums['real'],nums['user']+nums['sys'])<=260
review=ROOT/'.runs/runtime017-production-actual-review-001.json';reviewrow=f.read_json(review)
assert reviewrow.get('material_findings')==[] and reviewrow.get('Native_executed')is False
notes=ROOT/'evidence/runtime017-production-CLI-delivery-001-notes';notes.mkdir();rows=[]
def copy(path,relative):
 raw=path.read_bytes();assert not path.is_symlink()and len(raw)<4*1024**2 and b'\0'not in raw;raw.decode()
 relative=Path(*('owned-run-evidence'if component=='.runs'else component for component in relative.parts))
 target=notes/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 rows.append(dict(path=str(target.relative_to(ROOT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
for label,folder in [('workflow',out),('enclosure',outer_path.parent)]:
 for path in sorted(folder.rglob('*')):
  if path.is_file()and not(set(path.relative_to(folder).parts)&{'kicad-cache','kicad-config','kicad-documents','engine-config','tmp'}):copy(path,Path(label)/path.relative_to(folder))
for name in('qualify-runtime017-production-001.py','run-runtime017-production-001.py','runtime017-production-actual-review-001.json','runtime017-production-execution-001-command.log','runtime017-production-execution-001-time.log'):
 copy(ROOT/'.runs'/name,Path('controllers')/name)
copy(protocol,Path('controllers/production-delivery-protocol-frozen-001.json'))
record=dict(schema=1,kind='actual-runtime017-protected-four-cu-production-CLI-delivery-v1',accepted=False,passed=True,Native_executed=True,actual_GUI=False,human_review=False,
 source_head=plan['source_head'],qualified_source_commit=plan['qualified_source_commit'],preflight_checkpoint='d0689bdfe8f43970edbd6d4055f0cfaaf2e02de7',protocol_sha256=p.sha(protocol),
 whole_wall_seconds=nums['real'],whole_full_cpu_seconds=round(nums['user']+nums['sys'],8),whole_user_cpu_seconds=nums['user'],whole_system_cpu_seconds=nums['sys'],
 inner_enclosure_sample_wall_seconds=outer['inner_sample_wall_seconds'],inner_enclosure_sample_full_cpu_seconds=outer['inner_sample_full_cpu_seconds'],
 inner_child_sample_wall_seconds=child['inner_sample_wall_seconds'],inner_child_sample_full_cpu_seconds=child['inner_sample_full_cpu_seconds'],
 workflow=['preview','route','rendered review','software accept intent','fresh Native export','current export check'],own_candidate_native=child['own_candidate_native'],protected_routes=10,
 original_source_sha256=child['source_sha256'],original_source_unchanged=True,original_design_unchanged=True,native_edge_correction=child['native_edge_correction'],whole_project_drc_clean=False,source_review=reviewrow,
 caveats=['One fresh017 installed current workflow on the same exposed owned4Cu family; no repeat016/pair001/importer004/threshold006. No new family, completion/quality/speed or C-over-B2 claim.',
 'Only pipeline differs from016, other43runtime modules exact. Actual six shipped CLI stages use the GUI model; no actual new GUI qualification or human approval. Same pinned Mac/apps/cache/fixed path, no relocation/standalone/clean-OS claim.',
 'Every Route/export final has its own actual saved refill/fullSCH/class/dimension/original proof. Zeroopens/zeroblocking with sixwarnings/twoignored/zeroexclusions is not whole-project cleanliness or electrical suitability.',
 'Original unusedCRITICAL0.5mm exceedsedge0.3mm, so input-specific named correction remains unapplied. No original requirement was changed to force admission.',
 'Whole external command counts all conversion/attempt/validation/preview/selection/export/final readback/publication/exit costs. Inner samples are separately labeled. Research/authoring/AIreview/preparation/curation costs are separate and not zero.',
 'Current017failure-controls and actualGUI remain pending at this record. Prior013 negatives stay separately scoped. Cooperative process/ownership controls do not certify hostile same-user resistance or permanent descendant absence.'],files=rows)
(ROOT/'evidence/runtime017-production-CLI-delivery-001.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(passed=True,files=len(rows),bytes=sum(row['bytes']for row in rows),Native_reexecuted=False,whole_wall_seconds=nums['real'],whole_full_cpu_seconds=nums['user']+nums['sys'])))
