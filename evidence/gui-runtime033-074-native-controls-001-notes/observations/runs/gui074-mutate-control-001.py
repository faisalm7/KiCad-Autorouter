"""Deliberately alter one fresh owned fault control after its saved positive proof."""
from pathlib import Path
import json,hashlib,datetime,sys
label,workspace=sys.argv[1:];assert label in ('source','settings','export')
base=Path('.runs/runtime-directory-033/runtime/.runs/gui-session074');control=base/'freshness-controls-001'/label;w=base/'jobs'/workspace
proof=json.loads((control/'preopen-001.json').read_bytes());assert proof['route']['current'] is True and proof['export']['current'] is True
assert Path(proof['workspace']).resolve()==w.resolve()
p=control/'project/owned1007-transport.kicad_pro' if label=='source' else w/'settings.json' if label=='settings' else w/'export/export.json';raw=p.read_bytes();before=hashlib.sha256(raw).hexdigest()
if label in ('source','settings'): altered=raw+b'\n';kind='append newline to owned source PRO' if label=='source' else 'append newline to own captured settings'
else:
 d=json.loads(raw);assert d['export_accepted'] is True;d['export_accepted']=1;altered=(json.dumps(d,indent=2)+'\n').encode();kind='typed export_accepted true changed to integer1'
r=control/'mutation-001.json';assert not r.exists();p.write_bytes(altered)
r.write_text(json.dumps({'schema':1,'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':label,'path':str(p.resolve()),'before_sha256':before,'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'mutation':kind,'original_source_untouched':True,'positive_proof_before_mutation':'preopen-001.json'},indent=2)+'\n')
print(json.dumps({'label':label,'mutated_owned_copy':True}))
