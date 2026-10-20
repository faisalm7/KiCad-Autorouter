"""Retain completed049 Native deliveries with shared bounded reporting helpers.
No Native/solver/production acceptance readback, GUI, source rewrite or archive scan.
"""
from pathlib import Path
import ast,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io,sexpr as sx
notes=ROOT/'evidence/runtime049-native-milestone-001-notes';target=ROOT/'evidence/runtime049-native-milestone-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
helpers=[('curate-runtime030-native-workflow-qualification-001.py','b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',{'retain','cost'}),('curate-gui-runtime042-081-recovery-deliveries-001.py','340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',{'read','own_final'})]
for name,digest,names in helpers:
 path=ROOT/'.runs'/name;assert p.sha(path)==digest
 nodes=[node for node in ast.parse(path.read_text()).body if isinstance(node,ast.FunctionDef) and node.name in names]
 assert {n.name for n in nodes}==names
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path)+'::shared-reporting','exec'),globals())
prior=ROOT/'evidence/runtime049-pour-and-safety-progress-002.json';assert p.sha(prior)=='0650bc225c866fd393e5b82000b7f5c579f0eb4469b84c8b3b89b8a8132a197e'
prior_record=read(prior);idx=ROOT/prior_record['files_index']['path'];assert p.sha(idx)==prior_record['files_index']['sha256']
for item in read(idx)['files']:refs.setdefault(item['sha256'],item['path'])
runtime=ROOT/'.runs/runtime-directory-049/runtime';manifest=runtime/'runtime-distribution.json';M='70a388a6844d015350073401cb5f33bb1d552d1dc6195ece3aceee27baba5bd4';H='6e2357f975554478c2ba9fa35f18fdc3c1d194f9'
assert p.sha(manifest)==M
base=ROOT/'.runs/runtime049-native-qualification-001';frozen=read(base/'frozen.json');assert frozen['source_head']==H and frozen['runtime_manifest_sha256']==M
extra=ROOT/'.runs/runtime049-native-incumbent-return-001/no-removable/protocol.json'
assert p.sha(extra)=='22c95118fe6844e27c53ace7291df901708c2ef1b9e0588040986f27a6ac8ef2'
entries=frozen['protocols']+[dict(case='improve-no-removable-owned',method='improve',protocol=str(extra),protocol_sha256=p.sha(extra))]
rows=[]
for entry in entries:
 protocol=Path(entry['protocol']);plan=read(protocol);assert p.sha(protocol)==entry['protocol_sha256'] and plan['source_head']==H and plan['runtime_manifest_sha256']==M
 folder=protocol.parent;out=Path(plan['output']);assert io.inventory(Path(plan['source']).parent)==plan['source_hashes']
 retain(protocol,Path('cases')/entry['case']/'protocol.json');retain(folder/'settings.json',Path('cases')/entry['case']/'settings.json')
 execution=read(folder/'execution.json');child=read(out/'result.json');w=Path(child['workspace'])
 assert execution['child_sha256']==p.sha(out/'result.json') and execution['protocol_sha256']==entry['protocol_sha256']
 assert execution['process']['cleanup_complete'] and not execution['process']['log_truncated']
 assert execution['controls_passed'] and execution['workflow_delivered'] and child['status']=='completed'
 assert execution['Native_counts']==plan['expected_counts'] and execution['protected_count']==plan['expected_protected_count']
 row=dict(case=entry['case'],method=entry['method'],protocol_sha256=entry['protocol_sha256'],source_hashes=plan['source_hashes'],source_unchanged=True,controls_passed=True,workflow_delivered=True,actual_GUI=False,complete_external_cost=cost(folder/'outer-time.log'),sampled_wall_seconds=execution['complete_wall_seconds'],sampled_full_CPU_seconds=execution['complete_full_CPU_seconds'],Native_counts=execution['Native_counts'],protected_count=execution['protected_count'])
 for path in (folder/'execution.json',folder/'outer.log',folder/'outer-time.log',folder/'enclosure/process.json',out/'result.json'):
  retain(path,Path('cases')/entry['case']/path.name)
 for stage in child['processes']:retain(out/(stage['stage']+'.log'),Path('cases')/entry['case']/(stage['stage']+'.log'))
 route=read(w/'route/result.json');ex=read(w/'export/export.json');assert route['accepted'] and ex['export_accepted']
 assert route['candidate_sha256']==ex['candidate_sha256']==child['candidate_sha256']
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
  aux=[]
  # Preserve each actual final's auxiliary audit/process/proof files; CAD/netlist
  # inputs remain local. This is reporting, not new acceptance authority.
  for path in sorted(directory.iterdir()):
   if path.is_file() and path.suffix in ('.json','.log','.net') and (path.name.startswith(('final-','pour-keepout-audit','refill-drc','native7-improve-parent','pruning-preferences')) or path.name in ('result.json','metrics.json','metrics-process.json','default-targets.json')):
    retain(path,Path('cases')/entry['case']/label/path.name);aux.append(dict(name=path.name,sha256=p.sha(path)))
  proofs[label]=dict(candidate_sha256=data['candidate_sha256'],Native_counts=[data['native'][k] for k in ('opens','blocking','warnings','exclusions')],ignored_checks=data['native']['ignored_checks'],own_final=proof,retained_auxiliary=aux)
 retain(w/'export/export.json',Path('cases')/entry['case']/'export/export.json')
 for path in (w/'review/review.json',w/'choice/decision.json',w/'settings.json'):
  if path.is_file():retain(path,Path('cases')/entry['case']/'workflow'/path.name)
 row.update(own_finals=proofs,improvements=route.get('improvements'),trials=route.get('trials'),metrics=route['metrics'])
 if entry['case']=='improve-no-removable-owned':
  assert route['trials']==[] and route['improvements']==0
  incumbent=read(Path(route['incumbent']['receipt']))
  assert route['candidate_sha256']==incumbent['candidate_sha256']
  row.update(no_trial_incumbent_return=True,natural_budget_expiry_proved=False,reference_route_disclosed=True,comparison_eligible=False)
 rows.append(row)
