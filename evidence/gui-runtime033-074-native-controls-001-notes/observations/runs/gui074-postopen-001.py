from pathlib import Path
import sys,json,datetime
ROOT=Path(__file__).resolve().parents[1];runtime=ROOT/'.runs/runtime-directory-033/runtime';sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
base=runtime/'.runs/gui-session074';w=base/'jobs/autorouter-gui-f6382f193875484db910f6af4c4d143d';pre=json.loads((base/'preopen-001.json').read_bytes());before=pre['snapshot_hashes'];after=p.tree_hash(w/'export');snapshot=base/'postopen-snapshot-001';snapshot.mkdir()
for name,raw in io.inventory(w/'export',contents=True).items():
 target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
assert p.tree_hash(snapshot)==after
changed={key:dict(before=before.get(key),after=after.get(key)) for key in sorted(set(before)|set(after)) if before.get(key)!=after.get(key)}
assert p.tree_hash(base/'project')==json.loads((base/'prepared-state.json').read_bytes())['source_hashes']
p.save_json(base/'postopen-001.json',dict(schema=1,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),workspace=str(w),snapshot=str(snapshot),snapshot_hashes=after,changed=changed,source_unchanged=True,candidate_PCB_unchanged=before['validation/candidate/owned1007-transport.kicad_pcb']==after['validation/candidate/owned1007-transport.kicad_pcb'],observed=['Open checked export invoked own current CLI readback before opening KiCad manager.','Tools > PCB Editor opened actual candidate. Pixel display six pads/six segments/one via/three nets/unrouted0, ROUTE/KEEP/GND copper and filledzone. Older-format-on-save banner visible, no edit/save performed.','PCB closed with Cmd-W; project closed using File > Close Project; no save/discard prompt.'],limits='Before-open proof retained separately. Inspection does not establish new Native validity after any editor metadata changes. No human/physical review.'))
print(json.dumps(dict(changed=list(changed),PCB_unchanged=True)))
