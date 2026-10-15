"""Pure scope/geometry/receipt controls; no native routing evidence is claimed."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from autorouter import pipeline as p, sexpr as sx
import test_netclass as mapping_controls
import test_result as result_controls


class NetclassPipelineControls(unittest.TestCase):
    def setUp(self):
        scratch=Path(__file__).resolve().parents[1]/'.cache/netclass-tests'
        scratch.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.board=Path(self.temp.name)/'fixture.kicad_pcb'
        self.tree=sx.parse('(kicad_pcb (version 20260206) (layers (0 "F.Cu" signal) (2 "B.Cu" signal)) (segment (start 0 0) (end 1 0) (width 0.5) (layer "F.Cu") (net "GND")) (via (at 1 0) (size 1.6) (drill 0.6) (layers "F.Cu" "B.Cu") (net "GND")))')
        _,self.native,self.project=mapping_controls.fixtures()
        self.write()

    def write(self):
        sx.write(self.board,self.tree)
        self.board.with_suffix('.kicad_pro').write_text(json.dumps(self.project))
        self.native.update(source=str(self.board),board_sha256=p.sha(self.board),
                           project_sha256=p.sha(self.board.with_suffix('.kicad_pro')),board_saved=False)

    def audit(self,protected=()):
        return p.audit_candidate_netclasses(self.board,protected,self.native)

    def test_literal_two_class_preflight(self):
        self.assertEqual(p.preflight(self.board),self.tree)
        self.assertEqual(p.netclass_policy(self.board)['mode'],'literal_two_class')

    def test_default_only_legacy_scope_unchanged(self):
        self.board.with_suffix('.kicad_pro').write_text('{}')
        self.assertIsNone(p.netclass_policy(self.board))
        self.assertEqual(p.preflight(self.board),self.tree)

    def test_four_layer_multiclass_rejected(self):
        sx.one(self.tree,'layers').extend([['4','"In1.Cu"','signal'],['6','"In2.Cu"','signal']])
        self.write()
        with self.assertRaisesRegex(p.Rejected,'two copper layers'): p.preflight(self.board)

    def test_unknown_class_binding_rejected(self):
        self.project['net_settings']['netclass_patterns'][0]['pattern']='GND*'
        self.write()
        with self.assertRaisesRegex(p.Rejected,'literal identifier'): p.preflight(self.board)

    def test_exact_dimensions_pass(self):
        self.assertEqual(self.audit()['route_dimensions']['checked'],{'segments':1,'arcs':0,'vias':1,'protected':0})

    def test_narrow_track_above_board_floor_rejected(self):
        sx.one(p.routes(self.tree)[0],'width')[1]='0.3'
        self.write()
        self.assertGreater(0.3,self.project['board']['design_settings']['rules']['min_track_width'])
        with self.assertRaisesRegex(p.Rejected,'track differs'): self.audit()

    def test_wider_track_also_rejected(self):
        sx.one(p.routes(self.tree)[0],'width')[1]='0.6'
        self.write()
        with self.assertRaisesRegex(p.Rejected,'track differs'): self.audit()

    def test_via_diameter_and_drill_targets(self):
        for key,value in [('size','1.5'),('drill','0.55')]:
            with self.subTest(key=key):
                tree=copy.deepcopy(self.tree)
                sx.one(p.routes(tree)[1],key)[1]=value
                with self.assertRaisesRegex(p.Rejected,'via differs'): p.audit_route_dimensions(tree,[],self.native)

    def test_partial_span_via_rejected(self):
        sx.one(p.routes(self.tree)[1],'layers')[2]='"In1.Cu"'
        with self.assertRaisesRegex(p.Rejected,'via layer span'): p.audit_route_dimensions(self.tree,[],self.native)

    def test_unchanged_protected_width_is_exempt(self):
        route=p.routes(self.tree)[0]
        sx.one(route,'width')[1]='0.2'
        self.write()
        self.assertEqual(self.audit([copy.deepcopy(route)])['route_dimensions']['checked']['protected'],1)

    def test_edited_protected_route_not_exempt(self):
        route=p.routes(self.tree)[0]
        protected=[copy.deepcopy(route)]
        sx.one(route,'width')[1]='0.3'
        self.write()
        with self.assertRaisesRegex(p.Rejected,'track differs'): self.audit(protected)

    def test_numeric_native_net_atoms_map_to_name(self):
        self.tree.append(['net','42','"GND"'])
        for route in p.routes(self.tree): sx.one(route,'net')[1]='42'
        self.write()
        self.assertTrue(self.audit()['route_dimensions']['passed'])

    def test_unknown_route_net_rejected(self):
        sx.one(p.routes(self.tree)[0],'net')[1]='"UNKNOWN"'
        self.write()
        with self.assertRaisesRegex(p.Rejected,'unknown native net'): self.audit()

    def test_arc_target_checked(self):
        p.routes(self.tree)[0][0]='arc'
        self.write()
        self.assertEqual(self.audit()['route_dimensions']['checked']['arcs'],1)
        sx.one(p.routes(self.tree)[0],'width')[1]='0.3'
        self.write()
        with self.assertRaisesRegex(p.Rejected,'track differs'): self.audit()

    def test_stale_board_and_project_maps_rejected(self):
        for key in ['board_sha256','project_sha256']:
            with self.subTest(key=key):
                altered=copy.deepcopy(self.native);altered[key]='0'*64
                with self.assertRaisesRegex(p.Rejected,'not bound'): p.audit_candidate_netclasses(self.board,[],altered)

    def test_native_default_fallback_does_not_satisfy_targets(self):
        self.native['nets'][1]['class']='Default'
        with self.assertRaisesRegex(ValueError,'literal assignment'): self.audit()


class NetclassReceiptControls(unittest.TestCase):
    def setUp(self):
        # Reuse explicitly synthetic native evidence; this tests consistency only.
        self.fixture=result_controls.ResultFreshnessTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f=self.fixture
        _,self.native,project=mapping_controls.fixtures()
        f.source.with_suffix('.kicad_pro').write_text(json.dumps(project))
        tree=sx.read(f.source)
        sx.one(p.routes(tree)[1],'width')[1]='0.5'
        sx.write(f.source,tree)
        for directory in [f.run/'snapshot',f.run/'candidate',f.run/'final-drc-input']:
            shutil.copy2(f.source,directory/f.source.name)
            shutil.copy2(f.source.with_suffix('.kicad_pro'),directory/f.source.with_suffix('.kicad_pro').name)
        f.data.update(source_hashes=p.tree_hash(f.source.parent),candidate_sha256=p.sha(f.candidate),baseline='C-prototype')
        f.binding.update(before=p.tree_hash(f.candidate.parent),after=p.tree_hash(f.candidate.parent))
        (f.run/'final-drc-binding.json').write_text(json.dumps(f.binding))
        f.data['steps'][0]['validated_input_sha256']=p.sha(f.candidate)
        # Source/project edits are intentional fixture setup. Rebuild only its
        # authored transport now; later map/process tampering stays untouched.
        from tests.normal_prl_fixture import refresh_authored_normal_import
        refresh_authored_normal_import(f.run,f.data,test_root=f.root)
        self.native.update(source=str(f.candidate),board_sha256=p.sha(f.candidate),project_sha256=p.sha(f.candidate.with_suffix('.kicad_pro')),board_saved=False)
        (f.run/'final-netclasses.json').write_text(json.dumps(self.native))
        protected=[route for route in p.routes(tree) if p.locked(route)]
        audit=p.audit_candidate_netclasses(f.candidate,protected,self.native)
        audit['native_map_file_sha256']=p.sha(f.run/'final-netclasses.json')
        (f.run/'final-netclass-audit.json').write_text(json.dumps(audit))
        process={'name':'final-netclasses','cwd':str(f.run),'exit_code':0,'status':'success','cleanup_complete':True,
                 'argv':[str(p.c.PYTHON),str(p.c.ROOT/'autorouter/native.py'),'netclasses',str(f.candidate),str(f.run/'final-netclasses.json')],
                 'wall_seconds':0.1,'cpu_seconds':0.1,'monitor_cpu_seconds':0.01}
        (f.run/'final-netclasses-process.json').write_text(json.dumps(process))
        f.data['steps'].append(process)
        f.data.update(child_cpu_seconds=1.1,monitor_cpu_seconds=0.11,total_cpu_seconds=1.41)
        f.save_receipt()

    def test_bound_multiclass_receipt_passes_consistency(self):
        self.assertTrue(p.check_result(self.fixture.receipt)['current'])

    def test_missing_mapping_fails_closed(self):
        (self.fixture.run/'final-netclasses.json').unlink()
        with self.assertRaises(FileNotFoundError): p.check_result(self.fixture.receipt)

    def test_forged_target_map_fails_even_with_rehashed_map(self):
        f=self.fixture
        self.native['nets'][1]['width_nm']=200000
        (f.run/'final-netclasses.json').write_text(json.dumps(self.native))
        with self.assertRaisesRegex(ValueError,'differs from original'): p.check_result(f.receipt)

    def test_missing_native_mapping_process_fails(self):
        (self.fixture.run/'final-netclasses-process.json').unlink()
        with self.assertRaises(FileNotFoundError): p.check_result(self.fixture.receipt)

    def test_changed_native_mapping_argv_fails(self):
        f=self.fixture
        path=f.run/'final-netclasses-process.json'
        process=json.loads(path.read_text());process['argv'][-2]='/different/source.kicad_pcb'
        path.write_text(json.dumps(process))
        with self.assertRaisesRegex(p.Rejected,'provenance'): p.check_result(f.receipt)
