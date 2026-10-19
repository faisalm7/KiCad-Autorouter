"""Resume frozen Native observations; reuse completed001 exports unchanged."""
from pathlib import Path
import sys,json,shutil,time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,default_targets as d
from autorouter.runner import run
prior=ROOT/'.runs/native-default-floor-observation-001';plan=f.read_json(prior/'protocol.json');base=ROOT/'.runs/native-default-floor-observation-002';assert not base.exists();base.mkdir()
for name,pin in plan['worker_pins'].items():
 if name!=str(ROOT/'autorouter/default_targets.py'):assert p.sha(Path(name))==pin
helper=p.sha(ROOT/'autorouter/default_targets.py');toolchain=p.ExperimentalNativeToolchain.from_record(plan['toolchain'])
p.save_json(base/'protocol.json',dict(schema=1,prior_protocol_sha256=p.sha(prior/'protocol.json'),prior_controller_sha256=plan['controller_sha256'],current_helper_sha256=helper,controller_sha256=p.sha(Path(__file__)),reuse=['implicit','2Cu'],only_new_Native_case='4Cu',bounds=plan['bounds'],decision='Accept getter/parent/source-resolution precondition only; no routing/refill/DRC/install qualification.'))
rows=[]
for case in plan['cases']:
 label=case['label'];source=Path(case['source']);assert p.tree_hash(source.parent)==case['source_hashes']
 if label in ('implicit','2Cu'):
  folder=prior/label;process=f.read_json(folder/'process.json');assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True
 else:
  assert label=='4Cu' and not (prior/label).exists()
  folder=base/label;folder.mkdir();shutil.copytree(source.parent,folder/'source');board=folder/'source'/source.name
  process=run([*f.SANDBOX,*p.native_prefix(toolchain),'export',str(board),str(folder/'native.dsn'),str(folder/'native-map.json')],cwd=folder,log=folder/'native.log',timeout=8,max_log_bytes=65536,max_workdir_bytes=16*1024**2,max_group_rss_bytes=1024**3);p.save_json(folder/'process.json',process)
 assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True
 board=folder/'source'/source.name;mapping=f.read_json(folder/'native-map.json')
 assert mapping['source']==str(board) and mapping['board_sha256']==p.sha(board) and mapping['project_sha256']==p.sha(board.with_suffix('.kicad_pro')) and mapping['board_saved'] is False
 dimensions=d.source_dimensions(board.with_suffix('.kicad_pro').read_bytes(),mapping)
 assert p.tree_hash(board.parent)==case['source_hashes']==p.tree_hash(source.parent)
 rows.append(dict(label=label,reused_prior_export=label!='4Cu',directory=str(folder),process_sha256=p.sha(folder/'process.json'),map_sha256=p.sha(folder/'native-map.json'),dsn_sha256=p.sha(folder/'native.dsn'),dimensions=dimensions,dimension_resolution=d.resolution_fields(board.with_suffix('.kicad_pro').read_bytes()),priorities=sorted({parent['priority'] for row in mapping['nets'] for parent in row['parameter_parents'].values()}),source_unchanged=True))
assert helper==p.sha(ROOT/'autorouter/default_targets.py')
p.save_json(base/'result.json',dict(schema=1,observation_passed=True,routing_accepted=False,installed_qualified=False,actual_GUI=False,project_complete=False,cases=rows,protocol_sha256=p.sha(base/'protocol.json'),sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0,scope='Three real Native maps/scalar resolutions; firsttwo reused without Native repetition, only4Cu newly exported. No solver/import/refill/DRC or installed qualification. Complete external exit authoritative.'))
print(json.dumps({'observation_passed':True,'cases':rows}))
