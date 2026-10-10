"""Offline failed-fixture binding diagnosis. No native jobs or source modification."""
from pathlib import Path
import sys,json,hashlib,copy,math,traceback,importlib.util
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path[:0]=[str(ROOT),str(ROOT/'experiments/placement_diagnostic_v1')]
from autorouter import pipeline as p,sexpr as sx,board_floor as g,floor_route as f,config as c
import placement_transform as placement
HERE=Path(__file__).resolve().parent;RUN=ROOT/'.runs/placement-routing-fixture-001';read=lambda x:json.loads(x.read_text());checks=[]
# Keep the failed source-net behavior reproducible after its narrow repair.
spec=importlib.util.spec_from_file_location('failed_run_floor',RUN/'code/source/autorouter/board_floor.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
def ok(label,test):
 if not test:raise AssertionError(label)
 checks.append(label)
def byte_tree(path):return {k:(path/k).read_bytes() for k in p.tree_hash(path)}
def main():
 data=read(RUN/'result.json');source=Path(data['source']);before=p.tree_hash(RUN);source_before=p.tree_hash(source.parent);original=sx.read(source);task=g.task_from_source(original);board=RUN/'floor-export-input'/source.name;native=read(RUN/'floor-export-context.json');area=read(RUN/'area-context.json');raw=(RUN/'native.dsn').read_bytes();expected=dict(source_before);expected[source.name]=g.sha((sx.dump(task)+'\n').encode())
 ok('explicit pre-engine rejection, no qualification',data['status']=='rejected' and data['error']=='ValueError: unqualified named task net reference' and all(data[k] is False for k in ('routing_accepted','production_qualified','comparison_eligible')) and [x['name'] for x in data['steps']]==['source-drc','floor-area-export'])
 ok('complete original/snapshot inputs exact',source_before==data['source_hashes']==p.tree_hash(RUN/'snapshot'))
 ok('exact normal stripped task; original rules unchanged',board.read_bytes()==(sx.dump(task)+'\n').encode() and p.tree_hash(board.parent)==expected==p.tree_hash(RUN/'candidate'))
 for name,digest in data['freeze']['files_sha256'].items():ok('frozen source '+name,p.sha(RUN/'code/source'/name)==digest)
 ok('reviewed executed observer bytes',p.sha(RUN/'code/native_combined.py')==data['observer_sha256']=='3fb123a8a1fdbe119a7de60e97677940e26a15b5562a822599d854ba04553a70')
 ok('floor same-load board/project/raw input binding',native['board_sha256']==p.sha(board) and native['project_sha256']==p.sha(board.with_suffix('.kicad_pro')) and native['dsn_sha256']==g.sha(raw) and native['input_hashes_before']==native['input_hashes_after']==expected and native['routes']==[] and native['board_saved'] is False)
 f.context_binding(native,board,expected,'export',g.sha(raw));checks.append('production floor context_binding passes')
 _,_,area_binding=placement.native_binding(byte_tree(source.parent),byte_tree(board.parent),source.name,area,raw);checks.append('production placement native_binding passes')
 ok('same observation identities and explicit caps',all(native[k]==area[k] for k in ('native_version','source','board_sha256','project_sha256','dsn_sha256','input_hashes_before','input_hashes_after','board_saved')) and area['limits']['footprints']==512 and area['footprint_zone_count']==area['footprint_rulearea_count']==0)
 original_native=p.parse_report(RUN/'source-drc.json',source.name);binding=read(RUN/'source-drc-binding.json');input_board=Path(binding['input']);after=binding['after']
 ok('source raw native clean report binds original project',original_native==data['source_drc'] and original_native['findings']==[] and binding['source']==str(RUN/'snapshot'/source.name) and binding['before']==source_before and binding['saved'] is False and p.tree_hash(input_board.parent)==after and all(after.get(k)==v for k,v in source_before.items()) and set(after)-set(source_before)<={source.with_suffix('.kicad_prl').name})
 f.process_check(RUN,data,'source-drc',[*f.SANDBOX,str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(RUN/'source-drc.json'),str(input_board)]);checks.append('exact source DRC process/step')
 f.process_check(RUN,data,'floor-area-export',[*f.SANDBOX,str(c.PYTHON),'-B',str(RUN/'code/native_combined.py'),str(board),str(RUN/'floor-export-context.json'),str(RUN/'area-context.json'),str(RUN/'native.dsn')]);checks.append('exact combined observer process/step')
 # Reproduce the original production failure with unchanged retained inputs.
 try:g.transform(raw,native,source.with_suffix('.kicad_pro').read_bytes(),board.read_bytes())
 except ValueError as exc:
  ok('exact production failure independently reproduced',str(exc)=='unqualified named task net reference');failure={'error':str(exc),'traceback':traceback.format_exc()}
 else:raise AssertionError('prior production failure no longer reproduces; inspect current source change')
 declarations=sx.children(task,'net');refs=[]
 def walk(node,path):
  for i,value in enumerate(node):
   if not isinstance(value,list):continue
   if value and value[0]=='net':refs.append({'parent':node[0],'path':path+[i],'node':value})
   walk(value,path+[i])
 walk(task,[])
 ok('sole nonnamed reference is numeric-zero rule-area net',declarations==[] and [x['node'] for x in refs if x['parent']!='pad']==[['net','0']] and all(x['node'][1].startswith('"') and x['node'][1].endswith('"') for x in refs if x['parent']=='pad'))
 # Independent downstream structural analysis only: build context from separately
 # checked original JSON dimensions/native rows. Do NOT patch production identity
 # resolver, edit task/observations, or claim its qualification passed.
 project=read(source.with_suffix('.kicad_pro'));raw_dims={k:g.millimetres(project['net_settings']['classes'][0][v]) for k,v in g.DIMENSIONS.items()};floors={k:g.millimetres(project['board']['design_settings']['rules'][k],zero=True) for k in g.FLOORS}
 ok('native exact original preferences and board floors',native['floors_nm']==floors and all(x['class']=='Default' and all(x[k]==v for k,v in raw_dims.items()) for x in native['nets']))
 pads={};names=set()
 for fp in sx.children(task,'footprint'):
  ref=next(sx.unquote(n[2]) for n in sx.children(fp,'property') if sx.unquote(n[1])=='Reference')
  for pad in sx.children(fp,'pad'):
   net=sx.unquote(sx.one(pad,'net')[1]);names.add(net);layers=[sx.unquote(x) for x in sx.one(pad,'layers')[1:]];pads[sx.unquote(sx.one(pad,'uuid')[1])]={'reference':ref,'number':sx.unquote(pad[1]),'net':net,'copper_layers':[x for x in ('F.Cu','B.Cu') if x in layers]}
 ok('exact source pad identity and full named net inventory',len(pads)==4 and {x['uuid']:{k:x[k] for k in ('reference','number','net','copper_layers')} for x in native['pads']}==pads and {x['name'] for x in native['nets']}==names=={'SIGNAL_A','SIGNAL_B'})
 mapping={x['name']:x for x in native['nets']};ok('native consistent netcodes and actual two pads per net',all(x['netcode']==mapping[x['net']]['netcode'] for x in native['pads']) and all(x['copper_pad_count']==sum(y['net']==x['name'] for y in native['pads'])==2 for x in native['nets']))
 context={'policy':g.POLICY,'raw_nm':raw_dims,'floors_nm':floors,'derived_nm':g.derive(raw_dims,floors),'nets':native['nets'],'pads':native['pads'],'engine_requirements':dict(g.ENGINE_REQUIREMENTS)}
 ds=g._parse_dsn(raw.decode());rawaudit=g.audit_export(ds,context);guidedtree=g.expected_edit(ds,context);edit=g.verify_edit(ds,guidedtree,context);guided=g._dump_dsn(guidedtree).encode();placed,removal=placement.transform(byte_tree(source.parent),byte_tree(board.parent),source.name,area,raw,guided);adapted=g.adapter_bytes(placed,native['obstacles'])
 ok('downstream raw/guided/placement structure analysis',rawaudit['terminal_count']==4 and rawaudit['declared_copper_terminal_nets']==2 and edit['exact_allowed_change'] is True and removal['removed_count']==2 and not removal['routing_accepted'])
 ok('recorded bounded CPU and arithmetic',0<data['wall_seconds']<=60 and 0<data['total_cpu_seconds']<=60 and abs(data['parent_cpu_seconds']+data['waited_child_cpu_seconds']-data['total_cpu_seconds'])<1e-9 and data['waited_child_cpu_seconds']>=sum(s['cpu_seconds'] for s in data['steps']))
 ok('entire failed run and original inputs unchanged',before==p.tree_hash(RUN) and source_before==p.tree_hash(source.parent))
 result={'schema':1,'audit_passed':True,'native_or_engine_executed':False,'routing_accepted':False,'production_qualified':False,'check_count':len(checks),'checks':checks,'source_sha256':p.sha(source),'summary_sha256':p.sha(RUN/'result.json'),'run_inventory':before,'failure':failure,'all_task_net_references':refs,'downstream_structural_analysis_only':{'raw_audit':rawaudit,'exact_edit_audit':edit,'removed':removal['removed_count'],'derived_dimensions_nm':context['derived_nm'],'raw_sha256':g.sha(raw),'guided_sha256':g.sha(guided),'placed_sha256':g.sha(placed),'adapted_sha256':g.sha(adapted),'qualification':False,'limitation':'No production source-net resolver bypass or original/native bytes edited. Independent diagnostic context tests later pure grammar stages only. Actual route/final validation not reached.'},'accounting_point':data['accounting_point'],'wall_seconds_recorded':data['wall_seconds'],'cpu_seconds_recorded':data['total_cpu_seconds']}
 with (HERE/'audit.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('run_inventory','checks','failure')},indent=2))
if __name__=='__main__':main()
