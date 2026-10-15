"""Private stock optimizer-disable controls; no Native/JVM qualification."""
import copy,os,signal,stat,sys,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p,floor_route as f,engine_angle as angle,adapter as dsn,sexpr as sx
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


class EnginePlanningClearanceControls(unittest.TestCase):
    scratch=EngineOptimizerControls.scratch
    publication_fixture=EngineOptimizerControls.publication_fixture
    publish_actual_stable=EngineOptimizerControls.publish_actual_stable

    def raw(self,*,edge=True):
        tree=dsn._parse_dsn(angle_fixture.RAW.decode());structure=sx.one(tree,'structure')
        sx.one(structure,'rule').extend([['clearance','200'],['clearance','50',['type','smd_smd']]])
        if edge:
            sx.one(structure,'boundary').append(['clearance_class','kicadedge'])
            structure.append(['rule',*[['clearance','500',['type',pair]] for pair in ('default_kicadedge','smd_kicadedge','kicadedge_kicadedge')]])
        sx.one(tree,'network').append(['class','kicad_default','SIGNAL',['circuit',['use_via','round']],['rule',['width','250'],['clearance','200']]])
        return dsn._dump_dsn(tree).encode()

    def data(self):
        budget=p.engine_profile_settings(angle.PROFILE,100,experimental_free_angle=True,fanout_enabled=False,experimental_fanout=True,optimizer_enabled=False,experimental_optimizer=True)
        return dict(engine_profile=angle.PROFILE,engine_budget=budget,engine_fanout_override=False,engine_optimizer_override=False,
            engine_planning_clearance_margin_nm=20000,adapter='both',scope='whole_board_unlocked_routing',baseline='B2_tuned_free_angle')

    def record(self):
        directory=self.scratch();raw=self.raw();(directory/'task.dsn').write_bytes(raw)
        data=self.data();data['engine_angle_binding']=angle.prepare(directory,clearance_margin_nm=20000)
        return directory,data,raw

    def optimizer_publication_fixture(self):
        case=EngineOptimizerControls.optimizer_publication_fixture(self)
        (case.run/'task.dsn').write_bytes(self.raw())
        (case.run/angle.RECORD).unlink();(case.run/angle.INPUT).unlink()
        case.data.update(engine_planning_clearance_margin_nm=20000,engine_angle_binding=angle.prepare(case.run,clearance_margin_nm=20000))
        case.save_receipt();return case

    def test_default_none_preserves_bytes_and_original_record(self):
        for raw in (angle_fixture.RAW,self.raw()):
            self.assertEqual(angle.transform(raw),angle.transform(raw,clearance_margin_nm=None))
            output,record=angle.transform(raw)
            self.assertNotIn('clearance_margin_nm',record);self.assertNotIn('planning_clearance',record)
            self.assertTrue(record['exact_only_structure_snap_angle_insert'])

    def test_exact_two_decimal_atoms_and_all_other_geometry_scopes_unchanged(self):
        for edge in (False,True):
            raw=self.raw(edge=edge);before=dsn._parse_dsn(raw.decode());output,record=angle.transform(raw,clearance_margin_nm=20000)
            after=dsn._parse_dsn(output.decode());targets=angle._clearance_targets(after)
            self.assertEqual([node[1] for _,node in targets],['220','220'])
            self.assertEqual(len(record['planning_clearance']['changes']),2)
            self.assertEqual(record['planning_clearance']['classification'],'B1_adapter_only')
            self.assertFalse(record['exact_only_structure_snap_angle_insert'])
            self.assertEqual(sx.one(sx.one(after,'library'),'image'),sx.one(sx.one(before,'library'),'image'))
            for (_,node),change in zip(targets,record['planning_clearance']['changes']):node[1]=change['before']
            sx.one(after,'structure').remove(['snap_angle','none']);self.assertEqual(after,before)

    def test_literal_type_and_value_refusal(self):
        for value in (True,False,20000.,'20000',0,19999,20001,[],{}):
            with self.subTest(value=value),self.assertRaises(p.Rejected):angle.transform(self.raw(),clearance_margin_nm=value)

    def test_missing_duplicate_unknown_rule_class_clearance_and_unit_scopes_refuse(self):
        for mode in ('no_generic','duplicate_generic','duplicate_class','foreign_class','class_mismatch','extra_class_child','unknown_rule','duplicate_edge','unknown_edge','nested_clearance','duplicate_unit','mm','nan','exponent'):
            tree=dsn._parse_dsn(self.raw().decode());structure=sx.one(tree,'structure');rules=sx.children(structure,'rule');network=sx.one(tree,'network');cls=sx.one(network,'class')
            if mode=='no_generic':structure.remove(rules[0])
            elif mode=='duplicate_generic':structure.append(copy.deepcopy(rules[0]))
            elif mode=='duplicate_class':network.append(copy.deepcopy(cls))
            elif mode=='foreign_class':cls[1]='foreign'
            elif mode=='class_mismatch':sx.one(sx.one(cls,'rule'),'clearance')[1]='201'
            elif mode=='extra_class_child':cls.append(['layer_rule','F.Cu'])
            elif mode=='unknown_rule':structure.append(['rule',['clearance','200']])
            elif mode=='duplicate_edge':structure.append(copy.deepcopy(rules[1]))
            elif mode=='unknown_edge':rules[1][1][2][1]='foreign'
            elif mode=='nested_clearance':sx.one(tree,'library').append(['clearance','1'])
            elif mode=='duplicate_unit':tree.append(['unit','um'])
            elif mode=='mm':sx.one(tree,'unit')[1]='mm'
            elif mode=='nan':rules[0][2][1]='NaN'
            else:rules[0][2][1]='2e2'
            with self.subTest(mode=mode),self.assertRaises(p.Rejected):angle.transform(dsn._dump_dsn(tree).encode(),clearance_margin_nm=20000)

    def test_exact_prepare_check_preserves_original_task(self):
        directory,data,raw=self.record();proof=angle.check(directory,data)
        self.assertEqual(proof['clearance_margin_nm'],20000);self.assertEqual((directory/'task.dsn').read_bytes(),raw)
        angle.check_scope(data,'native')

    def test_reciprocal_marker_type_and_proof_erasure_refuse(self):
        for mode in ('report_erased','proof_erased','both_erased','report_type','proof_type','extra_witness'):
            directory,data,raw=self.record();proof=f.read_json(directory/angle.RECORD)
            if mode in ('report_erased','both_erased'):data.pop('engine_planning_clearance_margin_nm')
            if mode in ('proof_erased','both_erased'):proof.pop('clearance_margin_nm');proof.pop('planning_clearance')
            if mode=='report_type':data['engine_planning_clearance_margin_nm']=20000.
            if mode=='proof_type':proof['clearance_margin_nm']=20000.
            if mode=='extra_witness':proof['planning_clearance']['changes'][0]['after']='221'
            p.save_json(directory/angle.RECORD,proof);data['engine_angle_binding']['sha256']=p.sha(directory/angle.RECORD)
            with self.subTest(mode=mode),self.assertRaises(p.Rejected):angle.check(directory,data)

    def test_task_engine_width_geometry_and_typed_scope_tampering_refuse(self):
        for mode in ('task','engine','typed'):
            directory,data,raw=self.record();path=directory/('task.dsn' if mode=='task' else angle.INPUT)
            tree=dsn._parse_dsn(path.read_text())
            if mode=='typed':sx.children(sx.one(tree,'structure'),'rule')[0][3][1]='70'
            else:sx.one(sx.children(sx.one(tree,'structure'),'rule')[0],'width')[1]='251'
            path.write_bytes(dsn._dump_dsn(tree).encode())
            with self.subTest(mode=mode),self.assertRaises(p.Rejected):angle.check(directory,data)

    def test_private_scope_refuses_before_job_and_readers_refuse_downgrade(self):
        for changes in (dict(_engine_clearance_margin_nm=20000.),dict(_engine_clearance_margin_nm=True),dict(_optimizer_enabled=None),dict(_fanout_enabled=None),dict(engine_profile='tuned'),dict(adapter='none'),dict(keep_existing=True),dict(settings_path='/missing'),dict(native_toolchain=object())):
            args=dict(engine_profile=angle.PROFILE,adapter='both',_fanout_enabled=False,_optimizer_enabled=False,_engine_clearance_margin_nm=20000);args.update(changes)
            with self.subTest(changes=changes),patch.object(p,'Job',side_effect=AssertionError('no output')),self.assertRaises(p.Rejected):p.route('/missing/owned.kicad_pcb','/missing/output',**args)
        directory,data,_=self.record()
        for changes in (dict(engine_optimizer_override=None),dict(engine_fanout_override=None)):
            with self.subTest(changes=changes),self.assertRaises(p.Rejected):angle.check(directory,{**data,**changes})
        p.save_json(directory/'result.json',{**data,'engine_profile':'tuned'})
        with self.assertRaises(p.Rejected):p._check_result_uncached(directory/'result.json')

    def test_scope_rejects_partial_preferences_strategy_and_alternate_native(self):
        good=self.data()
        for changes in (dict(scope='partial_completion'),dict(routing_preferences={}),dict(layer_binding={}),dict(strategy='native_validated_zone_net_pruning')):
            with self.subTest(changes=changes),self.assertRaises(p.Rejected):angle.check_scope({**good,**changes},'native')
        with self.assertRaises(p.Rejected):angle.check_scope(good,'native',object())

    def test_actual_production_stable_with_margin_preserves_current_prl(self):
        case=self.optimizer_publication_fixture();result,state=self.publish_actual_stable(case)
        self.assertTrue(result['accepted']);self.assertEqual(state,dict(readbacks=1,triggered=False))

    @unittest.skipUnless(sys.platform=='darwin' and hasattr(os,'chflags'),'actual Mac PRL flags required')
    def test_actual_production_stable_rejects_late_owned_prl_flags_with_margin(self):
        # Reuse the exact existing fault/callback/assertions and cleanup; only
        # this class's setup includes the declared planning margin.
        EngineOptimizerControls.test_actual_stable_late_flag_only_mutation_invalidates_optimizer_receipt(self)


if __name__=='__main__':unittest.main()
