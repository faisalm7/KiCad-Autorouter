"""Pure draft/proof admission controls; no Native, model or GUI qualification."""
import ast
import copy
import hashlib
import json
import os
import subprocess
import stat
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from experiments import placement_choice as choice
from tests.test_placement_review import review
from experiments.placement_native_proposal_v1 import contract


class DraftAdmission(unittest.TestCase):
    def setUp(self):
        self.review = review()
        self.review.edit(contract.SELECTED[0], '14.5', '10')
        self.draft = self.review.decision(acknowledged=True, accepted=True, current_witness={'hash':'fresh'})

    def test_exact_edited_draft_is_detached_and_never_authorized(self):
        source = review(); before = copy.deepcopy(source.moves)
        selected = choice.validate_draft(source, self.draft)
        self.assertEqual(selected.moves, self.draft['moves_nm'])
        self.assertEqual(choice.digest(selected.pose), self.draft['pose_sha256'])
        self.assertEqual(source.moves, before)
        self.assertTrue(selected.intent['native_validation_required_for_changed_pose'])
        for key in ('execution_authorized','routing_accepted','human_PCB_approval','warning_acknowledged'):
            self.assertIs(selected.intent[key],False)
        selected.moves[contract.SELECTED[0]][0] += 1
        self.assertNotEqual(selected.moves, self.draft['moves_nm'])

    def test_every_original_field_is_required_and_unknown_fields_refuse(self):
        for key in self.draft:
            mutated=copy.deepcopy(self.draft);del mutated[key]
            with self.subTest(field=key),self.assertRaises((ValueError,KeyError)):
                choice.validate_draft(review(),mutated)
        mutated=dict(self.draft,unexpected='extra')
        with self.assertRaises(ValueError):choice.validate_draft(review(),mutated)

    def test_digests_scope_authority_and_review_choice_cannot_be_forged(self):
        edits=[('choice','reject'),('choice','accept'),('witness_sha256','0'*64),('facts_sha256','0'*64),
               ('pose_sha256','0'*64),('execution_authorized',True),('routing_accepted',True),
               ('human_PCB_approval',True),('warning_acknowledged',True),('new_native_validation_performed',True),
               ('schema',True),('execution_authorized',0),('revision',True),('revision',0),('revision',257),
               ('matches_retained_native_pose',True),('native_validation_required_for_changed_pose',False)]
        for key,value in edits:
            changed=copy.deepcopy(self.draft);changed[key]=value
            with self.subTest(field=key,value=value),self.assertRaises(ValueError):choice.validate_draft(review(),changed)
        changed=copy.deepcopy(self.draft);changed['options']['region_nm'][0]+=1
        with self.assertRaises(ValueError):choice.validate_draft(review(),changed)

    def test_coordinate_changes_require_new_digest_and_constraints(self):
        changed=copy.deepcopy(self.draft);changed['moves_nm'][contract.SELECTED[0]][0]+=1
        with self.assertRaises(ValueError):choice.validate_draft(review(),changed)
        for value in (True,14.5,10**400,-10**400):
            changed=copy.deepcopy(self.draft);changed['moves_nm'][contract.SELECTED[0]][0]=value
            with self.subTest(value=str(value)),self.assertRaises(ValueError):choice.validate_draft(review(),changed)
        changed=copy.deepcopy(self.draft);changed['moves_nm']['unknown-footprint']=[1,2]
        with self.assertRaises(ValueError):choice.validate_draft(review(),changed)
        changed=copy.deepcopy(self.draft);changed['moves_nm'][contract.SELECTED[0]]=[7_000_000,10_000_000]
        with self.assertRaises(ValueError):choice.validate_draft(review(),changed)

    def test_duplicate_nonfinite_or_truncated_json_refuses(self):
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":Infinity}',b'{"x":1e999}',b'{'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):choice.json_bytes(raw)

    def test_bootstrap_binding_read_rejects_link_and_size(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();source=root/'binding.json';source.write_text('{"schema":1}')
            self.assertEqual(choice.read_binding(source),{'schema':1})
            link=root/'link.json';link.symlink_to(source)
            with self.assertRaises(ValueError):choice.read_binding(link)
            source.write_bytes(b' '*(2*1024**2+1))
            with self.assertRaises(ValueError):choice.read_binding(source)

    def test_qualify_flag_is_required_before_context_or_writes(self):
        args=[]
        for key in ('runtime','evidence','protocol','draft','draft-sha256','output'):args += ['--'+key,'unused']
        with patch('experiments.placement_native_proposal_v1.driver.context') as context:
            with self.assertRaisesRegex(ValueError,'explicit --qualify'):choice.main(args)
            context.assert_not_called()


class CompletedProcessAdmission(unittest.TestCase):
    def records(self):
        process=dict(status='success',exit_code=0,cleanup_complete=True,log_truncated=False,wall_seconds=10.,cpu_seconds=8.,
            resource_guards=dict(max_group_rss_bytes=choice.RSS,max_workdir_bytes=choice.DISK,os_enforced=False))
        outer=dict(schema=1,kind=choice.KIND,status='pending_candidate',placement_qualified=True,process=copy.deepcopy(process),
            **{key:False for key in choice.AUTHORITY},total_limit_seconds=120,publication_allowance_seconds=1,
            controller_exit_not_measured=True,complete_worker_exit_wall_seconds=12.,parent_plus_waited_child_cpu_seconds=10.)
        return process,outer,dict(placement_qualified=True,external_exit_required=True)

    def test_completed_bound_process_only_remains_pending(self):
        process,outer,data=self.records();choice.outer_proof(process,outer,data)
        self.assertTrue(outer['placement_qualified'])
        self.assertTrue(all(outer[key] is False for key in choice.AUTHORITY))

    def test_cancel_crash_timeout_truncation_or_cleanup_failure_refuses(self):
        for key,value in [('status','cancelled'),('status','timeout'),('exit_code',-9),('exit_code',False),
                          ('cleanup_complete',False),('log_truncated',True)]:
            process,outer,data=self.records();process[key]=value;outer['process']=copy.deepcopy(process)
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):choice.outer_proof(process,outer,data)

    def test_outer_and_actual_inner_limits_independently_checked(self):
        for field,value in [('complete_worker_exit_wall_seconds',119.01),('parent_plus_waited_child_cpu_seconds',119.01),
                            ('complete_worker_exit_wall_seconds',True),('parent_plus_waited_child_cpu_seconds',float('nan'))]:
            process,outer,data=self.records();outer[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):choice.outer_proof(process,outer,data)
        for field in ('wall_seconds','cpu_seconds'):
            process,outer,data=self.records();process[field]=110.01;outer['process']=copy.deepcopy(process)
            outer['complete_worker_exit_wall_seconds']=118.;outer['parent_plus_waited_child_cpu_seconds']=118.
            with self.subTest(field=field),self.assertRaises(ValueError):choice.outer_proof(process,outer,data)
        process,outer,data=self.records();process['resource_guards']['max_group_rss_bytes']+=1;outer['process']=copy.deepcopy(process)
        with self.assertRaises(ValueError):choice.outer_proof(process,outer,data)

    def test_no_success_flag_or_self_approval_shortcuts(self):
        for key in choice.AUTHORITY:
            process,outer,data=self.records();outer[key]=True
            with self.subTest(key=key),self.assertRaises(ValueError):choice.outer_proof(process,outer,data)
        process,outer,data=self.records();data['placement_qualified']=False
        with self.assertRaises(ValueError):choice.outer_proof(process,outer,data)


