"""Frozen source-schema and charged-incumbent falsifiers; no native pass claim."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch
from autorouter import pipeline as p
from experiments.native_paired_v1 import readback as r


class SourceEvidenceContract(unittest.TestCase):
    def setUp(self):
        self.native_files = {name: str(i)*64 for i, name in enumerate((
            'board.kicad_pcb', 'board.kicad_pro', 'board.kicad_sch',
            '_licenses/creator/LICENSE', '_licenses/creator/README.md', 'libraries/part.kicad_mod'))}
        self.files = {'LICENSE': '3'*64, 'README.md': '4'*64,
                      **{'hardware/'+name: digest for name, digest in self.native_files.items()}}
        self.native = dict(opens=24, blocking=0, warnings=209, exclusions=0,
            ignored_checks=[], findings=[dict(type='unconnected_items', severity='error', description='control', items=[])])
        self.record = dict(project='cellscan', kind='original_hardware_native_diagnostic', status='observed',
            source_commit='revision', original_hashes=self.files, parity_native=self.native,
            final_candidate_sha256='candidate', steps=[{}]*4, original_preserved=True,
            acquired_source_still_exact=True, original_shell_nonfill_ast_equal=True, all_original_route_records_exact=True,
            source_file_count=8,source_bytes=1234,wall_seconds=1.,total_cpu_seconds=1.)
        self.spec = dict(kind='prospective larger CellScan complete-schematic four-arm development experiment',
            source_original_native_receipt_sha256='receipt', source_original_native_review_sha256='review',
            original_source_sha256=self.native_files, freeze=dict(source_hashes=self.native_files),
            source_revision='revision', coverage='all boards retained', initial_reference_feasibility='incomplete original',
            warnings='all warnings retained', shared_original_qualification_cost=dict(wall_seconds=25,full_cpu_seconds=25),
            final_readback_allowance_wall_full_cpu_seconds=15, bootstrap_publication_allowance_seconds_each_arm=1)
        self.review = dict(kind='CellScan original actual native diagnostic independent readback',
            passed=True, failures=[], new_native_execution=False, new_network_requests=0, checks={
                'exact_acquired_source_and_eight_input_files': dict(passed=True,copied_original_hashes=self.files,
                    native_input_files=8,native_input_bytes=1234,source_unchanged=True,source_commit='revision'),
                'exact_original_shell_routes_and_protection': dict(passed=True,all_original_route_records_exact=True,
                    immutable_original_design_and_companions_exact=True,candidate_sha256='candidate'),
                'actual_native_refill_full_schematic_and_all_workers': dict(passed=True,worker_count=4,drc_worker_count=2,
                    additional_field_netlist_and_audit_workers=2,native_acceptance=False,
                    native_rejection_reasons=p.native_rejection_reasons(self.native)),
                'exact_fifty_field_mismatch_descriptions_and_original_fields': dict(passed=True,ignored_checks=[],
                    native_observation_not_normalized_or_waived=True),
                'whole_costs_and_immutable_retained_evidence': dict(passed=True,native_receipt_sha256='receipt',
                    all_retained_evidence_unchanged=True,record_wall_seconds=1.,record_full_cpu_seconds=1.)})

    def contract(self):
        return r.source_evidence_contract(self.spec,self.record,self.review,'receipt','review',self.files,self.native_files)

    def test_alternate_schema_preserves_incomplete_original_and_input_bytes(self):
        before=copy.deepcopy((self.spec,self.record,self.review))
        result=self.contract()
        self.assertEqual(result['source_files'],self.files)
        self.assertEqual(result['native'],self.native)
        self.assertFalse(p.native_accepted(result['native']))
        self.assertEqual(before,(self.spec,self.record,self.review))

    def test_bound_receipt_and_review_pins_are_mandatory(self):
        for key in ('source_original_native_receipt_sha256','source_original_native_review_sha256'):
            with self.subTest(key=key):
                old=self.spec[key];self.spec[key]='other'
                with self.assertRaises(p.Rejected):self.contract()
                self.spec[key]=old

    def test_root_notices_and_native_six_files_are_separately_required(self):
        for target in ('root','native','review','record'):
            with self.subTest(target=target):
                if target=='root':changed={k:v for k,v in self.files.items()if k!='LICENSE'}
                elif target=='native':changed={k:v for k,v in self.native_files.items()if k!='libraries/part.kicad_mod'}
                elif target=='review':
                    old=self.review['checks']['exact_acquired_source_and_eight_input_files']['copied_original_hashes']
                    self.review['checks']['exact_acquired_source_and_eight_input_files']['copied_original_hashes']={}
                else:
                    old=self.record['original_hashes'];self.record['original_hashes']={}
                with self.assertRaises(p.Rejected):
                    if target=='root':r.source_evidence_contract(self.spec,self.record,self.review,'receipt','review',changed,self.native_files)
                    elif target=='native':r.source_evidence_contract(self.spec,self.record,self.review,'receipt','review',self.files,changed)
                    else:self.contract()
                if target=='review':self.review['checks']['exact_acquired_source_and_eight_input_files']['copied_original_hashes']=old
                elif target=='record':self.record['original_hashes']=old

    def test_missing_failed_or_truthy_instead_of_true_checks_reject(self):
        original=copy.deepcopy(self.review)
        for kind in ('missing','failed','truthy','failure-list','extra-failed'):
            self.review=copy.deepcopy(original)
            with self.subTest(kind=kind):
                key='exact_original_shell_routes_and_protection'
                if kind=='missing':del self.review['checks'][key]
                elif kind=='failed':self.review['checks'][key]['passed']=False
                elif kind=='truthy':self.review['checks'][key]['all_original_route_records_exact']='yes'
                elif kind=='failure-list':self.review['failures']=['retained control failure']
                else:self.review['checks']['extra-check']={'passed':False}
                with self.assertRaises(p.Rejected):self.contract()

    def test_alternate_does_not_create_original_acceptance_or_discount_costs(self):
        for kind in ('native-accepted','workers','source-wall','source-cpu','audit','bootstrap','record-wall','record-cpu'):
            with self.subTest(kind=kind):
                spec=copy.deepcopy(self.spec);review=copy.deepcopy(self.review)
                if kind=='native-accepted':review['checks']['actual_native_refill_full_schematic_and_all_workers']['native_acceptance']=True
                elif kind=='workers':review['checks']['actual_native_refill_full_schematic_and_all_workers']['worker_count']=3
                elif kind=='source-wall':spec['shared_original_qualification_cost']['wall_seconds']=0
                elif kind=='source-cpu':spec['shared_original_qualification_cost']['full_cpu_seconds']=0
                elif kind=='audit':spec['final_readback_allowance_wall_full_cpu_seconds']=0
                elif kind=='bootstrap':spec['bootstrap_publication_allowance_seconds_each_arm']=0
                elif kind=='record-wall':review['checks']['whole_costs_and_immutable_retained_evidence']['record_wall_seconds']=0
                else:review['checks']['whole_costs_and_immutable_retained_evidence']['record_full_cpu_seconds']=0
                with self.assertRaises(p.Rejected):
                    r.source_evidence_contract(spec,self.record,review,'receipt','review',self.files,self.native_files)

    def test_existing_schema_keeps_its_own_proofs_and_cannot_fallback(self):
        self.spec.update(source_original_native_readback_sha256='review',
            source_files={name:dict(sha256=digest) for name,digest in self.files.items()},limits=['legacy'])
        self.review.update(controls_passed=True,source_exact=True,original_constraints_and_all_routes_exact=True,native=self.native)
        self.assertEqual(self.contract()['schema'],'original-native-readback')
        self.review['controls_passed']=False
        with self.assertRaises(p.Rejected):self.contract()


class PruningIncumbentAccounting(unittest.TestCase):
    def setUp(self):
        self.folder=Path('/owned-control/C_feedback');self.board=Path('/owned-control/source/board.kicad_pcb')
        self.data=dict(status='drc_rejected',accepted=False,metrics={'vias':1},wall_seconds=.5,total_cpu_seconds=.6,
            source=str(self.board),tools={},source_hashes={},steps=[dict(name='engine')])
        self.parent=dict(tools={},incumbent={**{k:self.data[k] for k in ('status','accepted','metrics','wall_seconds')},
            'receipt':str(self.folder/'incumbent/result.json')},wall_seconds=1.,total_cpu_seconds=1.,
            steps=[dict(name='engine',phase='incumbent')])

    def call(self):
        with patch.object(r.f,'read_json',return_value=self.data),patch.object(p,'check_resource_accounting'),\
                patch.object(p,'check_engine_profile_record'),patch.object(r,'final_candidate_readback',return_value={'control':True}) as final:
            result=r.pruning_incumbent_readback(self.folder,self.parent,self.board,[],{})
            final.assert_called_once_with(self.folder/'incumbent',self.data,self.board,[],{})
            return result

    def test_rejected_own_incumbent_still_requires_shared_final_readback(self):
        self.assertFalse(self.call()[0]['accepted'])

    def test_relabelled_uncharged_or_foreign_incumbent_rejects(self):
        parent=copy.deepcopy(self.parent);data=copy.deepcopy(self.data)
        for kind in ('path','status','worker','wall','cpu','source','tools'):
            self.parent=copy.deepcopy(parent);self.data=copy.deepcopy(data)
            with self.subTest(kind=kind):
                if kind=='path':self.parent['incumbent']['receipt']='/other/result.json'
                elif kind=='status':self.parent['incumbent']['status']='routing_accepted'
                elif kind=='worker':self.parent['steps']=[]
                elif kind=='wall':self.parent['wall_seconds']=.4
                elif kind=='cpu':self.parent['total_cpu_seconds']=.5
                elif kind=='source':self.data['source']='/other/board.kicad_pcb'
                else:self.data['tools']={'changed':True}
                with self.assertRaises(p.Rejected):self.call()


if __name__=='__main__':unittest.main()
