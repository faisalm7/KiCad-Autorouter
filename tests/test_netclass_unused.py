"""Authored unused-class source/Native/DSN consistency controls, not routing proof."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from autorouter import netclass as nc,sexpr as sx
from autorouter.adapter import _dump_dsn
import test_netclass as existing


def fixture(name='5mil'):
    tree,native,project=existing.fixtures(default_only=True)
    # Deliberately different, below the track floor, but fully specified. No
    # actual net may use it. The source definition itself must remain intact.
    project['net_settings']['classes'].append({'name':name,'track_width':0.127,
        'clearance':0.25,'via_diameter':1.6,'via_drill':0.6})
    return tree,native,project


class UnusedClassControls(unittest.TestCase):
    def test_full_original_project_native_and_dsn_audit_without_projection(self):
        tree,native,project=fixture();before=copy.deepcopy((tree,native,project))
        verified=nc.audit_native(native,project)
        mapping=nc.audit_mapping(tree,native,project)
        self.assertTrue(verified['passed']);self.assertTrue(mapping['passed'])
        self.assertEqual(mapping['policy'],{'mode':'literal_two_class','literal_assignments':{}})
        self.assertEqual(mapping['membership'],{'DATA':'kicad_default','GND':'kicad_default'})
        self.assertEqual((tree,native,project),before)
        with tempfile.TemporaryDirectory() as folder:
            dsn=Path(folder)/'task.dsn';dsn.write_bytes(_dump_dsn(tree).encode())
            result=nc.audit_dsn(dsn,native,project)
            raw=json.dumps(project,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
            self.assertEqual(result['project_json_sha256'],hashlib.sha256(raw).hexdigest())
            self.assertEqual(len(project['net_settings']['classes']),2)
            self.assertFalse(result['source_modified']);self.assertFalse(result['routing_accepted'])

    def test_absent_or_empty_binding_fields_require_every_native_net_default(self):
        for patterns in (None,[]):
            for assignments in (None,{}):
                tree,native,project=fixture('Idle_33')
                project['net_settings'].update(netclass_patterns=patterns,netclass_assignments=assignments)
                self.assertTrue(nc.audit_mapping(tree,native,project)['passed'])
        tree,native,project=fixture()
        for bad_class in ('5mil','Default,5mil','Unknown'):
            with self.subTest(bad_class=bad_class):
                altered=copy.deepcopy(native);altered['nets'][0]['class']=bad_class
                with self.assertRaisesRegex(ValueError,'Native class resolution'):nc.audit_native(altered,project)
        # No copper pads is not evidence that a real nondefault net is unused.
        altered=copy.deepcopy(native);altered['nets'].append({'name':'UNPADDED','netcode':3,'class':'5mil',
            'width_nm':127000,'clearance_nm':250000,'via_diameter_nm':1600000,'via_drill_nm':600000,'copper_pad_count':0})
        with self.assertRaisesRegex(ValueError,'Native class resolution'):nc.audit_native(altered,project)

    def test_active_numeric_name_explicit_or_pattern_binding_is_still_unsupported(self):
        for assignments,patterns in (({'DATA':['5mil']},[]),(None,[{'pattern':'DATA','netclass':'5mil'}])):
            tree,native,project=fixture();project['net_settings'].update(netclass_assignments=assignments,netclass_patterns=patterns)
            with self.assertRaises(ValueError):nc.qualify_project(project)
            native['nets'][0].update(**{'class':'5mil','width_nm':127000,'via_diameter_nm':1600000})
            with self.assertRaises(ValueError):nc.audit_mapping(tree,native,project)
        # Existing active alphabetic classes retain the actual-resolution gate.
        tree,native,project=existing.fixtures()
        self.assertTrue(nc.audit_mapping(tree,native,project)['passed'])
        for row in native['nets']:row.update(**{'class':'Default','width_nm':400000,'via_diameter_nm':1400000})
        with self.assertRaises(ValueError):nc.audit_native(native,project)

    def test_unused_definition_names_dimensions_and_tuning_are_not_ignored(self):
        for name in ('','5-mil','5 mil','5mil,Default','kicad_default','KiCad_Default','default','DEFAULT','a'*65):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):nc.audit_native(fixture(name)[1],fixture(name)[2])
        for field,value in (('track_width',None),('track_width',float('nan')),('clearance',True),
                ('via_diameter',0),('via_drill',1.6),('via_drill',0.6000001),('tuning_profile','matched'),('tuning_profiles',['x'])):
            with self.subTest(field=field,value=value):
                _,native,project=fixture();project['net_settings']['classes'][1][field]=value
                with self.assertRaises(ValueError):nc.audit_native(native,project)
        _,native,project=fixture();del project['net_settings']['classes'][1]['clearance']
        with self.assertRaises(ValueError):nc.audit_native(native,project)
        for patterns in (False,{},''):
            _,native,project=fixture();project['net_settings']['netclass_patterns']=patterns
            with self.assertRaises(ValueError):nc.audit_native(native,project)
        _,native,project=fixture();project['tuning_profiles']={'tuning_profiles_impedance_geometric':[{}]}
        with self.assertRaises(ValueError):nc.audit_native(native,project)

    def test_unused_source_definition_is_not_an_exported_or_active_dsn_class(self):
        for mutation in ('extra-class','moved-member','wrong-width','wrong-via'):
            with self.subTest(mutation=mutation):
                tree,native,project=fixture();network=sx.one(tree,'network');default=sx.children(network,'class')[0]
                if mutation in ('extra-class','moved-member'):
                    extra=copy.deepcopy(default);extra[1]='5mil'
                    for name in ('DATA','GND'):
                        if name in extra:extra.remove(name)
                    if mutation=='moved-member':default.remove('DATA');extra.insert(2,'DATA')
                    sx.one(sx.one(extra,'rule'),'width')[1]='127';network.append(extra)
                elif mutation=='wrong-width':sx.one(sx.one(default,'rule'),'width')[1]='127'
                else:sx.one(sx.one(default,'circuit'),'use_via')[1]='"Via[0-1]_1600:600_um"'
                with self.assertRaises(ValueError):nc.audit_mapping(tree,native,project)
        # Existing single-Default path and arbitrary inactive-class dimensions
        # do not modify the original active Default targets.
        self.assertTrue(nc.audit_mapping(*existing.fixtures(default_only=True))['passed'])
        tree,native,project=fixture();native['nets'][0]['width_nm']=127000
        with self.assertRaisesRegex(ValueError,'original project value'):nc.audit_native(native,project)

if __name__=='__main__':unittest.main()
