"""Finite owned export prerequisite; no routing or support admission. GPL-3.0-or-later."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,copy,importlib.util,shutil
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'.runs/runtime042 fresh install 001'
sys.path.insert(0,str(RUNTIME));sys.dont_write_bytecode=True
from autorouter import pipeline as p,config as c,sexpr as sx,floor_route as f,placement_clearance as pc,native_edge as edge,padless_alias as alias
assert c.ROOT==RUNTIME and c.NATIVE_VERSION=='10.0.7'
assert p.sha(RUNTIME/'runtime-distribution.json')=='0fa1f13c4a43385d2d0b513c7c84fb89bb6370eb9962531018f0d1ccbfd6f039'
recipe=ROOT/'experiments/native_schematic_transport_v1/fixture.py'
spec=importlib.util.spec_from_file_location('owned_fractional_base',recipe);base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
OUT=ROOT/'.runs/native7-fractional-export-controls-001';assert not OUT.exists();OUT.mkdir()
assert shutil.disk_usage(ROOT).free>4*1024**3
tools=p.tool_manifest();scriptpin=p.sha(Path(__file__));recipepin=p.sha(recipe)
CASES={'positive':(['6.00025','6.0005','32.00025','30.0005'],Decimal(0)),
 'mixed':(['-6.00025','-6.0005','32.00025','30.0005'],Decimal(0)),
 'negative':(['-33.99975','-33.9995','-7.99975','-9.9995'],Decimal(-40)),
 'nm-grid':(['6.000001','6.000499','32.000999','30.000501'],Decimal(0))}
plans={}
for case,(bounds,shift) in CASES.items():
 material=base.files();tree=sx.parse(material[base.STEM+'.kicad_pcb'].decode())
 for node in tree[1:]:
  if not isinstance(node,list):continue
  if node[0]=='footprint':
   at=sx.one(node,'at');at[1:3]=[str(Decimal(v)+shift) for v in at[1:3]]
  elif node[0]=='segment':
   for key in ('start','end'):
    xy=sx.one(node,key);xy[1:3]=[str(Decimal(v)+shift) for v in xy[1:3]]
  elif node[0]=='zone':
   pts=sx.one(sx.one(node,'polygon'),'pts')
   for xy in pts[1:]:xy[1:3]=[str(Decimal(v)+shift) for v in xy[1:3]]
  elif node[0]=='gr_rect':
   sx.one(node,'start')[1:]=bounds[:2];sx.one(node,'end')[1:]=bounds[2:]
 material[base.STEM+'.kicad_pcb']=(sx.dump(tree)+'\n').encode()
 source=OUT/case/'source';source.mkdir(parents=True)
 for name,raw in material.items():
  with (source/name).open('xb') as stream:stream.write(raw)
 board=source/(base.STEM+'.kicad_pcb');context=edge.derive_context(material[board.name],material[board.with_suffix('.kicad_pro').name])
 assert context['applicable'] and any(Decimal(v)*10!=(Decimal(v)*10).to_integral_value() for v in context['rect_um'])
 plans[case]={'source':str(board),'source_hashes':pc.inventory(source),'rect_um':context['rect_um'],'minimum_mm':context['original_min_copper_edge_clearance_mm']}
p.save_json(OUT/'protocol.json',{'schema':1,'kind':'prospective-owned-native7-fractional-export-prerequisite-v1','accepted':False,'support_admitted':False,'tools':tools,'controller_sha256':scriptpin,'fixture_sha256':recipepin,'cases':plans,'bounds_seconds':120,'scope':'Four finite owned fullSCH diagnostic source rectangles: positive/mixed/negative signs and1nm grid. Actual selected10.0.7 exporter only, original source exact. Not routing, Native DRC, general rounding law, schematic or physical qualification. Existing0.5um discrepancy/0.1um inward grid are hypotheses to verify, not increased.'})
rows=[]
for case,plan in plans.items():
 board=Path(plan['source']);job=f.FloorJob(OUT/case/'export',30,lambda:120-(time.monotonic()-START))
 dsn=job.out/'native.dsn';mapping=job.out/'netclasses.json'
 job.native('export','export',board,dsn,mapping)
 raw=pc.read_bytes(dsn);tree=sx.parse(raw.decode());parser=sx.one(tree,'parser');shape=sx.one(sx.one(tree,'structure'),'boundary')[1]
 assert sx.one(parser,'host_version')==['host_version','"10.0.7"'] and sx.one(parser,'host_cad')==['host_cad','"KiCad\'s Pcbnew"']
 assert sx.one(tree,'resolution')==['resolution','um','10']
 assert shape[:3]==['path','pcb','0'] and len(shape)==13
 coords=list(map(Decimal,shape[3:]));points=list(zip(coords[::2],coords[1::2]));assert points[0]==points[-1] and len(set(points[:-1]))==4
 bounds=[min(coords[::2]),min(coords[1::2]),max(coords[::2]),max(coords[1::2])];want=list(map(Decimal,plan['rect_um']))
 assert all(abs(got-expected)<=Decimal('.5') for got,expected in zip(bounds,want))
 observed=f.read_json(mapping);proof=f.read_json(alias.artifact_paths(dsn)['proof'])
 assert observed['native_version']=='10.0.7' and observed['board_saved'] is False
 assert observed['board_sha256']==p.sha(board) and observed['project_sha256']==p.sha(board.with_suffix('.kicad_pro'))
 assert proof['dsn_sha256']==p.sha(dsn) and proof['board_saved'] is False and proof['source_sha256']==p.sha(board)
 assert pc.inventory(board.parent)==plan['source_hashes'] and p.tool_manifest()==tools and p.sha(Path(__file__))==scriptpin and p.sha(recipe)==recipepin
 rows.append({'case':case,'source_bounds_um':plan['rect_um'],'actual_bounds_um':list(map(str,bounds)),'delta_um':[str(got-expected) for got,expected in zip(bounds,want)],'source_unchanged':True,'native_version':observed['native_version'],'dsn_sha256':p.sha(dsn),'mapping_sha256':p.sha(mapping),'alias_sha256':p.sha(alias.artifact_paths(dsn)['proof']),'process':job.steps[0]})
 print(case,rows[-1]['delta_um'],flush=True)
p.save_json(OUT/'result.json',{'schema':1,'kind':'owned-native7-fractional-export-prerequisite-v1','passed':len(rows)==4,'accepted':False,'support_admitted':False,'Native_DRC':False,'routing':False,'rows':rows,'source_unchanged':all(pc.inventory(Path(row['source']).parent)==row['source_hashes'] for row in plans.values()),'protocol_sha256':p.sha(OUT/'protocol.json'),'sampled_wall_seconds':time.monotonic()-START,'sampled_full_CPU_seconds':cpu()-CPU0,'external_exit_required':True})
