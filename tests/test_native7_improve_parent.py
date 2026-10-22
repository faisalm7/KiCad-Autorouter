"""Constructed parent binding/budget controls, never Native qualification.

Reuse the owned child fixture. Native/tool identity and static source preflight
remain explicit stubs; shared inventories, source code, settings and Context are
real. No worker, public guard bypass or parent acceptance is asserted.
"""
import copy
import hashlib
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
from autorouter import _improve_context as child, config as c, floor_route as f
from autorouter import pipeline as p, preferences as pref, strategy as s
from tests import test_native7_improve_child_context as child_fixture


class Native7ParentControls(unittest.TestCase):
    setUp = child_fixture.ImproveChildContextControls.setUp
    make = child_fixture.ImproveChildContextControls.make
    record = child_fixture.ImproveChildContextControls.record

    def incumbent_with_basis(self,data):
        # Constructed binding only. Full child Native/DSN replay is explicitly
        # stubbed in this fixture; it cannot establish a real Default transform.
        inc=self.record();path=self.context.output/'default-targets.json'
        from autorouter.default_targets import POLICY
        p.save_json(path,dict(schema=1,policy=POLICY))
        inc.update(accepted=True,status='routing_accepted',steps=[],
            default_target_transport=dict(policy=POLICY,file=path.name,sha256=p.sha(path)))
        p.save_json(self.context.output/'result.json',inc)
        _,data['native7_default_target_basis']=s._native7_default_basis_material(self.parent)
        return inc

    def parent_data(self):
        effective={**pref.DEFAULTS,'seconds':90,'profile':'tuned'}
        path=self.parent/'pruning-preferences.json'
        data=dict(schema=1,strategy='native_validated_zone_net_pruning',proposal_policy='single',
            engine_profile='tuned',adapter='both',scope='whole_board_unlocked_routing',incumbent_baseline='B2_tuned',
            source=str(self.source),source_hashes=copy.deepcopy(self.hashes),tools=copy.deepcopy(self.tools),
            budget_seconds=90,cpu_budget_seconds=90,finalization_reserve_seconds=40,
            finalization_cpu_reserve_seconds=40,pruning_preferences_policy=s.PRUNING_PREFERENCES_POLICY,
            pruning_preferences=dict(file=path.name,sha256=p.sha(path),effective=effective),steps=[],trials=[])
        s._bind_native7_parent(self.parent,data,self.context)
        return data

    def test_support_helper_is_exact_and_does_not_create_workspace(self):
        effective={**pref.DEFAULTS,'seconds':90,'profile':'tuned'}
        self.assertEqual(s.native7_single_scope(self.source,effective),effective)
        for changes in ({'proposal_policy':'chains'},{'proposal_policy':'feedback'},
                {'proposal_policy':'adaptive'},{'incumbent_scoring':'via_default'},{'incumbent_policy':'strong'}):
            with self.subTest(changes=changes),self.assertRaises(p.Rejected):s.native7_single_scope(self.source,effective,**changes)
        for key,value in (('scope','partial_completion'),('adapter','none'),('profile','standard'),
                ('guidance','board-floors-v1'),('scoring_preference','via_low')):
            with self.subTest(key=key),self.assertRaises((p.Rejected,ValueError)):
                s.native7_single_scope(self.source,dict(effective,**{key:value}))
        self.assertFalse(self.context.output.exists())
        for classes in ([],[{'name':'Other'}],[{'name':'Default'},{'name':'Other'}],None):
            self.source.with_suffix('.kicad_pro').write_text(__import__('json').dumps({'net_settings':{'classes':classes}}))
            with self.subTest(classes=classes),self.assertRaises(p.Rejected):s.native7_single_scope(self.source,effective)

    def test_parent_reconstructs_definition_not_execution_budget(self):
        data=self.parent_data();ctx=s.native7_incumbent_context(self.parent,data)
        self.assertIs(type(ctx),child._Context)
        self.assertEqual(ctx._seal,self.context._seal)
        self.assertIsNot(ctx,self.context)
        self.assertFalse(hasattr(ctx,'parent_job'))
        self.assertEqual(ctx.parent,self.parent)
        with self.assertRaises((TypeError,p.Rejected)):child._Budget(ctx,data,0)

    def test_scope_requires_matching_saved_complete_project_before_output(self):
        effective={**pref.DEFAULTS,'seconds':90,'profile':'tuned'}
        schematic=self.source.with_suffix('.kicad_sch');retained=schematic.with_name('retained.kicad_sch')
        schematic.rename(retained)
        try:
            with self.assertRaises(p.Rejected):s.native7_single_scope(self.source,effective)
            with self.assertRaises(p.Rejected):s.prune(self.source,self.workspace/'no-output',90)
            self.assertFalse((self.workspace/'no-output').exists())
        finally:retained.rename(schematic)
        with self.assertRaises(p.Rejected):s.native7_single_scope(self.source.with_suffix('.txt'),effective)

    def test_parent_marker_policy_and_definition_deletion_cannot_downgrade(self):
        data=self.parent_data();path=self.parent/s.NATIVE7_PARENT_FILE
        for key,value in (('proposal_policy','feedback'),('single_selection_policy','other'),
                ('incumbent_assigned_seconds',49),('tools',{})):
            wrong=copy.deepcopy(data);wrong[key]=value
            with self.subTest(key=key),self.assertRaises((p.Rejected,KeyError,ValueError)):
                s.native7_incumbent_context(self.parent,wrong)
        raw=path.read_bytes();path.unlink();data.pop('native7_improve_parent')
        with self.assertRaises((p.Rejected,OSError)):s.native7_incumbent_context(self.parent,data)
        path.write_bytes(raw)

    def test_rebound_source_or_definition_does_not_rebase_parent(self):
        data=self.parent_data();path=self.parent/s.NATIVE7_PARENT_FILE
        contract=f.read_json(path);contract['context']['assigned_seconds']=49
        p.save_json(path,contract);data['native7_improve_parent']['sha256']=p.sha(path)
        with self.assertRaises(p.Rejected):s.native7_incumbent_context(self.parent,data)
        # Even coherent hashing cannot restore a changed original source.
        self.source.with_suffix('.kicad_pro').write_text('{"changed":true}')
        with self.assertRaises(p.Rejected):s.native7_incumbent_context(self.parent,data)

    def test_incumbent_helper_calls_exact_child_reader_and_never_parent(self):
        data=self.parent_data();inc=self.incumbent_with_basis(data)
        with patch.object(p,'check_result',return_value={'constructed':True}) as checker, patch.object(p,'check_engine_profile_record'):
            s.check_incumbent_scoring(self.parent,data)
        checker.assert_called_once()
        self.assertEqual(checker.call_args.args,(self.context.output/'result.json',))
        self.assertIs(type(checker.call_args.kwargs['_improve_context']),child._Context)
        self.assertEqual(checker.call_args.kwargs['_improve_context']._seal,self.context._seal)

    def test_default_basis_requires_exact_child_and_parent_lineage(self):
        data=self.parent_data();self.incumbent_with_basis(data)
        basis=s.native7_default_target_basis(self.parent,data)
        self.assertEqual(basis['policy'],s._native7_default_basis_material(self.parent)[0]['policy'])
        marker=data.pop('native7_default_target_basis')
        with self.assertRaises(p.Rejected):s.native7_default_target_basis(self.parent,data)
        data['native7_default_target_basis']=marker
        path=self.context.output/'default-targets.json';raw=path.read_bytes()
        path.write_bytes(raw+b'\n')
        with self.assertRaises(p.Rejected):s.native7_default_target_basis(self.parent,data)
        path.write_bytes(raw)
        receipt=self.context.output/'result.json';inc=f.read_json(receipt)
        inc.pop('default_target_transport');p.save_json(receipt,inc)
        with self.assertRaises(p.Rejected):s.native7_default_target_basis(self.parent,data)

    def test_final_guard_preserves_own_default_audit_and_last_all_root_metadata(self):
        data=self.parent_data();self.incumbent_with_basis(data);(self.parent/'trials').mkdir()
        trial=self.parent/'trials/trial-0000';trial.mkdir()
        record=dict(status='quality_rejected',accepted=False,steps=[])
        p.save_json(trial/'result.json',record)
        data['trials']=[dict(id=trial.name,receipt=str(trial/'result.json'),status=record['status'],accepted=False)]
        self.assertFalse((trial/'code').exists())
        events=[];flags={'late':False};extra=(self.workspace/'export-validation',{'steps':[]})
        pairs=[('constructed plot root','constructed binding','constructed process')]
        def material():events.append('material');flags['late']=True
        def metadata(packets,cli,*,pairs):
            events.append('last metadata')
            self.assertEqual([row[0] for row in packets],[self.parent,self.context.output,trial,extra[0]])
            self.assertEqual(len(pairs),1)
            if flags['late']:raise p.Rejected('constructed late metadata sentinel')
        def lineage(folder,*args):
            if folder==trial:raise p.Rejected('standalone trial code not part of parent census contract')
            events.append('root')
        from autorouter import local_settings as local
        with patch.object(p,'check_final_netclass_evidence') as audit, \
                patch.object(p,'check_experimental_local_settings',side_effect=lineage), \
                patch.object(local,'check_final_events',side_effect=metadata),self.assertRaisesRegex(p.Rejected,'late metadata sentinel'):
            s.check_native7_final(self.parent,data,additional=(extra,),pairs=pairs,material=material)
        self.assertTrue(audit.call_args.kwargs['default_target_policy'])
        self.assertEqual(audit.call_args.kwargs['default_target_basis']['policy'],data['native7_default_target_basis']['policy'])
        self.assertEqual(events,['root','root','root','material','last metadata'])

    def test_inherited_live_trial_deadline_ignores_historic_allocation_clock(self):
        parent=self.workspace/'new-route'
        job=p.Job(parent,90,protect_local_settings=True)
        job.started=100;job.deadline=190;job.cpu_started=1;job.child_cpu_started=2
        for name in ('code','snapshot'):shutil.copytree(self.parent/name,parent/name)
        shutil.copy2(self.parent/'pruning-preferences.json',parent/'pruning-preferences.json')
        ctx=self.make(parent=parent,parent_owner=dict(job._local_settings_owner))
        with patch.object(child.time,'monotonic',return_value=103),patch.object(child.time,'process_time',return_value=3),patch.object(f,'child_cpu',return_value=4):
            budget=child._Budget(ctx,job,2);budget.attach(job)
            trial=p.Job(parent/'trials/trial-0000',120,protect_local_settings=True);budget.attach(trial)
            self.assertEqual(trial.deadline,150)
            guard=s._single_trial_guard(trial,100,90)
            self.assertEqual(guard,dict(wall_deadline_elapsed_seconds=50,work_cpu_limit_seconds=50))
            # Full parent headroom differs from work headroom; JSON allocation
            # never resets the elapsed execution budget.
            self.assertEqual(budget.remaining(work=False)-budget.remaining(work=True),40)
            with patch.object(child.time,'monotonic',return_value=151):
                with self.assertRaises(p.Rejected):s._single_trial_guard(trial,100,90)

    def test_actual_finalization_body_allows_reserved_return_but_not_whole_shortfall(self):
        # Execute the actual pre-finalization body with controlled clocks. Native
        # validation is not executed; reaching its candidate path is the marker.
        import ast
        from types import SimpleNamespace
        source=Path(s.__file__).read_text()
        function=next(node for node in ast.parse(source).body if isinstance(node,ast.FunctionDef) and node.name=='prune')
        body=next(node.body for node in function.body if isinstance(node,ast.Try)
            and any(isinstance(item,ast.Assign) and any(isinstance(target,ast.Subscript)
                and isinstance(target.slice,ast.Constant) and target.slice.value=='finalization_started_elapsed_seconds'
                for target in item.targets) for item in node.body))
        start=next(index for index,node in enumerate(body) if isinstance(node,ast.Assign)
            and any(isinstance(target,ast.Subscript) and isinstance(target.slice,ast.Constant)
                and target.slice.value=='finalization_started_elapsed_seconds' for target in node.targets))
        end=next(index for index,node in enumerate(body[start:],start) if isinstance(node,ast.Assign)
            and any(isinstance(target,ast.Name) and target.id=='candidate' for target in node.targets))
        code=compile(ast.fix_missing_locations(ast.Module(body=body[start:end+1],type_ignores=[])),
            '<actual-improve-finalization-entry>','exec')
        for wall_remaining,cpu_remaining,passes in ((40,40,True),(12,12,True),(11.99,40,False),(40,11.99,False)):
            now=190-wall_remaining;budget=SimpleNamespace(remaining=lambda *,work:0 if work else min(wall_remaining,cpu_remaining))
            env=dict(native7=True,live_budget=budget,report={},started=100,deadline=190,seconds=90,
                cpu_used=lambda:90-cpu_remaining,output=self.parent,source=self.source,p=p,time=s.time,_remaining=s._remaining)
            with self.subTest(wall=wall_remaining,cpu=cpu_remaining),patch.object(s.time,'monotonic',return_value=now):
                self.assertEqual(budget.remaining(work=True),0)
                if passes:
                    exec(code,env)
                    self.assertEqual(env['candidate'],self.parent/'candidate'/self.source.name)
                else:
                    with self.assertRaises(p.Rejected):exec(code,env)
                    self.assertNotIn('candidate',env)

    def test_packets_are_bounded_and_keep_unqualified_trial_without_promoting_it(self):
        data=self.parent_data();inc=self.record()
        p.save_json(self.context.output/'result.json',inc)
        trials=self.parent/'trials';trials.mkdir()
        folder=trials/'trial-0000';folder.mkdir();path=folder/'result.json'
        failed=dict(id=folder.name,status='rejected',accepted=False,steps=[])
        p.save_json(path,failed)
        data['trials']=[dict(id=folder.name,receipt=str(path),status='rejected',accepted=False)]
        packets=s.native7_packets(self.parent,data)
        self.assertEqual([item[0] for item in packets],[self.parent,self.context.output,folder])
        self.assertIs(packets[0][1],data)
        self.assertIs(packets[-1][1]['accepted'],False)
        (trials/'trial-0001').mkdir()
        with self.assertRaises(p.Rejected):s.native7_packets(self.parent,data)

    def test_unsupported_parent_variant_refuses_before_workspace(self):
        output=self.workspace/'unsupported-parent'
        with self.assertRaises(p.Rejected):s.prune(self.source,output,90,proposal_policy='feedback')
        self.assertFalse(output.exists())


if __name__=='__main__':unittest.main()
