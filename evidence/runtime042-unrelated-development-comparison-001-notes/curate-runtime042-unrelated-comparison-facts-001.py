"""Facts/hash-only additive curation; no CAD retention, Native or central readers.

Reuse the measured comparison/own-final reporters, never repeat experiments.
All twelve terminal enclosures and external costs must exist before publication.
This is not a raw backup, legal clearance, restoration or independent validation.
"""
from pathlib import Path
from collections import Counter
import ast, datetime, hashlib, json, math, os, re, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
base=ROOT/'.runs/runtime042-unrelated-current-comparison-001'
runtime=ROOT/'.runs/runtime042 fresh install 001'
HEAD='82aaa3b750007ef2ffaafd367ffcb718aa93865e'
MANIFEST='0fa1f13c4a43385d2d0b513c7c84fb89bb6370eb9962531018f0d1ccbfd6f039'
ADMIN='84af1a721dc8fbb9a9db0076c4e30abe8ed77321'
POPULATION='e69f913897606d93347a8eb98fe8912e21efd4da8b2653e6d1e641abff7e951a'
FROZEN='8eb1f7ee4df493b6b52a576d755d1bc0d592ae1a043751dc321539eb9fa6bb22'
assert p.sha(base/'population.json')==POPULATION and p.sha(base/'frozen-children.json')==FROZEN
population=f.read_json(base/'population.json');frozen=f.read_json(base/'frozen-children.json')
assert population['administration_head']==frozen['administration_head']==ADMIN
assert population['source_head']==HEAD and population['runtime_manifest_sha256']==MANIFEST
assert p.sha(runtime/'runtime-distribution.json')==MANIFEST
families=population['planned_family_order'];arms=population['planned_arm_order']
assert families==['ds18b20','ir-obstacle'] and arms==['Cdefault','B0','B1','B2single_tuned','B2_portfolio','Cthermal']
helpers=[('.runs/curate-runtime030-native-workflow-qualification-001.py','b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',['cost']),
 ('.runs/curate-runtime042-current-comparison-001.py','d6d99941d9afe8d6a81e862d406d66b72f39fdf1c5241dc6cb7403154a61d974',['complete_cost','inventory','custody','counts','delivered_proof']),
 ('.runs/curate-gui-runtime042-081-recovery-deliveries-001.py','340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',['read','own_final'])]
