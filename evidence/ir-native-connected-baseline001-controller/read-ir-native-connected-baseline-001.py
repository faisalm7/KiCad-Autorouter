"""Pure independent readback with shared Native/process/original-design helpers."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,math,subprocess,copy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
real=subprocess.Popen
def readonly(argv,*args,**kwargs):
 if argv!=['git','rev-parse','HEAD'] or Path(kwargs.get('cwd','')).resolve()!=ROOT:raise AssertionError('reader permits only exact read-only Git HEAD')
 return real(argv,*args,**kwargs)
subprocess.Popen=readonly
from autorouter import pipeline as p,floor_route as f,board_floor as g,native_connected as nc,sexpr as sx,placement_clearance as pc,preferences as pref,local_settings as ls
from experiments.ir_native_connected_baseline_v1 import actor as a
from scripts import experiment_quality as q
OUT=ROOT/'.runs/ir-native-connected-baseline-readback-001';OUT.mkdir()
record=dict(schema=1,passed=False,accepted=False,new_native=False,new_engine=False,old_semantic_reader_replayed=False)
try:
 specpath=ROOT/'.runs/ir-native-connected-baseline-protocol-001.json';spec=f.read_json(specpath);specpin=p.sha(specpath);base=ROOT/'.runs/ir-native-connected-baseline-001';outerpath=ROOT/'.runs/ir-native-connected-baseline-execution-001/execution.json';outer=f.read_json(outerpath);data=f.read_json(base/'result.json');receiptpin=p.sha(base/'result.json');outerpin=p.sha(outerpath)
 def need(ok,why):
  if not ok:raise p.Rejected(why)
 def stable():
  need(p.tool_manifest()==spec['tools'],'current source/tools/HEAD changed');q.verify_freeze(spec['freeze'],Path(spec['source']))
  for n,d in spec['pins'].items():need(p.sha(ROOT/n)==d,'frozen prior/helper changed: '+n)
  need(p.sha(specpath)==specpin==outer['protocol_sha256']==data['protocol_sha256'] and p.sha(base/'result.json')==receiptpin==outer['result_sha256'] and p.sha(outerpath)==outerpin,'new receipt/protocol/outer changed')
  need(f.evidence_inventory(base)==outer['material']==data['completed_evidence'],'whole actor material changed')
  need((p.tree_hash(ROOT/'.runs/ir-native-connected-classifier-001') if (ROOT/'.runs/ir-native-connected-classifier-001').exists() else None)==outer['classifier_material']==data['classifier_material'],'classifier material changed')
  need(p.sha(Path(__file__))==spec['reader_sha256'] and p.sha(ROOT/'experiments/ir_native_connected_baseline_v1/actor.py')==spec['actor_sha256'],'reader/actor changed')
 stable();need(data['tools']==spec['tools'] and p.sha(base/'actor.py')==spec['actor_sha256'] and p.sha(base/'prospective.json')==specpin,'captured actor/protocol/runtime differs');source=Path(spec['source']);original=p.preflight(source);need(p.tree_hash(source.parent)==p.tree_hash(base/'source')==spec['source_hashes']==data['source_hashes'],'original source differs')
 need(data['accepted'] is False and data['production_qualified'] is False and outer['accepted'] is False and outer['production_qualified'] is False,'diagnostic scope differs')
 need(outer['status']=='completed' and outer['source_current'] is True and outer['within_actor_and_common_caps'] is True,'outer failed or exceeded caps')
 proc=outer['process'];need(proc['status'] in ('success','nonzero_exit') and proc['exit_code'] in (0,2) and proc['cleanup_complete'] is True and proc['log_truncated'] is False and p.sha(Path(proc['log']))==outer['log_sha256'],'actor process failed')
 need(proc['argv']==[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'experiments/ir_native_connected_baseline_v1/actor.py'),'--run-native','--output',str(base),'--protocol',str(specpath),'--protocol-sha256',specpin] and proc['cwd']==str(outerpath.parent),'actor command identity differs')
 probe=ROOT/'.runs/ir-native-connected-classifier-001';task=probe/'task'/source.name
 if 'classification' in data:
  cl=f.read_json(probe/'result.json');actual=nc.readback(probe,cl,base/'source'/source.name,task,probe/'refill'/source.name,probe/'candidate'/source.name,probe/'native.dsn')
  need(actual==data['classification'] and p.sha(probe/'result.json')==data['classifier_receipt_sha256'] and pc.read_bytes(task)==(sx.dump(g.task_from_source(original))+'\n').encode() and not p.routes(sx.read(task)),'fresh classifier/source binding differs')
 if 'child_receipt_sha256' in data:
  child=f.read_json(base/'route/result.json');need(p.sha(base/'route/result.json')==data['child_receipt_sha256'] and child['source']==str(task) and child['source_hashes']==p.tree_hash(task.parent),'selected child source differs')
  settings=pref.validate(f.read_json(base/'preferences.json'));need(settings==pref.readback(pc.read_bytes(base/'route/routing-preferences.json')) and settings['profile']=='completion-only' and settings['scoring_preference']=='via_high' and settings['nets']==data['classification']['active_names'],'selected baseline preset differs')
  if child['accepted']:need(p.check_result(base/'route/result.json')['current'] is True,'selected child is stale')
 need(type(data.get('method_qualified')) is bool,'method qualification must be exact bool')
 if data['method_qualified']:
  need(all(k in data for k in ('classification','child_receipt_sha256','final_candidate','metrics')),'qualified method missing mandatory proof')
  need(data['status']=='completed' and data['within_budget'] is True and max(data['wall_seconds'],data['total_cpu_seconds'])<=95 and proc['exit_code']==0,'actor successful budget differs')
 if 'final_candidate' in data:
  baseline=a.original_baseline(spec);entry=data['final_candidate'];job=base/'whole-original';candidate=Path(entry['candidate']);ctx=dict(steps=data['steps'],tools=spec['tools'],source_hashes=spec['source_hashes'])
  expected=p.transplant_routes(g.task_from_source(original),sx.read(Path(child['candidate'])),protected=[],policy='exact_non_uuid_lock_position_v2')
  need(pc.read_bytes(job/'pre-refill.kicad_pcb')==(sx.dump(expected)+'\n').encode(),'parent is not exact selected child transplantation')
  saved=f.check_drc_stage(job,ctx,'refill-drc',job/'refill'/source.name,job/'refill'/source.name,True,{**spec['source_hashes'],source.name:p.sha(job/'pre-refill.kicad_pcb')})
  final=f.check_drc_stage(job,ctx,'final-drc',candidate,job/'final-drc-input'/source.name,False,{**spec['source_hashes'],source.name:entry['candidate_sha256']},schematic_parity=True)
  need(saved==entry['saved_native'] and final==entry['native'] and p.sha(job/'final-drc.json')==entry['report_sha256'],'whole-original Native/warning/rule binding differs')
  if data['method_qualified']:need(p.native_accepted(final) and a.warn(final)==a.warn(baseline) and final['ignored_checks']==baseline['ignored_checks'],'whole-original acceptance or warning preservation failed')
  need(pc.read_bytes(candidate)==(sx.dump(p.transplant_fill(expected,sx.read(job/'refill'/source.name)))+'\n').encode() and p.immutable(sx.read(candidate))==p.immutable(original),'original shell/fill/routes differ');p.verify_candidate_files(candidate,spec['source_hashes'],entry['candidate_sha256']);ls.check_normal_policy(job,ctx)
  if p.netclass_policy(candidate) is not None:
   mapping=job/'final-netclasses.json';audit=p.audit_candidate_netclasses(candidate,[],f.read_json(mapping));audit['native_map_file_sha256']=p.sha(mapping);f.process_check(job,ctx,'final-netclasses',[*f.SANDBOX,str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'netclasses',str(candidate),str(mapping)]);need(audit==f.read_json(job/'final-netclass-audit.json'),'final classes differ')
  record['final_candidate']=entry
  if 'metrics' in data:
   metrics=f.read_json(job/'metrics.json');f.process_check(job,ctx,'metrics',[*f.SANDBOX,str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'metrics',str(candidate),str(job/'metrics.json')]);need(metrics==data['metrics'] and p.sha(job/'metrics.json')==data['metrics_sha256'] and metrics['version']=='10.0.0','actual metrics differ');record['metrics']=metrics;record['final_candidate']=entry
 need(f.read_json(ROOT/spec['prior_execution'])['final_charged_results']==spec['prior_rows'],'retained prior rows changed')
 stable();record.update(passed=True,method_qualified=data['method_qualified'],actor_status=data['status'],actor_reason=data.get('reason'),classification=data.get('classification'),outer_sha256=outerpin,result_sha256=receiptpin,protocol_sha256=specpin)
except (Exception,KeyboardInterrupt) as exc:record['error']=type(exc).__name__+': '+str(exc)
wall,full=time.monotonic()-START,cpu()-CPU0;record.update(wall_seconds=wall,full_cpu_seconds=full)
if max(wall,full)>25:record.update(passed=False,error='reader25 cap exceeded')
p.save_json(OUT/'result.json',record);print(json.dumps({k:record.get(k) for k in ('passed','error','method_qualified','actor_status','actor_reason','wall_seconds','full_cpu_seconds','metrics')}));raise SystemExit(0 if record['passed'] else 2)
