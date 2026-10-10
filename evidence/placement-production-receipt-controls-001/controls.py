"""Offline copied actual schema3 receipt controls. No native/engine execution.

Every negative has its own complete run/source copy and must first pass relocated
positive readback. Only declared disposable mutations and path metadata change.
"""
from pathlib import Path
import copy,datetime,hashlib,json,resource,shutil,sys,time,uuid
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,sexpr as sx
BASE=ROOT/'.runs/placement-production-native-001';LIMIT=16*1024*1024;SECONDS=60
CASES=('positive','downgrade_floor_markers_present','erase_new_markers_floor_attempt','rehashed_planning_clearance','rehashed_area_prohibition','matched_via_low_settings_process','missing_ses','arbitrary_observer_process','wrong_generated_width','changed_candidate_rules','rehashed_blocking_report','stale_source_copy','rehashed_immutable_pad')
RAW_REPORTS={'source-drc.json','refill-drc.json','final-drc.json','metrics.json'}
def dump(path,value):p.save_json(path,value)
def cpu():
 own=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
 return own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime
def size(root):return sum(x.stat().st_size for x in root.rglob('*') if x.is_file())
def replace(value,replacements):
 if isinstance(value,str):
  for old,new in replacements:value=value.replace(old,new)
  return value
 if isinstance(value,list):return [replace(x,replacements) for x in value]
 if isinstance(value,dict):return {replace(k,replacements):replace(v,replacements) for k,v in value.items()}
 return value
def refresh(run,data):data['floor_evidence_hashes']=f.evidence_inventory(run);dump(run/'result.json',data)
def relocate(label,original,source):
 case=HERE/'cases'/label;case.mkdir(parents=True);run=case/'run';source_copy=case/'source'
 shutil.copytree(BASE,run);shutil.copytree(source.parent,source_copy)
 replacements=[(str(BASE),str(run)),(str(source.parent),str(source_copy))];modified=[]
 for path in sorted(run.glob('*.json')):
  if path.name in RAW_REPORTS:continue
  value=f.read_json(path);rebased=replace(value,replacements)
  if rebased!=value:dump(path,rebased);modified.append(path.name)
 data=f.read_json(run/'result.json');board=source_copy/source.name;task=sx.read(run/'floor-export-input'/source.name)
 guided,contract=f.policy_contract((run/'native.dsn').read_bytes(),f.read_json(run/'floor-export-context.json'),board.with_suffix('.kicad_pro').read_bytes(),task,data['source_hashes'])
 if guided!=(run/'floor-guided.dsn').read_bytes():raise ValueError('relocation changed floor geometry')
 dump(run/'floor-policy.json',contract);data['floor_policy']['sha256']=p.sha(run/'floor-policy.json')
 outputs,policy=pc.derive_chain(run,source.name,data['source_hashes'])
 for name,value in outputs.items():
  if value!=(run/name).read_bytes():raise ValueError('relocation changed declared chain '+name)
 dump(run/'placement-policy.json',policy);data['placement_policy']['sha256']=p.sha(run/'placement-policy.json')
 final=f.read_json(run/'floor-final-audit.json');final['native_context_sha256']=p.sha(run/'floor-final-context.json');dump(run/'floor-final-audit.json',final)
 refresh(run,data)
 checked=p.check_result(run/'result.json')
 raw_names=['native.dsn','floor-guided.dsn','placement-guided.dsn','planning-guided.dsn','task.dsn','routes.ses','imported.kicad_pcb','candidate/'+source.name,'refill/'+source.name,'source-drc.json','refill-drc.json','final-drc.json','metrics.json','engine.log','floor-export.log','final-drc.log']
 if any((run/name).read_bytes()!=(BASE/name).read_bytes() for name in raw_names):raise ValueError('unchanged relocation altered actual raw evidence')
 dump(case/'relocation.json',{'scope':'Synthetic path metadata rebinding of complete actual run/source; not a new execution','positive_readback':checked,'rebound_top_level_json':modified,'raw_selected_files_unchanged':raw_names,'source_copy_hashes':p.tree_hash(source_copy),'relocated_receipt_sha256':p.sha(run/'result.json')})
 return case,run,source_copy,data
def mutate_json(path,fn):
 value=f.read_json(path);fn(value);dump(path,value)
def change_process(run,data,name,fn):
 path=run/(name+'-process.json');value=f.read_json(path);fn(value);dump(path,value)
 step=next(x for x in data['steps'] if x['name']==name)
 for key,value in value.items():step[key]=value

