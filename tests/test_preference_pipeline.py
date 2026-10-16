"""Captured-choice binding and read-only preview controls; no native correctness claim."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from autorouter import config as c, pipeline as p, preferences as pref, sexpr as sx
from autorouter.__main__ import preview


class PreferenceIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='preference-integration-',dir=c.ROOT/'.runs')
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.preset=self.root/'settings.json'
        self.preset.write_text(json.dumps(dict(pref.DEFAULTS,adapter='none')))
        captured=pref.load(self.preset)
        self.request={'captured':captured,'snapshot':pref.snapshot(captured),
                      'effective':pref.resolve(captured)}
        self.run=self.root/'run';self.run.mkdir()
        self.data={}
        p.capture_preferences(self.data,self.run,self.request)
        self.data.update(scope='whole_board_unlocked_routing',budget_seconds=120,cpu_budget_seconds=120,
                         adapter='none',engine_profile='standard',scoring_variant=None)
        settings=p.engine_profile_settings('standard',100)
        settings.update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120)
        self.data['engine_budget']=settings
        process={'name':'engine','status':'success','exit_code':0,'cleanup_complete':True,
                 'argv':p.engine_argv(self.run,settings['argv']),'cwd':str(self.run)}
        self.data['steps']=[process]
        (self.run/'engine-process.json').write_text(json.dumps(process))

    def test_capture_accepts_then_stale_input_rejects_without_rebasing_old_run(self):
        p.check_preferences_record(self.run,self.data)
        self.preset.write_text(json.dumps({**pref.DEFAULTS,'seconds':180}))
        with self.assertRaisesRegex(pref.PreferenceError,'changed'):p.preferences_fresh(self.run,self.request)
        p.check_preferences_record(self.run,self.data)  # Old run records the original exact bytes.

    def test_receipt_changes_and_missing_binding_are_rejected(self):
        for key,value in [('scope','partial_completion'),('budget_seconds',121),('cpu_budget_seconds',121),
                          ('adapter','both'),('engine_profile','tuned'),('scoring_variant','via_low'),
                          ('input_policy','placement-clearance-v1')]:
            with self.subTest(key=key),self.assertRaises(p.Rejected):
                p.check_preferences_record(self.run,{**self.data,key:value})
        changed=copy.deepcopy(self.data);del changed['routing_preferences']
        with self.assertRaises(p.Rejected):p.check_preferences_record(self.run,changed)
        changed=copy.deepcopy(self.data);changed['routing_preferences']['effective']['layers']='F.Cu'
        with self.assertRaises(pref.PreferenceError):p.check_preferences_record(self.run,changed)

    def test_changed_captured_bytes_or_missing_file_are_rejected(self):
        path=self.run/'routing-preferences.json';raw=path.read_bytes()
        path.write_bytes(raw+b' ')
        with self.assertRaises(p.Rejected):p.check_preferences_record(self.run,self.data)
        path.unlink()
        with self.assertRaises((p.Rejected,OSError)):p.check_preferences_record(self.run,self.data)

    def test_changed_engine_argv_is_rejected_even_when_process_and_summary_agree(self):
        for flag in ('--router.optimizer.enabled=false','--router.scoring.via_costs=999','--optimizer.enabled=false','-mp','--optimizer-scoring-version=v1'):
            changed=copy.deepcopy(self.data);changed['steps'][0]['argv'].append(flag)
            (self.run/'engine-process.json').write_text(json.dumps(changed['steps'][0]))
            with self.assertRaisesRegex(p.Rejected,'argv'):p.check_preferences_record(self.run,changed)

    def test_mixed_direct_and_preset_arguments_reject_before_creating_output(self):
        target=self.root/'ambiguous-route'
        with self.assertRaisesRegex(p.Rejected,'mixed route arguments'):
            p.route('not-read.kicad_pcb',target,seconds=90,settings_path=self.preset)
        self.assertFalse(target.exists())

    def test_layer_request_rejects_before_creating_route_output(self):
        target=self.root/'unqualified-route'
        with self.assertRaisesRegex(pref.PreferenceError,'layers'):
            p.route('not-read.kicad_pcb',target,preference_overrides={'layers':['F.Cu']})
        self.assertFalse(target.exists())

    def test_preview_counts_protected_routes_and_changes_no_source_files(self):
        project=self.root/'project';shutil.copytree(c.ROOT/'fixtures/smoke',project)
        board=project/'smoke.kicad_pcb';tree=sx.read(board)
        tree.extend([['segment',['start','1','1'],['end','2','1'],['width','0.25'],['layer','"F.Cu"'],['net','0'],'locked'],
                     ['segment',['start','2','2'],['end','3','2'],['width','0.25'],['layer','"F.Cu"'],['net','0']]])
        sx.write(board,tree);before=p.tree_hash(project)
        whole=preview(board,self.preset)
        partial=preview(board,self.preset,{'scope':'partial_completion','seconds':90})
        self.assertEqual(whole['protected_route_items'],1)
        self.assertEqual(whole['rerouted_route_items'],1)
        self.assertEqual(partial['protected_route_items'],2)
        self.assertEqual(partial['rerouted_route_items'],0)
        self.assertEqual(partial['effective_preferences']['seconds'],90)
        self.assertEqual(partial['copper_layers'],['F.Cu','B.Cu'])
        self.assertFalse(partial['native_validation_performed'])
        self.assertEqual(p.tree_hash(project),before)

    def test_settings_cli_exclusively_creates_persistent_file(self):
        output=self.root/'created.json'
        command=[sys.executable,'-B','-m','autorouter','settings-init','--output',str(output)]
        first=subprocess.run(command,cwd=c.ROOT,capture_output=True,text=True,timeout=10)
        self.assertEqual(first.returncode,0,first.stdout+first.stderr)
        raw=output.read_bytes();self.assertEqual(pref.load(output).parsed,dict(pref.DEFAULTS))
        second=subprocess.run(command,cwd=c.ROOT,capture_output=True,text=True,timeout=10)
        self.assertEqual(second.returncode,2)
        self.assertEqual(output.read_bytes(),raw)


if __name__=='__main__':unittest.main()
