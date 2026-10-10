"""Pure mapping/eligibility controls; these are not native routing evidence."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from autorouter.adapter import _parse_dsn, _dump_dsn
from autorouter import sexpr as sx

from autorouter import netclass as m


def fixtures(default_only=False):
    default = {'name':'Default','track_width':0.4,'clearance':0.25,'via_diameter':1.4,'via_drill':0.6}
    power = {'name':'Power','track_width':0.5,'clearance':0.25,'via_diameter':1.6,'via_drill':0.6}
    project = {'net_settings':{'classes':[default] if default_only else [default,power],
                              'netclass_assignments':None,
                              'netclass_patterns':[] if default_only else [{'pattern':'GND','netclass':'Power'},{'pattern':'VCC','netclass':'Power'}]},
               'board':{'design_settings':{'rules':{'min_track_width':0.2,'min_clearance':0.2,'min_via_diameter':0.9,'min_through_hole_diameter':0.5}}}}
    native = {'schema':1,'native_version':'10.0.0','units':'integer nanometres','nets':[
        {'name':'DATA','netcode':1,'class':'Default','width_nm':400000,'clearance_nm':250000,'via_diameter_nm':1400000,'via_drill_nm':600000,'copper_pad_count':1},
        {'name':'GND','netcode':2,'class':'Default' if default_only else 'Power','width_nm':400000 if default_only else 500000,'clearance_nm':250000,'via_diameter_nm':1400000 if default_only else 1600000,'via_drill_nm':600000,'copper_pad_count':1}]}
    dsn = '''(pcb "synthetic"
      (parser (string_quote ")) (unit um) (resolution um 10)
      (structure (layer F.Cu (type signal)) (layer B.Cu (type signal))
        (via "Via[0-1]_1400:600_um" "Via[0-1]_1600:600_um"))
      (library
        (padstack "Via[0-1]_1400:600_um" (shape (circle F.Cu 1400)) (shape (circle B.Cu 1400)) (attach off))
        (padstack "Via[0-1]_1600:600_um" (shape (circle F.Cu 1600)) (shape (circle B.Cu 1600)) (attach off)))
      (network (net DATA (pins J1-1)) (net GND (pins J2-1))
        (class kicad_default DATA (circuit (use_via "Via[0-1]_1400:600_um")) (rule (width 400) (clearance 250)))
        (class Power GND (circuit (use_via "Via[0-1]_1600:600_um")) (rule (width 500) (clearance 250)))))'''
    tree = _parse_dsn(dsn)
    if default_only:
        network = sx.one(tree,'network')
        cls = sx.children(network,'class')
        cls[0].insert(3,'GND'); network.remove(cls[1])
    return tree,native,project


class NetclassControls(unittest.TestCase):
    def setUp(self):
        self.tree,self.native,self.project=fixtures()
    def audit(self):
        return m.audit_mapping(self.tree,self.native,self.project)
    def test_two_class_exact_mapping(self):
        self.assertTrue(self.audit()['passed'])
    def test_single_default(self):
        self.assertTrue(m.audit_mapping(*fixtures(True))['passed'])
    def test_renaming_invariance(self):
        # No filename or GND/VCC heuristic: two renamed nets bind to a renamed class.
        self.project['net_settings']['classes'][1]['name']='Supply'
        self.project['net_settings']['netclass_patterns']=[{'pattern':'PWR_A','netclass':'Supply'},{'pattern':'RETURN_B','netclass':'Supply'}]
        self.native['nets'][0].update(name='PWR_A',**{'class':'Supply','width_nm':500000,'via_diameter_nm':1600000})
        self.native['nets'][1].update(name='RETURN_B',**{'class':'Supply'})
        network=sx.one(self.tree,'network');nets=sx.children(network,'net')
        nets[0][1]='PWR_A';nets[1][1]='RETURN_B'
        classes=sx.children(network,'class');classes[0].remove('DATA')
        classes[1][1]='Supply';classes[1][2]='PWR_A';classes[1].insert(3,'RETURN_B')
        result=self.audit()
        self.assertEqual(result['membership'],{'PWR_A':'Supply','RETURN_B':'Supply'})
    def test_wrong_membership(self):
        classes=sx.children(sx.one(self.tree,'network'),'class')
        classes[1].remove('GND');classes[0].insert(3,'GND')
        with self.assertRaisesRegex(ValueError,'DSN class differs'):self.audit()
    def test_missing_membership(self):
        sx.children(sx.one(self.tree,'network'),'class')[1].remove('GND')
        with self.assertRaisesRegex(ValueError,'missing from explicit'):self.audit()
    def test_duplicate_membership(self):
        sx.children(sx.one(self.tree,'network'),'class')[1].insert(3,'GND')
        with self.assertRaisesRegex(ValueError,'Duplicate class member'):self.audit()
    def test_via_copper_geometry_mismatch(self):
        stack=sx.children(sx.one(self.tree,'library'),'padstack')[1]
        sx.one(sx.children(stack,'shape')[0],'circle')[2]='1500'
        with self.assertRaisesRegex(ValueError,'actual copper shape'):self.audit()
    def test_missing_via_layer(self):
        stack=sx.children(sx.one(self.tree,'library'),'padstack')[1]
        stack.remove(sx.children(stack,'shape')[1])
        with self.assertRaisesRegex(ValueError,'layer coverage'):self.audit()
    def test_missing_via_stack(self):
        lib=sx.one(self.tree,'library');lib.remove(sx.children(lib,'padstack')[1])
        with self.assertRaisesRegex(ValueError,'padstack'):self.audit()
    def test_narrow_class_width(self):
        cls=sx.children(sx.one(self.tree,'network'),'class')[1]
        sx.one(sx.one(cls,'rule'),'width')[1]='250'
        with self.assertRaisesRegex(ValueError,'DSN class differs'):self.audit()
    def test_narrow_class_clearance(self):
        cls=sx.children(sx.one(self.tree,'network'),'class')[1]
        sx.one(sx.one(cls,'rule'),'clearance')[1]='125'
        with self.assertRaisesRegex(ValueError,'DSN class differs'):self.audit()
    def test_regex_pattern_rejected(self):
        self.project['net_settings']['netclass_patterns'][0]['pattern']='GND.*'
        with self.assertRaisesRegex(ValueError,'literal identifier'):self.audit()
    def test_explicit_assignment_rejected(self):
        self.project['net_settings']['netclass_assignments']={'DATA':['Power']}
        with self.assertRaisesRegex(ValueError,'assignments not qualified'):self.audit()
    def test_native_default_fallback_rejected(self):
        self.native['nets'][1]['class']='Default'
        with self.assertRaisesRegex(ValueError,'native class resolution|Native class resolution'):self.audit()
    def test_native_fractional_dimensions_rejected(self):
        self.native['nets'][0]['width_nm']=400000.0
        with self.assertRaisesRegex(ValueError,'integer nanometres'):self.audit()
    def test_terminal_loss_rejected(self):
        sx.one(sx.children(sx.one(self.tree,'network'),'net')[0],'pins').pop()
        with self.assertRaisesRegex(ValueError,'terminal count'):self.audit()
    def test_duplicate_class_definition(self):
        network=sx.one(self.tree,'network');network.append(copy.deepcopy(sx.children(network,'class')[1]))
        with self.assertRaisesRegex(ValueError,'Duplicate DSN class'):self.audit()
    def test_unknown_empty_class(self):
        network=sx.one(self.tree,'network');extra=copy.deepcopy(sx.children(network,'class')[1]);extra[1]='Unexpected';extra.remove('GND');network.append(extra)
        with self.assertRaisesRegex(ValueError,'Unknown DSN class'):self.audit()
    def test_wrong_drill_in_consistent_padstack_id(self):
        old='"Via[0-1]_1600:600_um"';new='"Via[0-1]_1600:500_um"'
        def replace(node):
            if isinstance(node,list):
                for i,x in enumerate(node):
                    if x==old:node[i]=new
                    elif isinstance(x,list):replace(x)
        replace(self.tree)
        with self.assertRaisesRegex(ValueError,'DSN class differs'):self.audit()
    def test_malformed_empty_pattern_value(self):
        tree,native,project=fixtures(True);project['net_settings']['netclass_patterns']=False
        with self.assertRaisesRegex(ValueError,'pattern list'):m.audit_mapping(tree,native,project)
    def test_board_floor_violation_rejected(self):
        self.project['board']['design_settings']['rules']['min_track_width']=0.45
        with self.assertRaisesRegex(ValueError,'below original board floor'):self.audit()
    def test_duplicate_layer_rejected(self):
        structure=sx.one(self.tree,'structure')
        structure.append(copy.deepcopy(sx.children(structure,'layer')[0]))
        with self.assertRaisesRegex(ValueError,'two-layer'):self.audit()
    def test_duplicate_via_declaration_rejected(self):
        vias=sx.one(sx.one(self.tree,'structure'),'via');vias.append(vias[1])
        with self.assertRaisesRegex(ValueError,'Duplicate DSN via'):self.audit()
    def test_invalid_board_floors_rejected(self):
        for invalid in (-0.1,True,float('nan'),'0.2'):
            with self.subTest(value=invalid):
                self.project['board']['design_settings']['rules']['min_track_width']=invalid
                with self.assertRaises(ValueError):self.audit()
    def test_impossible_project_via_rejected(self):
        self.project['net_settings']['classes'][1]['via_drill']=1.7
        with self.assertRaisesRegex(ValueError,'smaller than copper'):self.audit()
    def test_class_rule_override_rejected(self):
        cls=sx.children(sx.one(self.tree,'network'),'class')[1]
        sx.one(cls,'rule').append(['clearance','125',['type','smd_smd']])
        with self.assertRaisesRegex(ValueError,'duplicate singleton'):self.audit()
    def test_native_extra_pattern_match_rejected(self):
        # Exact literal binding is checked against native results, not inferred.
        self.native['nets'][0].update(**{'class':'Power','width_nm':500000,'via_diameter_nm':1600000})
        with self.assertRaisesRegex(ValueError,'literal assignment'):self.audit()
    def test_malformed_class_dimensions_rejected(self):
        cls=sx.children(sx.one(self.tree,'network'),'class')[1]
        for value in ('NaN','Infinity','not_a_number','500.0001'):
            with self.subTest(value=value):
                sx.one(sx.one(cls,'rule'),'width')[1]=value
                with self.assertRaises(ValueError):self.audit()
    def test_audit_binds_original_dsn_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'task.dsn';raw=_dump_dsn(self.tree).encode();path.write_bytes(raw)
            result=m.audit_dsn(path,self.native,self.project)
            self.assertEqual(result['dsn_sha256'],hashlib.sha256(raw).hexdigest())
            self.assertEqual(path.read_bytes(),raw)
            self.assertFalse(result['source_modified'])
            self.assertFalse(result['routing_accepted'])
            link=path.with_name('linked.dsn');link.symlink_to(path)
            with self.assertRaisesRegex(ValueError,'regular DSN'):m.audit_dsn(link,self.native,self.project)
    def test_native_only_audit_and_dimension_rejection(self):
        result=m.audit_native(self.native,self.project)
        self.assertEqual(result['native_nets'],2)
        self.assertEqual(result['nets'],self.native['nets'])
        result['nets'][0]['width_nm']=1
        self.assertEqual(self.native['nets'][0]['width_nm'],400000)
        self.native['nets'][1]['via_diameter_nm']=1400000
        with self.assertRaisesRegex(ValueError,'original project value'):m.audit_native(self.native,self.project)
    def test_native_only_membership_rejection(self):
        self.native['nets'][1]['name']='GND_DUP'
        with self.assertRaisesRegex(ValueError,'literal assignment'):m.audit_native(self.native,self.project)
    def test_native_only_malformed_schema_rejection(self):
        for value in (False,True,0,2,None):
            with self.subTest(value=value):
                self.native['schema']=value
                with self.assertRaisesRegex(ValueError,'native version'):m.audit_native(self.native,self.project)


if __name__=='__main__': unittest.main(verbosity=2)
