"""Post-fix synthetic receipt + shared validation/export stage controls.
Fabricated native-process seams ONLY. No native, subprocess or solver runs.
Reuses stored original/candidate/final report, never reconstructs native work.
"""
from pathlib import Path
from unittest.mock import patch
import copy,json,shutil,sys,hashlib
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p, routing_scope as rs, sexpr as sx, floor_route as f, review_export as e
OWN=Path(__file__).resolve().parent;run=OWN/'synthetic/run';receipt=run/'result.json'
FILES=['autorouter/pipeline.py','autorouter/routing_scope.py','autorouter/preferences.py','autorouter/review_export.py','autorouter/floor_route.py','autorouter/__main__.py']
initial={x:p.sha(ROOT/x) for x in FILES};results=[];before=p.tree_hash(OWN/'synthetic')
data=json.loads(receipt.read_text());source=Path(data['source']);candidate=Path(data['candidate']);original=sx.read(source);final=sx.read(candidate);protected=rs.protected_routes(original,['SEL'])
# Add only the now-mandatory import reconciliation through existing pure helper.
imported=run/'imported.kicad_pcb';imported.write_bytes(candidate.read_bytes());audit={'imported_sha256':p.sha(imported)}
p.transplant_routes(original,sx.read(imported),protected=protected,audit=audit,policy='exact_non_uuid_lock_position_v2');data['protected_route_import']=audit
for file,key in [('native.dsn','native_dsn_sha256'),('task.dsn','task_dsn_sha256')]:
 (run/file).write_text('Synthetic retained export; NOT a native DSN.\n');data[key]=p.sha(run/file)

def check(label,change=None,expected='reject'):
 d=copy.deepcopy(data)
 if change:change(d)
 p.save_json(receipt,d)
 try:
  with patch('subprocess.run',side_effect=AssertionError('forbidden subprocess')),patch('subprocess.Popen',side_effect=AssertionError('forbidden subprocess')):v=p.check_result(receipt)
  outcome='current'
 except (p.Rejected,ValueError,KeyError,FileNotFoundError) as exc:outcome='reject';v={'type':type(exc).__name__,'reason':str(exc)}
 entry={'case':label,'expected':expected,'outcome':outcome,'matched':outcome==expected,'detail':v};results.append(entry);print(json.dumps(entry,sort_keys=True))
check('same retained selected legacy Default/parity positive after mandatory import reconciliation',expected='current')
check('missing mandatory native export hash',lambda d:d.pop('native_dsn_sha256'))
check('missing mandatory task export hash',lambda d:d.pop('task_dsn_sha256'))
def removeboth(d):d.pop('native_dsn_sha256');d.pop('task_dsn_sha256')
check('previous both-DSN-field downgrade',removeboth)
check('protected import reconciliation downgrade',lambda d:d.pop('protected_route_import'))
check('rehashed incorrect protected import reconciliation',lambda d:d['protected_route_import'].update(transplanted_routes_sha256='0'*64))
p.save_json(receipt,data)
# Complete export validation stage seam using real shared helper, original files,
# exact all-severity argv and fabricated raw reports/processes. No native tool.
metrics=data['metrics'];raw={'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':candidate.name,'included_severities':['error','warning','exclusion'],'ignored_checks':[],'violations':[],'unconnected_items':[],'schematic_parity':[]}
outer=OWN/'stage-seams';outer.mkdir();active={};calls=[]
def fake_run(argv,*,cwd,log,**kwargs):
 name=log.stem;calls.append({'stage':name,'argv':argv,'case':active.get('case')});log.write_bytes(b'')
 if name in ('refill-drc','final-drc'):
  p.save_json(Path(argv[argv.index('--output')+1]),raw)
  if name=='refill-drc' and active.get('mutation'):
   target=active['candidate'];tree=sx.read(target)
   if active['mutation']=='unselected':tree.append(['segment',['start','3','1'],['end','4','1'],['width','0.2'],['layer','"F.Cu"'],['net','2'],['uuid','"00000000-0000-0000-0000-000000000005"']])
   elif active['mutation']=='protected_loss':tree.remove(next(row for row in p.routes(tree) if sx.one(row,'net')==['net','2']))
   sx.write(target,tree)
 elif name=='metrics':p.save_json(Path(argv[-1]),metrics)
 else:raise AssertionError('unexpected stage '+name)
 return {'argv':argv,'cwd':str(cwd),'log':str(log),'log_bytes':0,'log_truncated':False,'status':'success','exit_code':0,'cleanup_complete':True,'wall_seconds':0.01,'cpu_seconds':0.01,'monitor_cpu_seconds':0.001}

