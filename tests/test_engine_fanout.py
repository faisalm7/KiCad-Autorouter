"""Isolated fanout policy/software controls; never Native/engine qualification."""
import ast,copy,json,os,signal,stat,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p,floor_route as f,local_settings as ls,engine_angle as angle
from tests import test_result as receipt_fixture,test_normal_local_settings_policy as prl_fixture


class EngineFanoutControls(unittest.TestCase):
    def scratch(self):
        context=tempfile.TemporaryDirectory();self.addCleanup(context.cleanup)
        return Path(context.name).resolve()

    def record(self):
        directory=self.scratch();source=directory/'owned.kicad_pcb';source.write_text('(kicad_pcb)')
        source.with_suffix('.kicad_pro').write_text('{}')
        budget=p.engine_profile_settings('tuned',100,scoring_variant='via_default',fanout_enabled=False,experimental_fanout=True)
        budget.update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120)
        process=dict(name='engine',cwd=str(directory),argv=p.engine_argv(directory,budget['argv']),status='success',exit_code=0,cleanup_complete=True,wall_seconds=0,cpu_seconds=0,monitor_cpu_seconds=0)
        p.save_json(directory/'engine-process.json',process)
        data=dict(engine_fanout_override=False,engine_budget=budget,engine_profile='tuned',baseline='B2_tuned',adapter='both',scope='whole_board_unlocked_routing',scoring_variant='via_default',source=str(source),budget_seconds=120,cpu_budget_seconds=120,steps=[copy.deepcopy(process)])
        return directory,data

    def test_default_budget_and_profile_argv_stay_unchanged(self):
        for profile in ('standard','tuned','completion-only'):
            before=p.engine_profile_settings(profile,120)
            self.assertNotIn('fanout_enabled',before)
            self.assertNotIn('--router.fanout.enabled=false',before['argv'])
            self.assertEqual(before,p.engine_profile_settings(profile,120,fanout_enabled=None))
        self.assertEqual(p.engine_profile_settings('tuned',120)['assigned_job_timeout_seconds'],80)

    def test_only_one_flag_changes_and_strict_derivation_stays_false(self):
        for profile in ('tuned','tuned-free-angle'):
            kw=dict(experimental_free_angle=profile=='tuned-free-angle',scoring_variant='via_default')
            old=p.engine_profile_settings(profile,120,**kw)
            new=p.engine_profile_settings(profile,120,fanout_enabled=False,experimental_fanout=True,**kw)
            self.assertIs(new.pop('fanout_enabled'),False);self.assertFalse(new['strict_class_targets'])
            self.assertEqual(new['argv'].count('--router.fanout.enabled=false'),1)
            new['argv'].remove('--router.fanout.enabled=false');self.assertEqual(new,old)
            self.assertNotIn('--router.automatic_neckdown=false',new['argv']);self.assertNotIn('--router.neck_width_um=0',new['argv'])

    def test_types_true_strict_and_floor_without_optin_refuse(self):
        for value in (True,0,1,'false',[],{}):
            with self.subTest(value=value),self.assertRaises(p.Rejected):p.engine_profile_settings('tuned',120,fanout_enabled=value,experimental_fanout=True)
        for kw in ({},{'strict_class_targets':True,'experimental_fanout':True},{'experimental_fanout':1}):
            with self.subTest(kw=kw),self.assertRaises(p.Rejected):p.engine_profile_settings('tuned',120,fanout_enabled=False,**kw)
        for profile in ('standard','completion-only'):
            with self.subTest(profile=profile),self.assertRaises(p.Rejected):p.engine_profile_settings(profile,120,fanout_enabled=False,experimental_fanout=True)

    def test_non_native_preferences_partial_and_experimental_refuse_before_output(self):
        for change in (dict(_fanout_enabled=True),dict(_fanout_enabled=0),dict(adapter='none'),dict(keep_existing=True),dict(guidance_policy='board-floors-v1'),dict(guidance_policy='placement-clearance-v1'),dict(settings_path='/missing/preset'),dict(preference_overrides={}),dict(_preferences={}),dict(native_toolchain=object()),dict(experimental_schematic_parity=True),dict(engine_profile='standard')):
            args=dict(engine_profile='tuned',adapter='both',_fanout_enabled=False);args.update(change)
            with self.subTest(change=change),patch.object(p,'Job',side_effect=AssertionError('must not construct output')),self.assertRaisesRegex(p.Rejected,'fanout override'):
                p.route('/missing/owned.kicad_pcb','/missing/output',**args)

    def test_positive_width_or_class_policy_refuses_before_job(self):
        directory=self.scratch();source=directory/'source';source.mkdir();board=source/'owned.kicad_pcb';board.write_text('(kicad_pcb)');board.with_suffix('.kicad_pro').write_text('{}')
        for policy,width in (({'mode':'qualified-class'},None),(None,{'min_track_width_mm':.25})):
            with self.subTest(policy=policy,width=width),patch.object(p,'preflight',return_value=[]),patch.object(p,'netclass_policy',return_value=policy),patch.object(p,'minimum_width_guard',return_value=width),patch.object(p,'Job',side_effect=AssertionError('must not construct output')),self.assertRaisesRegex(p.Rejected,'derived non-strict'):
                p.route(board,directory/'output',engine_profile='tuned',adapter='both',_fanout_enabled=False)
        self.assertFalse((directory/'output').exists())

    def test_reciprocal_marker_budget_typed_and_duplicate_flag_refusals(self):
        directory,good=self.record();self.assertIs(p.check_engine_fanout_override(good,input_policy='native'),False)
        for mode in ('marker_missing','budget_key_missing','budget_missing','typed_marker','typed_budget','strict','duplicate_flag'):
            data=copy.deepcopy(good)
            if mode=='marker_missing':data.pop('engine_fanout_override')
            elif mode=='budget_key_missing':data['engine_budget'].pop('fanout_enabled')
            elif mode=='budget_missing':data.pop('engine_budget')
            elif mode=='typed_marker':data['engine_fanout_override']=0
            elif mode=='typed_budget':data['engine_budget']['fanout_enabled']=0
            elif mode=='strict':data['engine_budget']['strict_class_targets']=True
            else:data['engine_budget']['argv'].append('--router.fanout.enabled=false')
            with self.subTest(mode=mode),self.assertRaises(p.Rejected):p.check_engine_fanout_override(data,input_policy='native')

    def test_reader_scope_refuses_floors_strategy_layers_and_profile_downgrade(self):
        directory,data=self.record()
        for policy in ('board-floors-v1','placement-clearance-v1','placement-search-v1'):
            with self.subTest(policy=policy),self.assertRaises(p.Rejected):p.check_engine_fanout_override(data,input_policy=policy)
        for changes in (dict(adapter='none'),dict(scope='partial_completion'),dict(scope='selected_nets'),dict(strategy='native_validated_zone_net_pruning'),dict(layer_binding={}),dict(routing_preferences={}),dict(engine_profile='standard')):
            with self.subTest(changes=changes),self.assertRaises(p.Rejected):p.check_engine_fanout_override({**data,**changes},input_policy='native')
        with self.assertRaises(p.Rejected):p.check_engine_fanout_override(data,input_policy='native',native_toolchain=object())

    def test_shared_result_entry_rejects_missing_override_budget_before_dispatch(self):
        directory=self.scratch();path=directory/'result.json'
        p.save_json(path,dict(schema=1,engine_fanout_override=False,engine_profile='tuned'))
        with self.assertRaisesRegex(p.Rejected,'fanout override marker/budget'):p._check_result_uncached(path)

    def test_exact_settings_and_actual_journal_replay_succeeds(self):
        directory,data=self.record();p.check_engine_profile_record(data,directory)

    def test_erased_override_with_actual_or_asserted_flag_cannot_downgrade(self):
        for also_budget_argv in (False,True):
            directory,data=self.record();data.pop('engine_fanout_override');data['engine_budget'].pop('fanout_enabled')
            if also_budget_argv:data['engine_budget']['argv'].remove('--router.fanout.enabled=false')
            with self.subTest(also_budget_argv=also_budget_argv),self.assertRaises(p.Rejected):p.check_engine_profile_record(data,directory)

    def test_missing_mismatched_or_rewritten_journal_refuses(self):
        for mode in ('missing','argv','cwd','declared_step'):
            directory,data=self.record();path=directory/'engine-process.json';process=f.read_json(path)
            if mode=='missing':path.unlink()
            elif mode=='argv':process['argv'].remove('--router.fanout.enabled=false');p.save_json(path,process)
            elif mode=='cwd':process['cwd']=str(directory.parent);p.save_json(path,process)
            else:data['steps'][0]['argv'].remove('--router.fanout.enabled=false')
            with self.subTest(mode=mode),self.assertRaises((p.Rejected,FileNotFoundError)):p.check_engine_profile_record(data,directory)

    def test_erasing_budget_worker_and_override_still_requires_current_producer_budget(self):
        directory,data=self.record();code=directory/'code';code.mkdir();raw=(p.c.ROOT/'autorouter/pipeline.py').read_bytes();(code/'pipeline.py').write_bytes(raw)
        data['tools']=dict(implementation_sha256={'autorouter/pipeline.py':p.hashlib.sha256(raw).hexdigest()})
        data.pop('engine_fanout_override');data.pop('engine_budget');data['steps']=[];(directory/'engine-process.json').unlink()
        with self.assertRaisesRegex(p.Rejected,'requires retained engine budget/journal'):p.check_normal_engine_provenance(directory,data)

    def publication_fixture(self,profile,fanout):
        # Setup-only use of the existing complete synthetic transport/PRL
        # filesystem fixture. No tools run and no Native result is established.
        case=receipt_fixture.ResultFreshnessTests('runTest');case.setUp();self.addCleanup(case.doCleanups)
        prl_fixture.NormalPolicyReceiptControls._put_prl_in_fixture(case)
        rows=[row for row in case.data['steps'] if row.get('name')=='engine' and row.get('cwd')==str(case.run)]
        self.assertEqual(len(rows),1);self.assertEqual(f.read_json(case.run/'engine-process.json'),rows[0])
        self.assertEqual([rows[0][key] for key in ('wall_seconds','cpu_seconds','monitor_cpu_seconds')],[0,0,0])
        budget=p.engine_profile_settings(profile,119,scoring_variant='via_default',fanout_enabled=fanout,experimental_fanout=fanout is False,experimental_free_angle=profile==angle.PROFILE)
        budget.update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120)
        worker=copy.deepcopy(rows[0]);worker['argv']=p.engine_argv(case.run,budget['argv'],profile=profile)
        case.data['steps']=[worker if row is rows[0] else row for row in case.data['steps']]
        p.save_json(case.run/'engine-process.json',worker)
        case.data.update(engine_profile=profile,baseline=p.engine_baseline(profile,'both'),adapter='both',
                         scoring_variant='via_default',engine_budget=budget)
        if fanout is False:case.data['engine_fanout_override']=False
        if profile==angle.PROFILE:case.data['engine_angle_binding']=angle.prepare(case.run)
        case.save_receipt()
        return case

    def publish_actual_stable(self,case,*,late=None):
        # Compile the exact production closure, without adding/removing any AST
        # nodes. Its captured globals come from that imported pipeline module;
        # only expensive tool discovery and the explicit read seam are injected.
        # This is the same extraction pattern as pruning preference controls.
        source=p.c.ROOT/'autorouter/pipeline.py';raw=source.read_bytes()
        self.assertEqual(case.data['tools']['implementation_sha256']['autorouter/pipeline.py'],p.sha(source))
        self.assertEqual((case.run/'code/pipeline.py').read_bytes(),raw)
        producer=next(row for row in ast.parse(raw).body if isinstance(row,ast.FunctionDef) and row.name=='route')
        closures=[row for row in ast.walk(producer) if isinstance(row,ast.FunctionDef) and row.name=='stable']
        self.assertEqual(len(closures),1)
        state={'readbacks':0,'triggered':False};hash_tree=p.tree_hash
        def current_hash(path):
            value=hash_tree(path)
            if late is not None and state['readbacks'] and Path(path)==case.run/'snapshot' and not state['triggered']:
                late();state['triggered']=True
            return value
        def readback(path):
            self.assertEqual(Path(path),case.receipt)
            data=f.read_json(path)
            p.check_engine_fanout_override(data,input_policy='native')
            p.check_engine_profile_record(data,case.run)
            ls.check_normal_policy(case.run,data)
            state['readbacks']+=1
        env=dict(p.__dict__)
        env.update(report=case.data,output=case.run,source=case.source,before=hash_tree(case.source_dir),
                   completed=f.evidence_inventory(case.run),native_toolchain=None,_preferences=None,
                   _fanout_enabled=case.data.get('engine_fanout_override'),engine_profile=case.data['engine_profile'],
                   tool_manifest=lambda **kw:case.data['tools'],evidence_inventory=f.evidence_inventory,tree_hash=current_hash)
        exec(compile(ast.fix_missing_locations(ast.Module(body=closures,type_ignores=[])),str(source),'exec'),env)
        # Accounting is fixed to isolate late metadata freshness. The real
        # shared publisher and normal PRL-policy replay remain unchanged.
        result=f.publish(case.run,case.data,env['stable'],lambda:None,lambda:100,result_checker=readback)
        return result,state

    def test_actual_stable_and_shared_publisher_keep_unchanged_owned_prl_current_in_both_paths(self):
        for profile,fanout in (('tuned',False),(angle.PROFILE,None)):
            with self.subTest(profile=profile,fanout=fanout):
                case=self.publication_fixture(profile,fanout);result,state=self.publish_actual_stable(case)
                self.assertEqual(state,dict(readbacks=1,triggered=False))
                self.assertTrue(result['accepted']);self.assertTrue(f.read_json(case.receipt)['accepted'])
                self.assertFalse(list(case.run.glob('invalidated-result-*')))

    @unittest.skipUnless(sys.platform=='darwin' and hasattr(os,'chflags'),'actual Mac PRL flags required')
    def test_actual_final_stable_rejects_owned_prl_flag_only_mutation_after_readback_in_both_paths(self):
        for profile,fanout in (('tuned',False),(angle.PROFILE,None)):
            with self.subTest(profile=profile,fanout=fanout):
                case=self.publication_fixture(profile,fanout)
                target=case.run/'final-drc-input'/case.source.with_suffix('.kicad_prl').name
                raw=target.read_bytes();old_flags=target.stat().st_flags;before=f.evidence_inventory(case.run)
                self.assertEqual(old_flags,0)
                def change_flags():
                    os.chflags(target,stat.UF_IMMUTABLE,follow_symlinks=False)
                    self.assertTrue(target.stat().st_flags & stat.UF_IMMUTABLE)
                    self.assertEqual(target.read_bytes(),raw)
                    # Byte inventory is deliberately blind to this exact late fault.
                    self.assertEqual(f.evidence_inventory(case.run),before)
                previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
                def cancel(signum,frame):raise KeyboardInterrupt('received signal '+str(signum))
                try:
                    for sig in previous:signal.signal(sig,cancel)
                    result,state=self.publish_actual_stable(case,late=change_flags)
                    if result.get('status')=='cancelled':raise KeyboardInterrupt('shared publisher cancelled')
                    self.assertEqual(state,dict(readbacks=1,triggered=True))
                    self.assertFalse(result['accepted']);self.assertEqual(result['status'],'invalidated')
                    self.assertFalse(f.read_json(case.receipt)['accepted'])
                    self.assertIn('flags',result['reason']);self.assertTrue(list(case.run.glob('invalidated-result-*')))
                    self.assertEqual(target.read_bytes(),raw)
                finally:
                    # The fault is limited to one owned TemporaryDirectory PRL;
                    # restore flags even if a pre-fix publisher remains accepted.
                    try:os.chflags(target,old_flags,follow_symlinks=False)
                    finally:
                        for sig,handler in previous.items():signal.signal(sig,handler)
                self.assertEqual(target.stat().st_flags,old_flags)

    def test_late_journal_edit_invalidates_shared_guarded_publication(self):
        directory,data=self.record();data.update(accepted=False,passed=True,status='completed');save=p.save_json;triggered=[]
        def stable():p.check_engine_profile_record(data,directory)
        def write(path,value):
            save(path,value)
            if Path(path)==directory/'result.json' and not triggered:
                process=f.read_json(directory/'engine-process.json');process['argv'].remove('--router.fanout.enabled=false');save(directory/'engine-process.json',process);triggered.append(True)
        def account():
            if data['status']!='completed':data['passed']=False
        with patch.object(p,'save_json',side_effect=write):f.publish(directory,data,stable,account,lambda:100,final_check=stable)
        self.assertTrue(triggered);self.assertFalse(f.read_json(directory/'result.json')['passed']);self.assertTrue(list(directory.glob('invalidated-result-*')))


if __name__=='__main__':unittest.main()
