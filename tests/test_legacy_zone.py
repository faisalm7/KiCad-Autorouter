"""Authored pure legacy-rule controls, never Native evidence.

Fixtures are tiny owned ASTs, independent of datasets.
"""
import copy
import unittest
import uuid
import json
import tempfile
from pathlib import Path

from autorouter import sexpr as sx
from autorouter import pipeline as p

from autorouter import legacy_zone as lz


def uid(value):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'owned-legacy-zone/' + value))


def fixture():
    board = sx.parse('(kicad_pcb (version 20241229) (layers (0 "F.Cu" signal) (2 "B.Cu" signal) '
                     '(36 "F.SilkS" user)) (net 0 "") (net 1 "GND") (net 2 "PADLESS"))')
    board.append(sx.parse(f'(footprint "Owned" (uuid "{uid("fp")}") '
                          f'(pad "1" smd rect (at 0 0) (size 2 2) (layers "F.Cu") '
                          f'(net 1 "GND") (uuid "{uid("pad")}")))'))
    board.append(sx.parse(f'(zone (uuid "{uid("zone")}") (net 1) (net_name "GND") (layer "B.Cu") '
                          '(polygon (pts (xy 0 0) (xy 4 0) (xy 4 4) (xy 0 4))))'))
    project = {'board': {'design_settings': {'rule_severities': {'zone_has_empty_net': 'error'}}}}
    return board, project


def pad(board):
    return sx.children(sx.children(board, 'footprint')[0], 'pad')[0]