class FreshnessAndPublication(unittest.TestCase):
    def test_retained_binding_cannot_select_import_runtime(self):
        with patch.object(choice,'read_binding',return_value={'runtime':'/untrusted/runtime'}), patch.object(choice,'prepare') as prepare:
            with self.assertRaisesRegex(ValueError,'caller-trusted runtime'):
                choice.loaded(Path('/unused/output'),Path('/trusted/runtime'))
            prepare.assert_not_called()
        with self.assertRaises(TypeError):choice.check(Path('/unused/output'))

    def test_closed_worker_inventory_detects_real_mutation(self):
        from autorouter import placement_clearance as pc
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary).resolve();work=output/'work';work.mkdir()
            result=work/'result.json';result.write_text('{"accepted":false}')
            hashes=pc.inventory(work)
            choice.stable_work(output,hashes,pc)
            result.write_text('{"accepted":true}')
            with self.assertRaisesRegex(ValueError,'closed worker artifacts changed'):
                choice.stable_work(output,hashes,pc)

    def test_actual_material_mutation_during_tool_check_is_caught(self):
        from autorouter import placement_clearance as pc
        from autorouter import local_settings
        from experiments.placement_native_proposal_v1 import driver
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();source_dir=root/'source';source_dir.mkdir()
            source=source_dir/'board.kicad_pcb';source.write_text('original')
            draft=root/'draft.json';draft.write_text('{}')
            protocol=root/'protocol.json';protocol.write_text('{}')
            evidence=root/'evidence';evidence.mkdir();(evidence/'result.json').write_text('{}')
            sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
            binding=dict(runtime=str(root),draft=str(draft),protocol=str(protocol),evidence=str(evidence),source=str(source),
                draft_sha256=sha(draft),protocol_sha256=sha(protocol),source_hashes=pc.inventory(source_dir),
                bridge_code_sha256={'bridge':'original'},native_code_sha256={'worker':'original'},tools={})
            review=SimpleNamespace(witness={'artifact_hashes':pc.inventory(evidence)})
            context=(SimpleNamespace(PCBNEW=root/'native'),SimpleNamespace(sha=sha),SimpleNamespace(read_json=lambda path:{}),
                     SimpleNamespace(source_inventory=lambda path:pc.inventory(path.parent)),None,pc)
            def tool_read(*args):
                draft.write_text('{"changed":true}')
                return True
            with patch.object(driver,'context',return_value=context),patch.object(choice,'code_pins',return_value={'bridge':'original'}), \
                 patch.object(driver,'code_pins',return_value={'worker':'original'}),patch.object(driver,'source_manifest_unchanged',return_value=True), \
                 patch.object(driver,'runtime_unchanged',side_effect=tool_read),patch.object(local_settings,'check_current_metadata'):
                with self.assertRaisesRegex(ValueError,'draft/protocol changed'):choice.material(binding,review)

    def test_shared_publication_cancel_clears_pending_flag(self):
        # Exercise the real outer account closure with the existing publisher.
        from autorouter import floor_route as f
        tree=ast.parse(Path(choice.__file__).read_text())
        main=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='main')
        account=next(node for node in ast.walk(main) if isinstance(node,ast.FunctionDef) and node.name=='account')
        outer=dict(status='pending_candidate',placement_qualified=True,accepted=False,whole_project_drc_clean=False)
        namespace=dict(outer=outer,time=SimpleNamespace(monotonic=lambda:2.),ENTRY=0.,cpu=lambda:1.,PARENT_CPU=0.,CHILD_CPU=0.,remaining=lambda:100.)
        exec(compile(ast.Module(body=[account],type_ignores=[]),choice.__file__,'exec'),namespace)
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary).resolve()
            # Cancellation at final publication, after the first canonical write.
            def cancelled():raise KeyboardInterrupt()
            result=f.publish(output,outer,lambda:None,namespace['account'],lambda:100.,final_check=cancelled)
            self.assertEqual(result['status'],'cancelled');self.assertIs(result['placement_qualified'],False)
            saved=f.read_json(output/'result.json');self.assertIs(saved['placement_qualified'],False)
            self.assertEqual(saved['status'],'cancelled')
            self.assertEqual(len(list(output.glob('invalidated-result-*.json'))),1)


