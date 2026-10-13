"""Synthetic search/basis consistency controls; no new native execution.

The existing retained-fixture builder supplies complete process/transport files.
Search settings are deliberately synthetic and never qualify a routed profile.
"""
import copy
import json
import shutil
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import test_placement_policy as fixture
from autorouter import floor_route as f, pipeline as p, sexpr as sx


class FloorSearch(unittest.TestCase):
    setUp=fixture.Receipt.setUp
    save=fixture.Receipt.save

    def prepare(self,profile='completion-only',variant='via_default'):
        self.data.update(schema=4,input_policy=f.SEARCH_POLICY,engine_profile=profile,
                         baseline=p.engine_baseline(profile,'both'),scoring_variant=variant)
        path=self.out/'placement-search.json'
        p.save_json(path,f.search_contract(profile,variant))
        self.data['placement_search']={'file':path.name,'sha256':p.sha(path)}
        settings=p.engine_profile_settings(profile,self.data['engine_budget']['remaining_outer_wall_seconds_at_assignment'],
                                           strict_class_targets=True,scoring_variant=variant)
        settings.update(outer_task_wall_budget_seconds=self.data['budget_seconds'],outer_task_cpu_budget_seconds=self.data['cpu_budget_seconds'])
        self.data['engine_budget']=settings
        step=next(x for x in self.data['steps'] if x['name']=='engine')
        step['argv']=f.engine_argv(self.out,settings['argv'])
        path=self.out/'engine-process.json';process=f.read_json(path);process['argv']=step['argv'];p.save_json(path,process)
        if profile=='tuned':
            (self.out/'engine.log').write_text('synthetic settings consistency; no runtime observation\n')
            self.data['optimizer_threshold_audit']=p.optimizer_threshold_audit(self.out/'engine.log',0.1)
        else:self.data.pop('optimizer_threshold_audit',None)
        self.save()

    def check(self):
        return f.check_floor_result(self.out,self.data,sx.read(self.source),self.candidate,[])

    def test_nine_finite_search_combinations_keep_transport_and_geometry(self):
        frozen={name:(self.out/name).read_bytes() for name in ('native.dsn','floor-guided.dsn','placement-guided.dsn','planning-guided.dsn','task.dsn','floor-policy.json','placement-policy.json')}
        for profile in ('standard','tuned','completion-only'):
            for variant in ('via_default','via_low','via_high'):
                with self.subTest(profile=profile,variant=variant):
                    self.prepare(profile,variant)
                    self.assertEqual(f.receipt_policy(self.data,self.out),f.SEARCH_POLICY)
                    self.check()
                    for name,raw in frozen.items():self.assertEqual((self.out/name).read_bytes(),raw)

    def test_search_dispatch_is_explicit_and_keeps_legacy_call_shape(self):
        args=('missing','missing',120,False,'both','tuned','via_low')
        with patch.object(f,'_route',return_value={'synthetic':True}) as worker:
            f.route(*args,guidance_policy=f.SEARCH_POLICY)
            self.assertEqual(worker.call_args.args,('missing','missing',120,'tuned',f.SEARCH_POLICY,None))
            self.assertEqual(worker.call_args.kwargs,{'scoring_variant':'via_low'})
        with patch.object(f,'_route',return_value={}) as worker:
            f.route('missing','missing',120,False,'both','completion-only',None,guidance_policy=f.PLACEMENT_POLICY)
            self.assertEqual(worker.call_args.kwargs,{})
        with patch.object(f,'_route',return_value={}) as worker:
            f.route('missing','missing',120,False,'both','standard',None,guidance_policy=f.SEARCH_POLICY)
            self.assertEqual(worker.call_args.kwargs,{'scoring_variant':'via_default'})

    def test_invalid_request_fails_before_worker(self):
        base=dict(source='missing',output='missing',seconds=120,keep_existing=False,adapter='both',profile='tuned',scoring_variant='via_low',guidance_policy=f.SEARCH_POLICY)
        for changes in ({'preferences':{}},{'keep_existing':True},{'adapter':'none'},{'profile':'arbitrary'},{'profile':True},{'scoring_variant':25},{'scoring_variant':[]},{'scoring_variant':'unknown'}):
            with self.subTest(changes=changes),patch.object(f,'_route') as worker,self.assertRaises(p.Rejected):f.route(**{**base,**changes})
            worker.assert_not_called()

    def test_schema3_stays_fixed(self):
        self.assertEqual(f.receipt_policy(self.data,self.out),f.PLACEMENT_POLICY)
        for key,value in [('engine_profile','standard'),('scoring_variant','via_low'),('schema',4)]:
            old=copy.deepcopy(self.data);self.data[key]=value
            with self.subTest(key=key),self.assertRaises(p.Rejected):f.receipt_policy(self.data,self.out)
            self.data=old

    def test_schema4_cannot_downgrade_or_mix(self):
        self.prepare();saved=copy.deepcopy(self.data)
        for key,value in [('schema',3),('schema',1),('schema',True),('input_policy',f.PLACEMENT_POLICY),('input_policy','native'),('placement_search',None),('strategy','pruning'),('routing_preferences',{}),('guidance_policy',f.SEARCH_POLICY),('netclass_policy',{}),('production_qualified',True),('scope','partial_completion'),('engine_profile','other'),('scoring_variant',None),('baseline','C-prototype')]:
            self.data=copy.deepcopy(saved)
            if value is None:self.data.pop(key,None)
            else:self.data[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(p.Rejected):f.receipt_policy(self.data,self.out)
        self.data=copy.deepcopy(saved)
        self.data.update(schema=3,input_policy=f.PLACEMENT_POLICY);self.data.pop('placement_search')
        with self.assertRaises(p.Rejected):f.receipt_policy(self.data,self.out)

    def test_missing_search_marker_and_preferences_artifacts_reject(self):
        self.prepare();path=self.out/'placement-search.json';raw=path.read_bytes();path.unlink()
        with self.assertRaises((FileNotFoundError,p.Rejected)):f.receipt_policy(self.data,self.out)
        path.write_bytes(raw);(self.out/'routing-preferences.json').write_text('{}')
        with self.assertRaises(p.Rejected):f.receipt_policy(self.data,self.out)

    def test_rehashed_search_contract_must_match_profile(self):
        self.prepare('standard','via_low');path=self.out/'placement-search.json';value=f.read_json(path)
        value['scoring']['via_costs']=50;p.save_json(path,value);self.data['placement_search']['sha256']=p.sha(path);self.save()
        with self.assertRaisesRegex(p.Rejected,'search contract'):self.check()

    def test_engine_args_and_settings_cannot_differ_from_named_policy(self):
        self.prepare('standard','via_low')
        settings=p.engine_profile_settings('standard',self.data['engine_budget']['remaining_outer_wall_seconds_at_assignment'],strict_class_targets=True,scoring_variant='via_high')
        settings.update(outer_task_wall_budget_seconds=self.data['budget_seconds'],outer_task_cpu_budget_seconds=self.data['cpu_budget_seconds'])
        self.data['engine_budget']=settings
        step=next(x for x in self.data['steps'] if x['name']=='engine');step['argv']=f.engine_argv(self.out,settings['argv'])
        path=self.out/'engine-process.json';process=f.read_json(path);process['argv']=step['argv'];p.save_json(path,process);self.save()
        with self.assertRaisesRegex(p.Rejected,'engine configuration'):self.check()

    def test_all_three_width_reduction_guards_required(self):
        for arg in ('--router.automatic_neckdown=false','--router.fanout.enabled=false','--router.neck_width_um=0'):
            self.prepare('standard','via_low');self.data['engine_budget']['argv'].remove(arg)
            step=next(x for x in self.data['steps'] if x['name']=='engine');step['argv']=f.engine_argv(self.out,self.data['engine_budget']['argv'])
            path=self.out/'engine-process.json';process=f.read_json(path);process['argv']=step['argv'];p.save_json(path,process);self.save()
            with self.subTest(arg=arg),self.assertRaisesRegex(p.Rejected,'engine configuration'):self.check()

    def test_ordinary_search_still_needs_ses_and_exact_eight_stages(self):
        self.prepare();path=self.out/'routes.ses';raw=path.read_bytes();path.unlink();self.save()
        with self.assertRaisesRegex(p.Rejected,'SES'):self.check()
        path.write_bytes(raw);self.data['steps'].append({'name':'invented'});self.save()
        with self.assertRaisesRegex(p.Rejected,'execution stages'):self.check()

    def test_search_candidate_still_reconstructed_from_import_refill(self):
        self.prepare();path=self.out/'imported.kicad_pcb';tree=sx.read(path)
        sx.one(p.routes(tree)[0],'width')[1]='0.4';sx.write(path,tree);self.save()
        with self.assertRaises(p.Rejected):self.check()

    def move_basis(self):
        basis=self.root/'basis';basis.mkdir()
        for name in ('floor-export-context.json','native.dsn','floor-guided.dsn'):
            (self.out/name).rename(basis/name)
        return basis,f.read_json(self.out/'floor-policy.json')

    def test_external_basis_reads_original_export_but_checks_this_candidate(self):
        basis,contract=self.move_basis();original=sx.read(self.source)
        with self.assertRaises(FileNotFoundError):f.validate_contract(original,self.candidate,self.data['source_hashes'],[],contract,self.out)
        task,_=f.validate_contract(original,self.candidate,self.data['source_hashes'],[],contract,self.out,guidance_basis=basis)
        self.assertEqual(task,sx.read(self.out/'floor-export-input'/self.source.name))
        f.check_final_context(self.out,self.data,original,self.candidate,[],contract,guidance_basis=basis)
        path=self.out/'floor-final-context.json';value=f.read_json(path);value['project_sha256']='0'*64;p.save_json(path,value)
        with self.assertRaisesRegex(p.Rejected,'context input/project'):f.check_final_context(self.out,self.data,original,self.candidate,[],contract,guidance_basis=basis)

    def test_external_basis_cannot_change_preferences_guidance_or_source_contract(self):
        basis,contract=self.move_basis();original=sx.read(self.source)
        for name in ('native.dsn','floor-guided.dsn','floor-export-context.json'):
            path=basis/name;raw=path.read_bytes()
            if name.endswith('.json'):
                value=json.loads(raw);value['nets'][0]['width_nm']=123456;path.write_text(json.dumps(value))
            else:path.write_bytes(raw.replace(b'(width 300)',b'(width 301)').replace(b'(width 200)',b'(width 201)'))
            self.assertNotEqual(path.read_bytes(),raw)
            with self.subTest(name=name),self.assertRaises((ValueError,p.Rejected)):f.validate_contract(original,self.candidate,self.data['source_hashes'],[],contract,self.out,guidance_basis=basis)
            path.write_bytes(raw)
        bad=copy.deepcopy(contract);bad['source_hashes'][self.source.name]='0'*64
        with self.assertRaisesRegex(p.Rejected,'contract differs'):f.validate_contract(original,self.candidate,self.data['source_hashes'],[],bad,self.out,guidance_basis=basis)
        link=self.root/'alias';link.symlink_to(basis,target_is_directory=True)
        with self.assertRaisesRegex(p.Rejected,'symlink'):f.validate_contract(original,self.candidate,self.data['source_hashes'],[],contract,self.out,guidance_basis=link)

    def test_final_context_writes_fresh_job_not_basis(self):
        basis,contract=self.move_basis();frozen=p.tree_hash(basis);target=self.root/'trial';target.mkdir()
        native=f.read_json(self.out/'floor-final-context.json')
        def observe(job,mode,candidate):
            self.assertEqual((job.out,mode,candidate),(target,'final',self.candidate))
            p.save_json(target/'floor-final-context.json',native);return native
        with patch.object(f,'acquire_context',side_effect=observe) as observed:
            f.final_context(SimpleNamespace(out=target),sx.read(self.source),self.candidate,self.data['source_hashes'],[],contract,guidance_basis=basis)
        observed.assert_called_once();self.assertTrue((target/'floor-final-audit.json').is_file());self.assertEqual(p.tree_hash(basis),frozen)

    def test_extracted_drc_stage_preserves_binding_process_and_input_checks(self):
        name='source-drc';source=self.out/'snapshot'/self.source.name;inp=self.out/'source-drc-input'/self.source.name
        def check():return f.check_drc_stage(self.out,self.data,name,source,inp,False,self.data['source_hashes'])
        self.assertEqual(check(),self.data['source_drc'])
        path=self.out/'source-drc-binding.json';raw=path.read_bytes();value=f.read_json(path);value['saved']=True;p.save_json(path,value)
        with self.assertRaisesRegex(p.Rejected,'binding differs'):check()
        path.write_bytes(raw)
        rule=inp.with_suffix('.kicad_pro');raw=rule.read_bytes();rule.write_bytes(raw+b' ')
        with self.assertRaisesRegex(p.Rejected,'input changed'):check()
        rule.write_bytes(raw)
        step=next(x for x in self.data['steps'] if x['name']==name);step['argv']=['/usr/bin/true']
        path=self.out/'source-drc-process.json';value=f.read_json(path);value['argv']=step['argv'];p.save_json(path,value)
        with self.assertRaisesRegex(p.Rejected,'process provenance'):check()


if __name__=='__main__':unittest.main()
