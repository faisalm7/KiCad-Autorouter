"""Tiny installation harness controls; these do not run installs or native jobs."""
import copy
import contextlib
import hashlib
import io
import shutil
import importlib.util
import json
import tempfile
from pathlib import Path
import unittest
from unittest import mock

HERE = Path(__file__).resolve()
ROOT = next(parent for parent in HERE.parents if (parent / 'autorouter').is_dir())
SCRIPT = HERE.parents[1] / 'scripts/install_smoke.py'
spec = importlib.util.spec_from_file_location('install_smoke_under_test', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class InstallSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.runs')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def report(self):
        return {'status': 'passed', 'passed': True, 'commands': []}

    def result(self):
        return m.read_json(self.root / 'result.json')

    def test_default_selection_preserves_legacy_native_command(self):
        row = m.qualification('native')
        self.assertEqual(row['fixture'], 'fixtures/smoke/smoke.kicad_pcb')
        self.assertEqual(row['argv'], ['--seconds', '120'])
        self.assertEqual(row['directory'], 'install-native-smoke')

    def test_placement_selection_is_explicit_fixed_and_one_fixture(self):
        row = m.qualification('placement-clearance-v1')
        self.assertEqual(row['fixture'], m.PLACEMENT_FIXTURE)
        self.assertEqual(row['argv'], ['--seconds', '60', '--adapter', 'both', '--profile', 'completion-only', '--guidance', 'placement-clearance-v1'])
        with self.assertRaises(ValueError): m.qualification('via_low')

    def test_bootstrap_enables_actual_temporary_directory_precondition(self):
        clone = self.root / 'checkout'; clone.mkdir()
        with self.assertRaises(FileNotFoundError): tempfile.TemporaryDirectory(dir=clone / '.runs')
        action = m.bootstrap_runs(clone)
        with tempfile.TemporaryDirectory(dir=clone / '.runs') as created:
            self.assertTrue(Path(created).is_dir())
        self.assertTrue(action['created'])

    def test_bootstrap_refuses_existing_path_without_mutation(self):
        clone = self.root / 'checkout'; clone.mkdir()
        m.bootstrap_runs(clone)
        marker = clone / '.runs/marker'; marker.write_text('preserve')
        with self.assertRaises(FileExistsError): m.bootstrap_runs(clone)
        self.assertEqual(marker.read_text(), 'preserve')

    def test_bootstrap_refuses_symlink_clone_or_scratch(self):
        clone = self.root / 'checkout'; clone.mkdir()
        alias = self.root / 'alias'; alias.symlink_to(clone, target_is_directory=True)
        with self.assertRaises(RuntimeError): m.bootstrap_runs(alias)
        target = self.root / 'other'; target.mkdir()
        (clone / '.runs').symlink_to(target, target_is_directory=True)
        with self.assertRaises(FileExistsError): m.bootstrap_runs(clone)
        self.assertFalse(list(target.iterdir()))

    def test_tracked_inventory_bounds_stream_read_before_hash(self):
        source = self.root / 'source'; source.mkdir()
        (source / 'a').write_bytes(b'ok')
        self.assertEqual(m.tracked_inventory(source, 'a\0'), {'a': m.hashlib.sha256(b'ok').hexdigest()})
        with mock.patch.object(m.pc, 'read_bytes', side_effect=ValueError('oversize')) as reader:
            with self.assertRaisesRegex(ValueError, 'oversize'): m.tracked_inventory(source, 'a\0')
            self.assertEqual(reader.call_args.args[1], m.SOURCE_MAX_BYTES)
        with self.assertRaises(RuntimeError): m.tracked_inventory(source, '../other\0')

    def test_source_inventory_cumulative_cap_still_rejects(self):
        source = self.root / 'source'; source.mkdir()
        (source / 'a').write_bytes(b'abc')
        (source / 'b').write_bytes(b'def')
        with mock.patch.object(m, 'SOURCE_MAX_BYTES', 5):
            with self.assertRaisesRegex(RuntimeError, 'byte ceiling exceeded: 6 > 5 bytes at b'):
                m.tracked_inventory(source, 'a\0b\0')
        with mock.patch.object(m, 'SOURCE_MAX_FILES', 1):
            with self.assertRaisesRegex(RuntimeError, 'file ceiling exceeded: 2 > 1 files at b'):
                m.tracked_inventory(source, 'a\0b\0')

    def test_source_capacity_is_bounded_without_changing_scratch_or_wall(self):
        self.assertEqual(m.SOURCE_MAX_BYTES, 384 * 1024**2)
        self.assertEqual(m.SOURCE_MAX_FILES, 22000)
        self.assertEqual(m.MAX_BYTES, 512 * 1024**2)
        self.assertEqual(m.TOTAL_SECONDS, 600.0)

    def test_source_capacity_exact_boundary_and_excess_before_read(self):
        source = self.root / 'source'; source.mkdir()
        (source / 'a').write_bytes(b'abc')
        (source / 'b').write_bytes(b'de')
        (source / 'empty').write_bytes(b'')
        with mock.patch.object(m, 'SOURCE_MAX_BYTES', 5), mock.patch.object(m, 'SOURCE_MAX_FILES', 3):
            self.assertEqual(len(m.tracked_inventory(source, 'a\0b\0empty\0')), 3)
        (source / 'b').write_bytes(b'def')
        with mock.patch.object(m, 'SOURCE_MAX_BYTES', 5), mock.patch.object(m.pc, 'read_bytes', wraps=m.pc.read_bytes) as reader:
            with self.assertRaisesRegex(RuntimeError, 'byte ceiling exceeded'):
                m.tracked_inventory(source, 'a\0b\0')
            self.assertEqual(reader.call_count, 1)
            self.assertEqual(reader.call_args.args, (source / 'a', 5))

    def test_capacity_errors_do_not_mask_unsafe_or_invalid_file(self):
        source = self.root / 'source'; source.mkdir()
        (source / 'real').write_bytes(b'abc')
        (source / 'link').symlink_to(source / 'real')
        (source / 'directory').mkdir()
        with mock.patch.object(m, 'SOURCE_MAX_BYTES', 0), mock.patch.object(m, 'SOURCE_MAX_FILES', 0):
            with self.assertRaisesRegex(RuntimeError, 'unsafe tracked path'):
                m.tracked_inventory(source, 'link\0')
            for name in ('directory', 'missing'):
                with self.subTest(name=name), self.assertRaisesRegex(RuntimeError, 'tracked file missing'):
                    m.tracked_inventory(source, name + '\0')

    def test_git_identity_supports_packed_branch_and_rejects_ambiguity(self):
        gitdir = self.root / '.git'; gitdir.mkdir()
        head = 'a' * 40
        (gitdir / 'HEAD').write_text('ref: refs/heads/rebuild/local-review\n')
        (gitdir / 'index').write_bytes(b'index witness')
        packed = gitdir / 'packed-refs'
        row = head + ' refs/heads/rebuild/local-review\n'
        packed.write_text('# pack-refs with: peeled fully-peeled sorted\n' + row)
        result = m.git_identity(self.root, head, 'rebuild/local-review')
        self.assertEqual(result['resolved_commit'], head)
        packed.write_text(row + row)
        with self.assertRaisesRegex(RuntimeError, 'ambiguous'): m.git_identity(self.root, head, 'rebuild/local-review')

    def test_git_identity_rejects_linked_metadata_and_parent_refs(self):
        gitdir = self.root / '.git'; gitdir.mkdir()
        head = 'a' * 40
        (gitdir / 'HEAD').write_text(head + '\n')
        target = self.root / 'index-target'; target.write_bytes(b'index')
        (gitdir / 'index').symlink_to(target)
        with self.assertRaises(m.p.Rejected): m.git_identity(self.root, head)
        with self.assertRaises(RuntimeError): m.git_identity(self.root, head, '../escape')

    def test_native_contract_pins_placement_values(self):
        selected = m.qualification('placement-clearance-v1')
        fixture = self.root / 'fixture.kicad_pcb'
        result = {'accepted': True, 'tools': {'git_head': 'head'}, 'source': str(fixture), 'schema': 3,
                  'input_policy': 'placement-clearance-v1', 'adapter': 'both', 'engine_profile': 'completion-only',
                  'scoring_variant': 'via_default', 'scope': 'whole_board_unlocked_routing', 'budget_seconds': 60.0,
                  'cpu_budget_seconds': 60.0, 'planning_parameters': m.pc.parameters()}
        m.verify_native_contract(result, selected, fixture, 'head')
        for key, value in [('schema', 2), ('adapter', 'none'), ('source', 'other'), ('scoring_variant', 'via_low'), ('cpu_budget_seconds', 120.0), ('planning_parameters', {'clearance_margin_nm': 0})]:
            changed = copy.deepcopy(result); changed[key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError): m.verify_native_contract(changed, selected, fixture, 'head')

    def test_publication_success_rechecks_twice(self):
        stable = mock.Mock(); account = mock.Mock()
        m.publish_result(self.root, self.report(), stable, account)
        self.assertTrue(self.result()['passed'])
        self.assertEqual(stable.call_count, 2)
        self.assertEqual(account.call_count, 2)

    def test_signal_after_positive_write_invalidates_success(self):
        def writer(path, report):
            m.p.save_json(path, report)
            if report['passed']: raise KeyboardInterrupt('interrupt after positive')
        m.publish_result(self.root, self.report(), lambda: None, lambda: None, writer)
        self.assertEqual(self.result()['status'], 'cancelled')
        self.assertFalse(self.result()['passed'])
        self.assertTrue(json.loads((self.root / 'result.json.invalidated-0').read_text())['passed'])

    def test_partial_interruption_preserves_partial_and_publishes_cancelled(self):
        def writer(path, report):
            if report['passed']:
                path.with_suffix('.json.partial').write_text('{"passed": true')
                raise KeyboardInterrupt('partial')
            m.p.save_json(path, report)
        m.publish_result(self.root, self.report(), lambda: None, lambda: None, writer)
        self.assertFalse(self.result()['passed'])
        self.assertTrue((self.root / 'result.json.partial.invalidated-0').exists())
        self.assertFalse((self.root / 'result.json.partial').exists())

    def test_postwrite_source_mutation_rejects_with_actual_files(self):
        source = self.root / 'source'; source.write_text('original')
        def stable():
            if source.read_text() != 'original': raise RuntimeError('stale source')
        def writer(path, report):
            m.p.save_json(path, report)
            if report['passed']: source.write_text('changed')
        m.publish_result(self.root, self.report(), stable, lambda: None, writer)
        self.assertFalse(self.result()['passed'])
        self.assertIn('stale source', self.result()['reason'])

    def test_receipt_mutation_during_final_checker_rejects(self):
        calls = []
        def stable():
            calls.append(1)
            if len(calls) == 2:
                m.p.save_json(self.root / 'result.json', {'status': 'passed', 'passed': True, 'forged': True})
        m.publish_result(self.root, self.report(), stable, lambda: None)
        self.assertFalse(self.result()['passed'])
        self.assertIn('changed during final', self.result()['reason'])

    def test_postwrite_budget_failure_invalidates_success(self):
        calls = []
        def account():
            calls.append(1)
            if len(calls) == 2: raise RuntimeError('wall budget exhausted')
        m.publish_result(self.root, self.report(), lambda: None, account)
        self.assertFalse(self.result()['passed'])
        self.assertIn('wall budget', self.result()['reason'])

    def test_failed_correction_leaves_no_canonical_success(self):
        def writer(path, report):
            if report['passed']:
                m.p.save_json(path, report)
                raise KeyboardInterrupt('after positive')
            path.with_suffix('.json.partial').write_text('failed correction')
            raise OSError('write denied')
        with self.assertRaises(OSError): m.publish_result(self.root, self.report(), lambda: None, lambda: None, writer)
        self.assertFalse((self.root / 'result.json').exists())
        self.assertFalse((self.root / 'result.json.partial').exists())
        self.assertTrue((self.root / 'result.json.invalidated-0').exists())

    def test_duplicate_nonfinite_or_boolean_changed_receipt_rejects(self):
        for malformed in ('{"passed":false,"passed":true}', '{"passed":true,"extra":NaN}', '{"passed":1,"status":"passed","commands":[]}'):
            with self.subTest(malformed=malformed):
                def writer(path, report):
                    if report['passed']: path.write_text(malformed)
                    else: m.p.save_json(path, report)
                m.publish_result(self.root, self.report(), lambda: None, lambda: None, writer)
                self.assertFalse(self.result()['passed'])

    def test_interrupted_interim_partial_retains_cancelled_status(self):
        (self.root / 'result.json.partial').write_text('{"passed":false')
        report = self.report(); report.update(status='cancelled', passed=False, reason='SIGINT')
        m.publish_result(self.root, report, lambda: None, lambda: None)
        self.assertEqual(self.result()['status'], 'cancelled')
        self.assertTrue((self.root / 'result.json.partial.invalidated-0').exists())

    def test_already_failed_result_never_calls_success_validator(self):
        stable = mock.Mock(side_effect=AssertionError('no success validation'))
        report = self.report(); report.update(status='failed', passed=False)
        m.publish_result(self.root, report, stable, lambda: None)
        self.assertFalse(self.result()['passed']); stable.assert_not_called()


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def mock_install_case(m, base, name):
 HEAD="a"*40;SCRIPT=Path(m.__file__)
 base=base/name;base.mkdir(parents=True);source=base/'source';source.mkdir();out=base/'output';clone=out/'checkout'
 selected=m.qualification('placement-clearance-v1');fixture_relative=Path(selected['fixture'])
 for rel,raw in {'README.md':b'original source',str(fixture_relative):b'owned synthetic board control',str(fixture_relative.with_suffix('.kicad_pro')):b'{}','scripts/install_smoke.py':SCRIPT.read_bytes()}.items():
  path=source/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
 (source/'.git/refs/heads').mkdir(parents=True);(source/'.git/HEAD').write_text('ref: refs/heads/review\n');(source/'.git/refs/heads/review').write_text(HEAD+'\n');(source/'.git/index').write_bytes(b'original source index')
 listing='\0'.join(['README.md',str(fixture_relative),str(fixture_relative.with_suffix('.kicad_pro')),'scripts/install_smoke.py'])+'\0'
 jar=source/'.tools/test.jar';jar.parent.mkdir();jar.write_bytes(b'synthetic JAR is never executed')
 native_tool=base/'native-tool';native_tool.write_bytes(b'synthetic native binary never executed')
 source_python=base/'source-python';source_python.write_bytes(b'synthetic calling interpreter never executed')
 native=clone/'.runs'/selected['directory'];calls=[];mutation={}
 def run(argv,*,cwd,log,**kwargs):
  assert argv[:len(m.NETWORK_DENIAL)]==m.NETWORK_DENIAL
  a=argv[len(m.NETWORK_DENIAL):];log=Path(log);calls.append(a);text=''
  if a[0]=='git':
   if 'clone' in a:
    clone.mkdir();(clone/'.git').mkdir();(clone/'.git/HEAD').write_text(HEAD+'\n');(clone/'.git/index').write_bytes(b'original clone index')
    for rel in listing.split('\0'):
     if rel:
      dst=clone/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/rel,dst)
   elif 'rev-parse' in a:
    repo=Path(a[a.index('-C')+1]);text=(repo/'.git/HEAD').read_text()
    if text.startswith('ref: '):text=(repo/'.git'/text.strip()[5:]).read_text()
   elif 'symbolic-ref' in a:text='review\n'
   elif 'ls-files' in a:text=listing
   elif 'status' in a:text=''
   elif 'checkout' in a:pass
   else:raise AssertionError('unexpected fake Git command '+repr(a))
  elif '-m' in a and a[a.index('-m')+1]=='venv':
   venv=Path(a[-1]);(venv/'bin').mkdir(parents=True);(venv/'bin/python').write_bytes(b'copied fake python');(venv/'pyvenv.cfg').write_text('fake virtual environment')
  elif '-c' in a:
   venv=clone/'.venv';text=json.dumps({'version':'3.11 mock','executable':str(venv/'bin/python'),'prefix':str(venv),'base_prefix':str(base/'base-python')})
  elif 'scripts/setup_engine.py' in a:pass
  elif 'doctor' in a:text=json.dumps({'ready':True})
  elif 'unittest' in a:
   assert (clone/'.runs').is_dir(), 'fresh clone bootstrap missing before tests'
  elif 'route' in a:
   native.mkdir();(native/'candidate.board').write_bytes(b'before final checks')
   result={'accepted':True,'status':'routing_accepted','tools':{'git_head':HEAD,'files':{str(native_tool):digest(native_tool),str(clone/'.tools/test.jar'):digest(clone/'.tools/test.jar')}},'source':str(clone/fixture_relative),'schema':3,'input_policy':selected['guidance'],'adapter':'both','engine_profile':'completion-only','scoring_variant':'via_default','scope':'whole_board_unlocked_routing','budget_seconds':60.0,'cpu_budget_seconds':60.0,'planning_parameters':m.pc.parameters(),'wall_seconds':8.0}
   (native/'result.json').write_text(json.dumps(result))
  elif 'check-result' in a:text=json.dumps({'current':True,'scope':'synthetic controlled command; not actual validation'})
  else:raise AssertionError('unexpected fake command '+repr(a))
  log.write_text(text)
  if log.name=='freshness-7.log' and name not in ('unchanged','native_receipt_capture'):
   targets={'native_candidate':native/'candidate.board','source_tracked':source/'README.md','clone_tracked':clone/'README.md','native_tool':native_tool,'venv_python':clone/'.venv/bin/python','source_python':source_python,'command_log':out/'00-source-status.log','source_head':source/'.git/refs/heads/review','clone_head':clone/'.git/HEAD','source_index':source/'.git/index','clone_index':clone/'.git/index'}
   target=targets[name];mutation.update(path=str(target),before_sha256=digest(target));target.write_bytes(target.read_bytes()+b'\nchanged during final owned Git probe\n');mutation['after_sha256']=digest(target)
  return {'argv':argv,'status':'success','exit_code':0,'log':str(log),'cpu_seconds':0.0,'monitor_cpu_seconds':0.0}
 original_read = m.read_json
 def read_hook(path):
  value = original_read(path)
  if name == 'native_receipt_capture' and Path(path) == native/'result.json' and not mutation:
   target=Path(path);mutation.update(path=str(target),before_sha256=digest(target))
   changed=copy.deepcopy(value);changed['wall_seconds']=1.0;target.write_text(json.dumps(changed))
   mutation['after_sha256']=digest(target)
  return value
 with mock.patch.object(m,'read_json',side_effect=read_hook),mock.patch.object(m.c,'ROOT',source),mock.patch.object(m.c,'JAR',jar),mock.patch.object(m.c,'JAR_SHA256',digest(jar)),mock.patch.object(m.p,'check_storage',return_value=0),mock.patch.object(m,'run',side_effect=run),mock.patch.object(m.platform,'system',return_value='Darwin'),mock.patch.object(m.sys,'version_info',(3,11)),mock.patch.object(m.sys,'executable',str(source_python)):
  code=m.install_test(out,'placement-clearance-v1')
 result=m.read_json(out/'result.json');return {'case':name,'exit_code':code,'canonical_passed':result['passed'],'status':result['status'],'reason':result.get('reason'),'mutation':mutation,'mock_command_count':len(calls),'expected_pass':name=='unchanged','expectation_satisfied':result['passed']==(name=='unchanged')}