class ColdInstalledBootstrap(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('PLACEMENT_CHOICE_TEST_RUNTIME'), 'explicit installed runtime not supplied')
    def test_prepare_selects_trusted_config_before_contract_import(self):
        runtime=Path(os.environ['PLACEMENT_CHOICE_TEST_RUNTIME']).resolve()
        script="""
import json,sys
from pathlib import Path
from experiments import placement_choice
assert 'autorouter.config' not in sys.modules
runtime=Path(sys.argv[1])
missing=runtime/'__placement_choice_missing_draft_for_cold_test__'
assert not missing.exists()
try:
    placement_choice.prepare(runtime,runtime,runtime,missing,'0'*64)
except FileNotFoundError:
    pass
else:
    raise AssertionError('missing draft did not refuse')
from autorouter import config
print(json.dumps(dict(root=str(config.ROOT),native_version=config.NATIVE_VERSION,
                      config_file=config.__file__,Native_loaded='pcbnew' in sys.modules)))
"""
        env={key:value for key,value in os.environ.items() if key not in ('PYTHONPATH','PYTHONHOME')}
        result=subprocess.run([str(runtime/'.venv/bin/python'),'-B','-c',script,str(runtime)],
            cwd=choice.ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)
        observed=json.loads(result.stdout)
        self.assertEqual(observed['root'],str(runtime))
        self.assertEqual(observed['native_version'],'10.0.7')
        self.assertEqual(Path(observed['config_file']),runtime/'autorouter/config.py')
        self.assertIs(observed['Native_loaded'],False)


