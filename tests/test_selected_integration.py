"""Captured selection and scope guards; native qualification is separate."""
import copy,json,shutil,tempfile,unittest,uuid
from pathlib import Path
from autorouter import config as c,pipeline as p,preferences as pref,sexpr as sx
from autorouter.__main__ import preview


class SelectedIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=c.ROOT/'.runs');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.project=self.root/'project'
        shutil.copytree(c.ROOT/'fixtures/smoke',self.project);self.board=self.project/'smoke.kicad_pcb'
        self.choices={'scope':'selected_nets','nets':['SIGNAL_A'],'profile':'completion-only'}

    def test_capture_keeps_exact_selection_and_detects_rehashed_disagreement(self):
        raw=pref.snapshot(overrides=self.choices);effective=pref.readback(raw)
        self.assertEqual(effective['nets'],['SIGNAL_A'])
        record=json.loads(raw);record['effective']['nets']=['SIGNAL_B']
        with self.assertRaises(pref.PreferenceError):pref.readback(json.dumps(record).encode())

    def test_incompatible_or_ignored_choices_reject_before_output(self):
        changes=[{'profile':'tuned'},{'guidance':'placement-clearance-v1'},
                 {'layers':['F.Cu']},{'scope':'whole_board_unlocked_routing'},
                 {'nets':[]},{'nets':['SIGNAL_A','SIGNAL_A']}]
        for change in changes:
            target=self.root/'not-created'
            with self.subTest(change=change),self.assertRaises(ValueError):
                p.route('not-read.kicad_pcb',target,preference_overrides={**self.choices,**change})
            self.assertFalse(target.exists())

    def test_preview_resolves_known_names_and_protects_other_copper(self):
        tree=sx.read(self.board)
        for name,lock,y in [('SIGNAL_A',False,'10'),('SIGNAL_A',True,'12'),('SIGNAL_B',False,'20')]:
            route=['segment',['start','10',y],['end','15',y],['width','0.25'],['layer','"F.Cu"'],['net',json.dumps(name)],['uuid',json.dumps(str(uuid.uuid5(uuid.NAMESPACE_URL,'selection-'+y)))]]
            if lock:route.append(['locked','yes'])
            tree.append(route)
        sx.write(self.board,tree);before=p.tree_hash(self.project)
        result=preview(self.board,overrides=self.choices)
        self.assertEqual((result['protected_route_items'],result['rerouted_route_items']),(2,1))
        self.assertFalse(result['native_validation_performed']);self.assertEqual(p.tree_hash(self.project),before)
        with self.assertRaises(p.Rejected):preview(self.board,overrides={**self.choices,'nets':['UNKNOWN']})

    def test_selection_markers_cannot_downgrade_to_whole_scope(self):
        for marker in ['selected_net_binding','selected_net_audit']:
            with self.subTest(marker=marker),self.assertRaises(p.Rejected):
                p.protected_for_record({'scope':'whole_board_unlocked_routing',marker:{}},sx.read(self.board))
        with self.assertRaises(ValueError):p.protected_for_record({'scope':'selected_nets'},sx.read(self.board))

    def test_native_parity_is_required_exactly_when_complete_input_is_present(self):
        base={'scope':'selected_nets','source':str(self.board),'source_hashes':p.tree_hash(self.project),
              'schematic_parity':'unavailable: no native schematic in source project'}
        self.assertFalse(p.selected_parity_required(base))
        complete=copy.deepcopy(base);complete['source_hashes']['smoke.kicad_sch']='bound-source-hash'
        with self.assertRaises(p.Rejected):p.selected_parity_required(complete)
        complete['schematic_parity']='checked by final native DRC';self.assertTrue(p.selected_parity_required(complete))

    def test_export_cannot_disclaim_or_drop_required_selected_parity(self):
        from autorouter import review_export as e
        report={'scope':'selected_nets','schematic_parity':'checked by final native DRC'}
        for declaration in (None,'not checked','unavailable: no native schematic in source project'):
            with self.subTest(declaration=declaration),self.assertRaisesRegex(p.Rejected,'parity declaration'):
                e.check_stage(self.root,{'schematic_parity':declaration},{},report,None,None,None)


if __name__=='__main__':unittest.main()