def mutate(label,run,source,data):
 board=run/'candidate'/Path(data['source']).name
 if label=='downgrade_floor_markers_present':data.update(schema=2,input_policy='board-floors-v1');return ('downgraded placement policy',)
 if label=='erase_new_markers_floor_attempt':
  for path in list(run.iterdir()):
   if path.name.startswith(('placement-','planning-')):path.unlink()
  for key in list(data):
   if key.startswith(('placement_','planning_')):data.pop(key)
  data.update(schema=2,input_policy='board-floors-v1',scoring_variant=None)
  change_process(run,data,'floor-export',lambda x:x.update(argv=f.context_argv('export',run/'floor-export-input'/board.name,run/'floor-export-context.json',run/'native.dsn')))
  return ('adapter changed guided rules or geometry',)
 if label=='rehashed_planning_clearance':
  path=run/'planning-guided.dsn';raw=path.read_bytes();changed=raw.replace(b'(clearance 320)',b'(clearance 300)')
  if changed==raw:raise ValueError('planning atom fixture changed')
  path.write_bytes(changed)
  policy=f.read_json(run/'placement-policy.json');policy['outputs_sha256'][path.name]=p.sha(path);policy['planning']['output_sha256']=p.sha(path);dump(run/'placement-policy.json',policy);data['placement_policy']['sha256']=p.sha(run/'placement-policy.json')
  return ('placement planning/adapter bytes differ',)
 if label=='rehashed_area_prohibition':
  path=run/'placement-area-context.json';mutate_json(path,lambda x:x['zones'][0]['disallow'].update(tracks=True))
  policy=f.read_json(run/'placement-policy.json');policy['area_context_sha256']=p.sha(path);policy['removal']['observation_sha256']=hashlib.sha256(f.canonical(f.read_json(path)).encode()).hexdigest();dump(run/'placement-policy.json',policy);data['placement_policy']['sha256']=p.sha(run/'placement-policy.json')
  return ('source/native zone discrepancy: disallow',)
 if label=='matched_via_low_settings_process':
  settings=p.engine_profile_settings('completion-only',data['engine_budget']['remaining_outer_wall_seconds_at_assignment'],strict_class_targets=True,scoring_variant='via_low');settings.update(outer_task_wall_budget_seconds=data['budget_seconds'],outer_task_cpu_budget_seconds=data['cpu_budget_seconds']);data['engine_budget']=settings
  change_process(run,data,'engine',lambda x:x.update(argv=f.engine_argv(run,settings['argv'])))
  return ('floor engine configuration differs',)
 if label=='missing_ses':(run/'routes.ses').unlink();return ('retained SES transport',)
 if label=='arbitrary_observer_process':change_process(run,data,'floor-export',lambda x:x.update(argv=['/usr/bin/true']));return ('floor process provenance differs: floor-export',)
 if label=='wrong_generated_width':
  tree=sx.read(board);sx.one(sx.children(tree,'segment')[0],'width')[1]='0.2';sx.write(board,tree);data['candidate_sha256']=p.sha(board);return ('generated track differs from derived guidance',)
 if label=='changed_candidate_rules':
  mutate_json(board.with_suffix('.kicad_pro'),lambda x:x['board']['design_settings']['rule_severities'].update(clearance='warning'));return ('placement candidate tree changed',)
 if label=='rehashed_blocking_report':
  uid=sx.unquote(sx.one(sx.children(sx.read(board),'segment')[0],'uuid')[1]);violation={'type':'track_width','severity':'error','description':'deliberate offline semantic corruption control, not a new native finding','items':[{'uuid':uid,'description':'copied target','pos':{'x':0,'y':0}}]}
  mutate_json(run/'final-drc.json',lambda x:x['violations'].append(violation));data['native_report_sha256']=p.sha(run/'final-drc.json');data['native']=p.parse_report(run/'final-drc.json',board.name);data['native_rejection_reasons']=p.native_rejection_reasons(data['native']);data['whole_project_drc_clean']=False
  change_process(run,data,'final-drc',lambda x:x.update(exit_code=5,status='nonzero_exit'));return ('native findings reject candidate',)
 if label=='stale_source_copy':
  path=source/board.name;path.write_bytes(path.read_bytes()+b'\n; deliberately stale disposable source\n');return ('stale source project',)
 if label=='rehashed_immutable_pad':
  tree=sx.read(board);pad=sx.children(sx.children(tree,'footprint')[0],'pad')[0];sx.one(pad,'size')[1]='2.1';sx.write(board,tree);data['candidate_sha256']=p.sha(board);return ('immutable geometry changed',)
 raise ValueError(label)