@unittest.skipUnless(hasattr(os,'chflags') and hasattr(stat,'UF_IMMUTABLE'),'Darwin file flags unavailable')
class LateNewWorkMetadata(unittest.TestCase):
    """Actual temporary PRL flags at callback/readback edges, never Native."""
    def setUp(self):
        from autorouter import placement_clearance as pc
        from autorouter.pipeline import Rejected
        self.Rejected=Rejected;self.pc=pc;self.temporary=tempfile.TemporaryDirectory()
        self.output=Path(self.temporary.name).resolve()/'.runs'/'choice';self.output.mkdir(parents=True)
        original=self.output/'original';original.mkdir();source=original/'board.kicad_pcb'
        prl=source.with_suffix('.kicad_prl');prl.write_text('{}')
        self.binding=dict(source=str(source),source_hashes={prl.name:hashlib.sha256(prl.read_bytes()).hexdigest()},runtime=str(self.output))
        for role in ('snapshot','candidate','refill-preimage','refill-native','final-drc-input'):
            folder=self.output/'work'/role;folder.mkdir(parents=True)
            (folder/prl.name).write_bytes(prl.read_bytes())
        self.target=self.output/'work/candidate'/prl.name
        self.binding_path=self.output/'binding.json';self.binding_path.write_text('{}')
        self.result=self.output/'work/result.json';self.result.write_text('{"placement_qualified":true}')
        self.sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
        self.work_hashes=pc.inventory(self.output/'work')
        choice.work_prl(self.output,self.binding)
    def tearDown(self):
        os.chflags(self.target,0,follow_symlinks=False)
        self.temporary.cleanup()
    def late_tool_read(self,*args):
        os.chflags(self.target,stat.UF_IMMUTABLE,follow_symlinks=False)
        self.assertEqual(self.pc.inventory(self.output/'work'),self.work_hashes)
    def callback(self,owner,name,namespace):
        tree=ast.parse(Path(choice.__file__).read_text())
        function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name==owner)
        callback=next(node for node in ast.walk(function) if isinstance(node,ast.FunctionDef) and node.name==name)
        exec(compile(ast.Module(body=[callback],type_ignores=[]),choice.__file__,'exec'),namespace)
        return namespace[name]
    def test_worker_publication_fresh_refuses_late_flags(self):
        namespace=dict(h=SimpleNamespace(owned_destination=Mock()),job=SimpleNamespace(_local_settings_owner={}),
            remaining=lambda:100.,p=SimpleNamespace(sha=self.sha),binding_path=self.binding_path,
            expected_binding_sha=self.sha(self.binding_path),need=choice.need,material=self.late_tool_read,
            binding=self.binding,review=None,data={'placement_qualified':True},work_prl=choice.work_prl,output=self.output)
        fresh=self.callback('worker','fresh',namespace)
        with self.assertRaisesRegex(self.Rejected,'flags differ'):fresh()
    def test_outer_publication_stable_refuses_late_flags(self):
        namespace=dict(h=SimpleNamespace(owned_destination=Mock()),owner={},p=SimpleNamespace(sha=self.sha),output=self.output,
            binding_sha=self.sha(self.binding_path),need=choice.need,material=self.late_tool_read,binding=self.binding,review=None,
            data={'placement_qualified':True},stable_work=choice.stable_work,work_hashes=self.work_hashes,pc=self.pc,
            result=self.result,outer={'child_receipt_sha256':self.sha(self.result)},equal=choice.equal,
            f=SimpleNamespace(read_json=lambda path:json.loads(Path(path).read_bytes())),work_prl=choice.work_prl)
        stable=self.callback('main','stable',namespace)
        with self.assertRaisesRegex(self.Rejected,'flags differ'):stable()
    def test_independent_readback_refuses_flags_after_last_material(self):
        from experiments.placement_native_proposal_v1 import driver
        data={'placement_qualified':True};process={}
        outer={'worker_artifact_hashes':self.work_hashes,'binding_sha256':self.sha(self.binding_path),
               'child_receipt_sha256':self.sha(self.result)}
        process.update(argv=['bound'],cwd=str(self.output))
        def read(path):
            if path==self.output/'result.json':return outer
            if path==self.output/'process.json':return process
            if path==self.result:return data
            raise AssertionError(path)
        context=(None,SimpleNamespace(sha=self.sha),SimpleNamespace(read_json=read),None,
                 SimpleNamespace(real_path=lambda path:path),self.pc)
        with patch.object(choice,'ROOT',self.output.parent.parent), \
             patch.object(choice,'loaded',return_value=(self.binding,None,None)),patch.object(driver,'context',return_value=context), \
             patch.object(choice,'outer_proof'),patch.object(choice,'proof',return_value={}), \
             patch.object(choice,'worker_argv',return_value=['bound']),patch.object(choice,'material',side_effect=self.late_tool_read):
            with self.assertRaisesRegex(self.Rejected,'flags differ'):
                choice.check(self.output,expected_runtime=self.output)


if __name__=='__main__':unittest.main()
