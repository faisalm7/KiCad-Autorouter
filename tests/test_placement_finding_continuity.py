"""Metadata anchors may translate; warning approval and physical checks may not."""
import copy
import unittest

from autorouter import placement
from autorouter import schematic_field_evidence as fields, schematic_fields
from experiments.placement_native_proposal_v1 import contract, ordinary_fixture


class FindingContinuityTests(unittest.TestCase):
    def setUp(self):
        self.observation = contract.inspect_board(
            (contract.sx.dump(ordinary_fixture.board()) + '\n').encode(), scope=contract.ORDINARY_SCOPE)
        self.observation['scope'] = contract.CONTEXT_SCOPE
        self.identity = ordinary_fixture.selected()[0]
        fp = next(row for row in self.observation['footprints'] if row['uuid'] == self.identity)
        self.old = fp['position_nm']; self.target = [self.old[0] + 200000, self.old[1] + 100000]
        self.moves = {self.identity: self.target}
        self.source = dict(blocking=0, exclusions=0, ignored_checks=[], findings=[dict(
            type='lib_footprint_issues', severity='warning', description='Footprint library missing',
            items=[dict(uuid=self.identity, description='Footprint J1',
                        pos=dict(zip(('x', 'y'), (n/1e6 for n in self.old))))])])
        self.candidate = copy.deepcopy(self.source)
        self.candidate['findings'][0]['items'][0]['pos'] = dict(zip(('x', 'y'), (n/1e6 for n in self.target)))

    def check(self, native=None, source=None, moves=None, scope=None):
        return placement.finding_continuity(native or self.candidate, source or self.source,
            self.observation, moves or self.moves, scope or contract.CONTEXT_SCOPE)

    def test_only_exact_metadata_anchor_translations_with_raw_reports_unchanged(self):
        for kind in ('lib_footprint_issues', 'footprint_symbol_field_mismatch'):
            before, after = copy.deepcopy(self.source), copy.deepcopy(self.candidate)
            before['findings'][0]['type'] = kind; after['findings'][0]['type'] = kind
            if kind == fields.TYPE:
                for data in (before, after):
                    finding = data['findings'][0]; finding['description'] = schematic_fields.DESCRIPTION
                    data['field_parity'] = self.field_proof(finding)
            saved = copy.deepcopy((before, after))
            proof = self.check(after, before)
            self.assertEqual(proof['translated_metadata_anchors'][0]['candidate_position_nm'], self.target)
            self.assertFalse(proof['warning_acknowledged'])
            self.assertEqual((before, after), saved)

    def field_proof(self, finding):
        # A pure schema fixture; the real workflow must independently derive
        # this from complete Native netlist/field observations at each stage.
        q = dict(qualified=True, policy=schematic_fields.POLICY, component_count=1,
                 compared_field_count=2, comparison_map=[dict(uuid=self.identity,
                    schematic_fields=dict(Datasheet='', Description=''),
                    pcb_fields=dict(Datasheet='~', Description=''))],
                 warning_uuids=[self.identity],
                 warning_hashes=[schematic_fields.digest(schematic_fields.canonical(finding))],
                 native_export_sha256='0'*64, observer_sha256='1'*64, drc_report_sha256='2'*64)
        return dict(schema=1, policy=fields.POLICY, qualification=q)

    def test_symbol_field_warning_still_needs_independent_current_complete_proof(self):
        old, new = copy.deepcopy(self.source), copy.deepcopy(self.candidate)
        for data in (old, new):
            data['findings'][0].update(type=fields.TYPE, description=schematic_fields.DESCRIPTION)
            data['field_parity'] = self.field_proof(data['findings'][0])
        self.assertFalse(self.check(new, old)['warning_acknowledged'])
        for mutate in (lambda d: d.pop('field_parity'),
                       lambda d: d.update(field_parity=copy.deepcopy(old['field_parity'])),
                       lambda d: d['field_parity']['qualification']['comparison_map'][0]['pcb_fields'].update(Description='Changed')):
            bad = copy.deepcopy(new); mutate(bad)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError): self.check(bad, old)

    def test_old_scope_stays_exact_and_unchanged_findings_stay_exact(self):
        with self.assertRaisesRegex(ValueError, 'warning/check policy changed'):
            self.check(scope=contract.ORDINARY_SCOPE)
        self.assertIsNone(self.check(self.source, scope=contract.ORDINARY_SCOPE))

    def test_wrong_position_reference_description_type_or_census_refuses(self):
        changes = [lambda d: d['findings'][0]['items'][0]['pos'].update(x=0),
                   lambda d: d['findings'][0]['items'][0].update(uuid=ordinary_fixture.selected()[1]),
                   lambda d: d['findings'][0]['items'][0].update(description='Another part'),
                   lambda d: d['findings'][0].update(description='A different issue'),
                   lambda d: d['findings'][0].update(type='silk_overlap'),
                   lambda d: d['findings'].append(copy.deepcopy(d['findings'][0])),
                   lambda d: d['findings'].clear(),
                   lambda d: d.update(ignored_checks=['silk_overlap'])]
        for change in changes:
            bad = copy.deepcopy(self.candidate); change(bad)
            with self.subTest(change=change), self.assertRaises(ValueError): self.check(bad)

    def test_critical_or_geometric_warning_never_gets_anchor_permission(self):
        for kind in ('silk_overlap', 'silk_edge_clearance', 'clearance'):
            old, new = copy.deepcopy(self.source), copy.deepcopy(self.candidate)
            old['findings'][0]['type'] = kind; new['findings'][0]['type'] = kind
            with self.subTest(kind=kind), self.assertRaises(ValueError): self.check(new, old)
        for field in ('blocking', 'exclusions'):
            bad = copy.deepcopy(self.candidate); bad[field] = 1
            with self.subTest(field=field), self.assertRaises(ValueError): self.check(bad)
        bad = copy.deepcopy(self.candidate); bad['findings'][0]['severity'] = 'error'
        with self.assertRaises(ValueError): self.check(bad)

    def test_unproven_original_anchor_and_multi_item_findings_refuse(self):
        original = copy.deepcopy(self.source); original['findings'][0]['items'][0]['pos']['x'] += .1
        with self.assertRaisesRegex(ValueError, 'captured footprint position'):
            self.check(source=original)
        old, new = copy.deepcopy(self.source), copy.deepcopy(self.candidate)
        for data in (old, new):
            data['findings'][0]['items'].append(copy.deepcopy(data['findings'][0]['items'][0]))
        with self.assertRaises(ValueError): self.check(new, old)

    def test_fixed_or_unknown_target_cannot_normalize_a_warning(self):
        for identity in ('not-a-uuid', self.observation['footprints'][0]['uuid']):
            if identity == self.identity: continue
            moves = {identity: self.target}
            # Even a valid but different eligible identity cannot explain J1's
            # moved warning position; unknown IDs fail before comparison.
            with self.subTest(identity=identity), self.assertRaises(ValueError): self.check(moves=moves)
        for target in ([True, 100], [1.5, 2], [1], ['1', 2]):
            with self.subTest(target=target), self.assertRaises(ValueError): self.check(moves={self.identity: target})


if __name__ == '__main__':
    unittest.main()
