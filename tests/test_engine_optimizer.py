"""Private stock optimizer-disable controls; no Native/JVM qualification."""
import copy,os,signal,stat,sys,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p,floor_route as f,engine_angle as angle
from tests import test_engine_fanout as fanout,test_engine_angle as angle_fixture


class EngineOptimizerControls(unittest.TestCase):
    scratch=fanout.EngineFanoutControls.scratch
    publication_fixture=fanout.EngineFanoutControls.publication_fixture
    publish_actual_stable=fanout.EngineFanoutControls.publish_actual_stable

    def settings(self,**changes):
        args=dict(scoring_variant='via_default',experimental_free_angle=True,
                  fanout_enabled=False,experimental_fanout=True,
                  optimizer_enabled=False,experimental_optimizer=True)
        args.update(changes)
        return p.engine_profile_settings(angle.PROFILE,100,**args)

    def record(self):
        directory,data=fanout.EngineFanoutControls.record(self)
        (directory/'task.dsn').write_bytes(angle_fixture.RAW)
        data.update(engine_profile=angle.PROFILE,baseline=p.engine_baseline(angle.PROFILE,'both'),
                    engine_optimizer_override=False,engine_angle_binding=angle.prepare(directory))
        budget=self.settings();budget.update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120)
        data['engine_budget']=budget
        process=data['steps'][0];process['argv']=p.engine_argv(directory,budget['argv'],profile=angle.PROFILE)
        p.save_json(directory/'engine-process.json',process)
        return directory,data

    def optimizer_publication_fixture(self):
        case=self.publication_fixture(angle.PROFILE,False)
        budget=p.engine_profile_settings(angle.PROFILE,119,scoring_variant='via_default',
            experimental_free_angle=True,fanout_enabled=False,experimental_fanout=True,
            optimizer_enabled=False,experimental_optimizer=True)
        budget.update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120)
        worker=next(row for row in case.data['steps'] if row.get('name')=='engine')
        worker['argv']=p.engine_argv(case.run,budget['argv'],profile=angle.PROFILE)
        p.save_json(case.run/'engine-process.json',worker)
        case.data.update(engine_optimizer_override=False,engine_budget=budget)
        case.save_receipt()
        return case

    def test_none_defaults_preserve_existing_settings_and_argv(self):
        for profile in ('standard','tuned','completion-only',angle.PROFILE):
            kw=dict(experimental_free_angle=profile==angle.PROFILE)
            before=p.engine_profile_settings(profile,120,**kw)
            self.assertEqual(before,p.engine_profile_settings(profile,120,optimizer_enabled=None,**kw))
            self.assertNotIn('optimizer_enabled',before)
            self.assertEqual(before['argv'].count('--router.optimizer.enabled=false'),int(profile=='completion-only'))
        self.assertEqual(p.engine_profile_settings('tuned',120)['assigned_job_timeout_seconds'],80)
        self.assertEqual(p.engine_profile_settings('tuned',120)['assigned_optimizer_timeout_seconds'],80)

    def test_only_one_extra_flag_and_marker_all_inactive_caps_unchanged(self):
        expected=self.settings(optimizer_enabled=None,experimental_optimizer=False)
        actual=self.settings();self.assertIs(actual.pop('optimizer_enabled'),False)
        self.assertEqual(actual['argv'].count('--router.optimizer.enabled=false'),1)
        actual['argv'].remove('--router.optimizer.enabled=false')
        self.assertEqual(actual,expected)
        self.assertEqual(actual['assigned_optimizer_timeout_seconds'],60)
        self.assertIn('--router.optimizer.timeout=00:01:00',actual['argv'])
        self.assertIn('--router.optimizer.max_passes=50',actual['argv'])

    def test_types_optin_and_settings_scope_refuse(self):
        for value in (True,0,1,'false',[],{}):
            with self.subTest(value=value),self.assertRaises(p.Rejected):self.settings(optimizer_enabled=value)
        for changes in (dict(experimental_optimizer=False),dict(experimental_optimizer=1),
                        dict(fanout_enabled=None),dict(strict_class_targets=True)):
            with self.subTest(changes=changes),self.assertRaises(p.Rejected):self.settings(**changes)
        for profile in ('standard','tuned','completion-only'):
            with self.subTest(profile=profile),self.assertRaises(p.Rejected):
                p.engine_profile_settings(profile,100,fanout_enabled=False,experimental_fanout=True,
                    optimizer_enabled=False,experimental_optimizer=True)

    def test_route_types_and_scope_refuse_before_job(self):
        cases=[dict(_optimizer_enabled=x) for x in (True,0,1,'false',[],{})]
        cases += [dict(_fanout_enabled=None),dict(engine_profile='tuned'),dict(keep_existing=True),
                  dict(adapter='none'),dict(guidance_policy='board-floors-v1'),dict(settings_path='/missing'),
                  dict(preference_overrides={}),dict(_preferences={}),dict(native_toolchain=object()),
                  dict(experimental_schematic_parity=True)]
        for changes in cases:
            args=dict(engine_profile=angle.PROFILE,adapter='both',_fanout_enabled=False,_optimizer_enabled=False)
            args.update(changes)
            with self.subTest(changes=changes),patch.object(p,'Job',side_effect=AssertionError('no output Job')),self.assertRaises(p.Rejected):
                p.route('/missing/owned.kicad_pcb','/missing/output',**args)

    def test_derived_class_width_strictness_remains_a_pre_job_refusal(self):
        directory=self.scratch();source=directory/'source';source.mkdir()
        board=source/'owned.kicad_pcb';board.write_text('(kicad_pcb)');board.with_suffix('.kicad_pro').write_text('{}')
        for policy,width in (({'mode':'qualified-class'},None),(None,{'min_track_width_mm':.25})):
            with self.subTest(policy=policy,width=width),patch.object(p,'preflight',return_value=[]),patch.object(p,'netclass_policy',return_value=policy),patch.object(p,'minimum_width_guard',return_value=width),patch.object(p,'Job',side_effect=AssertionError('no output Job')),self.assertRaisesRegex(p.Rejected,'derived non-strict'):
                p.route(board,directory/'output',engine_profile=angle.PROFILE,adapter='both',_fanout_enabled=False,_optimizer_enabled=False)
        self.assertFalse((directory/'output').exists())

    def test_reciprocal_marker_budget_exact_types_and_flags(self):
        directory,good=self.record();self.assertIs(p.check_engine_optimizer_override(good,input_policy='native'),False)
        for mode in ('marker','budget_key','budget','typed_marker','typed_budget','duplicate','conflict','strict','fanout'):
            data=copy.deepcopy(good)
            if mode=='marker':data.pop('engine_optimizer_override')
            elif mode=='budget_key':data['engine_budget'].pop('optimizer_enabled')
            elif mode=='budget':data.pop('engine_budget')
            elif mode=='typed_marker':data['engine_optimizer_override']=0
            elif mode=='typed_budget':data['engine_budget']['optimizer_enabled']=0
            elif mode=='duplicate':data['engine_budget']['argv'].append('--router.optimizer.enabled=false')
            elif mode=='conflict':data['engine_budget']['argv'].append('--router.optimizer.enabled=true')
            elif mode=='strict':data['engine_budget']['strict_class_targets']=True
            else:data.pop('engine_fanout_override');data['engine_budget'].pop('fanout_enabled')
            with self.subTest(mode=mode),self.assertRaises(p.Rejected):p.check_engine_optimizer_override(data,input_policy='native')

    def test_reader_scope_and_early_result_marker_refusals(self):
        directory,data=self.record()
        for changes in (dict(adapter='none'),dict(scope='partial_completion'),dict(scope='selected_nets'),
                        dict(strategy='native_validated_zone_net_pruning'),dict(layer_binding={}),
                        dict(routing_preferences={}),dict(engine_profile='tuned')):
            with self.subTest(changes=changes),self.assertRaises(p.Rejected):
                p.check_engine_optimizer_override({**data,**changes},input_policy='native')
        with self.assertRaises(p.Rejected):p.check_engine_optimizer_override(data,input_policy='board-floors-v1')
        with self.assertRaises(p.Rejected):p.check_engine_optimizer_override(data,input_policy='native',native_toolchain=object())
        path=self.scratch()/'result.json';p.save_json(path,dict(schema=1,engine_profile='tuned',engine_optimizer_override=False))
        with self.assertRaisesRegex(p.Rejected,'optimizer override marker/budget'):p._check_result_uncached(path)

    def test_exact_actual_journal_replay(self):
        directory,data=self.record();p.check_engine_profile_record(data,directory)

    def test_erased_override_cannot_hide_actual_or_asserted_disabled_flag(self):
        for erase_budget_flag in (False,True):
            directory,data=self.record();data.pop('engine_optimizer_override');data['engine_budget'].pop('optimizer_enabled')
            if erase_budget_flag:data['engine_budget']['argv'].remove('--router.optimizer.enabled=false')
            with self.subTest(erase_budget_flag=erase_budget_flag),self.assertRaises(p.Rejected):p.check_engine_profile_record(data,directory)

    def test_erasing_markers_budget_and_worker_cannot_fall_back_to_legacy(self):
        directory,data=self.record();code=directory/'code';code.mkdir()
        raw=(p.c.ROOT/'autorouter/pipeline.py').read_bytes();(code/'pipeline.py').write_bytes(raw)
        data['tools']=dict(implementation_sha256={'autorouter/pipeline.py':p.hashlib.sha256(raw).hexdigest()})
        data.pop('engine_optimizer_override');data.pop('engine_fanout_override');data.pop('engine_budget');data['steps']=[]
        (directory/'engine-process.json').unlink()
        with self.assertRaisesRegex(p.Rejected,'requires retained engine budget/journal'):p.check_normal_engine_provenance(directory,data)

    def test_missing_modified_actual_journal_or_declared_step_refuses(self):
        for mode in ('missing','argv','declared_step','inactive_cap'):
            directory,data=self.record();path=directory/'engine-process.json';worker=f.read_json(path)
            if mode=='missing':path.unlink()
            elif mode=='argv':worker['argv'].remove('--router.optimizer.enabled=false');p.save_json(path,worker)
            elif mode=='declared_step':data['steps'][0]['argv'].remove('--router.optimizer.enabled=false')
            else:data['engine_budget']['assigned_optimizer_timeout_seconds']=None
            with self.subTest(mode=mode),self.assertRaises((p.Rejected,FileNotFoundError)):p.check_engine_profile_record(data,directory)

    def test_actual_stable_shared_publication_accepts_unchanged_owned_prl(self):
        case=self.optimizer_publication_fixture();result,state=self.publish_actual_stable(case)
        self.assertEqual(state,dict(readbacks=1,triggered=False));self.assertTrue(result['accepted'])
        self.assertTrue(f.read_json(case.receipt)['accepted'])

    @unittest.skipUnless(sys.platform=='darwin' and hasattr(os,'chflags'),'actual Mac PRL flags required')
    def test_actual_stable_late_flag_only_mutation_invalidates_optimizer_receipt(self):
        case=self.optimizer_publication_fixture()
        target=case.run/'final-drc-input'/case.source.with_suffix('.kicad_prl').name
        raw=target.read_bytes();old_flags=target.stat().st_flags;before=f.evidence_inventory(case.run)
        self.assertEqual(old_flags,0)
        def change_flags():
            os.chflags(target,stat.UF_IMMUTABLE,follow_symlinks=False)
            self.assertTrue(target.stat().st_flags & stat.UF_IMMUTABLE)
            self.assertEqual(target.read_bytes(),raw);self.assertEqual(f.evidence_inventory(case.run),before)
        handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
        def cancel(signum,frame):raise KeyboardInterrupt('received signal '+str(signum))
        try:
            for sig in handlers:signal.signal(sig,cancel)
            result,state=self.publish_actual_stable(case,late=change_flags)
            if result.get('status')=='cancelled':raise KeyboardInterrupt('shared publisher cancelled')
            self.assertEqual(state,dict(readbacks=1,triggered=True));self.assertFalse(result['accepted'])
            self.assertEqual(result['status'],'invalidated');self.assertIn('flags',result['reason'])
            self.assertFalse(f.read_json(case.receipt)['accepted']);self.assertTrue(list(case.run.glob('invalidated-result-*')))
        finally:
            try:os.chflags(target,old_flags,follow_symlinks=False)
            finally:
                for sig,handler in handlers.items():signal.signal(sig,handler)
        self.assertEqual(target.stat().st_flags,old_flags)


if __name__=='__main__':unittest.main()