def stage(label,mutation=None):
 folder=outer/label;job=e.ExportJob(folder,120,lambda:120);shutil.copytree(candidate.parent,folder/'candidate');target=folder/'candidate'/candidate.name;active.update(case=label,mutation=mutation,candidate=target);count=len(calls)
 try:
  with patch.object(e,'run',side_effect=fake_run),patch('subprocess.run',side_effect=AssertionError('forbidden subprocess')),patch('subprocess.Popen',side_effect=AssertionError('forbidden subprocess')):
   digest,native=p.validate_candidate(job,original,target,data['source_hashes'],protected,selected_names=['SEL'],schematic_parity=True)
   job.native('metrics','metrics',target,folder/'metrics.json')
  outcome='returned';detail={'sha256':digest,'native':native}
 except (p.Rejected,ValueError,KeyError) as exc:outcome='reject';detail={'type':type(exc).__name__,'reason':str(exc)}
 expected='reject' if mutation else 'returned';entry={'case':label,'expected':expected,'outcome':outcome,'matched':expected==outcome,'fabricated_stage_calls':len(calls)-count,'detail':detail};results.append(entry);print(json.dumps(entry,sort_keys=True))
 if mutation:return
 binding={'source':str(source),'validated_candidate':str(candidate),'validated_candidate_sha256':data['candidate_sha256'],'source_hashes':data['source_hashes']}
 record={'candidate':str(target),'candidate_sha256':digest,'native':native,'native_report_sha256':p.sha(folder/'final-drc.json'),'metrics':metrics,'steps':job.steps,'wall_seconds':1.,'budget_seconds':120,'cpu_budget_seconds':120,'parent_cpu_seconds':0.1,'child_step_cpu_seconds':0.03,'monitor_cpu_seconds':0.003,'total_cpu_seconds':0.133,'project_file':str(target.with_suffix('.kicad_pro')),'whole_project_drc_clean':True,'original_geometry_and_routing_unchanged':True,'source_hashes':data['source_hashes'],'original_routing_receipt_compute':{k:data.get(k) for k in ['budget_seconds','cpu_budget_seconds','wall_seconds','total_cpu_seconds']},'preview_board_sha256':data['candidate_sha256'],'final_sha_changed_after_refill':digest!=data['candidate_sha256'],'output_ceiling_bytes':e.OUTPUT_BYTES,'output_file_ceiling':e.OUTPUT_FILES,'schematic_parity':'checked by final native DRC'}
 for claim in ['checked by final native DRC','not checked',None]:
  altered=copy.deepcopy(record)
  if claim is None:altered.pop('schematic_parity')
  else:altered['schematic_parity']=claim
  try:e.check_stage(folder,altered,binding,data,None,None,None);outcome='returned';detail={}
  except (p.Rejected,ValueError,KeyError) as exc:outcome='reject';detail={'type':type(exc).__name__,'reason':str(exc)}
  expected='returned' if claim=='checked by final native DRC' else 'reject';entry={'case':'fresh selected export parity metadata '+str(claim),'expected':expected,'outcome':outcome,'matched':expected==outcome,'detail':detail};results.append(entry);print(json.dumps(entry,sort_keys=True))
stage('complete-export-stage')
stage('postrefill-extra-unselected','unselected')
stage('postrefill-protected-loss','protected_loss')
p.save_json(OWN/'postfix-results.json',{'kind':'pure synthetic consistency/stage seams only','native_validation_performed':False,'subprocesses_executed':0,'synthetic_before':before,'synthetic_after':p.tree_hash(OWN/'synthetic'),'source_sha256_before':initial,'source_sha256_after':{x:p.sha(ROOT/x) for x in FILES},'results':results,'fabricated_stage_calls':calls})
