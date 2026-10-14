"""Pure selector staging ownership control; synthetic five files, no workers."""
from pathlib import Path
import copy,hashlib,json,sys
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from scripts import fetch_led_demo as demo,experiment_quality as q
rows=copy.deepcopy(demo.ROWS);payloads={}
for row in rows:
 raw=('authored pure selector '+row['source_path']+'\n').encode();payloads[row['source_path']]=raw
 row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),git_blob_sha1=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest())
def prepare(name):
 root=HERE/name;project=root/'.data/led-demo-001/project';project.mkdir(parents=True);(root/'.runs').mkdir()
 for filename,raw in payloads.items():(project/filename).write_bytes(raw)
 return root
normal=prepare('normal');attack=prepare('replacement');target=attack/'.runs/led-demo-benchmark-source';moved=attack/'retained-partial-source'
original_write=Path.write_bytes;state={};owner_raw=b'private replacement-owner PCB sentinel'
def replace_between_writes(path,raw):
 value=original_write(path,raw)
 if path==target/'LICENSE' and not state:
  state['original_identity']=list((target.stat().st_dev,target.stat().st_ino));target.rename(moved);target.mkdir()
  state['replacement_identity']=list((target.stat().st_dev,target.stat().st_ino))
  original_write(target/'LICENSE',raw);original_write(target/'PushButtonLed.kicad_pcb',owner_raw)
 return value
with patch.object(demo,'ROWS',tuple(rows)),patch.object(q.c,'ROOT',normal):
 baseline=q.selected_source('push-button-led');assert baseline[0].is_file()
with patch.object(demo,'ROWS',tuple(rows)),patch.object(q.c,'ROOT',attack),patch.object(Path,'write_bytes',replace_between_writes):
 returned=q.selected_source('push-button-led')
state.update(selector_returned=str(returned[0]),replacement_owner_file_preserved=(target/'PushButtonLed.kicad_pcb').read_bytes()==owner_raw,retained_original_directory_exists=moved.is_dir(),native_execution=False,geometry_claim=False,source_sha256=hashlib.sha256((ROOT/'scripts/experiment_quality.py').read_bytes()).hexdigest(),helper_sha256=hashlib.sha256((ROOT/'experiments/placement_handoff_native_v1/driver.py').read_bytes()).hexdigest())
assert state['original_identity']!=state['replacement_identity'] and state['replacement_owner_file_preserved'] is False
print(json.dumps({'schema':1,'positive_exact_capture':True,'replacement_between_staging_writes':state,'finding':'Unchecked copy_bytes overwrites the replacement-owner PCB, then selected_source returns success because final hashes match.','scope':'Pure authored files/controlled API seam; no native/network/subprocess and no third-party geometry copied.'},indent=2))
