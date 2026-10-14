"""Parent/trial accounting falsifiers; no simulated native pass claims."""
from pathlib import Path
import copy
import unittest
from experiments.native_paired_v1.readback import inherited_trial_accounting
from autorouter import pipeline as p


class InheritedTrialAccounting(unittest.TestCase):
    def setUp(self):
        self.folder=Path('/owned-control/trials/trial-0000')
        step={'name':'refill-drc','phase':'trial-0000','wall_seconds':.2,'cpu_seconds':.4,'monitor_cpu_seconds':0}
        self.trial={'id':'trial-0000','status':'drc_rejected','accepted':False,'steps':[step],
            'started_elapsed_seconds':.1,'finished_elapsed_seconds':.7,'finished_observed_cpu_seconds':.8}
        self.parent={'steps':[copy.deepcopy(step)],'wall_seconds':1.,'budget_seconds':5.,'cpu_budget_seconds':5.,
            'total_cpu_seconds':1.,'parent_cpu_seconds':.6,'child_cpu_seconds':.4,'monitor_cpu_seconds':0,
            'trials':[{'id':'trial-0000','status':'drc_rejected','accepted':False,'receipt':str(self.folder/'result.json')}]}

    def test_workers_in_valid_charged_parent_pass_without_fabricated_trial_budget(self):
        inherited_trial_accounting(self.folder,self.trial,self.parent)

    def test_missing_wrong_parent_reference_or_worker_cost_cannot_be_omitted(self):
        for change in ('reference','worker','phase'):
            parent=copy.deepcopy(self.parent);trial=copy.deepcopy(self.trial)
            if change=='reference':parent['trials']=[]
            elif change=='worker':trial['steps'][0]['cpu_seconds']=.3
            else:trial['steps'][0]['phase']='other-trial'
            with self.assertRaises(p.Rejected):inherited_trial_accounting(self.folder,trial,parent)

    def test_over_parent_time_cpu_and_nonfinite_boundaries_reject(self):
        for key,value in [('finished_elapsed_seconds',1.1),('finished_elapsed_seconds',.05),
                ('finished_observed_cpu_seconds',1.1),('finished_observed_cpu_seconds',float('nan'))]:
            trial=copy.deepcopy(self.trial);trial[key]=value
            with self.assertRaises(p.Rejected):inherited_trial_accounting(self.folder,trial,self.parent)
