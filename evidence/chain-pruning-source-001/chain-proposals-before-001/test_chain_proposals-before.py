"""Deletion scope and ambiguity controls; these do not establish routing quality."""
import copy,unittest
from unittest.mock import patch
from autorouter import chain_proposals as c,sexpr as sx,strategy as s,pipeline as p

def segment(uid,a,b,net='1',layer='F.Cu',width='0.25',locked=False):
 return sx.parse(f'(segment (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (net {net}) (width {width}) (layer "{layer}") (uuid "{uid}")'+(' (locked yes)' if locked else '')+')')
def tree(routes):return ['kicad_pcb',*routes]
class ChainProposalControls(unittest.TestCase):
 def path(self):return [segment(str(i),(i,0),(i+1,0)) for i in range(4)]
 def test_exact_native_grid_refuses_rounding_nonfinite_and_large_values(self):
  self.assertEqual(c.nm('0.000001'),1)
  for atom in ('0.0000001','NaN','Infinity','1000001',True,'1'*41):
   with self.subTest(atom=atom),self.assertRaises(ValueError):c.nm(atom)
 def test_groups_are_deterministic_eligible_deletions_and_source_stays_exact(self):
  t=tree(self.path()+[segment('signal',(0,10),(8,10),'2')]);before=copy.deepcopy(t)
  a=c.build(t,{'1'},[]);b=c.build(tree(list(reversed(t[1:]))),{'1'},[])
  self.assertFalse(a['declined_reason']);self.assertEqual(a['proposals'],b['proposals']);self.assertEqual(len(a['proposals']),1)
  group=a['proposals'][0];self.assertEqual(group['segment_count'],4)
  out=s.delete_routes(t,group['route_ids'],{'1'},[]);self.assertEqual(len(p.routes(out)),1);self.assertEqual(t,before)
 def test_branch_protected_via_and_pad_envelopes_stop_continuations(self):
  t=tree(self.path()+[segment('branch',(2,0),(2,2),locked=True)])
  groups=c.build(t,{'1'},[t[-1]])['proposals'];self.assertEqual(sorted(g['segment_count'] for g in groups),[2,2]);self.assertTrue(all(s.route_id(t[-1]) not in g['route_ids'] for g in groups))
  via=sx.parse('(via (at 2 0) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net 1) (uuid "via"))')
  self.assertEqual(sorted(g['segment_count'] for g in c.build(tree(self.path()+[via]),{'1'},[])['proposals']),[2,2])
  fp=sx.parse('(footprint "owned" (at 2 0 37) (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu") (net 1)))')
  self.assertEqual(sorted(g['segment_count'] for g in c.build(tree(self.path()+[fp]),{'1'},[])['proposals']),[2,2])
 def test_other_net_layer_or_width_never_continues_a_group(self):
  for changed in (segment('tail',(1,0),(2,0),net='2'),segment('tail',(1,0),(2,0),layer='B.Cu'),segment('tail',(1,0),(2,0),width='0.3')):
   self.assertEqual(c.build(tree([self.path()[0],changed]),{'1','2'},[])['proposals'],[])
 def test_closed_cycles_and_parallel_overlaps_are_not_grouped(self):
  cycle=tree([segment('a',(0,0),(1,0)),segment('b',(1,0),(1,1)),segment('c',(1,1),(0,0))])
  self.assertEqual(c.build(cycle,{'1'},[])['proposals'],[])
  parallel=tree([segment('a',(0,0),(1,0)),segment('b',(1,0),(0,0))])
  self.assertEqual(c.build(parallel,{'1'},[])['proposals'],[])
 def test_limits_and_malformed_input_decline_with_visible_reason(self):
  with patch.object(c,'MAX_ROUTES',3):self.assertIn('ceiling',c.build(tree(self.path()),{'1'},[])['declined_reason'])
  bad=self.path();sx.one(bad[0],'start')[1]='0.0000001';self.assertIn('coordinate',c.build(tree(bad),{'1'},[])['declined_reason'])
  with patch.object(c,'MAX_SEGMENTS',3):self.assertEqual(c.build(tree(self.path()),{'1'},[])['oversize_groups'],1)
