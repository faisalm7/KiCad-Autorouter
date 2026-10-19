"""Pure scalar API/ownership/lifetime guards, not native routing evidence."""
import copy,gc,json,unittest,weakref
from autorouter import netclass_native as n

VALUES={'width_nm':600000,'clearance_nm':200000,'via_diameter_nm':600000,'via_drill_nm':300000}

class Parent:
 def __init__(self,name='POWER',values=None,priority=1,flags=None):
  self.name=name;self.values=copy.deepcopy(VALUES if values is None else values);self.priority=priority;self.flags={'width_nm':True,'clearance_nm':True,'via_diameter_nm':True,'via_drill_nm':1} if flags is None else flags
 def GetName(self):return self.name
 def GetPriority(self):return self.priority
 def __getattr__(self,method):
  for key,getter,_,flag in n.FIELDS:
   if method==getter:return lambda:self.values[key]
   if method==flag:return lambda:self.flags[key]
  raise AssertionError('unpermitted parent API: '+method)

class NativeClass:
 def __init__(self,name='POWER,Default',parents=None,values=None):
  self.name=name;self.parents=[Parent() for _ in n.FIELDS] if parents is None else parents;self.values=copy.deepcopy(VALUES if values is None else values)
 def GetName(self):return self.name
 def __getattr__(self,method):
  for index,(key,getter,parent_getter,_) in enumerate(n.FIELDS):
   if method==getter:return lambda:self.values[key]
   if method==parent_getter:return lambda:self.parents[index]
  raise AssertionError('unpermitted class API: '+method)

