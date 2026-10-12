"""Bounded retained-byte audit; no native/JVM execution."""
from pathlib import Path
import collections,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));from autorouter import placement_clearance as io
sha=lambda p:hashlib.sha256(io.read_bytes(p,4*1024**2)).hexdigest()
load=lambda p:json.loads(io.read_bytes(p,4*1024**2))
run=ROOT/'.runs/pic-mixed-transport-probe-004';source=ROOT/'.data/boards/kicad-pic-programmer'
before=io.inventory(run,max_bytes=16*1024**2,max_files=250,max_entries=500)
s=load(run/'summary.json');state=load(run/'clearance-initialization.json');proc=load(run/'native-observe-process.json')
assert all(before.get(k)==v for k,v in s['frozen_evidence'].items())
original=io.inventory(source,max_bytes=4*1024**2,max_files=30,max_entries=70)
assert len(original)==15 and original==s['runtime']['original']==io.inventory(run/'observe-input',max_bytes=4*1024**2,max_files=30,max_entries=70)
assert len(s['steps'])==1 and s['steps'][0]['exit_code']==proc['exit_code']==-11 and proc['cleanup_complete'] is True
assert s['native_process_executed'] is True and s['import_process_executed'] is False and s['observations_complete'] is False
assert set(state)=={'pre_initialization','pre_initialization_api_types'}
rows=state['pre_initialization'];types=state['pre_initialization_api_types']
assert len(rows)==len({r['uuid'] for r in rows})==247
assert len(types)==112 and sum(t['status']=='observed' for t in types)==111
assert all(t['raw_return_types']['key']=='wxString' and t['raw_return_types']['netcode']=='int' for t in types)
assert sum(r['class_metadata']['status']=='observed' for r in rows)==236
assert sum(r['class_metadata']['status']=='unavailable_netless' for r in rows)==11
absent=['initialization-drc.txt','context.json','custom.json','native.dsn','mixed.dsn','compile-process.json','import-process.json','observations.json']
assert all(not (run/n).exists() for n in absent)
helpers=ROOT/'.runs/lipo-export-failure-research-001/source/pcbnew/python/scripting/pcbnew_scripting_helpers.cpp'
network=load(ROOT/'.runs/lipo-export-failure-research-001/network.json')
receipt=next(x for x in network['requests'] if x.get('path','').endswith('pcbnew_scripting_helpers.cpp'))
assert sha(helpers)==receipt['sha256']=='42a827912a06c0d7c96f2cd790f87b2f01549ed04a58f728366d899b8dca90dd'
assert before==io.inventory(run,max_bytes=16*1024**2,max_files=250,max_entries=500)
assert original==io.inventory(source,max_bytes=4*1024**2,max_files=30,max_entries=70)
result={'schema':1,'passed':True,'run':str(run.relative_to(ROOT)),'head':s['runtime']['git']['head'],
 'bound_artifacts':{n:sha(run/n) for n in ['summary.json','native-observe-process.json','native-observe.log','clearance-initialization.json']},
 'original_files':15,'pre_rows':247,'assigned_rows':236,'netless_rows':11,'observed_net_metadata':111,'nonpositive_placeholder_entries':1,
 'observed_key_type':'wxString','observed_netcode_type':'int','process_exit_code':-11,'cleanup_complete':True,
 'absent_artifacts':absent,'initialization_return_unobserved':True,
 'crash_scope':'After complete pre-call observation was saved, while WriteDRCReport had not returned. Pgm assertion present; exact internal crash stack unobserved.',
 'wall_seconds':s['wall_seconds'],'total_cpu_seconds':s['total_cpu_seconds'],
 'outer':load(ROOT/'.runs/pic-mixed-transport-probe-004-execution.json'),
 'cached_primary_source':receipt,'source_lines':{'LoadBoard_project_load':'150-185','LoadBoard_InitEngine_catch_all':'244-256','LoadBoard_connectivity_sync':'258-264','WriteDRCReport_InitEngine':'579-587','WriteDRCReport_RunTests':'619-625'},
 'original_and_failed_run_unchanged':True,'native_jobs':0,'jvm_jobs':0}
(HERE/'input-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'rows':len(rows),'net_metadata':111,'native_exit':-11}))
