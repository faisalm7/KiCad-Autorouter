"""Pure method lineage controls; actual Native qualification is separate."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from autorouter import config as c,pipeline as p,recovery,thermal as t


class ThermalParentPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();code=self.root/'code';code.mkdir()
        producer=code/'recovery.py';producer.write_bytes(Path(recovery.__file__).read_bytes())
        self.data=dict(schema=1,baseline='C-prototype',strategy='native_validated_thermal_bridge',
            adapter='both',scope='whole_board_unlocked_routing',engine_profile='completion-only',
            thermal_parent_policy=t.PARENT_POLICY,source=str(self.root/'source/board.kicad_pcb'),
            tools={'implementation_sha256':{'autorouter/recovery.py':p.sha(producer)}},
            budget_seconds=180,cpu_budget_seconds=180,recovery_reserve_seconds=40.,finalization_reserve_seconds=15.,
            recovery_needed=False,repair=None,candidate_sha256='a'*64)
        self.inc=dict(accepted=True,candidate_sha256='a'*64)

    def test_profile_is_selected_from_trusted_version(self):
        for version,profile in [('10.0.0','completion-only'),('10.0.7','standard')]:
            with patch.object(c,'NATIVE_VERSION',version):
                self.assertEqual(t.parent_profile(),profile)
                self.data['engine_profile']=profile
                self.assertTrue(t.check_parent_scope(self.root,self.data))
        for version in ('10.0.8','',True,None):
            with patch.object(c,'NATIVE_VERSION',version),self.assertRaises(p.Rejected):
                t.parent_profile()

    def test_current_source_cannot_delete_marker_or_broaden_scope(self):
        changes=[('thermal_parent_policy',None),('thermal_parent_policy','foreign'),
            ('schema',True),('scope','partial_completion'),('adapter','none'),
            ('strategy',None),('baseline','B1'),('engine_profile','standard'),
            ('routing_preferences',{}),('scoring_variant',None),('experimental_contact',False),
            ('budget_seconds',True),('budget_seconds',60),('cpu_budget_seconds',900),
            ('recovery_reserve_seconds',0),('finalization_reserve_seconds',0)]
        for key,value in changes:
            data=copy.deepcopy(self.data)
            if value is None and key=='thermal_parent_policy':data.pop(key)
            else:data[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(p.Rejected):
                t.check_parent_scope(self.root,data)

    def test_known_legacy_declaration_remains0_only(self):
        producer=self.root/'code/recovery.py'
        producer.write_text('"""Authored historical no-policy producer, never executed."""\n')
        self.data['tools']['implementation_sha256']['autorouter/recovery.py']=p.sha(producer)
        self.data.pop('thermal_parent_policy')
        self.assertFalse(t.check_parent_scope(self.root,self.data))
        with patch.object(c,'NATIVE_VERSION','10.0.7'),self.assertRaises(p.Rejected):
            t.check_parent_scope(self.root,self.data)
        self.data['thermal_parent_policy']=t.PARENT_POLICY
        with self.assertRaises(p.Rejected):t.check_parent_scope(self.root,self.data)

    def test_producer_bytes_must_match_captured_pin(self):
        producer=self.root/'code/recovery.py';producer.write_text(producer.read_text()+'\n')
        with self.assertRaisesRegex(p.Rejected,'producer differs'):
            t.check_parent_scope(self.root,self.data)

    def test_current_producer_cannot_repin_after_deleting_policy_declaration(self):
        producer=self.root/'code/recovery.py'
        raw=producer.read_text();declaration="THERMAL_PARENT_POLICY = 'native-thermal-parent-selection-v1'\n"
        self.assertEqual(raw.count(declaration),1)
        producer.write_text(raw.replace(declaration,''))
        self.data['tools']['implementation_sha256']['autorouter/recovery.py']=p.sha(producer)
        self.data.pop('thermal_parent_policy')
        with self.assertRaisesRegex(p.Rejected,'policy missing'):
            t.check_parent_scope(self.root,self.data)

    def test_accepted_incumbent_cannot_be_replaced_or_claim_repair(self):
        t.check_parent_selection(self.root,self.data,self.inc)
        for key,value in [('recovery_needed',True),('recovery_needed',0),
                          ('repair',{}),('candidate_sha256','b'*64)]:
            data=copy.deepcopy(self.data);data[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(p.Rejected,'accepted-incumbent'):
                t.check_parent_selection(self.root,data,self.inc)
        (self.root/'recovery').mkdir()
        with self.assertRaisesRegex(p.Rejected,'accepted-incumbent'):
            t.check_parent_selection(self.root,self.data,self.inc)

    def test_repair_flag_and_retained_receipt_are_mandatory(self):
        directory=self.root/'recovery';directory.mkdir()
        repair=dict(status='validated_trial_candidate',validation_passed=True,
            routing_accepted=False,comparison_eligible=False,geometry_receipt='foreign',proposal_receipt='foreign')
        p.save_json(directory/'repair.json',repair)
        inc=dict(accepted=False)
        # These failures precede all geometry/Native readers; a JSON flag alone
        # cannot turn either branch into a selected candidate.
        for field,value in [('recovery_needed',False),('repair',None),('repair',{})]:
            data={**self.data,'recovery_needed':True,'repair':repair};data[field]=value
            with self.subTest(field=field,value=value),self.assertRaisesRegex(p.Rejected,'repaired selection'):
                t.check_parent_selection(self.root,data,inc)
        for field,value in [('validation_passed',False),('routing_accepted',True),
                            ('comparison_eligible',True),('experimental_contact',False)]:
            changed={**repair,field:value};p.save_json(directory/'repair.json',changed)
            data={**self.data,'recovery_needed':True,'repair':changed}
            with self.subTest(field=field),self.assertRaisesRegex(p.Rejected,'repaired selection'):
                t.check_parent_selection(self.root,data,inc)
        p.save_json(directory/'repair.json',repair)
        with self.assertRaisesRegex(p.Rejected,'observation paths'):
            t.check_parent_selection(self.root,{**self.data,'recovery_needed':True,'repair':repair},inc)

    def test_enriched_drc_step_matches_its_journal_without_hiding_compute(self):
        repairdir=self.root/'recovery';trialdir=repairdir/'trial-01';trialdir.mkdir(parents=True)
        geometry=dict(name='thermal-geometry',cwd=str(repairdir),argv=['owned-worker'],
                      status='success',exit_code=0,cleanup_complete=True)
        process=dict(name='final-drc',cwd=str(trialdir),argv=['owned-native'],
                     status='nonzero_exit',exit_code=5,cleanup_complete=True,cpu_seconds=2.)
        p.save_json(repairdir/'thermal-geometry-process.json',geometry)
        p.save_json(trialdir/'final-drc-process.json',process)
        step={**process,'validated_input_sha256':'a'*64,'emitted_candidate':str(trialdir/'candidate/board.kicad_pcb')}
        trials=[dict(id='trial-01',steps=[step])];data=dict(steps=[geometry,step])
        t._check_trial_steps(repairdir,data,trials)
        for changed in ([geometry],[geometry,step,step]):
            with self.subTest(steps=len(changed)),self.assertRaisesRegex(p.Rejected,'compute'):
                t._check_trial_steps(repairdir,dict(steps=changed),trials)
        for change in (dict(argv=['other']),dict(cpu_seconds=0.),dict(unexpected='field')):
            altered={**step,**change}
            with self.subTest(change=change),self.assertRaises(p.Rejected):
                t._check_trial_steps(repairdir,dict(steps=[geometry,altered]),[dict(id='trial-01',steps=[altered])])
        p.save_json(trialdir/'final-netclasses-process.json',{**process,'name':'final-netclasses'})
        with self.assertRaisesRegex(p.Rejected,'omitted or duplicated a process journal'):
            t._check_trial_steps(repairdir,data,trials)

    def test_direct_route_cannot_impersonate_a_thermal_parent(self):
        from tests.test_normal_selected_import import NormalSelectedImportControls
        root,data,original,_,_=NormalSelectedImportControls.make(self,selected=False)
        data['strategy']='native_validated_thermal_bridge'
        imports=[dict(cwd=str(root))]
        with self.assertRaisesRegex(p.Rejected,'checked incumbent, not a direct import'):
            p.normal_import_contract(root,data,imports,input_policy='native',original=original)


if __name__=='__main__':unittest.main()
