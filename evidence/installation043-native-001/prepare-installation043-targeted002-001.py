"""Freeze current installed explicit-context/import/field controls; preparation only."""
from pathlib import Path
import ast
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f

parser=argparse.ArgumentParser();parser.add_argument('--source-head',required=True);args=parser.parse_args()
BASE = ROOT / '.runs/installation-043'
CLONE = BASE / 'checkout'
OUT = ROOT / '.runs/installation043-missing-preparation-001'
MODULES = ['tests.test_engine_angle', 'tests.test_engine_angle_native_control', 'tests.test_engine_profiles', 'tests.test_padstack_policy', 'tests.test_preference_publication', 'tests.test_pruning_preferences_freshness', 'tests.test_selected_evidence', 'tests.test_result']
WATCHED = ['autorouter.pipeline', 'autorouter.engine_angle', 'autorouter.floor_route', 'autorouter.adapter', 'autorouter.netclass', 'autorouter.netclass_native', 'autorouter.local_settings', 'autorouter.placement_clearance', 'experiments.free_angle_baseline_v1.fixture', 'experiments.free_angle_baseline_v1.controls', 'experiments.free_angle_baseline_v1.enclosure']
CONTROLLERS = ['.runs/prepare-installation043-targeted002-001.py',
               '.runs/run-installation043-targeted002-001.py']

receipt_path = BASE / 'result.json'
receipt = f.read_json(receipt_path)
tools = p.tool_manifest()
assert receipt['passed'] is True and receipt['status'] == 'passed'
assert receipt['git_head'] == tools['git_head'] == args.source_head
assert receipt['source_installation_mode'] == 'distribution'
assert receipt['source_checkout'] == str(ROOT) and receipt['output'] == str(BASE)
source = f.read_json(BASE / 'source-tracked.json')
assert p.sha(BASE / 'source-tracked.json') == receipt['source_inventory_sha256']
from scripts import install_smoke as install
listing=(BASE/'03-source-files.log').read_text()
assert install.tracked_inventory(ROOT,listing)==source
selected=install.distribution_listing(listing)
assert install.tracked_inventory(CLONE,selected)=={n:source[n] for n in selected.split('\0') if n}

# Fixed shipped authored controls; one exact current-engine provenance method.
# No historical omitted-evidence supplement.
names = set(tools['implementation_sha256'])
names.update(name.replace('.', '/') + '.py' for name in MODULES + WATCHED)
names.update({'autorouter/__init__.py', 'autorouter/config.py',
              'scripts/install_smoke.py', 'scripts/backup.py', 'toolchain.lock.json', 'experiments/hfe_original_native_v1/driver.py',
              'tests/test_result.py', 'tests/normal_prl_fixture.py', 'scripts/experiment_quality.py', 'scripts/experiment_portfolio.py', 'scripts/experiment_paired.py', 'experiments/placement_handoff_native_v1/driver.py', 'experiments/native_schematic_transport_v1/fixture.py', 'experiments/free_angle_baseline_v1/AngleObservation.java'})
names.update(str(path.relative_to(ROOT)) for path in
             (ROOT / 'fixtures/smoke').rglob('*') if path.is_file())
pins = {name: source[name] for name in sorted(names)}
assert all(p.sha(ROOT / name) == p.sha(CLONE / name) == pin
           for name, pin in pins.items())
SELECTORS = ['tests.test_engine_angle.EngineAngleControls.test_current_captured_producer_cannot_drop_budget_and_worker_markers', 'tests.test_engine_angle.EngineAngleControls.test_missing_tampered_binding_task_or_geometry_refuse', 'tests.test_engine_angle.EngineAngleControls.test_policy_downgrade_and_aliases_refuse', 'tests.test_engine_angle.EngineAngleControls.test_prepare_preserves_canonical_task_and_refuses_overwrite', 'tests.test_engine_angle.EngineAngleControls.test_shared_normal_reader_requires_angle_budget_even_after_profile_downgrade', 'tests.test_padstack_policy.PolicyReceiptControls.test_handoff_rejects_before_creating_review_copy', 'tests.test_padstack_policy.PolicyReceiptControls.test_rehashed_unknown_warning_receipt_and_handoff_reject']
old=ROOT/'.runs/installation043-targeted-001'
prior=f.read_json(old/'result.json');assert prior['passed'] is False and prior['status']=='failed' and prior['population']['ran']==62
failure_material=f.evidence_inventory(old);prior_pin=p.sha(old/'result.json')
assert failure_material==prior['completed_evidence']
text=(old/'tests.log').read_text()
import re
failed_names=re.findall(r'(?m)^(?:ERROR|FAIL): \S+ \(([^)]+)\)$',text)
assert set(failed_names)==set(SELECTORS) and len(failed_names)==7
authored=7

