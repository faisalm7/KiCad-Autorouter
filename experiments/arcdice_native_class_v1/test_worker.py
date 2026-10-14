"""Closed native-name decoding controls; no mocked routing/GUI proof."""
import unittest
from experiments.arcdice_native_class_v1.worker import namespace,decode
class EncodedNames(unittest.TestCase):
 def project(self,names):return {'net_settings':{'classes':[{'name':x} for x in names]}}
 def test_ambiguous_source_namespace_refuses(self):
  for names in [['Default','default'],['Default','kicad_default'],['Default','POWER,Default'],['Default','POWER','power'],['POWER'],['Default','']]:
   with self.subTest(names=names),self.assertRaises(ValueError):namespace(self.project(names))
 def test_root_and_order_preserved_without_pattern_evaluation(self):
  names=namespace(self.project(['Default','POWER','SIGNAL']))
  self.assertEqual(decode('POWER,Default',names),['POWER','Default'])
  self.assertEqual(decode('Default',names),['Default'])
  self.assertEqual(decode('Default,POWER',names),['Default','POWER'])
 def test_unknown_empty_duplicate_or_excess_encoding_refuses(self):
  names=['Default','POWER','SIGNAL']
  for value in ['','POWER,','POWER,POWER','UNKNOWN,Default','POWER\x00,Default',','.join(['POWER']*17)]:
   with self.subTest(value=value),self.assertRaises(ValueError):decode(value,names)
 def test_string_and_source_population_caps(self):
  with self.assertRaises(ValueError):decode('A'*4097,['A'*4097])
  with self.assertRaises(ValueError):namespace(self.project(['Default']+['N'+str(x) for x in range(16)]))
if __name__=='__main__':unittest.main()
