"""Read-only original/source preparation. No native or run-output access."""
from decimal import Decimal
from fractions import Fraction
import hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import sexpr as sx
source=ROOT/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def inventory(root):
    result={}
    for p in root.rglob('*'):
        assert not p.is_symlink()
        if p.is_file():
            assert len(result)<32 and p.stat().st_size<2*1024*1024
            b=p.read_bytes();result[str(p.relative_to(root))]={'bytes':len(b),'sha256':sha(b),'git_blob_sha1':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()}
    return dict(sorted(result.items()))
before=inventory(source.parent);acq=json.loads((ROOT/'data/sources.json').read_text())
expected={}
for r in acq['files']:
    if r.get('project_id')=='kicad-pic-programmer':
        rel=str((ROOT/'.data'/r['destination']).relative_to(source.parent))
        assert rel not in expected
        expected[rel]={k:r[k] for k in ('bytes','sha256','git_blob_sha1')}
assert before==expected and len(before)==15
board=sx.read(source);fps=sx.children(board,'footprint')
fp=next(f for f in fps if any(sx.unquote(x[1])=='Reference' and sx.unquote(x[2])=='JP1' for x in sx.children(f,'property')))
nm=lambda s:int(Decimal(s)*1000000)
polys=[];pads=[]
for p in sx.children(fp,'pad'):
    assert p[3]=='custom';at=sx.one(p,'at');assert len(at)==3
    primitive=sx.one(sx.one(p,'primitives'),'gr_poly');points=sx.children(sx.one(primitive,'pts'),'xy')
    assert len(points)==5 and sx.one(primitive,'width')==['width','0'] and sx.one(primitive,'fill')==['fill','yes']
    poly=[(nm(q[1])+nm(at[1]),nm(q[2])+nm(at[2])) for q in points]
    polys.append(poly);pads.append({'uuid':sx.unquote(sx.one(p,'uuid')[1]),'number':sx.unquote(p[1]),'net_ast':sx.one(p,'net'),'local_relative_to_footprint_nm':poly,'anchor_size_ast':sx.one(p,'size'),'layers_ast':sx.one(p,'layers')})
def dist(p,a,b):
    v=(b[0]-a[0],b[1]-a[1]);w=(p[0]-a[0],p[1]-a[1]);den=v[0]**2+v[1]**2
    t=max(Fraction(0),min(Fraction(1),Fraction(w[0]*v[0]+w[1]*v[1],den)))
    q=(a[0]+t*v[0],a[1]+t*v[1]);d=(p[0]-q[0])**2+(p[1]-q[1])**2
    return d,q
best=None
for i in (0,1):
    for p in polys[i]:
        for a,b in zip(polys[1-i],polys[1-i][1:]+polys[1-i][:1]):
            d,q=dist(p,a,b)
            if best is None or d<best[0]:best=(d,i,p,q,a,b)
clearance=nm(sx.one(fp,'clearance')[1]);after=inventory(source.parent);assert before==after
files=['AGENTS.md','MASTER_PROMPT.md','data/sources.json','toolchain.lock.json','autorouter/floor_context.py','experiments/pic_custom_observer_v1/driver.py','experiments/pic_custom_observer_v1/worker.py','experiments/pic_custom_observer_v1/mapping.py']
result={'schema':1,'status':'source_only_preparation','native_executed':False,'actual_run_outputs_read':False,'source_unchanged':True,'source_inventory':before,'source_bytes':sum(x['bytes'] for x in before.values()),'footprints':len(fps),'pads':sum(len(sx.children(f,'pad')) for f in fps),'jp1':{'fp_at_ast':sx.one(fp,'at'),'fp_layer_ast':sx.one(fp,'layer'),'clearance_nm':clearance,'pads':pads,'nearest_vertex_edge_squared_nm':str(best[0]),'distance_mm':math.sqrt(best[0])/1e6,'shortfall_nm':clearance-math.sqrt(best[0]),'squared_below_clearance':best[0]<clearance**2,'witness_pad_index':best[1],'witness_vertex_nm':best[2],'witness_projection_nm':[str(x) for x in best[3]],'witness_edge_nm':[best[4],best[5]]},'source_read_hashes':{s:sha((ROOT/s).read_bytes()) for s in files},'limits':'Analytic source geometry only; native provider tolerance/rounding and exact native effective geometry remain unobserved. No routing qualification or immutable-source infeasibility conclusion before report.'}
(HERE/'source-preparation-001.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','source_bytes','footprints','pads')}));print(json.dumps(result['jp1'],indent=2))