for name,pin,names in helpers:
 source=ROOT/name;assert p.sha(source)==pin
 selected=[n for n in ast.parse(source.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names]
 assert [n.name for n in selected]==names
 exec(compile(ast.Module(body=selected,type_ignores=[]),str(source),'exec'),globals())
keys=('opens','blocking','warnings','exclusions')
output=ROOT/'evidence/runtime042-unrelated-development-comparison-001.json'
notes=ROOT/'evidence/runtime042-unrelated-development-comparison-001-notes'
assert not os.path.lexists(output) and not os.path.lexists(notes)
rows=[];observations=[];retained=[]
for family in families:
 entry=population['families'][family];source=Path(entry['source'])
 assert io.inventory(source.parent)==entry['source_hashes'] and entry['publication']=='hashes_only'
 assert set(frozen['protocols'][family])==set(arms)
 for arm in arms:
  item=frozen['protocols'][family][arm];protocol=Path(item['path'])
  assert protocol==base/family/arm/'protocol.json' and p.sha(protocol)==item['sha256']
  plan=f.read_json(protocol);out=Path(plan['output']);outer=f.read_json(protocol.parent/'enclosure/result.json')
  assert plan['population_protocol_sha256']==POPULATION and plan['source_hashes']==entry['source_hashes']
  assert plan['source']==str(source) and plan['runtime_manifest_sha256']==MANIFEST and plan['source_head']==HEAD
  assert plan['output']==population['outputs'][family][arm] and outer['protocol_sha256']==item['sha256']
  extra=custody(out,plan,outer,arm);allowed=[out,*extra]
  child=out/'result.json';data=f.read_json(child) if child.is_file() else {}
  timing=complete_cost(protocol.parent/'outer-time.log')
  assert all((protocol.parent/name).is_file() for name in ('outer.log','enclosure/process.json','enclosure/command.log'))
  summary=None;summary_pin=None;summary_bound=False
  if arm=='B2_portfolio':
   sp=Path(plan['portfolio_output'])/'portfolio-summary.json'
   if sp.is_file():summary=f.read_json(sp);summary_pin=p.sha(sp)
   if data.get('portfolio_summary_sha256') is not None:
    assert summary is not None and summary_pin==data['portfolio_summary_sha256'];summary_bound=True
   if summary is not None:
    for trial in summary.get('trials',[]):
     if trial.get('result') is not None:
      variant=trial['id'];number=('via_default','via_low','via_high').index(variant)+1
      expected=Path(plan['portfolio_output']+'-'+f'{number:02d}-'+variant)/'route/result.json'
      assert Path(trial['result'])==expected and p.sha(expected)==trial['result_sha256']
  cap=timing['wall_seconds']<=600 and timing['CPU_seconds']<=600
  method=[data.get('method_wall_seconds'),data.get('method_full_cpu_seconds',data.get('method_full_CPU_seconds'))]
  method_ok=all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=450 for v in method)
  qualified=bool(outer['passed'] and data.get('status')=='completed' and data.get('controls_passed') is True and cap and method_ok)
  if summary is not None and summary['status'] in {'budget_exceeded','invalidated','cancelled'}:qualified=False
  if arm=='B2_portfolio' and qualified:assert summary is not None and summary_bound
  if arm!='B2_portfolio':qualified=qualified and data.get('attempt_qualified') is True
  delivered=bool(qualified and data.get('workflow_delivered') is True)
  negative=bool(qualified and data.get('outcome') in ('validated_completed_negative','validated_no_valid_candidate') and not delivered)
  row=dict(family=family,arm=arm,evidence_classification='validated_delivery' if delivered else 'validated_completed_negative' if negative else 'unqualified_or_not_delivered_method',
   outer_passed=outer['passed'],outer_status=outer.get('status'),process_status=outer['process']['status'],cleanup_complete=outer['process']['cleanup_complete'],log_truncated=outer['process']['log_truncated'],
   controller_status=data.get('status'),outcome=data.get('outcome'),controls_passed=data.get('controls_passed'),attempt_qualified=qualified,workflow_delivered=delivered,validated_completed_negative=negative,
   complete_external_cap_ok=cap,method_cap_ok=method_ok,complete_cost=timing,method_sample=dict(wall_seconds=method[0],full_CPU_seconds=method[1]),
   Native_counts=counts(data.get('route_native',data.get('native'))),route_metrics=data.get('route_metrics'),delivered_metrics=data.get('metrics') if delivered else None,
   reason=data.get('reason') or data.get('error') or outer.get('reason') or outer.get('error'),
   protocol_sha256=item['sha256'],child_sha256=outer['child_sha256'],outer_sha256=p.sha(protocol.parent/'enclosure/result.json'),source_hashes=entry['source_hashes'])
  if not qualified and arm!='B2_portfolio':
   raw_path=(Path(data['workspace'])/'route/result.json' if arm=='Cdefault' and data.get('workspace') else out/('thermal-route/result.json' if arm=='Cthermal' else 'route/result.json'))
   assert out in raw_path.parents
   if raw_path.is_file():
    attempt=f.read_json(raw_path)
    row['unqualified_raw_attempt']=dict(receipt_sha256=p.sha(raw_path),status=attempt.get('status'),accepted=attempt.get('accepted'),reason=attempt.get('reason'),
     schematic_parity=attempt.get('schematic_parity'),Native_counts=counts(attempt.get('native')),interpretation='Raw observation only; never promoted to qualified negative or delivery.')
  if delivered:
   proofs={}
   for label,path,export in [('route',Path(data['selected_route_receipt']),False),('export',Path(data['export_receipt']),True)]:
    assert p.sha(path)==data['export_sha256' if export else 'selected_route_sha256']
    proof=delivered_proof(path,export=export,source_hashes=entry['source_hashes'],allowed=allowed)
    record=f.read_json(path);folder=path.parent/'validation' if export else path.parent
    proof['own_final']=own_final(record,folder,folder,entry['source_hashes'],record['candidate']);proofs[label]=proof
    proof['finding_types']=dict(sorted(Counter(str(v['severity'])+':'+str(v['type']) for v in record['native']['findings']).items()))
   assert proofs['route']['candidate_sha256']==proofs['export']['candidate_sha256']
   row['delivered_own_proof']=proofs
   if row['Native_counts'] is None:row['Native_counts']=proofs['route']['Native_counts']
  if arm=='B0':row['stock_DSN_observation']={k:data.get(k) for k in ('stock_native_dsn_sha256','stock_task_dsn_sha256','stock_dsn_identical')}
  if summary is not None:
   selected=summary.get('selected')
   row['portfolio']=dict(status=summary['status'],summary_sha256=summary_pin,summary_bound_to_child=summary_bound,
    selected=({k:selected.get(k) for k in ('id','result_sha256','candidate_sha256','native_report_sha256','vias','length_mm')} if selected else None),
    all_variants_attempted=summary.get('all_variants_attempted'),trials=[dict(variant=t.get('id'),eligible=t.get('eligible'),validated_rejection=t.get('validated_rejection'),Native_counts=counts(t.get('native')),status=t.get('status'),reason=t.get('reason'),result_sha256=t.get('result_sha256')) for t in summary.get('trials',[])])
   for trial,t in zip(row['portfolio']['trials'],summary.get('trials',[])):
    if t.get('result'):
     attempt=f.read_json(Path(t['result']));trial['raw_attempt_reason']=attempt.get('reason')
  rows.append(row);observations.append((out,plan,outer,arm))
