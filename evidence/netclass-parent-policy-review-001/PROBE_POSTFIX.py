"""Reviewer-only authored pure controls; never native routing proof."""
import copy, hashlib, io, json, subprocess, sys, unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
OWN = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from autorouter import netclass as n, sexpr as sx
from test_netclass_parent_policy import example
from test_netclass import fixtures
import test_netclass_parent_policy, test_netclass_native

FILES = ['autorouter/netclass.py', 'autorouter/netclass_native.py',
         'autorouter/native.py', 'tests/test_netclass_parent_policy.py',
         'tests/test_netclass_native.py', 'tests/test_netclass.py']
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def pins(tree): return sx.children(sx.one(tree, 'network'), 'net')
def classes(tree): return sx.children(sx.one(tree, 'network'), 'class')
def run_case(name, mutate=None, expected='reject'):
    tree, native, project = example()
    if mutate: mutate(tree, native, project)
    before = copy.deepcopy((tree, native, project))
    try:
        result = n.audit_mapping(tree, native, project, parent_policy=True)
        observed = 'pass'
        detail = {'membership': result['membership'], 'routing_accepted': result['routing_accepted']}
    except Exception as exc:
        observed = 'reject'
        detail = {'error_type': type(exc).__name__, 'error': str(exc)}
    unchanged = before == (tree, native, project)
    return {'case': name, 'expected': expected, 'observed': observed,
            'matched': observed == expected and unchanged, 'inputs_unchanged': unchanged, **detail}

def change_parent(key, value):
    return lambda t, m, p: m['nets'][1]['parameter_parents']['width_nm'].__setitem__(key, value)
def zero_pad(t, m, p):
    m['nets'][2]['copper_pad_count'] = 0
    sx.one(t, 'network').remove(pins(t)[2])
def remove_zero_member(t, m, p):
    zero_pad(t,m,p); classes(t)[2].remove('LED1')
def remove_zero_class(t,m,p):
    zero_pad(t,m,p); sx.one(t,'network').remove(classes(t)[2])
def add_unknown_class(t,m,p):
    extra=copy.deepcopy(classes(t)[1]);extra[1]='Unknown';extra.remove('GND');sx.one(t,'network').append(extra)
def duplicate_class(t,m,p): sx.one(t,'network').append(copy.deepcopy(classes(t)[1]))
def shadow_case(t,m,p): p['net_settings']['classes'][2]['name']='power'
def source_parent_mismatch(t,m,p):
    p['net_settings']['classes'][1]['track_width']=.6
def wrong_parents_consistent_dimensions(t,m,p):
    for parent in m['nets'][1]['parameter_parents'].values(): parent['name']='Signal'
def reorder_declared_classes(t,m,p): p['net_settings']['classes'].reverse()
def same_priority_unambiguous(t,m,p):
    p['net_settings']['classes'][2]['priority']=1
    for parent in m['nets'][2]['parameter_parents'].values(): parent['priority']=1
def two_nondefault(t,m,p): m['nets'][1]['class']='Power,Signal'
def unused_source_class(t,m,p):
    extra=copy.deepcopy(p['net_settings']['classes'][2]);extra['name']='Unused';p['net_settings']['classes'].append(extra)
def unused_profile(t,m,p):
    unused_source_class(t,m,p);p['net_settings']['classes'][-1]['tuning_profile']='restricted'
def profile_definition(t,m,p):
    p['tuning_profiles']={'meta':{'version':0},'tuning_profiles_impedance_geometric':[{'name':'unused'}]}

