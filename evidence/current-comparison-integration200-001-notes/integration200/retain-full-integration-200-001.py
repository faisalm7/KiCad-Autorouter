"""Small integration receipt using the existing retained-text/index helpers."""
from pathlib import Path
import ast,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
notes=ROOT/'evidence/current-comparison-integration200-001-notes';target=ROOT/'evidence/current-comparison-integration200-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','cost')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared','exec'),globals())
base=ROOT/'.runs/full-integration-200';protocol=json.loads((base/'protocol.json').read_bytes());execution=json.loads((base/'execution.json').read_bytes())
assert execution['passed'] is True and execution['sources_unchanged'] is True
assert protocol['tools']['git_head']=='0fc886233ec49f8dbe507f5826130f23c6391f36'
assert execution['process']['status']=='success' and execution['process']['exit_code']==0 and execution['process']['cleanup_complete'] is True and execution['process']['log_truncated'] is False
assert all(p.sha(ROOT/name)==pin for name,pin in protocol['source_sha256'].items())
assert p.sha(base/'command.log')==execution['log_sha256']
assert 'Ran 2515 tests' in (base/'command.log').read_text() and 'OK (skipped=1)' in (base/'command.log').read_text()
paths=[*(base/name for name in ('protocol.json','execution.json','command.log')),ROOT/'.runs/run-full-integration-200.py',ROOT/'.runs/full-suite-local-root-019.py',ROOT/'.runs/full-integration-200-controller-001.log',ROOT/'.runs/full-integration-200-time-001.log',Path(__file__)]
for path in paths:retain(path,Path('integration200')/path.name)
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material))
p.save_json(target,dict(schema=1,kind='current-comparison-administration-full-integration200-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),administration_source_head=protocol['tools']['git_head'],product_source_head='aa0072c6b3d8090de2603e5ecb42a95968fb873b',product_runtime_changed=False,passed=True,tests=2515,skipped=1,complete_external=cost(ROOT/'.runs/full-integration-200-time-001.log'),nested=dict(wall_seconds=execution['wall_seconds'],CPU_seconds=execution['full_cpu_seconds']),source_pins_unchanged=True,Native_routing_qualification=False,GUI_qualification=False,comparison_executed=False,project_complete=False,scope='Full current regression suite after comparison administration controls and reporting fixes; includes preserved QFN experiment regressions. Runtime050 and its completed Native/GUI proofs unchanged. Existing helper/discovery/shared runner and Native lane reused. Test count is not routing quality. Complete external and nested samples overlap; count once. Preparation/curation/research/authoring/AI review additional, unknown costs notzero.',dependency=dict(path='evidence/current-comparison-improve-administration-001.json',sha256=p.sha(ROOT/'evidence/current-comparison-improve-administration-001.json')),backup='Small owned source/log facts; newer full raw remains Mac-only/outside010, full restoration capacity still blocked.',files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index))))
print(json.dumps(dict(files=len(files),bytes=total,passed=True)))