assert len(rows)==12
full=f.read_json(ROOT/'.runs/full-integration-189/execution.json')
assert full['passed']is True and full['sources_unchanged']is True
assert full['process']['status']=='success' and full['process']['cleanup_complete']is True and full['process']['log_truncated']is False
assert p.sha(ROOT/'.runs/full-integration-189/command.log')==full['log_sha256']
assert p.sha(ROOT/'.runs/run-full-integration-189.py')==full['controller_sha256']=='a2c8e293a6b0348ae113d3378597f853f090e9079de5dbb2c30aa032a4f92a5b'
assert 'Ran 2349 tests' in io.read_bytes(ROOT/'.runs/full-integration-189/command.log',512*1024).decode()
# Only explicit own metadata/logs are retained; no source/output CAD, plots or raw DRC findings.
metadata=[base/'population.json',base/'frozen-children.json',base/'sources.json',base/'tools-defaults.json',base/'tools-defaults-process.json',base/'preflight-protocol-check-001.json',
 ROOT/'.runs/runtime042-unrelated-current-comparison-preregistration-001.json',ROOT/'.runs/runtime042-unrelated-development-sources-verification-001.json',ROOT/'.runs/runtime042-unrelated-development-source-review-001.json',
 ROOT/'.runs/runtime042-default-target-portfolio-replay-diagnosis-001.json',ROOT/'.runs/runtime042-fractional-native7-support-diagnosis-001.json',
 ROOT/'.runs/runtime042-unrelated-current-comparison-freeze-001.log',ROOT/'.runs/runtime042-unrelated-current-comparison-freeze-001-time.log',
 ROOT/'.runs/run-full-integration-189.py',ROOT/'.runs/full-integration-189/protocol.json',ROOT/'.runs/full-integration-189/execution.json',ROOT/'.runs/full-integration-189/command.log',ROOT/'.runs/full-integration-189-time.log',Path(__file__)]
