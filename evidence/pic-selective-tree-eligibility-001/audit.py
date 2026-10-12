"""Read actual failed observer and cached source/API evidence; no worker execution."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.pic_mixed_transport_probe_v1 import driver as d,transport,ses_checks
run=ROOT/'.runs/pic-selective-area-observation-001';before=d.inventory(run);s=d.base.decode(d.base.content(run/'summary.json'));o=d.base.decode(d.base.content(run/'observations.json',16*1024**2));row=o['case']
original=d.inventory(d.original.SOURCE.parent)
assert original==s['runtime']['original']==d.inventory(run/'observe-input')
assert all(before[k]==v for k,v in s['frozen_evidence'].items())
for rel,pin in s['runtime']['sources'].items():assert d.base.content(run/'code'/rel,2*1024**2,digest=True)==pin
assert s['status']=='failed' and s['observations_complete'] is False and s['routing_accepted'] is False
assert row['status']=='failed' and row['error']=='java.lang.IllegalArgumentException: complete search-tree entry validation failed'
assert 'selective_override' not in row and 'state_after_selective' not in row and 'predicates_after' not in row
items={x['id']:x for x in row['state']['items']};entries={x['id']:x for x in row['predicates_before']['tree_entries']}
assert len(items)==len(entries)==1222 and set(items)==set(entries)
assert all(type(x['valid']) is bool and set(x)=={'id','valid'} for x in entries.values())
counts=Counter(x['kind'] for x in items.values());invalid=Counter(items[i]['kind'] for i,x in entries.items() if not x['valid']);valid=Counter(items[i]['kind'] for i,x in entries.items() if x['valid'])
assert invalid=={'app.freerouting.board.model.items.ComponentOutline':619} and sum(valid.values())==603
assert row['predicates_before']['all_tree_entries_valid'] is False
assert row['state']['ignore_conduction'] is True and all(x['obstacle'] is False for x in row['state']['areas'])
local=d.base.decode(d.base.content(run/'local-basis-observations.json',16*1024**2));expected=d.base.decode(d.base.content(run/'expectations.json'))
transport.validate_local(local,expected)
for field in ('input_sha256','argv','settings_before','settings_after','parser_result_class','state_before_local','local_override','state'):assert row[field]==local['cases'][0][field]
assert row['route_geometry_before_local']==row['route_geometry'];ses_checks.geometry_check(row['route_geometry'],row['state'])
assert [(x['name'],x['status'],x['exit_code']) for x in s['steps']]==[('compile','success',0),('import','nonzero_exit',2)]
for step in s['steps']:
 process=d.base.decode(d.base.content(run/(step['name']+'-process.json')))
 assert step==dict(process,name=step['name']) and process['cleanup_complete'] is True and process['log_truncated'] is False
source_paths=['.runs/pic-local-clearance-transport-design-001/source/SearchTreeManager.java','.runs/pic-local-clearance-transport-design-001/source/Item.java','.runs/pic-selective-area-plan-001/source/ShapeSearchTree.java','.runs/custom-pad-area-api-inspection-002/app.freerouting.board.model.items.Item.txt']
source_pins={p:{'bytes':(ROOT/p).stat().st_size,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in source_paths}
net=json.loads((OUT/'network-receipt.json').read_text())
for x in net['files']:assert hashlib.sha256((ROOT/x['path']).read_bytes()).hexdigest()==x['sha256']
assert d.inventory(run)==before and d.inventory(d.original.SOURCE.parent)==original
result={'passed':True,'scope':'Failed actual observation diagnosis, no reclassification or new worker','head':s['runtime']['git']['head'],'summary_sha256':before['summary.json'],'observations_sha256':before['observations.json'],'frozen_files':len(s['frozen_evidence']),'run_files':len(before),'original_files':len(original),'original_and_run_unchanged':True,'item_kinds':dict(counts),'raw_invalid_kinds':dict(invalid),'raw_valid_kinds':dict(valid),'zero_shape_and_null_entries_observed':False,'selective_mutation_reached':False,'pre_selective_state_matches_actual_false_baseline':True,'stored_wall_seconds':s['wall_seconds'],'stored_full_cpu_seconds':s['total_cpu_seconds'],'cached_source_api_pins':source_pins,'new_source_bytes':net['total_bytes']}
(OUT/'actual-diagnosis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
