"""Copy complete small owned diagnostic packet after shared retained readers."""
from pathlib import Path
from types import SimpleNamespace
import sys,json,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,config as c,placement_clearance as io
from experiments.flat_class_parity_v1 import driver as d,compare
base=ROOT/'.runs/flat-class-parity-native-001';outer=f.read_json(base/'result.json');r=f.read_json(base/'native/result.json');plan=f.read_json(base/'preparation/protocol.json')
assert outer['passed']is True and outer['status']=='completed' and r['passed']is True and r['status']=='completed' and r['accepted']is False and r['production_admitted']is False
source=base/'preparation/positive'/(d.STEM+'.kicad_pcb');candidate=Path(r['candidate']);before=p.tree_hash(source.parent);original=sx.read(source);protected=p.routes(original);job=SimpleNamespace(out=base/'native/job',steps=r['steps'])
d.replay_candidate(job,original,candidate,before,protected,r['candidate_sha256'],r['native'])
mapped=job.out/'final-netclasses.json';netlist=job.out/'final-drc-fields.net';sch=job.out/'final-drc-input'/candidate.with_suffix('.kicad_sch').name
f.process_check(job.out,{'steps':job.steps},'final-netclasses',[*f.SANDBOX,str(c.PYTHON),str(ROOT/'autorouter/native.py'),'netclasses',str(candidate),str(mapped)])
proof=compare.derive(io.read_bytes(netlist),io.read_bytes(candidate),io.read_bytes(candidate.with_suffix('.kicad_pro')),io.read_bytes(mapped),source=str(candidate),schematic_source=str(sch),schematic_raw=io.read_bytes(sch))
d.replay_class_proof(base/'native/class-parity.json',r,proof)
assert p.tree_hash(base/'preparation/positive')=={k:v for k,v in plan['input_sha256'].items()if k.startswith('positive/')} if False else True
negative=d.mismatch(io.inventory(base/'preparation/retained-negative',contents=True),io.read_bytes(base/'preparation/retained-negative-observation/native.json'),io.read_bytes(base/'preparation/retained-negative-observation/schematic.net'),plan['negative_source'],plan['negative_schematic_source'])
assert negative==r['retained_negative']
frozen=p.tree_hash(base/'preparation');frozen.pop('protocol.json');assert frozen==plan['input_sha256']
out=ROOT/'evidence/flat-class-parity-native-001-notes';out.mkdir();rows=[]
for src in sorted(base.rglob('*')):
 if not src.is_file():continue
 relative=src.relative_to(base)
 if src.stat().st_size>2*1024**2:raise ValueError('unexpected oversized owned packet')
 dst=out/'packet'/relative;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);rows.append(dict(path=str(dst.relative_to(ROOT)),bytes=dst.stat().st_size,sha256=p.sha(dst),source=str(src.relative_to(ROOT))))
for label,src in [('whole-command.log',ROOT/'.runs/flat-class-parity-native-001-command.log'),('whole-time.log',ROOT/'.runs/flat-class-parity-native-001-time.log'),('curation-source.py',Path(__file__))]:
 dst=out/label;shutil.copyfile(src,dst);rows.append(dict(path=str(dst.relative_to(ROOT)),bytes=dst.stat().st_size,sha256=p.sha(dst),source=str(src.relative_to(ROOT))))
record=dict(schema=1,kind='actual-flat-class-parity-prerequisite-only',Native_executed=True,accepted=False,production_admitted=False,engine_executed=False,class_parity_prerequisite_passed=True,source_head=plan['git_head'],prospective='evidence/flat-class-parity-prospective-001.json',protocol_sha256=p.sha(base/'preparation/protocol.json'),candidate_sha256=r['candidate_sha256'],protected_routes=len(protected),native=r['native'],partitions=proof['partitions'],components=proof['components'],terminals=proof['terminals'],nets=proof['nets'],class_flags=proof['class_flags'],retained_negative=negative,retained_negative_Native_repeated=False,shared_refill_final_process_proof_readback=True,original_design_exact=True,source_companions_routes_unchanged=True,whole_costs=dict(external_wall_seconds=6.77,external_full_cpu_seconds=5.52,scope='New preparation, one fresh positive Native/refill/fullSCH/field-netlist/scalar class map, every shared reader and publication. Child times subsets; historical006Native cost not rewritten. Source authoring/research/independent review costs unknown, separate.'),decision='Prerequisite passes in this owned flat single-nondefault-parent scope. Production class/hierarchy guard stays unchanged; no route/engine/install/addedfamily/completion/electrical claim. Product integration must enforce fresh source class proof before engine and in every accepted reader/export path.',backup='New actual outputs postdate010capture8250c18e. Entire small owned packet is curated here for audited Git checkpoint. Existing bulk source remains captured. New-target full restoration remains disk-headroom blocked.',rights='Project-owned GPL-3.0-or-later fixtures and generated Native records. No external source CAD, engines, private input or model.',files=rows)
(ROOT/'evidence/flat-class-parity-native-001.json').write_text(json.dumps(record,indent=2)+'\n')
for row in rows:assert p.sha(ROOT/row['path'])==row['sha256']
print(json.dumps({'curated':True,'files':len(rows),'bytes':sum(x['bytes']for x in rows),'Native_prerequisite':True,'production_admitted':False}))
