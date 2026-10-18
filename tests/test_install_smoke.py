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
        self.assertEqual(m.SOURCE_MAX_FILES, 23000)
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
    def test_unknown_installation_mode_creates_nothing(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.runs') as directory:
            out=Path(directory)/'not-created'
            with self.assertRaisesRegex(RuntimeError,'unknown'):m.install_test(out,source_mode='unexpected')
            self.assertFalse(out.exists())


class CuratedDistributionTests(unittest.TestCase):
    """Real tiny builder/files; every Git observation and child command is fake."""
    def case(self, base, *, version='10.0.7', mutation=None, material_fault=None):
        source=base/'source';source.mkdir();out=base/'output';runtime=out/'runtime';head='a'*40
        lock=json.loads((ROOT/'toolchain.lock.json').read_bytes())
        jar=source/m.pv.ENGINE_PATH;jar.parent.mkdir();jar.write_bytes(b'owned synthetic engine; never executed')
        lock['tools']['freerouting']=dict(path=m.pv.ENGINE_PATH,sha256=digest(jar),bytes=jar.stat().st_size)
        product={name:b'owned synthetic product' for name in m.pv.FIXED_FILES}
        product.update({'toolchain.lock.json':json.dumps(lock).encode(),'autorouter/__init__.py':b'',
                        'autorouter/provenance.py':b'# owned synthetic module; never imported\n'})
        material={name:b'owned fixture '+name.encode() for name in (*m.SMOKE_FILES,*m.INSTALL_CONTROL_FILES)}
        for name,raw in {**product,**material}.items():
            path=source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        if material_fault in ('symlink','hardlink','fifo'):
            target=source/m.SMOKE_FILES[0];target.unlink();other=base/'owned-target';other.write_bytes(material[m.SMOKE_FILES[0]])
            if material_fault=='symlink':target.symlink_to(other)
            elif material_fault=='hardlink':m.os.link(other,target)
            else:m.os.mkfifo(target)
        # This excluded path must never be opened, inventoried or fetched.
        excluded=source/'evidence/large-private-lead';excluded.parent.mkdir();excluded.symlink_to(base/'absent')
        native_tool=base/'native-tool';native_tool.write_bytes(b'owned tool; never executed')
        calls=[];git_calls=[];changed=[];objects={str(i+1).zfill(40):name for i,name in enumerate(material)}
        def git(root,*args,**kwargs):
            git_calls.append(args)
            if args[0]=='status':return b'M selected\n' if material_fault=='dirty' else b''
            if args[0]=='ls-tree':
                rows=[b'100644 blob '+oid.encode()+b'\t'+name.encode()+b'\0' for oid,name in objects.items()]
                if material_fault=='missing':rows.pop()
                elif material_fault=='duplicate':rows.append(rows[0])
                elif material_fault=='mode':rows[0]=rows[0].replace(b'100644',b'120000',1)
                elif material_fault=='escape':rows.append(b'100644 blob '+b'b'*40+b'\t../escape\0')
                return b''.join(rows)
            if args[:2]==('cat-file','blob'):return material[objects[args[2]]]
            raise AssertionError('unbounded/unexpected Git operation '+repr(args))
        implementation=lambda:{name:digest(runtime/name) for name in product if name.startswith('autorouter/')}
        def change():
            targets={'source':source/'LICENSE','runtime':runtime/'LICENSE','controller':source/m.INSTALL_CONTROL_FILES[0],
                     'fixture':out/'source-fixture/smoke.kicad_pcb','tool':native_tool,
                     'venv':runtime/'.venv/bin/python','native':runtime/'.runs/install-native-smoke/candidate.board'}
            target=targets[mutation];target.write_bytes(target.read_bytes()+b'changed');changed.append(target)
        def run(argv,*,cwd,log,**kwargs):
            self.assertEqual(argv[:len(m.NETWORK_DENIAL)],m.NETWORK_DENIAL)
            args=argv[len(m.NETWORK_DENIAL):];text='';raw=None
            if args[0]=='git':
                self.assertIn('core.fsmonitor=false',args);self.assertIn('core.hooksPath=/dev/null',args)
                raw=git(Path(args[args.index('-C')+1]),*args[args.index('core.hooksPath=/dev/null')+1:])
            else:calls.append(args)
            if raw is not None:pass
            elif '-m' in args and args[args.index('-m')+1]=='venv':
                venv=Path(args[-1]);(venv/'bin').mkdir(parents=True);(venv/'bin/python').write_bytes(b'copied owned interpreter')
                (venv/'pyvenv.cfg').write_bytes(b'owned venv config')
            elif '-c' in args:text=json.dumps(dict(prefix=str(runtime/'.venv'),base_prefix=str(base/'base-python')))
            elif 'doctor' in args:
                text=json.dumps(dict(ready=True,checks={'runtime_provenance':{'identity':m.pv.source_identity(runtime,implementation())}}))
            elif 'route' in args:
                folder=runtime/'.runs/install-native-smoke';folder.mkdir();(folder/'candidate.board').write_bytes(b'owned candidate')
                fixture=out/'source-fixture/smoke.kicad_pcb'
                (folder/'result.json').write_text(json.dumps(dict(accepted=True,status='routing_accepted',source=str(fixture),
                    tools=dict(git_head=head,source_provenance=m.pv.source_identity(runtime,implementation()),
                               files={str(native_tool):digest(native_tool),str(runtime/m.pv.ENGINE_PATH):digest(runtime/m.pv.ENGINE_PATH)}))))
            elif 'check-result' in args:
                text=json.dumps({'current':True})
                if mutation and mutation!='publication':change()
            else:raise AssertionError('unexpected child command '+repr(args))
            Path(log).write_bytes(raw if raw is not None else text.encode())
            return dict(argv=argv,status='success',exit_code=0,log=str(log),cpu_seconds=0,monitor_cpu_seconds=0,
                        cleanup_complete=True,log_truncated=False)
        writer=m.p.save_json
        def write(path,record):
            writer(path,record)
            if mutation=='publication' and record.get('passed') is True and not changed:
                target=runtime/'LICENSE';target.write_bytes(target.read_bytes()+b'changed after publication');changed.append(target)
        with contextlib.ExitStack() as stack:
            for item in (mock.patch.object(m.c,'ROOT',source),mock.patch.object(m.c,'JAR',jar),
                mock.patch.object(m.pv,'committed_snapshot',side_effect=lambda root:(head,m.pv.owned_snapshot(root))),
                mock.patch.object(m.pv,'git_head',return_value=head),mock.patch.object(m.pv,'_git',side_effect=git),
                mock.patch.object(m,'tracked_inventory',side_effect=AssertionError('whole archive inventory forbidden')),
                mock.patch.object(m.p,'check_storage') ,mock.patch.object(m,'run',side_effect=run),
                mock.patch.object(m.p,'save_json',side_effect=write),mock.patch.object(m.platform,'system',return_value='Darwin'),
                mock.patch.object(m.sys,'version_info',(3,11)),contextlib.redirect_stdout(io.StringIO())):
                stack.enter_context(item)
            code=m.install_test(out,source_mode='distribution',native_version=version)
            m.p.check_storage.assert_called_once_with(active_root=out)
        return code,m.read_json(out/'result.json'),calls,git_calls,runtime

    def test_curated_runtime_for_both_known_profiles_omits_archive_and_history(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.runs') as directory:
            for version in ('10.0.0','10.0.7'):
                base=Path(directory)/version;base.mkdir()
                code,record,calls,git_calls,runtime=self.case(base,version=version)
                self.assertEqual(code,0,record);self.assertTrue(record['passed'])
                self.assertEqual(record['native_version'],version)
                self.assertFalse((runtime/'.git').exists());self.assertFalse((runtime/'tests').exists())
                self.assertFalse((runtime/'fixtures').exists());self.assertIsNone(record['complete_source_tracked_files'])
                self.assertIn('Route/check smoke only',record['qualification'])
                self.assertTrue(any('doctor' in argv for argv in calls));self.assertTrue(any('route' in argv for argv in calls))
                self.assertFalse(any('unittest' in argv or 'scripts/setup_engine.py' in argv for argv in calls))
                self.assertTrue(all(args[0] in ('status','ls-tree','cat-file') for args in git_calls))
                self.assertIn('separate integration gate',record['installed_test_scope'])
                self.assertEqual(len(list((base/'output').glob('source-git-*.json'))),len(git_calls))
                self.assertTrue(all(not step['name'].startswith('source-git') for step in record['commands']))

    def test_selected_material_is_complete_committed_regular_and_unaliased(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.runs') as directory:
            for name in ('missing','duplicate','mode','escape','dirty','symlink','hardlink','fifo'):
                with self.subTest(material=name):
                    base=Path(directory)/name;base.mkdir();code,record,calls,_,runtime=self.case(base,material_fault=name)
                    self.assertEqual(code,2,record);self.assertFalse(record['passed'])
                    self.assertFalse(calls);self.assertFalse(runtime.exists())

    def test_real_file_mutations_invalidate_new_distribution(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.runs') as directory:
            for name in ('source','runtime','controller','fixture','tool','venv','native','publication'):
                with self.subTest(mutation=name):
                    base=Path(directory)/name;base.mkdir();code,record,_,_,_=self.case(base,mutation=name)
                    self.assertEqual(code,2,record);self.assertFalse(record['passed']);self.assertTrue(record.get('reason'))
                    if name=='publication':
                        self.assertTrue(list((base/'output').glob('result.json.invalidated-*')))
                        self.assertFalse(record['selected_source_unchanged']);self.assertFalse(record['installed_product_unchanged'])

    def test_unsupported_distribution_options_refuse_before_creating_output(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.runs') as directory:
            out=Path(directory)/'absent'
            for kwargs in (dict(source_mode='distribution',guidance='placement-clearance-v1'),
                dict(source_mode='full',native_version='10.0.7'),dict(source_mode='distribution',native_version=True),
                dict(source_mode='distribution',native_version='10.0.8')):
                with self.subTest(kwargs=kwargs),self.assertRaises(RuntimeError):m.install_test(out,**kwargs)
                self.assertFalse(out.exists())


class BoundedProvenanceGitTests(unittest.TestCase):
    def test_exact_binary_output_sandbox_remaining_budget_and_no_report_mutation(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.runs') as directory:
            out=Path(directory);payload=b'\xff\x00blob\r\n';original=m.pv._git
            def run(argv,**kwargs):
                self.assertEqual(argv[:len(m.NETWORK_DENIAL)],m.NETWORK_DENIAL)
                self.assertIn('core.fsmonitor=false',argv);self.assertIn('core.hooksPath=/dev/null',argv)
                self.assertEqual(kwargs['timeout'],.25)
                self.assertNotIn('GIT_CONFIG_PARAMETERS',kwargs['env']);self.assertNotIn('GIT_DIR',kwargs['env'])
                self.assertEqual(kwargs['max_workdir_bytes'],m.MAX_BYTES)
                Path(kwargs['log']).write_bytes(payload)
                return dict(status='success',exit_code=0,cleanup_complete=True,log_truncated=False)
            with mock.patch.object(m.time,'monotonic',return_value=m.TOTAL_SECONDS-.25),mock.patch.object(m,'run',side_effect=run):
                with m.bounded_provenance_git(out,0,{'GIT_CONFIG_PARAMETERS':'unsafe','GIT_DIR':'other','PATH':'/usr/bin:/bin'}):
                    self.assertEqual(m.pv._git(ROOT,'cat-file','blob','a'*40,limit=100),payload)
                    self.assertEqual(m.pv._git(ROOT,'ls-tree','-z','a'*40,limit=100),payload)
            self.assertIs(m.pv._git,original)
            self.assertEqual(len(list(out.glob('source-git-*.json'))),2)

    def test_expired_budget_does_not_start_git_and_restores_helper(self):
        original=m.pv._git
        with tempfile.TemporaryDirectory(dir=ROOT/'.runs') as directory:
            with mock.patch.object(m.time,'monotonic',return_value=m.TOTAL_SECONDS),mock.patch.object(m,'run') as run:
                with self.assertRaisesRegex(RuntimeError,'budget'),m.bounded_provenance_git(Path(directory),0,{}):m.pv._git(ROOT,'status')
                run.assert_not_called()
            self.assertIs(m.pv._git,original)

    def test_truncated_failed_incomplete_cancelled_and_oversize_git_refuse(self):
        original=m.pv._git
        faults=({'log_truncated':True},{'cleanup_complete':False},{'exit_code':1},
                {'status':'cancelled'},{'oversize':True},{'raise':True})
        with tempfile.TemporaryDirectory(dir=ROOT/'.runs') as directory:
            for index,fault in enumerate(faults):
                out=Path(directory)/str(index);out.mkdir()
                def run(argv,**kwargs):
                    if fault.get('raise'):raise RuntimeError('callback failed')
                    Path(kwargs['log']).write_bytes(b'oversize' if fault.get('oversize') else b'x')
                    return dict(status=fault.get('status','success'),exit_code=fault.get('exit_code',0),
                                cleanup_complete=fault.get('cleanup_complete',True),log_truncated=fault.get('log_truncated',False))
                with self.subTest(fault=fault),mock.patch.object(m,'run',side_effect=run):
                    with self.assertRaises(Exception),m.bounded_provenance_git(out,m.time.monotonic(),{}):m.pv._git(ROOT,'status',limit=1)
                    self.assertIs(m.pv._git,original)

if __name__ == '__main__': unittest.main()
