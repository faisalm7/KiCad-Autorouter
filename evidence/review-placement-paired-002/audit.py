"""Offline actual paired audit using hash-bound frozen checker; no subprocesses."""
from pathlib import Path
from collections import Counter
import copy,hashlib,json,math,signal,subprocess,sys,time
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;RUN=ROOT/'.runs/placement-paired-002/run'
sys.path.insert(0,str(HERE/'frozen-import'));sys.dont_write_bytecode=True
from autorouter import config as c
c.ROOT=ROOT;c.JAR=ROOT/'.tools/freerouting-2.5.0.jar'
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,placement_strategy as ps,sexpr as sx,strategy as s
from scripts import experiment_paired as paired,experiment_portfolio as portfolio
start=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('60-second offline audit ceiling')));signal.alarm(60)
def read(path):return f.read_json(path)
def inventory(path):return pc.inventory(path,max_bytes=512*1024**2,max_files=16000,max_entries=32000)
def require(condition,message):
 if not condition:raise ValueError(message)
def forbidden(*a,**kw):raise AssertionError('Audit must not launch native/Git/network/subprocesses')
protocol=read(RUN/'protocol.json');freeze=protocol['freeze'];source=Path(protocol['source']);summary=read(RUN/'paired-summary.json');outer=read(RUN.parent/'execution.json')
all_before=inventory(RUN);source_before=pc.inventory(source.parent);original=p.preflight(source)
require(source_before==freeze['source_hashes'],'original source differs from prospective protocol')
require(protocol['arm_order']==['B0','B1','B2_portfolio','C_feedback'],'omitted/mixed arm population')
require(protocol['freeze']['tools']['git_head']=='e984d7c49193da9688c21fe9017cb409c9fd3164'==outer['git_head'],'frozen head differs')
require(summary['protocol_sha256']==p.sha(RUN/'protocol.json'),'protocol byte hash differs')
for rel,digest in freeze['files_sha256'].items():require(p.sha(RUN/'frozen-code'/rel)==digest,'frozen run code differs: '+rel)
for rel,digest in freeze['tools']['implementation_sha256'].items():require(p.sha(HERE/'frozen-import'/rel)==digest,'frozen checker bytes differ')
current_differences=[rel for rel,digest in freeze['files_sha256'].items() if p.sha(ROOT/rel)!=digest]
require(protocol['wall_budget_per_arm_seconds']==120 and protocol['cpu_budget_per_arm_seconds']==120,'unequal outer budgets')
rows=summary['results'];require([row['id'] for row in rows]==protocol['arm_order'],'summary arm order differs')
require(summary['status']=='completed' and summary['comparisons']==paired.comparisons(rows),'comparison/frontier reconstruction differs')
require(not any(x.get('pareto_improvement') or x.get('C_dominates_with_1e_6mm_tolerance') for x in summary['comparisons']),'comparison unexpectedly claims C gain')
require(outer['log_sha256']==p.sha(RUN.parent/'command.log') and outer['wrapper_sha256']==p.sha(ROOT/'.runs/run-placement-paired-002.py'),'outer log/wrapper binding differs')
require(outer['process']['exit_code']==0 and outer['process']['status']=='success' and outer['process']['cleanup_complete'] is True and not outer['process']['log_truncated'],'outer cleanup/log/exit invalid')
require(outer['process']['argv']==[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/experiment_paired.py'),'--project','multichannel','--system','placement','--output',str(RUN)],'outer native/network denied wrapper differs')
checks={};records={}
with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden):
 # Accepted receipt checks reconstruct source/import/refill/final/context and
 # pruning ancestry using the exact checker bytes retained by this run.
 checks['B1']=p.check_result(RUN/'B1/result.json')
 psum=read(RUN/'B2_portfolio/portfolio-summary.json');checks['B2_portfolio']=paired.verify_portfolio(RUN/'B2_portfolio',psum,source,freeze)
 checks['C_inner']=p.check_result(RUN/'C_feedback/result.json')
 for name,relative in [('B0','B0'),('B1','B1'),('B2_portfolio','B2_portfolio/01-via_default'),('C_feedback','C_feedback')]:
  folder=RUN/relative;record=read(folder/'result.json');records[name]=record
  require(record['source']==str(source) and record['source_hashes']==source_before and record['tools']==freeze['tools'],'arm source/tool freeze differs')
  require(pc.inventory(folder/'snapshot')==source_before,'source snapshot differs')
  candidate=Path(record['candidate']);pc.verify_candidate(candidate,source_before,record['candidate_sha256'])
  require(p.immutable(sx.read(candidate))==p.immutable(original),'original geometry differs')
  require(p.sha(folder/'final-drc.json')==record['native_report_sha256'] and p.parse_report(folder/'final-drc.json',source.name)==record['native'],'raw final native report differs')
  require(read(folder/'metrics.json')==record['metrics'],'metrics differ')
  require(record['whole_project_drc_clean'] is False,'96warnings/invalid B0 concealed')
  failed_steps={(step['cwd'],step['name']):step for row in record.get('trials',[]) if row.get('completed') is False for step in row['steps']}
  require(all(step['cleanup_complete'] is True and (step['status'] in ('success','nonzero_exit') or (step==failed_steps.get((step['cwd'],step['name'])) and step['status']=='timeout')) for step in record['steps']),'unexplained failed process or cleanup')
  for step in record['steps']:
   process=read(Path(step['cwd'])/(step['name']+'-process.json'))
   require(all(step.get(key)==value for key,value in process.items()),'process differs from recorded step')
   require(process['log_bytes']==Path(process['log']).stat().st_size and not process['log_truncated'],'process log byte count/truncation')
  child=sum(step['cpu_seconds'] for step in record['steps']);monitor=sum(step['monitor_cpu_seconds'] for step in record['steps'])
  require(abs(child-record['child_cpu_seconds'])<1e-6 and abs(monitor-record['monitor_cpu_seconds'])<1e-6,'receipt child CPU omitted/duplicated')
  require(abs(record['total_cpu_seconds']-(record['parent_cpu_seconds']+child+monitor+record.get('control_child_cpu_seconds',0)))<1e-6,'receipt full CPU algebra differs')
  assigned=psum['trials'][0]['assigned_seconds'] if name=='B2_portfolio' else protocol['inner_allowance_seconds']
  require(record['budget_seconds']==assigned,'arm/trial inner allowance differs')
 # B0 is deliberately rejected; central accepted checker must refuse it. Still
 # bind its real source/refill/final reports and reconstruct emitted geometry.
 b0=records['B0'];folder=RUN/'B0';task=f.g.task_from_source(original)
 require(b0['task_sha256']==hashlib.sha256((sx.dump(task)+'\n').encode()).hexdigest(),'B0 task differs')
 before_tree=p.transplant_routes(task,sx.read(folder/'imported.kicad_pcb'))
 rebuilt=p.transplant_fill(before_tree,sx.read(folder/'refill'/source.name))
 require((sx.dump(rebuilt)+'\n').encode()==pc.read_bytes(Path(b0['candidate'])),'B0 import/refill reconstruction differs')
 def b0_drc(name,board,input_path,saved,before):
  binding=read(folder/(name+'-binding.json'))
  require(binding['source']==str(board) and binding['input']==str(input_path) and binding['before']==before and binding['saved'] is saved,'B0 DRC provenance differs')
  p.check_drc_project(before,binding['after'],source.name,saved=saved);require(pc.inventory(input_path.parent)==binding['after'],'B0 DRC input differs')
  native=p.parse_report(folder/(name+'.json'),source.name)
  argv=[str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(folder/(name+'.json'))]
  if saved:argv.append('--save-board')
  argv.append(str(input_path));f.process_check(folder,b0,name,argv,allowed=(5 if native['findings'] else 0,));return native
 require(b0_drc('source-drc',folder/'snapshot'/source.name,folder/'source-drc-input'/source.name,False,source_before)==b0['source_drc'],'B0 source native differs')
 before=dict(source_before);before[source.name]=hashlib.sha256((sx.dump(before_tree)+'\n').encode()).hexdigest()
 b0_drc('refill-drc',folder/'refill'/source.name,folder/'refill'/source.name,True,before)
 before=dict(source_before);before[source.name]=b0['candidate_sha256']
 require(b0_drc('final-drc',Path(b0['candidate']),folder/'final-drc-input'/source.name,False,before)==b0['native'],'B0 final native differs')
 for name,action,output,extra in [('import','import',folder/'imported.kicad_pcb',[folder/'routes.ses']),('metrics','metrics',folder/'metrics.json',[])]:
  f.process_check(folder,b0,name,[str(c.PYTHON),str(ROOT/'autorouter/native.py'),action,b0['candidate'],str(output),*[str(x) for x in extra]])
 settings=p.engine_profile_settings('standard',b0['engine_budget']['remaining_outer_wall_seconds_at_assignment'])
 f.process_check(folder,b0,'engine',f.engine_argv(folder,settings['argv']))
 for name,key in [('native.dsn','native_dsn_sha256'),('task.dsn','task_dsn_sha256')]:require(p.sha(folder/name)==b0[key],'B0 exported DSN differs')
 try:p.check_result(folder/'result.json')
 except p.Rejected as exc:checks['B0_accepted_checker_rejection']=str(exc)
 else:raise ValueError('B0 rejected receipt unexpectedly admitted')
crecord=records['C_feedback'];require(len(crecord['trials'])==1 and crecord['improvements']==0,'C attempt population/gain differs')
trial=crecord['trials'][0];folder=RUN/'C_feedback/trials/0000';basis=RUN/'C_feedback/incumbent'
require(trial['status']=='failed' and trial['completed'] is False and trial['accepted'] is False and trial['proposal']['kind']=='whole_zone_net' and trial['proposal']['net']=='1','partial whole-GND attempt misclassified')
require(abs(trial['assigned_seconds']-6.213624000000863)<1e-9 and abs(trial['total_cpu_seconds']-5.666675999999995)<1e-9,'failed trial cost differs')
require(trial['error']=='Rejected: final-drc: timeout exit=-15','first failed stage differs')
with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden):
 ps.trial_process_history(folder,trial)
 before_tree=ps.deletion(Path(trial['parent']),trial['proposal'],s.zone_net_ids(original))
 before=dict(source_before);before[source.name]=hashlib.sha256((sx.dump(before_tree)+'\n').encode()).hexdigest()
 refill=folder/'refill'/source.name;intermediate=f.check_drc_stage(folder,trial,'refill-drc',refill,refill,True,before)
 candidate=Path(trial['candidate']);pc.verify_candidate(candidate,source_before,p.sha(candidate))
 require((sx.dump(p.transplant_fill(before_tree,sx.read(refill)))+'\n').encode()==pc.read_bytes(candidate),'failed trial delete/refill geometry differs')
 require(p.immutable(sx.read(candidate))==p.immutable(original),'failed trial original immutable geometry differs')
 f.check_final_context(folder,dict(trial,source_hashes=source_before,candidate_sha256=p.sha(candidate)),original,candidate,[],read(basis/'floor-policy.json'),guidance_basis=basis)
 require({k:intermediate[k] for k in ('opens','blocking','warnings','exclusions')}=={'opens':1,'blocking':1,'warnings':96,'exclusions':0},'actual intermediate native counts differ')
 thermal=[x for x in intermediate['findings'] if x['type']=='starved_thermal'];opens=[x for x in intermediate['findings'] if x['type']=='unconnected_items']
 require(len(thermal)==1 and len(opens)==1 and any('pad2' in x.get('description','').replace(' ','').casefold() and 'c2' in x.get('description','').casefold() for x in thermal[0]['items']),'actual thermal/open target differs')
 failed_process=read(folder/'final-drc-process.json');failure=read(folder/'final-drc-failure.json');binding=read(folder/'final-drc-binding.json')
 require(failed_process['status']=='timeout' and failed_process['exit_code']==-15 and failed_process['cleanup_complete'] is True,'trial timeout/cleanup differs')
 require(not (folder/'final-drc.json').exists() and failure.get('passed') is False and failure.get('phase')=='native' and failure.get('error',{}).get('message')==trial['error'].split(': ',1)[1],'failed final DRC report/capture differs')
 require(binding['saved'] is False and binding['source']==str(candidate) and binding['input']==str(folder/'final-drc-input'/source.name),'failed final input binding differs')
 expected=dict(source_before);expected[source.name]=p.sha(candidate)
 require(binding['before']==expected and failure['binding']==binding and pc.inventory(folder/'final-drc-input')==binding['after'],'failed final native/input capture differs')
 require(all(binding['after'].get(name)==digest for name,digest in expected.items()) and set(binding['after'])-set(expected)=={'~'+source.with_suffix('.kicad_pro').name+'.lck'},'failed final original-rule material changed beyond retained lock')
 for name,item in failure['artifacts'].items():
  path=folder/name
  require((not path.exists()) if item is None else path.is_file() and p.sha(path)==item['sha256'] and path.stat().st_size==item['bytes'],'failed native artifact capture differs')
 require(crecord['candidate_sha256']==crecord['selected_parent_sha256']==p.sha(Path(trial['parent'])),'failed attempt changed C selected parent')
