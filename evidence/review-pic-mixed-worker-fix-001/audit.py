"""Read-only API ownership and one pure regression; no native/JVM imports or calls."""
from pathlib import Path
import ast,hashlib,importlib.util,json,sys
from unittest.mock import patch
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;RUN=R/'.runs/pic-mixed-transport-probe-001';CURRENT=R/'experiments/pic_mixed_transport_probe_v1'
sys.dont_write_bytecode=True;sys.path.insert(0,str(R));sys.path.insert(0,str(CURRENT))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
from autorouter import placement_clearance as io
before=io.inventory(RUN,max_bytes=64*1024**2,max_files=2000,max_entries=4000)
r=json.loads((RUN/'summary.json').read_text());w=Path('/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/pcbnew.py')
assert sha(w)==r['runtime']['tools']['native_wrapper']['sha256']
classes={c.name:c for c in ast.parse(w.read_text()).body if isinstance(c,ast.ClassDef)}
methods=lambda name:{x.name:x for x in classes[name].body if isinstance(x,ast.FunctionDef)}
assert [ast.unparse(x) for x in classes['PAD'].bases]==['BOARD_CONNECTED_ITEM']
assert 'GetEffectiveNetClass' in methods('BOARD_CONNECTED_ITEM') and 'GetNetClassSlow' not in methods('BOARD_CONNECTED_ITEM') and 'GetNetClassSlow' not in methods('PAD')
assert 'GetNetClassSlow' in methods('NETINFO_ITEM')
method=methods('BOARD_CONNECTED_ITEM')['GetEffectiveNetClass'];assert ast.get_docstring(method)=='GetEffectiveNetClass(BOARD_CONNECTED_ITEM self) -> NETCLASS'
cpp=R/'.runs/pic-clearance-api-001/source/board_connected_item.cpp';assert sha(cpp)==r['runtime']['basis'][str(cpp.relative_to(R))]['sha256']
assert 'NETCLASS* BOARD_CONNECTED_ITEM::GetEffectiveNetClass() const' in cpp.read_text()
old=RUN/'code/experiments/pic_mixed_transport_probe_v1/worker.py';now=CURRENT/'worker.py'
assert old.read_text().replace('pad.GetNetClassSlow()','pad.GetEffectiveNetClass()')==now.read_text()
for path,digest in r['frozen_evidence'].items():assert sha(RUN/path)==digest
assert r['native_process_executed'] is True and r['import_process_executed'] is False and len(r['steps'])==1 and r['steps'][0]['exit_code']==1 and r['steps'][0]['cleanup_complete'] is True
assert all(r[k] is False for k in ('observations_complete','routing_executed','ses_executed','routing_accepted','custom_pad_support_qualified','mixed_clearance_equivalence_qualified'))
log=(RUN/'native-observe.log').read_text();assert "AttributeError: 'PAD' object has no attribute 'GetNetClassSlow'" in log
assert json.loads((RUN/'clearance-initialization.json').read_text())=={'initialization_error_type':'AttributeError'}
assert not any((RUN/name).exists() for name in ('initialization-drc.txt','context.json','custom.json','native.dsn','mixed.dsn','observations.json','compile-process.json','import-process.json'))
original=R/'.data/boards/kicad-pic-programmer';assert io.inventory(original)==r['runtime']['original']==io.inventory(RUN/'observe-input') and len(r['runtime']['original'])==15
spec=importlib.util.spec_from_file_location('specific_mixed_test',CURRENT/'test_draft.py');tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
new_method=tests.Pure('test_clearance_census_uses_pad_effective_class_api');new_method.test_clearance_census_uses_pad_effective_class_api()
spec=importlib.util.spec_from_file_location('failed_native_worker',old);oldworker=importlib.util.module_from_spec(spec);spec.loader.exec_module(oldworker)
try:
 with patch.object(tests,'worker',oldworker):tests.Pure('test_clearance_census_uses_pad_effective_class_api').test_clearance_census_uses_pad_effective_class_api()
except AttributeError as exc:old_error=str(exc)
else:raise AssertionError('old worker must fail same fake PADs')
assert 'GetNetClassSlow' in old_error
outerpath=R/'.runs/pic-mixed-transport-probe-001-execution.json';outer=json.loads(outerpath.read_text())
assert outer['exit_code']==1 and outer['git_head']==r['runtime']['git']['head']
assert io.inventory(RUN,max_bytes=64*1024**2,max_files=2000,max_entries=4000)==before
result={'schema':1,'passed':True,'scope':'Getter ownership/API source and exact single-regression review, not native qualification','worker_before_sha256':sha(old),'worker_after_sha256':sha(now),'tests_sha256':sha(CURRENT/'test_draft.py'),'wrapper_sha256':sha(w),'source_cpp_sha256':sha(cpp),'wrapper_ownership':{'PAD_bases':['BOARD_CONNECTED_ITEM'],'effective_getter_owner':'BOARD_CONNECTED_ITEM','effective_return':'NETCLASS','slow_getter_owner':'NETINFO_ITEM'},'same_247_fake_PAD_regression':{'fixed_passed':True,'old_failed_as_expected':old_error,'fake_PAD_has_slow_getter':False},'actual_failure':{'head':r['runtime']['git']['head'],'summary_sha256':sha(RUN/'summary.json'),'native_log_sha256':sha(RUN/'native-observe.log'),'initialization_sidecar_sha256':sha(RUN/'clearance-initialization.json'),'steps':1,'native_exit_code':1,'shared_wall_seconds':r['wall_seconds'],'shared_total_cpu_seconds':r['total_cpu_seconds'],'outer':outer,'initialization_export_compile_import_not_reached':True,'original15_unchanged':True,'raw_inventory_unchanged_during_review':True},'native_jobs':0,'jvm_jobs':0,'full_suites':0,'remaining_blockers':[]}
(H/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'worker_sha256':sha(now),'old_fake_pad_error':old_error},indent=2))
