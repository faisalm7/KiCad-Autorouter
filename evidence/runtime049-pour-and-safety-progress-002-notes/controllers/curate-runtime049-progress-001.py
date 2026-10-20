"""Retain actual048 pilot outcomes, using existing bounded retention/report helpers.
No Native, production reader, solver, GUI, source rewrite or archive census.
"""
from pathlib import Path
import ast,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io,sexpr as sx
notes=ROOT/'evidence/runtime049-pour-and-safety-progress-001-notes';target=ROOT/'evidence/runtime049-pour-and-safety-progress-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
helpers=[('curate-runtime030-native-workflow-qualification-001.py','b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',{'retain','cost'}),('curate-gui-runtime042-081-recovery-deliveries-001.py','340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',{'read','own_final'})]
for name,digest,names in helpers:
 path=ROOT/'.runs'/name;assert p.sha(path)==digest
 module=ast.parse(path.read_text());nodes=[node for node in module.body if isinstance(node,ast.FunctionDef) and node.name in names]
 assert {n.name for n in nodes}==names
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path)+'::shared-reporting','exec'),globals())
runtime=ROOT/'.runs/runtime-directory-049/runtime';manifest=runtime/'runtime-distribution.json';M='70a388a6844d015350073401cb5f33bb1d552d1dc6195ece3aceee27baba5bd4';H='6e2357f975554478c2ba9fa35f18fdc3c1d194f9'
assert p.sha(manifest)==M
base=ROOT/'.runs/runtime049-native-qualification-001';frozen=read(base/'frozen.json');assert frozen['source_head']==H and frozen['runtime_manifest_sha256']==M
rows=[]
for entry in frozen['protocols']:
 protocol=Path(entry['protocol']);plan=read(protocol);assert p.sha(protocol)==entry['protocol_sha256'] and plan['source_head']==H and plan['runtime_manifest_sha256']==M
 folder=protocol.parent;out=Path(plan['output']);assert io.inventory(Path(plan['source']).parent)==plan['source_hashes']
 retain(protocol,Path('cases')/entry['case']/'protocol.json');retain(folder/'settings.json',Path('cases')/entry['case']/'settings.json')
 row=dict(case=entry['case'],method=entry['method'],protocol_sha256=entry['protocol_sha256'],source_hashes=plan['source_hashes'],source_unchanged=True,executed=(folder/'execution.json').exists())
 if row['executed']:
  execution=read(folder/'execution.json');child=read(out/'result.json');w=Path(child['workspace']);assert execution['child_sha256']==p.sha(out/'result.json')
  assert execution['protocol_sha256']==entry['protocol_sha256'] and execution['process']['cleanup_complete'] and not execution['process']['log_truncated']
  row.update(controls_passed=execution['controls_passed'],workflow_delivered=execution['workflow_delivered'],child_status=child['status'],child_error=child.get('error'),complete_external_cost=cost(folder/'outer-time.log'),sampled_wall_seconds=execution['complete_wall_seconds'],sampled_full_CPU_seconds=execution['complete_full_CPU_seconds'],Native_counts=execution['Native_counts'],protected_count=execution['protected_count'])
  for path in (folder/'execution.json',folder/'outer.log',folder/'outer-time.log',folder/'enclosure/process.json',out/'result.json'):
   retain(path,Path('cases')/entry['case']/path.name)
  for stage in child['processes']:retain(out/(stage['stage']+'.log'),Path('cases')/entry['case']/(stage['stage']+'.log'))
  route=read(w/'route/result.json');retain(w/'route/result.json',Path('cases')/entry['case']/'route/result.json')
  if execution['workflow_delivered']:
   assert execution['controls_passed'] and route['accepted'] and child['status']=='completed'
   ex=read(w/'export/export.json');assert ex['export_accepted'] and route['candidate_sha256']==ex['candidate_sha256']==child['candidate_sha256']
   original=sx.read(Path(plan['source']));protected=p.protected_for_record(route,original);assert len(protected)==row['protected_count']
   packets=[('parent',route,w/'route'),('export',ex,w/'export/validation')]
   if entry['method']=='improve':
    packets.append(('incumbent',read(w/'route/incumbent/result.json'),w/'route/incumbent'))
    packets.extend((t['id'],read(Path(t['receipt'])),Path(t['receipt']).parent) for t in route['trials'])
   proofs={}
   for label,data,directory in packets:
    candidate=directory/'candidate'/Path(plan['source']).name
    assert p.sha(candidate)==data['candidate_sha256'] and p.immutable(sx.read(candidate))==p.immutable(original)
    assert all(item in p.routes(sx.read(candidate)) for item in protected)
    proof=own_final(data,directory,directory,plan['source_hashes'],candidate)
    proofs[label]=dict(candidate_sha256=data['candidate_sha256'],Native_counts=[data['native'][k] for k in ('opens','blocking','warnings','exclusions')],ignored_checks=data['native']['ignored_checks'],own_final=proof)
    for name in ('result.json','final-drc.json','final-drc-binding.json','final-drc-process.json','final-netclass-audit.json','final-netclasses.json'):
     path=directory/name
     if path.is_file():retain(path,Path('cases')/entry['case']/label/name)
   retain(w/'export/export.json',Path('cases')/entry['case']/'export/export.json')
   row.update(own_finals=proofs,improvements=route.get('improvements'),trials=route.get('trials'),metrics=route['metrics'])
  else:
   assert entry['case']=='improve-pour-only' and route['status']=='incumbent_rejected' and not route['accepted']
   inc=w/'route/incumbent';d=read(inc/'result.json');assert 'unqualified named task net reference' in d['reason']
   row.update(refusal=d['reason'],source_counts=[d['source_drc'][k] for k in ('opens','blocking','warnings','exclusions')],final_native_performed=False,delivered_candidate=False)
   for name in ('result.json','refill-drc.json','refill-drc-process.json','refill-drc-binding.json','pour-dsn-correction.json'):
    retain(inc/name,Path('cases')/entry['case']/'failed-incumbent'/name)
 else:row['state']='started_not_completed' if out.exists() else 'unexecuted'
 rows.append(row)
