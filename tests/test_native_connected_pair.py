"""Filesystem publication continuity controls; these do not simulate native passes."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from autorouter import floor_route as f, pipeline as p
from experiments.native_connected_pair_v1 import driver as d


class OuterWitness(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.out=self.root/'arm';self.out.mkdir()
        self.probe=self.root/'arm-classifier';self.probe.mkdir()
        self.source=self.root/'source';self.source.mkdir()
        self.files={
            'candidate':self.out/'final-candidate'/'owned.kicad_pcb',
            'report':self.out/'original-validation'/'final-drc.json',
            'child':self.out/'selected-route'/'result.json',
            'probe':self.probe/'task'/'owned.kicad_pcb',
            'receipt':self.probe/'result.json',
            'original':self.source/'owned.kicad_pcb',
            'companion':self.source/'owned.kicad_pro',
            'helper':self.root/'helper.py'}
        for name,path in self.files.items():
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text('authored '+name+'\n')
        self.spec={'source':str(self.files['original']),'source_hashes':p.tree_hash(self.source),
                   'code_sha256':{'helper.py':p.sha(self.files['helper'])}}
        self.record=dict(schema=1,kind='exposed-NUS-native-connected-selected-seam-diagnostic',
            method='all-active',status='completed',accepted=False,method_qualified=True,
            production_admitted=False,within_budget=True,protocol_sha256='prospective-pin',
            budget_seconds=120,cpu_budget_seconds=120,bootstrap_allowance_seconds=1,
            final_reserve_seconds=20,wall_seconds=50.,total_cpu_seconds=40.,
            charged_wall_seconds=51.,charged_full_cpu_seconds=41.,classifier=str(self.probe),
            classifier_sha256=p.sha(self.files['receipt']),classifier_material=f.evidence_inventory(self.probe),
            completed_material=f.evidence_inventory(self.out),source=self.spec['source'],
            source_hashes=self.spec['source_hashes'],tools={'authored':'metadata only'})
        self.addCleanup(patch.stopall)
        patch.object(d,'ROOT',self.root).start()
        # Isolate metadata checking, never invoke or assert native validation here.
        patch.object(p,'tool_manifest',return_value=self.record['tools']).start()

    def check(self,record=None):
        d.check_outer_witness(self.out,self.record if record is None else record,
                              'all-active','prospective-pin',self.spec)

    def test_unchanged_files_and_exact_metadata(self):
        self.check()

    def test_nested_material_mutation_and_removal_reject(self):
        for name,path in self.files.items():
            before=path.read_bytes()
            for action in ('mutate','remove'):
                with self.subTest(file=name,action=action):
                    if action=='mutate':path.write_bytes(before+b'changed')
                    else:path.unlink()
                    try:
                        with self.assertRaises((p.Rejected,FileNotFoundError)):self.check()
                    finally:path.write_bytes(before)
            self.check()

    def test_actor_identity_and_accounting_cannot_be_relabelled(self):
        changes={'schema':True,'kind':'different','method':'native-connected','status':'failed',
            'accepted':True,'production_admitted':True,'method_qualified':1,'within_budget':1,
            'protocol_sha256':'other','budget_seconds':121,'cpu_budget_seconds':True,
            'bootstrap_allowance_seconds':0,'final_reserve_seconds':19,'wall_seconds':-1,
            'charged_wall_seconds':120.1,'charged_full_cpu_seconds':float('nan'),
            'total_cpu_seconds':True,'classifier':str(self.out),'classifier_material':{},
            'completed_material':{},'source_hashes':{},'tools':{}}
        for key,value in changes.items():
            with self.subTest(key=key):
                record=copy.deepcopy(self.record);record[key]=value
                with self.assertRaises(p.Rejected):self.check(record)
        record=copy.deepcopy(self.record);record['charged_full_cpu_seconds']+=.1
        with self.assertRaises(p.Rejected):self.check(record)

    def test_new_material_also_rejects(self):
        for directory in (self.out,self.probe,self.source):
            path=directory/'unexpected'
            with self.subTest(directory=directory),self.assertRaises(p.Rejected):
                path.write_text('late writer');self.check()
            path.unlink()


if __name__=='__main__':unittest.main()
