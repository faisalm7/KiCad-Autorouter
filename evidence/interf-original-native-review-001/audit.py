import time
START=time.monotonic()
import json,hashlib,resource,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,placement_clearance as io
from experiments.original_project_native_v1 import driver as d
def forbidden(*args,**kwargs):raise AssertionError('No subprocess allowed in read-only audit')
subprocess.run=forbidden;subprocess.Popen=forbidden
OUT=Path(__file__).parent;RUN=ROOT/'.runs/interf-original-complete-sch-001'
EXEC=ROOT/'.runs/interf-original-complete-sch-001-execution/execution.json'
def digest(path):return hashlib.sha256(io.read_bytes(path,25*1024**2)).hexdigest()
before=d.completed_evidence(RUN);receipt=digest(RUN/'result.json');execution_sha=digest(EXEC)
r=f.read_json(RUN/'result.json');execution=f.read_json(EXEC);job=RUN/'job'
assert r['status']=='observed' and r['accepted'] is False and r['routing_executed'] is False
assert r['native_routing_scope_accepted'] is False and r['production_support_qualified'] is False and r['serialization_equivalence_qualified'] is False
assert r['source_commit']==d.CASES['interf_u'][2] and r['helper_sha256']==digest(ROOT/'experiments/original_project_native_v1/driver.py')
captured=d.capture_interf_source();expected={n:hashlib.sha256(raw).hexdigest() for n,raw in captured.items()}
assert expected==r['original_hashes']==io.inventory(RUN/'original',max_bytes=d.LIMIT,max_files=64,max_entries=128)
assert len(captured)==25 and sum(map(len,captured.values()))==1490971
board=RUN/'original/interf_u.kicad_pcb';saved=RUN/'saved/interf_u.kicad_pcb';candidate=Path(r['final_candidate'])
assert candidate==RUN/'candidate/interf_u.kicad_pcb'
original=sx.read(board);emitted=sx.read(saved);final=sx.read(candidate)
routes=d.route_records(original);final_routes=d.route_records(final)
assert len(routes)==815 and routes==final_routes and p.immutable(original)==p.immutable(final)
assert io.read_bytes(candidate)==(sx.dump(p.transplant_fill(original,emitted))+'\n').encode()
p.verify_candidate_files(candidate,expected,r['final_candidate_sha256'])
assert digest(candidate)==r['final_candidate_sha256'] and digest(job/'original-final.json')==r['final_native_report_sha256']
stage_results={}
for name,native_board,saved_flag,key,parity in [('original-refill',saved,True,'original_native',False),('original-final',candidate,False,'parity_native',True)]:
 binding=f.read_json(job/(name+'-binding.json'))
 input_path=native_board if saved_flag else job/(name+'-input')/native_board.name
 checked=f.check_drc_stage(job,r,name,native_board,input_path,saved_flag,binding['before'],schematic_parity=parity)
 assert checked==r[key] and checked['opens']==0 and checked['blocking']==2 and checked['exclusions']==0
 stage_results[name]=checked
assert len(r['steps'])==2 and {x['name'] for x in r['steps']}==set(stage_results)
refill=stage_results['original-refill'];native=stage_results['original-final']
assert refill['warnings']==0 and native['warnings']==22 and r['schematic_parity_findings']==22
thermals=lambda native:[x for x in native['findings'] if x['type']=='starved_thermal']
assert thermals(refill)==thermals(native) and len(thermals(native))==2
assert all(x['severity']=='error' for x in thermals(native))
warnings=[x for x in native['findings'] if x['severity']=='warning']
assert len(warnings)==22 and all(x['type']=='footprint_symbol_mismatch' for x in warnings)
raw=f.read_json(job/'original-final.json')
assert raw['schematic_parity']==warnings and refill['ignored_checks']==native['ignored_checks']
assert p.native_accepted(refill) is False and p.native_accepted(native) is False
assert r['native_saved_nonfill_ast_equal']==(p.immutable(emitted)==p.immutable(original)) is False
assert r['native_saved_route_records_equal']==(d.route_records(emitted)==routes) is False
for name,sha in {**r['tools']['implementation_sha256'],**r['additional_implementation_sha256']}.items():
 assert p.sha(ROOT/name)==sha==p.sha(RUN/'code'/name)
