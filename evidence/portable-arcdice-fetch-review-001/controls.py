"""Tiny authored filesystem ownership controls; no HTTP/native/JVM/Git."""
import time
START=time.monotonic()
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import copy,hashlib,json,shutil,subprocess,traceback
from unittest.mock import patch
from autorouter import handoff as h, pipeline as p
from scripts import fetch_led_demo as demo
from experiments.placement_handoff_native_v1 import driver
D=Path(__file__).resolve().parent
MATERIAL=[ROOT/n for n in (*demo.MATERIAL,*demo.ARC_MATERIAL)]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
BEFORE={str(x.relative_to(ROOT)):digest(x)for x in MATERIAL}
def no_process(*a,**k):raise AssertionError('no child processes in filesystem controls')
results=[]
def save(name,data):(D/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
def fixture(name):
    root=D/name;root.mkdir()
    for n in (*demo.MATERIAL,*demo.ARC_MATERIAL):
        target=root/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/n).read_bytes())
    cfg=copy.deepcopy(demo.ARC_PROFILE);values={}
    for row in cfg['rows']:
        raw=('authored pure control '+row['source_path']+'\n').encode();values[row['source_path']]=raw
        row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),git_blob_sha1=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest())
    cfg['bytes']=sum(len(v)for v in values.values());cfg['network_byte_cap']=cfg['bytes']+5
    def transport(row,req,path,allowance,remaining):
        remaining();raw=values[row['source_path']]
        with path.open('xb')as handle:handle.write(raw)
        req.update(received_bytes=len(raw),response_sha256=demo.shared.sha(raw),status='response_received',http_status=200,wall_seconds=0.)
        return raw
    return root,cfg,values,transport

def check_fetch(name,inject=None):
    root,cfg,values,transport=fixture(name);out=root/'.data/arcdice-demo-control'
    actual_copy=driver.copy_bytes;injected=[]
    def copier(files,target,**kwargs):
        if inject=='parent-before'and not injected:
            injected.append(True);out.rename(root/'preserved-out');out.mkdir();(out/'foreign-owner').write_bytes(b'keep')
        owner=actual_copy(files,target,**kwargs)
        if inject=='project-after'and target.name=='project':
            injected.append(True);target.rename(root/'preserved-project');shutil.copytree(root/'preserved-project',target)
        if inject=='native-after'and target.name=='native-project':
            injected.append(True);target.rename(root/'preserved-native');shutil.copytree(root/'preserved-native',target)
        return owner
    exc=None;record=None
    with patch.object(demo,'ARC_PROFILE',cfg),patch.object(driver,'copy_bytes',copier):
        try:record=demo.fetch_demo('.data/arcdice-demo-control',profile_id='arcdice',fetch=True,root=root,transport=transport)
        except Exception as error:exc={'type':type(error).__name__,'message':str(error)}
    if inject is None:
        assert exc is None and record['status']=='acquired_unqualified'and record['source_files_exact']is True and record['accepted']is False
        assert demo.shared.inventory(out/'project')['file_count']==5 and demo.shared.inventory(out/'native-project')['file_count']==7
    else:
        assert injected and exc is not None
        if inject=='parent-before':
            assert set(x.name for x in out.iterdir())=={'foreign-owner'}and(out/'foreign-owner').read_bytes()==b'keep'
            assert not(out/'project').exists()
        else:
            replaced=out/('project'if inject=='project-after'else'native-project')
            expected=values if inject=='project-after'else{**values,**{n:values[v]for n,v in cfg['native_packet_notice_copies'].items()}}
            assert {n:(replaced/n).read_bytes()for n in expected}==expected
            assert not(out/'result.json').exists()
    results.append({'case':name,'injection':inject,'passed':True,'exception':exc,'new_network_requests':0,'new_native_jobs':0,'foreign_replacement_preserved':inject is not None})

def run():
    parent=D/'copy-parent';parent.mkdir();owner={};h.capture_destination(owner,parent)
    lifecycle=driver.copy_bytes({'hardware/owned.txt':b'authored'},parent/'packet',expected_parent_owner=owner)
    assert h.owned_destination(lifecycle)==parent/'packet'
    default=driver.copy_bytes({'x':b'authored'},parent/'legacy')
    assert h.owned_destination(default)==parent/'legacy'
    results.append({'case':'expected-parent-and-legacy-default','passed':True,'original_identity_returned':True})
    check_fetch('positive')
    check_fetch('parent-takeover','parent-before')
    check_fetch('project-takeover','project-after')
    check_fetch('native-takeover','native-after')
    assert {str(x.relative_to(ROOT)):digest(x)for x in MATERIAL}==BEFORE
    return {'status':'passed','controls':results,'source_sha256_before_after':BEFORE,'new_network_requests':0,'new_native_jobs':0,'new_git_calls':0,'fixture_scope':'Only authored tiny payloads in synthetic fixed-profile controls; no actual Creator payloads or fetch/native qualification','selector_scope':'Current selector still research-only; upcoming portable selector not yet reviewed'}
try:
    with patch.object(subprocess,'run',no_process),patch.object(subprocess,'Popen',no_process):record=run()
except BaseException as exc:record={'status':'failed','error':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc(),'completed_controls':results}
record.update(wall_seconds=time.monotonic()-START,lifetime_self_cpu_seconds=time.process_time())
save('controls-result.json',record)
print(json.dumps({k:record.get(k)for k in ('status','error','message','wall_seconds','lifetime_self_cpu_seconds')}))
raise SystemExit(0 if record['status']=='passed'else 1)