def main():
 if (HERE/'cases').exists() or (HERE/'summary.json').exists():raise ValueError('refuse control collision')
 started=time.monotonic();cpu0=cpu();original=f.read_json(BASE/'result.json');source=Path(original['source']);before={'run':p.tree_hash(BASE),'source':p.tree_hash(source.parent),'tools':p.tool_manifest()}
 original_positive=p.check_result(BASE/'result.json')
 if original['candidate_sha256']!='4c118026360d23ecfffad6b4c8638aabf592f9534ca1e8cb999a77316dee09e1' or original['tools']['git_head']!='d6f7f81b129dbccd8d7201868782ac317c646fc2':raise ValueError('actual fixture binding differs')
 projected=len(CASES)*(size(BASE)+size(source.parent))+size(HERE)+256*1024
 if projected>LIMIT:raise ValueError('planned complete copies exceed16MiB')
 dump(HERE/'original-bindings.json',before)
 summary={'schema':1,'status':'running','passed':False,'scope':'Offline synthetic relocation/tampering of actual schema3 native evidence; no authentication or fresh native execution','native_executed':False,'engine_executed':False,'original_positive':original_positive,'base_run':str(BASE),'base_result_sha256':p.sha(BASE/'result.json'),'base_source':str(source),'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'disk_ceiling_bytes':LIMIT,'projected_copy_bytes':projected,'cases':[]}
 def bound():
  if time.monotonic()-started>SECONDS or cpu()-cpu0>SECONDS:raise ValueError('offline control time/CPU ceiling')
  if size(HERE)>LIMIT:raise ValueError('offline artifact16MiB ceiling')
 def stable():
  if p.tree_hash(BASE)!=before['run'] or p.tree_hash(source.parent)!=before['source'] or p.tool_manifest()!=before['tools']:raise ValueError('original input/code/tools changed')
 try:
  for label in CASES:
   bound();row={'case':label,'positive_relocated':False,'expected_negative':label!='positive','passed':False}
   try:
    case,run,copied_source,data=relocate(label,original,source);row['positive_relocated']=True
    if label=='positive':row.update(outcome='accepted unchanged relocated evidence',passed=True)
    else:
     expected=mutate(label,run,copied_source,data);row['expected_reason_fragments']=list(expected);refresh(run,data)
     try:verdict=p.check_result(run/'result.json')
     except Exception as exc:
      row.update(outcome='rejected',reason=type(exc).__name__+': '+str(exc),passed=any(x in str(exc) for x in expected))
     else:row.update(outcome='UNEXPECTED ACCEPTANCE',verdict=verdict)
    row['receipt_sha256']=p.sha(run/'result.json');dump(case/'control.json',row)
   except Exception as exc:row.update(outcome='relocation/control failure, not a negative pass',reason=type(exc).__name__+': '+str(exc))
   summary['cases'].append(row);dump(HERE/'progress.json',summary)
   if not row['passed']:break
  stable();bound();summary.update(status='passed' if len(summary['cases'])==len(CASES) and all(x['passed'] for x in summary['cases']) else 'failed',original_run_source_code_tools_unchanged=True)
  summary['passed']=summary['status']=='passed'
 except (Exception,KeyboardInterrupt) as exc:summary.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',passed=False,reason=type(exc).__name__+': '+str(exc))
 summary.update(wall_seconds=time.monotonic()-started,total_cpu_seconds=cpu()-cpu0,stored_bytes=size(HERE),accounting_point='before final publication/freshness; final caps include both')
 try:
  stable();bound();expected=f.canonical(summary);dump(HERE/'summary.json',summary);stable();bound()
  if f.canonical(f.read_json(HERE/'summary.json'))!=expected:raise ValueError('control summary changed during publication')
 except (Exception,KeyboardInterrupt) as exc:
  for path in (HERE/'summary.json',HERE/'summary.json.partial'):
   if path.exists():path.rename(HERE/('invalidated-'+uuid.uuid4().hex+'-'+path.name))
  summary.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'invalidated',passed=False,reason=type(exc).__name__+': '+str(exc))
  dump(HERE/'summary.json',summary)
 print(json.dumps({'status':summary['status'],'passed':summary['passed'],'cases':summary['cases'],'wall_seconds':summary['wall_seconds'],'total_cpu_seconds':summary['total_cpu_seconds'],'stored_bytes':summary['stored_bytes']},indent=2))
 return summary['passed']
if __name__=='__main__':raise SystemExit(0 if main() else 1)
