"""One fresh normal literal-composite positive and one actual Native target negative."""
from pathlib import Path
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
import sys,copy,json,shutil
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,config as c,placement_clearance as pc,local_settings as ls
from experiments.netclass_parent_transport_v1 import fixture
from experiments.placement_handoff_native_v1.driver import copy_bytes
from autorouter import netclass as nc
OUT=ROOT/'.runs/literal-composite-native-controls-001'
CAP=150.
def require(value,reason):
 if not value:raise p.Rejected(reason)
def check(out,result):
 """Pure existing-helper replay; no Native/engine execution."""
 require(result['kind']=='literal-composite-native-controls-v1' and result['controls_passed'] is True,'controls incomplete')
 source=out/'original/fixture.kicad_pcb';hashes=result['source_hashes'];require(p.tree_hash(source.parent)==hashes,'control source changed')
 data=f.read_json(out/'positive/result.json');require(data['accepted'] is True,'fresh positive missing')
 checked=p.check_result(out/'positive/result.json');candidate=Path(checked['candidate']);require(checked['candidate_sha256']==result['positive_candidate_sha256'],'positive changed')
 mapping=f.read_json(out/'positive/final-netclasses.json');project=f.read_json(source.with_suffix('.kicad_pro'))
 require(set(x['class'] for x in mapping['nets'])=={'Default','Power,Default'},'positive did not exercise exact composite')
 require(nc.audit_dsn(out/'positive/task.dsn',f.read_json(out/'positive/export-netclasses.json'),project)['passed'] is True,'positive DSN identity differs')
 folder=out/'negative';negative=folder/'candidate'/source.name;before=folder/'pre-refill.kicad_pcb';saved=folder/'refill'/source.name
 require(p.sha(negative)==result['negative_candidate_sha256'],'negative changed')
 require(p.immutable(sx.read(negative))==p.immutable(sx.read(source)),'negative changed original geometry')
 p.verify_candidate_files(negative,hashes)
 native=f.check_drc_stage(folder,{'steps':result['negative_steps']},'refill-drc',saved,saved,True,{**hashes,source.name:p.sha(before)},sandboxed=False)
 require(native==result['negative_saved_native'],'negative saved Native changed')
 require((sx.dump(p.transplant_fill(sx.read(before),sx.read(saved)))+'\n').encode()==pc.read_bytes(negative),'negative saved refill differs')
 process=f.read_json(folder/'final-netclasses-process.json')
 f.process_check(folder,{'steps':result['negative_steps']},'final-netclasses',[str(c.PYTHON),str(ROOT/'autorouter/native.py'),'netclasses',str(negative),str(folder/'final-netclasses.json')])
 observed=f.read_json(folder/'final-netclasses.json')
 try:p.audit_candidate_netclasses(negative,[],observed)
 except p.Rejected as exc:require('generated track differs from native netclass target' in str(exc),'negative rejected for unexpected cause')
 else:raise p.Rejected('below-target composite track was accepted')
 require(result['negative_expected_rejection']=='generated track differs from native netclass target','negative result differs')
 binding=f.read_json(folder/'refill-drc-binding.json');ls.check_event(folder,binding,f.read_json(folder/'refill-drc-process.json'))
 require(result['source_hashes']==p.tree_hash(source.parent),'source changed during checks')
 return dict(passed=True,positive_candidate_sha256=p.sha(candidate),negative_candidate_sha256=p.sha(negative),new_native_execution=False,original_rules_preserved=True,native_composite_identity_preserved=True)
