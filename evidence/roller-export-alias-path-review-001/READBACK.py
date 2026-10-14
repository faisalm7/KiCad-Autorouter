"""Read-only actual002 audit and pure comparison/protected-order controls.
Never invokes native, JVM, subprocess, Git or a solver; no raw board output.
"""
import copy, hashlib, json, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT),str(ROOT/'experiments/roller_export_alias_v1')]
from autorouter import sexpr as sx,pipeline as p,floor_route as f,placement_clearance as io
from autorouter.adapter import _parse_dsn,_dump_dsn
from experiments.roller_export_alias_v1 import padless_alias as a
from experiments.roller_export_alias_v1.retained_ses import build,restore_protected_order
from experiments.pic_mixed_transport_probe_v1 import ses_checks as sc
from collections import Counter
from experiments.roller_export_alias_v1.worker import without_authorized_reference_display
OUT=Path(__file__).resolve().parent
OLD=ROOT/'.runs/roller-export-alias-native-002'
SRC=ROOT/'.data/corpus-expansion-audit-001/sparkfun__SparkFun_Roller_Encoder_Breakout'
NAME='SparkFun_Roller_Encoder_Breakout.kicad_pcb'
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def inventory(x):return io.inventory(x,max_bytes=96*1024**2,max_files=4000,max_entries=8000,with_directories=True)
def read(x):return json.loads(x.read_text())
def invjson(v):return {'files':v[0],'directories':list(v[1])}
def reject(fn):
 try:fn()
 except (Exception,KeyboardInterrupt) as exc:return {'rejected':True,'type':type(exc).__name__,'reason':str(exc)}
 raise AssertionError('invalid control accepted')
