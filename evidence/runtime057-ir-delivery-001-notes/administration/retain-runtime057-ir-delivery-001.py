"""DRAFT: retain a completed057 IR single Improve delivery, never run routing/readers.

Port of056 retain002. Shared030 retention and approved public report custody,
own-final, Improve auxiliary/trial and complete-cost readers are reused verbatim.
No057 outcome or future candidate/report hash is guessed. Original foreign
CAD/findings stay local; only sanitized generated facts and safe metadata ship.
"""
from pathlib import Path
import ast,datetime,hashlib,json,math,os,re,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io,provenance as pv,floor_route as f
from scripts import report_current_comparison as report
HEAD='ac1a48c3b25b2217e0f8252e0e6da21905f144a4'
MANIFEST='9c667b15b916fc18fadec6dcbd6e0f9710a0c4cc6daeb36fc616f111ef03722e'
PROTOCOL='1171c6d3709920a65552ee88f51bc00c3b2e647c52e9ef7087d3c35f56c884e4'
REPORT='0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e'
base=ROOT/'.runs/runtime057-ir-review-regression-001';runtime=ROOT/'.runs/runtime-directory-057/runtime'
notes=ROOT/'evidence/runtime057-ir-delivery-001-notes';target=ROOT/'evidence/runtime057-ir-delivery-001.json'
assert not os.path.lexists(notes) and not os.path.lexists(target), 'Fresh packet only; preserve any partial failure'
refs={};files=[];material=[];total=0
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='retain']
assert len(nodes)==1
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared-retain','exec'),globals())
assert Path(report.__file__).resolve()==ROOT/'scripts/report_current_comparison.py' and p.sha(Path(report.__file__))==REPORT
read=report.read;cost=report.complete_cost
# Historical056 supplies identical shared bytes for hash deduplication only.
prior=ROOT/'evidence/runtime056-ir-delivery-002.json'
assert p.sha(prior)=='a7c221bc05246bc6a9e1e46ccb6d7a2c3949be78a85019cce74c529e4a0e3be6'
prior_record=read(prior);idx=ROOT/prior_record['files_index']['path'];assert p.sha(idx)==prior_record['files_index']['sha256']
for row in read(idx)['files']:refs.setdefault(row['sha256'],row['path'])
plan=report.pinned(base/'protocol.json',PROTOCOL);frozen=read(base/'frozen.json');manifest=runtime/pv.MANIFEST
assert frozen['protocol_sha256']==PROTOCOL and frozen['only_arm']=='Cimprove' and frozen['executed'] is False
assert plan['kind']=='installed-native7-current-method-v2' and plan['arm']=='Cimprove' and plan['source_head']==HEAD
assert plan['runtime']==str(runtime) and plan['runtime_manifest_sha256']==MANIFEST==p.sha(manifest)
assert pv._runtime_identity(runtime,plan['tools']['implementation_sha256'])==plan['tools']['source_provenance']
assert plan['limits']==dict(routing_seconds=420,method_wall_cpu_cap_seconds=450,delivery_wall_cpu_cap_seconds=600,export_validation_seconds=120)
for name,pin in plan['prerequisite_sha256'].items():assert p.sha(Path(name))==pin
outer_path=base/'enclosure/result.json';outer_pin=p.sha(outer_path);outer=report.pinned(outer_path,outer_pin);out=Path(plan['output']);producer=out/'result.json'
assert outer['protocol_sha256']==PROTOCOL and outer['accepted'] is False and outer['production_admitted'] is False
assert report.custody(out,plan,outer,'Cimprove')==[]
child=read(producer);complete=cost(base/'outer-time.log')
classification=report.classify(outer,child,complete,'Cimprove')
assert classification['workflow_delivered'] is True and classification['attempt_qualified'] is True
assert outer['passed'] is True and outer['status']=='completed' and child['outcome']=='validated_delivery'
routepath=Path(child['selected_route_receipt']);assert child['selected_route_sha256']==p.sha(routepath)
workspace=routepath.parent.parent;assert workspace.parent==out and re.fullmatch('autorouter-gui-[0-9a-f]{32}',workspace.name)
route=read(routepath);export_path=workspace/'export/export.json';export=read(export_path)
assert child['export_receipt']==str(export_path) and child['export_sha256']==p.sha(export_path)
allowed=[out]
parent_proof=report.own_final(routepath,export=False,plan=plan,allowed=allowed,accepted=True,public_sanitize=True)
export_proof=report.own_final(export_path,export=True,plan=plan,allowed=allowed,accepted=True,public_sanitize=True)
improve=report.improve_facts(routepath,plan,allowed,qualified_parent=True,public_sanitize=True)
export_auxiliary=report.improve_auxiliary(export_path.parent/'validation',export,plan)
assert parent_proof['Native_counts']==export_proof['Native_counts']
counts=parent_proof['Native_counts'];assert counts[:2]==[0,0] and counts[3]==0
assert route['candidate_sha256']==export['candidate_sha256']==child['candidate_sha256']
assert p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']
review=read(workspace/'review/review.json');choice=read(workspace/'choice/choice.json')
assert review['status']=='ready_for_manual_review' and choice['choice_recorded'] is True and choice['choice']=='accept'
assert choice['human_pcb_approval_observed'] is False and choice['applied'] is False
assert review['receipt_sha256']==choice['receipt_sha256']==p.sha(routepath)
assert choice['review_sha256']==p.sha(workspace/'review/review.json')
assert all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=30 for v in (review['wall_seconds'],review['total_cpu_seconds'],choice['wall_seconds'],choice['total_cpu_seconds']))
processes={};queue=[];omitted=[]
for q in sorted(producer.parent.glob('*.process.json')):
 data=read(q);assert data['exit_code']==0 and data['cancel_requested'] is False and data['log_truncated'] is False
 processes[q.name]=dict(wall_seconds=data['wall_seconds'],exit_code=0,cancel_requested=False,cleanup_scope=data['cleanup_scope'],sha256=p.sha(q))
 queue.append((q,Path('stage-processes')/q.name))
