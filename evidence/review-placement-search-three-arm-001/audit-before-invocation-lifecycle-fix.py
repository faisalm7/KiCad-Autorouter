"""Read-only completed diagnostic pair audit. Execute only after lead completion signal.

Reads retained files and current pinned tools; launches no native/engine job.
No board copies or mutations. Writes only this audit's own result once.
"""
from pathlib import Path
import sys,json,math,datetime,subprocess,hashlib
from collections import Counter
from decimal import Decimal
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path[:0]=[str(ROOT),str(ROOT/'experiments/placement_diagnostic_v2')]
from autorouter import pipeline as p,sexpr as sx,board_floor as g,floor_route as f
import diagnostic_route as d,experiment_search as pair
HERE=Path(__file__).resolve().parent;RUN=ROOT/'.runs/placement-search-three-arm-001';read=lambda x:json.loads(x.read_text());checks=[]
def ok(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
def norm_dsn(path):
 t=g._parse_dsn(path.read_text());t[1]='"display-name-only"';return t
def same_float(a,b):return abs(a-b)<1e-7

def verify_frozen(frozen):
 current=p.tool_manifest()
 ok('same current implementation and tool bytes excluding allowed later HEAD', {k:v for k,v in current.items() if k!='git_head'}=={k:v for k,v in frozen['tools'].items() if k!='git_head'})
 for relative,digest in frozen['files_sha256'].items():
  ok('runtime bytes same as frozen '+relative,p.sha(ROOT/relative)==digest)
  blob=subprocess.run(['git','show',frozen['tools']['git_head']+':'+relative],cwd=ROOT,check=True,capture_output=True,timeout=5).stdout
  ok('exact committed frozen blob '+relative,hashlib.sha256(blob).hexdigest()==digest)

def nm(value,m=1000000):
 value=Decimal(value)*m;assert value==value.to_integral_value();return int(value)
def ses_equal(directory,board):
 routes=sx.one(sx.read(directory/'routes.ses'),'routes');ok(str(directory.name)+': SES resolution qualified',sx.one(routes,'resolution')==['resolution','um','10'])
 _,resolve=g.source_net_identity(board)
 def canon(net,layer,width,a,b):return(net,layer,width,*sorted((tuple(a),tuple(b))))
 expected=[];actual=[]
 for net in sx.one(routes,'network_out')[1:]:
  for wire in sx.children(net,'wire'):
   path=sx.one(wire,'path');points=[[nm(path[i],100),-nm(path[i+1],100)] for i in range(3,len(path),2)]
   for a,b in zip(points,points[1:]):expected.append(canon(sx.unquote(net[1]),sx.unquote(path[1]),nm(path[2],100),a,b))
 for item in p.routes(board):
  if item[0]=='segment':actual.append(canon(resolve(sx.one(item,'net')),sx.unquote(sx.one(item,'layer')[1]),nm(sx.one(item,'width')[1]),[nm(v) for v in sx.one(item,'start')[1:]],[nm(v) for v in sx.one(item,'end')[1:]]))
 ok(str(directory.name)+': all final track segments exactly transported from SES',Counter(expected)==Counter(actual))
 return len(actual)
def ast_diff(first,last,path=()):
 if isinstance(first,list) and isinstance(last,list):
  if len(first)!=len(last):return[(path,'length',len(first),len(last))]
  return sum((ast_diff(a,b,path+(i,))for i,(a,b)in enumerate(zip(first,last))),[])
 return [] if first==last else[(path,first,last)]

def main():
 summary=read(RUN/'summary.json');before=p.tree_hash(RUN);protocol=read(RUN/'protocol.json');source=Path(protocol['source']);source_before=p.tree_hash(source.parent);frozen=protocol['frozen'];rows=summary['results'];arm_results=[]
 ok('completed denominator remains three explicit policies',summary['status']=='completed' and summary['kind']=='diagnostic_placement_search_three_arm' and summary['production_qualified'] is False and [x['policy'] for x in rows]==list(d.POLICIES))
 ok('immutable protocol exact',summary['protocol_sha256']==p.sha(RUN/'protocol.json') and protocol['protocol']==read(ROOT/'experiments/placement_diagnostic_v2/protocol.json') and protocol['fixed_order'] is True)
 ok('original full source corpus identity',p.tree_hash(RUN/'source-project')==protocol['source_hashes']==source_before and pair.selected_source()[0]==source)
 verify_frozen(frozen)
 for relative,digest in frozen['files_sha256'].items():ok('copied pair implementation '+relative,p.sha(RUN/'code'/relative)==digest)
 for path,inventory in summary['completed_trees'].items():ok('retained completed tree '+str(Path(path).relative_to(ROOT)),p.tree_hash(Path(path))==inventory)
 fixture=Path(protocol['fixture_receipt']);fixture_before=p.tree_hash(fixture.parent);ok('same-code fixture prerequisite current',p.sha(fixture)==protocol['fixture_sha256'] and pair.fixture_gate(fixture,frozen)==fixture_before)
 fx=read(fixture);fxdir=fixture.parent;fxsource=Path(fx['source']);fxcandidate=Path(fx['candidate']);fxnative=p.parse_report(fxdir/'final-drc.json',fxcandidate.name)
 ok('fresh strongest fixture has same frozen HEAD/code/tools and zero findings',fx['freeze']==frozen and fxnative==fx['native'] and not fxnative['findings'] and fx['policy']==d.POLICIES[2] and fx['routing_accepted'] is True)
 ok('fixture source and candidate immutable complete project',p.tree_hash(fxsource.parent)==fx['source_hashes']==p.tree_hash(fxdir/'snapshot') and p.tree_hash(fxcandidate.parent)=={**fx['source_hashes'],fxsource.name:fx['candidate_sha256']} and p.immutable(sx.read(fxsource))==p.immutable(sx.read(fxcandidate)))
 fixture_segments=ses_equal(fxdir,sx.read(fxcandidate))
 fixture_audit={'receipt_sha256':p.sha(fixture),'candidate_sha256':p.sha(fxcandidate),'final_drc_sha256':p.sha(fxdir/'final-drc.json'),'routing_accepted':True,'native':{k:fxnative[k] for k in ('opens','blocking','warnings','exclusions')},'segments_transported':fixture_segments,'metrics':fx['metrics'],'receipt_wall_seconds':fx['wall_seconds'],'receipt_cpu_seconds':fx['total_cpu_seconds'],'frozen_head':frozen['tools']['git_head']}
 original=sx.read(source);areas=d.narrow_source(original);ruleareas=[x for x in areas if x['is_rule_area']];ok('four original unrestricted placement areas and six zones',len(areas)==6 and len(ruleareas)==4 and all(x['placement_enabled'] and x['placement_source_type']=='SHEETNAME' and not any(x['disallow'].values()) for x in ruleareas))
 assigned=protocol['identical_assigned_seconds'];expected_assigned=math.floor((120-max(protocol['shared_wall_at_assignment'],protocol['shared_cpu_at_assignment'])-5)*1000)/1000
 ok('identical declared allocation after charged setup reserve',50<=assigned<=120 and assigned==expected_assigned)
 for i,row in enumerate(rows):
  directory=RUN/('arm-'+str(i));data=read(directory/'result.json');candidate=Path(data['candidate']);native=p.parse_report(directory/'final-drc.json',candidate.name);raw_summary=read(RUN/('arm-'+str(i)+'-invocation.json'));tree=p.tree_hash(directory)
  prefix='arm'+str(i)+': '
  ok(prefix+'bound receipt and invocation index',row['receipt_sha256']==p.sha(directory/'result.json') and all(row.get(k)==v for k,v in raw_summary.items()))
  ok(prefix+'same source code tools and allowance',data['source']==str(source) and data['source_hashes']==source_before and data['freeze']==frozen and data['tools']==frozen['tools'] and data['budget_seconds']==data['cpu_budget_seconds']==assigned and data['policy']==d.POLICIES[i])
  ok(prefix+'original snapshot/rules and candidate immutable geometry',p.tree_hash(directory/'snapshot')==source_before and p.tree_hash(candidate.parent)=={**source_before,source.name:data['candidate_sha256']} and p.immutable(sx.read(candidate))==p.immutable(original))
  task,contract,chain=d.derive(directory,source_before,data['policy']);ok(prefix+'exact chain and declared removal count',chain==data['chain']==row['chain'] and chain['placement_removed_count']==8)
  export=read(directory/'floor-export-context.json');area=read(directory/'area-context.json');final_context=read(directory/'floor-final-context.json')
  ok(prefix+'same-load floor/area hashes and zero task routes',all(export[k]==area[k] for k in ('source','board_sha256','project_sha256','dsn_sha256','input_hashes_before','input_hashes_after','board_saved')) and export['routes']==[] and area['footprint_zone_count']==area['footprint_rulearea_count']==0)
  ok(prefix+'original class preferences/floors remain',export['nets']==final_context['nets'] and export['floors_nm']==final_context['floors_nm'] and export['pads']==final_context['pads'])
  f.audit_transport(directory,data,task,candidate);checks.append(prefix+'SES/import/saved native refill/source DRC exactly rederived')
  ok(prefix+'final report and candidate hashes exact',native==data['native'] and p.sha(directory/'final-drc.json')==data['native_report_sha256'] and p.sha(candidate)==data['candidate_sha256'] and p.sha(directory/'final-drc-input'/candidate.name)==p.sha(candidate))
  verdict=d.check_result(directory/'result.json');ok(prefix+'full diagnostic readback agrees even for rejected native',verdict['diagnostic_verified'] is True and verdict['routing_accepted']==row['verified_native_accepted']==data['routing_accepted'] and row['diagnostic_verified'] is True)
  ok(prefix+'critical raw counters equal index',all(native[k]==row[k] for k in ('opens','blocking','warnings','exclusions')) and p.native_accepted(native)==data['routing_accepted'])
  ok(prefix+'eight process outcomes success and exact checker-bound argv',len(data['steps'])==8 and [x['name'] for x in data['steps']]==['source-drc','floor-area-export','engine','import','refill-drc','floor-final','final-drc','metrics'] and all(x['exit_code'] in (0,5) and x['cleanup_complete'] for x in data['steps']))
  ok(prefix+'strict common profile settings',data['engine_profile']=='completion-only' and data['adapter']=='both' and {'--router.optimizer.enabled=false','--router.automatic_neckdown=false','--router.fanout.enabled=false','--router.neck_width_um=0'}<=set(data['engine_budget']['argv']))
  ok(prefix+'invocation includes receipt time and total CPU',row['invocation_wall_seconds']>=data['wall_seconds'] and row['invocation_cpu_seconds']>=data['total_cpu_seconds'] and all(math.isfinite(row[k]) and row[k]>=0 for k in ('invocation_wall_seconds','invocation_cpu_seconds')))
  ok(prefix+'full measured shared overhead charged',same_float(row['charged_wall_seconds'],row['invocation_wall_seconds']+summary['shared_wall_seconds']) and same_float(row['charged_cpu_seconds'],row['invocation_cpu_seconds']+summary['shared_cpu_seconds']) and row['within_charged_caps']==(row['charged_wall_seconds']<=120 and row['charged_cpu_seconds']<=120))
  ok(prefix+'accepted only with native and charged caps',row['accepted']==(row['verified_native_accepted'] and row['within_charged_caps']))
  segments=ses_equal(directory,sx.read(candidate)); metrics=read(directory/'metrics.json');ok(prefix+'raw quality metrics exact',metrics==data['metrics'] and metrics['track_length_mm']==row['length_mm'] and metrics['vias']==row['vias'])
  binding=read(directory/'final-drc-binding.json');ok(prefix+'native original project input tree retained',p.tree_hash(Path(binding['input']).parent)==binding['after'] and binding['before']==p.tree_hash(candidate.parent))
  arm_results.append({'arm':i,'policy':data['policy'],'status':data['status'],'routing_accepted':data['routing_accepted'],'candidate_sha256':data['candidate_sha256'],'report_sha256':data['native_report_sha256'],'native':{k:native[k] for k in ('opens','blocking','warnings','exclusions')},'finding_types':dict(Counter(x['type'] for x in native['findings'])),'segments_transported':segments,'blocking_findings':[x for x in native['findings'] if x['severity']=='error' and x['type']!='unconnected_items'],'metrics':metrics,'assigned_seconds':assigned,'internal_job_seconds':data['engine_budget']['assigned_job_timeout_seconds'],'receipt_wall_seconds':data['wall_seconds'],'receipt_cpu_seconds':data['total_cpu_seconds'],'invocation_wall_seconds':row['invocation_wall_seconds'],'invocation_cpu_seconds':row['invocation_cpu_seconds'],'charged_wall_seconds':row['charged_wall_seconds'],'charged_cpu_seconds':row['charged_cpu_seconds'],'source_zone_count':len(sx.children(original,'zone')),'candidate_zone_count':len(sx.children(sx.read(candidate),'zone')),'recorded_started_utc':data['started_utc']})
  ok(prefix+'readback does not alter retained tree',p.tree_hash(directory)==tree)
 raw=[norm_dsn(RUN/('arm-'+str(i))/'native.dsn') for i in range(3)];guided=[norm_dsn(RUN/('arm-'+str(i))/'floor-guided.dsn') for i in range(3)];pre=[norm_dsn(RUN/('arm-'+str(i))/'pre-adapter.dsn') for i in range(3)]
 ok('fresh raw exports semantically equal except displayed path',raw[0]==raw[1] and summary['raw_tasks_equivalent'] is True)
 ok('common floor-guided problem equal',guided[0]==guided[1]==guided[2])
 expected=g._parse_dsn((RUN/'arm-0/floor-guided.dsn').read_text());structure=sx.one(expected,'structure');removed=[x for x in structure if isinstance(x,list) and x and x[0]=='keepout'];structure[:]=[x for x in structure if not (isinstance(x,list) and x and x[0]=='keepout')];expected[1]='"display-name-only"'
 ok('sole pre-adapter AST difference eight attributed keepouts',len(removed)==8 and expected==pre[0])
 placed=[norm_dsn(RUN/('arm-'+str(i))/'placement-guided.dsn') for i in range(3)]
 ok('all placement-guided DSN problems identical',placed[0]==placed[1]==placed[2]==pre[0])
 diffs=ast_diff(pre[0],pre[1]);ok('only three clearance atoms gain20um',len(diffs)==3 and all(a=='300' and b=='320' for _,a,b in diffs) and pre[1]==pre[2])
 tasks=[norm_dsn(RUN/('arm-'+str(i))/'task.dsn') for i in range(3)];diffs_task=ast_diff(tasks[0],tasks[1])
 ok('both adapter preserves only same three clearance changes into engine input',len(diffs_task)==3 and all(a=='300' and b=='320' for _,a,b in diffs_task) and tasks[1]==tasks[2])
 for i,policy in enumerate(d.POLICIES):
  data=read(RUN/('arm-'+str(i))/'result.json');settings=data['engine_budget'];via,plane=(25,3) if i==2 else(50,5)
  ok('arm'+str(i)+': exact declared costs and planning margin',data['search_parameters']=={'clearance_margin_nm':0 if i==0 else 20000,'scoring_variant':'via_low' if i==2 else 'via_default','via_costs':via,'plane_via_costs':plane} and '--router.scoring.via_costs='+str(via) in settings['argv'] and '--router.scoring.plane_via_costs='+str(plane) in settings['argv'])
 ok('batch shared arithmetic reconciles',same_float(summary['batch_wall_seconds'],sum(x['invocation_wall_seconds'] for x in rows)+summary['shared_wall_seconds']) and same_float(summary['batch_cpu_seconds'],sum(x['invocation_cpu_seconds'] for x in rows)+summary['shared_cpu_seconds']) and summary['shared_wall_seconds']>=0 and summary['shared_cpu_seconds']>=0)
 ok('comparison eligibility and interpretation consistent',summary['comparison_eligible']==all(x['diagnostic_verified'] and x['within_charged_caps'] for x in rows) and summary['comparison']==(pair.compare(rows) if summary['comparison_eligible'] else None))
 ok('quality deltas only if both native accepted',all((c['reference_accepted'] and c['variant_accepted']) or ('length_delta_mm' not in c and 'via_delta' not in c) for c in summary['comparison'].values()))
 starts=[datetime.datetime.fromisoformat(x['recorded_started_utc']) for x in arm_results];ok('recorded sequential order consistent',all(starts[i+1]>starts[i] and (starts[i+1]-starts[i]).total_seconds()+0.05>=arm_results[i]['receipt_wall_seconds'] for i in range(2)))
 ok('entire pair prerequisite and original source unchanged by audit',p.tree_hash(RUN)==before and p.tree_hash(fixture.parent)==fixture_before and p.tree_hash(source.parent)==source_before)
 result={'schema':1,'audit_passed':True,'review_kind':'independent AI read-only evidence audit','native_or_engine_executed':False,'check_count':len(checks),'checks':checks,'summary_sha256':p.sha(RUN/'summary.json'),'protocol_sha256':p.sha(RUN/'protocol.json'),'run_inventory':before,'arms':arm_results,'comparison':summary['comparison'],'shared_wall_seconds':summary['shared_wall_seconds'],'shared_cpu_seconds':summary['shared_cpu_seconds'],'accounting_point':summary['accounting_point'],'accounting_limit':'Stored measurements precede final publication/freshness. Source includes a postpublication cap guard; this offline audit verifies stored arithmetic and outcomes, not an independent postpublication elapsed measurement.','fixture':fixture_audit,'scope':'One exposed development-board diagnostic planning/search ablation; no production/C/B2/generalized/electrical claim.'}
 with (HERE/'audit.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('checks','run_inventory')},indent=2))
if __name__=='__main__':main()
