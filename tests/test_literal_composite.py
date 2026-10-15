"""Authored scalar/DSN controls only; no Native execution or routing proof."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from autorouter import netclass as m, pipeline as p, sexpr as sx
from test_netclass import fixtures


def composite():
    tree, native, project = fixtures()
    for cls in project['net_settings']['classes']:
        cls['priority'] = 2147483647 if cls['name'] == 'Default' else 0
    row = native['nets'][1]
    row['class'] = 'Power,Default'
    row['parameter_parents'] = {key: dict(name='Power', value_nm=row[key], specified=True, priority=0)
        for key in ('width_nm','clearance_nm','via_diameter_nm','via_drill_nm')}
    sx.children(sx.one(tree,'network'),'class')[1][1] = 'Power,Default'
    return tree, native, project


class LiteralCompositeControls(unittest.TestCase):
    def test_verified_opaque_identity_and_inputs_unchanged(self):
        tree, native, project = composite(); before = copy.deepcopy((tree,native,project))
        audit = m.audit_mapping(tree,native,project)
        self.assertEqual(audit['membership']['GND'],'Power,Default')
        self.assertEqual(audit['policy']['mode'],'literal_two_class')
        self.assertEqual((tree,native,project),before)

    def test_historical_plain_mapping_needs_no_new_parent_metadata(self):
        self.assertTrue(m.audit_mapping(*fixtures())['passed'])
        self.assertTrue(m.audit_mapping(*fixtures(True))['passed'])

    def test_default_fallback_and_unqualified_encodings_refused(self):
        for encoded in ('Default','Default,Power','Power,Power','Power,Default,Default','Power,Other','Power,','Power, Default'):
            with self.subTest(encoded=encoded):
                tree,native,project=composite();native['nets'][1]['class']=encoded
                with self.assertRaises(ValueError):m.audit_mapping(tree,native,project)
        tree,native,project=composite();native['nets'][0]['class']='Default,Default'
        with self.assertRaises(ValueError):m.audit_mapping(tree,native,project)

    def test_composite_on_unassigned_net_refused(self):
        tree,native,project=composite();native['nets'][1]['name']='OTHER'
        with self.assertRaises(ValueError):m.audit_mapping(tree,native,project)

    def test_all_four_parameter_parents_are_mandatory_and_exact(self):
        for key in ('width_nm','clearance_nm','via_diameter_nm','via_drill_nm'):
            for field,value in (('name','Default'),('specified',False),('specified',1),('priority',1),('priority',False),('value_nm',1),('value_nm',500000.0)):
                with self.subTest(key=key,field=field,value=value):
                    tree,native,project=composite();native['nets'][1]['parameter_parents'][key][field]=value
                    with self.assertRaises(ValueError):m.audit_mapping(tree,native,project)
            tree,native,project=composite();del native['nets'][1]['parameter_parents'][key]
            with self.assertRaises(ValueError):m.audit_mapping(tree,native,project)

    def test_explicit_source_priorities_dimensions_and_literal_scope(self):
        for cls in (0,1):
            tree,native,project=composite();del project['net_settings']['classes'][cls]['priority']
            with self.assertRaises(ValueError):m.audit_mapping(tree,native,project)
        for key in ('track_width','clearance','via_diameter','via_drill'):
            tree,native,project=composite();del project['net_settings']['classes'][1][key]
            with self.assertRaises(ValueError):m.audit_mapping(tree,native,project)
        tree,native,project=composite();project['net_settings']['netclass_patterns'][0]['pattern']='GND.*'
        with self.assertRaises(ValueError):m.audit_mapping(tree,native,project)

    def test_native_and_source_dimensions_cannot_drift(self):
        for key in ('width_nm','clearance_nm','via_diameter_nm','via_drill_nm'):
            tree,native,project=composite();native['nets'][1][key]+=1
            native['nets'][1]['parameter_parents'][key]['value_nm']+=1
            with self.assertRaises(ValueError):m.audit_mapping(tree,native,project)
        tree,native,project=composite();project['board']['design_settings']['rules']['min_track_width']=0.6
        with self.assertRaises(ValueError):m.audit_mapping(tree,native,project)

    def test_dsn_identity_membership_width_and_via_cannot_be_relabelled(self):
        for field,value in (('class','Power'),('width','499'),('width','501'),('clearance','249')):
            tree,native,project=composite();cls=sx.children(sx.one(tree,'network'),'class')[1]
            if field=='class':cls[1]=value
            else:sx.one(sx.one(cls,'rule'),field)[1]=value
            with self.assertRaises(ValueError):m.audit_mapping(tree,native,project)
        tree,native,project=composite();classes=sx.children(sx.one(tree,'network'),'class');classes[1].remove('GND');classes[0].insert(3,'GND')
        with self.assertRaises(ValueError):m.audit_mapping(tree,native,project)
        tree,native,project=composite()
        def replace(node):
            for i,value in enumerate(node):
                if isinstance(value,list):replace(value)
                elif value=='"Via[0-1]_1600:600_um"':node[i]='"Via[0-1]_1600:500_um"'
        replace(tree)
        with self.assertRaises(ValueError):m.audit_mapping(tree,native,project)

    def test_bound_candidate_dimensions_and_stale_map_refused(self):
        _,native,project=composite()
        tree=sx.parse('(kicad_pcb (version 20260206) (layers (0 "F.Cu" signal) (2 "B.Cu" signal)) (segment (start 0 0) (end 1 0) (width 0.5) (layer "F.Cu") (net "GND")) (via (at 1 0) (size 1.6) (drill 0.6) (layers "F.Cu" "B.Cu") (net "GND")))')
        with tempfile.TemporaryDirectory() as tmp:
            board=Path(tmp)/'fixture.kicad_pcb';sx.write(board,tree);board.with_suffix('.kicad_pro').write_text(json.dumps(project))
            native.update(source=str(board),board_sha256=p.sha(board),project_sha256=p.sha(board.with_suffix('.kicad_pro')),board_saved=False)
            self.assertEqual(p.audit_candidate_netclasses(board,[],native)['route_dimensions']['checked']['vias'],1)
            for key,value in (('width','0.499'),('width','0.501'),('size','1.5'),('drill','0.5')):
                changed=copy.deepcopy(tree);sx.one(p.routes(changed)[0 if key=='width' else 1],key)[1]=value;sx.write(board,changed)
                with self.assertRaises(p.Rejected):p.audit_candidate_netclasses(board,[],native)
                native['board_sha256']=p.sha(board)
                with self.assertRaises(p.Rejected):p.audit_candidate_netclasses(board,[],native)
                sx.write(board,tree);native['board_sha256']=p.sha(board)
            board.with_suffix('.kicad_pro').write_text(json.dumps({**project,'changed':True}))
            with self.assertRaises(p.Rejected):p.audit_candidate_netclasses(board,[],native)
