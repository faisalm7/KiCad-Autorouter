"""Bounded synthetic normalization differential; no Native/tool/route claim."""
from pathlib import Path
import copy,json,resource,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,sexpr as sx
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();out=ROOT/'.runs/derived-copy-control-001';assert not out.exists();out.mkdir(mode=0o700)
source=['kicad_pcb',['version','20260101'],['unknown',['must','remain']],['footprint','"owned"',['zone',['filled_polygon',['must','remain']]]],['segment',['net','"owned"'],['start','0','0'],['end','1','1']],['zone',['uuid','"owned-zone"'],['net','"owned"'],['polygon',['pts',['xy','0','0'],['xy','20','0'],['xy','20','20'],['xy','0','20']]],['unknown',['must','remain']],['filled_polygon',['layer','"F.Cu"'],['pts',*[['xy',str(i%100),str(i//100)] for i in range(20000)]]]]]
raw=(sx.dump(source)+'\n').encode();(out/'source.sexpr').write_bytes(raw)
def old(tree):
 t=copy.deepcopy(tree);t[:]=[n for n in t if not isinstance(n,list) or not n or n[0] not in p.ROUTES]
 for z in sx.children(t,'zone'):z[:]=[n for n in z if not isinstance(n,list) or not n or n[0] not in p.DERIVED_ZONE]
 return t
expected=old(source);assert p.immutable(source)==expected
rows={}
for label,func in [('previous',old),('project_retained_before_copy',p.immutable)]:
 start=time.monotonic();c=time.process_time()
 for _ in range(20):assert func(source)==expected
 rows[label]=dict(wall_seconds=time.monotonic()-start,CPU_seconds=time.process_time()-c)
 assert time.monotonic()-START<15
assert (sx.dump(source)+'\n').encode()==raw
p.save_json(out/'result.json',dict(schema=1,passed=True,kind='synthetic-pure-invariant-projection-differential-v1',source_sha256=p.sha(out/'source.sexpr'),generated_points=20000,repetitions_per_method=20,same_exact_output=True,source_unchanged=True,rows=rows,whole_wall_seconds=time.monotonic()-START,whole_full_CPU_seconds=cpu()-CPU0,pipeline_sha256=p.sha(ROOT/'autorouter/pipeline.py'),controller_sha256=p.sha(Path(__file__)),Native_executed=False,accepted=False,project_complete=False,scope='Owned synthetic AST normalization only. The previous function is the exact pre-change immutable projection. No actual board routing/delivery/comparative/electrical/Native/GUI claim; pure microbenchmark timings are not user-visible job speed. Authoring/review/qualification costs additional.'))
print(json.dumps(dict(passed=True,rows=rows)))
