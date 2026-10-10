"""Read-only audit of retained native controls; launches no native/engine worker."""
from pathlib import Path
import json,sys,hashlib,math,copy
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx,floor_route as f,board_floor as g,config as c
HERE=Path(__file__).resolve().parent
RUN=ROOT/'.runs/board-floor-production-controls-native-001'
read=lambda path:json.loads(path.read_text())
checks=[]
def ok(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
def uid(node):return sx.unquote(sx.one(node,'uuid')[1])
def main():
 data=read(RUN/'summary.json');source=Path(data['source']);positive=Path(data['positive_result']);before={str(x):p.tree_hash(x) for x in (RUN,source.parent,positive.parent)}
 freeze=data['freeze'];original=sx.read(source);pos=read(positive);board=Path(pos['candidate']);original_routes={uid(n):n for n in p.routes(sx.read(board))};original_project=read(board.with_suffix('.kicad_pro'))
 ok('summary exact five completed controls and honest diagnostic scope',data['status']=='completed' and data['controls_passed'] is True and data['routing_accepted'] is False and data['new_engine_execution'] is False and [x['case'] for x in data['cases']]==['positive','narrow_track','small_via','missing_via','changed_rule'])
 ok('original full source and positive inventories unchanged',freeze['source']==p.tree_hash(source.parent)==p.tree_hash(RUN/'source') and freeze['positive']==p.tree_hash(positive.parent) and freeze['candidate']==p.tree_hash(board.parent)==p.tree_hash(RUN/'positive-candidate'))
 ok('copied frozen code inventory',freeze['code']==p.tree_hash(RUN/'code'))
 ok('exact reviewed control driver',p.sha(RUN/'code/driver.py')=='2603edf856ddc09ce3d866a59b4928083073a2907c8d1fa10a0c2942c06afa6d')
 ok('frozen production implementation bytes',all(p.sha(RUN/'code'/k)==v for k,v in freeze['tools']['implementation_sha256'].items()))
 ok('positive receipt and candidate hashes',p.sha(positive)==data['positive_result_sha256'] and p.sha(board)==data['positive_candidate_sha256']=='79c46687d355a60f3917794f277ef41fb839088622123784dddc55c13e23af06')
 expected_counts={'positive':(0,0,0,0),'narrow_track':(0,1,1,0),'small_via':(0,2,0,0),'missing_via':(1,0,2,0),'changed_rule':(0,0,0,0)}
 reasons={'narrow_track':'generated track differs from derived guidance','small_via':'generated via differs from derived guidance/floor','changed_rule':'native context/source/DSN byte binding mismatch'}
 for row in data['cases']:
  case=row['case'];base=RUN/case;expect=row['expected'];diag=base/'diagnostic';candidate=diag/'candidate'/board.name;native=p.parse_report(diag/'diagnostic-drc.json',board.name)
  ok(case+': completed case inventory and record',p.tree_hash(base)==data['completed_evidence'][str(base)] and row==read(base/'case.json'))
  ok(case+': raw report and exact counters',native==row['native'] and tuple(native[k] for k in ('opens','blocking','warnings','exclusions'))==expected_counts[case] and native['ignored_checks']==pos['native']['ignored_checks'])
  ok(case+': actual candidate/project hashes',p.sha(candidate)==expect['board_sha256'] and p.sha(candidate.with_suffix('.kicad_pro'))==expect['project_sha256'])
  altered=sx.read(candidate);ok(case+': immutable board unchanged',p.immutable(altered)==p.immutable(sx.read(board)))
  wanted=copy.deepcopy(original_routes)
  if case=='narrow_track':sx.one(wanted[expect['target_uuid']],'width')[1]='0.2'
  if case=='small_via':sx.one(wanted[expect['target_uuid']],'size')[1]='0.6'
  if case=='missing_via':del wanted[expect['target_uuid']]
  ok(case+': only exact intended route mutation',{uid(n):n for n in p.routes(altered)}==wanted)
  wanted_project=copy.deepcopy(original_project)
  if case=='changed_rule':wanted_project['board']['design_settings']['rule_severities']['track_width']='warning'
  ok(case+': exact project severity change only',read(candidate.with_suffix('.kicad_pro'))==wanted_project)
  if case in reasons:
   val=base/'validation';vb=val/'candidate'/board.name
   try:f.validate_contract(original,vb,freeze['source'],[],read(val/'floor-policy.json'),val)
   except (p.Rejected,ValueError) as exc:actual_reason=str(exc)
   else:actual_reason=None
   ok(case+': pure production contract reason independently reproduced',actual_reason==reasons[case] and row['production_steps']==[] and row['production_rejection'].endswith(': '+actual_reason))
  else:
   val=base/'validation';vb=val/'candidate'/board.name;raw=p.parse_report(val/'final-drc.json',board.name)
   ok(case+': separately retained final native report',raw==native==row['production_native'] and p.sha(vb)==expect['board_sha256'])
   f.validate_contract(original,vb,freeze['source'],[],read(val/'floor-policy.json'),val)
   context=read(val/'floor-final-context.json');policy=g.qualify(read(vb.with_suffix('.kicad_pro')),context,g.task_from_source(original))
   audit={'candidate_sha256':p.sha(vb),'native_context_sha256':p.sha(val/'floor-final-context.json'),'generated':g.audit_generated_routes(sx.read(vb),policy),'native_routes':g.audit_native_routes(sx.read(vb),context)}
   ok(case+': exact final native route audit',audit==read(val/'floor-final-audit.json'))
  for item in (row['diagnostic_binding'],row.get('production_binding')):
   if item is None:continue
   directory=diag if item is row['diagnostic_binding'] else val;name='diagnostic-drc' if directory==diag else 'final-drc';bind=read(directory/(name+'-binding.json'));native_board=Path(bind['input'])
   ok(case+': '+name+' binding hashes/input/project',p.sha(directory/(name+'.json'))==item['native_report_sha256'] and p.sha(directory/(name+'-binding.json'))==item['native_binding_sha256'] and p.tree_hash(native_board.parent)==item['input_hashes']==bind['after'] and p.sha(native_board)==expect['board_sha256'] and p.sha(native_board.with_suffix('.kicad_pro'))==expect['project_sha256'])
  if case=='missing_via':
   refs=set(expect['adjacent_route_uuids']);ok('missing via: native open names both actual adjacent routes',any(x['type']=='unconnected_items' and x['severity']=='error' and refs=={i['uuid'] for i in x['items']} for x in native['findings']))
  elif case in ('narrow_track','small_via'):
   kind='track_width' if case=='narrow_track' else 'via_diameter';ok(case+': native error names exact mutated UUID',any(x['type']==kind and x['severity']=='error' and expect['target_uuid'] in {i['uuid'] for i in x['items']} for x in native['findings']))
 for step in data['steps']:
  directory=Path(step['cwd']);name=step['name'];stored=read(directory/(name+'-process.json'))
  ok('process binding '+str(directory.relative_to(RUN))+'/'+name,all(step[k]==v for k,v in stored.items()) and stored['argv'][:3]==f.SANDBOX and stored['cleanup_complete'] is True and stored['status']==('success' if stored['exit_code']==0 else 'nonzero_exit') and stored['exit_code'] in (0,5))
  if name.endswith('-drc'):
   binding=read(directory/(name+'-binding.json'));raw=p.parse_report(directory/(name+'.json'),board.name);saved=binding['saved'];inputboard=Path(binding['input'])
   argv=[*f.SANDBOX,str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(directory/(name+'.json')),*(['--save-board'] if saved else []),str(inputboard)]
   ok('exact native command/input '+str(directory.relative_to(RUN))+'/'+name,stored['argv']==argv and stored['exit_code']==(5 if raw['findings'] else 0) and p.tree_hash(inputboard.parent)==binding['after'] and binding['before']['fixture.kicad_pro']==binding['after']['fixture.kicad_pro'])
 ok('finite recorded resource totals below shared ceilings',data['budget_seconds']==data['cpu_budget_seconds']==60 and all(math.isfinite(data[k]) and 0<data[k]<=60 for k in ('wall_seconds','total_cpu_seconds')) and data['within_budget'] is True)
 ok('child CPU consistent and not double-counted',abs(sum(x['cpu_seconds'] for x in data['steps'])-data['child_step_cpu_seconds'])<1e-9 and data['total_cpu_seconds']>=data['child_step_cpu_seconds'])
 ok('audit unchanged every original byte',all(p.tree_hash(Path(k))==v for k,v in before.items()))
 out={'schema':1,'audit_passed':True,'native_executed_by_reviewer':False,'checks':checks,'count':len(checks),'run':str(RUN),'summary_sha256':p.sha(RUN/'summary.json'),'before':before,'wall_seconds_recorded':data['wall_seconds'],'cpu_seconds_recorded':data['total_cpu_seconds'],'scope':'Actual retained native findings independently rebound offline. Recorded totals predate final publication checks; no separate enclosing invocation timer. Zero-zone exposed fixture, not new routing/comparison/electrical qualification.'}
 with (HERE/'audit.json').open('x') as stream:json.dump(out,stream,indent=2);stream.write('\n')
 print(json.dumps({k:v for k,v in out.items() if k not in ('before','checks')},indent=2))
if __name__=='__main__':main()
