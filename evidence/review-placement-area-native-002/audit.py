"""Offline AI audit of retained actual002; no native invocation."""
from pathlib import Path
import sys,json,copy,math
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx,floor_route as f,config as c,board_floor as g
HERE=Path(__file__).resolve().parent;RUN=ROOT/'.runs/placement-area-native-002';OLD=ROOT/'.runs/placement-area-native-001'
read=lambda x:json.loads(x.read_text());checks=[]
def ok(label,test):
 if not test:raise AssertionError(label)
 checks.append(label)
def main():
 data=read(RUN/'summary.json');old=read(OLD/'summary.json');before=p.tree_hash(RUN);prior=p.tree_hash(OLD);fr=data['freeze']
 ok('exact diagnostic denominator and no qualification',data['status']=='completed' and data['controls_passed'] is True and [r['case'] for r in data['cases']]==['track_prohibited','via_prohibited','mixed'] and all(data[k] is False for k in ('routing_accepted','comparison_eligible','adapter_policy_qualified','constraint_qualification_passed','adapter_transformation_performed','engine_executed')))
 ok('original failed run entire inventory bound',prior==fr['actual001'] and p.sha(OLD/'summary.json')==data['actual001_summary_sha256']=='c61d54b5508f0508528e1236ead7bf97ad21ef336e32448994c6239db56b058f')
 ok('historical recorded source/code/case inventories unchanged',all(p.tree_hash(OLD/k)==old['freeze'][k] for k in ('fixtures','code')) and all(p.tree_hash(Path(k))==v for k,v in old['completed_evidence'].items()))
 ok('reviewed code exact',p.tree_hash(RUN/'code')==fr['code'] and p.sha(RUN/'code/driver.py')=='c8fd3aba64473bc3717d89c659727aa4a13c681a96646e5a478aba41121f4c36' and p.sha(RUN/'code/native_areas.py')=='1c20e255b69eea8bb9ddd0ae864bbed5ac7797719866de4fc51e3bc326913771')
 for rel,digest in fr['tools']['implementation_sha256'].items():ok('frozen implementation '+rel,p.sha(RUN/'code'/rel)==digest)
 for path,inventory in data['completed_evidence'].items():ok('completed tree '+str(Path(path).relative_to(RUN)),p.tree_hash(Path(path))==inventory)
 outcomes=[]
 for row in data['cases']:
  case=row['case'];d=RUN/case;board=d/'candidate/fixture.kicad_pcb';source=Path(row['source']);pr=next(x for x in old['cases'] if x['case']==case);original=Path(pr['source']);tree=p.tree_hash(board.parent);obs=read(d/'areas.json');native=p.parse_report(d/'diagnostic-drc.json',board.name);binding=read(d/'diagnostic-drc-binding.json');inp=Path(binding['input'])
  a=sx.parse(original.read_text());b=sx.parse(source.read_text());restored=copy.deepcopy(b);removed=[]
  for z,n in zip(sx.children(a,'zone'),sx.children(restored,'zone')):
   place=sx.one(z,'placement')
   if place is not None and sx.one(n,'placement') is None:n.insert(z.index(place),copy.deepcopy(place));removed.append(sx.unquote(sx.one(z,'uuid')[1]))
  ok(case+': only prohibited disabled placement nodes removed',restored==a and len(removed)==(2 if case=='mixed' else 1) and set(removed)=={x['uuid'] for x in row['removed_placement_nodes']} and all(x['node']==['placement',['enabled','no'],['sheetname','"/Diagnostic/"']] for x in row['removed_placement_nodes']))
  expected=dict(pr['source_hashes']);expected[board.name]=p.sha(source)
  ok(case+': complete original project preserved except declared board',expected==tree==p.tree_hash(source.parent)==row['source_hashes'] and p.sha(board)==p.sha(source)==row['expected']['board_sha256'] and read(board.with_suffix('.kicad_pro'))['board']['design_settings']['rule_severities']['items_not_allowed']=='error')
  ok(case+': source scope unsupported',row['production_scope']['supported'] is False and row['constraint_qualification_passed'] is False and row['routing_accepted'] is False)
  try:p.preflight(source)
  except p.Rejected as exc:ok(case+': current production scope rejects',str(exc)=='unsupported: rule-area restrictions not qualified by pinned native validator')
  else:raise AssertionError('production scope admitted '+case)
  ok(case+': native exact flags/census',obs==row['area_observation'] and sorted(obs['zones'],key=lambda x:x['uuid'])==sorted(row['expected']['zones'],key=lambda x:x['uuid']) and obs['footprint_zone_count']==obs['footprint_rulearea_count']==0)
  ok(case+': same-load source/export bindings',obs['source']==str(board) and obs['board_sha256']==p.sha(board) and obs['project_sha256']==p.sha(board.with_suffix('.kicad_pro')) and obs['input_hashes_before']==obs['input_hashes_after']==tree and obs['dsn_sha256']==p.sha(d/'native.dsn') and obs['board_saved'] is False)
  ds=g._parse_dsn((d/'native.dsn').read_text());keep=[x for x in sx.one(ds,'structure') if isinstance(x,list) and x and x[0] in ('keepout','wire_keepout','via_keepout')];wanted=[]
  for z in obs['zones']:
   flags=z['disallow'];kind='keepout' if flags['tracks']==flags['vias'] else ('wire_keepout' if flags['tracks'] else 'via_keepout');pts=z['outlines_nm'][0]
   assert all(x%1000==0 and y%1000==0 for x,y in pts)
   for layer in z['layers']:wanted.append([kind,'""',['polygon',layer,'0',*[str(v) for x,y in pts+[pts[0]] for v in (x//1000,-y//1000)]]])
  ok(case+': exact typed keepout bijection',len(keep)==len(wanted) and sorted(map(repr,keep))==sorted(map(repr,wanted)))
  ok(case+': raw DRC omission remains no qualification',native==row['native'] and all(native[k]==0 for k in ('opens','blocking','warnings','exclusions')) and native['findings']==[] and native['ignored_checks']==pr['native']['ignored_checks'] and row['passed'] is True and row['omission_reproduced'] is True and row['native_rejected_known_invalid_constraint'] is False)
  ok(case+': DRC input/report binding',binding['source']==str(board) and binding['before']==tree and binding['saved'] is False and p.tree_hash(inp.parent)==binding['after'] and all(binding['after'].get(k)==v for k,v in tree.items()) and set(binding['after'])-set(tree)<={'fixture.kicad_prl'} and p.sha(inp)==p.sha(board) and row['native_binding']['native_report_sha256']==p.sha(d/'diagnostic-drc.json') and row['native_binding']['native_binding_sha256']==p.sha(d/'diagnostic-drc-binding.json'))
  for name,argv in {'area-export':[*f.SANDBOX,str(c.PYTHON),'-B',str(RUN/'code/native_areas.py'),str(board),str(d/'areas.json'),str(d/'native.dsn')],'diagnostic-drc':[*f.SANDBOX,str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(d/'diagnostic-drc.json'),str(inp)]}.items():f.process_check(d,data,name,argv);checks.append(case+': exact '+name+' process/step/argv')
  ok(case+': case receipt exact',read(d/'case.json')==row)
  outcomes.append({'case':case,'board_sha256':p.sha(board),'native_report_sha256':p.sha(d/'diagnostic-drc.json'),'removed_placement_nodes':len(removed),'keepout_kinds':[x[0] for x in keep],'native_findings':[],'genuine_constraints_qualified':False})
 ok('shared recorded finite resources',all(math.isfinite(data[k]) and 0<data[k]<=60 for k in ('wall_seconds','total_cpu_seconds')) and data['budget_seconds']==data['cpu_budget_seconds']==60)
 ok('CPU stages counted once',abs(sum(x['cpu_seconds'] for x in data['steps'])-data['native_step_cpu_seconds'])<1e-9 and data['total_cpu_seconds']>=data['native_step_cpu_seconds'])
 ok('all inspected run inputs unchanged',p.tree_hash(RUN)==before and p.tree_hash(OLD)==prior)
 result={'schema':1,'audit_passed':True,'reviewer':'independent AI read-only audit','native_executed':False,'check_count':len(checks),'checks':checks,'summary_sha256':p.sha(RUN/'summary.json'),'summary_outcomes':outcomes,'run_inventory':before,'wall_seconds_recorded':data['wall_seconds'],'cpu_seconds_recorded':data['total_cpu_seconds'],'accounting_point':data['accounting_point'],'qualification':False}
 with (HERE/'audit.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('checks','run_inventory')},indent=2))
if __name__=='__main__':main()
