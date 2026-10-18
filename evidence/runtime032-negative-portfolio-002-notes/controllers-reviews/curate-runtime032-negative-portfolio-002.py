"""Retain the bounded regression and next diagnostic prerequisite; reuse helpers."""
from pathlib import Path
import ast,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
notes=ROOT/'evidence/runtime032-negative-portfolio-002-notes';assert not notes.exists()
refs={};files=[];material=[];total=0
for name in ('runtime032-native-controls-001','runtime030-native-workflow-qualification-001','runtime022-thermal-export-control-001'):
 data=f.read_json(ROOT/('evidence/'+name+'.json'));index=ROOT/data['files_index']['path'];assert p.sha(index)==data['files_index']['sha256'];idx=f.read_json(index)
 for row in idx.get('files',[])+idx.get('material',[]):refs.setdefault(row['sha256'],row.get('path',row.get('retained')))
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
functions=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','tree','cost')];assert len(functions)==3
exec(compile(ast.Module(body=functions,type_ignores=[]),str(helper),'exec'))
base=ROOT/'.runs/runtime032-v2-portfolio-negative-002';plan=f.read_json(base/'protocol.json');out=Path(plan['output'])
enclosure=f.read_json(base/'enclosure/result.json');result=f.read_json(out/'result.json');summary=f.read_json(Path(plan['portfolio_output'])/'portfolio-summary.json')
assert enclosure['passed'] and result['controls_passed'] and not result['workflow_delivered']
assert summary['status']=='no_valid_candidate' and summary['selected'] is None and summary['all_variants_attempted']
assert all(row['validated_rejection'] and not row['eligible'] for row in summary['trials'])
tree(base,Path('enclosure'));tree(out,Path('control'))
for n,path in enumerate(plan['material_roots']):tree(Path(path),Path('material')/str(n))
for name in ('runtime032-v2-portfolio-negative-002-time.log','runtime032-v2-portfolio-negative-002-controller.log','freeze-runtime032-negative-portfolio-002.py','freeze-runtime032-negative-portfolio-002.log','freeze-runtime032-negative-portfolio-002-authoring-original.py','freeze-runtime032-negative-portfolio-002-preflight-failure.json','ordinary-standard-negative-review-001.json','ordinary-standard-negative-targeted-001.log','ordinary-standard-negative-targeted-001-time.log','current-method-negative-contract-review-001.json'):
 retain(ROOT/'.runs'/name,Path('controllers-reviews')/name)
retain(Path(__file__),Path('controllers-reviews')/Path(__file__).name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
record=dict(schema=1,kind='runtime032-negative-portfolio-budget-regression-and-next-diagnostic-prerequisite',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project_complete=False,accepted=False,production_admitted=False,actual_GUI=False,human_review=False,
 runtime=plan['runtime'],source_head=plan['source_head'],runtime_manifest_sha256=plan['runtime_manifest_sha256'],administration_head=plan['administration_head'],administration_files_sha256=plan['administration_files_sha256'],protocol_sha256=p.sha(base/'protocol.json'),
 passed=True,status='no_valid_candidate',workflow_delivered=False,selected=None,all_variants_attempted=True,Native_counts=[[row['native'][key] for key in ('opens','blocking','warnings','exclusions')] for row in summary['trials']],
 complete_cost=cost(ROOT/'.runs/runtime032-v2-portfolio-negative-002-time.log'),inner_sample=dict(wall_seconds=summary['wall_seconds'],CPU_seconds=summary['total_cpu_seconds'],cap=420),method_sample=dict(wall_seconds=result['method_wall_seconds'],CPU_seconds=result['method_full_CPU_seconds'],cap=450),whole_cap=600,
 decision='Integrate API-only removal of three redundant generic negative replay rounds. All three actual Native attempts still reject and no candidate is selected/accepted/exported. Unchanged source/tools/settings/420route450method600whole120export/balanced30+15 reserves; complete current exit fits. Prior failed001 retained, not overwritten or converted into a win. No routing completion gain or general speed claim.',
 previous_failure='evidence/runtime032-native-controls-001.json',
 next_diagnostic=dict(implemented=True,Native_qualified=False,pipeline_sha256='8a0276c178649ff76383865e125c63803a71a15b144ac29905a0c072c67480af',test_sha256='6f22b7bca06ea259094d148e934d9c5f6cfb109b2153a9d488e843652014a37b',focused_tests=66,focused_complete_cost=cost(ROOT/'.runs/ordinary-standard-negative-targeted-001-time.log'),scope='Explicit ordinary_profile standard|tuned expectation for non-admitting completed-negative diagnostics, defaulttuned. Context remains own authority; selected7 scope, positive/export admission and all semantic/Native/process/resource/source/material guards unchanged. Software fixtures and AI review only; current product032 is immutable. Full integration, new build and actual ordinary CLI standard negative remain required.'),
 source_rights=plan['source_rights'],accounting='Complete349.91wall412.21CPU exit includes all invocations/finalization/diagnostics. Stored inner/method samples omit later tails, do not sum nested values. Prior failed371.91/435.31 plus software/research/review/authoring/preparation/curation additional; unknown interactive CPU notzero. Decimal-only failed preflight occurred before mkdir/Native and is retained.',
 remaining=['New diagnostic prerequisite full integration and actual default CLI negative','Current installed default/optional vsstock/corrected/competentB2 fairmatrix, broader unrelated families/untouched confirmation','CurrentGUI/WindowsNative-equivalent safeguards/cleanOS-relocation-standalone','Newtargetrestoration headroom and authorized human/cleanup/physicalvalidation/separateformalpublication'],
 backup_scope='Essential public licensed proof and source checkpoint; new full raw remains on this Mac outside008/010. No new full restoration or release completion.',files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
p.save_json(ROOT/'evidence/runtime032-negative-portfolio-002.json',record)
print(json.dumps(dict(files=len(files),bytes=total,material=len(material),passed=True,routing_gain=False)))