start=time.monotonic();old_before=inventory(OLD)
modules=['experiments/roller_export_alias_v1/'+n for n in ('padless_alias.py','worker.py','retained_ses.py','driver.py')]
code_before={n:sha(ROOT/n) for n in modules}
record=read(OLD/'result.json')
assert record['status']=='failed' and record['controls_passed'] is False and record['production_support'] is False
assert record['reason']=='Rejected: dual native alias namespaces differ outside authorized placement identity'
assert len(record['steps'])==2
runtime=record['runtime_source_sha256'];runtime_current={n:sha(ROOT/n) for n in runtime}
changed={n:{'retained':runtime[n],'current':runtime_current[n]} for n in runtime if runtime[n]!=runtime_current[n]}
assert set(changed)=={'experiments/roller_export_alias_v1/padless_alias.py'},changed
pins=record['pins'];assert io.inventory(SRC,max_bytes=32*1024**2,max_files=4000,max_entries=8000)==pins['source_inventory']
assert all(sha(ROOT/n)==h for n,h in pins['files_sha256'].items())
cases={};normal=[];alias_only=[]
for ns in ('A','B'):
 case=OLD/ns;board=case/'input'/NAME;raw=board.read_bytes();dsn=case/'native.dsn';ctx=read(case/'context.json');diag=read(case/'diagnostic.json');ev=read(case/'alias-evidence.json');binding=a.plan(raw,ns)
 assert ev['namespace']==ns and ev['schema']==1
 hashes=io.inventory(board.parent,max_bytes=32*1024**2,max_files=4000,max_entries=8000)
 assert hashes==ctx['input_hashes_before']==ctx['input_hashes_after']==diag['input_hashes_before']==diag['input_hashes_after']
 f.context_binding(ctx,board,hashes,'final',None)
 assert diag['floor_context_sha256']==sha(case/'context.json')
 assert diag['source']==str(board) and diag['board_sha256']==sha(board) and diag['project_sha256']==sha(board.with_suffix('.kicad_pro'))
 assert diag['same_loaded_board'] is True and diag['observation_before_export']==diag['observation_after_export'] and diag['dsn_sha256'] is None
 for k,name in [('source_sha256','input/'+NAME),('context_sha256','context.json'),('diagnostic_sha256','diagnostic.json'),('dsn_sha256','native.dsn'),('before_board_sha256','before.kicad_pcb'),('after_board_sha256','after.kicad_pcb')]:assert ev[k]==sha(case/name),(ns,k)
 assert sx.read(case/'before.kicad_pcb')==sx.read(case/'after.kicad_pcb')
 events=ev['events'];assert [x['phase'] for x in events]==['during_alias','restored']
 during,restored=events[0]['observation'],events[1]['observation']
 assert digest(restored)==diag['observation_before_export']['native_observation_sha256']
 assert without_authorized_reference_display(during,binding,True)==without_authorized_reference_display(restored,binding)
 assert events[1]['result']=={'exported':True,'restored':True,'alias_count':6,'routing_accepted':False}
 assert len(restored['footprints'])==23 and len(restored['pads'])==15 and len(restored['routes'])==11 and len(restored['zones'])==1
 originals=sx.read(board);routes=p.routes(originals);ident=[sx.one(x,'uuid')[1] for x in routes]
 assert len(routes)==len(set(ident))==11 and all(x[0]=='segment' for x in routes)
 assert p.sha(board)==pins['source_inventory']['Hardware/'+NAME]
 argv=[str(f.SANDBOX[0]),str(f.SANDBOX[1]),str(f.SANDBOX[2]),str(p.c.PYTHON),str(ROOT/'experiments/roller_export_alias_v1/worker.py'),str(board),str(case/'context.json'),str(dsn),str(case/'diagnostic.json'),ns,str(case/'before.kicad_pcb'),str(case/'after.kicad_pcb')]
 process=f.process_check(OLD,record,'export-'+ns,argv)
 assert process['log_truncated'] is False and process['log_bytes']==(OLD/('export-'+ns+'.log')).stat().st_size==0
 actualpath=str(dsn);tree=_parse_dsn(dsn.read_text());assert sx.unquote(tree[1])==actualpath
 alias_only.append(a.normalize_dsn(dsn.read_bytes(),raw,binding))
 normalized=a.normalize_dsn(dsn.read_bytes(),raw,binding,export_path=actualpath);normal.append(normalized)
 transport=reject(lambda:build(dsn.read_bytes(),raw,binding))
 assert transport['reason']=='native DSN does not preserve exact original route population'
 want,_=sc.source_routes(originals);actual=Counter()
 for wire in sx.children(sx.one(tree,'wiring'),'wire'):
  routepath=sx.one(wire,'path');net=sx.unquote(sx.one(wire,'net')[1]);layer={'F.Cu':'top_layer','B.Cu':'bottom_layer'}[sx.unquote(routepath[1])]
  actual.update(sc.segments(net,layer,sc.number(routepath[2]),sc.pairs(routepath[3:])))
 assert sum(want.values())==sum(actual.values())==11 and sum((want-actual).values())==sum((actual-want).values())==9
 def topology(counter):
  return Counter((net,layer,width,*sorted(((x.quantize(sc.Decimal(1)),y) for x,y in (pa,pb)))) for (net,layer,width,pa,pb),n in counter.items() for _ in range(n))
 assert topology(want)==actual
 transport.update(source_segments=11,dsn_segments=11,exactly_matching_segments=2,changed_segments=9,source_counter_sha256=digest(sorted((str(k),v) for k,v in want.items())),dsn_counter_sha256=digest(sorted((str(k),v) for k,v in actual.items())),observed_difference='X half-micrometre endpoints round to integral micrometres; net/layer/width/Y and expanded segment count preserved',maximum_observed_coordinate_delta_um=0.5,native_import_not_executed=True)
 classproof=a.unused_class_proof(raw,board.with_suffix('.kicad_pro').read_bytes(),ctx,dsn.read_bytes())
 cases[ns]={'board_sha256':sha(board),'project_sha256':sha(board.with_suffix('.kicad_pro')),'dsn_sha256':sha(dsn),'root_design_matches_worker_output':True,'context_sha256':sha(case/'context.json'),'diagnostic_sha256':sha(case/'diagnostic.json'),'full_sidecar_sha256':sha(case/'alias-evidence.json'),'full_sidecar_bytes':(case/'alias-evidence.json').stat().st_size,'restored_full_observation_sha256':digest(restored),'active_equals_restored_except_six_authorized_reference_displays':True,'before_after_native_emission_ast_equal':True,'before_board_sha256':sha(case/'before.kicad_pcb'),'after_board_sha256':sha(case/'after.kicad_pcb'),'full_population':{'footprints':23,'pads':15,'routes':11,'zones':1,'aliases':6},'process':process,'class_proof':classproof,'retained_route_transport':transport}
assert alias_only[0]!=alias_only[1] and normal[0]==normal[1]
ta,tb=[_parse_dsn(x.decode()) for x in alias_only]
diffs=[]
def diff(x,y,path=()):
 if type(x)!=type(y):diffs.append(path);return
 if isinstance(x,list):
  if len(x)!=len(y):diffs.append(path);return
  for i,(xx,yy) in enumerate(zip(x,y)):diff(xx,yy,path+(i,))
 elif x!=y:diffs.append(path)
diff(ta,tb);assert diffs==[(1,)]
raw=(OLD/'A/input'/NAME).read_bytes();binding=a.plan(raw,'A');data=(OLD/'A/native.dsn').read_bytes();path=str(OLD/'A/native.dsn');controls={}
for label,bad in [('wrong_absolute','/wrong/native.dsn'),('relative','native.dsn'),('traversal','/owned/../A/native.dsn'),('wrong_basename','/owned/A/other.dsn'),('non_string',Path(path))]:
 controls[label]=reject(lambda bad=bad:a.normalize_dsn(data,raw,binding,export_path=bad))
