"""Bounded falsifiers: tiny files + virtual metadata/iterator; no large allocations."""
from pathlib import Path
from unittest.mock import patch
import importlib.util,json,os,sys,tempfile
HERE=Path(__file__).resolve().parent;SNAP=HERE/'snapshot-before-bounds-fix';sys.path.insert(0,str(SNAP))
spec=importlib.util.spec_from_file_location('reporter_before_bounds',SNAP/'generate.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
with tempfile.TemporaryDirectory(dir=HERE)as tmp:
 root=Path(tmp).resolve();g.ROOT=root;a=root/'a';a.write_bytes(b'x');b=root/'b';b.write_bytes(b'y')
 reader=g.Reader();reader.bytes(a);real_stat=Path.stat;real_read=Path.read_bytes;read_calls=[]
 def fake_stat(path,*args,**kwargs):
  info=real_stat(path,*args,**kwargs)
  if path==a:
   values=list(info);values[6]=33*1024**2;return os.stat_result(values)
  return info
 def tracked_read(path):read_calls.append(str(path));return real_read(path)
 with patch.object(Path,'stat',fake_stat),patch.object(Path,'read_bytes',tracked_read):reader.stable()
 oversized={'virtual_size_bytes':33*1024**2,'actual_size_bytes':1,'stable_passed':True,'body_read_after_oversize_metadata':str(a)in read_calls}
 reader=g.Reader();reader.trees[str(root)]=['a'];events=[]
 def stream(_path,_pattern):
  yield a;events.append('saw expected a');yield b;events.append('continued after unexpected b');raise RuntimeError('continued beyond already-mismatched inventory')
 try:
  with patch.object(Path,'rglob',stream):reader.stable()
 except RuntimeError as exc:overflow={'events':events,'sentinel_reached':True,'error':str(exc)}
 else:raise AssertionError('sentinel did not run')
 result={'native_or_engine_executed':False,'large_allocation_or_large_file_created':False,'oversize_final_read':oversized,'late_extra_inventory_continued':overflow,'interpretation':'Reproduces unbounded final read/scan design under tiny mocked metadata/iterator. Does not indicate a wrong actual index.'}
 with (HERE/'bounds-reproduction.json').open('x')as stream:json.dump(result,stream,indent=2);stream.write('\n')
 print(json.dumps(result,indent=2))