assert set(processes)=={name+'.process.json' for name in ('preview','route','review','choice','export','verify_export')}
# No raw result/native findings, map/netlist/source/transport/plots or CAD copied.
# Own-final/trial readers above have already checked their actual local bytes.
for relative,pin in outer['completed_evidence'].items():
 q=out/relative
 safe=(q.name.endswith('-process.json') or q.name.endswith('-binding.json')
       or q.name.endswith('-local-settings.json') or q.suffix=='.kicad_prl')
 if safe:
  assert p.sha(q)==pin;queue.append((q,Path('current-own-proof-metadata')/relative))
 else:omitted.append(dict(original=str(q.relative_to(ROOT)),sha256=pin,reason='Raw foreign source/candidate/findings/transport/plots/cache or unselected metadata stays local; sanitized current proof facts retained instead.'))
for name in ('protocol.json','frozen.json','tools-defaults.json','tools-defaults-process.json','enclosure/command.log','enclosure/process.json','enclosure/result.json','outer.log','outer-time.log'):
 queue.append((base/name,Path('single-regression')/name))
full=ROOT/'.runs/full-integration-207';execution=read(full/'execution.json');prepared=read(runtime.parent/'preparation.json')
assert execution['passed'] is True and execution['sources_unchanged'] is True and execution['process']['cleanup_complete'] is True and execution['process']['log_truncated'] is False
assert prepared['source_head']==HEAD and prepared['manifest_sha256']==MANIFEST and prepared['full207_execution_sha256']==p.sha(full/'execution.json')
full_text=io.read_bytes(full/'command.log',512*1024).decode();matches=re.findall(r'^Ran ([0-9]+) tests in ',full_text,re.M)
assert len(matches)==1 and re.search(r'^OK \(skipped=1\)$',full_text,re.M)
for name in ('protocol.json','execution.json','command.log'):queue.append((full/name,Path('integration/full207')/name))
for name in ('runtime-distribution.json','RUNTIME_README.txt'):queue.append((runtime/name,Path('runtime')/name))
for name in ('preparation.json','venv-process.json','venv.log'):queue.append((runtime.parent/name,Path('runtime/preparation')/name))
for name in ('run-full-integration-207.py','full-integration-207-controller-001.log','full-integration-207-time-001.log','prepare-runtime057-001.py','prepare-runtime057-001.log','prepare-runtime057-001-time.log','freeze-runtime057-ir-review-regression-001.py','freeze-runtime057-ir-review-regression-001.log','freeze-runtime057-ir-review-regression-001-time.log'):
 queue.append((ROOT/'.runs'/name,Path('controllers-and-costs')/name))
for q in (Path(__file__),helper,Path(report.__file__),ROOT/'scripts/enclose_current_comparison.py',ROOT/'scripts/qualify_current_method.py',ROOT/'scripts/qualify_installed_workflow.py'):
 queue.append((q,Path('administration')/q.name))