root=_parse_dsn(data.decode());root[1]='"/wrong/native.dsn"';controls['raw_root_changed']=reject(lambda:a.normalize_dsn(_dump_dsn(root).encode(),raw,binding,export_path=path))
root=_parse_dsn(data.decode());root.append(['unknown',json.dumps(path)]);controls['path_used_outside_root']=reject(lambda:a.normalize_dsn(_dump_dsn(root).encode(),raw,binding,export_path=path))
root=_parse_dsn(data.decode());root.append(['unknown',binding['aliases'][0]['alias']]);controls['alias_used_outside_placement']=reject(lambda:a.normalize_dsn(_dump_dsn(root).encode(),raw,binding,export_path=path))
for label,modify in [('wire_width',lambda t:sx.one(sx.children(sx.one(t,'wiring'),'wire')[0],'path').__setitem__(2,'999')),('terminal_mapping',lambda t:sx.one(sx.children(sx.one(t,'network'),'net')[0],'pins').__setitem__(1,'UNRELATED-999'))]:
 root=_parse_dsn(data.decode());modify(root);out=a.normalize_dsn(_dump_dsn(root).encode(),raw,binding,export_path=path);assert out!=normal[0];controls[label]={'normalized_still_differs':True}
original=sx.parse(raw.decode());reordered=copy.deepcopy(original);routes=iter(reversed(copy.deepcopy(p.routes(original))))
for i,x in enumerate(reordered):
 if isinstance(x,list) and x and x[0] in p.ROUTES:reordered[i]=next(routes)
assert p.routes(reordered)!=p.routes(original) and restore_protected_order(original,reordered)==original
controls['protected_order_only']={'exact_original_ast_restored':True}
for label,modify in [('protected_width',lambda t:sx.one(p.routes(t)[0],'width').__setitem__(1,'0.999')),('protected_loss',lambda t:t.remove(p.routes(t)[0])),('duplicate_uuid',lambda t:sx.one(p.routes(t)[1],'uuid').__setitem__(1,sx.one(p.routes(t)[0],'uuid')[1]))]:
 bad=copy.deepcopy(reordered);modify(bad);controls[label]=reject(lambda bad=bad:restore_protected_order(original,bad))
outer1=read(ROOT/'.runs/roller-export-alias-native-001-execution/execution.json');outer2=read(ROOT/'.runs/roller-export-alias-native-002-execution/execution.json')
assert inventory(OLD)==old_before and {n:sha(ROOT/n) for n in modules}==code_before
result={'schema':1,'kind':'independent-readonly-alias-path-review','native_execution':False,'solver_execution':False,'accepted':False,'production_support':False,'prior_controller_status_preserved':'failed','prior_reason':record['reason'],'actual_native_002_git_head':record['tools']['git_head'],'current_reviewed_code_sha256':code_before,'retained_runtime_current_mismatches':changed,'all_other_retained_runtime_files_match':True,'pin_files_and_full_source_inventory_match':True,'retained_actual_002_tree':invjson(old_before),'retained_tree_digest':digest(invjson(old_before)),'retained_tree_bytes':sum((OLD/n).stat().st_size for n in old_before[0]),'cases':cases,'comparison':{'alias_only_diff_paths':diffs,'only_additional_raw_difference':'root design absolute output filename','bound_comparison_normalized_equal':True,'normalized_sha256':hashlib.sha256(normal[0]).hexdigest(),'raw_dsn_and_raw_ses_not_rewritten':True},'pure_controls':controls,'old_attempt_cost_prefix':{'001':{'wall_seconds':outer1['wall_seconds'],'full_cpu_seconds':outer1['full_cpu_seconds']},'002':{'wall_seconds':outer2['wall_seconds'],'full_cpu_seconds':outer2['full_cpu_seconds']},'combined_wall_seconds':outer1['wall_seconds']+outer2['wall_seconds'],'combined_full_cpu_seconds':outer1['full_cpu_seconds']+outer2['full_cpu_seconds'],'baseline_if_in_scope':pins['prior_baseline']},'review_wall_seconds':time.monotonic()-start,'evidence_unchanged_at_end':True,'code_unchanged_at_end':True}
(OUT/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':'checks_passed','result_sha256':sha(OUT/'RESULT.json'),'actual_tree_bytes':result['retained_tree_bytes'],'code_mismatches':list(changed),'normalized_sha256':result['comparison']['normalized_sha256'],'checks':len(controls),'review_wall_seconds':result['review_wall_seconds']},sort_keys=True))