bootstrap = '''import sys,json,unittest,subprocess,os
from pathlib import Path
CLONE=Path(CLONE_LITERAL)
sys.path[:0]=[str(CLONE),str(CLONE/'tests')];sys.dont_write_bytecode=True
from autorouter import config as c
from importlib import import_module
assert c.ROOT==CLONE and Path(sys.prefix).resolve()==CLONE/'.venv'
assert Path(sys.executable)==CLONE/'.venv/bin/python' and sys.prefix!=sys.base_prefix
def forbidden(*a,**kw):raise AssertionError('installed software controls forbid Native/JVM/network/Git subprocess')
real_run,real_popen=subprocess.run,subprocess.Popen
git_active=False;git_observations=[]
safe_git=['git','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null','rev-parse','HEAD']
def readonly_run(argv,*args,**kw):
 global git_active
 assert argv==['git','rev-parse','HEAD'] and not args and Path(kw.get('cwd',''))==CLONE
 assert set(kw)=={'cwd','capture_output','text','check'} and all(kw[k] is True for k in ('capture_output','text','check'))
 assert not git_active
 git_active=True
 try:
  observed=real_run(safe_git,**kw)
  assert observed.stdout.strip()==HEAD_LITERAL
  git_observations.append(dict(argv=safe_git,cwd=str(CLONE),head=observed.stdout.strip(),returncode=observed.returncode))
  return observed
 finally:git_active=False
def controlled_popen(argv,*args,**kw):
 assert git_active and argv==safe_git and not args and Path(kw.get('cwd',''))==CLONE
 return real_popen(argv,**kw)
subprocess.run=readonly_run;subprocess.Popen=controlled_popen
scratch=CLONE/'.local-backups'
assert not scratch.exists() and not scratch.is_symlink()
scratch.mkdir(mode=0o700)

os.environ.pop('HFE_CONTROLLER',None)
modules=MODULES_LITERAL
selectors=SELECTORS_LITERAL
watched=[import_module(name) for name in WATCHED_LITERAL]
shipped={m.__name__:str(Path(m.__file__).resolve()) for m in watched}
assert all(Path(m.__file__).resolve()==CLONE/(m.__name__.replace('.','/')+'.py') for m in watched)
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(m) for m in selectors)
planned=suite.countTestCases()
result=unittest.TextTestRunner(verbosity=2).run(suite)
assert all(Path(m.__file__).resolve().is_relative_to(CLONE) for name,m in tuple(sys.modules.items()) if name.split('.')[0] in {'autorouter','scripts','experiments','tests'} and getattr(m,'__file__',None))
population=dict(modules=modules,selectors=selectors,planned=planned,ran=result.testsRun,successful=result.wasSuccessful(),skipped=len(result.skipped),shipped_modules=shipped,read_only_git_observations=git_observations,scratch_parent_created=str(scratch))
Path('population.json').write_text(json.dumps(population,indent=2)+'\\n')
raise SystemExit(0 if result.wasSuccessful() and planned==result.testsRun==7 and not result.skipped else 2)
'''.replace('CLONE_LITERAL', repr(str(CLONE))).replace('HEAD_LITERAL',repr(tools['git_head'])).replace('MODULES_LITERAL', repr(MODULES)).replace('SELECTORS_LITERAL',repr(SELECTORS)).replace('WATCHED_LITERAL', repr(WATCHED))

plan = dict(schema=1, kind='installation043-missing-preparation-v1',
            status='frozen_for_lead_execution', git_head=tools['git_head'], tools=tools,
            installation_receipt_sha256=p.sha(receipt_path),
            source_inventory_sha256=receipt['source_inventory_sha256'],
            source_sha256=pins,
            controller_sha256={name: p.sha(ROOT / name) for name in CONTROLLERS},
            target_modules=MODULES, new_shipped_modules=WATCHED,
            expected_target_method_count=7,target_selectors=SELECTORS,
            expected_target_method_count_basis='Static authored method census only; not a test execution or pass.',
            target_bootstrap=bootstrap, historical_test_supplement=None,
            retained_failure=dict(receipt_sha256=prior_pin,material=failure_material,failed_selectors=SELECTORS,prior_attempts=62,prior_successful=55,whole_external_command_wall_seconds=63.36,whole_external_command_full_cpu_seconds=57.91,preparation_wall_seconds=4.51,preparation_full_cpu_seconds=2.54),
            limits=dict(targeted_whole_wall_full_cpu_seconds=92,
                        worker_timeout_seconds=90, publication_allowance_seconds=2,
                        scratch_bytes=16*1024**2, group_rss_bytes=1024**3,
                        log_bytes=256*1024),
            scope='Missing-only7 controls from exact immutable failed00162attempts/55successes. Create owned ignored installed scratch parent; allow only exact read-only installedGitHEAD via bothrun/Popen guarded whitelist. No Native/JVM/network/otherGit worker or source/mocks/rule changes. New7mustpass; combined69attempts/62unique successful, never one62passrun. Costs all retained stage-specifically;92per delivered software cohort, not cumulative target or routing claim. SameMac/noGUI/fullinstalledsuite/family/quality claim.')
OUT.mkdir()
p.save_json(OUT / 'protocol.json', plan)
print(json.dumps(dict(prepared=True, git_head=plan['git_head'],
                      module_count=len(MODULES), authored_static_methods=authored,
                      tests_executed=False)))
