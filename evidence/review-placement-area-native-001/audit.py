"""Read-only retained native bindings and pure transform check; no native jobs."""
from pathlib import Path
import sys,json,hashlib,importlib.util,math
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx,floor_route as f,config as c
HERE=Path(__file__).resolve().parent;RUN=ROOT/'.runs/placement-area-native-001';read=lambda p:json.loads(p.read_text());checks=[]
def ok(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
def byte_tree(path):return {k:(path/k).read_bytes() for k in p.tree_hash(path)}
def main():
 data=read(RUN/'summary.json');before=p.tree_hash(RUN);fr=data['freeze'];positive=ROOT/'.runs/board-floor-production-native-001/result.json';prior=read(positive);orig=Path(prior['source']);old=p.tree_hash(orig.parent)
 ok('false qualification and correct four outcomes',data['controls_passed'] is False and data['adapter_policy_qualified'] is False and data['engine_executed'] is False and [(r['case'],r['passed']) for r in data['cases']]==[('allowed_placement',True),('track_prohibited',False),('via_prohibited',False),('mixed',False)])
 ok('source/positive/code/fixed fixtures unchanged',p.tree_hash(positive.parent)==fr['positive'] and old==fr['original_source'] and p.tree_hash(RUN/'fixtures')==fr['fixtures'] and p.tree_hash(RUN/'code')==fr['code'])
 ok('actual reviewed worker/driver bytes',p.sha(RUN/'code/driver.py')=='4596891c758613610193f65fe5b9d72547dd2bc8594d4152f6f3222f8f7c9089' and p.sha(RUN/'code/native_areas.py')=='1c20e255b69eea8bb9ddd0ae864bbed5ac7797719866de4fc51e3bc326913771')
 modpath=ROOT/'.runs/review-placement-area-001/transform-snapshot-002/placement_transform.py';ok('reviewed pure transform fixed version',p.sha(modpath)=='493616a7328f2a7486d571d39fd3aa04b66f7e8548eee1997b0765f82d0dd003');spec=importlib.util.spec_from_file_location('review_transform',modpath);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 transforms=[];counts=[]
 for row in data['cases']:
  case=row['case'];directory=RUN/case;board=directory/'candidate/fixture.kicad_pcb';source=Path(row['source']);obs=read(directory/'areas.json');raw=(directory/'native.dsn').read_bytes();native=p.parse_report(directory/'diagnostic-drc.json',board.name);bind=read(directory/'diagnostic-drc-binding.json');copied=Path(bind['input']);expected=row['expected'];tree=p.tree_hash(board.parent)
  ok(case+': entire completed case retained',p.tree_hash(directory)==data['completed_evidence'][str(directory)] and read(directory/'case.json')==row)
  ok(case+': source/candidate complete project equal',p.tree_hash(source.parent)==tree==row['source_hashes'] and p.sha(board)==expected['board_sha256'])
  ok(case+': original rules exactly preserved/error enabled',p.sha(board.with_suffix('.kicad_pro'))==data['original_project_sha256'] and read(board.with_suffix('.kicad_pro'))['board']['design_settings']['rule_severities']['items_not_allowed']=='error')
  ok(case+': exact fresh native area export binding',obs==row['area_observation'] and obs['source']==str(board) and obs['board_sha256']==p.sha(board) and obs['project_sha256']==p.sha(board.with_suffix('.kicad_pro')) and obs['input_hashes_before']==obs['input_hashes_after']==tree and obs['dsn_sha256']==p.sha(directory/'native.dsn') and obs['board_saved'] is False)
  ok(case+': exact source/native area census',sorted(obs['zones'],key=lambda x:x['uuid'])==sorted(expected['zones'],key=lambda x:x['uuid']) and obs['footprint_zone_count']==obs['footprint_rulearea_count']==0)
  ok(case+': fresh raw native zero findings',native==row['native'] and all(native[k]==0 for k in ('opens','blocking','warnings','exclusions')) and native['findings']==[] and native['ignored_checks']==prior['native']['ignored_checks'])
  ok(case+': DRC board/project inventory exact',bind['source']==str(board) and bind['before']==tree and bind['saved'] is False and p.tree_hash(copied.parent)==bind['after'] and all(bind['after'].get(k)==v for k,v in tree.items()) and p.sha(copied)==p.sha(board) and set(bind['after'])-set(tree)<={'fixture.kicad_prl'})
  cmds={'area-export':[*f.SANDBOX,str(c.PYTHON),'-B',str(RUN/'code/native_areas.py'),str(board),str(directory/'areas.json'),str(directory/'native.dsn')], 'diagnostic-drc':[*f.SANDBOX,str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(directory/'diagnostic-drc.json'),str(copied)]}
  for name,argv in cmds.items():
   f.process_check(directory,data,name,argv);checks.append(case+': exact '+name+' process/step/argv')
  parsed=m._parse_dsn(raw.decode());entries=m.keepouts(parsed);kinds=[e['node'][0] for e in entries];counts.append({'case':case,'keepout_kinds':kinds,'findings':[],'control_passed':row['passed']})
  try:
   output,receipt=m.transform(byte_tree(source.parent),byte_tree(board.parent),board.name,obs,raw,raw)
   outcome={'case':case,'pure_transform_passed':True,'removed':receipt['removed_count'],'routing_accepted':False,'native_qualification':False}
   ok(case+': no unsafe positive on failed negatives',case=='allowed_placement' and receipt['removed_count']==2)
  except ValueError as e:
   outcome={'case':case,'pure_transform_passed':False,'reason':str(e)};ok(case+': expected conservative transform rejection',case!='allowed_placement')
  transforms.append(outcome)
 ok('finite shared recorded resources within caps',all(math.isfinite(data[k]) and 0<data[k]<=60 for k in ('wall_seconds','total_cpu_seconds')) and data['budget_seconds']==data['cpu_budget_seconds']==60)
 ok('child CPU sum reconciles without double count',abs(sum(s['cpu_seconds'] for s in data['steps'])-data['native_step_cpu_seconds'])<1e-9 and data['total_cpu_seconds']>=data['native_step_cpu_seconds'])
 ok('review read-only input inventories',p.tree_hash(RUN)==before and p.tree_hash(orig.parent)==old)
 result={'schema':1,'audit_passed':True,'native_controls_passed':False,'native_or_engine_executed_by_reviewer':False,'count':len(checks),'checks':checks,'summary_sha256':p.sha(RUN/'summary.json'),'before':before,'cases':counts,'pure_transform_on_actual_area_observations':transforms,'transform_scope':'Pure attribution probe only; raw is also passed as guided input, so this is not a floor-guidance chain or a production routing acceptance test. Negative native controls remain failed.','wall_seconds_recorded':data['wall_seconds'],'cpu_seconds_recorded':data['total_cpu_seconds'],'accounting_point':data['accounting_point']}
 with (HERE/'audit.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('before','checks')},indent=2))
if __name__=='__main__':main()
