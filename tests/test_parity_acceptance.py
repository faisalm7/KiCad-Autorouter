"""Pure final-validator controls; real native evidence remains separate."""
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from autorouter import pipeline as p,sexpr as sx

class CompleteSchematicAcceptance(unittest.TestCase):
 def test_every_scope_and_trial_final_validator_checks_captured_schematic(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp).resolve();candidate=root/'candidate';candidate.mkdir();board=candidate/'board.kicad_pcb'
   tree=sx.parse('(kicad_pcb (version 20260206) (layers (0 "F.Cu" signal) (2 "B.Cu" signal)))');sx.write(board,tree)
   board.with_suffix('.kicad_pro').write_text('{}');board.with_suffix('.kicad_sch').write_text('captured native schematic: pure seam')
   hashes=p.tree_hash(candidate);calls=[]
   class Job:
    out=root/'job'
    def drc(self,name,path,save=False,**kwargs):
     calls.append((name,save,kwargs));return {'pure_seam':True}
   Job.out.mkdir()
   with patch.object(p,'netclass_policy',return_value=None):
    p.validate_candidate(Job(),tree,board,hashes,[],schematic_parity=False)
   self.assertEqual(calls,[('refill-drc',True,{}),('final-drc',False,{'schematic_parity':True})])
   self.assertEqual(p.tree_hash(candidate),hashes)
 def test_declaration_and_process_policy_follow_complete_original_input(self):
  for scope in ('whole_board_unlocked_routing','partial_completion','selected_nets'):
   row={'scope':scope,'source':'/project/board.kicad_pcb','source_hashes':{'board.kicad_sch':'bound'},'schematic_parity':'checked by final native DRC'}
   self.assertTrue(p.selected_parity_required(row))
   row['schematic_parity']='unavailable: no native schematic in source project'
   with self.assertRaisesRegex(p.Rejected,'parity declaration'):p.selected_parity_required(row)
   row['source_hashes']={};self.assertFalse(p.selected_parity_required(row))
  self.assertFalse(p.selected_parity_required({'scope':'whole_board_unlocked_routing','schematic_parity':'not checked'}))
 def test_schematic_net_mismatch_warning_cannot_be_routing_accepted(self):
  raw={'opens':0,'blocking':0,'warnings':1,'exclusions':0,'ignored_checks':[],
       'findings':[{'type':'net_conflict','severity':'warning','items':[],'description':'PCB pad differs from schematic'}]}
  self.assertFalse(p.native_accepted(raw));self.assertIn('net_conflict',' '.join(p.native_rejection_reasons(raw)))
  raw['findings']=[];raw['warnings']=0;raw['ignored_checks']=[{'key':'net_conflict'}]
  self.assertFalse(p.native_accepted(raw))

if __name__=='__main__':unittest.main()
