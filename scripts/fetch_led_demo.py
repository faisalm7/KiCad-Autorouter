"""Fetch five pinned public LED design files into a fresh local demo directory."""
import time,resource
START=time.monotonic()
def cpu():
    own=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime
CPU_START=cpu()
import argparse,copy,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.licensed_acquisition_v1 import fetch as shared
from autorouter import floor_route as publication,handoff as h
ROWS=({'bytes': 1066, 'commit': '29c46b7c03d2afd9fe3a58fe2070309b12f94b42', 'destination': 'push-button-led/LICENSE', 'git_blob_sha1': '388e1398eb6be796a0ceab266799819af37311b9', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/gurusaeth12/push-button-led-kicad/29c46b7c03d2afd9fe3a58fe2070309b12f94b42/LICENSE', 'repository': 'gurusaeth12/push-button-led-kicad', 'rights_basis': 'Root MIT notice by Gurusaeth covers supplied editable hardware/documentation; README has no separate hardware-scope sentence. Retain exact LICENSE/README; embedded stock KiCad content exception only, models unclosed.', 'sha256': '18f4f144c2d9457195bb6383cdebed6e2e99df4c3d70378363972ddcc992f7a6', 'source_path': 'LICENSE'}, {'bytes': 103334, 'commit': '29c46b7c03d2afd9fe3a58fe2070309b12f94b42', 'destination': 'push-button-led/PushButtonLed.kicad_pcb', 'git_blob_sha1': '1548cd51c6ea153763fd3e9741d3c3af8355775a', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/gurusaeth12/push-button-led-kicad/29c46b7c03d2afd9fe3a58fe2070309b12f94b42/PushButtonLed.kicad_pcb', 'repository': 'gurusaeth12/push-button-led-kicad', 'rights_basis': 'Root MIT notice by Gurusaeth covers supplied editable hardware/documentation; README has no separate hardware-scope sentence. Retain exact LICENSE/README; embedded stock KiCad content exception only, models unclosed.', 'sha256': 'a85c5b499b7803d184ec34ef396746afcd16c0557166bd63d7675beb7b61f7a3', 'source_path': 'PushButtonLed.kicad_pcb'}, {'bytes': 16753, 'commit': '29c46b7c03d2afd9fe3a58fe2070309b12f94b42', 'destination': 'push-button-led/PushButtonLed.kicad_pro', 'git_blob_sha1': '8acce63ccb417f5f4ac0c1ad832d071a7e5b1e4f', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/gurusaeth12/push-button-led-kicad/29c46b7c03d2afd9fe3a58fe2070309b12f94b42/PushButtonLed.kicad_pro', 'repository': 'gurusaeth12/push-button-led-kicad', 'rights_basis': 'Root MIT notice by Gurusaeth covers supplied editable hardware/documentation; README has no separate hardware-scope sentence. Retain exact LICENSE/README; embedded stock KiCad content exception only, models unclosed.', 'sha256': '186a7d811ca4bf09afa7c286ce0773deb0d8ca4a6404a530658ee664e69d23e0', 'source_path': 'PushButtonLed.kicad_pro'}, {'bytes': 36854, 'commit': '29c46b7c03d2afd9fe3a58fe2070309b12f94b42', 'destination': 'push-button-led/PushButtonLed.kicad_sch', 'git_blob_sha1': '44bae1475b69f202d8a4c06f32038faea6382578', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/gurusaeth12/push-button-led-kicad/29c46b7c03d2afd9fe3a58fe2070309b12f94b42/PushButtonLed.kicad_sch', 'repository': 'gurusaeth12/push-button-led-kicad', 'rights_basis': 'Root MIT notice by Gurusaeth covers supplied editable hardware/documentation; README has no separate hardware-scope sentence. Retain exact LICENSE/README; embedded stock KiCad content exception only, models unclosed.', 'sha256': '2fe34f261ee78cf81bc9e7751d9e1b2ca6416944d830d4f5ac50fe40409a0877', 'source_path': 'PushButtonLed.kicad_sch'}, {'bytes': 3064, 'commit': '29c46b7c03d2afd9fe3a58fe2070309b12f94b42', 'destination': 'push-button-led/README.md', 'git_blob_sha1': '4c7fbdc5e95d2449b32e7155e511bfeec6ac98c3', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/gurusaeth12/push-button-led-kicad/29c46b7c03d2afd9fe3a58fe2070309b12f94b42/README.md', 'repository': 'gurusaeth12/push-button-led-kicad', 'rights_basis': 'Root MIT notice by Gurusaeth covers supplied editable hardware/documentation; README has no separate hardware-scope sentence. Retain exact LICENSE/README; embedded stock KiCad content exception only, models unclosed.', 'sha256': 'db7a1e9afa9c288e0e5474637ab3a9d2a2abe07555f6157c06488337cf426de4', 'source_path': 'README.md'})
SECONDS=300
NETWORK_BYTES=161076
OUTPUT_BYTES=2*1024**2
MATERIAL=('scripts/fetch_led_demo.py','experiments/licensed_acquisition_v1/fetch.py','autorouter/floor_route.py','autorouter/handoff.py','autorouter/pipeline.py')

def destination(root,name):
    root=Path(root).absolute();relative=shared.safe(name)
    if len(relative.parts)!=2 or relative.parts[0]!='.data' or not re.fullmatch(r'led-demo-[a-z0-9][a-z0-9-]{0,47}',relative.parts[1]):
        raise ValueError('fresh .data/led-demo-NAME directory required')
    return shared.contained(root,root/relative)

def verify_project(path):
    """Read-only exact five-file source verifier, independent of research cache."""
    path=Path(path).absolute();shared.contained(path,path)
    expected={r['source_path']:{'bytes':r['bytes'],'sha256':r['sha256']} for r in ROWS}
    before=shared.inventory(path,cap=OUTPUT_BYTES)
    if before['files']!=expected or before['directories']!=[]:raise ValueError('exact five original LED project files required')
    for row in ROWS:shared.payload(row,shared.bounded(path/shared.safe(row['source_path'])))
    shared.inventory(path,before,cap=OUTPUT_BYTES)
    return {'schema':1,'verified':True,'project':str(path),'repository':ROWS[0]['repository'],
        'source_commit':ROWS[0]['commit'],'file_count':5,'bytes':161071,'files':expected,'native_accepted':False}

class OwnedFile:
    """Guard shared transport's delayed open against directory replacement."""
    def __init__(self,path,owned):self.path=path;self.owned=owned
    def open(self,*args,**kwargs):self.owned();return self.path.open(*args,**kwargs)
    def exists(self):self.owned();return self.path.exists()

def fetch_demo(name,*,fetch=False,root=ROOT,transport=shared.fetch_one,started=None,cpu_started=None):
    started=time.monotonic() if started is None else started;cpu_started=cpu() if cpu_started is None else cpu_started
    root=Path(root).absolute();out=destination(root,name);rows=copy.deepcopy(ROWS)
    if out.exists():raise ValueError('destination already exists; preserve earlier attempts')
    if fetch is not True:
        return {'schema':1,'action':'plan_only','destination':str(out),'source_commit':rows[0]['commit'],
            'planned_files':5,'planned_bytes':161071,'network_requests':0,'native_accepted':False,
            'command':'scripts/fetch_led_demo.py --fetch --output '+name}
    def material():return {n:shared.sha(shared.bounded(shared.contained(root,root/n))) for n in MATERIAL}
    witness=material();owner={};project_owner={};completed={};requests=[]
    def owned():
        h.owned_destination(owner);h.owned_destination(project_owner);return out
    def remaining():
        left=min(SECONDS-(time.monotonic()-started),SECONDS-(cpu()-cpu_started))
        if left<=0:raise TimeoutError('whole LED demo acquisition wall/CPU budget exhausted')
        return left
    shared.contained(root,out.parent);out.parent.mkdir(exist_ok=True);shared.contained(root,out.parent);out.mkdir();h.capture_destination(owner,out);project=out/'project';project.mkdir();h.capture_destination(project_owner,project)
    record={'schema':1,'kind':'fixed_public_led_source_acquisition','status':'running','accepted':False,
        'native_accepted':False,'physical_electrical_validation':False,'routing_support':'unqualified',
        'destination':str(out),'project':str(project),'repository':rows[0]['repository'],'source_commit':rows[0]['commit'],
        'source_profile':'licensed_acquisition_v7 fixed five-file public LED selection',
        'runtime_sha256':witness,'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,
        'max_requests':5,'network_byte_cap':NETWORK_BYTES,'output_byte_cap':OUTPUT_BYTES,
        'planned_files':5,'planned_bytes':161071,'requests':requests,'files':[],
        'new_network_requests':0,'received_bytes':0,'engine_jobs':0,'native_jobs':0,'models_downloaded':0,
        'independent_ancestry_established':False,'split':'development-exposed',
        'source_files_exact':False,'original_source_constraints_modified':False,
        'warnings':['Small seven-component support/control; no broad routing superiority.',
          'Copy of the same selected LED source, not an additional independent circuit/family.',
          'Original native loading/DRC/complete schematic parity and electrical function are unverified.',
          'Creator makes no fabrication or physical testing claim.',
          'Root MIT/README retained; README gives no separate hardware-license sentence.',
          'Five unique stock-model references remain unclosed; no models/libraries/firmware downloaded.',
          'Original missing_tuning_profile warning and track_on_post_machined_layer error remain unchanged.'],
        'accounting':'Controller clock begins before project imports for CLI. Stored wall/fullCPU sample precedes final publication; final cap covers publication/readback. No speedup or routing-quality claim.'}
    def scan():return shared.inventory(owned(),cap=OUTPUT_BYTES)
    def stable():
        owned();remaining()
        if material()!=witness:raise ValueError('acquisition implementation changed during execution')
        actual=scan()['files'];allowed={'project/'+r['source_path'] for r in requests}|{'result.json','result.json.partial'}
        if record['status'] in {'invalidated','failed','cancelled'}:
            allowed|={n for n in actual if re.fullmatch(r'(?:invalidated-result|interrupted-result)-[0-9a-f]{32}\.json',n)}
        if set(actual)-allowed:raise ValueError('unexpected output member')
        for n,info in completed.items():
            if actual.get(n)!=info:raise ValueError('completed source file changed: '+n)
        if record['status']=='acquired_unqualified':
            if len(completed)!=5:raise ValueError('complete source population required')
            verify_project(project)
        remaining();owned()
    def account():
        owned();actual=scan();record.update(wall_seconds=time.monotonic()-started,total_cpu_seconds=cpu()-cpu_started,output_bytes=actual['bytes'],
          new_network_requests=len(requests),received_bytes=sum(x.get('received_bytes',0) for x in requests))
        record['source_files_exact']=len(completed)==5 and all(actual['files'].get(n)==info for n,info in completed.items())
        record['within_budget']=record['wall_seconds']<=SECONDS and record['total_cpu_seconds']<=SECONDS and actual['bytes']<=OUTPUT_BYTES and len(requests)<=5 and record['received_bytes']<=NETWORK_BYTES
        if not record['within_budget'] or record['status']=='acquired_unqualified' and not record['source_files_exact']:record.update(status='failed',accepted=False)
    try:
        stable()
        for index,row in enumerate(rows):
            stable();req={'index':index,'source_path':row['source_path']};requests.append(req)
            allowance=NETWORK_BYTES-sum(r.get('received_bytes',0) for r in requests)
            raw=transport(row,req,OwnedFile(project/row['source_path'],owned),allowance,remaining)
            owned();remaining()
            if sum(r.get('received_bytes',0) for r in requests)>NETWORK_BYTES:raise ValueError('network byte cap exceeded')
            info=shared.payload(row,raw)
            if shared.bounded(project/row['source_path'])!=raw or req.get('response_sha256')!=shared.sha(raw):raise ValueError('response artifact/returned payload differ')
            completed['project/'+row['source_path']]=info;record['files'].append({**row,**info});stable()
        record['status']='acquired_unqualified'
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',first_failure=type(exc).__name__+': '+str(exc))
    publication.publish(out,record,stable,account,remaining,owned=owned)
    try:
        owned();remaining();stable()
        if publication.canonical(publication.read_json(out/'result.json'))!=publication.canonical(record):raise ValueError('final acquisition receipt differs')
        remaining();owned();return record
    except (Exception,KeyboardInterrupt) as exc:
        record.setdefault('first_failure',type(exc).__name__+': '+str(exc));record.update(status='invalidated',accepted=False,source_files_exact=False)
        publication.publish(out,record,stable,account,remaining,owned=owned)
        raise

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--fetch',action='store_true');parser.add_argument('--output',default='.data/led-demo-001');args=parser.parse_args()
    try:
        with shared.cancellation(),shared.alarm(SECONDS):record=fetch_demo(args.output,fetch=args.fetch,started=START,cpu_started=CPU_START)
    except (Exception,KeyboardInterrupt) as exc:
        print(json.dumps({'status':'failed','reason':type(exc).__name__+': '+str(exc),'accepted':False}));return 2
    print(json.dumps({k:record[k] for k in ('action','status','destination','project','planned_files','planned_bytes','new_network_requests','received_bytes','wall_seconds','total_cpu_seconds','source_files_exact','within_budget') if k in record}));return 0 if record.get('action')=='plan_only' or record.get('status')=='acquired_unqualified' and record.get('within_budget') and record.get('source_files_exact') else 2
if __name__=='__main__':raise SystemExit(main())
