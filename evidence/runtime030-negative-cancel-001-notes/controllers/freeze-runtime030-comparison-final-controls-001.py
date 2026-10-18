"""Freeze remaining functional controls; no engine, selection or validation run."""
from pathlib import Path
import hashlib,json,sys,time,resource
START=time.monotonic()
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
def save(q,j):
 q.parent.mkdir(exist_ok=False)
 with q.open('x') as stream:json.dump(j,stream,indent=2);stream.write('\n')
runtime=ROOT/'.runs/runtime-directory-030/runtime'
material=json.loads((ROOT/'.runs/runtime030-native-controls-preparation-001/material.json').read_text())
old=json.loads((ROOT/'evidence/runtime026-interf-native7-prerequisite-001-notes/enclosure/protocol.json').read_text())
source=Path(old['source']);assert p.tree_hash(source.parent)==old['source_hashes']
manifest=runtime/'runtime-distribution.json';assert sha(manifest)==material['runtime_manifest_sha256']
child=runtime/'.runs/qualify-native7-comparison-route-child-001.py';assert sha(child)=='1ff4ddb3ef5ea56bd381a40da306d1a71bbbea4cc9aa048e3bdd7c870b73e879'
base=dict(schema=1,runtime=str(runtime),runtime_manifest_sha256=sha(manifest),source_head=material['source_head'],tools=material['runtime_tools'],source=str(source),source_hashes=old['source_hashes'],source_rights=old['source_rights'],route_seconds=420,child_sha256=sha(child))
frozen=[]
for profile in ('standard','tuned'):
 folder=ROOT/'.runs'/('runtime030-comparison-completed-'+profile+'-001');output=runtime/'.runs'/('native7-comparison-completed-'+profile+'-001');assert not output.exists()
 enclosure=ROOT/'.runs/enclose-runtime030-independent-control-001.py'
 plan=dict(base,kind='caller-bound-comparison-completed-functional-control',profile=profile,mode='completed',controller=str(child),controller_sha256=sha(child),enclosure_sha256=sha(enclosure),output=str(output),whole_wall_full_cpu_seconds=600,pass_key='controls_passed',scope='One prospective changed-code current installed comparison API functional attempt on exposed Interf, not a new fair matrix or general gain. Accept a genuine validated delivery if obtained; otherwise only a central-reader-verified completed-negative qualifies. Unsupported, stale, invalid-source, cancellation and budget outcomes remain failures of this control. All original constraints and warnings retained;420 Route and120 fresh export within600 whole wall/fullCPU. Preparation/authoring/review additional; no board-specific modification.')
 q=folder/'protocol.json';save(q,plan);frozen.append(dict(protocol=str(q),sha256=sha(q),enclosure=str(enclosure)))
parent=runtime/'.runs/native7-comparison-cancel-attempt-001';assert not parent.exists()
folder=ROOT/'.runs/runtime030-comparison-engine-cancel-001';folder.mkdir()
child_plan=dict(base,profile='tuned',mode='cancel',output=str(parent),whole_wall_full_cpu_seconds=220)
q=folder/'child-protocol.json'
with q.open('x') as stream:json.dump(child_plan,stream,indent=2);stream.write('\n')
driver=runtime/'.runs/cancel-runtime030-comparison-engine-001.py';assert sha(driver)=='689067ac0b9a61d4ef8246952a4b22b6e32f7fca9c9963608cc05e78e6073b3b'
observer=runtime/'.runs/owned-child-path-observer-001.py';assert sha(observer)==sha(ROOT/'.runs/owned-child-path-observer-001.py')
enclosure=ROOT/'.runs/enclose-runtime030-independent-control-002.py';output=runtime/'.runs/native7-comparison-cancellation-control-001';assert not output.exists()
plan=dict(base,kind='actual-owned-comparison-engine-cancellation-functional-control',profile='tuned',controller=str(driver),controller_sha256=sha(driver),controller_args=['--runtime',str(runtime)],enclosure_sha256=sha(enclosure),observer_sha256=sha(observer),child=str(child),child_protocol=str(q),child_protocol_sha256=sha(q),route_parent=str(parent),output=str(output),whole_wall_full_cpu_seconds=230,pass_key='controls_passed',scope='One actual current installed corrected-comparison tuned engine cancellation using existing CliJob.cancel and finite exact owned-executable observer.420 route declaration;220 child driver acceptance and230 external whole wall/fullCPU cap. Requires matched cancelled engine PID and durable journal, source/tool freshness and cleanup, no accepted/exported result. No GUI/allphase/SIGINT-only/permanent-descendant/fairmatrix claim. Existing sandbox, runner, resource and publication helpers reused; preparation/authoring/review additional.')
q=folder/'protocol.json'
with q.open('x') as stream:json.dump(plan,stream,indent=2);stream.write('\n')
frozen.append(dict(protocol=str(q),sha256=sha(q),enclosure=str(enclosure)))
print(json.dumps(dict(frozen=frozen,source_files=len(old['source_hashes']),sampled_wall_seconds=time.monotonic()-START,preparation_only=True)))