# All prospective guards and costs resolve before first new public payload.
full_cost=cost(ROOT/'.runs/full-integration-207-time-001.log');build_cost=cost(ROOT/'.runs/prepare-runtime057-001-time.log');prep_cost=cost(ROOT/'.runs/freeze-runtime057-ir-review-regression-001-time.log')
timings=(complete,full_cost,build_cost,prep_cost)
def timing_fresh():
 for row in timings:assert p.sha(Path(row['source']))==row['time_log_sha256']
 assert p.sha(outer_path)==outer_pin
timing_fresh()
assert len(queue)<2000 and all(q.is_file() and not q.is_symlink() and q.stat().st_size<=4*1024**2 for q,_ in queue)
assert sum(q.stat().st_size for q,_ in queue if p.sha(q) not in refs)<16*1024**2, 'Stop for split; never raise packet caps'
seen=set()
for path,name in queue:
 if path in seen:continue
 assert '.runs' not in name.parts and '..' not in name.parts
 seen.add(path);retain(path,name)
timing_fresh()
assert report.custody(out,plan,outer,'Cimprove')==[]
assert p.tree_hash(Path(plan['source']).parent)==plan['source_hashes'] and p.sha(Path(report.__file__))==REPORT
timing_fresh()
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material,omitted_local_hash_only=omitted))
p.save_json(target,dict(schema=1,kind='runtime057-single-fresh-exposed-IR-Improve-delivery-regression-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,workflow_delivered=True,attempt_qualified=True,project_complete=False,actual_GUI=False,human_review=False,source_head=HEAD,runtime_manifest_sha256=MANIFEST,protocol_sha256=PROTOCOL,full207=dict(passed=True,tests=int(matches[0]),skips=1,complete_cost=full_cost),build=dict(complete_cost=build_cost),preparation=dict(complete_cost=prep_cost),single_fresh_exposed_IR_Improve=dict(classification=classification,complete_cost=complete,outer_complete_wall_seconds=outer['complete_wall_seconds'],outer_complete_full_CPU_seconds=outer['complete_full_CPU_seconds'],child_sha256=p.sha(producer),route_receipt_sha256=p.sha(routepath),review_receipt_sha256=p.sha(workspace/'review/review.json'),choice_receipt_sha256=p.sha(workspace/'choice/choice.json'),export_receipt_sha256=p.sha(export_path),candidate_sha256=route['candidate_sha256'],Native_counts=counts,trials=len(route['trials']),review_wall_seconds=review['wall_seconds'],review_CPU_seconds=review['total_cpu_seconds'],choice_wall_seconds=choice['wall_seconds'],choice_CPU_seconds=choice['total_cpu_seconds'],metrics=route['metrics'],stages=processes,parent_own_final=parent_proof,export_own_final=export_proof,Improve_lineage=improve,export_auxiliary=export_auxiliary),source_hashes=plan['source_hashes'],source_rights=plan['source_rights'],source_unchanged=True,scope='Fresh057 single exposed IR default-score Improve delivery regression: unchanged420wholeImprove/450method/600complete wall+fullCPU/export120 and30s review/choice ceilings. Stored actual own parent/export/incumbent/every-trial Native/Default/field/PRL/report/process/input proofs checked by shared reporter; no Native or central reader rerun. Not a comparison, old-result substitution, GUI, family/holdout gain, electrical/cleanup or routing-superiority claim.',historical056_reference=dict(path=str(prior.relative_to(ROOT)),sha256=p.sha(prior),scope='Historical delivered056 regression and same-byte payload deduplication only; not current057 qualification or current reporting failure.'),not_a_comparison=True,all_prior_cohorts_and_failures_unchanged=True,remaining='Current Native cohort/invalids and actual GUI/installation/cancellation/freshness evidence retained separately. Broader families/untouched confirmation/engineer cleanup/physical/Windows/restoration gates remain; no transfer from this one regression.',costs='Complete actual exits counted once; nested samples overlap. Earlier failures/full suites/builds/source research/authoring/AI review/profiles/GUI/install/curation additional and partly unmetered, not zero. Current057 reporting failure is not fabricated from historical056 formatting attempts.',raw_scope='Owned code/logs and sanitized factual metadata/hashes only. Foreign CAD/DSN/SES/plots/full Native findings stay local. New raw Mac-only/outside010; no full raw backup or restoration claim.',files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
print(json.dumps(dict(files=len(files),bytes=total,material=len(material),delivered=True,Native_rerun=False,project_complete=False)))
