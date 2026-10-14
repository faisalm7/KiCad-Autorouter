import time
START=time.monotonic()
import json,hashlib,resource,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,placement_clearance as io
from experiments.original_project_native_v1 import driver as d
from scripts import fetch_led_demo as demo
def forbidden(*args,**kwargs):raise AssertionError('No subprocess allowed in read-only audit')
subprocess.run=forbidden;subprocess.Popen=forbidden
OUT=Path(__file__).parent;RUN=ROOT/'.runs/analog-filter-original-native-001'
EXEC=ROOT/'.runs/analog-filter-original-native-001-execution/execution.json'
def digest(path):return hashlib.sha256(io.read_bytes(path,25*1024**2)).hexdigest()
before=d.completed_evidence(RUN);receipt=digest(RUN/'result.json');execution_sha=digest(EXEC)
r=f.read_json(RUN/'result.json');execution=f.read_json(EXEC);job=RUN/'job'
assert r['status']=='observed' and r['accepted'] is False and r['routing_executed'] is False
assert r['native_routing_scope_accepted'] is True and r['production_support_qualified'] is False and r['serialization_equivalence_qualified'] is False
assert r['source_commit']==d.CASES['analog-filter'][2] and r['helper_sha256']==digest(ROOT/'experiments/original_project_native_v1/driver.py')
captured=demo.capture_native_source('analog-filter',root=ROOT)[1];expected={n:hashlib.sha256(raw).hexdigest() for n,raw in captured.items()}
assert expected==r['original_hashes']==io.inventory(RUN/'original',max_bytes=d.LIMIT,max_files=64,max_entries=128)
assert len(captured)==7 and sum(map(len,captured.values()))==198305
board=RUN/'original/kicad/analog_filter_module.kicad_pcb';saved=RUN/'saved/analog_filter_module.kicad_pcb';candidate=Path(r['final_candidate'])
assert candidate==RUN/'candidate/analog_filter_module.kicad_pcb'
original=sx.read(board);emitted=sx.read(saved);final=sx.read(candidate)
routes=d.route_records(original);final_routes=d.route_records(final)
assert len(routes)==47 and routes==final_routes and p.immutable(original)==p.immutable(final)
assert io.read_bytes(candidate)==(sx.dump(p.transplant_fill(original,emitted))+'\n').encode()
p.verify_candidate_files(candidate,expected,r['final_candidate_sha256'])
assert digest(candidate)==r['final_candidate_sha256'] and digest(job/'original-final.json')==r['final_native_report_sha256']
stage_results={}
for name,native_board,saved_flag,key,parity in [('original-refill',saved,True,'original_native',False),('original-final',candidate,False,'parity_native',True)]:
 binding=f.read_json(job/(name+'-binding.json'))
 input_path=native_board if saved_flag else job/(name+'-input')/native_board.name
 checked=f.check_drc_stage(job,r,name,native_board,input_path,saved_flag,binding['before'],schematic_parity=parity)
 assert checked==r[key] and checked['opens']==0 and checked['blocking']==0 and checked['exclusions']==0
 stage_results[name]=checked
