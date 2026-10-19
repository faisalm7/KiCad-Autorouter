"""Finite real selected7 floor/default API observation before installed qualification.
No routing/import/refill/acceptance; reuse existing pinned diagnostic worker/runner.
"""
from pathlib import Path
import json,sys,shutil,time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,config as c,floor_route as f,default_targets as d
from autorouter.runner import run
base=ROOT/'.runs/native-default-floor-observation-001';assert not base.exists();base.mkdir()
selection=c.native_selection(f.read_json(ROOT/'toolchain.lock.json'),'10.0.7')['tools']
record=dict(schema=1,mode='experimental-native-qualification',expected_version='10.0.7',tools={key:{'path':selection[role]['path'],'sha256':selection[role]['sha256']} for key,role in [('cli','kicad_cli'),('python','kicad_python'),('pcbnew','pcbnew')]})
toolchain=p.ExperimentalNativeToolchain.from_record(record)
construction=f.read_json(ROOT/'.runs/default-floor-owned-controls-001/construction.json')
source_rows=[('implicit',ROOT/'fixtures/smoke/smoke.kicad_pcb'),*[(case['label'],Path(case['source'])) for case in construction['cases']]]
pins={str(ROOT/name):p.sha(ROOT/name) for name in ('autorouter/native.py','autorouter/netclass_native.py','autorouter/default_targets.py','autorouter/netclass.py','autorouter/floor_context.py')}
rows=[];protocol=dict(schema=1,controller_sha256=p.sha(Path(__file__)),worker_pins=pins,toolchain=record,cases=[dict(label=label,source=str(source),source_hashes=p.tree_hash(source.parent)) for label,source in source_rows],bounds=dict(whole_seconds=30,per_case_seconds=8,RSS_bytes=1024**3),hypothesis='Real selected7 same-load getters supply effective missing Default/floors and exactly match explicit authored fields.',decision='Observe API precondition only; mismatch blocks installed qualification. No routing/production or electrical claim.')
p.save_json(base/'protocol.json',protocol)
for label,source in source_rows:
 folder=base/label;folder.mkdir();before=p.tree_hash(source.parent);shutil.copytree(source.parent,folder/'source');board=folder/'source'/source.name;mapping=folder/'native-map.json';dsn=folder/'native.dsn'
 process=run([*f.SANDBOX,*p.native_prefix(toolchain),'export',str(board),str(dsn),str(mapping)],cwd=folder,log=folder/'native.log',timeout=min(8,30-(time.monotonic()-START)),max_log_bytes=65536,max_workdir_bytes=16*1024**2,max_group_rss_bytes=1024**3);p.save_json(folder/'process.json',process)
 assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True
 observed=f.read_json(mapping);dimensions=d.source_dimensions(board.with_suffix('.kicad_pro').read_bytes(),observed)
 assert p.tree_hash(board.parent)==before==p.tree_hash(source.parent)
 rows.append(dict(label=label,process=process,map_sha256=p.sha(mapping),dsn_sha256=p.sha(dsn),dimensions=dimensions,dimension_resolution=d.resolution_fields(board.with_suffix('.kicad_pro').read_bytes()),native_nets=len(observed['nets']),source_unchanged=True))
assert all(p.sha(Path(name))==pin for name,pin in pins.items())
p.save_json(base/'result.json',dict(schema=1,observation_passed=True,installed_qualified=False,routing_accepted=False,actual_GUI=False,project_complete=False,cases=rows,protocol_sha256=p.sha(base/'protocol.json'),sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0,scope='Actual pinned7 loaded-board export/map and pure scalar/source matching only; no solver/import/refill/DRC or installed qualification. Complete external exit authoritative.'))
print(json.dumps({'observation_passed':True,'cases':[dict(label=x['label'],dimensions=x['dimensions'],nets=x['native_nets']) for x in rows]}))
