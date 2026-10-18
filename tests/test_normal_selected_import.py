"""Authored process/source consistency controls only; no Native tools ran."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from autorouter import adapter, floor_route as f, pipeline as p, placement_clearance as pc, preferences, routing_scope as rs, sexpr as sx
from tests.test_selected_proposal_import import board, proposals
from tests.test_fixed_placement_session import fixture, encode


class NormalSelectedImportControls(unittest.TestCase):
    def make(self, *, protected=True, nested=False, selected=True, locked_selected=False):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name).resolve();code=root/'code';code.mkdir()
        original=board()
        if not protected:original[:]=[n for n in original if n not in p.routes(original)]
        if locked_selected:p.routes(original)[1].append(['locked','yes'])
        imported=proposals(original)
        if locked_selected:
            generated=copy.deepcopy(p.routes(imported)[1])
            p.routes(imported)[0][:]=copy.deepcopy(p.routes(original)[0]);p.routes(imported)[1][:]=copy.deepcopy(p.routes(original)[1]);imported.append(generated)
        if not selected:
            p.routes(imported)[0][:]=copy.deepcopy(p.routes(original)[0])
        work=root/'incumbent' if nested else root
        work.mkdir(exist_ok=True);source=root/'source/owned.kicad_pcb';source.parent.mkdir();sx.write(source,original)
        candidate=work/'candidate/owned.kicad_pcb';candidate.parent.mkdir()
        selected_names=['LED'];protection=rs.protected_routes(original,selected_names) if selected else []
        policy=p.normal_selected_import_policy(original,selected_names) if selected else 'exact_non_uuid_lock_position_v2'
        proof={};tree=p.transplant_routes(original,imported,protected=protection,audit=proof,policy=policy,
            **({'selected_names':selected_names} if policy==p.SELECTED_PROPOSAL_IMPORT_POLICY else {}))
        sx.write(candidate,tree);(work/'refill').mkdir();sx.write(work/'refill'/candidate.name,tree)
        (work/'pre-refill.kicad_pcb').write_bytes(candidate.read_bytes())
        output=work/'imported.kicad_pcb';sx.write(output,imported);raw=work/'routes.ses';raw.write_bytes(encode(fixture()))
        derived=output.with_suffix('.routes-only.ses');filtered,metadata=adapter.fixed_placement_session(raw.read_bytes());derived.write_bytes(filtered)
        metadata.update(source_session=str(raw),import_session=str(derived),imported_board_sha256=p.sha(output));p.save_json(derived.with_suffix('.json'),metadata)
        worker={'name':'import','cwd':str(work),'status':'success','exit_code':0,'cleanup_complete':True,
            'wall_seconds':0,'cpu_seconds':0,'argv':[*f.SANDBOX,str(p.c.PYTHON),str(p.c.ROOT/'autorouter/native.py'),'import',str(candidate),str(output),str(raw)]}
        p.save_json(work/'import-process.json',worker)
        (code/'pipeline.py').write_text('NORMAL_SELECTED_PROPOSAL_IMPORT_POLICY="selected-proposals-exact-source-v1"\n')
        (code/'native.py').write_text('FIXED_PLACEMENT_SESSION_POLICY="fixed-placement-session-v1"\n')
        project=Path(p.__file__).resolve().parent
        for name in ('adapter.py','routing_scope.py','board_floor.py','preferences.py','sexpr.py'):(code/name).write_bytes((project/name).read_bytes())
        tools={'implementation_sha256':{'autorouter/'+file.name:p.sha(file) for file in code.iterdir()},
            'normal_selected_proposal_import_policy':p.NORMAL_SELECTED_PROPOSAL_IMPORT_POLICY}
        effective={**preferences.DEFAULTS,'scope':'selected_nets','profile':'completion-only','nets':['LED']}
        data={'schema':1,'scope':'selected_nets' if selected else 'whole_board_unlocked_routing','source':str(source),
            'source_hashes':p.tree_hash(source.parent),
            'candidate':str(candidate),'tools':tools,'steps':[copy.deepcopy(worker)],
            'protected_route_import':{'imported_sha256':p.sha(output),**proof}}
        # An honestly authored saved-refill fixture: no Native tool ran. Its
        # empty report, exact project copy, process and input hash agree.
        refill=work/'refill'/candidate.name;inputs=p.tree_hash(refill.parent);name='refill-drc'
        p.save_json(work/(name+'.json'),{
            '$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0',
            'source':source.name,'coordinate_units':'mm','date':'2026-10-09T19:00:00',
            'included_severities':['error','warning','exclusion'],'ignored_checks':[],
            'violations':[],'unconnected_items':[],'schematic_parity':[]})
        p.save_json(work/(name+'-binding.json'),{
            'source':str(refill),'input':str(refill),'saved':True,'before':inputs,'after':dict(inputs)})
        saved_worker={'name':name,'cwd':str(work),'status':'success','exit_code':0,'cleanup_complete':True,
            'wall_seconds':0,'cpu_seconds':0,'monitor_cpu_seconds':0,
            'argv':[str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors',
                    '--refill-zones','--exit-code-violations','--output',str(work/(name+'.json')),
                    '--save-board',str(refill)]}
        p.save_json(work/(name+'-process.json'),saved_worker)
        data['steps'].append(dict(saved_worker,validated_input_sha256=inputs[source.name],emitted_candidate=str(refill)))
        if selected:data.update(routing_preferences={'effective':effective},selected_net_binding=rs.bind(source.read_bytes(),['LED']),selected_net_audit=rs.audit(original,tree,['LED']),selected_dsn_binding={})
        def check():
            retained=pc.inventory(root,max_bytes=4*1024**2,max_files=100,max_entries=200)
            imports=adapter.check_fixed_placement_import(root,data,retained)
            policy=f.receipt_policy(data,root)
            contract=p.normal_import_contract(root,data,imports,input_policy=policy,original=original)
            if contract is not None:p.check_protected_import(root,data,original,candidate,protection,**contract)
            return contract
        return root,data,original,candidate,check

    def test_new_selected_protected_and_zero_protected_replay_exactly(self):
        for protected in (True,False):
            with self.subTest(protected=protected):
                root,data,original,candidate,check=self.make(protected=protected);before=pc.inventory(root)
                self.assertEqual(check(),{'expected_policy':p.SELECTED_PROPOSAL_IMPORT_POLICY,'selected_names':['LED']})
                self.assertEqual(pc.inventory(root),before)

    def test_combined_proof_policy_tool_and_scope_deletion_never_becomes_legacy(self):
        for mutation in ('proof','proof_and_scope','proof_scope_and_tools'):
            with self.subTest(mutation=mutation):
                root,data,_,_,check=self.make(protected=False);del data['protected_route_import']
                if mutation!='proof':
                    data['scope']='whole_board_unlocked_routing'
                    for name in ('routing_preferences','selected_net_binding','selected_net_audit','selected_dsn_binding'):data.pop(name)
                if mutation.endswith('tools'):data['tools'].pop('normal_selected_proposal_import_policy')
                with self.assertRaises(p.Rejected):check()

    def test_scope_names_proof_and_helper_tampering_refuse(self):
        for mutation in ('scope','names','layers','policy','helper_and_pin','captured_pipeline','literal_deleted','unknown_literal','nested_literal'):
            with self.subTest(mutation=mutation):
                root,data,_,_,check=self.make()
                if mutation=='scope':data['scope']='whole_board_unlocked_routing'
                elif mutation=='names':data['routing_preferences']['effective']['nets']=['GND']
                elif mutation=='layers':data['routing_preferences']['effective']['layers']=['F.Cu']
                elif mutation=='policy':data['protected_route_import']['policy']='exact_non_uuid_lock_position_v2'
                elif mutation=='helper_and_pin':(root/'code/routing_scope.py').unlink();data['tools']['implementation_sha256'].pop('autorouter/routing_scope.py')
                else:
                    producer=root/'code/pipeline.py'
                    producer.write_text('# drift\n') if mutation=='captured_pipeline' else producer.write_text('# missing literal\n' if mutation=='literal_deleted' else 'NORMAL_SELECTED_PROPOSAL_IMPORT_POLICY="unknown"\n' if mutation=='unknown_literal' else 'if True:\n NORMAL_SELECTED_PROPOSAL_IMPORT_POLICY="selected-proposals-exact-source-v1"\n')
                    if mutation!='captured_pipeline':data['tools']['implementation_sha256']['autorouter/pipeline.py']=p.sha(producer)
                with self.assertRaises((p.Rejected,ValueError,OSError)):check()

    def test_import_row_orphan_and_incumbent_annotation_cannot_hide_direct_worker(self):
        for mutation in ('steps','process','all_proofs','phase'):
            with self.subTest(mutation=mutation):
                root,data,_,_,check=self.make(protected=False)
                if mutation=='steps':data['steps']=[]
                elif mutation=='process':(root/'import-process.json').unlink()
                elif mutation=='all_proofs':
                    data['steps']=[]
                    for name in ('import-process.json','imported.routes-only.ses','imported.routes-only.json'):(root/name).unlink()
                else:
                    data['steps'][0]['phase']='incumbent';data.pop('protected_route_import')
                with self.assertRaises((p.Rejected,ValueError,OSError)):check()

    def test_genuine_old_captured_producer_and_strict_default_keep_original_contract(self):
        root,data,original,candidate,check=self.make(selected=False)
        self.assertEqual(check(),{})
        producer=root/'code/pipeline.py';project=Path(p.__file__).resolve().parents[1]
        producer.write_bytes((project/'evidence/default-tuning-native-001/code/pipeline.py').read_bytes())
        data['tools']['implementation_sha256']['autorouter/pipeline.py']=p.sha(producer);data['tools'].pop('normal_selected_proposal_import_policy')
        self.assertIsNone(check())
        p.check_protected_import(root,data,original,candidate,[])

    def test_new_whole_zero_protected_still_requires_own_strict_import_record(self):
        root,data,_,_,check=self.make(selected=False);self.assertEqual(check(),{})
        data.pop('protected_route_import')
        with self.assertRaisesRegex(p.Rejected,'complete proof'):check()

    def test_current_strict_source_declaration_and_tool_marker_cannot_downgrade(self):
        for fault in (None,'marker_deleted','marker_changed','literal_deleted','literal_and_marker_deleted','unknown_literal','older_policy_and_proof_deleted'):
            with self.subTest(fault=fault):
                root,data,_,_,check=self.make(selected=False)
                producer=root/'code/pipeline.py'
                raw=Path(p.__file__).read_text()
                # Current captured source also declares paired task-copper
                # workers. Author that synthetic contract before this test's
                # independent strict-via declaration fault.
                from tests.test_task_copper_contract import author_current_task_copper
                author_current_task_copper(root,data)
                literal="NORMAL_PROTECTED_VIA_IMPORT_POLICY='legacy-via-off-source-v3'"
                data['tools']['normal_protected_via_import_policy']=p.PROTECTED_VIA_IMPORT_POLICY
                if fault in ('marker_deleted','literal_and_marker_deleted'):
                    data['tools'].pop('normal_protected_via_import_policy')
                if fault=='marker_changed':data['tools']['normal_protected_via_import_policy']='unknown'
                if fault in ('literal_deleted','literal_and_marker_deleted'):raw=raw.replace(literal,'# removed declaration')
                if fault=='unknown_literal':raw=raw.replace(literal,"NORMAL_PROTECTED_VIA_IMPORT_POLICY='unknown'")
                if fault=='older_policy_and_proof_deleted':
                    raw=raw.replace("NORMAL_SELECTED_PROPOSAL_IMPORT_POLICY='selected-proposals-exact-source-v1'",'# removed older declaration')
                    data['tools'].pop('normal_selected_proposal_import_policy');data.pop('protected_route_import')
                producer.write_text(raw);data['tools']['implementation_sha256']['autorouter/pipeline.py']=p.sha(producer)
                if fault is None:self.assertEqual(check(),{})
                else:
                    with self.assertRaises(p.Rejected):check()

    def test_deleted_import_population_and_unrecognized_nested_worker_refuse(self):
        for nested,scope in ((False,'selected_nets'),(False,'whole_board_unlocked_routing'),(True,'selected_nets'),(True,'whole_board_unlocked_routing')):
            with self.subTest(nested=nested,scope=scope):
                root,data,original,_,_=self.make(protected=False,nested=nested);data.pop('protected_route_import')
                if scope!='selected_nets':
                    data['scope']=scope
                    for name in ('routing_preferences','selected_net_binding','selected_net_audit','selected_dsn_binding'):data.pop(name)
                if not nested:
                    data['steps']=[]
                    for name in ('imported.kicad_pcb','routes.ses','import-process.json','imported.routes-only.ses','imported.routes-only.json'):(root/name).unlink()
                else:data['steps'][0]['phase']='incumbent'
                imports=adapter.check_fixed_placement_import(root,data,pc.inventory(root))
                with self.assertRaisesRegex(p.Rejected,'exact direct import population'):
                    p.normal_import_contract(root,data,imports,input_policy=f.receipt_policy(data,root),original=original)
                data.update(input_policy='board-floors-v1')
                with self.assertRaises(p.Rejected):f.receipt_policy(data,root)

    def test_existing_floor_receipt_keeps_its_real_owned_import_without_normal_proof(self):
        from tests.test_board_floor_policy import FloorReceipt
        owned=FloorReceipt(methodName='runTest');owned.setUp();self.addCleanup(owned.doCleanups)
        self.assertNotIn('protected_route_import',owned.data)
        self.assertTrue(p.check_result(owned.receipt)['current'])

    def test_selected_locked_source_uses_source_derived_strict_fallback_and_legacy_stays_closed(self):
        root,data,original,candidate,check=self.make(locked_selected=True)
        self.assertEqual(p.normal_selected_import_policy(original,['LED']),'exact_non_uuid_lock_position_v2')
        self.assertEqual(check(),{})
        self.assertTrue(all(node in p.routes(sx.read(candidate)) for node in rs.protected_routes(original,['LED'])))
        data['protected_route_import']['policy']=p.SELECTED_PROPOSAL_IMPORT_POLICY
        with self.assertRaisesRegex(p.Rejected,'original locks'):check()
        with self.assertRaisesRegex(p.Rejected,'locked selected'):
            p.transplant_routes(original,sx.read(root/'imported.kicad_pcb'),protected=rs.protected_routes(original,['LED']),
                policy=p.SELECTED_PROPOSAL_IMPORT_POLICY,selected_names=['LED'])
        source=Path(data['source']);request={'started':0,'started_utc':'authored','parent_cpu':0,'effective':data['routing_preferences']['effective']}
        with patch.object(p,'sha',return_value=p.c.JAR_SHA256),patch.object(p,'check_storage'),patch.object(p,'Job',side_effect=RuntimeError('authored stop before any worker')) as job:
            with self.assertRaisesRegex(RuntimeError,'authored stop'):p.route(source,root/'new-output',_preferences=request)
            job.assert_called_once();self.assertFalse((root/'new-output').exists())
        source.with_suffix('.kicad_pro').write_text('{}\n');sx.one(original,'version')[1]='20240108';sx.write(source,original)
        with self.assertRaisesRegex(p.Rejected,'unqualified board format'):
            p.preflight(source,task_scope=('selected_nets','native','source_all'))


if __name__=='__main__':unittest.main()