for family in families:
 for arm in arms:
  folder=base/family/arm
  metadata += [folder/name for name in ('protocol.json','outer.log','outer-time.log','enclosure/result.json','enclosure/process.json','enclosure/command.log')]
assert len(metadata)==len(set(metadata)) and len(metadata)<128
pending=[];total=0
for path in metadata:
 raw=io.read_bytes(path,4*1024**2);raw.decode('utf8');total+=len(raw);assert b'\0' not in raw and total<16*1024**2
 relative=path.relative_to(ROOT);assert relative.parts[0]=='.runs';target=notes/Path(*relative.parts[1:])
 pending.append((path,target,raw,p.sha(path)))
for out,plan,outer,arm in observations:custody(out,plan,outer,arm)
notes.mkdir()
for source,target,raw,pin in pending:
 assert p.sha(source)==pin;target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as stream:stream.write(raw)
 assert p.sha(target)==pin;retained.append(dict(original=str(source.relative_to(ROOT)),retained=str(target.relative_to(ROOT)),sha256=pin,bytes=len(raw)))
for family in families:assert io.inventory(Path(population['families'][family]['source']).parent)==population['families'][family]['source_hashes']
for out,plan,outer,arm in observations:custody(out,plan,outer,arm)
assert p.sha(base/'population.json')==POPULATION and p.sha(base/'frozen-children.json')==FROZEN
for name,pin in population['tracked_administration_files_sha256'].items():assert p.sha(ROOT/name)==pin
record=dict(schema=1,kind='runtime042-two-publisher-exposed-development-facts-only-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,actual_GUI=False,human_review=False,
 source_head=HEAD,runtime_manifest_sha256=MANIFEST,administration_head=ADMIN,population_sha256=POPULATION,frozen_children_sha256=FROZEN,
 exposed_circuit_family_labels=2,independent_pedigree_count=None,exposed_development=True,confirmatory=False,rows=rows,source_rights={n:e['source_rights'] for n,e in population['families'].items()},limits=population['limits'],files=retained,
 preparation_complete_external=complete_cost(ROOT/'.runs/runtime042-unrelated-current-comparison-freeze-001-time.log'),
 full189=dict(passed=True,tests=2349,skips=1,complete_external=complete_cost(ROOT/'.runs/full-integration-189-time.log')),
 reporting_helpers=[dict(path=n,sha256=pin,functions=names) for n,pin,names in helpers],
 publication='Audited own facts/hash inventories/control metadata only; source CAD/generated CAD/DSN/SES/plots/raw DRC findings remain local while embedded title chains are unclosed. This is not a full raw backup/restoration.',
 accounting='Actual complete external exits include all runtime conversion/startup/attempt/selection/validation/delivery. Nested method/Native samples counted once. Source preparation, protocol checking, setup, full/targeted tests, research/authoring/review/curation are additional; incompletely metered administrative/interactive costs unknown, notzero.',
 delivery_workload_caveat='B0 has common fidelity/Native safeguards, not untouched vanilla plugin. API comparison authority checking differs from actual C CLI workflow; no generic or algorithmic speed claim. Desktop contention not fully measured.',
 interpretation='B1 standard remains default. Recovery420 includes incumbent/repair/selection/parent validation; Cthermal is recover, not Improve. Two previously exposed sources/different publishers, no independent ancestry/untouched/broad/cleanup/electrical claim.',
 backup='Essential facts/code remote only after independently verified checkpoint. All new raw Mac-only/outside010; full current restoration capacity blocked.')
p.save_json(output,record)
print(json.dumps(dict(output=str(output),rows=len(rows),delivered=[(r['family'],r['arm']) for r in rows if r['workflow_delivered']],retained_files=len(retained),retained_bytes=total)))