trial_finding={'index':0,'status':trial['status'],'completed':False,'accepted':False,'kind':trial['proposal']['kind'],'net':trial['proposal']['net'],'deleted_route_ids':len(trial['proposal']['route_ids']),
 'proposal_sha256':hashlib.sha256(f.canonical(trial['proposal']).encode()).hexdigest(),'assigned_seconds':trial['assigned_seconds'],'wall_seconds':trial['wall_seconds'],'total_cpu_seconds':trial['total_cpu_seconds'],
 'error':trial['error'],'candidate_sha256':p.sha(candidate),'refill_report_sha256':p.sha(folder/'refill-drc.json'),'intermediate_native_counts':{k:intermediate[k] for k in ('opens','blocking','warnings','exclusions')},
 'intermediate_thermal_findings':thermal,'intermediate_open_findings':opens,'final_drc_process':failed_process,'final_drc_failure':failure,'retained_native_lock_file':'~'+source.with_suffix('.kicad_pro').name+'.lck','meaning':'Intermediate refill/context evidence only; final native DRC timed out without report. Trial remains failed and unselected; cannot support final candidate acceptance.'}

require(all(abs(records[name]['metrics']['track_length_mm']-2640.1985526390617)<1e-9 and records[name]['metrics']['vias']==19 and records[name]['native']['warnings']==96 for name in ('B1','B2_portfolio','C_feedback')),'common route metrics/warnings differ')
for row in rows:
 require(abs(row['charged_wall_seconds']-(row['invocation_wall_seconds']+summary['shared_overhead_wall_seconds']))<1e-9,'shared wall charge omitted')
 require(abs(row['charged_cpu_seconds']-(row['invocation_cpu_seconds']+summary['shared_overhead_cpu_seconds']))<1e-9,'shared CPU charge omitted')
 within=row['charged_wall_seconds']<=120 and row['charged_cpu_seconds']<=120
 require(row['within_charged_budgets'] is within and row['accepted'] is (row['accepted_before_shared_charge'] and within),'charged outcome differs')
 for observation in row.get('observations',[]):require(observation['final_delivery_accepted'] is row['accepted'],'early checkpoint mislabelled final accepted')
