from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
HEAD='7e73c35a27e04986e879ae44f646c88366036ea8'
plan=f.read_json(R/'.runs/installation033-preparation-001/protocol.json');plan.update(kind='installation034-preparation-v1',git_head=HEAD,tools=p.tool_manifest())
assert plan['tools']['git_head']==HEAD
CLONE=R/'.runs/installation-034/checkout';modules=['tests.test_schematic_fields', 'tests.test_schematic_field_evidence', 'tests.test_native_edge', 'tests.test_native_edge_record', 'tests.test_literal_composite', 'tests.test_netclass', 'tests.test_netclass_native', 'tests.test_netclass_unused', 'tests.test_netclass_parent_policy', 'tests.test_netclass_parent_pipeline', 'tests.test_netclass_pipeline', 'tests.test_experiment_quality']
plan.update(target_modules=modules,expected_target_method_count=144)
plan['target_bootstrap']="import sys,json,unittest,subprocess\nfrom pathlib import Path\nCLONE=Path(CLONE_LITERAL)\nsys.path[:0]=[str(CLONE),str(CLONE/'tests')];sys.dont_write_bytecode=True\nfrom autorouter import native_edge as edge,schematic_field_evidence as fields,netclass,netclass_native,config as c\nfrom scripts import fetch_led_demo,experiment_quality\nassert c.ROOT==CLONE and Path(sys.prefix).resolve()==CLONE/'.venv'\ndef forbidden(*a,**kw):raise AssertionError('installed software controls forbid Native/JVM/network/Git subprocess')\nsubprocess.run=forbidden;subprocess.Popen=forbidden\nmodules=MODULES_LITERAL\nsuite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(m) for m in modules);planned=suite.countTestCases()\nwatched=(edge,fields,netclass,netclass_native,fetch_led_demo,experiment_quality)\nshipped={m.__name__:str(Path(m.__file__).resolve()) for m in watched}\nassert all(Path(m.__file__).resolve()==CLONE/(m.__name__.replace('.','/')+'.py') for m in watched)\nresult=unittest.TextTestRunner(verbosity=2).run(suite)\npopulation=dict(modules=modules,planned=planned,ran=result.testsRun,successful=result.wasSuccessful(),skipped=len(result.skipped),shipped_modules=shipped)\nPath('population.json').write_text(json.dumps(population,indent=2)+'\\n')\nraise SystemExit(0 if result.wasSuccessful() and planned==result.testsRun==COUNT_LITERAL and not result.skipped else 2)\n".replace('CLONE_LITERAL',repr(str(CLONE))).replace('MODULES_LITERAL',repr(modules)).replace('COUNT_LITERAL',str(plan['expected_target_method_count']))
names=set(plan['source_sha256'])|set(m.replace('.','/')+'.py' for m in modules)|{'scripts/experiment_quality.py','scripts/fetch_led_demo.py','experiments/netclass_parent_transport_v1/fixture.py','experiments/licensed_acquisition_v1/fetch.py'}
names.update(str(x.relative_to(R)) for x in (R/'tests/fixtures/board-floor').rglob('*') if x.is_file())
plan['source_sha256']={n:p.sha(R/n) for n in sorted(names)}
assert all(p.sha(CLONE/n)==pin for n,pin in plan['source_sha256'].items())
plan['controller_sha256']={n:p.sha(R/n) for n in ('.runs/run-installation-034.py','.runs/run-installation034-targeted-001.py')}
plan['new_shipped_modules']=['autorouter.native_edge','autorouter.schematic_field_evidence','autorouter.netclass','autorouter.netclass_native','scripts.fetch_led_demo','scripts.experiment_quality']
plan.update(historical_test_supplement=None,scope='Current field/edge/composite/netclass/parent/unused/quality source-selection controls; actual fixed distribution count read after run; no historical supplements/fullsuite/freshOS claim.')
out=R/'.runs/installation034-preparation-001';out.mkdir();p.save_json(out/'protocol.json',plan)
print(json.dumps({'prepared':True,'module_count':len(modules),'expected_authored_methods':plan['expected_target_method_count']}))
