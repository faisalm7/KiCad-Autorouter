"""Retain actual048 pilot outcomes, using existing bounded retention/report helpers.
No Native, production reader, solver, GUI, source rewrite or archive census.
"""
from pathlib import Path
import ast,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io,sexpr as sx
notes=ROOT/'evidence/runtime048-pilot-cutoff-001-notes';target=ROOT/'evidence/runtime048-pilot-cutoff-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
helpers=[('curate-runtime030-native-workflow-qualification-001.py','b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',{'retain','cost'}),('curate-gui-runtime042-081-recovery-deliveries-001.py','340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',{'read','own_final'})]
for name,digest,names in helpers:
 path=ROOT/'.runs'/name;assert p.sha(path)==digest
 module=ast.parse(path.read_text());nodes=[node for node in module.body if isinstance(node,ast.FunctionDef) and node.name in names]
 assert {n.name for n in nodes}==names
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path)+'::shared-reporting','exec'),globals())
runtime=ROOT/'.runs/runtime-directory-048/runtime';manifest=runtime/'runtime-distribution.json';M='97b4d212270c1fda57a8b151910e2f42ba81bc64828ffefda2fc4de4e2651693';H='e49a8d7c5f1423c9a82241e5ab58592cd5f119ac'
assert p.sha(manifest)==M
base=ROOT/'.runs/runtime048-native-qualification-001';frozen=read(base/'frozen.json');assert frozen['source_head']==H and frozen['runtime_manifest_sha256']==M
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
 else:assert not out.exists()
 rows.append(row)
assert [r['controls_passed'] for r in rows if r['executed']]==[True,True,False]
full=read(ROOT/'.runs/full-integration-197/execution.json');assert full['passed'] and full['sources_unchanged'] and full['process']['cleanup_complete']
for path in [manifest,runtime.parent/'preparation.json',base/'frozen.json',base/'doctor.json',base/'doctor-process.json',ROOT/'.runs/full-integration-197/execution.json',ROOT/'.runs/full-integration-197/protocol.json',ROOT/'.runs/full-integration-197/command.log',ROOT/'.runs/full-integration-197-time.log',ROOT/'.runs/runtime048-edge-review-observation-001.json',ROOT/'.runs/gui083-access-resolved-001.json',ROOT/'.runs/prepare-runtime048-001.py',ROOT/'.runs/freeze-runtime048-native-001.py',ROOT/'.runs/freeze-runtime048-controls-001.py',ROOT/'.runs/prepare-runtime048-gui084.py',Path(__file__)]:
 retain(path,Path('controllers-and-prerequisites')/path.relative_to(ROOT).as_posix().removeprefix('.runs/'))
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
record=dict(schema=1,kind='runtime048-two-deliveries-and-pour-only-refusal-facts-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=H,runtime_manifest_sha256=M,qualified=False,accepted=False,project_complete=False,actual_GUI=False,human_review=False,full197=dict(passed=True,tests=2443,skips=1,complete_external_cost=cost(ROOT/'.runs/full-integration-197-time.log')),cases=rows,diagnosis='Named-net pre-refill source contains qualified root pour-only area (net0)(net_name empty); the shared refill route-identity decoder recognizes numeric0 on unrestricted areas only. Native refill succeeds, then reconciliation refuses before final acceptance/fullSCH. Other3frozen cases are unexecuted, not exclusions or passes.',GUI='Actual Edge screenshots paint current048 F.Cu/B.Cu CLI-generated review; no current toolbar/wxGUI qualification.083 access resolved using advertised Raise/Escape/Cancel.084 preparation helper remains unexecuted, requires unexecuted ordinary-alias prerequisite.',controls='Prospective048 invalid/cancel protocols frozen but unexecuted at this cutoff. No no-improvement/work-expiry/stale/recovery/current-GUI qualification is inferred.',stale_labels='Shared encloser kind044 and frozen scope installed045 are historical textual labels; pinned actual runtime048/sourcee49/manifest97b and all tools/candidate paths determine identity. Frozen records were not rewritten.',decision='Preserve2delivered owned regressions,1safe failed supported-combination case and3unexecuted cases. Repair exact demonstrated source-form identity composition with regression negatives, then fresh new-build qualification; no cap increase, source/constraint change, result promotion or stitched unattended claim.',independent_AI_review='Read-only spot review of first048 actual final/export/source/protected/cost evidence found no concrete false-pass blocker. AI review is not humanPCB review; no redundant Native execution.',raw_backups='Selected owned text evidence retained here for auditedGit; all unique complete raw remains on thisMac outside010. No full restoration/capacity claim.',accounting='Use complete external exits once; sampled parent/child/Native/GUI controller costs overlap. Setup/query, full integration, profiling, authoring, independent AI review and curation are additional, unknown interactive CPU notzero.',claims_limit='Owned/exposed diagnostic combinations only. Default remains correctedB1; optional shorter zone-net copper is not broader completion, electrical improvement, independent confirmation, GUI, Windows, standalone or release proof.',files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
p.save_json(target,record);print(json.dumps(dict(path=str(target),sha256=p.sha(target),files=len(files),bytes=total)))