def main():
 OUT.mkdir();result=dict(schema=1,kind='literal-composite-native-controls-v1',status='incomplete',accepted=False,controls_passed=False,tools=p.tool_manifest(),source_unchanged=False,physical_electrical_approval=False)
 try:
  files,recipe=fixture.prepare(protected=False);tree=sx.parse(files['fixture.kicad_pcb'].decode());project=json.loads(files['fixture.kicad_pro'])
  changes={'"/PWR_PAIR"':'"PWR_PAIR"','"/SIG_PAIR"':'"SIG_PAIR"','"/DEFAULT_PAIR"':'"DEFAULT_PAIR"'}
  def rename(node):
   for i,value in enumerate(node):
    if isinstance(value,list):rename(value)
    elif value in changes:node[i]=changes[value]
  rename(tree)
  default,power=project['net_settings']['classes'][:2];power['name']='Power'
  project['net_settings']['classes']=[default,power];project['net_settings']['netclass_patterns']=[dict(pattern='PWR_PAIR',netclass='Power')]
  files['fixture.kicad_pcb']=(sx.dump(tree)+'\n').encode();files['fixture.kicad_pro']=(json.dumps(project,indent=2)+'\n').encode()
  copy_bytes(files,OUT/'original');source=OUT/'original/fixture.kicad_pcb';hashes=p.tree_hash(source.parent)
  result.update(source=str(source),source_hashes=hashes,source_recipe=recipe,source_transform='Narrow existing owned three-pair fixture to two source classes and exact literal PWR_PAIR assignment; rename three source net identifiers consistently, preserve source geometry/rules/notices. No benchmark board used.')
  positive=p.route(source,OUT/'positive',90,False,'both','completion-only',scoring_variant='via_high')
  require(positive['accepted'] is True,'fresh normal positive rejected: '+str(positive.get('reason')))
  checked=p.check_result(OUT/'positive/result.json');valid=Path(checked['candidate']);result.update(positive_candidate_sha256=p.sha(valid),positive_native=positive['native'],positive_metrics=positive['metrics'])
  folder=OUT/'negative';job=p.Job(folder,max(1,CAP-max(time.monotonic()-START,cpu()-CPU0)),protect_local_settings=True)
  shutil.copytree(valid.parent,folder/'candidate');negative=folder/'candidate'/source.name;changed=sx.read(negative)
  routes=[x for x in p.routes(changed) if x[0]=='segment' and sx.unquote(sx.one(x,'net')[1])=='PWR_PAIR']
  require(bool(routes),'positive had no generated Power segment');route=routes[0];old=copy.deepcopy(route);sx.one(route,'width')[1]='0.5';sx.write(negative,changed)
  result['negative_mutation']=dict(original_route=old,changed_route=copy.deepcopy(route),original_track_floor_mm=project['board']['design_settings']['rules']['min_track_width'],native_power_target_mm=power['track_width'],changed_mm=.5)
  try:p.validate_candidate(job,sx.read(source),negative,hashes,[])
  except p.Rejected as exc:require('generated track differs from native netclass target' in str(exc),'unexpected negative refusal: '+str(exc))
  else:raise p.Rejected('negative unexpectedly accepted')
  saved=folder/'refill'/source.name
  result.update(negative_candidate_sha256=p.sha(negative),negative_steps=job.steps,negative_saved_native=f.check_drc_stage(folder,{'steps':job.steps},'refill-drc',saved,saved,True,{**hashes,source.name:p.sha(folder/'pre-refill.kicad_pcb')},sandboxed=False),negative_expected_rejection='generated track differs from native netclass target',controls_passed=True,status='completed')
  result['shared_checks']=check(OUT,result)
  require(p.tool_manifest()==result['tools'],'tools changed');result['source_unchanged']=p.tree_hash(source.parent)==hashes
  require(result['source_unchanged'] and max(time.monotonic()-START,cpu()-CPU0)+2<=CAP,'control source/budget changed')
 except BaseException as exc:result.update(controls_passed=False,status='failed',reason=type(exc).__name__+': '+str(exc))
 result.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,actor_sha256=p.sha(Path(__file__)),publication_allowance_seconds=2)
 p.save_json(OUT/'result.json',result);print(json.dumps({k:result.get(k) for k in ('status','controls_passed','reason','wall_seconds','full_cpu_seconds')}));return 0 if result['controls_passed'] else 2
if __name__=='__main__':raise SystemExit(main())