require([row['accepted'] for row in rows]==[False,True,True,True],'delivered outcomes differ')
require(rows[3]['charged_cpu_seconds']<=120,'C actual charged cap differs')
require(abs(summary['batch_wall_seconds']-sum(row['invocation_wall_seconds'] for row in rows)-summary['shared_overhead_wall_seconds'])<1e-9,'batch wall algebra differs')
require(abs(summary['batch_cpu_seconds']-sum(row['invocation_cpu_seconds'] for row in rows)-summary['shared_overhead_cpu_seconds'])<1e-9,'batch full CPU algebra differs')
require(outer['full_cpu_seconds']>=outer['process']['cpu_seconds']>=summary['batch_cpu_seconds'] and outer['wall_seconds']>=outer['process']['wall_seconds']>=summary['batch_wall_seconds'],'outer compute omitted or inconsistent')
full_outer_shared_wall=outer['wall_seconds']-sum(row['invocation_wall_seconds'] for row in rows)
full_outer_shared_cpu=outer['full_cpu_seconds']-sum(row['invocation_cpu_seconds'] for row in rows)
require(full_outer_shared_wall>=summary['shared_overhead_wall_seconds'] and full_outer_shared_cpu>=summary['shared_overhead_cpu_seconds'],'outer overhead below stored setup/finalization')
full_outer_budget=[row['invocation_wall_seconds']+full_outer_shared_wall<=120 and row['invocation_cpu_seconds']+full_outer_shared_cpu<=120 for row in rows]
require(full_outer_budget==[True,True,True,True],'whole wrapper conservative charges change delivered budget outcome')
require(inventory(RUN)==all_before and pc.inventory(source.parent)==source_before,'original/run evidence changed during readback')
result={'schema':1,'status':'passed_scoped_readback','review_seconds':time.monotonic()-start,'native_executed':False,'subprocesses_executed':False,'git_executed':False,'routing_gain':False,'production_qualification_extended':False,
 'frozen_head':outer['git_head'],'current_sources_differ_from_frozen':current_differences,'checker':'Exact frozen run sources copied into review/frozen-import; config ROOT and JAR rebound only to original checkout. subprocess.run/Popen prohibited.',
 'all_run_files':len(all_before),'all_run_bytes':sum((RUN/name).stat().st_size for name in all_before),'all_run_inventory_sha256':hashlib.sha256(f.canonical(all_before).encode()).hexdigest(),'source_files':len(source_before),'source_inventory_sha256':hashlib.sha256(f.canonical(source_before).encode()).hexdigest(),
 'checks':checks,'arms':[], 'batch':{key:summary[key] for key in ('batch_wall_seconds','batch_cpu_seconds','shared_overhead_wall_seconds','shared_overhead_cpu_seconds')},
 'outer':{key:outer[key] for key in ('wall_seconds','full_cpu_seconds','wrapper_sha256','log_sha256')},
 'full_outer_shared_charge_to_each_arm':{'wall_seconds':full_outer_shared_wall,'cpu_seconds':full_outer_shared_cpu,'within_120_per_arm':full_outer_budget,'meaning':'Conservatively include entire wrapper startup/supervision/final publication overhead in EACH arm, beyond paired-summary pre-publication sample; outcomes unchanged.'},
 'warning':'Mutable stored-evidence consistency review, not authentication, a fresh native run, humanPCB/physical review, or independent-family result.',
 'comparisons':summary['comparisons'],'failed_C_trial':trial_finding,
 'finding':'C final candidate and delivery are accepted within120CPU, including full outer shared charge. Its single whole-net trial failed at final DRC; zero improvements and tied19via/2640.198553mm/96warning metrics establish no C gain. B2 executed default only and stopped truthfully at its remaining-budget reserve.'}
