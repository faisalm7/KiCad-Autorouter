import time
START=time.monotonic()
import ast,hashlib,json,resource,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from scripts import fetch_led_demo as demo
from autorouter import placement_clearance as io,sexpr as sx
OUT=Path(__file__).parent
path=ROOT/'scripts/fetch_led_demo.py';source=path.read_text();tree=ast.parse(source)
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fetch_demo')
stmt=next(n for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='record' for t in n.targets))
identity=[]
for profile in ('led','arcdice','analog-filter'):
 cfg=demo.fixed_profile(profile)
 namespace={'profile_id':profile,'nested':bool(cfg['native_packet_notice_copies']),'out':Path('/authored/no-write'),'project':Path('/authored/no-write/project'),'rows':cfg['rows'],'witness':{},'network_cap':cfg['network_byte_cap'],'planned':cfg['bytes'],'requests':[],'SECONDS':demo.SECONDS,'OUTPUT_BYTES':demo.OUTPUT_BYTES}
 record=eval(compile(ast.Expression(stmt.value),str(path),'eval'),namespace)
 assert record['kind']=='fixed_public_'+profile.replace('-','_')+'_source_acquisition'
 assert record['source_profile']=={'led':'licensed_acquisition_v7 fixed five-file public LED selection','arcdice':'fixed five-file public ArcDice selection','analog-filter':'fixed five-file public analog-filter selection'}[profile]
 identity.append({'profile':profile,'kind':record['kind'],'source_profile':record['source_profile']})
cfg=demo.fixed_profile('analog-filter');ready=json.loads((ROOT/'.runs/licensed-cohort-leads-001/READY-analog-filter.json').read_text())
assert cfg['commit']==ready['commit']=='6a34b221758fe32f33eca20d735e88028346753a'
assert [{k:v for k,v in row.items() if k!='destination'} for row in cfg['rows']]==ready['files']
assert len(cfg['rows'])==5 and sum(r['bytes'] for r in cfg['rows'])==cfg['bytes']==189336
assert cfg['native_packet_notice_copies']==ready['native_packet_notice_copies']
assert cfg['native_packet_files']==ready['native_packet_file_count']==7 and cfg['native_packet_bytes']==ready['native_packet_bytes']==198305
for row in cfg['rows']:
 assert row['repository']=='Myrto-Angeliki/analog-filter' and row['commit']==cfg['commit'] and row['mode']=='100644'
 assert row['raw_url']=='https://raw.githubusercontent.com/'+row['repository']+'/'+row['commit']+'/'+row['source_path']
cached=ROOT/'.runs/new-family-source-leads-001/source/Myrto-Angeliki/analog-filter'
for row in cfg['rows']:
 if row['source_path'].startswith('kicad/'):demo.shared.payload(row,io.read_bytes(cached/row['source_path']))
board=sx.read(cached/ready['board_path'])
layers=sx.one(board,'layers');copper=[x for x in layers[1:] if isinstance(x,list) and len(x)>1 and sx.unquote(x[1]).endswith('.Cu')]
assert len(copper)==4
empty=OUT/'authored-empty-root';empty.mkdir();before=io.inventory(empty,with_directories=True)
try:demo.capture_native_source('analog-filter',root=empty)
except (ValueError,OSError):pass
else:raise AssertionError('Missing fixed source must reject')
assert io.inventory(empty,with_directories=True)==before
arcpath,arcfiles=demo.capture_native_source('arcdice',root=ROOT)
assert len(arcfiles)==7 and sum(map(len,arcfiles.values()))==599338
assert demo.capture_native_source('arcdice',root=ROOT)==(arcpath,arcfiles)
ru=resource.getrusage(resource.RUSAGE_SELF);ch=resource.getrusage(resource.RUSAGE_CHILDREN)
sources=['scripts/fetch_led_demo.py','scripts/experiment_quality.py','experiments/original_project_native_v1/driver.py','experiments/placement_handoff_native_v1/driver.py','experiments/licensed_acquisition_v1/fetch.py']
result={'kind':'pure source/profile review controls','identity_labels':identity,'READY_rows_equal':True,'raw5_bytes':189336,'native7_bytes':198305,'cached_three_native_original_pins_verified':True,'cached_source_copper_layers':4,'absent_source_rejects_without_staging':True,'existing_ArcDice_capture_readonly_byte_equal':True,'native_executed':False,'GET_executed':False,'fetch_execution':False,'Git_executed':False,'original_source_mutated':False,'code_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sources},'READY_sha256':hashlib.sha256((ROOT/'.runs/licensed-cohort-leads-001/READY-analog-filter.json').read_bytes()).hexdigest(),'wall_seconds_after_script_entry':time.monotonic()-START,'lifetime_self_cpu_seconds':ru.ru_utime+ru.ru_stime,'waited_children_cpu_seconds':ch.ru_utime+ch.ru_stime,'cost_scope':'Pure controls only. Earlier source reads, interpreter bootstrap and final packet emission unsampled; not an algorithm/runtime comparison.'}
(OUT/'controls-final.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
