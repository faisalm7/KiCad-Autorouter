"""Correct only the demonstrated order comparator using completed native evidence."""
from pathlib import Path
import json,sys,time
from unittest.mock import patch
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));sys.dont_write_bytecode=True
from experiments.kicad8_native_compat_continuation_v1 import driver as d
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,sexpr as sx
out=root/'.runs/kicad8-route-order-readback-002';out.mkdir();start=time.monotonic();cpu=time.process_time()
run=root/'.runs/kicad8-native-compat-continuation-001/run';folder=run/'ideal_diode'
before=pc.inventory(run,max_bytes=20*1024**2,max_files=2000,max_entries=4000)
s=f.read_json(run/'summary.json');case=f.read_json(folder/'case.json');source=d.prior.SOURCE
original_before=pc.inventory(source.parent);assert original_before==case['source_hashes']
proof=f.read_json(root/'.runs/review-kicad8-native-continuation-001/audit-003.json')
assert proof['status']=='audit_passed_original_controller_failed' and proof['summary_sha256']==p.sha(run/'summary.json')
assert s['status']=='failed' and case['error']=='Rejected: native saved/reloaded non-fill geometry or routes differ'
with patch.object(p.subprocess,'run',side_effect=AssertionError('no subprocesses allowed')):
 prefix=d.prefix_readback(d.f.read_json(d.HERE/'PROTOCOL.json'))
 hashes=case['source_hashes'];candidate=folder/'candidate'/source.name;saved=folder/'refill'/source.name
 observed=f.check_drc_stage(folder,case,'refill-drc',saved,saved,True,hashes)
 expected=dict(hashes);expected[source.name]=case['candidate_sha256']
 final=f.check_drc_stage(folder,case,'final-drc',candidate,folder/'final-drc-input'/source.name,False,expected)
 assert final==observed==case['final_drc']['native']==case['saved_drc']['native']
 assert (sx.dump(d.prior.old_shell(sx.read(source),sx.read(saved)))+'\n').encode()==pc.read_bytes(candidate)
 original=sx.read(folder/'original-native.kicad_pcb')
 witnesses={name:d.emission_equal_by_uuid(original,sx.read(folder/(name+'-native.kicad_pcb'))) for name in ('saved','shell')}
 assert all(x['route_count']==113 and x['native_routes_equal_by_uuid'] for x in witnesses.values())
 assert witnesses['saved']['route_list_order_equal'] is False and witnesses['shell']['route_list_order_equal'] is True
assert before==pc.inventory(run,max_bytes=20*1024**2,max_files=2000,max_entries=4000) and original_before==pc.inventory(source.parent)
record={'schema':1,'status':'diagnostic_readback_passed','controller_status':'failed','controller_rewritten':False,
 'native_reexecuted':False,'subprocess_executed':False,'source_and_raw_evidence_unchanged':True,'scope':'Exact native geometry/route identity readback after demonstrated list-order comparator defect; no rule/geometry field discarded.',
 'raw_summary_sha256':p.sha(run/'summary.json'),'raw_case_sha256':p.sha(folder/'case.json'),'independent_audit_sha256':p.sha(root/'.runs/review-kicad8-native-continuation-001/audit-003.json'),
 'checker_sha256':p.sha(d.HERE/'driver.py'),'wrapper_sha256':p.sha(Path(__file__)),'route_witnesses':witnesses,
 'native_counts':{k:final[k] for k in ('opens','blocking','warnings','exclusions')},'ignored_check_keys':[x['key'] for x in final['ignored_checks']],
 'actual_native_processes_with_prefix':21,'all_admission_flags':{k:False for k in d.FALSE_FLAGS},
 'new_wall_seconds':time.monotonic()-start,'new_parent_cpu_seconds':time.process_time()-cpu,'prior_full_outer_wall_seconds':25.137507459003245,'prior_full_outer_cpu_seconds':16.52282}
p.save_json(out/'readback.json',record);print(json.dumps(record,indent=2))