class WholeInstallationFlowTests(unittest.TestCase):
    def test_late_final_git_mutations_are_rejected(self):
        # Every subprocess is mocked. Only tiny owned files are copied/mutated;
        # this exercises the real install_test sequencing, not native correctness.
        with tempfile.TemporaryDirectory(dir=ROOT / '.runs') as directory:
            for name in ('unchanged', 'native_candidate', 'source_tracked', 'clone_tracked',
                         'native_tool', 'venv_python', 'source_python', 'command_log',
                         'source_head', 'clone_head', 'source_index', 'clone_index', 'native_receipt_capture'):
                with self.subTest(case=name), contextlib.redirect_stdout(io.StringIO()):
                    result = mock_install_case(m, Path(directory), name)
                    self.assertEqual(result['canonical_passed'], name == 'unchanged', result)
                    self.assertEqual(result['exit_code'], 0 if name == 'unchanged' else 2, result)
                    if name != 'unchanged':
                        self.assertNotEqual(result['mutation']['before_sha256'], result['mutation']['after_sha256'])


class DistributionScopeTests(unittest.TestCase):
    def source_names(self):
        return ['autorouter/pipeline.py','scripts/install_smoke.py','LICENSE','toolchain.lock.json',
                'tests/test_arcdice_demo_fetch.py','docs/quickstart.md',m.PLACEMENT_FIXTURE,
                'evidence/nus-additive-publication-fix-002/producer.py',
                'evidence/nus-additive-publication-fix-002/producer.py.foreign',
                'evidence/unrelated-history/large.json']
    def test_distribution_retains_runtime_tests_and_required_controls(self):
        names=self.source_names();original='\0'.join(names)+'\0'
        selected=m.distribution_listing(original).split('\0')[:-1]
        self.assertEqual(selected,names[:-2])
        self.assertEqual(original,'\0'.join(names)+'\0')
    def test_duplicate_or_line_ambiguous_paths_reject_before_setup(self):
        names=self.source_names()
        for extra in (names[0],'file\nother','file\rother'):
            with self.subTest(extra=extra),self.assertRaisesRegex(RuntimeError,'ambiguous'):
                m.distribution_listing('\0'.join([*names,extra])+'\0')
    def test_required_runtime_cannot_be_omitted(self):
        names=self.source_names()
        for required in ('LICENSE','toolchain.lock.json','autorouter/pipeline.py','scripts/install_smoke.py'):
            with self.subTest(required=required),self.assertRaisesRegex(RuntimeError,'required'):
                m.distribution_listing('\0'.join(n for n in names if n!=required)+'\0')
    def test_unknown_installation_mode_creates_nothing(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.runs') as directory:
            out=Path(directory)/'not-created'
            with self.assertRaisesRegex(RuntimeError,'unknown'):m.install_test(out,source_mode='unexpected')
            self.assertFalse(out.exists())

if __name__ == '__main__': unittest.main()
