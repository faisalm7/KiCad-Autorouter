"""Original global-width policy controls; no Native/JVM routing proof."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p,engine_angle as angle,strategy as s,floor_route as f
from tests import test_engine_optimizer as opt,test_pruning_scoring as pruning


class GlobalWidthControls(unittest.TestCase):
    settings=opt.EngineOptimizerControls.settings

    def raw(self,**kw):
        return opt.EnginePlanningClearanceControls.raw(self,**kw).replace(b'(width 250)',b'(width 300)')

    def scratch(self):
        context=tempfile.TemporaryDirectory();self.addCleanup(context.cleanup)
        self.root=Path(context.name).resolve();child=self.root/'incumbent';child.mkdir();return child

    def project(self,board,minimum=.2):
        data={'board':{'design_settings':{'rules':{'min_track_width':minimum}}},
            'net_settings':{'classes':[{'name':'Default','track_width':.3,'clearance':.2}],
                'netclass_assignments':None,'netclass_patterns':[]}}
        p.save_json(board.with_suffix('.kicad_pro'),data);return data

    def budget(self,**changes):
        kw=dict(strict_class_targets=True,experimental_free_angle=True,fanout_enabled=False,
            experimental_fanout=True,optimizer_enabled=False,experimental_optimizer=True,
            global_width_policy=p.ENGINE_GLOBAL_WIDTH_POLICY,scoring_variant='via_default')
        kw.update(changes);return p.engine_profile_settings(angle.PROFILE,100,**kw)

    def scene(self):
        child,inc=opt.EngineOptimizerControls.record(self)
        self.project(Path(inc['source']))
        inc.update(engine_budget=self.budget(),engine_global_width_policy=p.ENGINE_GLOBAL_WIDTH_POLICY,
            minimum_width_guard=p.minimum_width_guard(inc['source'],'both'),engine_planning_clearance_margin_nm=20000)
        inc['engine_budget'].update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120)
        (child/'task.dsn').write_bytes(self.raw());(child/angle.RECORD).unlink();(child/angle.INPUT).unlink()
        inc['engine_angle_binding']=angle.prepare(child,clearance_margin_nm=20000)
        worker=inc['steps'][0];worker['argv']=p.engine_argv(child,inc['engine_budget']['argv'],profile=angle.PROFILE)
        p.save_json(child/'engine-process.json',worker);p.save_json(child/'result.json',inc)
        return child,inc

    def test_strict_flags_remain_exactly_once_and_default_none_unchanged(self):
        new=self.budget()
        self.assertIs(new['strict_class_targets'],True)
        for flag in ('--router.automatic_neckdown=false','--router.fanout.enabled=false','--router.neck_width_um=0'):
            self.assertEqual(new['argv'].count(flag),1)
        self.assertEqual(new['argv'].count('--router.optimizer.enabled=false'),1)
        for profile in ('standard','tuned','completion-only'):
            self.assertEqual(p.engine_profile_settings(profile,100),p.engine_profile_settings(profile,100,global_width_policy=None))
        for changed in (dict(strict_class_targets=False),dict(global_width_policy=True),dict(global_width_policy='other'),
                dict(fanout_enabled=None),dict(optimizer_enabled=None),dict(experimental_fanout=1),dict(experimental_optimizer=1)):
            with self.subTest(changed=changed),self.assertRaises(p.Rejected):self.budget(**changed)

    def test_source_global_minimum_single_Default_and_target_are_mandatory(self):
        child=self.scratch();board=child/'owned.kicad_pcb';board.write_text('(kicad_pcb)')
        good=self.project(board);raw=board.with_suffix('.kicad_pro').read_bytes()
        self.assertEqual(p.global_width_source_guard(board),p.minimum_width_guard(board,'both'))
        self.assertEqual(board.with_suffix('.kicad_pro').read_bytes(),raw)
        for mode in ('zero','negative','bool','missing_class','foreign_class','small_target','bool_target','patterns','assignments','classes'):
            data=copy.deepcopy(good);ns=data['net_settings']
            if mode=='zero':data['board']['design_settings']['rules']['min_track_width']=0
            elif mode=='negative':data['board']['design_settings']['rules']['min_track_width']=-1
            elif mode=='bool':data['board']['design_settings']['rules']['min_track_width']=True
            elif mode=='missing_class':ns.pop('classes')
            elif mode=='foreign_class':ns['classes'][0]['name']='arbitrary'
            elif mode=='small_target':ns['classes'][0]['track_width']=.1
            elif mode=='bool_target':ns['classes'][0]['track_width']=True
            elif mode=='patterns':ns['netclass_patterns']=[{'pattern':'*','netclass':'Default'}]
            elif mode=='assignments':ns['netclass_assignments']={'ROUTE':'Default'}
            else:ns['classes'].append(copy.deepcopy(ns['classes'][0]))
            p.save_json(board.with_suffix('.kicad_pro'),data)
            with self.subTest(mode=mode),self.assertRaises(p.Rejected):p.global_width_source_guard(board)

    def test_early_angle_and_full_engine_replay_keep_original_width_guard(self):
        child,data=self.scene();self.assertEqual(p.check_engine_global_width_policy(data),p.ENGINE_GLOBAL_WIDTH_POLICY)
        self.assertIs(p.check_engine_optimizer_override(data,input_policy='native'),False)
        p.check_engine_profile_record(data,child)
        self.assertEqual(p.check_minimum_width_record(data,child)['min_track_width_mm'],.2)

    def test_reciprocal_erasure_types_guard_and_neckdown_conflicts_refuse(self):
        child,good=self.scene()
        for mode in ('marker','budget_marker','both','typed','strict_false','guard','bool_min','fanout','duplicate','neckdown','neck_width','margin','nondefault'):
            data=copy.deepcopy(good)
            if mode=='marker':data.pop('engine_global_width_policy')
            elif mode=='budget_marker':data['engine_budget'].pop('global_width_policy')
            elif mode=='both':data.pop('engine_global_width_policy');data['engine_budget'].pop('global_width_policy')
            elif mode=='typed':data['engine_global_width_policy']=True
            elif mode=='strict_false':data['engine_budget']['strict_class_targets']=False
            elif mode=='guard':data.pop('minimum_width_guard')
            elif mode=='bool_min':data['minimum_width_guard']['min_track_width_mm']=True
            elif mode=='fanout':data['engine_fanout_override']=True
            elif mode=='duplicate':data['engine_budget']['argv'].append('--router.fanout.enabled=false')
            elif mode=='neckdown':data['engine_budget']['argv'].append('--router.automatic_neckdown=true')
            elif mode=='neck_width':data['engine_budget']['argv'].remove('--router.neck_width_um=0')
            elif mode=='margin':data['engine_planning_clearance_margin_nm']=20000.
            else:data['netclass_policy']={}
            with self.subTest(mode=mode),self.assertRaises(p.Rejected):p.check_engine_fanout_override(data,input_policy='native')

    def test_erased_policy_and_coherently_relabeled_budget_cannot_hide_actual_strict_worker(self):
        child,data=self.scene();data.pop('engine_global_width_policy');data['engine_budget'].pop('global_width_policy')
        data['engine_budget']['strict_class_targets']=False
        data['engine_budget']['argv']=[v for v in data['engine_budget']['argv'] if not v.startswith(('--router.automatic_neckdown','--router.neck_width_um'))]
        with self.assertRaisesRegex(p.Rejected,'width guard'):p.check_engine_profile_record(data,child)

    def test_narrower_legal_task_width_still_cannot_replace_original_Default_target(self):
        child,data=self.scene();original=(child/'task.dsn').read_bytes()
        angle.check_global_width_targets(child,data['source'])
        # .25 is above the original .2 minimum but differs from its .3 target.
        changed=original.replace(b'(width 300)',b'(width 250)');self.assertNotEqual(original,changed)
        (child/'task.dsn').write_bytes(changed)
        with self.assertRaisesRegex(p.Rejected,'original Default target'):angle.check_global_width_targets(child,data['source'])

    def test_route_admits_only_versioned_original_global_width_scope_before_job(self):
        child=self.scratch();source=child/'source';source.mkdir();board=source/'owned.kicad_pcb';board.write_text('(kicad_pcb)');self.project(board)
        kw=dict(adapter='both',engine_profile=angle.PROFILE,_fanout_enabled=False,_optimizer_enabled=False,_engine_clearance_margin_nm=20000)
        class ReachedJob(Exception):pass
        with patch.object(p,'preflight',return_value=[]),patch.object(p,'check_storage'),patch.object(p,'sha',return_value=p.c.JAR_SHA256),patch.object(p,'Job',side_effect=ReachedJob):
            with self.assertRaisesRegex(p.Rejected,'derived non-strict'):p.route(board,self.root/'out',**kw)
            with self.assertRaises(ReachedJob):p.route(board,self.root/'out',**kw,_engine_global_width_policy=p.ENGINE_GLOBAL_WIDTH_POLICY)
        for changes in (dict(_engine_global_width_policy=True),dict(_engine_clearance_margin_nm=None),dict(_engine_clearance_margin_nm=20000.),dict(_optimizer_enabled=None),dict(_fanout_enabled=None),dict(adapter='none'),dict(keep_existing=True),dict(settings_path='/missing')):
            args=dict(kw,_engine_global_width_policy=p.ENGINE_GLOBAL_WIDTH_POLICY);args.update(changes)
            with self.subTest(changes=changes),patch.object(p,'Job',side_effect=AssertionError('no output')),self.assertRaises(p.Rejected):p.route(board,self.root/'out',**args)

    def nested_scene(self):
        child,inc,parent=pruning.StrongerIncumbentControls.scene(self)
        self.project(Path(inc['source']))
        inc.update(engine_budget=self.budget(),engine_global_width_policy=p.ENGINE_GLOBAL_WIDTH_POLICY,
            minimum_width_guard=p.minimum_width_guard(inc['source'],'both'))
        inc['engine_budget'].update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120)
        inc['steps'][0]['argv']=p.engine_argv(child,inc['engine_budget']['argv'],profile=angle.PROFILE)
        p.save_json(child/'engine-process.json',inc['steps'][0]);p.save_json(child/'result.json',inc)
        parent.update(incumbent_policy=s.STRONG_WIDTH_INCUMBENT_POLICY,incumbent_receipt_sha256=p.sha(child/'result.json'),steps=[dict(row,phase='incumbent') for row in inc['steps']])
        marker=self.root/'pruning-incumbent-policy.json';p.save_json(marker,s._incumbent_policy_contract(self.root,inc,s.STRONG_WIDTH_INCUMBENT_POLICY))
        parent['incumbent_policy_binding']['sha256']=p.sha(marker)
        return child,inc,parent

    def test_v2_parent_replays_new_child_and_nested_angle_population_without_root_markers(self):
        child,inc,parent=self.nested_scene()
        with patch.object(p,'check_result',return_value={'current':True}),patch.object(s,'check_pruning_preferences'),patch('autorouter.local_settings.check_normal_policy'):
            s.check_incumbent_scoring(self.root,parent);self.assertFalse(angle.marked(self.root,parent))
        self.assertEqual(s._incumbent_route_options(s.STRONG_WIDTH_INCUMBENT_POLICY,'via_default')['_engine_global_width_policy'],p.ENGINE_GLOBAL_WIDTH_POLICY)

    def test_v1_cannot_adopt_v2_or_root_width_marker_and_v2_requires_width_marker(self):
        for mode in ('v1','missing_child','root'):
            child,inc,parent=self.nested_scene()
            if mode=='v1':parent['incumbent_policy']=s.STRONG_INCUMBENT_POLICY
            elif mode=='missing_child':inc.pop('engine_global_width_policy');p.save_json(child/'result.json',inc)
            else:parent['engine_global_width_policy']=p.ENGINE_GLOBAL_WIDTH_POLICY
            marker=self.root/'pruning-incumbent-policy.json';p.save_json(marker,s._incumbent_policy_contract(self.root,inc,parent['incumbent_policy']))
            parent['incumbent_policy_binding']['sha256']=p.sha(marker)
            with self.subTest(mode=mode),self.assertRaises(p.Rejected):s.check_incumbent_policy(self.root,parent)

    def test_late_original_width_edit_invalidates_shared_publication(self):
        child,data=self.scene();data.update(passed=True,accepted=False,status='completed');save=p.save_json;seen=[]
        def stable():p.check_engine_profile_record(data,child)
        def write(path,value):
            save(path,value)
            if Path(path)==child/'result.json' and not seen:
                project=Path(data['source']).with_suffix('.kicad_pro');changed=f.read_json(project);changed['board']['design_settings']['rules']['min_track_width']=.21;save(project,changed);seen.append(True)
        def account():
            if data['status']!='completed':data['passed']=False
        with patch.object(p,'save_json',side_effect=write):f.publish(child,data,stable,account,lambda:100,final_check=stable)
        self.assertTrue(seen);self.assertFalse(f.read_json(child/'result.json')['passed'])


if __name__=='__main__':unittest.main()