for name,sha in r['tools']['files'].items():assert p.sha(name)==sha
assert r['tools']==execution['tools'] and execution['result_sha256']==receipt
for name,sha in execution['initial_source_sha256'].items():assert p.sha(name)==sha
proc=execution['process'];log=Path(proc['log'])
assert proc['status']=='success' and proc['exit_code']==0 and proc['cleanup_complete'] is True
assert proc['cwd']==str(EXEC.parent) and proc['log_truncated'] is False and proc['log_bytes']==len(io.read_bytes(log))
assert r['within_budget'] is True and max(r['wall_seconds'],r['total_cpu_seconds'])<=90 and r['output_bytes']<=20*1024**2
assert execution['charged_wall_seconds']<=90 and execution['lifetime_full_cpu_seconds']<=90
assert r['original_preserved'] is True and r['acquired_source_still_exact'] is True
assert before==d.completed_evidence(RUN) and r['completed_evidence_sha256']==hashlib.sha256(f.canonical(before).encode()).hexdigest()
assert digest(RUN/'result.json')==receipt and digest(EXEC)==execution_sha and d.capture_interf_source()==captured
ru=resource.getrusage(resource.RUSAGE_SELF);ch=resource.getrusage(resource.RUSAGE_CHILDREN)
result={'kind':'actual retained native original diagnostic readback','native_rerun':False,'routing_executed':False,'whole_project_qualified':False,'accepted':False,'observed_head':r['tools']['git_head'],'receipt_sha256':receipt,'execution_sha256':execution_sha,'final_candidate_sha256':r['final_candidate_sha256'],'final_native_report_sha256':r['final_native_report_sha256'],'raw_source_files':25,'source_bytes':1490971,'exact_original_route_UUID_records':len(routes),'immutable_AST_and_companion_files_preserved':True,'candidate_exact_original_shell_refill_reconstruction':True,'refill_counts':{k:refill[k] for k in ('opens','blocking','warnings','exclusions')},'final_counts':{k:native[k] for k in ('opens','blocking','warnings','exclusions')},'identical_thermal_findings':[{k:x[k] for k in ('type','severity','description')}|{'items':[{'uuid':z['uuid'],'description':z['description']} for z in x['items']]} for x in thermals(native)],'parity_warnings':[{k:x[k] for k in ('type','severity','description')}|{'items':[{'uuid':z['uuid'],'description':z['description']} for z in x['items']]} for x in warnings],'ignored_checks':native['ignored_checks'],'native_saved_nonfill_AST_equal':False,'native_saved_route_records_equal':False,'native_steps_checked':len(r['steps']),'inner_cost':{k:r[k] for k in ('wall_seconds','total_cpu_seconds','output_bytes')},'outer_charged_wall_seconds':execution['charged_wall_seconds'],'outer_lifetime_full_cpu_seconds':execution['lifetime_full_cpu_seconds'],'review_wall_seconds_before_emission':time.monotonic()-START,'review_lifetime_self_cpu_seconds':ru.ru_utime+ru.ru_stime,'review_waited_children_cpu_seconds':ch.ru_utime+ch.ru_stime,'review_cost_scope':'from first script line and lifetime SELF; interpreter bootstrap, earlier source reads and final receipt/report/manifest emission unsampled; no algorithm timing or native execution','input_whole_evidence_sha256':r['completed_evidence_sha256']}
(OUT/'actual-readback.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('accepted','exact_original_route_UUID_records','refill_counts','final_counts','review_wall_seconds_before_emission','review_lifetime_self_cpu_seconds','review_waited_children_cpu_seconds')}))
