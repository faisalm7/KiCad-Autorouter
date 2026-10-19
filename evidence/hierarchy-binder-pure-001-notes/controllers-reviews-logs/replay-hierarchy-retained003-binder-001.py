"""Pure development replay of retained003; no new Native evidence/admission."""
import datetime,hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));sys.dont_write_bytecode=True
from autorouter import schematic_hierarchy as q, sexpr as sx
out=root/'.runs/hierarchy-binder-retained003-001.json';assert not out.exists()
base=root/'.data/boards/kicad-multichannel'
paths=[base/'multichannel_mixer.kicad_pcb',base/'multichannel_mixer.kicad_pro',base/'multichannel_mixer.kicad_sch',base/'channel_strip.kicad_sch',root/'evidence/runtime035-hierarchy-observation-001-notes/resume003/observation/native-pcb.json',root/'evidence/runtime035-hierarchy-observation-001-notes/failed001/observation/hierarchy.net']
raws=[p.read_bytes() for p in paths]
native=json.loads(raws[4])['native_classes'];net=sx.parse(raws[5].decode());source=sx.unquote(sx.one(sx.one(net,'design'),'source')[1])
try:
 proof=q.derive(raws[5],raws[0],raws[1],(json.dumps(native,indent=2)+'\n').encode(),source=native['source'],schematic_source=source,schematics={paths[i].name:raws[i] for i in (2,3)})
 record=dict(passed=True,proof=proof)
except Exception as exc:
 record=dict(passed=False,error=type(exc).__name__+': '+str(exc))
record.update(schema=1,kind='pure-retained003-hierarchy-binder-development-replay',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),Native_executed=False,support_admitted=False,routing_accepted=False,project_complete=False,
 source_pins=[dict(path=str(p.relative_to(root)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)) for p,raw in zip(paths,raws)],comparator_sha256=hashlib.sha256((root/'autorouter/schematic_hierarchy.py').read_bytes()).hexdigest(),
 scope='Completed001netlist and003PCBmap reused verbatim. Extracted nested classmap is serialized for strict pure API; no new process/freshness/native/admission proof. All historical source24errors/206warnings/ignoredchecks remain unchanged.')
assert [p.read_bytes() for p in paths]==raws
out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k not in ('proof','source_pins')}))
raise SystemExit(0 if record['passed'] else 1)