class ScalarClassGuards(unittest.TestCase):
 def test_floor_observation_uses_loaded_settings_and_rejects_malformed_values(self):
  from types import SimpleNamespace
  from autorouter.floor_context import FLOORS
  settings=SimpleNamespace(**{attribute:100000 for attribute in FLOORS.values()})
  board=SimpleNamespace(GetDesignSettings=lambda:settings)
  self.assertEqual(n.observe_floors(board),dict.fromkeys(FLOORS,100000))
  for value in (True,False,-1,1.0,None,n.MAX_NATIVE_INTEGER+1):
   setattr(settings,FLOORS['min_clearance'],value)
   with self.subTest(value=value),self.assertRaises(ValueError):n.observe_floors(board)
  setattr(settings,FLOORS['min_clearance'],0)
  self.assertEqual(n.observe_floors(board)['min_clearance'],0)
 def test_exact_opaque_name_four_parent_scalars_json_and_no_extra_methods(self):
  cls=NativeClass();before={'name':cls.name,'values':copy.deepcopy(cls.values),'parents':[copy.deepcopy(x.__dict__) for x in cls.parents]};result=n.observe_class(cls)
  self.assertEqual(result['class'],'POWER,Default');self.assertEqual(set(result),{'class','parameter_parents',*VALUES});self.assertEqual({k:result[k] for k in VALUES},VALUES)
  self.assertEqual(result['parameter_parents']['via_drill_nm'],{'name':'POWER','value_nm':300000,'specified':True,'priority':1});self.assertEqual(json.loads(json.dumps(result)),result)
  self.assertEqual(cls.name,before['name']);self.assertEqual(cls.values,before['values']);self.assertEqual([x.__dict__ for x in cls.parents],before['parents'])
 def test_preserves_encoded_backslashes_commas_spaces_and_unicode_without_decode(self):
  encoded='Power\\,domain, Default,電源';parents=[Parent(name='Power,domain') for _ in n.FIELDS];result=n.observe_class(NativeClass(encoded,parents))
  self.assertEqual(result['class'],encoded);self.assertEqual(result['parameter_parents']['width_nm']['name'],'Power,domain');self.assertNotIn('constituents',result)
 def test_specified_bool_or_int0_1_only_and_false_not_inferred(self):
  for flag in (True,False,1,0):
   parents=[Parent(flags={k:flag for k in VALUES}) for _ in n.FIELDS];result=n.observe_class(NativeClass(parents=parents));self.assertIs(result['parameter_parents']['via_drill_nm']['specified'],bool(flag))
  for flag in (None,2,-1,1.0,'true',[],{}):
   with self.subTest(flag=flag),self.assertRaises(ValueError):n.observe_class(NativeClass(parents=[Parent(flags={k:flag for k in VALUES}) for _ in n.FIELDS]))
 def test_nonpositive_bool_float_null_or_oversized_effective_and_parent_values_reject(self):
  for value in (0,-1,True,False,1.0,float('nan'),None,n.MAX_NATIVE_INTEGER+1):
   values={**VALUES,'width_nm':value}
   with self.subTest(value=value),self.assertRaises(ValueError):n.observe_class(NativeClass(values=values))
   with self.subTest(parent_value=value),self.assertRaises(ValueError):n.observe_class(NativeClass(parents=[Parent(values=values) for _ in n.FIELDS]))
 def test_integer_parent_priority_including_unset_ctor_minus1_and_intmax(self):
  for priority in (-1,0,1,n.MAX_NATIVE_INTEGER):
   result=n.observe_class(NativeClass(parents=[Parent(priority=priority) for _ in n.FIELDS]));self.assertEqual(result['parameter_parents']['width_nm']['priority'],priority)
  for priority in (-2,n.MAX_NATIVE_INTEGER+1,True,1.0,None,'1'):
   with self.subTest(priority=priority),self.assertRaises(ValueError):n.observe_class(NativeClass(parents=[Parent(priority=priority) for _ in n.FIELDS]))
 def test_null_class_or_parent_missing_and_noncallable_getters_fail(self):
  with self.assertRaises(ValueError):n.observe_class(None)
  with self.assertRaises(ValueError):n.observe_class(NativeClass(parents=[None,Parent(),Parent(),Parent()]))
  class Missing:pass
  with self.assertRaises(ValueError):n.observe_class(Missing())
  cls=NativeClass();cls.GetViaDrillParent=42
  with self.assertRaises(ValueError):n.observe_class(cls)
 def test_bounded_names_reject_wrong_type_controls_surrogates_multibyte_overflow(self):
  for name in (None,42,False,'','name\x00','name\n','name\x7f','x'*(n.MAX_NAME_BYTES+1),'é'*(n.MAX_NAME_BYTES//2+1),'\ud800'):
   with self.subTest(name=repr(name)),self.assertRaises(ValueError):n.observe_class(NativeClass(name))
   with self.subTest(parent_name=repr(name)),self.assertRaises(ValueError):n.observe_class(NativeClass(parents=[Parent(name=name) for _ in n.FIELDS]))
  self.assertEqual(n.observe_class(NativeClass('x'*n.MAX_NAME_BYTES))['class'],'x'*n.MAX_NAME_BYTES)
 def test_all_owned_parent_proxies_live_through_every_scalar_getter(self):
  references=[];observed=[]
  class CheckedParent(Parent):
   def GetName(self):
    gc.collect();observed.append(sum(x() is not None for x in references));return super().GetName()
  class EphemeralClass(NativeClass):
   def __init__(self):self.name='POWER,Default';self.values=VALUES
   def __getattr__(self,method):
    for key,getter,parent_getter,_ in n.FIELDS:
     if method==getter:return lambda:self.values[key]
     if method==parent_getter:
      def create():
       gc.collect();parent=CheckedParent();references.append(weakref.ref(parent));return parent
      return create
    raise AssertionError('unpermitted class API: '+method)
  result=n.observe_class(EphemeralClass());self.assertEqual(observed,[4,4,4,4]);self.assertEqual(len(result['parameter_parents']),4);gc.collect();self.assertTrue(all(x() is None for x in references))
 def test_cancellation_is_not_reclassified_as_a_native_value_failure(self):
  cls=NativeClass();cls.GetViaDrillParent=lambda:(_ for _ in ()).throw(KeyboardInterrupt())
  with self.assertRaises(KeyboardInterrupt):n.observe_class(cls)
if __name__=='__main__':unittest.main()
