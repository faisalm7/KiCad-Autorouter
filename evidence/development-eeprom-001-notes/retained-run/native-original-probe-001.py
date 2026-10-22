"""One original-project diagnostic via the unchanged shared Native Job."""
from pathlib import Path
import sys,json,hashlib,time,resource
ROOT=Path(__file__).resolve().parents[2];RUNTIME=ROOT/'.runs/runtime-directory-057/runtime'
sys.path.insert(0,str(RUNTIME));sys.dont_write_bytecode=True
from autorouter import pipeline as p,provenance as pv
self_pin=p.sha(Path(__file__));base=ROOT/'.runs/development-eeprom-001'
copy=json.loads((base/'reference-copy.json').read_bytes());source=Path(copy['reference_project'])/'EEPROM_Board.kicad_pcb'
assert Path(p.__file__).resolve()==RUNTIME/'autorouter/pipeline.py' and p.c.NATIVE_VERSION=='10.0.7'
assert p.sha(RUNTIME/pv.MANIFEST)=='9c667b15b916fc18fadec6dcbd6e0f9710a0c4cc6daeb36fc616f111ef03722e'
assert p.tree_hash(source.parent)==p.tree_hash(Path(copy['raw_project']))==copy['hashes']
job=p.Job(base/'native-original-001',60,protect_local_settings=True)
record=dict(schema=1,accepted=False,routing_attempted=False,Native=True,source=str(source),source_hashes=copy['hashes'],controller_sha256=self_pin,tools=p.tool_manifest(),status='running',unrouted_alone_is_routing_demand=True)
try:
 native=job.drc('original-drc',source,schematic_parity=True)
 record.update(status='completed',native=native,source_native_policy=p.native_accepted(native),source_native_reasons=p.native_rejection_reasons(native))
except BaseException as exc:
 record.update(status='diagnostic_refused',error=type(exc).__name__+': '+str(exc));raise
finally:
 assert p.sha(Path(__file__))==self_pin and p.tree_hash(source.parent)==p.tree_hash(Path(copy['raw_project']))==copy['hashes']
 record.update(source_unchanged=True,steps=job.steps,wall_seconds=time.monotonic()-job.started,scope='Original project on preserved byte-identical working copy, no routing; source Native conflicts and requested unrouted demand remain separate. Not candidate acceptance, electrical/physical/human qualification or new-family confirmation.')
 p.save_json(job.out/'result.json',record)
print(json.dumps(dict(status=record['status'],Native_counts=[native[k] for k in ('opens','blocking','warnings','exclusions')],source_native_policy=record['source_native_policy'],source_unchanged=True,accepted=False,routing=False)))
