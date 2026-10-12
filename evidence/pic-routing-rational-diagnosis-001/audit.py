"""Read retained actual artifacts only; no point reconstruction or native execution."""
from pathlib import Path
import hashlib,json,sys
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
RUN=ROOT/'.runs/pic-selective-routing-001'
sys.dont_write_bytecode=True;sys.path.insert(0,str(RUN/'code'));sys.path.insert(1,str(ROOT))
from autorouter import sexpr as sx
from experiments.pic_mixed_transport_probe_v1 import ses_checks
assert str(ses_checks.__file__).startswith(str(RUN/'code'))
def digest(p):
 assert not p.is_symlink() and p.is_file() and p.stat().st_size<=16*1024*1024
 return hashlib.sha256(p.read_bytes()).hexdigest()
summary=json.loads((RUN/'summary.json').read_bytes());observed=json.loads((RUN/'observations.json').read_bytes())
frozen=summary['frozen_evidence'];assert all(digest(RUN/k)==v for k,v in frozen.items())
original=summary['runtime']['original'];assert all(digest(ROOT/'.data/boards/kicad-pic-programmer'/k)==v for k,v in original.items())
try:ses_checks.geometry_check(observed['final_geometry'],observed['final_state'])
except ValueError as exc:assert str(exc)=='exact integer engine point required';failure=str(exc)
else:raise AssertionError('saved unsupported point unexpectedly passes')
assert observed['writer']['state_after_ses']==observed['final_state']
assert observed['writer']['route_geometry_after_ses']==observed['final_geometry']
raw=(RUN/'raw.ses').read_bytes();assert digest(RUN/'raw.ses')==observed['writer']['ses']['sha256'] and len(raw)==observed['writer']['ses']['bytes']
tree=sx.parse(raw.decode());routes=sx.one(tree,'routes');resolution=sx.one(routes,'resolution');assert resolution==['resolution','um','10'];scale=Decimal(resolution[2])
paths=[]
for net in sx.children(sx.one(routes,'network_out'),'net'):
 for wire in sx.children(net,'wire'):
  path=sx.one(wire,'path')
  if not path:continue
  values=[Decimal(x)/scale for x in path[3:]]
  paths.append({'net':sx.unquote(net[1]),'layer':sx.unquote(path[1]),'width':Decimal(path[2])/scale,'points':list(zip(values[::2],values[1::2]))})
findings=[]
for trace in observed['final_geometry']['traces']:
 bad=[i for i,k in enumerate(trace['corner_classes']) if k!='app.freerouting.geometry.planar.IntPoint']
 if not bad:continue
 assert len(bad)==1;i=bad[0];assert trace['corner_classes'][i]=='app.freerouting.geometry.planar.RationalPoint' and trace['corners_board_integer'][i] is None
 displayed=[tuple(Decimal(str(x)) for x in p) for p in trace['corners_um']]
 choices=[p for p in paths if p['net']==trace['nets'][0] and p['layer']==trace['layer'] and p['width']==Decimal(str(trace['width_um'])) and len(p['points'])==len(displayed) and all(p['points'][k]==displayed[k] for k in range(len(displayed)) if k!=i)]
 assert len(choices)==1;p=choices[0];actual=p['points'][i]
 findings.append({'trace_id':trace['id'],'corner_index':i,'net':p['net'],'layer':p['layer'],'width_um':str(p['width']),'engine_class':trace['corner_classes'][i],'exact_engine_integer':None,'engine_displayed_um':[str(x) for x in displayed[i]],'ses_um':[str(x) for x in actual],'ses_minus_displayed_engine_um':[str(a-b) for a,b in zip(actual,displayed[i])],'matching_nonrational_corners':len(displayed)-1})
assert len(findings)==3 and {f['trace_id'] for f in findings}=={1177,1178,1179}
assert len({tuple(f['ses_um']) for f in findings})==1
assert all(digest(RUN/k)==v for k,v in frozen.items())
assert all(digest(ROOT/'.data/boards/kicad-pic-programmer'/k)==v for k,v in original.items())
record={'scope':'Read-only actual001 failed-geometry diagnosis, not rational reconstruction or transport qualification','head':summary['runtime']['git']['head'],'status':summary['status'],'error_reproduced':failure,'artifact_hashes':{k:digest(RUN/k) for k in ['summary.json','observations.json','raw.ses','import-process.json','compile-process.json']},'source_original_files_verified_unchanged':len(original),'frozen_artifacts_verified_unchanged':len(frozen),'engine_census':observed['final_state']['census'],'coordinate_scale_board_units_per_um':observed['final_state']['board_units_per_um'],'coordinate_origin_dsn_um':observed['final_state']['board_origin_dsn_um'],'routing':observed['routing'],'routing_executed':observed['routing_executed'],'ses_executed':observed['ses_executed'],'native_process_executed':summary['native_process_executed'],'writer_state_and_geometry_unchanged':True,'junctions':findings,'exact_rational_triplets_available':False,'routing_accepted':False,'stored_wall_seconds':summary['wall_seconds'],'stored_full_cpu_seconds':summary['total_cpu_seconds'],'processes':[{k:p.get(k) for k in ['name','exit_code','wall_seconds','cpu_seconds','cleanup_complete']} for p in summary['steps']]}
(OUT/'diagnosis.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
