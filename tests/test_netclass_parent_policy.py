"""Experimental closed-native class proof; pure controls are not routing proof."""
import copy,unittest
from autorouter import netclass as n,sexpr as sx
from tests.test_netclass import fixtures

def example():
 tree,native,project=fixtures()
 default,power=project['net_settings']['classes'];default['priority']=2147483647;power['priority']=1
 signal={**default,'name':'Signal','priority':0,'track_width':.25};project['net_settings']['classes'].append(signal)
 project['net_settings']['netclass_patterns']=[{'pattern':'G*','netclass':'Power'},{'pattern':'LED*','netclass':'Signal'}]
 for row in native['nets']:
  cls=default if row['class']=='Default' else power
  if row['class']!='Default':row['class']+=',Default'
  row['parameter_parents']={key:{'name':cls['name'],'value_nm':row[key],'specified':True,'priority':cls['priority']} for key,_,_ in n._DIMENSIONS}
 network=sx.one(tree,'network');sx.children(network,'class')[1][1]='Power,Default'
 row=copy.deepcopy(native['nets'][0]);row.update(name='LED1',netcode=3,**{'class':'Signal,Default'},width_nm=250000)
 row['parameter_parents']={key:{'name':'Signal','value_nm':row[key],'specified':True,'priority':0} for key,_,_ in n._DIMENSIONS};native['nets'].append(row)
 network.append(['net','LED1',['pins','J3-1']]);cls=copy.deepcopy(sx.children(network,'class')[0]);cls[1]='Signal,Default';cls[2]='LED1';sx.one(sx.one(cls,'rule'),'width')[1]='250';network.append(cls)
 return tree,native,project

class NativeParentPolicy(unittest.TestCase):
 def test_returned_parent_records_do_not_alias_native_evidence(self):
  _,native,project=example();before=copy.deepcopy(native)
  audited=n.audit_native(native,project,parent_policy=True)
  audited['nets'][1]['parameter_parents']['width_nm']['value_nm']+=1
  self.assertEqual(native,before)
 def test_experimental_three_class_mapping_preserves_opaque_identity(self):
  tree,native,project=example();result=n.audit_mapping(tree,native,project,parent_policy=True)
  self.assertTrue(result['passed']);self.assertFalse(result['routing_accepted']);self.assertFalse(result['policy']['pattern_evaluation_in_python'])
  self.assertEqual(result['membership']['LED1'],'Signal,Default')
  with self.assertRaises(ValueError):n.audit_mapping(tree,native,project)
 def test_unknown_default_targets_priorities_and_ambiguous_namespace_refuse(self):
  for change in ['comma','case_alias','implicit','default_target','missing_priority','boolean_priority']:
   tree,native,project=example()
   if change=='comma':project['net_settings']['classes'][1]['name']='Power,Default'
   elif change=='case_alias':project['net_settings']['classes'][2]['name']='power'
   elif change=='implicit':project['net_settings']['netclass_patterns'][0]['netclass']='Unknown'
   elif change=='default_target':project['net_settings']['netclass_patterns'][0]['netclass']='Default'
   elif change=='missing_priority':del project['net_settings']['classes'][1]['priority']
   else:project['net_settings']['classes'][1]['priority']=True
   with self.subTest(change=change),self.assertRaises(ValueError):n.audit_mapping(tree,native,project,parent_policy=True)
 def test_missing_wrong_unspecified_priority_and_value_parents_refuse(self):
  for change in ['missing','wrong_name','not_specified','priority','value','bool_value']:
   tree,native,project=example();row=native['nets'][1];parent=row['parameter_parents']['width_nm']
   if change=='missing':del row['parameter_parents']['width_nm']
   elif change=='wrong_name':parent['name']='Default'
   elif change=='not_specified':parent['specified']=False
   elif change=='priority':parent['priority']=0
   elif change=='bool_value':parent['value_nm']=True
   else:parent['value_nm']+=1
   with self.subTest(change=change),self.assertRaises(ValueError):n.audit_mapping(tree,native,project,parent_policy=True)
 def test_unknown_duplicate_reversed_or_multi_nondefault_native_class_refuse(self):
  for identity in ['Implicit,Default','Power,Power','Default,Power','Power,Signal,Default','Power,']:
   tree,native,project=example();native['nets'][1]['class']=identity
   with self.subTest(identity=identity),self.assertRaises(ValueError):n.audit_mapping(tree,native,project,parent_policy=True)
 def test_original_floor_native_target_and_dsn_identity_tamper_refuse(self):
  for change in ['floor','target','dsn_name','dsn_width']:
   tree,native,project=example()
   if change=='floor':project['board']['design_settings']['rules']['min_track_width']=.3
   elif change=='target':native['nets'][1]['width_nm']-=1;native['nets'][1]['parameter_parents']['width_nm']['value_nm']-=1
   elif change=='dsn_name':sx.children(sx.one(tree,'network'),'class')[1][1]='Power'
   else:sx.one(sx.one(sx.children(sx.one(tree,'network'),'class')[1],'rule'),'width')[1]='400'
   with self.subTest(change=change),self.assertRaises(ValueError):n.audit_mapping(tree,native,project,parent_policy=True)
if __name__=='__main__':unittest.main()