assert len(r['steps'])==2 and {x['name'] for x in r['steps']}==set(stage_results)
refill=stage_results['original-refill'];native=stage_results['original-final']
assert refill['warnings']==native['warnings']==14 and r['schematic_parity_findings']==0
warnings=[x for x in native['findings'] if x['severity']=='warning']
assert len(warnings)==14 and all(x['type']=='lib_footprint_issues' for x in warnings)
raw=f.read_json(job/'original-final.json')
assert raw['schematic_parity']==[] and refill['ignored_checks']==native['ignored_checks'] and refill['findings']==native['findings']
assert p.native_accepted(refill) is True and p.native_accepted(native) is True
layers=sx.one(original,'layers');copper=[x for x in layers[1:] if isinstance(x,list) and len(x)>1 and sx.unquote(x[1]).endswith('.Cu')]
assert len(copper)==4
assert r['native_saved_nonfill_ast_equal']==(p.immutable(emitted)==p.immutable(original)) is False
assert r['native_saved_route_records_equal']==(d.route_records(emitted)==routes) is True
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
assert digest(RUN/'result.json')==receipt and digest(EXEC)==execution_sha and demo.capture_native_source('analog-filter',root=ROOT)[1]==captured
DATA=ROOT/'.data/analog-filter-demo-001';FETCH=ROOT/'.runs/fresh-analog-filter-fetch-001/result.json'
data_before=io.inventory(DATA,max_bytes=2*1024**2,max_files=64,max_entries=128,with_directories=True)
fetched=f.read_json(FETCH);source_receipt=f.read_json(DATA/'result.json');cfg=demo.fixed_profile('analog-filter')
assert fetched['status']=='completed' and fetched['controls_passed'] is True and fetched['accepted'] is False and fetched['within_budget'] is True
assert fetched['source_receipt_sha256']==digest(DATA/'result.json') and fetched['controller_sha256']==digest(ROOT/'.runs/run-fresh-analog-filter-fetch-001.py')
assert fetched['tools']==r['tools']
for name,sha in fetched['source_implementation_sha256'].items():assert p.sha(ROOT/name)==sha
assert source_receipt['repository']==cfg['repository'] and source_receipt['source_commit']==cfg['commit']
assert source_receipt['kind']=='fixed_public_analog_filter_source_acquisition' and source_receipt['source_profile']=='fixed five-file public analog-filter selection'
assert source_receipt['status']=='acquired_unqualified' and source_receipt['native_accepted'] is False and source_receipt['source_files_exact'] is True
assert source_receipt['new_network_requests']==len(source_receipt['requests'])==5 and source_receipt['received_bytes']==189336
for index,(row,request) in enumerate(zip(cfg['rows'],source_receipt['requests'])):
 assert request['index']==index and request['source_path']==row['source_path'] and request['artifact']=='responses/'+str(index+1).zfill(2)+'.payload'
 assert request['status']=='response_received' and request['url']==request['final_url']==row['raw_url'] and request['http_status']==200
 raw_response=io.read_bytes(DATA/request['artifact']);demo.shared.payload(row,raw_response)
 assert len(raw_response)==request['received_bytes']==row['bytes'] and digest(DATA/request['artifact'])==request['response_sha256']==row['sha256']
 assert io.read_bytes(DATA/'project'/row['source_path'])==raw_response