assert len(rows)==7 and all(row['workflow_delivered'] for row in rows)
full=read(ROOT/'.runs/full-integration-198/execution.json');assert full['passed'] and full['sources_unchanged'] and full['process']['cleanup_complete']
for path in [manifest,runtime.parent/'preparation.json',base/'frozen.json',base/'doctor.json',base/'doctor-process.json',ROOT/'.runs/full-integration-198/execution.json',ROOT/'.runs/full-integration-198/protocol.json',ROOT/'.runs/full-integration-198/command.log',ROOT/'.runs/full-integration-198-time.log',ROOT/'.runs/native7-no-improvement-owned-source-001/prepared.json',ROOT/'.runs/prepare-runtime049-gui085.py',runtime/'.runs/gui-session085/prepared-state.json',ROOT/'.runs/prepare-runtime049-001.py',ROOT/'.runs/freeze-runtime049-native-001.py',Path(__file__)]:
 retain(path,Path('controllers-and-prerequisites')/path.relative_to(ROOT).as_posix().removeprefix('.runs/'))
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
complete=dict(wall_seconds=round(sum(row['complete_external_cost']['wall_seconds'] for row in rows),2),CPU_seconds=round(sum(row['complete_external_cost']['CPU_seconds'] for row in rows),2))
record=dict(schema=1,kind='runtime049-completed-native-cohort-and-no-trial-incumbent-return-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=H,runtime_manifest_sha256=M,Native_cohort_passed=True,release_qualified=False,accepted=False,project_complete=False,actual_GUI=False,human_review=False,full198=dict(passed=True,tests=2451,skips=1,complete_external_cost=cost(ROOT/'.runs/full-integration-198-time.log')),cases=rows,complete_deliveries_external_cost=complete,prior_progress=dict(path=str(prior.relative_to(ROOT)),sha256=p.sha(prior),scope='Immutable earlier cutoff plus actual invalid/cancel controls and failed40s probe; later completed cases are reported here, not rewritten there.'),result='All six frozen owned/exposed cases complete six installed workflow stages. Additional disclosed-reference/locked-copper control returns its actual verified incumbent with zero trials/improvements and fresh own final/export Native/fullSCH/original/protected2 checks. Every final proof retains warnings/ignored checks. No independent family, broad quality or natural expiry claim.',return_limit='No-removable-zone-copper return is observed at90s, not natural work-budget expiry. The one40s directCLI probe safely refused before incumbent and remains unproved; no tuned retries.',GUI='GUI085 prepared/manager launch observed but project selection currently blocked by disabledOpen despite selected valid file; no current049 toolbar/wxGUI role qualified.042 remains last actual graphical qualification. Edge only; Chrome untouched. Owner asked once to double-click selectedproject, not unlock/security.',next='Finish actual049 GUI085 roles and queued source/settings/export freshness/recovery, then bounded relevant equal-budget development comparison. No rebuild/repeat of completed cases on restart.',backup_scope='Selected owned small text evidence for auditedGit; complete raw/candidateCAD/new049 outputs remain on thisMac/outside010. Capacity-blocked full restoration is not repeated or claimed.',accounting='Complete external delivery exits summed once; nested samples overlap. Full198,preparation/doctor,failed40s/control callers,controller authoring,AI review,reporting/research and unknown whole-interactiveCPU additional, notzero.',files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
p.save_json(target,record);print(json.dumps(dict(path=str(target),sha256=p.sha(target),files=len(files),bytes=total,complete=complete)))
