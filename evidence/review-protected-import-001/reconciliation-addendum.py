"""Pure reconciliation readback on copied actual imported copper; no native."""
from pathlib import Path
import copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx
OUT=Path(__file__).resolve().parent;SCRATCH=OUT/'reconciliation-files';SCRATCH.mkdir(exist_ok=False)
BASE=ROOT/'evidence/preferences-native-qualification-001/preferences-native-partial-001'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
pins={n:sha(ROOT/n) for n in ('autorouter/pipeline.py','tests/test_protected_import.py')}
original=sx.read(BASE/'snapshot/smoke.kicad_pcb');imported=sx.read(BASE/'imported.kicad_pcb');protected=p.routes(original)
(SCRATCH/'imported.kicad_pcb').write_bytes((BASE/'imported.kicad_pcb').read_bytes())
audit={'imported_sha256':p.sha(SCRATCH/'imported.kicad_pcb')};candidate=p.transplant_routes(original,imported,protected=protected,audit=audit)
sx.write(SCRATCH/'candidate.kicad_pcb',candidate);data={'protected_route_import':audit}
results=[]
def check(name,record,expect):
 try:p.check_protected_import(SCRATCH,record,original,SCRATCH/'candidate.kicad_pcb',protected);accepted=True;error=None
 except Exception as exc:accepted=False;error=type(exc).__name__+': '+str(exc)
 assert accepted==expect,(name,accepted,error)
 results.append({'case':name,'accepted':accepted,'expected':expect,'error':error})
check('actual_reconstruction_positive',data,True)
for key in ('original_uuid','imported_uuid','non_uuid_sha256'):
 altered=copy.deepcopy(data);altered['protected_route_import']['matches'][0][key]='changed';check(key,altered,False)
(SCRATCH/'imported.kicad_pcb').write_bytes((BASE/'imported.kicad_pcb').read_bytes()+b'\n');check('stale_import_bytes',data,False)
(SCRATCH/'imported.kicad_pcb').write_bytes((BASE/'imported.kicad_pcb').read_bytes())
changed=copy.deepcopy(imported)
# Change a generated, unprotected route and recompute every reconciliation field.
protected_ids={r['imported_uuid'] for r in audit['matches']}
new=next(r for r in p.routes(changed) if sx.one(r,'uuid')[1] not in protected_ids)
sx.one(new,'width')[1]='0.123';sx.write(SCRATCH/'imported.kicad_pcb',changed)
rehashed={'imported_sha256':p.sha(SCRATCH/'imported.kicad_pcb')};p.transplant_routes(original,changed,protected=protected,audit=rehashed)
check('rehash_changed_generated_route_still_rejects_final_mismatch',{'protected_route_import':rehashed},False)
assert pins=={n:sha(ROOT/n) for n in pins}
(OUT/'reconciliation-addendum.json').write_text(json.dumps({'scope':'Pure actual retained evidence reconstruction; no new native validation.','source_pins':pins,'all_passed':True,'cases':results},indent=2)+'\n')
print(json.dumps({'cases':len(results),'all_passed':True,'source_pins':pins}))
