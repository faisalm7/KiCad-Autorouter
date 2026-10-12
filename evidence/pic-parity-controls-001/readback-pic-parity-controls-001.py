import sys,json,hashlib,types
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'experiments/pic_parity_controls_v1'))
import driver as d
out=R/'.runs/pic-parity-controls-001';r=d.read(out/'summary.json')
assert r['status']=='controls_passed' and r['controls_passed']is True
assert d.source_binding()==(r['source_hashes'],r['source_bytes'])
assert {k:v for k,v in d.inventory(out).items()if k!='summary.json'}==r['completed_evidence']
for rel,value in r['runtime_sources'].items():assert d.digest(out/'code'/rel)==value==d.digest(R/rel)
baseline=None;rows=[]
for row in r['cases']:
 case=out/row['case'];binding=d.read(case/'parity-binding.json');job=types.SimpleNamespace(out=case,captured=row['stage_evidence'],input_after=binding['after'],steps=row['steps'])
 result=d.validate_case(job,row,baseline);assert result==row['predicate'] and result['predicate_met']
 if baseline is None:baseline=result['ordinary_fingerprint']
 native=result['native'];rows.append({'case':row['case'],'parity_count':result['parity_count'],'counts':{k:native[k]for k in ('opens','blocking','warnings','exclusions')}})
receipt={'schema':1,'scope':'Readback only; no native rerun. Shared helper rederives raw predicates, process, project and evidence bindings.','summary_sha256':d.digest(out/'summary.json'),'passed':True,'cases':rows,'frozen_files':len(r['completed_evidence']),'runtime_sources':len(r['runtime_sources']),'wall_seconds':r['wall_seconds'],'full_cpu_seconds':r['total_cpu_seconds'],'routing_accepted':False,'production_support_changed':False}
path=R/'.runs/pic-parity-controls-001-readback.json';assert not path.exists();path.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
