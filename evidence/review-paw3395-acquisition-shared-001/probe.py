"""Offline, tiny whole-flow falsifiers using the author's real shared-profile fixture.
Mocked transport/Git only; real material, data, response and canonical files.
"""
from pathlib import Path
import argparse, hashlib, json, sys
from unittest import mock
P=argparse.ArgumentParser();P.add_argument('--snapshot',required=True);P.add_argument('--output',required=True);A=P.parse_args()
snapshot=Path(A.snapshot).resolve();out=Path(A.output).resolve();out.mkdir(exist_ok=False)
sys.path.insert(0,str(snapshot))
from experiments.licensed_acquisition_v2 import test_fetch as tests
f=tests.f
results=[]
for case in ('positive','late_original','late_response','late_acquired','late_shared'):
 t=tests.SharedProfileControls();t.setUp();count=0;fired=False;error=None;returned=None;target=None;before=None
 original_identity=f.git_identity
 def identity(root):
  global count,fired,target,before
  value=original_identity(root)
  receipt=t.out/'receipt.json'
  if receipt.exists() and json.loads(receipt.read_bytes()).get('status')=='acquired_unqualified':
   count+=1
   # Third sample after positive write is stable()'s final material() HEAD read,
   # after that stable() has already scanned .data and frozen response bytes.
   if count==3 and case!='positive':
    targets={'late_original':t.root/'.data/original','late_response':t.out/'response-000.bin',
             'late_acquired':t.root/'.data/expansion005/paw3395/.gitignore',
             'late_shared':t.root/'experiments/licensed_acquisition_v1/fetch.py'}
    target=targets[case];before=target.read_bytes();target.write_bytes(b'changed');fired=True
  return value
 try:
  with mock.patch.object(f,'git',side_effect=t.git),mock.patch.object(f,'git_identity',side_effect=identity):
   returned=t.run_small()
 except BaseException as e:error=type(e).__name__+': '+str(e)
 receipt=json.loads((t.out/'receipt.json').read_bytes())
 d=out/case;d.mkdir();(d/'receipt.json').write_bytes((t.out/'receipt.json').read_bytes())
 for path in t.out.glob('receipt.*.json'):(d/path.name).write_bytes(path.read_bytes())
 row={'case':case,'mutation_fired':fired,'positive_head_reads':count,'error':error,
      'returned_status':None if returned is None else returned['status'],'canonical_status':receipt['status'],
      'original_inputs_unchanged':receipt['original_inputs_unchanged'],
      'changed_path':None if target is None else str(target.relative_to(t.root)),
      'before_sha256':None if before is None else f.sha(before),
      'after_sha256':None if target is None else f.sha(target.read_bytes())}
 results.append(row);t.doCleanups()
result={'source_sha256':hashlib.sha256((snapshot/'experiments/licensed_acquisition_v1/fetch.py').read_bytes()).hexdigest(),
        'scope':'Synthetic four-byte transport, fake Git, actual small files; no network or real .data writes','cases':results}
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
