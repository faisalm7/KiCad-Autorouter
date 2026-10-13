"""Independent targeted cache controls on complete existing receipt fixtures.
All temporary writes stay in this review folder. The exact tool_manifest body
hashes actual tools/code/lock; only Git lookup is replaced by a static marker.
Synthetic receipt declarations do not qualify a fresh native execution.
"""
from pathlib import Path
import ast,copy,json,sys,tempfile,subprocess,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'tests')];sys.dont_write_bytecode=True
from autorouter import pipeline as p
import test_validation_readback as tests
text=(ROOT/'autorouter/pipeline.py').read_text();node=copy.deepcopy(next(x for x in ast.parse(text).body if isinstance(x,ast.FunctionDef) and x.name=='tool_manifest'));node.name='review_tool_manifest'
assignment=next(x for x in node.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='git_head' for t in x.targets));assignment.value=ast.Constant('review-no-git')
namespace=dict(vars(p));exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(ROOT/'autorouter/pipeline.py'),'exec'),namespace);identity=namespace['review_tool_manifest']
real_temp=tempfile.TemporaryDirectory
def owned_temp(*args,**kwargs):kwargs['dir']=HERE;return real_temp(*args,**kwargs)
def forbidden(*args,**kwargs):raise RuntimeError('review forbids child processes')
suite=unittest.defaultTestLoader.loadTestsFromTestCase(tests.ReadbackSession)
with patch.object(p,'tool_manifest',identity),patch.object(tempfile,'TemporaryDirectory',owned_temp),patch.object(subprocess,'run',side_effect=forbidden),patch.object(subprocess,'Popen',side_effect=forbidden):
 result=unittest.TextTestRunner(verbosity=2).run(suite)
p.save_json(HERE/'targeted-controls-001.json',{'scope':__doc__,'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'successful':result.wasSuccessful(),'pipeline_sha256':p.sha(ROOT/'autorouter/pipeline.py'),'test_source_sha256':p.sha(ROOT/'tests/test_validation_readback.py'),'native_executed':False,'git_executed':False})
if not result.wasSuccessful():raise SystemExit(1)
