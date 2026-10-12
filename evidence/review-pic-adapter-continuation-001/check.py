"""Offline actual-cache continuation guard replay and native gate checks; no workers."""
import ast, copy, hashlib, importlib.util, json, sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import sexpr as sx
from autorouter.placement_clearance import inventory,read_bytes
from experiments.pic_mixed_transport_probe_v1 import routing_checks,routing_native,ses_checks
HERE=ROOT/'experiments/pic_mixed_transport_probe_v1';OUT=Path(__file__).parent;RUN=ROOT/'.runs/pic-corrected-adapter-routing-001'
spec=importlib.util.spec_from_file_location('review_adapter_driver',HERE/'driver.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
load=lambda p:json.loads(read_bytes(p,16*1024*1024))
sha=lambda raw:hashlib.sha256(raw).hexdigest()
original_before=d.inventory(d.original.SOURCE.parent);run_before=d.inventory(RUN)
summary=load(RUN/'summary.json');protocol=load(HERE/'ADAPTER_NATIVE_PROTOCOL.json')
assert protocol['mode']=='local250-routing-adapter-native' and protocol['reuse_routing']==str(RUN.relative_to(ROOT))
assert all(run_before[k]==v for k,v in summary['frozen_evidence'].items())
# Execute the existing guarded cache branch verbatim, with its already-bound
# dependencies from the actual retained run; writes only tiny owned review copies.
module=ast.parse((HERE/'driver.py').read_text());fn=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='experiment')
branches=[n for n in ast.walk(fn) if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='native_from_routing']
assert len(branches)==1
fragment=compile(ast.fix_missing_locations(ast.Module(body=branches[0].body,type_ignores=[])),str(HERE/'driver.py'),'exec')
base_before=copy.deepcopy(summary['runtime']);base_before['cached_routing_inventory']=run_before
for name in ('MixedClassProbe.java','SelectiveAreaProbe.java','SelectiveRoutingProbe.java','ExactPointWitness.java'):
 key=str((HERE/name).relative_to(ROOT));assert base_before['sources'][key]==d.base.content(HERE/name,2*1024*1024,digest=True)
results=[]
for case in ('positive','unrouted_bytes','helper_digest','frozen_observations','source_hashes'):
 out=OUT/case;out.mkdir();before=copy.deepcopy(base_before)
 env=dict(ROOT=ROOT,HERE=HERE,protocol=protocol,base=d.base,before=before,inventory=d.inventory,
          derived=read_bytes(RUN/'mixed.dsn'),unrouted=read_bytes(RUN/'unrouted.dsn'),expected=load(RUN/'expectations.json'),
          route_expected=load(RUN/'routing-expectations.json'),removal=load(RUN/'removal-ledger.json'),
          adapter_proposal=True,out=out,record={},capture=lambda:None)
 if case=='unrouted_bytes':env['unrouted']+=b'\n'
 if case=='helper_digest':before['sources'][str((HERE/'ExactPointWitness.java').relative_to(ROOT))]['sha256']='0'*64
 if case=='frozen_observations':before['cached_routing_inventory']['observations.json']='0'*64
 if case=='source_hashes':before['original']['pic_programmer.kicad_pro']='0'*64
 try:exec(fragment,env);passed=True;error=None
 except ValueError as exc:passed=False;error=str(exc)
 assert passed==(case=='positive'),(case,passed,error)
 results.append({'case':case,'cache_guard_passed':passed,'error':error})
 if passed:
  assert all(read_bytes(out/n,16*1024*1024)==read_bytes(RUN/n,16*1024*1024) for n in ('observations.json','prepared.json','raw.ses'))
  assert env['record']['routing_reuse']['new_routing_execution'] is False and env['record']['routing_reuse']['new_ses_writer_execution'] is False
obs=load(RUN/'observations.json');expected=load(RUN/'routing-expectations.json');receipt=load(RUN/'routing-adapter.json')
strict=routing_checks.compare(obs,expected,load(RUN/'selective-basis-observations.json'),adapter_receipt=receipt)
assert strict['geometry_verified'] is True
# Shared recipe makes a complete original-rules copy, only ordinary routes removed.
task=routing_native.task_copy(RUN/'observe-input/pic_programmer.kicad_pcb',OUT/'task-project')
_,transport=ses_checks.audit(read_bytes(RUN/'raw.ses'),read_bytes(RUN/'unrouted.dsn'),expected,sx.read(task),obs['final_geometry'],generated=True,proposal_only=False)
assert transport['safe_structure'] is True and transport['generated_engine_to_ses_exact'] is True and transport['proposal_only'] is False
transport['adapter_proposal_only']=True
class ReachedNative(Exception):pass
gates=[]
for case in ('positive','structure_false','exact_null','adapter_absent','bool_string'):
 value=copy.deepcopy(transport)
 if case=='structure_false':value['safe_structure']=False
 if case=='exact_null':value['generated_engine_to_ses_exact']=None
 if case=='adapter_absent':value['adapter_proposal_only']=False
 if case=='bool_string':value['generated_engine_to_ses_exact']='true'
 with patch.object(routing_native.ses_native,'SesJob',side_effect=ReachedNative):
  try:routing_native.execute(OUT,task,expected,value,lambda:180,None,{},lambda:None,{},None,diagnostic_only=True)
  except ReachedNative:reached=True
  except ValueError:reached=False
  else:raise AssertionError('native gate did not stop at sentinel')
 assert reached==(case=='positive'),case
 gates.append({'case':case,'reached_mock_native_boundary':reached})
assert run_before==d.inventory(RUN) and original_before==d.inventory(d.original.SOURCE.parent)
source={n:{'sha256':sha(read_bytes(HERE/n)),'bytes':len(read_bytes(HERE/n))} for n in ('driver.py','routing_native.py','routing_checks.py','ADAPTER_NATIVE_PROTOCOL.json')}
result={'scope':'Actual cached bytes and shared pure checkers; native job constructor mocked only to stop at gate. No native/JVM/compiler/solver.','source':source,'cache_guards':results,'native_gate':gates,'strict':strict,'generated_transport':transport,'original_files_unchanged':len(original_before),'full_failed_run_files_unchanged':len(run_before),'failed_summary_unchanged':run_before['summary.json']}
(OUT/'checks.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2))
