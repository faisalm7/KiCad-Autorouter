"""Fresh exposed IR stronger-stock B2 versus existing C/chains; no general gain claim.
SPDX-License-Identifier: GPL-3.0-or-later
One command per arm; read/report are pure and never rerun a solver or Native.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,contextlib,fcntl,hashlib,json,os,re,signal,stat,subprocess,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,strategy as s,handoff as h,placement_clearance as io,sexpr as sx,local_settings as ls,engine_angle
from autorouter.runner import run
from scripts import experiment_quality as q
from scripts.fetch_led_demo import capture_native_source
from experiments.native_paired_v1 import observations as obs,readback as rb
from experiments.hfe_original_native_v1 import driver as shared
from experiments.stronger_incumbent_v1 import native_control as owned
PREP=ROOT/'.runs/stronger-incumbent-pair-preparation-001';PROTOCOL=PREP/'protocol.json'
OUT=ROOT/'.runs/stronger-incumbent-pair-command-001';TIMING=ROOT/'.runs/stronger-incumbent-pair-timing-001'
READ=ROOT/'.runs/stronger-incumbent-pair-read-001';REPORT=ROOT/'.runs/stronger-incumbent-pair-report-001'
CONTROL=owned.OUT/'result.json';KIND='fresh-ir-stronger-stock-vs-chains-v1'
ARMS={'B2_stronger':dict(id='B2_stronger',operation='route',adapter='both',engine_profile='tuned-free-angle'),
 'C_stronger':dict(id='C_stronger',operation='prune',adapter='both',engine_profile='tuned',proposal_policy='chains',incumbent_policy=s.STRONG_INCUMBENT_POLICY)}
ORDER=[('ir-obstacle',name) for name in ARMS]
POPULATION=[(project,name) for project in ('ir-obstacle','arcdice') for name in ARMS]
LIMITS=dict(route=120,worker=180,delivered=240,output=128*1024**2,rss=4*1024**3,log=256*1024,publication=2,reader=90,report=30)
GATES={'ir-obstacle':['.runs/ir-obstacle-original-native-001/result.json','.runs/ir-obstacle-original-native-readback-001/result.json','.runs/ir-obstacle-original-field-gate-003/result.json'],
 'arcdice':['.runs/arcdice-original-native-001/result.json','.runs/arcdice-original-native-002-readback/result.json']}
COMMAND=ROOT/'.runs/run-stronger-incumbent-pair-command-001.py'
ENCLOSURES=ROOT/'.runs/stronger-incumbent-pair-enclosures-001'
HELPERS=['.runs/run-stronger-incumbent-pair-command-001.py','scripts/experiment_quality.py','scripts/fetch_led_demo.py','experiments/native_paired_v1/observations.py','experiments/native_paired_v1/readback.py',
 'experiments/hfe_original_native_v1/driver.py','experiments/placement_handoff_native_v1/driver.py','experiments/stronger_incumbent_v1/native_control.py',
 'experiments/fanout_baseline_v1/clearance_control.py','experiments/fanout_baseline_v1/clearance_fixture.py','experiments/fanout_baseline_v1/fixture.py',
 'experiments/free_angle_baseline_v1/fixture.py','experiments/native_schematic_transport_v1/fixture.py']

def control_external(plan,receipt_pin,data):
 # Reuse actual bounded command envelopes and the already completed pure002.
 files={};envelopes={}
 def retain(path):files[str(path.relative_to(ROOT))]=p.sha(path)
 wrapper=ROOT/'.runs/run-stronger-incumbent-native-command-001.py';retain(wrapper)
 for mode in ('prepare','run'):
  folder=ROOT/('.runs/stronger-incumbent-command-001/'+mode);path=folder/'execution.json';entry=f.read_json(path);proc=entry['process'];retain(path)
  expected=[str(ROOT/'.venv/bin/python'),'-B',str(Path(owned.__file__).resolve()),'--mode',mode,'--source-head',plan['git_head']]
  if mode=='run':expected+=['--protocol-sha256',p.sha(owned.PROTOCOL)]
  if (entry.get('mode')!=mode or entry.get('source_head')!=plan['git_head'] or entry.get('module_sha256')!=p.sha(Path(owned.__file__)) or entry.get('controller_sha256')!=p.sha(wrapper)
      or proc.get('argv')!=expected or proc.get('cwd')!=str(folder) or proc.get('log')!=str(folder/'command.log') or proc.get('status')!='success' or type(proc.get('exit_code'))is not int or proc['exit_code']!=0
      or proc.get('cleanup_complete') is not True or proc.get('log_truncated') is not False or (folder/'command.log').stat().st_size!=proc.get('log_bytes')):raise p.Rejected('actual prerequisite prepare/run envelope differs')
  retain(folder/'command.log');envelopes[mode]=entry
 reader_path=ROOT/'.runs/stronger-incumbent-native-readback-002/result.json';reader=f.read_json(reader_path);retain(reader_path)
 failure=ROOT/'.runs/stronger-incumbent-native-timing-001/read-command.log'
 if (reader.get('accepted') is not False or reader.get('passed') is not True or reader.get('status')!='completed' or reader.get('git_head')!=plan['git_head'] or reader.get('protocol_sha256')!=p.sha(owned.PROTOCOL)
     or reader.get('whole_control_receipt_sha256')!=receipt_pin or reader.get('native_executed') is not False or reader.get('engine_executed') is not False
     or reader.get('positive_candidate_sha256')!=data['positive']['candidate_sha256'] or reader.get('positive_native_report_sha256')!=data['positive']['native_report_sha256']
     or reader.get('negative_candidate_sha256')!=data['physical_short']['candidate_sha256'] or reader.get('negative_native_report_sha256')!=data['physical_short']['report_sha256']
     or reader.get('prior_reader_guard_refusal_sha256')!=p.sha(failure)):raise p.Rejected('completed pure prerequisite002 or retained first refusal differs')
 folder=ROOT/'.runs/stronger-incumbent-native-readback-command-002';path=folder/'execution.json';entry=f.read_json(path);proc=entry['process'];retain(path)
 worker=ROOT/'.runs/read-stronger-incumbent-native-002.py';wrapper2=ROOT/'.runs/run-stronger-incumbent-native-readback-002.py';retain(worker);retain(wrapper2)
 if (entry.get('worker_sha256')!=p.sha(worker) or entry.get('controller_sha256')!=p.sha(wrapper2) or proc.get('argv')!=[str(ROOT/'.venv/bin/python'),'-B',str(worker)]
     or proc.get('cwd')!=str(folder) or proc.get('log')!=str(folder/'command.log') or proc.get('status')!='success' or type(proc.get('exit_code'))is not int or proc['exit_code']!=0
     or proc.get('cleanup_complete') is not True or proc.get('log_truncated') is not False or (folder/'command.log').stat().st_size!=proc.get('log_bytes')):raise p.Rejected('actual pure002 envelope differs')
 retain(folder/'command.log');timings={}
 for stage in ('prepare','run','read','read002'):
  timepath=ROOT/('.runs/stronger-incumbent-native-timing-001/'+stage+'-time.log');command=timepath.with_name(stage+'-command.log');retain(timepath);retain(command)
  pairs=re.findall(r'(?m)^(real|user|sys) ([0-9.]+)$',io.read_bytes(timepath,64*1024).decode());values={name:float(value) for name,value in pairs}
  if len(pairs)!=3 or set(values)!={'real','user','sys'} or any(not q.finite_nonnegative(value) for value in values.values()):raise p.Rejected('actual prerequisite full external timing missing')
  timings[stage]=dict(wall_seconds=values['real'],full_cpu_seconds=values['user']+values['sys'],disposition='failed pure read-only startup guard before Native' if stage=='read' else 'completed')
 charge=dict(wall_seconds=sum(row['wall_seconds']+.01 for row in timings.values()),full_cpu_seconds=sum(row['full_cpu_seconds']+.02 for row in timings.values()))
 if max(charge.values())>180:raise p.Rejected('whole prerequisite incl failed reader exceeds180')
 return dict(files_sha256=files,external_operations=timings,whole_control_charged=charge,scope='Complete external prepare/run/failed-read/read002 cost, context engineering separate from fresh comparison arms; no partial sample is represented as complete exit cost.')

def control(pin):
 path=ls.canonical(CONTROL);protocol_pin=p.sha(owned.PROTOCOL);plan=f.read_json(owned.PROTOCOL);owned.context(plan,protocol_pin)
 data=f.read_json(path);literal=f.canonical(data);material=shared.material(owned.OUT)
 if (p.sha(path)!=pin or data.get('passed') is not True or data.get('status')!='completed' or data.get('accepted') is not False
     or data.get('git_head')!=plan['git_head'] or data.get('protocol_sha256')!=protocol_pin or data.get('completed_evidence')!=material
     or plan.get('policy')!=s.STRONG_INCUMBENT_POLICY or plan.get('kind')!='fresh-stronger-pruning-incumbent-v1'
     or any(not q.finite_nonnegative(data.get(k)) for k in ('wall_seconds','full_cpu_seconds'))):
  raise p.Rejected('fresh same-checkpoint C/short control required')
 positive=owned.check_positive(plan);owned.check_negative(plan,data['physical_short'])
 expected={k:positive[k] for k in ('candidate_sha256','native_report_sha256','native','metrics','improvements')};expected['receipt_sha256']=p.sha(owned.OUT/'route/result.json')
 if data['positive']!=expected or p.sha(path)!=pin or f.canonical(f.read_json(path))!=literal or shared.material(owned.OUT)!=material:
  raise p.Rejected('control complete positive/negative material changed')
 binding=dict(receipt=str(path),receipt_sha256=pin,literal=literal,protocol_sha256=protocol_pin,material=material,external_qualification=control_external(plan,pin,data))
 control_prl(binding)
 return plan,binding

def control_prl(binding):
 plan=f.read_json(owned.PROTOCOL);data=f.read_json(CONTROL);positive=f.read_json(owned.OUT/'route/result.json');bad=data['physical_short']
 if (p.sha(owned.PROTOCOL)!=binding['protocol_sha256'] or p.sha(CONTROL)!=binding['receipt_sha256']
     or f.canonical(data)!=binding['literal'] or shared.material(owned.OUT)!=binding['material']
     or any(p.sha(ROOT/name)!=digest for name,digest in binding['external_qualification']['files_sha256'].items())):raise p.Rejected('owned prerequisite material changed before PRL check')
 negative=dict(schema=1,steps=bad['steps'],source_hashes=bad['before'],tools=plan['tools'])
 ls.check_normal_policy(owned.OUT/'route',positive,max_bytes=LIMITS['output'],max_files=2048)
 ls.check_normal_policy(owned.OUT/'invalid-job',negative,max_bytes=LIMITS['output'],max_files=2048)

def source(project):
 board,family=q.selected_source(project);packet,files=capture_native_source(project,root=ROOT)
 return board,family,dict(packet=str(packet),files={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()})

def eligibility(board):
 policy=p.netclass_policy(board);width=p.minimum_width_guard(board,'both');strict=policy is not None or width is not None
 return dict(execution_eligible=not strict,derived_strict_class_targets=strict,netclass_policy=policy,minimum_width_guard=width,
  refusal='unsupported: qualified private free-angle/fanoutFalse/optimizerFalse/clearance20 requires derived non-strict native class/width targets' if strict else None)

def prepare(head,control_pin):
 shared.clean(head);qualified,binding=control(control_pin)
 if qualified['git_head']!=head:raise p.Rejected('fresh owned prerequisite must use exact new verified checkpoint')
 projects={}
 for project in ('ir-obstacle','arcdice'):
  board,family,packet=source(project);frozen=q.freeze(board);p.preflight(board)
  gates={name:p.sha(ROOT/name) for name in GATES[project]};last=f.read_json(ROOT/GATES[project][-1]);baseline=last['qualified_native'] if project=='ir-obstacle' else last['native']
  if not p.native_accepted(baseline) or baseline['warnings']!=({'ir-obstacle':42,'arcdice':26}[project]):raise p.Rejected('original fullSCH Native qualification unavailable')
  state=eligibility(board)
  if state['execution_eligible'] is not (project=='ir-obstacle'):raise p.Rejected('frozen full-population eligibility changed')
  projects[project]=dict(source=str(board),family=family,packet=packet,freeze=frozen,gates=gates,gate_material={name:shared.material((ROOT/name).parent) for name in gates},baseline=baseline,eligibility=state)
 plan=dict(schema=1,kind=KIND,status='frozen',git_head=head,tools=qualified['tools'],projects=projects,arms=ARMS,
  arm_order=[list(x) for x in ORDER],population=[list(x) for x in POPULATION],control_binding=binding,helper_sha256={name:p.sha(ROOT/name) for name in HELPERS},
  controller_sha256=p.sha(Path(__file__)),limits=LIMITS,planned_external_timing_directory=str(TIMING),
  scope='One exposed source IR fresh stock B2 versus existing C/chains; Arc strict unsupported retained. Both method budgets120, delivery240 each including common preparation+entire current pure reader+all tails. C owns a fresh incumbent with unchanged25reserve (actual child<=95, not a free120 incumbent). All source/rules/PRL/geometry/fullSCH unchanged. No historical candidate/solver reused as incumbent; current qualified control proof is only a prerequisite, global quality/default/novelty/support claim.')
 context(plan);plan['preparation_costs']=dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
 if max(plan['preparation_costs']['wall_seconds'],plan['preparation_costs']['full_cpu_seconds'])+2>=58:raise p.Rejected('preparation exhausted fixed delivery margin')
 PREP.mkdir();p.save_json(PROTOCOL,plan);print(f.canonical(dict(prepared=True,protocol_sha256=p.sha(PROTOCOL),new_native_or_engine_execution=False)))

def context(plan,pin=None):
 shared.clean(plan['git_head'])
 if (plan.get('kind')!=KIND or plan.get('status')!='frozen' or plan.get('arms')!=ARMS or plan.get('arm_order')!=[list(x) for x in ORDER]
     or plan.get('population')!=[list(x) for x in POPULATION] or plan.get('limits')!=LIMITS or set(plan.get('projects',{}))!={'ir-obstacle','arcdice'}
     or plan.get('planned_external_timing_directory')!=str(TIMING) or p.sha(Path(__file__))!=plan['controller_sha256'] or p.tool_manifest()!=plan['tools']):raise p.Rejected('fixed protocol/controller/tools changed')
 if any(p.sha(ROOT/name)!=pin for name,pin in plan['helper_sha256'].items()):raise p.Rejected('frozen helper changed')
 qualified,binding=control(plan['control_binding']['receipt_sha256'])
 if binding!=plan['control_binding'] or qualified['git_head']!=plan['git_head'] or qualified['tools']!=plan['tools']:raise p.Rejected('fresh owned prerequisite changed')
 for project,spec in plan['projects'].items():
  board,family,packet=source(project);q.verify_freeze(spec['freeze'],board)
  if str(board)!=spec['source'] or family!=spec['family'] or packet!=spec['packet'] or eligibility(board)!=spec['eligibility']:raise p.Rejected('source or eligibility changed')
  for name,digest in spec['gates'].items():
   if p.sha(ROOT/name)!=digest or shared.material((ROOT/name).parent)!=spec['gate_material'][name]:raise p.Rejected('original qualification changed')
 if pin is not None and (p.sha(PROTOCOL)!=pin or f.canonical(f.read_json(PROTOCOL))!=f.canonical(plan)):raise p.Rejected('protocol changed')
 control_prl(plan['control_binding'])

def planning(folder,data):
 # Same child-only actual engine/proof checker for direct B2 and C's charged incumbent.
 p.check_engine_profile_record(data,folder);engine_angle.check_scope(data,'native')
 proof=engine_angle.check(folder,data);changes=proof.get('planning_clearance',{}).get('changes',[])
 if (data.get('engine_profile')!='tuned-free-angle' or data.get('scoring_variant')!='via_default'
     or data.get('engine_fanout_override') is not False or data.get('engine_optimizer_override') is not False
     or type(data.get('engine_planning_clearance_margin_nm'))is not int or data['engine_planning_clearance_margin_nm']!=20000
     or len(changes)!=2 or any(row.get('before')!='200' or row.get('after')!='220' for row in changes)):
  raise p.Rejected('exact qualified strong stock planning configuration differs')
 return dict(assigned_seconds=data['budget_seconds'],cpu_assigned_seconds=data['cpu_budget_seconds'],engine_process_sha256=p.sha(folder/'engine-process.json'),engine_angle_proof_sha256=p.sha(folder/'engine-angle.json'),planning_proof=proof)

def observations(folder,data,spec,arm):
 board=Path(spec['source']);original=sx.read(board);hashes=spec['freeze']['source_hashes'];finals=[];errors=[]
 workers=obs.workers(folder,data,board,hashes,original);resource_error=obs.resource_failure(folder,data)
 def final(directory,record,label,parent=None):
  if not (directory/'final-drc.json').is_file():return dict(id=label,status=record.get('status'),final_native_available=False)
  try:
   error=obs.resource_failure(directory,record,parent)
   proof=obs.candidate(directory,record,board,original,hashes,spec['baseline'],parent=parent,resource_error=error)
   qualification=record['native'].get('field_parity',{}).get('qualification',{});census=record['native'].get('field_parity',{}).get('board_only_field_census',{})
   if qualification.get('component_count')!=11 or qualification.get('compared_field_count')!=26 or census.get('complete_footprint_count')!=12 or census.get('compared_footprint_count')!=11 or len(census.get('artwork',[]))!=1 or len(record['native']['ignored_checks'])!=7:
    raise p.Rejected('complete11components26fields/padless artwork/seven ignored checks differ')
   return dict(id=label,status=record.get('status'),accepted_in_receipt=record.get('accepted') is True,native=record['native'],proof=proof,field_parity=record['native']['field_parity'])
  except Exception as exc:
   errors.append(dict(id=label,error=type(exc).__name__+': '+str(exc)));return dict(id=label,status=record.get('status'),final_native_available=True,qualified=False,candidate_sha256=record.get('candidate_sha256'),native_report_sha256=record.get('native_report_sha256'),native=record.get('native'))
 finals.append(final(folder,data,'final'))
 child=folder/'incumbent/result.json' if arm['operation']=='prune' else folder/'result.json'
 incumbent=f.read_json(child) if child.is_file() else None;planproof=None
 if incumbent is not None:
  try:
   planproof=planning(child.parent,incumbent)
   if arm['operation']=='prune' and (child.parent/'final-drc.json').is_file():
    rb.pruning_incumbent_readback(folder,data,board,original,hashes)
  except Exception as exc:errors.append(dict(id='incumbent' if arm['operation']=='prune' else 'planning',error=type(exc).__name__+': '+str(exc)))
  if arm['operation']=='prune':finals.append(final(child.parent,incumbent,'incumbent'))
 if arm['operation']=='prune':
  for trial in data.get('trials',[]):
   path=Path(trial['receipt']);expected=folder/'trials'/trial['id']/'result.json'
   if path!=expected or path.is_symlink():raise p.Rejected('trial receipt escaped its declared arm')
   record=f.read_json(path)
   if any(record.get(k)!=trial.get(k) for k in ('id','status','accepted')):raise p.Rejected('trial summary differs from retained receipt')
   finals.append(final(path.parent,record,trial['id'],data))
 return dict(workers=workers,finals=finals,errors=errors,resource_failure=resource_error,planning=planproof)

def arm_prl(folder,data):ls.check_normal_policy(folder,data,max_bytes=LIMITS['output'],max_files=2048)

def worker(plan,pin,project,name):
 context(plan,pin);spec=plan['projects'][project];arm=ARMS[name];board=Path(spec['source']);folder=OUT/project/name/'child'
 if spec['eligibility']['execution_eligible'] is not True:raise p.Rejected(spec['eligibility']['refusal'])
 folder.mkdir();owner={};h.capture_destination(owner,folder);data=None
 record=dict(schema=1,accepted=False,passed=False,status='failed',project=project,arm=name,protocol_sha256=pin,git_head=plan['git_head'],tools=plan['tools'])
 try:
  with p.validation_readback_session():
   began,initial=time.monotonic(),cpu()
   data=(p.route(board,folder/'route',120,False,'both','tuned-free-angle',scoring_variant='via_default',_fanout_enabled=False,_optimizer_enabled=False,_engine_clearance_margin_nm=20000) if arm['operation']=='route'
    else s.prune(board,folder/'route',120,proposal_policy='chains',incumbent_scoring='via_default',_incumbent_policy=s.STRONG_INCUMBENT_POLICY))
   wall,full=time.monotonic()-began,cpu()-initial;stored=f.read_json(folder/'route/result.json')
   if f.canonical(data)!=f.canonical(stored) or data['tools']!=plan['tools'] or data['source_hashes']!=spec['freeze']['source_hashes']:raise p.Rejected('returned/stored source/tool lineage differs')
   record['route_receipt_sha256']=p.sha(folder/'route/result.json');row=q.summarize(arm,folder/'route',data,wall,full)
   record['row']=row;record['observations']=observations(folder/'route',data,spec,arm);row['observations']=q.observations(folder/'route',data,row)
   row['accepted']=bool(row['accepted'] and not record['observations']['errors'] and record['observations']['resource_failure'] is None)
   record.update(passed=row['accepted'],status='completed' if row['accepted'] else 'failed')
 except (Exception,KeyboardInterrupt) as exc:record.update(passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) or data and q.cancelled(data) else 'failed',error=type(exc).__name__+': '+str(exc))
 witness=shared.material(folder);record['completed_evidence']=witness
 def remaining():return min(178-(time.monotonic()-START),178-(cpu()-CPU0))
 def stable():
  h.owned_destination(owner);context(plan,pin)
  if shared.material(folder)!=witness:raise p.Rejected('child material changed')
  if data is not None and data.get('accepted') is True:p.check_result(folder/'route/result.json')
  if shared.material(folder)!=witness:raise p.Rejected('child material changed late')
  control_prl(plan['control_binding'])
  if data is not None:arm_prl(folder/'route',data)
 def account():
  record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
  if remaining()<=0 and record['status']!='cancelled':record['status']='budget_exceeded'
  if record['status']!='completed':record['passed']=False
 f.publish(folder,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
 return 0 if record['passed'] and record['status']=='completed' else 130 if record['status']=='cancelled' else 2

def execute(plan,pin,project,name):
 context(plan,pin)
 for prior_project,prior_name in ORDER[:ORDER.index((project,name))]:
  old=f.read_json(OUT/prior_project/prior_name/'result.json')
  if old.get('protocol_sha256')!=pin or old.get('status')=='cancelled' or old.get('process',{}).get('cleanup_complete') is not True:raise p.Rejected('prior arm absent/cancelled or cleanup incomplete; second arm not attempted')
 folder=OUT/project/name;folder.parent.mkdir(parents=True,exist_ok=True);folder.mkdir();owner={};h.capture_destination(owner,folder)
 costs=plan['preparation_costs']
 if costs.get('publication_allowance_seconds')!=2 or any(not q.finite_nonnegative(costs.get(k)) for k in ('wall_seconds','full_cpu_seconds')):raise p.Rejected('finite preparation costs required')
 prewall,precpu=costs['wall_seconds']+2,costs['full_cpu_seconds']+2
 def remaining():return min(238-prewall-(time.monotonic()-START),238-precpu-(cpu()-CPU0))
 fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
 with os.fdopen(fd,'r+') as lock:
  info=os.fstat(lock.fileno())
  if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary existing shared lane required')
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__)),'--mode','worker','--source-head',plan['git_head'],'--protocol-sha256',pin,'--project',project,'--arm',name]
  env={key:value for key,value in os.environ.items() if key not in {'PYTHONPATH','PYTHONHOME'}};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',LANG='C',LC_ALL='C')
  process=run(argv,cwd=folder,env=env,log=folder/'command.log',timeout=max(.001,min(180,remaining())),max_log_bytes=LIMITS['log'],max_workdir_bytes=LIMITS['output'],max_group_rss_bytes=LIMITS['rss'])
  path=folder/'child/result.json';child=f.read_json(path) if path.is_file() else None;childpin=p.sha(path) if child else None;literal=f.canonical(child)
  bound=bool(child and child.get('completed_evidence')==shared.material(folder/'child') and p.sha(path)==childpin and f.canonical(f.read_json(path))==literal)
  witness=shared.material(folder);passed=bool(bound and child.get('passed') is True and child.get('status')=='completed' and child.get('accepted') is False and child.get('project')==project and child.get('arm')==name
   and child.get('protocol_sha256')==pin and child.get('git_head')==plan['git_head'] and child.get('tools')==plan['tools'] and process['status']=='success' and type(process['exit_code'])is int and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
  record=dict(schema=1,accepted=False,passed=passed,status='completed' if passed else 'cancelled' if process['status']=='cancelled' or child and child.get('status')=='cancelled' else 'failed',project=project,arm=name,
   protocol_sha256=pin,git_head=plan['git_head'],controller_sha256=plan['controller_sha256'],process=process,child_receipt_sha256=childpin,child_literal=literal,child_material_bound=bound,completed_evidence=witness,
   preparation_costs=costs,delivered_qualification_pending=True,scope=plan['scope'])
  def stable():
   h.owned_destination(owner);context(plan,pin)
   if shared.material(folder)!=witness or child is not None and (not bound or p.sha(path)!=childpin or f.canonical(f.read_json(path))!=literal or shared.material(folder/'child')!=child['completed_evidence']):raise p.Rejected('outer/child complete material changed')
   control_prl(plan['control_binding'])
   route=folder/'child/route/result.json'
   if route.is_file():arm_prl(route.parent,f.read_json(route))
  def account():
   record.update(wall_seconds=prewall+time.monotonic()-START,full_cpu_seconds=precpu+cpu()-CPU0,publication_allowance_seconds=2)
   if remaining()<=0 and record['status']!='cancelled':record['status']='budget_exceeded'
   if record['status']!='completed':record['passed']=False
  f.publish(folder,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
  print(f.canonical({k:record.get(k) for k in ('project','arm','passed','status','wall_seconds','full_cpu_seconds')}))
  return 0 if record['passed'] and record['status']=='completed' else 130 if record['status']=='cancelled' else 2

@contextlib.contextmanager
def pure_process_guard():
 old_run,old_popen=subprocess.run,subprocess.Popen;active=False
 prefix=['git','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null'];allowed=[['git','rev-parse','HEAD'],[*prefix,'rev-parse','HEAD'],[*prefix,'status','--porcelain=v1','--untracked-files=normal']]
 def check(argv,kw):
  if type(argv)is not list or argv not in allowed or Path(kw.get('cwd','')).resolve()!=ROOT or kw.get('shell') or kw.get('executable')is not None:raise p.Rejected('pure reader allows only exact read-only source Git observations')
 def run_git(argv,*a,**kw):
  nonlocal active
  check(argv,kw)
  if a or active:raise p.Rejected('unexpected nested pure process call')
  active=True
  try:return old_run(argv,**kw)
  finally:active=False
 def popen_git(argv,*a,**kw):
  check(argv,kw)
  if a or not active:raise p.Rejected('unqualified pure process launch')
  return old_popen(argv,**kw)
 subprocess.run,subprocess.Popen=run_git,popen_git
 try:yield
 finally:subprocess.run,subprocess.Popen=old_run,old_popen

def dispositions(plan,pin):
 rows=[]
 for project,name in POPULATION:
  spec=plan['projects'][project];path=OUT/project/name/'result.json'
  if spec['eligibility']['execution_eligible'] is not True:
   if path.parent.exists() or path.parent.is_symlink():raise p.Rejected('unsupported Arc unexpectedly has runtime output')
   rows.append(dict(project=project,arm=name,status='unsupported',accepted=False,attempted=False,reason=spec['eligibility']['refusal']));continue
  if not path.is_file():
   rows.append(dict(project=project,arm=name,status='not_attempted' if not path.parent.exists() else 'missing_receipt',accepted=False,attempted=path.parent.exists(),reason='Frozen arm absent or incomplete; consult retained enclosing command logs. No candidate or pass synthesized.'));continue
  outer=f.read_json(path)
  if outer.get('protocol_sha256')!=pin or outer.get('project')!=project or outer.get('arm')!=name:raise p.Rejected('arm identity differs')
  rows.append(dict(project=project,arm=name,status=outer['status'],accepted=False,attempted=True,result=str(path),result_sha256=p.sha(path)))
 return rows

def read(plan,pin):
 READ.mkdir();owner={};h.capture_destination(owner,READ)
 with pure_process_guard(),p.validation_readback_session():
  context(plan,pin);rows=dispositions(plan,pin);witnesses={};errors=[]
  for row in rows:
   if row['project']!='ir-obstacle' or not row.get('result'):continue
   project,name=row['project'],row['arm'];folder=OUT/project/name;outer=f.read_json(folder/'result.json');process=outer['process'];childpath=folder/'child/result.json'
   witnesses[str(folder)]=dict(material=shared.material(folder),result_sha256=p.sha(folder/'result.json'),literal=f.canonical(outer))
   try:
    expected=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__)),'--mode','worker','--source-head',plan['git_head'],'--protocol-sha256',pin,'--project',project,'--arm',name]
    if process['argv']!=expected or process['cwd']!=str(folder) or process['log']!=str(folder/'command.log') or process['cleanup_complete'] is not True or process['log_truncated'] is not False or Path(process['log']).stat().st_size!=process['log_bytes'] or process['resource_guards']['max_group_rss_bytes']!=LIMITS['rss'] or process['resource_guards']['max_workdir_bytes']!=LIMITS['output']:raise p.Rejected('actual enclosing worker process differs')
    if (shared.material(folder)!=outer['completed_evidence'] or outer.get('git_head')!=plan['git_head'] or outer.get('controller_sha256')!=plan['controller_sha256'] or outer.get('preparation_costs')!=plan['preparation_costs']):raise p.Rejected('outer complete witness/source/provenance changed')
    child=f.read_json(childpath)
    if (outer.get('child_material_bound') is not True or p.sha(childpath)!=outer['child_receipt_sha256'] or f.canonical(child)!=outer['child_literal'] or shared.material(childpath.parent)!=child['completed_evidence'] or child['protocol_sha256']!=pin or child.get('project')!=project or child.get('arm')!=name or child.get('git_head')!=plan['git_head'] or child.get('tools')!=plan['tools']):raise p.Rejected('child literal/prepublication witness differs')
    route=folder/'child/route';data=f.read_json(route/'result.json')
    if (p.sha(route/'result.json')!=child['route_receipt_sha256'] or data.get('source')!=plan['projects'][project]['source'] or data.get('source_hashes')!=plan['projects'][project]['freeze']['source_hashes'] or data.get('tools')!=plan['tools']):raise p.Rejected('route receipt/source/tool binding differs')
    observed=observations(route,data,plan['projects'][project],ARMS[name])
    raw=q.summarize(ARMS[name],route,data,child['row']['invocation_wall_seconds'],child['row']['invocation_cpu_seconds']);raw['observations']=q.observations(route,data,raw)
    raw['accepted']=bool(raw['accepted'] and not observed['errors'] and observed['resource_failure'] is None)
    if raw!=child['row'] or observed!=child['observations']:raise p.Rejected('retained summary/whole-final observations differ')
    if data.get('accepted') is True:p.check_result(route/'result.json')
    enclosure=(outer.get('passed') is True and outer.get('status')=='completed' and child.get('passed') is True and child.get('status')=='completed' and child.get('accepted') is False and process.get('status')=='success' and type(process.get('exit_code'))is int and process['exit_code']==0
     and all(q.finite_nonnegative(outer.get(key)) and outer[key]+2<=240 for key in ('wall_seconds','full_cpu_seconds')) and all(q.finite_nonnegative(child.get(key)) and child[key]+2<=180 for key in ('wall_seconds','full_cpu_seconds')))
    row.update(native_result_accepted=raw['accepted'],arm_enclosure_completed=enclosure,row=raw,observations=observed,outcome_evidence_qualified=True)
   except Exception as exc:errors.append(dict(project=project,arm=name,error=type(exc).__name__+': '+str(exc)));row.update(outcome_evidence_qualified=False,error=errors[-1]['error'])
  record=dict(schema=1,accepted=False,passed=not errors,status='completed' if not errors else 'failed',git_head=plan['git_head'],protocol_sha256=pin,rows=rows,errors=errors,arm_complete_trees=witnesses,new_native_execution=False,new_JVM_execution=False)
  own=shared.material(READ);record['completed_evidence']=own
  def remaining():return min(88-(time.monotonic()-START),88-(cpu()-CPU0))
  def stable():
   h.owned_destination(owner);context(plan,pin)
   if shared.material(READ)!=own or any(shared.material(Path(folder))!=tree['material'] or p.sha(Path(folder)/'result.json')!=tree['result_sha256'] or f.canonical(f.read_json(Path(folder)/'result.json'))!=tree['literal'] for folder,tree in witnesses.items()):raise p.Rejected('pure reader retained material changed')
   control_prl(plan['control_binding'])
   for project,name in ORDER:
    path=OUT/project/name/'child/route/result.json'
    if path.is_file():arm_prl(path.parent,f.read_json(path))
  def account():
   record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
   if remaining()<=0:record.update(passed=False,status='budget_exceeded')
   if record['status']!='completed':record['passed']=False
  f.publish(READ,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
  print(f.canonical(dict(passed=record['passed'],status=record['status'],errors=errors)))
  return 0 if record['passed'] else 2

def timing(stage,plan,pin):
 files={suffix:TIMING/(stage+'-'+suffix) for suffix in ('time.log','command.log')};text=io.read_bytes(files['time.log'],64*1024).decode()
 pairs=re.findall(r'(?m)^(real|user|sys) ([0-9.]+)$',text);values={key:float(value) for key,value in pairs}
 if len(pairs)!=3 or set(values)!={'real','user','sys'} or any(not q.finite_nonnegative(value) for value in values.values()):raise p.Rejected('unique complete external process-exit timing required')
 mode='run' if stage in ARMS else stage
 expected=[str(Path(__file__).resolve()),'--mode',mode,'--source-head',plan['git_head']]
 if mode=='prepare':expected+=['--control-sha256',plan['control_binding']['receipt_sha256']]
 else:expected+=['--protocol-sha256',pin]
 if mode=='run':expected+=['--project','ir-obstacle','--arm',stage]
 cwd=ENCLOSURES/stage;enclosure=cwd/'execution.json';e=f.read_json(enclosure);process=e['process'];log=cwd/'command.log'
 success=process.get('status')=='success' and type(process.get('exit_code'))is int and process['exit_code']==0
 completed=success or (stage in ARMS and process.get('status')=='nonzero_exit' and type(process.get('exit_code'))is int and process['exit_code']!=0)
 if (e.get('stage')!=stage or e.get('source_head')!=plan['git_head'] or e.get('driver_sha256')!=plan['controller_sha256']
     or e.get('wrapper_sha256')!=plan['helper_sha256'].get(str(COMMAND.relative_to(ROOT))) or p.sha(COMMAND)!=e['wrapper_sha256']
     or process.get('argv')!=[str(ROOT/'.venv/bin/python'),'-B',*expected] or process.get('cwd')!=str(cwd)
     or process.get('log')!=str(log) or not completed
     or process.get('cleanup_complete') is not True or process.get('log_truncated') is not False
     or e.get('log_sha256')!=p.sha(log) or log.stat().st_size!=process.get('log_bytes')
     or process['resource_guards']['max_workdir_bytes']!=8*1024**2 or process['resource_guards']['max_group_rss_bytes']!=LIMITS['rss']):
  raise p.Rejected('actual complete stage process/argv/cwd/log/source/cleanup differs')
 lines=io.read_bytes(files['command.log'],LIMITS['log']).decode().splitlines()
 if not lines:raise p.Rejected('actual external invocation journal missing')
 invocation=json.loads(lines[0]).get('invocation')
 if invocation!=dict(argv=expected,cwd=str(cwd),executable=str(ROOT/'.venv/bin/python'),controller_sha256=plan['controller_sha256']):raise p.Rejected('external timing log is not bound to exact actual invocation')
 lower_wall=process['wall_seconds'];lower_cpu=sum(process.get(k) or 0 for k in ('cpu_seconds','monitor_cpu_seconds','supervisor_cpu_seconds'))
 if stage=='prepare':sample=plan['preparation_costs'];sample_wall=sample['wall_seconds'];sample_cpu=sample['full_cpu_seconds']
 elif stage in ARMS:
  outer=f.read_json(OUT/'ir-obstacle'/stage/'result.json');prep=plan['preparation_costs']
  sample_wall=max(0,outer['wall_seconds']-prep['wall_seconds']-2);sample_cpu=max(0,outer['full_cpu_seconds']-prep['full_cpu_seconds']-2)
 else:
  sample=f.read_json(READ/'result.json');sample_wall=sample['wall_seconds'];sample_cpu=sample['full_cpu_seconds']
 if (any(not q.finite_nonnegative(x) for x in (lower_wall,lower_cpu,sample_wall,sample_cpu))
     or values['real']+.01<max(lower_wall,sample_wall) or values['user']+values['sys']+.02<max(lower_cpu,sample_cpu)):
  raise p.Rejected('external complete cost below retained actual process/stage lower bound')
 files.update(execution=enclosure,worker_log=log)
 return dict(wall_seconds=values['real'],full_cpu_seconds=values['user']+values['sys'],complete_process_success=success,actual_process_status=process['status'],actual_exit_code=process['exit_code'],files_sha256={str(path.relative_to(ROOT)):p.sha(path) for path in files.values()},rounding_allowance_seconds=.02)


def report(plan,pin):
 REPORT.mkdir();owner={};h.capture_destination(owner,REPORT)
 with pure_process_guard():
  context(plan,pin);reader=f.read_json(READ/'result.json');readpin=p.sha(READ/'result.json');readliteral=f.canonical(reader)
  if reader.get('passed') is not True or reader.get('status')!='completed' or reader.get('protocol_sha256')!=pin or reader.get('completed_evidence')!=shared.material(READ):raise p.Rejected('completed current whole pure reader required')
  costs={stage:timing(stage,plan,pin) for stage in ('prepare','B2_stronger','C_stronger','read')};rows=json.loads(f.canonical(reader['rows']))
  for row in rows:
   if row['project']!='ir-obstacle':continue
   selected=[costs['prepare'],costs[row['arm']],costs['read']]
   row['charged_wall_seconds']=sum(x['wall_seconds']+x['rounding_allowance_seconds'] for x in selected)+LIMITS['report']
   row['charged_full_cpu_seconds']=sum(x['full_cpu_seconds']+x['rounding_allowance_seconds'] for x in selected)+LIMITS['report']
   row['delivered_within_240']=max(row['charged_wall_seconds'],row['charged_full_cpu_seconds'])<=240
   row['accepted']=bool(row.get('native_result_accepted') and row.get('arm_enclosure_completed') and row.get('outcome_evidence_qualified') and row['delivered_within_240'] and costs[row['arm']]['complete_process_success'])
  record=dict(schema=1,accepted=False,passed=True,status='completed',git_head=plan['git_head'],protocol_sha256=pin,reader_sha256=readpin,external_costs=costs,rows=rows,
   common_report_wall_full_cpu_upper_allowance_seconds=LIMITS['report'],scope=plan['scope'],cost_scope='Each IR arm pays full external preparation + own full external arm + ENTIRE current external pure reader +.02perroundedlog +30s bounded report allowance. No failed or publication tails removed; actual report process-exit log retained separately. No historical quality comparison.')
  material=shared.material(REPORT);record['completed_evidence']=material
  def remaining():return min(28-(time.monotonic()-START),28-(cpu()-CPU0))
  def stable():
   h.owned_destination(owner);context(plan,pin)
   if p.sha(READ/'result.json')!=readpin or f.canonical(f.read_json(READ/'result.json'))!=readliteral or reader['completed_evidence']!=shared.material(READ) or shared.material(REPORT)!=material:raise p.Rejected('reader/report material changed')
   if any(timing(stage,plan,pin)!=old for stage,old in costs.items()) or any(shared.material(Path(folder))!=tree['material'] or p.sha(Path(folder)/'result.json')!=tree['result_sha256'] or f.canonical(f.read_json(Path(folder)/'result.json'))!=tree['literal'] for folder,tree in reader['arm_complete_trees'].items()):raise p.Rejected('actual command timing or arm material changed')
   control_prl(plan['control_binding'])
   for project,name in ORDER:
    path=OUT/project/name/'child/route/result.json'
    if path.is_file():arm_prl(path.parent,f.read_json(path))
  def account():
   record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
   if remaining()<=0:record.update(passed=False,status='budget_exceeded')
   if record['status']!='completed':
    record['passed']=False
    for row in rows:row['accepted']=False
  f.publish(REPORT,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
  print(f.canonical(dict(passed=record['passed'],status=record['status'],rows=[{key:row.get(key) for key in ('project','arm','status','accepted','charged_wall_seconds','charged_full_cpu_seconds')} for row in rows])));return 0 if record['passed'] else 2

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['prepare','worker','run','read','report'],required=True);ap.add_argument('--source-head',required=True);ap.add_argument('--protocol-sha256');ap.add_argument('--control-sha256');ap.add_argument('--project',choices=['ir-obstacle']);ap.add_argument('--arm',choices=list(ARMS));args=ap.parse_args()
 handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
 def interrupted(*_):raise KeyboardInterrupt
 try:
  for sig in handlers:signal.signal(sig,interrupted)
  with p.validation_readback_session():
   if args.mode=='prepare':prepare(args.source_head,args.control_sha256)
   else:
    plan=f.read_json(PROTOCOL);pin=p.sha(PROTOCOL)
    if plan['git_head']!=args.source_head or args.protocol_sha256!=pin:raise p.Rejected('exact frozen HEAD/protocol required')
    if args.mode in ('read','report'):raise SystemExit(read(plan,pin) if args.mode=='read' else report(plan,pin))
    if (args.project,args.arm) not in ORDER:raise p.Rejected('exact frozen eligible arm required')
    raise SystemExit(worker(plan,pin,args.project,args.arm) if args.mode=='worker' else execute(plan,pin,args.project,args.arm))
 finally:
  for sig,handler in handlers.items():signal.signal(sig,handler)
