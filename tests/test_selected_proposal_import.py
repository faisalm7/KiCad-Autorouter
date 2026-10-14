"""Pure selected-proposal scope/provenance controls; never a Native pass."""
import copy
import tempfile
import unittest
import uuid
from pathlib import Path
from autorouter import pipeline as p,routing_scope as rs,sexpr as sx


def uid(name):return str(uuid.uuid5(uuid.NAMESPACE_URL,'owned-selected-proposal/'+name))
def segment(name,net,end='2.0005'):
    return sx.parse(f'(segment (start 0 0) (end {end} 0) (width .5) (layer "F.Cu") (net {net}) (uuid "{uid(name)}"))')
def board():
    tree=sx.parse('(kicad_pcb (version 20241229) (net 0 "") (net 1 "GND") (net 2 "LED") (net 3 "OTHER") '
        f'(uuid "{uid("board")}") (footprint "Owned" (uuid "{uid("fp")}") '
        f'(pad "1" smd rect (net 1 "GND") (uuid "{uid("pad1")}")) '
        f'(pad "2" smd rect (net 2 "LED") (uuid "{uid("pad2")}")) '
        f'(pad "3" smd rect (net 3 "OTHER") (uuid "{uid("pad3")}"))))')
    tree.extend([segment('source-protected','1'),segment('source-selected','2')]);return tree

def proposals(original):
    imported=copy.deepcopy(original);imported[:]=[n for n in imported if n not in p.routes(imported)]
    imported.extend([segment('ignored-rounded','1',end='2'),segment('generated-selected','2',end='3')]);return imported


