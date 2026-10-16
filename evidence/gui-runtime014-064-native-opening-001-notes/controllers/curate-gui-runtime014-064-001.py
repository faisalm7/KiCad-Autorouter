"""Reuse central readers and the retained complete pre-open snapshot; no Native/GUI rerun."""
from pathlib import Path
import hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[1];runtime=ROOT/'.runs/runtime-directory-014/runtime';sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,review_export as ex,placement_clearance as pc,schematic_class_evidence as classes,schematic_classes as comparator
base=runtime/'.runs/gui-session064';work=base/'jobs/autorouter-gui-1a2ccd64e1244fff9349710285e68401'
launch=f.read_json(base/'launch.json');pre=f.read_json(base/'preopen-001.json');snapshot=Path(pre['snapshot']);tools=p.tool_manifest()
assert tools['git_head']==launch['source_git_head']=='523440c609543235c9982858911d5828790a52fd'
source=Path(launch['source']);assert p.tree_hash(source.parent)==launch['source_sha256']
assert p.tree_hash(snapshot)==pre['snapshot_hashes'] and len(pre['snapshot_hashes'])==106
assert pre['route']['current']is True and pre['export']['current']is True and pre['human_review']is False
route=f.read_json(work/'route/result.json');export=f.read_json(work/'export/export.json')
assert p.check_result(work/'route/result.json')['current']is True
assert p.sha(work/'export/export.json')==pre['snapshot_hashes']['export.json']
try:ex.check_export(work/'export/export.json')
except p.Rejected as exc:stale=str(exc)
else:raise AssertionError('opened export unexpectedly current')
assert stale=='export inputs/runtime/evidence changed'
assert route['accepted']is True and export['export_accepted']is True and route['tools']==export['tools']==tools
original=p.sx.read(source);protected=p.protected_for_record(route,original);assert len(protected)==10
for candidate in (Path(route['candidate']),Path(export['candidate'])):
 tree=p.sx.read(candidate);assert p.immutable(original)==p.immutable(tree)and all(r in p.routes(tree)for r in protected)
assert p.sha(Path(export['candidate']))==export['candidate_sha256']
native=[]
for label,folder,data in [('route',work/'route',route),('export',work/'export/validation',export)]:
 stages={}
 for stage in ('refill-drc','final-drc'):
  binding=f.read_json(folder/(stage+'-binding.json'))
  stages[stage]=f.check_drc_stage(folder,data,stage,Path(binding['source']),Path(binding['input']),binding['saved'],binding['before'],schematic_parity=stage=='final-drc',sandboxed=label=='export')
 assert stages['final-drc']==data['native'] and p.native_accepted(data['native'])
 assert [data['native'][k]for k in('opens','blocking','warnings','exclusions')]==[0,0,6,0]and len(data['native']['ignored_checks'])==2
 candidate=Path(data['candidate']);packet=candidate.parent if label=='route'else snapshot/'validation/candidate'
 if label=='route':
  proof=classes.check(folder,data,'final',board_raw=pc.read_bytes(packet/candidate.name),source=str(candidate),project_raw=pc.read_bytes(packet/candidate.with_suffix('.kicad_pro').name),schematic_raw=pc.read_bytes(packet/candidate.with_suffix('.kicad_sch').name),native_map=folder/'final-netclasses.json')
  assert proof['qualification']['class_parity_qualified']is True
  class_scope='Current complete central/class replay; original companions unchanged.'
 else:
  # The central reader before opening is retained in the complete hashed
  # snapshot. Current companions deliberately refuse after KiCad normalization.
  # Reuse only the pure historical comparator here; never relabel this current.
  proof=f.read_json(snapshot/'validation/final-classes-proof.json')
  q=comparator.derive(pc.read_bytes(snapshot/'validation/final-classes.net'),pc.read_bytes(packet/candidate.name),pc.read_bytes(packet/candidate.with_suffix('.kicad_pro').name),pc.read_bytes(snapshot/'validation/final-netclasses.json'),source=str(candidate),schematic_source=str(folder/'final-classes-input'/candidate.with_suffix('.kicad_sch').name),schematic_raw=pc.read_bytes(packet/candidate.with_suffix('.kicad_sch').name))
  assert f.canonical(q)==f.canonical(proof['qualification'])and q['class_parity_qualified']is True
  class_scope='Complete central export/class check passed before opening and is retained in the exact106file snapshot. Pure historical class comparator rederived; current full export/class acceptance is false after companion normalization.'
 native.append(dict(label=label,stages=stages,historical_class_parity_qualified=True,class_proof_scope=class_scope))
