"""Explicit offline source qualification after acquisition; never a native pass."""
from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pour_rule_area as m
path=ROOT/'.data/expansion008/nus-usb-led/src/usb_led.kicad_pcb'
data=path.read_bytes()
assert hashlib.sha256(data).hexdigest()=='a8e69c14ceec9dd0954c3027cc89ca6bbb9c0b0ec3aeede5feacfdd47736f362'
rows=m.qualify(m.sx.parse(data.decode()))
assert len(rows)==1 and rows[0]['uuid']=='1abd2188-f015-4692-bf4a-117c7482b9fc' and rows[0]['layers']==['F.Cu']
assert path.read_bytes()==data
print('Exact acquired NUS source qualifies static pour intent; no native/export/routing claim.')
