"""Actual installed CLI refusal; new owned source differs in one ordinary field."""
import time,resource
START=time.monotonic()
def cpu():return sum(r.ru_utime+r.ru_stime for r in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import json,os,sys
ROOT=Path(__file__).resolve().parents[1];RUNTIME=ROOT/'.runs/runtime-directory-009/runtime';sys.path.insert(0,str(RUNTIME));sys.path.append(str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,config as c,handoff as h,sexpr as sx
from autorouter.runner import run
from experiments.hfe_original_native_v1.driver import material
from experiments.placement_handoff_native_v1.driver import copy_bytes
assert c.ROOT==RUNTIME and Path(sys.prefix).resolve()==RUNTIME/'.venv'
setup=f.read_json(ROOT/'.runs/runtime-directory-009/setup.json');original=Path(setup['duplicate_artwork_source']);before=p.tree_hash(original.parent)
assert before==setup['duplicate_artwork_source_hashes']
out=ROOT/'.runs/runtime009-duplicate-artwork-field-negative-001';out.mkdir();owner={};h.capture_destination(owner,out)
packet={n:(original.parent/n).read_bytes()for n in before};tree=sx.parse(packet[original.name].decode());prior=sx.parse(sx.dump(tree))
fp=next(fp for fp in sx.children(tree,'footprint')if sx.unquote(sx.one(fp,'uuid')[1])not in setup['duplicate_artwork_UUIDs'])
field=next(n for n in sx.children(fp,'property')if sx.unquote(n[1])=='Description');old=field[2];field[2]='"OWNED_INVALID_ORDINARY_DESCRIPTION"';negative=sx.parse(sx.dump(tree));field[2]=old;assert tree==prior
packet[original.name]=(sx.dump(negative)+'\n').encode();copy_bytes(packet,out/'source');source=out/'source'/original.name;negative_hashes=p.tree_hash(source.parent)
tools=p.tool_manifest();pin=p.sha(__file__);record=dict(schema=1,accepted=False,controls_passed=False,status='failed',source_hashes=negative_hashes,original_source_hashes=before,tools=tools,ordinary_footprint_uuid=sx.unquote(sx.one(fp,'uuid')[1]),scope='Fresh installed CLI negative, changes only one ordinary PCB Description in newly owned source; complete originalSCH/PRO/PRL, sourceartwork/group/geometry/rules unchanged. Must refuse Native field mismatch before routing engine. Not a delivered candidate or routing comparison.')
def remaining():return min(28-(time.monotonic()-START),28-(cpu()-CPU0))
try:
 process=run([*f.SANDBOX,str(RUNTIME/'.venv/bin/python'),'-B','-m','autorouter','route',str(source),'--output',str(out/'route'),'--seconds','30','--adapter','both','--keep-existing'],cwd=RUNTIME,log=out/'command.log',timeout=max(.001,remaining()-2),max_log_bytes=256*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=2*1024**3,env={k:v for k,v in os.environ.items()if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}})
 record['process']=process;route=f.read_json(out/'route/result.json');record['route']=route
 assert process['exit_code']==2 and process['cleanup_complete']is True and process['log_truncated']is False
 assert route['accepted']is False and route.get('candidate_sha256')is None
 assert not any(str(c.JAVA)in step.get('argv',[])for step in route.get('steps',[]))
 native=route['source_drc'];proof=native['field_parity'];assert proof['qualification']['qualified']is False and 'Description'in proof['qualification']['reason']
 assert proof['board_only_field_census']['policy']=='source-bound-padless-field-census-v2'
 assert native['warnings']==8 and native['exclusions']==0
 record.update(controls_passed=True,status='completed',engine_executed=False,route_receipt_sha256=p.sha(out/'route/result.json'))
except(Exception,KeyboardInterrupt)as exc:record.update(controls_passed=False,status='cancelled'if isinstance(exc,KeyboardInterrupt)else'failed',error=type(exc).__name__+': '+str(exc))
witness=material(out);record['completed_evidence']=witness
def stable():
 h.owned_destination(owner)
 if p.tree_hash(original.parent)!=before or p.tree_hash(source.parent)!=negative_hashes or p.tool_manifest()!=tools or p.sha(__file__)!=pin or material(out)!=witness:raise p.Rejected('installed negative source/runtime/evidence changed')
def account():
 record.update(wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0)
 if remaining()<=0:record.update(status='budget_exceeded',controls_passed=False)
 if record['status']!='completed':record['controls_passed']=False
f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
print(json.dumps({k:record.get(k)for k in('status','controls_passed','error','wall_seconds','full_CPU_seconds')}));raise SystemExit(0 if record['status']=='completed'and record['controls_passed']else 2)
