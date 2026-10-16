"""Reuse the owned four-copper geometry and same-rule Native negative control."""
from pathlib import Path
import importlib.util,json,resource,sys,time
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1]
runtime=ROOT/'.runs/runtime-directory-007/runtime';sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,sexpr as sx,board_floor as g,review_export as ex,local_settings as ls
assert c.ROOT==runtime and Path(sys.prefix).resolve()==runtime/'.venv'
case=ROOT/'.runs/runtime-directory-007/native1000';case.mkdir()
setup=json.loads((case.parent/'setup.json').read_bytes())
workflow=json.loads((runtime/'.runs/qualification-route/result.json').read_bytes());workspace=Path(workflow['workspace'])
tools=p.tool_manifest();original=p.tree_hash(Path(setup['source']).parent);assert original==setup['source_hashes']
source=sx.read(Path(setup['source']));protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},source)
driver=ROOT/'evidence/four-cu-class-native-001/driver.py';pin=p.sha(driver)
spec=importlib.util.spec_from_file_location('retained_owned_four_cu_control',driver);control=importlib.util.module_from_spec(spec);spec.loader.exec_module(control)
positive=json.loads((workspace/'route/result.json').read_bytes());export=json.loads((workspace/'export/export.json').read_bytes())
record=dict(schema=1,accepted=False,passed=False,source_head=tools['git_head'],tools=tools,source_hashes=original,helper_sha256=pin,workflow_sha256=p.sha(runtime/'.runs/qualification-route/result.json'),negative_attempt={})
try:
 with p.validation_readback_session():
  checked=p.check_result(workspace/'route/result.json');export_checked=ex.check_export(workspace/'export/export.json')
 assert workflow['workflow_delivered'] and checked['current'] and export_checked['current']
 tree=sx.read(Path(positive['candidate']));_,resolve=g.source_net_identity(tree)
 generated=[row for row in p.routes(tree) if row not in protected]
 vias=[row for row in generated if row[0]=='via'];inner={resolve(sx.one(row,'net'))for row in generated if row[0]in('segment','arc')and sx.one(row,'layer')in(['layer','"In1.Cu"'],['layer','"In2.Cu"'])}
 route_vias=[row for row in vias if resolve(sx.one(row,'net'))=='ROUTE']
 assert len(protected)==10 and all(p.locked(row)and row in p.routes(tree)for row in protected)
 assert len(route_vias)>=2 and set(setup['required_new_inner_nets'])<=inner
 assert all(sx.one(row,'layers')==['layers','"F.Cu"','"B.Cu"']for row in vias)
 assert sx.one(tree,'layers')==sx.one(source,'layers') and p.immutable(tree)==p.immutable(source)
 assert positive['source_drc']['opens']==1 and positive['source_drc']['blocking']==0
 assert p.native_accepted(positive['native']) and positive['native']['exclusions']==0
 assert positive['native']['field_parity']['qualification']['component_count']==6
 assert positive['native']['field_parity']['qualification']['compared_field_count']==18
 assert positive['metrics']['copper_layers']==4
 plan={'source_sha256':original,'protected_ast':protected,'tools':{'native1000':tools}}
 remaining=lambda:min(85-(time.monotonic()-START),85-(cpu()-CPU0))
 negative=control.invalid_control(case,positive,plan,None,remaining,record['negative_attempt'])
 assert negative['passed'] and not p.native_accepted(negative['native'])
 # The same shared reader/event checks remain mandatory after the control.
 data={'steps':negative['steps']}
 replay=control.f.check_drc_stage(case/'invalid-job',data,'invalid-final',Path(negative['candidate']),case/'invalid-job/invalid-final-input'/Path(setup['source']).name,False,negative['before'],schematic_parity=True)
 assert control.f.canonical(replay)==control.f.canonical(negative['native'])
 ls.check_event(case/'invalid-job',control.f.read_json(case/'invalid-job/invalid-final-binding.json'),control.f.read_json(case/'invalid-job/invalid-final-process.json'))
 assert p.tree_hash(Path(setup['source']).parent)==original and p.tool_manifest()==tools and p.sha(driver)==pin
 assert p.check_result(workspace/'route/result.json')['current'] and ex.check_export(workspace/'export/export.json')['current']
 for name,module in tuple(sys.modules.items()):
  if name.split('.')[0]=='autorouter'and getattr(module,'__file__',None):assert Path(module.__file__).resolve().is_relative_to(runtime),name
 record.update(passed=True,route_pour_audit=json.loads((workspace/'route/pour-keepout-audit.json').read_bytes()),export_pour_audit=json.loads((workspace/'export/validation/pour-keepout-audit.json').read_bytes()),geometry={'protected_routes':len(protected),'generated_through_vias':len(vias),'route_through_vias':len(route_vias),'inner_nets':sorted(inner),'original_layer_table_exact':True,'original_invariants_exact':True},negative=negative,route_readback=checked,export_readback=export_checked)
except BaseException as exc:
 record.update(passed=False,error=type(exc).__name__+': '+str(exc))
record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
p.save_json(case/'result.json',record);print(json.dumps({k:record.get(k)for k in('passed','geometry','error','wall_seconds','full_cpu_seconds')}))
raise SystemExit(0 if record['passed']else 2)
