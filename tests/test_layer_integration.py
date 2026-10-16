"""Layer contract integration controls; these do not substitute for native DRC."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from autorouter import config as c, pipeline as p, preferences as pref, sexpr as sx
from autorouter.__main__ import preview


class LayerIntegration(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='layers-',dir=c.ROOT/'.runs')
        self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
        self.project=self.root/'source';shutil.copytree(c.ROOT/'fixtures/smoke',self.project)
        self.source=self.project/'smoke.kicad_pcb'
        self.run=self.root/'run';self.run.mkdir()
        for name in ('native.dsn','task.dsn'):
            shutil.copyfile(c.ROOT/'evidence/placement-production-native-001/native.dsn',self.run/name)
        shutil.copytree(self.project,self.run/'candidate');self.candidate=self.run/'candidate'/self.source.name
        self.tree=sx.read(self.candidate)
        self.tree.append(sx.parse('(segment (start 10 10) (end 15 10) (width 0.25) (layer "F.Cu") (net "A") (uuid "abc"))'))
        sx.write(self.candidate,self.tree)
        self.effective=pref.resolve(overrides={'profile':'completion-only','layers':['F.Cu'],'adapter':'none'})
        self.contract=p.layer_contract(self.run,self.source,self.effective)
        self.data={'source':str(self.source),'candidate':str(self.candidate)}
        request={'captured':None,'effective':self.effective,'snapshot':pref.snapshot(overrides={'profile':'completion-only','layers':['F.Cu'],'adapter':'none'})}
        p.capture_preferences(self.data,self.run,request)
        self.data.update(scope='whole_board_unlocked_routing',budget_seconds=120,cpu_budget_seconds=120,
            adapter='none',engine_profile='completion-only',scoring_variant=None,
            layer_binding=self.contract['binding'],layer_audit=p.audit_layer_contract(self.candidate,self.contract))
        settings=p.engine_profile_settings('completion-only',100)
        settings.update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120)
        settings['argv'].append(self.contract['binding']['engine_argument'])
        self.data['engine_budget']=settings
        self.process={'name':'engine','status':'success','exit_code':0,'cleanup_complete':True,
            'argv':p.engine_argv(self.run,settings['argv']),'cwd':str(self.run)}
        self.data['steps']=[self.process];self.write_process(self.process)

    def write_process(self,process):
        (self.run/'engine-process.json').write_text(json.dumps(process))

    def test_captured_choice_rederived_from_bytes_and_actual_argv(self):
        p.check_preferences_record(self.run,self.data)
        for field,value in [('layer_binding',None),('layer_audit',None)]:
            data=copy.deepcopy(self.data);data[field]=value
            with self.subTest(field=field),self.assertRaises((ValueError,p.Rejected)):
                p.check_preferences_record(self.run,data)
        data=copy.deepcopy(self.data);data['layer_binding']['routable']=[1,0]
        with self.assertRaises(p.Rejected):p.check_preferences_record(self.run,data)
        data=copy.deepcopy(self.data);data['layer_audit']['layer_scope_passed']=1
        with self.assertRaises(p.Rejected):p.check_preferences_record(self.run,data)

    def test_markers_cannot_be_removed_individually_to_downgrade_dispatch(self):
        for key in ('layer_binding','layer_audit','routing_preferences'):
            data=copy.deepcopy(self.data);del data[key]
            with self.subTest(key=key),self.assertRaises(p.Rejected):p.check_preferences_record(self.run,data)
        (self.run/'routing-preferences.json').unlink()
        for keep in ('layer_binding','layer_audit','steps','engine_budget','process'):
            data={keep:copy.deepcopy(self.data[keep])} if keep!='process' else {}
            self.write_process(self.process if keep=='process' else {'argv':[]})
            with self.subTest(keep=keep),self.assertRaisesRegex(p.Rejected,'requires captured'):
                p.check_preferences_record(self.run,data)

    def test_wrong_duplicate_alias_and_extra_flags_reject_even_consistently_rewritten(self):
        for flag in ('--router.layers.routable=false,true','--router.layers.routable=true,false','--router.layers.active=true,false'):
            data=copy.deepcopy(self.data);data['steps'][0]['argv'].append(flag)
            self.write_process(data['steps'][0])
            with self.subTest(flag=flag),self.assertRaises(p.Rejected):p.check_preferences_record(self.run,data)
        data=copy.deepcopy(self.data);data['engine_budget']['argv'][-1]='--router.layers.routable=false,true'
        data['steps'][0]['argv']=p.engine_argv(self.run,data['engine_budget']['argv']);self.write_process(data['steps'][0])
        with self.assertRaises(p.Rejected):p.check_preferences_record(self.run,data)

    def test_changed_dsn_source_or_final_copper_reject(self):
        for target in (self.source,self.run/'native.dsn',self.run/'task.dsn'):
            raw=target.read_bytes();target.write_bytes(raw+b'\n')
            with self.subTest(path=target),self.assertRaises(p.Rejected):p.check_preferences_record(self.run,self.data)
            target.write_bytes(raw)
        tree=copy.deepcopy(self.tree);sx.one(tree[-1],'layer')[1]='"B.Cu"';sx.write(self.candidate,tree)
        with self.assertRaisesRegex(ValueError,'disallowed'):p.check_preferences_record(self.run,self.data)
        # Adding a lock to generated copper cannot make it an original exemption.
        tree[-1].append(['locked','yes']);sx.write(self.candidate,tree)
        with self.assertRaisesRegex(ValueError,'disallowed'):p.check_preferences_record(self.run,self.data)

    def test_before_and_after_refill_are_audited_before_final_native(self):
        class Job:
            def __init__(self,out):self.out=out;self.calls=[]
            def drc(self,name,board,**kwargs):self.calls.append(name);return {}
        original=sx.read(self.source);hashes=p.tree_hash(self.project)
        job=Job(self.run)
        tree=copy.deepcopy(self.tree);sx.one(tree[-1],'layer')[1]='"B.Cu"';sx.write(self.candidate,tree)
        with self.assertRaisesRegex(ValueError,'disallowed'):
            p.validate_candidate(job,original,self.candidate,hashes,[],layer_contract=self.contract)
        self.assertEqual(job.calls,[])
        sx.write(self.candidate,self.tree)
        def altered(original,filled):
            result=copy.deepcopy(original);sx.one(result[-1],'layer')[1]='"B.Cu"';return result
        with patch.object(p,'transplant_fill',altered),self.assertRaisesRegex(ValueError,'disallowed'):
            p.validate_candidate(job,original,self.candidate,hashes,[],layer_contract=self.contract)
        self.assertEqual(job.calls,['refill-drc'])

    def test_preview_reports_original_protected_exemption_without_native_or_source_edit(self):
        tree=sx.read(self.source);route=copy.deepcopy(self.tree[-1]);sx.one(route,'layer')[1]='"B.Cu"'
        tree.append(route);sx.write(self.source,tree);before=p.tree_hash(self.project)
        result=preview(self.source,overrides={'profile':'completion-only','layers':['F.Cu'],'scope':'partial_completion'})
        self.assertEqual(result['layer_restriction']['protected_items_outside_allowed_layers'],1)
        self.assertEqual(result['layer_restriction']['allowed_new_route_layers'],['F.Cu'])
        self.assertFalse(result['native_validation_performed']);self.assertEqual(p.tree_hash(self.project),before)

    def test_cli_explicit_list_overrides_only_layers_and_mixed_source_all_rejects(self):
        preset=self.root/'preset.json';preset.write_text(json.dumps(dict(pref.DEFAULTS,profile='completion-only',layers=['B.Cu'],seconds=90)))
        command=[sys.executable,'-B','-m','autorouter','preview',str(self.source),'--settings',str(preset),'--layers','F.Cu']
        result=subprocess.run(command,capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        effective=json.loads(result.stdout)['effective_preferences'];self.assertEqual(effective['layers'],['F.Cu']);self.assertEqual(effective['seconds'],90)
        result=subprocess.run(command+['source_all'],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,2)


if __name__=='__main__':unittest.main()
