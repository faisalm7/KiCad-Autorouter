"""Static real-byte development control with explicitly SYNTHETIC area observations.

No native/engine work. Does not claim a fresh same-load native area census.
"""
from pathlib import Path
import importlib.util,json,sys,time
from decimal import Decimal
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx
spec=importlib.util.spec_from_file_location('placement_transform',HERE/'placement_transform.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def run():
 start=time.monotonic();source=ROOT/'.data/boards/kicad-multichannel';run=ROOT/'.runs/board-floor-multichannel-001';native=run/'floor-export-input';board='multichannel_mixer.kicad_pcb'
 before={str(d):p.tree_hash(d) for d in (source,native)};pins={str(run/n):p.sha(run/n) for n in ('native.dsn','floor-guided.dsn','floor-export-context.json')}
 original={str(f.relative_to(source)):f.read_bytes() for f in source.rglob('*') if f.is_file()};inputs={str(f.relative_to(native)):f.read_bytes() for f in native.rglob('*') if f.is_file()}
 raw=(run/'native.dsn').read_bytes();guided=(run/'floor-guided.dsn').read_bytes();tree=sx.parse(inputs[board].decode());rows=[]
 # This intentionally independent source parser constructs mock-native rows;
 # only the original byte/AST and retained DSN matching is actual evidence.
 for z in sx.children(tree,'zone'):
  ko=sx.one(z,'keepout');place=sx.one(z,'placement');selector=sx.one(z,'layer') or sx.one(z,'layers')
  points=[[int(Decimal(q[1])*1000000),int(Decimal(q[2])*1000000)] for q in sx.one(sx.one(z,'polygon'),'pts')[1:]]
  rows.append({'uuid':sx.unquote(sx.one(z,'uuid')[1]),'name':sx.unquote((sx.one(z,'name') or ['name','""'])[1]),'parent':'board','is_rule_area':ko is not None or place is not None,
   'placement_enabled':bool(place and sx.one(place,'enabled')[1]=='yes'),'placement_source_type':'SHEETNAME','placement_source':sx.unquote(sx.one(place,'sheetname')[1]) if place else '',
   'disallow':{key:(sx.one(ko,key)[1]=='not_allowed' if ko else False) for key in ('tracks','vias','pads','copperpour','footprints')},'layers':[sx.unquote(x) for x in selector[1:]],'outlines_nm':[points],'holes':[0],'arc_count':0,'outline_closed':[True]})
 obs={'context_schema':1,'native_version':'10.0.0','units':'integer nanometres','source':str(native/board),'board_sha256':p.sha(native/board),'project_sha256':p.sha(native/'multichannel_mixer.kicad_pro'),'dsn_sha256':m.sha(raw),'input_hashes_before':p.tree_hash(native),'input_hashes_after':p.tree_hash(native),'board_saved':False,'footprint_zone_count':0,'footprint_rulearea_count':0,'zones':rows,'observation_origin':'SYNTHETIC derived from source parser, not native API'}
 output,receipt=m.transform(original,inputs,board,obs,raw,guided)
 # Every other entire DSN subtree, including network, remains exactly equal.
 pre=m._parse_dsn(guided.decode());post=m._parse_dsn(output.decode());expected=__import__('copy').deepcopy(pre);st=sx.one(expected,'structure');st[:]=[n for n in st if not isinstance(n,list) or not n or n[0]!='keepout']
 assert post==expected and receipt['removed_count']==8 and receipt['kept_keepout_count']==0
 assert {str(d):p.tree_hash(d) for d in (source,native)}==before
 assert {name:p.sha(Path(name)) for name in pins}==pins
 record={'scope':'Static development-byte attribution only; mock native area rows, NO native qualification','passed':True,'routing_accepted':False,'native_executed':False,'native_qualification':False,'source_and_retained_inputs_unchanged':True,'input_trees':before,'retained_pins':pins,'module_sha256':p.sha(HERE/'placement_transform.py'),'script_sha256':p.sha(Path(__file__)),'removed_entries':8,'native_source_census_pending':True,'whole_non_target_AST_preserved':True,'wall_seconds':time.monotonic()-start,'transform_receipt':receipt}
 for name,data in [('static-multichannel-002.json',json.dumps(record,indent=2)+'\n')]:
  with (HERE/name).open('x') as f:f.write(data)
 with (HERE/'static-transformed-002.dsn').open('xb') as f:f.write(output)
 print(json.dumps({k:v for k,v in record.items() if k not in {'input_trees','retained_pins','transform_receipt'}}))
if __name__=='__main__':run()