assert rows[0]['case']=='improve-pour-only' and rows[0]['controls_passed'] is True
full=read(ROOT/'.runs/full-integration-198/execution.json');assert full['passed'] and full['sources_unchanged'] and full['process']['cleanup_complete']
for path in [manifest,runtime.parent/'preparation.json',base/'frozen.json',base/'doctor.json',base/'doctor-process.json',ROOT/'.runs/full-integration-198/execution.json',ROOT/'.runs/full-integration-198/protocol.json',ROOT/'.runs/full-integration-198/command.log',ROOT/'.runs/full-integration-198-time.log',ROOT/'.runs/runtime048-edge-review-observation-001.json',ROOT/'.runs/gui083-access-resolved-001.json',ROOT/'.runs/prepare-runtime049-001.py',ROOT/'.runs/freeze-runtime049-native-001.py',ROOT/'.runs/freeze-runtime049-controls-001.py',ROOT/'.runs/prepare-runtime049-gui085.py',Path(__file__)]:
 retain(path,Path('controllers-and-prerequisites')/path.relative_to(ROOT).as_posix().removeprefix('.runs/'))
controls=[]
for label,folder in [('invalid',ROOT/'.runs/runtime049-native-controls-001/invalid'),('cancel',ROOT/'.runs/runtime049-native-controls-003/cancel'),('reserved-return-namespace-refusal',ROOT/'.runs/runtime049-native-controls-002/reserved-return'),('reserved-return-insufficient-incumbent-budget',ROOT/'.runs/runtime049-native-controls-003/reserved-return')]:
 plan=read(folder/'protocol.json');execution=read(folder/'enclosure/result.json');child=read(Path(execution['child_receipt']))
 assert execution['process']['cleanup_complete'] and not execution['process']['log_truncated'] and execution['child_sha256']==p.sha(Path(execution['child_receipt']))
 assert plan['runtime_manifest_sha256']==M and plan['source_head']==H and p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']
 if label in ('invalid','cancel'):assert execution['passed'] and child['control_passed']
 else:assert execution['passed'] is False and child['control_passed'] is False
 row=dict(control=label,passed=execution['passed'],status=child['status'],error=child.get('error'),parent_status=child.get('parent_status'),parent_reason=child.get('parent_reason'),complete_external_cost=cost(folder/'outer-time.log'),protocol_sha256=p.sha(folder/'protocol.json'),child_sha256=execution['child_sha256'])
 if label=='invalid':row['cases']=[dict(case=c['case'],passed=c['passed'],rejection=c['rejection'],Native_counts=[c.get('native',c.get('diagnostic_native'))[k] for k in ('opens','blocking','warnings','exclusions')]) for c in child['cases']]
 if label=='cancel':row.update(parent_accepted=child['parent_accepted'],observed_owned_engine=child['observed_owned_engine'],engine_cancel_signal=child['engine_process']['cancel_signal'],engine_cleanup=child['engine_process']['cleanup_complete'],remaining_owned_group=child['remaining_owned_group'],adoption_refusal=child['adoption_refusal'],central_reader_refusal=child['central_reader_refusal'])
 controls.append(row)
 for path in [folder/'protocol.json',folder/'outer.log',folder/'outer-time.log',folder/'enclosure/result.json',Path(execution['child_receipt'])]:retain(path,Path('controls')/label/path.name)
 for key in ('controller',):retain(Path(plan[key]),Path('controllers')/Path(plan[key]).name)
