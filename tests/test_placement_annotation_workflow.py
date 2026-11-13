"""Shared annotation binding/constraints/UI seams; mocked processes are not Native proof."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import stat
import unittest
from unittest.mock import patch, Mock

from autorouter import gui, pipeline as p, placement_intent as intent, placement_view
from autorouter import placement_annotations as annotations, project_inspection as inspection
from autorouter import local_settings
from experiments.placement_native_proposal_v1 import contract, ordinary_fixture
from experiments.constrained_placement_v1 import constraints
from tests import test_placement_gui as gui_fixture


class AnnotationWorkflowTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='annotation-workflow-')
        self.addCleanup(temporary.cleanup);self.root=Path(temporary.name).resolve()
        self.board=ordinary_fixture.write_project(self.root/'source')
        self.raw=self.board.read_bytes();self.hashes=gui.source_inventory(self.board)
        self.observation=contract.inspect_board(self.raw,scope=contract.CONTEXT_SCOPE)
        self.selected=ordinary_fixture.selected()
        self.context=dict(schema=1,policy=annotations.POLICY,scope=contract.CONTEXT_SCOPE,
            source_board_sha256=self.hashes[self.board.name],outline_nm=self.observation['outline']['bounds_nm'],
            silk_clearance_nm=100000,
            footprint_anchors_nm={fp['uuid']:fp['position_nm'] for fp in self.observation['footprints']},
            movable_owners=[fp['uuid'] for fp in self.observation['footprints'] if fp['placement_eligible']],
            rows=[dict(uuid=ordinary_fixture.uid('annotation-test-field'),owner=self.selected[0],kind='silk',
                       bbox_nm=[-500000,-3000000,500000,-2000000]),
                  dict(uuid=ordinary_fixture.uid('annotation-test-fixed'),owner=None,kind='silk',
                       bbox_nm=[29500000,8000000,30500000,9000000])])
        self.directory=self.root/'inspection';self.directory.mkdir()
        self.snapshot=ordinary_fixture.write_project(self.directory/'snapshot')
        self.geometry_path=self.directory/'placement-context.json'
        self.geometry=dict(schema=1,kind='autorouter.native-placement-context.v1',native_version='10.0.7',
            source=str(self.snapshot),board_sha256=self.hashes[self.board.name],
            project_sha256=self.hashes[self.board.with_suffix('.kicad_pro').name],
            schematic_sha256=self.hashes[self.board.with_suffix('.kicad_sch').name],
            board_saved=False,context=self.context)
        p.save_json(self.geometry_path,self.geometry)
        process=self.directory/'placement-context-process.json';p.save_json(process,{})
        prl=self.snapshot.with_suffix('.kicad_prl')
        protection=dict(policy=local_settings.POLICY,present=True,path=str(prl),sha256=self.hashes[prl.name],
                        flags_before=0,flags_during=getattr(stat,'UF_IMMUTABLE',2),flags_restored=True,bytes_unchanged=True)
        self.record=dict(policy=inspection.PLACEMENT_POLICY,source=str(self.board),source_hashes=self.hashes,
                         placement_context=dict(file='placement-context.json',sha256=p.sha(self.geometry_path),
                             local_settings_policy=local_settings.JOB_POLICY,process_sha256=p.sha(process),protection=protection))
        self.receipt=self.directory/'inspection.json';p.save_json(self.receipt,self.record)

    def test_new_flag_is_explicit_and_version_gated_without_touching_source(self):
        for flag in (True, 1, 'yes'):
            with self.subTest(flag=flag),patch.object(inspection.c,'NATIVE_VERSION','10.0.0'), \
                    patch.object(p,'Job') as job,self.assertRaises(ValueError):
                inspection.inspect(self.board,self.root/'unused',placement_context=flag)
            job.assert_not_called()
        self.assertEqual(self.board.read_bytes(),self.raw)

    def test_context_replays_exact_process_source_and_material_binding(self):
        with patch.object(inspection.c,'NATIVE_VERSION','10.0.7'), \
                patch.object(inspection.f,'process_check') as process, \
                patch.object(local_settings,'check_preserved') as metadata:
            self.assertEqual(inspection.check_placement_context(self.directory,self.record,self.snapshot,self.hashes),self.context)
        metadata.assert_called_once_with(self.snapshot.with_suffix('.kicad_prl'),self.hashes,self.record['placement_context']['protection'])
        self.assertIn('placement-context',process.call_args.args[3])
        for key,value in [('board_saved',True),('native_version','10.0.0'),('source',str(self.board)),('schema',True)]:
            data=copy.deepcopy(self.geometry);data[key]=value;p.save_json(self.geometry_path,data)
            record=copy.deepcopy(self.record);record['placement_context']['sha256']=p.sha(self.geometry_path)
            with self.subTest(key=key),patch.object(inspection.c,'NATIVE_VERSION','10.0.7'), \
                    patch.object(inspection.f,'process_check') as process,self.assertRaises(ValueError):
                inspection.check_placement_context(self.directory,record,self.snapshot,self.hashes)
            process.assert_not_called()

    def test_context_local_settings_and_actual_process_reference_cannot_disappear(self):
        for key,value in [('local_settings_policy','none'),('process_sha256','0'*64),('protection',None)]:
            record=copy.deepcopy(self.record);record['placement_context'][key]=value
            with self.subTest(key=key),patch.object(inspection.c,'NATIVE_VERSION','10.0.7'), \
                    patch.object(inspection.f,'process_check'),self.assertRaises((ValueError,p.Rejected)):
                inspection.check_placement_context(self.directory,record,self.snapshot,self.hashes)

    def test_native_receipt_is_bound_to_saved_intake_and_cannot_be_silently_replaced(self):
        with patch.object(inspection,'check',return_value=self.record):
            value=intent.inspect_saved(self.board,native_context=self.receipt)
            self.assertEqual(value['observation']['scope'],contract.CONTEXT_SCOPE)
            self.assertEqual(value['annotation_context'],self.context)
            self.assertFalse(value['execution_authorized']);self.assertFalse(value['approval_granted'])
            self.assertEqual(intent.current(value),value)
            self.receipt.write_text(self.receipt.read_text()+'\n')
            with self.assertRaisesRegex(ValueError,'evidence changed'):
                intent.current(value)

    def test_changed_geometry_receipt_other_source_or_incomplete_policy_refuses(self):
        with patch.object(inspection,'check',return_value=self.record):
            self.geometry_path.write_text(self.geometry_path.read_text()+'\n')
            with self.assertRaisesRegex(ValueError,'context changed'):
                intent.inspect_saved(self.board,native_context=self.receipt)
        p.save_json(self.geometry_path,self.geometry)
        other=copy.deepcopy(self.record);other['source']=str(self.snapshot)
        p.save_json(self.receipt,other)
        with patch.object(inspection,'check',return_value=other),self.assertRaisesRegex(ValueError,'another source'):
            intent.inspect_saved(self.board,native_context=self.receipt)
        with self.assertRaises(ValueError):intent.inspect_saved(self.board,native_context={'receipt':str(self.receipt)})

    def test_extra_native_prefilter_remains_inside_shared_constraint_enforcement(self):
        facts=contract.facts_from_observation(self.observation,scope=contract.CONTEXT_SCOPE,
            selected=self.selected,region_nm=[7000000,7000000,31000000,13000000])
        facts['annotation_context']=self.context;facts=constraints.prepare(facts)
        original=constraints.original_alternative(facts);constraints.validate_alternative(facts,original)
        pose=copy.deepcopy(original)
        next(t for t in pose['transforms'] if t['component_id']==self.selected[0]).update(x_mm=30,y_mm=11)
        with self.assertRaisesRegex(constraints.Refused,'annotation conflict'):
            constraints.validate_alternative(facts,pose)
        altered=copy.deepcopy(facts);altered['annotation_context']['footprint_anchors_nm'][self.selected[0]][0]+=1
        with self.assertRaisesRegex(constraints.Refused,'source anchor differs'):constraints.prepare(altered)

    def test_real_search_numeric_edit_and_draft_share_the_native_fact_binding(self):
        with patch.object(inspection,'check',return_value=self.record):
            source=intent.inspect_saved(self.board,native_context=self.receipt)
            settings=intent.settings(self.selected,[7000000,7000000,31000000,13000000],scope=contract.CONTEXT_SCOPE)
            proposal=intent.propose(source,settings)
            self.assertEqual(proposal['search']['status'],'proposals_ready')
            review=intent.Review(proposal);review.edit_many({self.selected[0]:['13.2','10']})
            draft=review.decision(acknowledged=True,accepted=True)
            self.assertEqual(intent.validate_draft(source,draft),draft)
            self.assertEqual(draft['native_context'],source['native_context'])
            self.assertFalse(draft['native_validation_performed']);self.assertFalse(draft['approval_granted'])
            missing=copy.deepcopy(draft);del missing['native_context']
            with self.assertRaises(ValueError):intent.validate_draft(source,missing)

    def test_preview_shows_selected_native_silkscreen_extents_without_granting_authority(self):
        moves={key:self.context['footprint_anchors_nm'][key] for key in self.selected}
        svg=placement_view.render(self.observation,moves,self.selected,[7000000,7000000,31000000,13000000],annotation_context=self.context)
        self.assertIn('proposed-silkscreen-proxy',svg)
        self.assertIn('Native silkscreen extents; final checks required',svg)
        self.assertIn('Geometry draft',svg)

    def test_GUI_uses_off_thread_native_detail_for_ordinary_saved_sources(self):
        from autorouter import placement_gui as pg
        window=gui_fixture.PlacementGuiTests().window();window.board=Mock();window.board.GetValue.return_value=str(self.board)
        window.start=Mock();window.owned_workspace=Mock(return_value=self.root)
        gui_fixture.window_method('inspect_project')(window,None)
        work=window.start.call_args.args[1];job=Mock()
        job.run.return_value=dict(exit_code=0,log_truncated=False,cancel_requested=False)
        legacy=dict(observation=dict(scope=contract.ORDINARY_SCOPE));captured=dict(native_context='owned receipt')
        with patch.object(pg.c,'NATIVE_VERSION','10.0.7'), \
                patch.object(intent,'inspect_saved',side_effect=[legacy,captured]) as inspect:
            self.assertEqual(work(job,None),captured)
        argv=job.run.call_args.args[0];self.assertIn('--placement-context',argv)
        self.assertEqual(inspect.call_args.kwargs['native_context'].name,'inspection.json')
        self.assertIsNone(window.qualified)

    def test_GUI_native_inspection_failure_never_adopts_saved_only_geometry(self):
        from autorouter import placement_gui as pg
        window=gui_fixture.PlacementGuiTests().window();window.board=Mock();window.board.GetValue.return_value=str(self.board)
        window.start=Mock();window.owned_workspace=Mock(return_value=self.root)
        gui_fixture.window_method('inspect_project')(window,None)
        work=window.start.call_args.args[1];job=Mock()
        job.run.return_value=dict(exit_code=2,log_truncated=False,cancel_requested=False)
        with patch.object(intent,'inspect_saved',return_value=dict(observation=dict(scope=contract.CONTEXT_SCOPE))) as inspect, \
                self.assertRaisesRegex(ValueError,'inspection refused'):
            work(job,None)
        self.assertEqual(inspect.call_count,1);self.assertIsNone(window.qualified)


if __name__=='__main__':unittest.main()