inspections=[]
for path in sorted(work.glob('inspect-export-*.command.log')):
 d=f.read_json(path);proc=f.read_json(path.with_suffix('.process.json'))
 assert proc['exit_code']==(0 if d['current']else 2)and not proc['cancel_requested']and not proc['log_truncated']
 inspections.append(dict(current=d['current'],reason=d.get('reason'),process=proc,log_sha256=p.sha(path)))
assert len(inspections)==2 and sum(x['current']is True for x in inspections)==1
preview=f.read_json(work/'preview.command.log');review=f.read_json(work/'review/review.json');choice=f.read_json(work/'choice/choice.json')
assert preview['protected_route_items']==10 and preview['schematic_class_check']['native_validation_performed']is False
assert choice['choice']=='accept'and choice['human_pcb_approval_observed']is False and choice['applied']is False
assert review['preview']['layers']==['F.Cu','In1.Cu','In2.Cu','B.Cu']
failed=base/'jobs/autorouter-gui-e553ea8ce70a474fa6d0778bbeaa76bf';bad=f.read_json(failed/'preview.command.log');assert bad['status']=='rejected'and 'schematic class intent'in bad['reason']
assert all(t in (base/'improve-refusal-001.ax.txt').read_text() for t in ('Saved-project preview refused:',bad['reason'],'Start a fresh preview','Full failure log:','No positive state adopted.'))
assert 'KiCad must verify schematic/PCB class bindings'in(base/'route-preview-001.ax.txt').read_text()
assert 'Full failure log:'in(base/'stale-export-refusal-001.ax.txt').read_text()
cleanup=f.read_json(base/'process-cleanup-001.json');assert cleanup['still_running']==[]
notes=ROOT/'evidence/gui-runtime014-064-native-opening-001-notes';notes.mkdir();rows=[]
def copy(path,relative):
 raw=pc.read_bytes(path,4*1024**2);dest=notes/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);rows.append(dict(path=str(dest.relative_to(ROOT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
for label,folder in [('route',work/'route'),('preopen-export',snapshot),('rendered-review',work/'review')]:
 for name in pc.inventory(folder,max_bytes=64*1024**2):
  if label in {'route','rendered-review'}and set(Path(name).parts)&{'code','kicad-cache','kicad-config','kicad-documents','engine-config'}:continue
  copy(folder/name,Path(label)/name)
for path in work.glob('*.command.*'):copy(path,Path('GUI-journals')/path.name)
for path in failed.glob('*.command.*'):copy(path,Path('failed-Improve-preview')/path.name)
for name in ('launch.json','preopen-001.json','process-cleanup-001.json','improve-refusal-001.ax.txt','route-preview-001.ax.txt','route-accepted-001.ax.txt','export-accepted-001.ax.txt','export-opened-PCB-001.ax.txt','stale-export-refusal-001.ax.txt','rendered-review-content-001.ax.txt','route-started-001.ax.txt','review-ready-001.ax.txt','choice-completed-001.ax.txt','export-progress-001.ax.txt'):
 copy(base/name,Path('observations')/name)
for name in launch['source_sha256']:copy(source.parent/name,Path('source')/name)
for path in(work/'review/review.json',work/'choice/choice.json',work/'settings.json',runtime/'runtime-distribution.json'):
 copy(path,Path('records')/path.name)
for path in(ROOT/'.runs/prepare-gui-runtime014-064.py',ROOT/'.runs/prepare-runtime-directory-014.py',ROOT/'.runs/gui064-preopen-001.py',Path(__file__),ROOT/'.runs/gui064-preopen-001-command.log',ROOT/'.runs/gui064-preopen-001-time.log',ROOT/'.runs/prepare-runtime-directory-014-command.log',ROOT/'.runs/prepare-runtime-directory-014-time.log',ROOT/'.runs/runtime-directory-014/setup.json'):
 copy(path,Path('controllers')/path.name)
after=p.tree_hash(work/'export');initial=pre['snapshot_hashes'];changes=dict(added=sorted(set(after)-set(initial)),removed=sorted(set(initial)-set(after)),changed=sorted(k for k in set(after)&set(initial)if after[k]!=initial[k]));assert any(changes.values())
browser=(base/'rendered-review-content-001.ax.txt').read_text()
assert all(('before '+layer in browser and 'after '+layer in browser)for layer in review['preview']['layers'])
prior=f.read_json(ROOT/'.runs/runtime-directory-013/setup.json')['tools']['implementation_sha256']
current=tools['implementation_sha256'];assert set(prior)==set(current)and len(current)==44
changed=sorted(k for k in current if current[k]!=prior[k]);assert changed==['autorouter/gui.py']
record=dict(schema=1,kind='actual-runtime014-GUI064-specific-preview-refusal-Route-export-opening',accepted=False,actual_GUI=True,human_review=False,full_release_qualified=False,Native_executed=True,source_head=tools['git_head'],source_hashes=launch['source_sha256'],source_unchanged=True,route_export_and_checked_KiCad_PCB_opening_passed=True,preopen_snapshot_files=106,export_current=False,current_export_refusal=stale,postopen_changes=changes,own_retained_native=native,native=export['native'],metrics=export['metrics'],protected_routes=10,inspections=inspections,
 preview_refusal=dict(improve_correctly_refused=True,inline_specific_reason_present=True,actual_CLI_reason=bad['reason'],no_positive_state_adopted=True),
 runtime_comparison=dict(previous_source=prior,changed_modules=changed,unchanged_runtime_modules=43,scope='013 actual negative controls remain separate, not represented as new014 runs.'),
 observations=dict(toolbar_launch=True,closed_source_acknowledgement=True,pending_class_preview=True,standard_route=True,review_created=True,browser_AX_before_after_four_layers=True,browser_visual_rendering_observed=True,software_test_accept_intent=True,fresh_Native_export=True,checked_opening=True,actual_KiCad_exported_PCB_with_4vias_19segments_0unrouted=True,natural_stale_refusal_with_specific_reason_and_log=True,new_cancel_or_reject_intent_test=False),
 caveats=['One exposed owned4Cu family; no new independent-family, routing-quality, speedup, physical/electrical or human-review claim.','Four before/after layer pairs retained in owned browser content AX and actual Native SVG/HTML; local screenshot inspection confirmed rendering. No unrelated browser UI or private content published.','Whole interactive wall/fullCPU including idle/authoring/review unmeasured, not zero. Stage journals and Native receipts retain actual operation costs; no fabricated whole-interactive benchmark.','Complete central export/class check passed before opening and is retained in the complete106file preopen snapshot. Current companions normalized by KiCad and correctly refuse. Historical pure comparator replay is not a current full export/class pass. No repair/rebinding/reacceptance.','Only gui.py changed from013. Runtime014 has its own actual final Route/export Native proof. Broader clean/partial/plain/cancel/short and2Cu Improve013 controls explicitly belong to013 and unchanged43module basis; they did not run in014.','All known original scientific/platform/backup/external release gates remain.'],files=rows)
assert p.tree_hash(source.parent)==launch['source_sha256']and p.tree_hash(snapshot)==initial and p.tool_manifest()==tools
(ROOT/'evidence/gui-runtime014-064-native-opening-001.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(files=len(rows),bytes=sum(r['bytes']for r in rows),GUI_route_export_opening=True,export_current=False,specific_preview_message=True,unchanged_modules=43)))
