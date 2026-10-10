"""Read-only static LiPo compatibility audit; never invokes native tools."""
from pathlib import Path
import collections,copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,sexpr as sx,board_floor as g,netclass
SOURCE=ROOT/'.data/expansion003/lipo-disconnector';BOARD=SOURCE/'lipo_disconnector.kicad_pcb'
RECEIPT=ROOT/'.runs/licensed-acquisition-003/lipo-disconnector-001/receipt.json'
PARSER=ROOT/'.runs/placement-area-export-review-001/source/pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr_parser.cpp'
def digest(data):return hashlib.sha256(data).hexdigest()
def count(tree,key):
 return sum(1 for n in walk(tree) if n[0]==key)
def walk(tree):
 yield tree
 for n in tree[1:]:
  if isinstance(n,list) and n:yield from walk(n)
def value(tree,key,default=None):
 n=sx.one(tree,key)
 return n[1:] if n is not None else default
def attempt(name,fn):
 try:return {'name':name,'outcome':'returned','value':fn()}
 except Exception as e:return {'name':name,'outcome':'rejected','exception':type(e).__name__,'reason':str(e)}
def main():
 if (HERE/'audit.json').exists():raise ValueError('refuse collision')
 before=p.tree_hash(SOURCE);receipt=json.loads(RECEIPT.read_text());checks=[]
 assert receipt['status']=='acquired_unqualified'
 expected={}
 for row in receipt['files']:
  path=Path(row['destination']);assert path.parts[0]=='lipo-disconnector'
  rel=str(Path(*path.parts[1:]));raw=(SOURCE/rel).read_bytes()
  assert len(raw)==row['bytes'] and digest(raw)==row['sha256']
  assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob_sha1']
  expected[rel]=row['sha256']
 assert before==expected
 assert p.sha(PARSER)=='78f6380806e15b2a25300f8134c6492cd343d6dfb538546e299d60d26a62ec27'
 tree=sx.read(BOARD);project=json.loads(BOARD.with_suffix('.kicad_pro').read_text());sch=sx.read(BOARD.with_suffix('.kicad_sch'))
 fps=sx.children(tree,'footprint');pads=[pad for fp in fps for pad in sx.children(fp,'pad')];zones=sx.children(tree,'zone')
 edge=[n for n in tree if isinstance(n,list) and n and sx.one(n,'layer')==['layer','"Edge.Cuts"']]
 task=p.immutable(tree)
 checks.append(attempt('current original preflight',lambda:p.preflight(BOARD)))
 checks.append(attempt('current fill transplant original into same original; pure API precondition probe, NOT native',lambda:p.transplant_fill(tree,tree)))
 checks.append(attempt('current floor task pad identity on original; pure parser probe',lambda:g.task_pads(tree)))
 checks.append(attempt('current floor scope stripped task; pure structural subset only',lambda:g.qualify_scope(project,task)))
 names,_=g.source_net_identity(tree)
 # A transformed in-memory syntax surrogate is NOT loaded/saved native evidence.
 modern=copy.deepcopy(tree)
 for z in sx.children(modern,'zone'):sx.one(z,'tstamp')[0]='uuid'
 checks.append(attempt('current fill transplant old base + uuid-zone surrogate; NOT native migration',lambda:p.transplant_fill(tree,modern)))
 observations={'schema':1,'kind':'static compatibility plan evidence; no native qualification','source':str(BOARD),'source_repository':'solderparty/lipo_disconnector_hw','source_commit':'e70656fad7e7756d6595a1598037d724dcd0e5d6','source_hashes':before,'file_count':len(before),'bytes':sum((SOURCE/n).stat().st_size for n in before),'board_format':value(tree,'version'),'schematic_format':value(sch,'version'),'generator':value(tree,'generator'),'project_meta':project['meta'],'project_design_meta':project['board']['design_settings']['meta'],'net_settings_meta':project['net_settings']['meta'],'preflight_and_pure_api_probes':checks,'default_policy':netclass.qualify_project(project),'native_effective_settings_observed':False,'footprints':len(fps),'padless_footprints':sum(not sx.children(fp,'pad') for fp in fps),'pads':len(pads),'routes':dict(collections.Counter(n[0] for n in p.routes(tree))),'protected_routes':sum(p.locked(n) for n in p.routes(tree)),'source_track_widths':sorted(set(n[1] for route in sx.children(tree,'segment') for n in sx.children(route,'width'))),'source_vias':[{k:value(v,k) for k in ['at','size','drill','layers','net','tstamp']}|{'free':'free' in v or sx.one(v,'free') is not None} for v in sx.children(tree,'via')],'edges':dict(collections.Counter(n[0] for n in edge)),'layers':value(tree,'layers'),'ids':{key:count(tree,key) for key in ['tstamp','uuid','module']},'footprint_reference_forms':{'fp_text_reference':sum(n[1]=='reference' for fp in fps for n in sx.children(fp,'fp_text')),'property_Reference':sum(sx.unquote(n[1])=='Reference' for fp in fps for n in sx.children(fp,'property'))},'net_names':sorted(names),'zones':[{k:value(z,k) for k in ['tstamp','uuid','net','net_name','layer','layers','name','priority','attr','keepout','placement','connect_pads','min_thickness','filled_areas_thickness','fill']}|{'polygon_count':len(sx.children(z,'polygon')),'derived_fill_count':len(sx.children(z,'filled_polygon'))} for z in zones],'rules_original':project['board']['design_settings']['rules'],'severities_original':project['board']['design_settings']['rule_severities'],'exclusions_original':project['board']['design_settings']['drc_exclusions'],'net_settings_original':project['net_settings'],'native_jobs':0,'engine_jobs':0,'network_requests':0,'source_unchanged':p.tree_hash(SOURCE)==before,'read_source_bindings':{str(x.relative_to(ROOT)):p.sha(x) for x in [RECEIPT,PARSER,ROOT/'.runs/licensed-closure-audit-003/audit.json',ROOT/'.runs/licensed-closure-followup-004/findings.json',ROOT/'autorouter/pipeline.py',ROOT/'autorouter/board_floor.py',ROOT/'autorouter/floor_context.py',ROOT/'autorouter/native.py',ROOT/'autorouter/placement_transform.py']}}
 assert observations['source_unchanged']
 (HERE/'audit.json').write_text(json.dumps(observations,indent=2,sort_keys=True)+'\n')
 print(json.dumps({key:observations[key] for key in ['file_count','bytes','board_format','schematic_format','footprints','padless_footprints','pads','routes','edges','ids','footprint_reference_forms','preflight_and_pure_api_probes','source_unchanged']},indent=2))
if __name__=='__main__':main()
