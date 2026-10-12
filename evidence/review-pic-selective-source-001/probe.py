"""Finite comparator falsifiers using the existing synthetic harness; no JVM/native."""
from pathlib import Path
import copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.pic_mixed_transport_probe_v1 import test_selective as tests
T=tests.Controls;T.setUpClass();t=T();c=tests.c
baseline=copy.deepcopy(t.baseline);before=c.canonical(baseline);cases=[]

def run(name,change=None):
 o=t.observation()
 if change:change(o)
 try:result=c.compare(o,t.expected,baseline)
 except (ValueError,KeyError,TypeError) as exc:accepted=False;error=str(exc)
 else:accepted=True;error=None
 expected=change is None
 assert accepted==expected,(name,accepted)
 cases.append({'case':name,'accepted':accepted,'expected':expected,'error':error})
run('unchanged_synthetic_positive')
run('later_router_enable',lambda o:o['case']['settings_after_selective'].update(router_enabled=True))
run('missing_complete_tree_entry',lambda o:o['case']['predicates_after']['tree_entries'].pop())
run('extra_unrecorded_area',lambda o:o['case']['state_after_selective']['areas'].append(copy.deepcopy(o['case']['state_after_selective']['areas'][0])))
run('same_net_blocking',lambda o:next(r for a in o['case']['predicates_after']['areas'] for r in a['routes'] if r['same_net']).update(item_obstacle=True,trace_obstacle=True,drillable=False))
run('foreign_custom_body_drillable',lambda o:next(r for a in o['case']['predicates_after']['areas'] if a['id'] in o['case']['selective_override']['changed_area_ids'] for r in a['routes'] if not r['same_net']).update(drillable=True))
run('unchanged_gnd_starts_blocking',lambda o:next(a for a in o['case']['state_after_selective']['areas'] if a['nets']==['GND']).update(obstacle=True))
run('non_target_filter_changed',lambda o:o['case']['predicates_after']['trace_queries'][0]['flag_filtered_overlap_ids'].append(next(i['id'] for i in o['case']['state']['items'] if i['id'] not in o['case']['predicates_after']['trace_queries'][0]['raw_overlap_ids'])))
run('query_total_nan',lambda o:o['case']['predicates_after'].update(trace_shape_count=float('nan')))
run('query_boolean_integer',lambda o:o['case']['predicates_after']['trace_queries'][0].update(tree_trace_check_clear=1))
run('old_false_query_becomes_clear',lambda o:(o['case']['predicates_before']['trace_queries'][0].update(tree_trace_check_clear=False),o['case']['predicates_after']['trace_queries'][0].update(tree_trace_check_clear=True)))
assert c.canonical(baseline)==before
pins=json.loads((OUT/'source-before.json').read_text())
for path,pin in pins.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==pin['sha256']
report={'passed':True,'scope':'Existing synthetic selective fixture and real retained local basis; no native/JVM execution or validity claim','source_files_unchanged':True,'retained_input_in_memory_unchanged':True,'cases':cases}
(OUT/'probe-results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
