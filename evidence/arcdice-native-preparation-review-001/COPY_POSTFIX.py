"""Exact final descriptor copy controls; no native/Git, authored bytes only."""
from pathlib import Path
import hashlib,json,os,sys
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from experiments.placement_handoff_native_v1 import driver as d
files={'LICENSE':b'authored license','README.md':b'authored readme','hardware/ArcDice.kicad_pcb':b'authored PCB','hardware/ArcDice.kicad_pro':b'{}','hardware/ArcDice.kicad_sch':b'authored SCH'}
positive=HERE/'copy-fixed-positive';d.copy_bytes(files,positive);assert d.inventory(positive)==d.hashes(files)
results={'positive_exact_copy':True}
for label,threshold,nested in [('root-replacement',1,False),('nested-replacement',3,True)]:
 base=HERE/('copy-fixed-'+label);base.mkdir();target=base/'original';moved=base/'retained-source';calls=[];real=os.write;owner_payload=b'private replacement owner PCB'
 def replace(fd,raw):
  count=real(fd,raw);calls.append(fd)
  if len(calls)==threshold:
   path=target/'hardware' if nested else target;path.rename(moved);path.mkdir()
   if not nested:(path/'hardware').mkdir()
   (path/'ArcDice.kicad_pcb' if nested else path/'hardware/ArcDice.kicad_pcb').write_bytes(owner_payload)
  return count
 with patch.object(d.os,'write',side_effect=replace):
  try:d.copy_bytes(files,target)
  except d.p.Rejected as exc:results[label]=str(exc)
  else:raise AssertionError('replaced copy directory adopted')
 owner=target/'hardware/ArcDice.kicad_pcb';assert owner.read_bytes()==owner_payload
 assert len(calls)==threshold and moved.is_dir()
 results[label+'_owner_preserved']=True
results['helper_sha256']=hashlib.sha256(Path(d.__file__).read_bytes()).hexdigest()
print(json.dumps({'schema':1,'scope':'Direct current fd copy helper, authored files; no native/network/Git','results':results},indent=2))