class SelectedProposalImportTests(unittest.TestCase):
    def apply(self,original,imported,*,protected=None,names=None):
        names=['LED'] if names is None else names
        protected=rs.protected_routes(original,names) if protected is None else protected
        audit={};candidate=p.transplant_routes(original,imported,protected=protected,audit=audit,
            policy=p.SELECTED_PROPOSAL_IMPORT_POLICY,selected_names=names)
        return candidate,audit

    def reader_fixture(self,original,imported):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);directory=Path(temporary.name).resolve()
        sx.write(directory/'imported.kicad_pcb',imported);candidate,audit=self.apply(original,imported);sx.write(directory/'candidate.kicad_pcb',candidate)
        data={'scope':'selected_nets','protected_route_import':{'imported_sha256':p.sha(directory/'imported.kicad_pcb'),**audit}}
        def check(**kw):return p.check_protected_import(directory,data,original,directory/'candidate.kicad_pcb',rs.protected_routes(original,['LED']),**kw)
        return directory,data,check

    def test_quantized_or_changed_nonselected_proposal_is_discarded_not_normalized(self):
        original=board();imported=proposals(original);original_before=copy.deepcopy(original);imported_before=copy.deepcopy(imported)
        candidate,audit=self.apply(original,imported)
        self.assertEqual(p.routes(candidate)[0],p.routes(original)[0]);self.assertEqual(sx.one(p.routes(candidate)[0],'end')[1],'2.0005')
        self.assertEqual(p.routes(candidate)[1],p.routes(imported)[1]);self.assertTrue(rs.audit(original,candidate,['LED'])['scope_passed'])
        self.assertEqual(len(audit['ignored_nonselected_proposals']),1);self.assertEqual(audit['ignored_nonselected_proposals'][0]['net_name'],'GND')
        self.assertEqual(audit['requested_names'],['LED']);self.assertEqual(original,original_before);self.assertEqual(imported,imported_before)
        with self.assertRaises(p.Rejected):p.transplant_routes(rs.task(original,['LED']),imported,protected=rs.protected_routes(original,['LED']),policy='exact_non_uuid_lock_position_v2')

    def test_reader_rederives_all_ignored_records_even_if_import_hash_is_updated(self):
        original=board();imported=proposals(original);directory,data,check=self.reader_fixture(original,imported)
        options=dict(expected_policy=p.SELECTED_PROPOSAL_IMPORT_POLICY,selected_names=['LED']);check(**options)
        changed=sx.read(directory/'imported.kicad_pcb');sx.one(p.routes(changed)[0],'end')[1]='4';sx.write(directory/'imported.kicad_pcb',changed)
        data['protected_route_import']['imported_sha256']=p.sha(directory/'imported.kicad_pcb')
        with self.assertRaises(p.Rejected):check(**options)
        sx.write(directory/'imported.kicad_pcb',imported);data['protected_route_import']['imported_sha256']=p.sha(directory/'imported.kicad_pcb')
        data['protected_route_import']['ignored_nonselected_proposals']=[]
        with self.assertRaises(p.Rejected):check(**options)

    def test_policy_deletion_and_normal_reader_refused_even_without_protected_routes(self):
        original=board();original[:]=[n for n in original if n not in p.routes(original)];directory,data,check=self.reader_fixture(original,proposals(original))
        options=dict(expected_policy=p.SELECTED_PROPOSAL_IMPORT_POLICY,selected_names=['LED']);check(**options)
        with self.assertRaises(p.Rejected):check()  # Normal receipt path is not admitted.
        del data['protected_route_import']
        with self.assertRaises(p.Rejected):check(**options)
        check()  # Historical zero-protected default behavior remains unchanged.

    def test_requested_names_complete_source_protection_and_source_intent_bound(self):
        original=board();imported=proposals(original)
        with self.assertRaises(p.Rejected):self.apply(original,imported,protected=[])
        altered=rs.protected_routes(original,['LED']);sx.one(altered[0],'width')[1]='.4'
        with self.assertRaises(p.Rejected):self.apply(original,imported,protected=altered)
        directory,data,check=self.reader_fixture(original,imported)
        options=dict(expected_policy=p.SELECTED_PROPOSAL_IMPORT_POLICY,selected_names=['LED'])
        data['protected_route_import']['requested_names']=['GND']
        with self.assertRaises(p.Rejected):check(**options)
        data['protected_route_import']['requested_names']=['LED'];original.append(['generator','"changed source intent"'])
        with self.assertRaises(p.Rejected):check(**options)

    def test_locked_selected_source_or_generated_copper_is_refused(self):
        original=board();p.routes(original)[1].append(['locked','yes'])
        with self.assertRaises(p.Rejected):self.apply(original,proposals(original))
        original=board();imported=proposals(original);p.routes(imported)[1].append(['locked','yes'])
        with self.assertRaises(p.Rejected):self.apply(original,imported)

    def test_net_aliases_unknown_nets_duplicate_ids_and_source_collisions_refused(self):
        for mode in ('source_code','source_name','source_pad_alias','import_code','import_pad_alias','unknown_net','import_uuid','source_protected_collision'):
            original=board();imported=proposals(original)
            if mode=='source_code':original.append(['net','1','"NEW"'])
            elif mode=='source_name':original.append(['net','4','"LED"'])
            elif mode=='source_pad_alias':sx.one(sx.children(sx.one(original,'footprint'),'pad')[0],'net')[2]='"LED"'
            elif mode=='import_code':imported.append(['net','1','"NEW"'])
            elif mode=='import_pad_alias':sx.one(sx.children(sx.one(imported,'footprint'),'pad')[0],'net')[2]='"LED"'
            elif mode=='unknown_net':imported.append(['net','4','"UNKNOWN"']);sx.one(p.routes(imported)[0],'net')[1]='4'
            elif mode=='import_uuid':sx.one(p.routes(imported)[1],'uuid')[1]=sx.one(p.routes(imported)[0],'uuid')[1]
            else:sx.one(p.routes(imported)[1],'uuid')[1]=sx.one(p.routes(original)[0],'uuid')[1]
            with self.subTest(mode=mode),self.assertRaises((p.Rejected,ValueError)):self.apply(original,imported)

    def test_modern_named_import_maps_to_exact_legacy_source_identity(self):
        original=board();imported=proposals(original);table={n[1]:n[2] for n in sx.children(imported,'net')}
        imported[:]=[n for n in imported if n not in sx.children(imported,'net')]
        def convert(node):
            for child in node[1:]:
                if isinstance(child,list) and child:
                    if child[0]=='net':child[:]=['net',table[child[1]]]
                    else:convert(child)
        convert(imported);sx.one(imported,'version')[1]='20260206'
        candidate,audit=self.apply(original,imported)
        self.assertEqual(sx.one(p.routes(candidate)[1],'net'),['net','2']);self.assertEqual(audit['selected_proposals'][0]['net_name'],'LED')
        self.assertEqual(p.immutable(candidate),p.immutable(original))

    def test_old_strict_policy_and_default_reader_continue_to_reconcile_exact_import(self):
        original=board();imported=proposals(original);p.routes(imported)[0][:]=copy.deepcopy(p.routes(original)[0]);sx.one(p.routes(imported)[0],'uuid')[1]='"'+uid('regenerated-protected')+'"'
        protected=rs.protected_routes(original,['LED']);audit={};candidate=p.transplant_routes(rs.task(original,['LED']),imported,protected=protected,audit=audit,policy='exact_non_uuid_lock_position_v2')
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp).resolve();sx.write(directory/'imported.kicad_pcb',imported);sx.write(directory/'candidate.kicad_pcb',candidate)
            data={'scope':'selected_nets','protected_route_import':{'imported_sha256':p.sha(directory/'imported.kicad_pcb'),**audit}}
            p.check_protected_import(directory,data,original,directory/'candidate.kicad_pcb',protected)
        self.assertEqual(p.routes(candidate)[0],protected[0])
        with self.assertRaises(p.Rejected):p.transplant_routes(original,imported,selected_names=['LED'])