for path,origin in cfg['native_packet_notice_copies'].items():assert io.read_bytes(DATA/'native-project'/path)==io.read_bytes(DATA/'project'/origin)
raw_project=demo.verify_project(DATA/'project',profile_id='analog-filter');packet=demo.verify_project(DATA/'native-project',profile_id='analog-filter',native_packet=True)
assert raw_project['file_count']==5 and raw_project['bytes']==189336 and packet['file_count']==7 and packet['bytes']==198305
assert source_receipt['native_packet_hashes']==packet['files'] and source_receipt['native_packet_prepared'] is True
for name,sha in source_receipt['runtime_sha256'].items():assert p.sha(ROOT/name)==sha
fetch_process=fetched['process'];fetch_log=Path(fetch_process['log'])
assert fetch_process['status']=='success' and fetch_process['exit_code']==0 and fetch_process['cleanup_complete'] is True
assert fetch_process['cwd']==str(FETCH.parent) and fetch_process['log_truncated'] is False and fetch_process['log_bytes']==len(io.read_bytes(fetch_log))
assert digest(fetch_log)==fetched['log_sha256']
assert fetch_process['argv']==[str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/fetch_led_demo.py'),'--project','analog-filter','--fetch','--output','.data/analog-filter-demo-001']
assert fetched['charged_wall_seconds']<=305 and fetched['lifetime_full_cpu_seconds']<=305
assert set(data_before[0])==({'result.json'}|{x['artifact'] for x in source_receipt['requests']}|{'project/'+x['source_path'] for x in cfg['rows']}|{'native-project/'+x for x in packet['files']})
assert data_before==io.inventory(DATA,max_bytes=2*1024**2,max_files=64,max_entries=128,with_directories=True)
assert before==d.completed_evidence(RUN) and digest(RUN/'result.json')==receipt and digest(EXEC)==execution_sha
ru=resource.getrusage(resource.RUSAGE_SELF);ch=resource.getrusage(resource.RUSAGE_CHILDREN)
shared_wall=fetched['charged_wall_seconds']+execution['charged_wall_seconds'];shared_cpu=fetched['lifetime_full_cpu_seconds']+execution['lifetime_full_cpu_seconds']
result={'kind':'retained actual public fetch and original native readback','native_rerun':False,'GET_rerun':False,'Git_execution':False,'routing_executed':False,'routing_scope_native_accepted':True,'whole_project_DRC_clean':False,'diagnostic_accepted':False,'production_support_qualified':False,'serialization_equivalence_qualified':False,'observed_head':r['tools']['git_head'],'receipt_sha256':receipt,'execution_sha256':execution_sha,'fetch_receipt_sha256':digest(FETCH),'source_receipt_sha256':digest(DATA/'result.json'),'final_candidate_sha256':r['final_candidate_sha256'],'final_native_report_sha256':r['final_native_report_sha256'],'raw_source_files':5,'raw_source_bytes':189336,'native_packet_files':7,'native_packet_bytes':198305,'source_copper_layers':4,'exact_original_route_UUID_records':len(routes),'immutable_AST_and_project_companions_exact':True,'exact_original_shell_refill_reconstruction':True,'native_saved_nonfill_AST_equal':False,'native_saved_route_records_equal':True,'refill_counts':{k:refill[k] for k in ('opens','blocking','warnings','exclusions')},'final_counts':{k:native[k] for k in ('opens','blocking','warnings','exclusions')},'exact_warning_records_unchanged':True,'warning_details':[{k:x[k] for k in ('type','severity','description')}|{'items':[{'uuid':z['uuid'],'description':z['description']} for z in x['items']]} for x in warnings],'ignored_checks':native['ignored_checks'],'native_steps_checked':2,'actual_GET_requests_checked':5,'GET_request_byte_sum':sum(x['received_bytes'] for x in source_receipt['requests']),'shared_prior_wall_seconds':shared_wall,'shared_prior_cpu_seconds':shared_cpu,'charged_with_full_5s_audit_wall_seconds':shared_wall+5,'charged_with_full_5s_audit_cpu_seconds':shared_cpu+5,'shared_15s_covers_prior_plus_audit5':max(shared_wall+5,shared_cpu+5)<=15,'original_inner_cost':{k:r[k] for k in ('wall_seconds','total_cpu_seconds','output_bytes')},'original_outer_wall_seconds':execution['charged_wall_seconds'],'original_outer_full_cpu_seconds':execution['lifetime_full_cpu_seconds'],'fetch_outer_wall_seconds':fetched['charged_wall_seconds'],'fetch_outer_full_cpu_seconds':fetched['lifetime_full_cpu_seconds'],'review_wall_seconds_before_emission':time.monotonic()-START,'review_lifetime_self_cpu_seconds':ru.ru_utime+ru.ru_stime,'review_waited_children_cpu_seconds':ch.ru_utime+ch.ru_stime,'review_cost_scope':'From first script line/lifetime SELF; earlier exploratory reads (including one wrong-filename error), interpreter bootstrap and packet emission unsampled review preparation. Do not hide future shared/final readback or comparative solver costs.'}
(OUT/'actual-readback.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('routing_scope_native_accepted','whole_project_DRC_clean','exact_original_route_UUID_records','final_counts','charged_with_full_5s_audit_wall_seconds','charged_with_full_5s_audit_cpu_seconds','review_wall_seconds_before_emission','review_lifetime_self_cpu_seconds','review_waited_children_cpu_seconds')}))