for row in rows:
 name=row['id'];record=records[name]
 result['arms'].append({'id':name,'delivered_accepted':row['accepted'],'inner_accepted':record['accepted'],'candidate_sha256':record['candidate_sha256'],'native_report_sha256':record['native_report_sha256'],
  'receipt_sha256':p.sha(Path(record['candidate']).parent.parent/'result.json'),'metrics':record['metrics'],'native_counts':{key:record['native'][key] for key in ('opens','blocking','warnings','exclusions')},
  'warning_types':dict(Counter(x['type'] for x in record['native']['findings'] if x['severity']=='warning')),'ignored_checks':record['native']['ignored_checks'],
  'source_native_counts':{key:record['source_drc'][key] for key in ('opens','blocking','warnings','exclusions')},
  'process_steps':len(record['steps']),'native_child_cpu_seconds':sum(x['cpu_seconds'] for x in record['steps']),
  'full_outer_charged_wall_seconds':row['invocation_wall_seconds']+full_outer_shared_wall,'full_outer_charged_cpu_seconds':row['invocation_cpu_seconds']+full_outer_shared_cpu,
  'inner_wall_seconds':record['wall_seconds'],'inner_cpu_seconds':record['total_cpu_seconds'],'enclosing_wall_seconds':row['invocation_wall_seconds'],'enclosing_cpu_seconds':row['invocation_cpu_seconds'],'charged_wall_seconds':row['charged_wall_seconds'],'charged_cpu_seconds':row['charged_cpu_seconds']})
require(time.monotonic()-start<60,'offline audit ceiling exceeded');signal.alarm(0)
(HERE/'findings.json').write_text(json.dumps(result,indent=2)+'\n');(HERE/'run-inventory.json').write_text(json.dumps(all_before,indent=2)+'\n')
print(json.dumps({'status':result['status'],'review_seconds':result['review_seconds'],'run_files':len(all_before),'run_bytes':result['all_run_bytes'],'delivered':[row['accepted'] for row in rows]}))
