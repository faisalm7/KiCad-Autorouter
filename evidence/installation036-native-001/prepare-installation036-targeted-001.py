"""Freeze current installed chain/strategy/paired controls; preparation only."""
from pathlib import Path
import ast
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f

BASE = ROOT / '.runs/installation-036'
CLONE = BASE / 'checkout'
OUT = ROOT / '.runs/installation036-preparation-001'
MODULES = ['tests.test_chain_proposals', 'tests.test_strategy', 'tests.test_paired']
WATCHED = ['autorouter.chain_proposals', 'autorouter.strategy',
           'scripts.experiment_paired', 'scripts.experiment_portfolio',
           'scripts.experiment_quality', 'experiments.chain_pruning_v1.fixture']
CONTROLLERS = ['.runs/prepare-installation036-targeted-001.py',
               '.runs/run-installation036-targeted-001.py']

receipt_path = BASE / 'result.json'
receipt = f.read_json(receipt_path)
tools = p.tool_manifest()
assert receipt['passed'] is True and receipt['status'] == 'passed'
assert receipt['git_head'] == tools['git_head']
assert receipt['source_installation_mode'] == 'distribution'
assert receipt['source_checkout'] == str(ROOT) and receipt['output'] == str(BASE)
source = f.read_json(BASE / 'source-tracked.json')
assert p.sha(BASE / 'source-tracked.json') == receipt['source_inventory_sha256']

# The selected controls use authored temporary boards and the shipped smoke
# fixture. They do not read default-tuning-native-001/code/pipeline.py.
names = set(tools['implementation_sha256'])
names.update(name.replace('.', '/') + '.py' for name in MODULES + WATCHED)
names.update({'autorouter/__init__.py', 'autorouter/config.py',
              'scripts/install_smoke.py', 'toolchain.lock.json'})
names.update(str(path.relative_to(ROOT)) for path in
             (ROOT / 'fixtures/smoke').rglob('*') if path.is_file())
pins = {name: source[name] for name in sorted(names)}
assert all(p.sha(ROOT / name) == p.sha(CLONE / name) == pin
           for name, pin in pins.items())
authored = sum(sum(isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
                   and method.name.startswith('test_') for method in node.body)
               for module in MODULES
               for node in ast.parse((ROOT / (module.replace('.', '/') + '.py')).read_text()).body
               if isinstance(node, ast.ClassDef))
assert authored == 78

bootstrap = '''import sys,json,unittest,subprocess
from pathlib import Path
CLONE=Path(CLONE_LITERAL)
sys.path[:0]=[str(CLONE),str(CLONE/'tests')];sys.dont_write_bytecode=True
from autorouter import config as c
from importlib import import_module
assert c.ROOT==CLONE and Path(sys.prefix).resolve()==CLONE/'.venv'
assert Path(sys.executable)==CLONE/'.venv/bin/python' and sys.prefix!=sys.base_prefix
def forbidden(*a,**kw):raise AssertionError('installed software controls forbid Native/JVM/network/Git subprocess')
subprocess.run=forbidden;subprocess.Popen=forbidden
modules=MODULES_LITERAL
watched=[import_module(name) for name in WATCHED_LITERAL]
shipped={m.__name__:str(Path(m.__file__).resolve()) for m in watched}
assert all(Path(m.__file__).resolve()==CLONE/(m.__name__.replace('.','/')+'.py') for m in watched)
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(m) for m in modules)
planned=suite.countTestCases()
result=unittest.TextTestRunner(verbosity=2).run(suite)
population=dict(modules=modules,planned=planned,ran=result.testsRun,successful=result.wasSuccessful(),skipped=len(result.skipped),shipped_modules=shipped)
Path('population.json').write_text(json.dumps(population,indent=2)+'\\n')
raise SystemExit(0 if result.wasSuccessful() and planned==result.testsRun==78 and not result.skipped else 2)
'''.replace('CLONE_LITERAL', repr(str(CLONE))).replace('MODULES_LITERAL', repr(MODULES)).replace('WATCHED_LITERAL', repr(WATCHED))

plan = dict(schema=1, kind='installation036-targeted-preparation-v1',
            status='frozen_for_lead_execution', git_head=tools['git_head'], tools=tools,
            installation_receipt_sha256=p.sha(receipt_path),
            source_inventory_sha256=receipt['source_inventory_sha256'],
            source_sha256=pins,
            controller_sha256={name: p.sha(ROOT / name) for name in CONTROLLERS},
            target_modules=MODULES, new_shipped_modules=WATCHED,
            expected_target_method_count=78,
            expected_target_method_count_basis='Static authored method census only; not a test execution or pass.',
            target_bootstrap=bootstrap, historical_test_supplement=None,
            limits=dict(targeted_whole_wall_full_cpu_seconds=92,
                        worker_timeout_seconds=90, publication_allowance_seconds=2,
                        scratch_bytes=16*1024**2, group_rss_bytes=1024**3,
                        log_bytes=256*1024),
            scope='Current installed chain proposal, strategy and shared paired software controls; own fresh incumbents/equal allocation/cancellation/publication guards. No historical fixture supplement, Native/JVM/network execution, full installed suite, routing gain or fresh OS claim.')
OUT.mkdir()
p.save_json(OUT / 'protocol.json', plan)
print(json.dumps(dict(prepared=True, git_head=plan['git_head'],
                      module_count=len(MODULES), authored_static_methods=authored,
                      tests_executed=False)))