class LegacyZoneControls(unittest.TestCase):
    def check(self, board=None, project=None):
        original, settings = fixture()
        return lz.qualify(original if board is None else board, settings if project is None else project)

    def test_three_old_control_semantics_without_relabeling_native(self):
        for code, name, passes in [('1', 'GND', True), ('2', 'PADLESS', False), ('0', '', True)]:
            with self.subTest(code=code):
                board, _ = fixture(); zone = sx.children(board, 'zone')[0]
                sx.one(zone, 'net')[1] = code; sx.one(zone, 'net_name')[1] = '"' + name + '"'
                if not passes:
                    with self.assertRaisesRegex(ValueError, 'lacks.*witness'): self.check(board)
                else:
                    result = self.check(board)
                    self.assertIs(result['native_enforcement_claimed'], False)
                    self.assertEqual(result['zones'][0]['net0_exempt'], code == '0')
                    self.assertEqual('pad_witness' in result['zones'][0], code != '0')

    def test_smd_need_not_touch_zone_or_share_layer(self):
        row = self.check()['zones'][0]
        self.assertEqual(row['copper_layers'], ['B.Cu'])
        self.assertEqual(row['pad_witness']['copper_layers'], ['F.Cu'])
        self.assertEqual(row['pad_witness']['pad_uuid'], uid('pad'))

    def test_positive_pth_and_no_annulus_or_noncentered_drill_refuse(self):
        board, _ = fixture(); node = pad(board); node[2] = 'thru_hole'
        sx.one(node, 'layers')[:] = ['layers', '"*.Cu"']; node.append(['drill', '.8'])
        node.append(['remove_unused_layers','no'])
        self.assertEqual(self.check(board)['zones'][0]['pad_witness']['drill_nm'], 800000)
        changed=copy.deepcopy(board);sx.one(pad(changed),'remove_unused_layers')[1]='yes'
        with self.assertRaisesRegex(ValueError,'modifier'):self.check(changed)
        for drill in (['drill', '2'], ['drill', '.8', ['offset', '1', '0']], ['drill', 'oval', '.8', '1']):
            changed = copy.deepcopy(board); sx.one(pad(changed), 'drill')[:] = drill
            with self.subTest(drill=drill), self.assertRaises(ValueError): self.check(changed)
        sx.one(node, 'layers')[:] = ['layers', '"F.Cu"']
        with self.assertRaisesRegex(ValueError, 'all copper'): self.check(board)

    def test_non_copper_npth_or_tracks_are_not_pad_substitutes(self):
        for mode in ('noncopper', 'npth', 'tracks'):
            board, _ = fixture()
            if mode == 'noncopper': sx.one(pad(board), 'layers')[:] = ['layers', '"F.SilkS"']
            elif mode == 'npth':
                pad(board)[2] = 'np_thru_hole'; pad(board).append(['drill', '.8'])
            else:
                board.remove(sx.children(board, 'footprint')[0])
                board.append(sx.parse(f'(segment (uuid "{uid("track")}") (net 1) (layer "F.Cu"))'))
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'lacks.*witness'): self.check(board)

    def test_repeated_physical_pad_number_can_supply_witness(self):
        board, _ = fixture(); second = copy.deepcopy(pad(board))
        sx.one(second, 'uuid')[1] = '"' + uid('second-pad') + '"'
        sx.children(board, 'footprint')[0].append(second)
        self.assertEqual(self.check(board)['zones'][0]['pad_witness']['net_name'], 'GND')

    def test_orphan_name_alias_duplicate_net_uuid_or_singleton_refuse(self):
        edits = [lambda b: sx.one(pad(b), 'net').__setitem__(1, '9'),
                 lambda b: sx.one(pad(b), 'net').__setitem__(2, '"PADLESS"'),
                 lambda b: b.append(['net', '1', '"OTHER"']),
                 lambda b: b.append(['net', '3', '"GND"']),
                 lambda b: sx.children(b, 'zone')[0].append(['net', '1']),
                 lambda b: sx.one(sx.children(b, 'zone')[0], 'net_name').__setitem__(1, '"OTHER"'),
                 lambda b: sx.one(sx.children(b, 'zone')[0], 'uuid').__setitem__(1, '"' + uid('pad') + '"')]
        for edit in edits:
            board, _ = fixture(); edit(board)
            with self.subTest(edit=edits.index(edit)), self.assertRaises(ValueError): self.check(board)

    def test_custom_footprint_zone_unknown_alias_and_named_only_refuse(self):
        for mode in ('custom', 'footprint-zone', 'root-pad', 'group-alias', 'named'):
            board, _ = fixture()
            if mode == 'custom': pad(board)[3] = 'custom'
            elif mode == 'footprint-zone':
                zone = sx.children(board, 'zone')[0]; board.remove(zone)
                sx.children(board, 'footprint')[0].append(zone)
            elif mode == 'root-pad':
                node = pad(board); sx.children(board, 'footprint')[0].remove(node); board.append(node)
            elif mode == 'group-alias': sx.one(sx.children(board, 'zone')[0], 'layer')[1] = '"*.Cu"'
            else: board[:] = [n for n in board if not (isinstance(n, list) and n and n[0] == 'net')]
            with self.subTest(mode=mode), self.assertRaises(ValueError): self.check(board)

    def test_two_outer_layer_alias_and_dimension_owner_annotation(self):
        board,project=fixture();zone=sx.children(board,'zone')[0]
        sx.one(zone,'layer')[:]=['layers','"F&B.Cu"']
        self.assertEqual(self.check(board)['zones'][0]['copper_layers'],['B.Cu','F.Cu'])
        dimension=sx.parse(f'(dimension (uuid "{uid("dimension")}") (gr_text "owned" (uuid "{uid("dimension")}")))')
        board.append(dimension);self.check(board,project)
        sx.one(sx.one(dimension,'gr_text'),'uuid')[1]='"'+uid('pad')+'"'
        with self.assertRaisesRegex(ValueError,'duplicate UUID'):self.check(board,project)
        board.remove(dimension)
        sx.one(board,'layers').extend([['4','"In1.Cu"','signal'],['6','"In2.Cu"','signal']])
        with self.assertRaisesRegex(ValueError,'two outer copper'):self.check(board,project)

    def test_literal_error_only_and_input_is_not_modified(self):
        board, project = fixture(); before = copy.deepcopy((board, project))
        self.check(board, project); self.assertEqual((board, project), before)
        for value in ('warning', 'ignore', True, None):
            project['board']['design_settings']['rule_severities'][lz.KEY] = value
            with self.subTest(value=value), self.assertRaises(ValueError): self.check(board, project)

    def test_rederive_binds_source_geometry_but_ignores_new_routes_fill(self):
        board, _ = fixture(); record = self.check(board)
        board.append(sx.parse(f'(segment (uuid "{uid("added-route")}") (net 1) (layer "F.Cu"))'))
        sx.children(board, 'zone')[0].append(['filled_polygon', ['pts', ['xy', '1', '1']]])
        self.assertEqual(self.check(board), record)
        sx.one(pad(board), 'at')[1] = '1'
        self.assertNotEqual(self.check(board), record)  # Caller must reject retained stale witness.

    def test_preflight_error_constraint_is_separate_from_format_admission(self):
        board,project=fixture()
        with tempfile.TemporaryDirectory() as root:
            source=Path(root).resolve()/'owned.kicad_pcb'
            sx.write(source,board);source.with_suffix('.kicad_pro').write_text(json.dumps(project))
            self.assertEqual(p.preflight(source),board)
            sx.one(board,'version')[1]='20240108';sx.write(source,board)
            with self.assertRaisesRegex(p.Rejected,'unqualified board format'):p.preflight(source)
            sx.one(board,'version')[1]='20241229'
            sx.one(pad(board),'net')[:]=['net','2','"PADLESS"'];sx.write(source,board)
            with self.assertRaisesRegex(p.Rejected,'lacks.*witness'):p.preflight(source)

    def test_final_artifact_is_mandatory_rederived_and_rejects_type_tampering(self):
        board,project=fixture()
        with tempfile.TemporaryDirectory() as root:
            output=Path(root).resolve();candidate=output/'owned.kicad_pcb'
            sx.write(candidate,board);candidate.with_suffix('.kicad_pro').write_text(json.dumps(project))
            with self.assertRaisesRegex(p.Rejected,'missing or changed'):p.check_legacy_zone_evidence(output,board,candidate)
            artifact=output/'legacy-zone-witness.json';record=p.legacy_zone_evidence(board,candidate)
            p.save_json(artifact,record);p.check_legacy_zone_evidence(output,board,candidate)
            pins=record['implementation_sha256']
            p.check_legacy_zone_evidence(output,board,candidate,implementation=pins)
            for missing in ('autorouter/legacy_zone.py','autorouter/board_floor.py'):
                partial={name:pin for name,pin in pins.items() if name!=missing}
                with self.assertRaisesRegex(p.Rejected,'provenance'):
                    p.check_legacy_zone_evidence(output,board,candidate,implementation=partial)
            changed=copy.deepcopy(record);changed['native_enforcement_claimed']=0;p.save_json(artifact,changed)
            with self.assertRaisesRegex(p.Rejected,'changed'):p.check_legacy_zone_evidence(output,board,candidate)
            p.save_json(artifact,record)
            sx.one(pad(board),'at')[1]='1';sx.write(candidate,board)
            with self.assertRaisesRegex(p.Rejected,'changed'):p.check_legacy_zone_evidence(output,board,candidate)


if __name__ == '__main__': unittest.main()