for name in ('enclose-native7-independent-control-005.py','qualify-native7-reserved-return-001.py','qualify-native7-reserved-return-002.py','qualify-native7-reserved-return-003.py','qualify-runtime049-cancel-002.py','freeze-runtime049-controls-001-before-positive-path-correction.py','freeze-runtime049-controls-preparation-failure-001.json','freeze-runtime049-controls-002.log','freeze-runtime049-controls-002-time.log'):
 retain(ROOT/'.runs'/name,Path('controllers')/name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
record=dict(schema=1,kind='runtime049-qualified-pour-only-delivery-and-bounded-safety-progress-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=H,runtime_manifest_sha256=M,qualified=False,accepted=False,project_complete=False,actual_GUI=False,human_review=False,full198=dict(passed=True,tests=2451,skips=1,complete_external_cost=cost(ROOT/'.runs/full-integration-198-time.log')),cases=rows,controls=controls,repair_result='Actual formerly refused pour-only source now completes six stages with own final Native/fullSCH/original rules/source/protected1,0opens/0blocking/6warnings/0exclusions.195-ish complete seconds include all stages/selection/Native/exit; exact external194.90wall/185.68CPU. Existing048refusal remains retained, no stitched result.',scope='One completed owned combination closes the demonstrated identity seam, not general board-family/quality superiority. Remaining frozen cases are unqualified until completed. CorrectedB1 default unchanged; optional ground copper reduction is not electrical improvement.',return_limit='The one frozen40s ordinary CLI diagnostic did not produce an incumbent: after the namespace harness correction it safely refused insufficient engine grace/finalization reserves. No natural work expiry/reserved return is proved; do not tune/retry its timing to obtain a pass. GUI minimum90 unchanged. Additional prepared90s zero-removable-copper control remains unexecuted.',harness_history='Return001 static review found material/event witness gaps and was unexecuted.002 preserves the comparison-namespace refusal before any Native worker,1.80wall/1.30CPU.003 uses exact ordinary-control allowlist in shared005enclosure; no router authority/caps changed. Cancel001 remained unexecuted with same latent namespace issue. First049control-freezer path failure happened before namespace/Native; its source/error/unmeasuredCPU retained.',cancellation_limit='Actual own engine SIGINT via production CliJob, cancelled/unaccepted parent, no adopted route/review/choice/export and group absent at observation. Not actualGUI/all-phase/permanent-descendant/kill/power-loss proof.',GUI='042lastactualGUI;048EdgeCLI-reviewpaint observed separately.049GUI085helper remains prospective until its own ordinary-alias/fractional Native prerequisites. No access/lock/security action pending; useEdge and advertisedRaise. No old-role transfer.',next='Continue exact remaining frozen049 cases sequentially, then additional90s no-trial incumbent return and actual current GUI/queued-staleness/recovery. Preserve every final candidate proof and failed/unexecuted outcome; do not rebuild or repeat completed steps merely on restart.',raw_backups='Selected small owned text evidence retained here for auditedGit; newer complete raw remains on thisMac/outside010. Restoration capacity gate unchanged; no newfullrestore or publication claim.',accounting='Use complete external exits once; nested sampled stages overlap. Full198,preparation/doctor,controller authoring/failures,AI review,curation/research and unknown interactive CPU are additional and notzero.',files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
p.save_json(target,record);print(json.dumps(dict(path=str(target),sha256=p.sha(target),files=len(files),bytes=total)))
