"""Pure composed lineage controls; synthetic witness, no Native approval."""
import copy
import json
import shutil
import unittest
from unittest.mock import patch

from autorouter import gui, placement, sexpr as sx
from experiments.placement_native_proposal_v1 import contract
from tests.test_placement_copper import raw
from tests import test_placement_copper_qualification as base


class ComposedOrigin(unittest.TestCase):
    def setUp(self):
        base.PreparedSourceQualification.setUp(self)
        self.binding['intent']['moves_nm'] = dict(zip(self.settings['selected'],
            ([14_000_000, 10_000_000], [24_000_000, 10_000_000])))
        self.candidate = self.root/'posed'/self.board.name
        shutil.copytree(self.board.parent, self.candidate.parent)
        prepared = placement.copper.prepare(self.raw, self.plan)
        tree = contract.translated_tree(prepared, self.binding['intent']['moves_nm'],
            scope=contract.ORDINARY_SCOPE, selected=self.settings['selected'], region_nm=self.settings['region_nm'])
        self.candidate.write_bytes(raw(tree))
        self.witness = dict(binding=self.binding, candidate=str(self.candidate), evidence_hashes={'synthetic': 'witness'})
        self.preferences = placement.routing_settings(self.witness)

    def test_exact_task_and_scope_proof_do_not_grant_native_or_approval_authority(self):
        self.assertIsNone(placement._routing_task(self.witness, self.preferences, 'route'))
        result = placement._routing_task(self.witness, self.preferences, 'route', self.candidate)
        self.assertTrue(result['audit_passed'])
        for key in ('approval_granted', 'execution_authorized', 'routing_accepted', 'native_validation_performed'):
            self.assertIs(result[key], False)
        self.assertEqual(self.board.read_bytes(), self.raw)

    def test_scope_method_or_search_policy_cannot_expand_approved_rebuild(self):
        cases = [('nets', ['ROUTE_A']), ('nets', ['ROUTE_A','ROUTE_B','GND']),
                 ('nets', ['ROUTE_B','ROUTE_A']), ('adapter','none'), ('scoring_preference','via_low'),
                 ('scoring_preference','via_default'), ('profile','standard'), ('layers',['F.Cu']),
                 ('guidance','board-floors-v1'), ('seconds',True)]
        for key,value in cases:
            changed = copy.deepcopy(self.preferences); changed[key] = value
            with self.subTest(key=key,value=value), self.assertRaises(ValueError):
                placement._routing_task(self.witness, changed, 'route')
        for method in ('improve','recover'):
            with self.subTest(method=method), self.assertRaises(ValueError):
                placement._routing_task(self.witness, self.preferences, method)

    def test_changed_protected_copper_and_sidecars_refuse(self):
        original = self.candidate.read_bytes(); tree = sx.parse(original.decode())
        retained = placement.p.routes(tree)[0]; sx.one(retained,'width')[1] = '0.4'
        self.candidate.write_bytes(raw(tree))
        with self.assertRaises((ValueError,placement.p.Rejected)):
            placement._routing_task(self.witness,self.preferences,'route',self.candidate)
        self.candidate.write_bytes(original)
        for suffix in ('.kicad_pro','.kicad_sch','.kicad_prl'):
            path = self.candidate.with_suffix(suffix); before = path.read_bytes()
            path.write_bytes(before+b'\n')
            with self.subTest(suffix=suffix), self.assertRaisesRegex(ValueError,'sidecars'):
                placement._routing_task(self.witness,self.preferences,'route',self.candidate)
            path.write_bytes(before)

    def test_marker_and_field_are_both_required_and_cannot_change(self):
        folder = self.root/'route'; folder.mkdir(); qualification = self.root/'qualification'; qualification.mkdir()
        for name in ('result.json','binding.json'): (qualification/name).write_text('{}')
        descriptor = placement._origin(qualification,self.witness)
        report = dict(schema=1,source=str(self.candidate),placement_origin=descriptor,
                      routing_preferences=dict(effective=self.preferences))
        marker = folder/placement.ORIGIN_FILE
        with self.assertRaisesRegex(ValueError,'missing'): placement.check_routing_record(folder,report)
        marker.write_text(json.dumps(descriptor))
        with self.assertRaisesRegex(ValueError,'missing'): placement.check_routing_record(folder,{})
        with patch.object(placement,'check',return_value=self.witness), patch.object(placement,'source_guard') as guard:
            audit = placement.check_routing_record(folder,report,self.candidate)
            self.assertTrue(audit['audit_passed']); guard.return_value.check.assert_called_with(str(self.candidate))
            (qualification/'result.json').write_text('{"changed":true}')
            with self.assertRaisesRegex(ValueError,'origin changed'):
                placement.check_routing_record(folder,report,self.candidate)
        self.assertIsNone(placement.check_routing_record(self.root,{}))

    def test_existing_origin_cannot_be_relabelled_as_another_policy(self):
        folder = self.root/'route'; folder.mkdir(); (folder/placement.ORIGIN_FILE).write_text('{}')
        for key,value in [('schema',True), ('input_policy','placement-clearance-v1'),
                          ('strategy','native_validated_zone_net_pruning'), ('comparison_route',{}),
                          ('engine_fanout_override',False), ('native_improve_child',{})]:
            report=dict(schema=1,placement_origin={});report[key]=value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError,'cannot mix'):
                placement.check_routing_record(folder,report)

    def test_late_material_fence_detects_original_or_retained_evidence_change(self):
        folder = self.root/'route'; folder.mkdir()
        output = self.root/'.runs'/'qualification'; output.mkdir(parents=True)
        posed = output/'work/candidate'/self.board.name
        shutil.copytree(self.candidate.parent,posed.parent)
        (output/'binding.json').write_text(json.dumps(self.binding))
        (output/'result.json').write_text('{"synthetic":true}')
        evidence = placement.h.evidence_witness(output)
        descriptor = placement._origin(output,dict(evidence_hashes=evidence))
        (folder/placement.ORIGIN_FILE).write_text(json.dumps(descriptor))
        report=dict(placement_origin=descriptor,source=str(posed))
        # Only the new late byte/source fence is under test; Native qualification
        # and its metadata replay are explicitly synthetic here.
        with patch.object(placement.c,'ROOT',self.root), patch.object(placement,'material'), \
                patch.object(placement,'_metadata') as metadata:
            self.assertIsNone(placement.routing_origin_material(folder,report))
            metadata.assert_called_once()
            self.board.write_bytes(self.raw+b'\n')
            with self.assertRaisesRegex(ValueError,'source changed'):
                placement.routing_origin_material(folder,report)
            self.board.write_bytes(self.raw)
            (output/'result.json').write_text('{"synthetic":"changed"}')
            with self.assertRaisesRegex(ValueError,'material changed'):
                placement.routing_origin_material(folder,report)


if __name__ == '__main__': unittest.main()
