"""Prospective experimental baseline controls; no Native/quality evidence.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from autorouter import config as c,engine_angle as a,pipeline as p,sexpr as sx,adapter as dsn

RAW=b'(pcb "owned" (parser (string_quote ")) (resolution um 10) (unit um) (structure (layer F.Cu (type signal)) (layer B.Cu (type signal)) (boundary (rect pcb 0 0 10000 10000)) (rule (width 250))) (library (image "part" (pin "round" "1" 100 200)) (padstack "round" (shape (circle F.Cu 250)))) (network (net SIGNAL (pins part-1))))\n'

class EngineAngleControls(unittest.TestCase):
    def scratch(self):
        context=tempfile.TemporaryDirectory(dir=c.ROOT/'.local-backups');self.addCleanup(context.cleanup);return Path(context.name)
    def test_only_missing_structure_angle_is_inserted_and_all_geometry_rules_survive(self):
        output,record=a.transform(RAW);before=dsn._parse_dsn(RAW.decode());after=dsn._parse_dsn(output.decode())
        self.assertEqual(sx.one(sx.one(after,'structure'),'snap_angle'),['snap_angle','none'])
        sx.one(after,'structure').remove(['snap_angle','none']);self.assertEqual(after,before)
        self.assertEqual(record['input']['sha256'],p.hashlib.sha256(RAW).hexdigest())
        self.assertTrue(record['exact_only_structure_snap_angle_insert'])
    def test_existing_or_ambiguous_angle_is_not_overridden(self):
        for node in [['snap_angle','fortyfive_degree'],['snap_angle','none'],['snap_angle','ninety_degree'],['snapAngle','none'],['SNAP_ANGLE','none']]:
            for parent in ['structure','library']:
                tree=dsn._parse_dsn(RAW.decode());sx.one(tree,parent).append(node)
                with self.subTest(node=node,parent=parent),self.assertRaises(p.Rejected):a.transform(dsn._dump_dsn(tree).encode())
    def test_missing_duplicate_structure_and_non_pcb_root_refuse(self):
        before=dsn._parse_dsn(RAW.decode())
        for mode in ['missing','duplicate','root']:
            tree=copy.deepcopy(before)
            if mode=='missing':tree.remove(sx.one(tree,'structure'))
            elif mode=='duplicate':tree.append(copy.deepcopy(sx.one(tree,'structure')))
            else:tree[0]='board'
            with self.subTest(mode=mode),self.assertRaises(p.Rejected):a.transform(dsn._dump_dsn(tree).encode())
    def test_bounded_bytes_and_parser_errors_refuse(self):
        for raw in [None,RAW.decode(),b'',b'(',b'\xff']:
            with self.subTest(raw=raw),self.assertRaises(p.Rejected):a.transform(raw)
        with patch.object(a,'MAX_BYTES',len(RAW)-1),self.assertRaises(p.Rejected):a.transform(RAW)
    def test_prepare_preserves_canonical_task_and_refuses_overwrite(self):
        directory=self.scratch();(directory/'task.dsn').write_bytes(RAW);binding=a.prepare(directory)
        self.assertEqual((directory/'task.dsn').read_bytes(),RAW)
        self.assertEqual(a.check(directory,dict(engine_profile=a.PROFILE,engine_budget={},engine_angle_binding=binding))['profile'],a.PROFILE)
        with self.assertRaises(FileExistsError):a.prepare(directory)
    def test_missing_tampered_binding_task_or_geometry_refuse(self):
        for change in ['binding','task','output','record']:
            directory=self.scratch();(directory/'task.dsn').write_bytes(RAW);binding=a.prepare(directory);data=dict(engine_profile=a.PROFILE,engine_budget={},engine_angle_binding=binding)
            if change=='binding':data.pop('engine_angle_binding')
            elif change=='task':(directory/'task.dsn').write_bytes(RAW.replace(b'(width 250)',b'(width 200)'))
            elif change=='output':(directory/a.INPUT).write_bytes((directory/a.INPUT).read_bytes().replace(b'(width 250)',b'(width 200)'))
            else:
                record=json.loads((directory/a.RECORD).read_text());record['extra']='unbound';(directory/a.RECORD).write_text(json.dumps(record));data['engine_angle_binding']['sha256']=p.sha(directory/a.RECORD)
            with self.subTest(change=change),self.assertRaises(p.Rejected):a.check(directory,data)
    def test_policy_downgrade_and_aliases_refuse(self):
        directory=self.scratch();(directory/'task.dsn').write_bytes(RAW);binding=a.prepare(directory)
        with self.assertRaises(p.Rejected):a.check(directory,dict(engine_profile='tuned',engine_angle_binding=binding))
        with self.assertRaises(p.Rejected):a.check(directory,dict(engine_profile='tuned'))
        target=directory/'foreign';target.write_bytes((directory/a.INPUT).read_bytes());(directory/a.INPUT).unlink();(directory/a.INPUT).symlink_to(target)
        with self.assertRaises((p.Rejected,ValueError)):a.check(directory,dict(engine_profile=a.PROFILE,engine_budget={},engine_angle_binding=binding))
    def test_shared_normal_reader_requires_angle_budget_even_after_profile_downgrade(self):
        for changed_profile in [a.PROFILE,'tuned']:
            directory=self.scratch();(directory/'task.dsn').write_bytes(RAW);binding=a.prepare(directory)
            (directory/'result.json').write_text(json.dumps(dict(schema=1,engine_profile=changed_profile,engine_angle_binding=binding)))
            with self.subTest(profile=changed_profile),self.assertRaisesRegex(p.Rejected,'search-angle'):
                p._check_result_uncached(directory/'result.json')
        directory=self.scratch();data=dict(engine_profile='tuned',steps=[dict(argv=['java','-de',str(directory/a.INPUT)])])
        self.assertTrue(a.marked(directory,data))
        with self.assertRaisesRegex(p.Rejected,'another engine profile'):a.check(directory,data)
        (directory/'engine-process.json').write_text(json.dumps(data['steps'][0]))
        with self.assertRaisesRegex(p.Rejected,'another engine profile'):a.check(directory,dict(engine_profile='tuned'))

    def test_current_captured_producer_cannot_drop_budget_and_worker_markers(self):
        directory=self.scratch();(directory/'code').mkdir();code=(directory/'code/pipeline.py')
        raw=(c.ROOT/'autorouter/pipeline.py').read_bytes();code.write_bytes(raw)
        data=dict(engine_profile='tuned',tools=dict(implementation_sha256={'autorouter/pipeline.py':p.hashlib.sha256(raw).hexdigest()}))
        with self.assertRaisesRegex(p.Rejected,'requires retained engine budget/journal'):p.check_normal_engine_provenance(directory,data)
        data['engine_budget']={};p.check_normal_engine_provenance(directory,data)
        legacy=b'x=1\n';code.write_bytes(legacy);data.pop('engine_budget');data['tools']['implementation_sha256']['autorouter/pipeline.py']=p.hashlib.sha256(legacy).hexdigest()
        p.check_normal_engine_provenance(directory,data)

    def test_tuned_settings_caps_and_scoring_are_identical_but_engine_path_is_distinct(self):
        for remaining in [41,120,900]:
            for score in [None,'via_low','via_high']:
                old=p.engine_profile_settings('tuned',remaining,strict_class_targets=True,scoring_variant=score)
                new=p.engine_profile_settings(a.PROFILE,remaining,strict_class_targets=True,scoring_variant=score,experimental_free_angle=True)
                self.assertEqual({k:v for k,v in old.items() if k!='profile'},{k:v for k,v in new.items() if k!='profile'})
                self.assertEqual(p.engine_argv(Path('/owned'),old['argv'])[-4:],['-de','/owned/task.dsn','-do','/owned/routes.ses'])
                self.assertEqual(p.engine_argv(Path('/owned'),new['argv'],profile=a.PROFILE)[-4:],['-de','/owned/'+a.INPUT,'-do','/owned/routes.ses'])
        self.assertEqual(p.engine_baseline(a.PROFILE,'both'),'B2_tuned_free_angle')
    def test_floor_or_other_reader_scope_cannot_validate_an_unused_angle_copy(self):
        good=dict(adapter='both',scope='whole_board_unlocked_routing',baseline='B2_tuned_free_angle')
        a.check_scope(good,'native')
        for policy in ['board-floors-v1','placement-clearance-v1','placement-search-v1']:
            with self.subTest(policy=policy),self.assertRaisesRegex(p.Rejected,'search-angle receipt'):a.check_scope(good,policy)
        for changed in [dict(adapter='none'),dict(scope='partial_completion'),dict(strategy='native_validated_zone_net_pruning'),dict(baseline='B2_tuned'),dict(routing_preferences={}),dict(layer_binding={})]:
            with self.subTest(changed=changed),self.assertRaises(p.Rejected):a.check_scope({**good,**changed},'native')
        with self.assertRaisesRegex(p.Rejected,'explicit native baseline opt-in'):p.engine_profile_settings(a.PROFILE,120)
        with self.assertRaises(p.Rejected):p.engine_profile_settings(a.PROFILE,120,experimental_free_angle=1)

    def test_non_native_partial_and_uncorrected_modes_refuse_before_output(self):
        for kwargs in [dict(adapter='none'),dict(adapter='both',keep_existing=True),dict(adapter='both',guidance_policy='board-floors-v1')]:
            with self.subTest(kwargs=kwargs),self.assertRaisesRegex(p.Rejected,'free-angle baseline requires'):
                p.route('/nonexistent/owned.kicad_pcb','/nonexistent/out',engine_profile=a.PROFILE,**kwargs)

if __name__=='__main__':unittest.main()
