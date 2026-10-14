"""Current shared driver's pre-native copy ownership control, authored bytes."""
from pathlib import Path
import hashlib,json,sys
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from experiments.original_project_native_v1 import driver as d
from experiments.arcdice_native_class_v1 import source
root=HERE/'copy-case';(root/'.runs').mkdir(parents=True);out=root/'.runs/arcdice-original';original=out/'original';moved=root/'retained-partial-original'
files={'LICENSE':b'authored license','README.md':b'authored readme','hardware/ArcDice.kicad_pcb':b'authored PCB','hardware/ArcDice.kicad_pro':b'{}','hardware/ArcDice.kicad_sch':b'authored SCH'}
real=Path.write_bytes;state={};owner_payload=b'private replacement owner PCB'
def replace(path,raw):
 value=real(path,raw)
 if path==original/'LICENSE' and not state:
  state['initial_identity']=[original.stat().st_dev,original.stat().st_ino];original.rename(moved);original.mkdir();(original/'hardware').mkdir()
  state['replacement_identity']=[original.stat().st_dev,original.stat().st_ino]
  real(original/'LICENSE',raw);real(original/'hardware/ArcDice.kicad_pcb',owner_payload)
 return value
def stop():raise d.p.Rejected('deliberate review stop before any Git/native')
with patch.object(d,'ROOT',root),patch.object(source,'capture',return_value=files),patch.object(d.p,'tool_manifest',side_effect=stop),patch.object(Path,'write_bytes',replace):
 result=d.experiment('arcdice',out,run_native=True)
state.update(native_jobs=0,git_calls=0,owner_file_preserved=(original/'hardware/ArcDice.kicad_pcb').read_bytes()==owner_payload,driver_status=result['status'],driver_error=result.get('error'),driver_sha256=hashlib.sha256(Path(d.__file__).read_bytes()).hexdigest(),copy_helper_sha256=hashlib.sha256((ROOT/'experiments/placement_handoff_native_v1/driver.py').read_bytes()).hexdigest())
assert state['owner_file_preserved'] is False and state['initial_identity']!=state['replacement_identity'] and result['status']=='failed'
print(json.dumps({'schema':1,'scope':'Exact shared driver pre-native seam; all input bytes authored, no Git/native/network','finding':'Nested original directory replacement overwrites replacement-owner PCB before source/runtime gates; outer ownership is insufficient','control':state},indent=2))