def main():
    before={path:sha(ROOT/path) for path in FILES}
    rows=[]
    cases=[
      ('positive_three_class',None,'pass'),
      ('source_class_order_independent',reorder_declared_classes,'pass'),
      ('priority_tie_separate_resolved_classes',same_priority_unambiguous,'pass'),
      ('unused_declared_class_is_not_active',unused_source_class,'pass'),
      ('zero_copper_net_still_has_class',zero_pad,'pass'),
      ('zero_copper_net_membership_lost',remove_zero_member,'reject'),
      ('zero_copper_net_class_lost',remove_zero_class,'reject'),
      ('unknown_empty_dsn_class',add_unknown_class,'reject'),
      ('duplicate_dsn_class',duplicate_class,'reject'),
      ('unknown_dsn_net',lambda t,m,p:pins(t)[0].__setitem__(1,'UNKNOWN'),'reject'),
      ('missing_dsn_net',lambda t,m,p:sx.one(t,'network').remove(pins(t)[0]),'reject'),
      ('unmapped_native_net',lambda t,m,p:m['nets'].append({**copy.deepcopy(m['nets'][2]),'name':'UNMAPPED','netcode':4}),'reject'),
      ('wrong_dsn_class_member',lambda t,m,p:classes(t)[0].insert(3,'GND'),'reject'),
      ('duplicate_native_netcode',lambda t,m,p:m['nets'][2].__setitem__('netcode',2),'reject'),
      ('duplicate_native_netname',lambda t,m,p:m['nets'][2].__setitem__('name','GND'),'reject'),
      ('wrong_parent_name',change_parent('name','Default'),'reject'),
      ('all_wrong_parents',wrong_parents_consistent_dimensions,'reject'),
      ('wrong_parent_priority',change_parent('priority',0),'reject'),
      ('wrong_parent_value',change_parent('value_nm',499999),'reject'),
      ('boolean_parent_value',change_parent('value_nm',True),'reject'),
      ('not_specified_parent',change_parent('specified',False),'reject'),
      ('int_one_not_exact_true',change_parent('specified',1),'reject'),
      ('source_parent_width_changed',source_parent_mismatch,'reject'),
      ('source_casefold_shadow',shadow_case,'reject'),
      ('multiple_nondefault_constituents',two_nondefault,'reject'),
      ('default_before_nondefault',lambda t,m,p:m['nets'][1].__setitem__('class','Default,Power'),'reject'),
      ('unknown_composite',lambda t,m,p:m['nets'][1].__setitem__('class','Implicit,Default'),'reject'),
      ('source_minimum_width_raised',lambda t,m,p:p['board']['design_settings']['rules'].__setitem__('min_track_width',.55),'reject'),
      ('unused_active_class_profile',unused_profile,'reject'),
      ('unused_global_profile_definition',profile_definition,'reject'),
      ('explicit_source_assignment',lambda t,m,p:p['net_settings'].__setitem__('netclass_assignments',{'GND':['Power']}),'reject'),
      ('default_pattern_target',lambda t,m,p:p['net_settings']['netclass_patterns'][0].__setitem__('netclass','Default'),'reject'),
    ]
    with mock.patch.object(subprocess,'run',side_effect=AssertionError('No subprocess permitted')), mock.patch.object(subprocess,'Popen',side_effect=AssertionError('No subprocess permitted')):
        for args in cases:rows.append(run_case(*args))
        # Existing flag-default behavior remains separate and unchanged.
        for default_only in (True,False):
            tree,native,project=fixtures(default_only)
            result=n.audit_mapping(tree,native,project)
            rows.append({'case':'existing_default_policy_'+str(default_only),'matched':result['passed'] and not result['routing_accepted']})
        tree,native,project=example()
        try:n.audit_mapping(tree,native,project)
        except ValueError:rows.append({'case':'new_policy_not_auto_enabled','matched':True})
        else:rows.append({'case':'new_policy_not_auto_enabled','matched':False})
        # New nested metadata is shallow-copied: record this concrete API edge.
        tree,native,project=example();original=copy.deepcopy(native)
        result=n.audit_native(native,project,parent_policy=True)
        result['nets'][0]['parameter_parents']['width_nm']['value_nm']=1
        alias={'input_changed_by_mutating_returned_parent':native!=original,
               'nested_parent_same_object':result['nets'][0]['parameter_parents'] is native['nets'][0]['parameter_parents'],
               'routing_accepted':result['routing_accepted']}
        stream=io.StringIO()
        suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(test_netclass_parent_policy),unittest.defaultTestLoader.loadTestsFromModule(test_netclass_native)])
        test_result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    after={path:sha(ROOT/path) for path in FILES}
    record={'scope':'authored pure controls only; no native, JVM, Git, network or production writes',
            'files_before':before,'files_after':after,'source_unchanged':before==after,
            'controls':rows,'nested_alias':alias,'targeted_test_count':test_result.testsRun,
            'targeted_tests_passed':test_result.wasSuccessful(),
            'all_expected_controls':all(row['matched'] for row in rows),
            'native_routing_qualification':False}
    (OWN/'controls-after-fix.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
    (OWN/'targeted-tests-after-fix.txt').write_text(stream.getvalue())
    print(json.dumps({k:record[k] for k in ['source_unchanged','all_expected_controls','nested_alias','targeted_test_count','targeted_tests_passed']}))

if __name__=='__main__':main()
