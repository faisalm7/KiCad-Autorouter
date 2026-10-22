"""Constructed private-child controls; no Native/engine/product qualification.

Only selected-runtime/tool identity and static source preflight are stubbed.
Real bounded inventories, source/code/preset pins, sealing and dispatch execute.
"""
import copy
import os
from dataclasses import replace
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from autorouter import _improve_context as child, config as c, floor_route as f
from autorouter import handoff as h, pipeline as p, placement_clearance as pc, preferences as pref, provenance as pv, sexpr as sx

ROOT = Path(__file__).resolve().parents[1]


class ImproveChildContextControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=ROOT / '.cache')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.runtime = self.base / 'runtime'; (self.runtime / 'autorouter').mkdir(parents=True)
        self.workspace = self.runtime / '.runs/gui-session083/jobs' / ('autorouter-gui-' + 'a'*32)
        self.workspace.mkdir(parents=True)
        self.parent = self.workspace / 'route'
        self.parent_job = p.Job(self.parent,90,protect_local_settings=True)
        self.owner = {}; h.capture_destination(self.owner, self.parent)
        self.source = self.base / 'source' / 'owned.kicad_pcb'; self.source.parent.mkdir()
        self.source.write_text('(kicad_pcb (version 20260206) (layers (0 "F.Cu" signal) (2 "B.Cu" signal)))')
        self.source.with_suffix('.kicad_pro').write_text('{}')
        self.source.with_suffix('.kicad_sch').write_text('(kicad_sch)')
        self.hashes = pc.inventory(self.source.parent)
        shutil.copytree(self.source.parent, self.parent / 'snapshot')
        (self.parent / 'pruning-preferences.json').write_bytes(pref.snapshot(None, {'profile':'tuned', 'seconds':90}))
        code = self.parent / 'code'; code.mkdir()
        pins = {}
        for name in ('pipeline.py', 'strategy.py', '_improve_context.py'):
            for folder in (code, self.runtime / 'autorouter'):shutil.copy2(ROOT / 'autorouter' / name, folder / name)
            pins['autorouter/' + name] = p.sha(code / name)
        self.tools = dict(kicad='10.0.7', native_improve_child_policy=child.POLICY,
            source_provenance=dict(kind=pv.KIND, native_version='10.0.7', manifest_sha256='1'*64),
            implementation_sha256=pins, files={'not-executed':'2'*64})
        for target in (patch.object(c, 'ROOT', self.runtime), patch.object(c, 'NATIVE_VERSION', '10.0.7'),
                patch.object(c, 'current_native_selection', return_value={'version':'10.0.7'}),
                patch.object(p, 'tool_manifest', side_effect=lambda: copy.deepcopy(self.tools)),
                patch.object(p, 'preflight', side_effect=lambda source, **kwargs:sx.read(source)),
                patch.object(p, 'netclass_policy', return_value=None),
                patch.object(p, 'check_schematic_class_support', return_value=None)):
            target.start(); self.addCleanup(target.stop)
        self.context = self.make()

    def make(self, **changes):
        values = dict(source=self.source, parent=self.parent, parent_owner=dict(self.owner), method_seconds=90, assigned_seconds=48,
            allocation=dict(elapsed_wall_seconds=1, elapsed_cpu_seconds=2),
            tools=copy.deepcopy(self.tools), source_hashes=copy.deepcopy(self.hashes))
        values.update(changes)
        return child._Context(**values)

    def authorize(self, context=None, **changes):
        values = dict(context=self.context if context is None else context, source=self.source,
            output=self.parent/'incumbent', seconds=48, keep=False, adapter='both', profile='tuned',
            scoring=None, guidance='native', extras=())
        values.update(changes); return child.authorize(**values)

    def budget(self):
        return child._Budget(self.context,self.parent_job,self.parent_job.child_cpu_started)

    def record(self):
        output = self.context.output; output.mkdir()
        shutil.copytree(self.parent/'code', output/'code')
        data = dict(schema=1, source=str(self.source), source_hashes=copy.deepcopy(self.hashes),
            tools=copy.deepcopy(self.tools), baseline=p.engine_baseline('tuned','both'), engine_profile='tuned',
            adapter='both', scope='whole_board_unlocked_routing', scoring_variant=None,
            budget_seconds=48, cpu_budget_seconds=48)
        child.bind(output,data,self.context)
        return data

    def test_exact_child_request_and_reserved_assignment(self):
        self.authorize()
        for changes in ({'method_seconds':True}, {'assigned_seconds':True}, {'assigned_seconds':49},
                {'allocation':{'elapsed_wall_seconds':1,'elapsed_cpu_seconds':-1}},
                {'allocation':{'elapsed_wall_seconds':1,'elapsed_cpu_seconds':2,'reserve':40}}):
            with self.subTest(changes=changes), self.assertRaises((p.Rejected, ValueError)):self.make(**changes)
        for name,value in (('seconds',49),('keep',True),('profile','standard'),('adapter','none'),
                ('scoring','via_default'),('guidance','board-floors-v1'),('extras',(False,)),
                ('source',self.source.with_name('other.kicad_pcb')),('output',self.parent/'other')):
            with self.subTest(name=name), self.assertRaises(p.Rejected):self.authorize(**{name:value})

    def test_exact_type_and_nested_seal(self):
        class Other(child._Context):pass
        with self.assertRaises(p.Rejected):child.require(Other(**{name:getattr(self.context,name) for name in
            ('source','parent','parent_owner','method_seconds','assigned_seconds','allocation','tools','source_hashes')}))
        with self.assertRaises(p.Rejected):child.require(self.context.record())
        self.context.allocation['elapsed_cpu_seconds']=3
        with self.assertRaises(p.Rejected):child.require(self.context)

    def test_each_parent_source_preset_code_and_runtime_mutation_refuses(self):
        files = (self.source.with_suffix('.kicad_pro'), self.parent/'snapshot'/self.source.name,
                 self.parent/'pruning-preferences.json', self.parent/'code'/'strategy.py')
        for target in files:
            raw = target.read_bytes(); target.write_bytes(raw+b'\n')
            with self.subTest(path=target), self.assertRaises((p.Rejected, ValueError)):child.require(self.context)
            target.write_bytes(raw)
        self.tools['files']['not-executed']='3'*64
        with self.assertRaises(p.Rejected):child.require(self.context)

    def test_context_requires_canonical_owned_parent_and_scope(self):
        alias=self.runtime/'.runs'/'alias';alias.symlink_to(self.parent, target_is_directory=True)
        with self.assertRaises((p.Rejected, ValueError)):self.make(parent=alias)
        with patch.object(p,'check_schematic_class_support',return_value={'required':True}):
            with self.assertRaises(p.Rejected):self.make()
        self.source.write_text('(kicad_pcb (version 20260206) (layers (0 "F.Cu" signal) (4 "In1.Cu" signal) (6 "In2.Cu" signal) (2 "B.Cu" signal)))')
        with self.assertRaises((p.Rejected, ValueError)):self.make(source_hashes=pc.inventory(self.source.parent))

    def test_actual_nested_gui_parent_uses_captured_owner_without_namespace_authority(self):
        self.assertEqual(self.parent, self.workspace/'route')
        self.assertNotEqual(self.parent.parent, self.runtime/'.runs')
        self.assertEqual(self.context._owner, self.owner)
        self.assertIsNot(self.context._owner, self.owner)
        self.authorize()
        self.assertTrue(child.check_record(self.context.output,self.record(),self.context))
        # A JSON-shaped owner or receipt-shaped context cannot mint authority.
        json_owner = dict(self.owner, destination=str(self.parent), directory_identity=list(self.owner['directory_identity']))
        with self.assertRaises(p.Rejected):self.make(parent_owner=json_owner)
        with self.assertRaises(p.Rejected):child.require(self.context.record())

    def test_wrong_inode_foreign_parent_owner_and_source_refuse(self):
        for owner in (None, {}, dict(self.owner, directory_identity=(0,0))):
            with self.subTest(owner=owner), self.assertRaises(p.Rejected):self.make(parent_owner=owner)
        foreign=self.workspace/'foreign-route';foreign.mkdir()
        with self.assertRaises(p.Rejected):self.make(parent=foreign)
        with self.assertRaises(p.Rejected):self.authorize(source=self.source.with_name('foreign.kicad_pcb'))
        foreign_uid=os.getuid()+1
        with patch.object(child.os,'getuid',return_value=foreign_uid):
            with self.assertRaises(p.Rejected):self.make()
        retained=self.workspace/'retained-route'
        self.parent.rename(retained);self.parent.mkdir()
        try:
            # An identical pathname cannot replace the captured directory.
            with self.assertRaises(p.Rejected):child.require(self.context)
            with self.assertRaises(p.Rejected):self.make()
        finally:
            self.parent.rmdir();retained.rename(self.parent)
        self.context.parent_owner['directory_identity']=(0,0)
        with self.assertRaises(p.Rejected):child.require(self.context)

    def test_caller_and_marker_required_without_reconstructing_authority(self):
        data=self.record(); self.assertTrue(child.check_record(self.context.output,data,self.context))
        with self.assertRaises(p.Rejected):child.check_record(self.context.output,data,None)
        for key,value in (('budget_seconds',49),('scoring_variant','via_low'),('adapter','none'),
                ('engine_fanout_override',False),('comparison_route',{})):
            wrong=copy.deepcopy(data);wrong[key]=value
            with self.subTest(key=key),self.assertRaises(p.Rejected):child.check_record(self.context.output,wrong,self.context)
        (self.context.output/child.SIDECAR).unlink()
        with self.assertRaises((p.Rejected, OSError)):child.check_record(self.context.output,data,self.context)
        data.pop('native_improve_child')
        # Combined deletion cannot turn tuned selected-7 evidence into ordinary admission.
        p.save_json(self.context.output/'result.json',data)
        with self.assertRaises(p.Rejected):p.check_result(self.context.output/'result.json')

    def test_equal_valued_owner_type_mutations_refuse(self):
        # Python equality alone considers True == 1 and int == float. Preserve
        # the exact typed captured witness, including after construction.
        for key,value in (('created',1), ('directory_identity',tuple(float(v) for v in self.owner['directory_identity']))):
            with self.subTest(key=key):
                before=self.context.parent_owner[key]
                self.context.parent_owner[key]=value
                try:
                    with self.assertRaises(p.Rejected):child.require(self.context)
                finally:
                    self.context.parent_owner[key]=before

    def test_route_dispatch_only_exact_context_passes_ordinary_capability_gate(self):
        class StopBeforeJob(Exception):pass
        budget=self.budget()
        with patch.object(p,'sha',return_value=c.JAR_SHA256), patch.object(p,'check_storage',side_effect=StopBeforeJob):
            with self.assertRaises(p.Rejected):p.route(self.source,self.context.output,48,False,'both','tuned')
            with self.assertRaises(p.Rejected):p.route(self.source,self.context.output,48,False,'both','tuned',_improve_context=self.context)
            with self.assertRaises(StopBeforeJob):p.route(self.source,self.context.output,48,False,'both','tuned',_improve_context=self.context,_improve_budget=budget)
            with self.assertRaises(p.Rejected):p.route(self.source,self.context.output,48,False,'both','tuned',_improve_context=self.context,_improve_budget=budget,comparison_context=object())
        # A method label alone cannot authorize the ordinary standard profile.
        with self.assertRaises(p.Rejected):p.require_native_scope(purpose='improve')

    def test_live_context_never_enters_ordinary_result_cache(self):
        path=self.context.output/'result.json'
        # Authored child metadata satisfies canonical-path intake only; the
        # full Native reader remains the explicit constructed seam below.
        p.save_json(path,self.record())
        with p.validation_readback_session(), patch.object(p,'_check_result_uncached',return_value={'constructed':True}) as raw:
            state=p._readback_session.get()
            self.assertIn(child,state['modules'])
            p.check_result(path,_improve_context=self.context)
            p.check_result(path,_improve_context=self.context)
            self.assertEqual(raw.call_count,2)
            self.assertIs(raw.call_args.kwargs['_improve_context'],self.context)
            self.assertEqual(state['entries'],{})
            with self.assertRaises(p.Rejected):p.check_result(path,_improve_context=self.context,comparison_context=object())

    def test_live_parent_budget_charges_preparation_and_reaped_cpu_once(self):
        budget=self.budget();job=self.parent_job
        with patch.object(child.time,'monotonic',return_value=job.started+4), \
                patch.object(child.time,'process_time',return_value=job.cpu_started+6), \
                patch.object(f,'child_cpu',return_value=budget.children_start+7):
            self.assertEqual(budget.remaining(),37)
            self.assertEqual(budget.remaining(work=False),77)
        # Long Context intake cannot renew the parent's absolute work window.
        worker=p.Job(self.context.output,48,protect_local_settings=True)
        budget.attach(worker)
        self.assertLessEqual(worker.deadline,job.deadline-40)
        with patch.object(child.time,'monotonic',return_value=job.started+51), \
                patch.object(child.time,'process_time',return_value=job.cpu_started+1), \
                patch.object(f,'child_cpu',return_value=budget.children_start), \
                patch.object(p,'run') as run:
            with self.assertRaises(p.Rejected):worker.step('never-launch',['never-execute'])
            with self.assertRaises(p.Rejected):worker.drc('never-drc',self.source)
            run.assert_not_called()
            # Work has expired; the parent still has its reserved return time.
            budget.attach(job)
            self.assertEqual(job.remaining(),39)

    def test_budget_cpu_exhaustion_clock_mutations_and_foreign_jobs_refuse(self):
        budget=self.budget();job=self.parent_job
        with patch.object(child.time,'process_time',return_value=job.cpu_started+51), \
                patch.object(f,'child_cpu',return_value=budget.children_start):
            self.assertLess(budget.remaining(),0)
            self.assertGreater(budget.remaining(work=False),0)
        for name,value in (('deadline',job.deadline+1),('started',job.started+1),('cpu_started',job.cpu_started+1)):
            before=getattr(job,name);setattr(job,name,value)
            try:
                with self.subTest(name=name),self.assertRaises(p.Rejected):budget.remaining()
            finally:setattr(job,name,before)
        with self.assertRaises(p.Rejected):child.require_budget(budget,replace(self.context))
        with self.assertRaises(p.Rejected):child.require_budget(budget.context.record(),self.context)
        foreign=p.Job(self.workspace/'foreign',30,protect_local_settings=True)
        with self.assertRaises(p.Rejected):budget.attach(foreign)
        for name in ('trial-0000','trial-0031'):
            trial=p.Job(self.parent/'trials'/name,12,protect_local_settings=True)
            self.assertIs(budget.attach(trial),trial)
        extra=p.Job(self.parent/'trials'/'trial-0032',12,protect_local_settings=True)
        with self.assertRaises(p.Rejected):budget.attach(extra)

    def test_preconstruction_child_cpu_cannot_be_rebased_at_budget_creation(self):
        original=self.budget().children_start;job=self.parent_job
        with patch.object(f,'child_cpu',return_value=original+70), \
                patch.object(child.time,'monotonic',return_value=job.started+10), \
                patch.object(child.time,'process_time',return_value=job.cpu_started+1):
            with self.assertRaises(p.Rejected):child._Budget(self.context,job,original+70)
            retained=child._Budget(self.context,job,original)
            self.assertLess(retained.remaining(),0)
            self.assertEqual(retained.remaining(work=False),19)

    def test_central_reader_final_context_then_metadata_and_no_early_acceptance(self):
        # Extract the actual final block, stubbing only the large Native replay
        # already preceding it. A late tool/context metadata fault must refuse.
        import ast
        tree=ast.parse((ROOT/'autorouter/pipeline.py').read_text())
        function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='_check_result_uncached')
        block=next(node for node in function.body if isinstance(node,ast.If) and isinstance(node.test,ast.Name) and node.test.id=='is_improve_child')
        code=compile(ast.fix_missing_locations(ast.Module(body=[block],type_ignores=[])),'<actual-child-final-fence>','exec')
        class MutatingContext:
            @staticmethod
            def check_record(*args):events.append('context');flags['changed']=True
        events=[];flags={'changed':False}
        def replay(*args):
            events.append('metadata')
            if flags['changed']:raise p.Rejected('constructed late PRL metadata fault')
        from types import SimpleNamespace
        data=b'fixed'; digest=__import__('hashlib').sha256(data).hexdigest()
        env=dict(is_improve_child=True,improve_child=MutatingContext,path=SimpleNamespace(parent=Path('/owned')),
            data={},_improve_context=object(),tree_hash=lambda path:{},improve_material={},
            hashlib=__import__('hashlib'),bounded_bytes=lambda path:data,receipt_digest=digest,
            Rejected=p.Rejected,check_experimental_local_settings=replay)
        with self.assertRaises(p.Rejected):exec(code,env)
        self.assertEqual(events,['context','metadata'])


if __name__ == '__main__':unittest.main()
