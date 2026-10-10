"""Real-file prerequisite source mutation with mocked native stages, not native proof."""
from pathlib import Path
import sys,shutil,json
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE/'snapshot-001'))
import test_diagnostic as t
p=t.d.p;d=t.d;pair=t.pair
case=t.PairTests(methodName='test_shared_overhead_both_arms_and_identical_assignment');case.setUp()
try:
 origin=case.base/'qualification-original';shutil.copytree(t.FIXTURE,origin);expected=p.tree_hash(origin)
 fixture={'source':str(origin/'fixture.kicad_pcb'),'source_hashes':expected,'tools':{},'freeze':{'files_sha256':case.frozen['files_sha256']},'policy':d.POLICIES[1],'native':t.clean(),'metrics':{'vias':1}}
 p.save_json(case.fixture/'result.json',fixture)
 # Restore actual gate while native report readback remains mocked. The mock
 # reproduces its source-tree guard explicitly; all file hashes/trees are real.
 gate=case.patches[-3];gate.stop()
 calls=[]
 def checked(path):
  calls.append(str(path))
  if Path(path)==case.fixture/'result.json' and p.tree_hash(origin)!=expected:raise p.Rejected('diagnostic source/snapshot/candidate identity changed')
  return {'diagnostic_verified':True,'routing_accepted':True}
 def route(source,out,assigned,policy):
  value=case.route(source,out,assigned,policy)
  if policy==d.POLICIES[0]:(origin/'fixture.kicad_pro').write_text('{}')
  return value
 with patch.object(d,'narrow_source',side_effect=lambda tree: d.placement.source_zones(tree) if tree else []),patch.object(pair,'fixture_gate',wraps=pair.fixture_gate),patch.object(d,'check_result',side_effect=checked),patch.object(d,'route',side_effect=route):
  result=case.run_pair()
 try:checked(case.fixture/'result.json');stale_would_reject=False
 except p.Rejected:stale_would_reject=True
 output={'native_executed':False,'stage_scope':'mocked routes/native checks; actual filesystem source mutation and original fixture gate','summary_status':result['status'],'summary_reason':result.get('reason'),'comparison_eligible':result['comparison_eligible'],'fixture_original_changed':p.tree_hash(origin)!=expected,'fresh_fixture_check_would_reject':stale_would_reject,'fixture_check_calls_during_pair':calls.count(str(case.fixture/'result.json'))-1,'pair_sha256':p.sha(HERE/'snapshot-001/experiment_pair.py')}
 with (HERE/'fixture-freshness-002.json').open('x') as stream:json.dump(output,stream,indent=2);stream.write('\n')
 print(json.dumps(output,indent=2))
finally:case.tearDown()
