"""One final-runtime negative on the actual delivered candidate; no refill."""
import time,resource
START=time.monotonic()
def cpu():return sum(r.ru_utime+r.ru_stime for r in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import copy,json,sys
ROOT=Path(__file__).resolve().parents[1];RUNTIME=ROOT/'.runs/runtime-directory-007/runtime'
sys.path.insert(0,str(RUNTIME));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,pour_rule_area as policy,placement_clearance as io,config as c,handoff as h
sys.path.append(str(ROOT))
from experiments.hfe_original_native_v1.driver import BoundJob,material
from experiments.placement_handoff_native_v1.driver import copy_bytes
assert c.ROOT==RUNTIME and Path(sys.prefix).resolve()==RUNTIME/'.venv'
out=ROOT/'.runs/runtime007-pour-intrusion-001';out.mkdir();owner={};h.capture_destination(owner,out);tools=p.tool_manifest()
workflow=f.read_json(RUNTIME/'.runs/qualification-route/result.json');workspace=Path(workflow['workspace']);route=f.read_json(workspace/'route/result.json');source=Path(route['candidate']);source_hashes=p.tree_hash(source.parent)
record=dict(schema=1,accepted=False,controls_passed=False,status='failed',tools=tools,source_candidate=str(source),source_candidate_sha256=p.sha(source),source_project_hashes=source_hashes,worker_sha256=p.sha(__file__),scope='Actual delivered candidate/current runtime007 copied into one fresh owned job; append only derived In2 fill inside unchanged original area. Direct current production pour-audit without refill/save. No engine/new routing/human acceptance.')
remaining=lambda:min(40-(time.monotonic()-START),40-(cpu()-CPU0))
job=BoundJob(out/'job',remaining(),remaining,protect_local_settings=True)
try:
 with p.validation_readback_session():assert p.check_result(workspace/'route/result.json')['current']is True
 positive=f.read_json(workspace/'route/pour-keepout-audit.json');policy.verify_native_record(positive,source)
 copy_bytes(io.inventory(source.parent,contents=True),job.out/'negative');bad=job.out/'negative'/source.name;original=sx.read(bad);tree=copy.deepcopy(original)
 zones=sx.children(tree,'zone');target=next(z for z in zones if sx.one(z,'keepout')is None and sx.one(z,'layer')==['layer','"In2.Cu"'])
 injected=['filled_polygon',['layer','"In2.Cu"'],['pts',['xy','18.5','23.5'],['xy','19.5','23.5'],['xy','19.5','24.5'],['xy','18.5','24.5']]]
 target.append(copy.deepcopy(injected));sx.write(bad,tree)
 if p.immutable(tree)!=p.immutable(original)or p.routes(tree)!=p.routes(original):raise p.Rejected('negative changed original design or routes')
 restored=copy.deepcopy(tree);next(z for z in sx.children(restored,'zone')if sx.one(z,'uuid')==sx.one(target,'uuid')).pop()
 if restored!=original:raise p.Rejected('negative is not exact one-node derived delta')
 before=p.tree_hash(bad.parent);report=job.out/'negative-audit.json';argv=[c.PYTHON,c.ROOT/'autorouter/native.py','pour-audit',bad,report]
 job.step('negative-audit',argv,allowed=(1,));f.process_check(job.out,{'steps':job.steps},'negative-audit',[*f.SANDBOX,*map(str,argv)],allowed=(1,));observed=f.read_json(report)
 if observed['passed']is not False or len(observed['fill_checks'])!=len(positive['fill_checks'])or not any(row['layer']=='In2.Cu'and row['applicable']is True and row['intersection']and row['passed']is False and row['native_fill_outline_count']==row['stored_fill_node_count'] for row in observed['fill_checks']):raise p.Rejected('actual applicable intrusion did not reject')
 if observed['native_areas']!=positive['native_areas']or observed['native_area_nets']!=positive['native_area_nets']or observed['copper_layers']!=positive['copper_layers']:raise p.Rejected('negative changed area/net/layer semantics')
 try:policy.verify_native_record(observed,bad)
 except ValueError:pass
 else:raise p.Rejected('negative final-runtime reader accepted')
 if p.tree_hash(bad.parent)!=before or p.tree_hash(source.parent)!=source_hashes or p.tool_manifest()!=tools:raise p.Rejected('read-only input/runtime changed')
 record.update(status='controls_passed',controls_passed=True,positive_audit_sha256=p.sha(workspace/'route/pour-keepout-audit.json'),negative_candidate_sha256=p.sha(bad),negative_project_hashes=before,injected_node=injected,negative_audit=observed,negative_audit_sha256=p.sha(report))
except(Exception,KeyboardInterrupt)as exc:record.update(error=type(exc).__name__+': '+str(exc),status='cancelled'if isinstance(exc,KeyboardInterrupt)else'failed')
record['steps']=job.steps;witness=material(out);record['completed_evidence']=witness
def stable():
 h.owned_destination(owner)
 if p.tree_hash(source.parent)!=source_hashes or p.tool_manifest()!=tools or material(out)!=witness:raise p.Rejected('completed negative evidence/source changed')
def account():
 record.update(wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0)
 if remaining()<=0:record.update(status='budget_exceeded',controls_passed=False)
f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
print(json.dumps({k:record.get(k)for k in('status','controls_passed','error','wall_seconds','full_CPU_seconds')}))
raise SystemExit(0 if record['controls_passed']and record['status']=='controls_passed'else 2)
