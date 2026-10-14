"""Fetch five pinned public LED design files into a fresh local demo directory."""
import time,resource
START=time.monotonic()
def cpu():
    own=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime
CPU_START=cpu()
import argparse,copy,json,re,sys,os,stat
from contextlib import contextmanager
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
ARC_MATERIAL=('experiments/placement_handoff_native_v1/driver.py','experiments/placement_production_controls_v1/driver.py','autorouter/placement_clearance.py')

ARC_PROFILE={'schema': 1, 'profile_id': 'arcdice', 'project_id': 'arcdice', 'repository': 'VorosEgyes/ArcDice', 'commit': '5908d99db1ef98b5996b380c75e5aee8bb8caaa6', 'rows': [{'source_path': 'LICENSE', 'bytes': 1067, 'sha256': '13aa5751cc47416650ad3c976d1c001f32ca3b3d49caac777ae66e819a437298', 'git_blob_sha1': '9d4599da9dcec69bb6e4c6cdc867aacbfbd77cdd', 'repository': 'VorosEgyes/ArcDice', 'commit': '5908d99db1ef98b5996b380c75e5aee8bb8caaa6', 'mode': '100644', 'destination': 'arcdice/LICENSE', 'raw_url': 'https://raw.githubusercontent.com/VorosEgyes/ArcDice/5908d99db1ef98b5996b380c75e5aee8bb8caaa6/LICENSE', 'rights_basis': 'Root MIT notice, Miklos Mod 2024, and exact README retained. README declares MIT but has no separate hardware-scope sentence. Embedded MyFootprints:TP4056-Module origin and optional model rights/closure remain unqualified; no raw board/assets publication or models/libraries/firmware download.'}, {'source_path': 'README.md', 'bytes': 2930, 'sha256': '876a106e288ec606cf29239d6129d07b79a134005769ba50ef0d450622c1751b', 'git_blob_sha1': '09720df73a14f8f037486dc49d815ade7312083f', 'repository': 'VorosEgyes/ArcDice', 'commit': '5908d99db1ef98b5996b380c75e5aee8bb8caaa6', 'mode': '100644', 'destination': 'arcdice/README.md', 'raw_url': 'https://raw.githubusercontent.com/VorosEgyes/ArcDice/5908d99db1ef98b5996b380c75e5aee8bb8caaa6/README.md', 'rights_basis': 'Root MIT notice, Miklos Mod 2024, and exact README retained. README declares MIT but has no separate hardware-scope sentence. Embedded MyFootprints:TP4056-Module origin and optional model rights/closure remain unqualified; no raw board/assets publication or models/libraries/firmware download.'}, {'source_path': 'hardware/ArcDice.kicad_pcb', 'bytes': 488060, 'sha256': '098e90725279e698f61d7f4a5f0281202ba32f655b9c430047c019783a60bf96', 'git_blob_sha1': '4efafcc2ce836ba6414e48197c305ac6fe458aa1', 'repository': 'VorosEgyes/ArcDice', 'commit': '5908d99db1ef98b5996b380c75e5aee8bb8caaa6', 'mode': '100644', 'destination': 'arcdice/hardware/ArcDice.kicad_pcb', 'raw_url': 'https://raw.githubusercontent.com/VorosEgyes/ArcDice/5908d99db1ef98b5996b380c75e5aee8bb8caaa6/hardware/ArcDice.kicad_pcb', 'rights_basis': 'Root MIT notice, Miklos Mod 2024, and exact README retained. README declares MIT but has no separate hardware-scope sentence. Embedded MyFootprints:TP4056-Module origin and optional model rights/closure remain unqualified; no raw board/assets publication or models/libraries/firmware download.'}, {'source_path': 'hardware/ArcDice.kicad_pro', 'bytes': 17925, 'sha256': 'be12f193331f3091ef31b9df28dc968119be56269adddcd5b2ed2921523223f6', 'git_blob_sha1': '53d28b286d88e0a1919bee83b70b2afa3f71f7ff', 'repository': 'VorosEgyes/ArcDice', 'commit': '5908d99db1ef98b5996b380c75e5aee8bb8caaa6', 'mode': '100644', 'destination': 'arcdice/hardware/ArcDice.kicad_pro', 'raw_url': 'https://raw.githubusercontent.com/VorosEgyes/ArcDice/5908d99db1ef98b5996b380c75e5aee8bb8caaa6/hardware/ArcDice.kicad_pro', 'rights_basis': 'Root MIT notice, Miklos Mod 2024, and exact README retained. README declares MIT but has no separate hardware-scope sentence. Embedded MyFootprints:TP4056-Module origin and optional model rights/closure remain unqualified; no raw board/assets publication or models/libraries/firmware download.'}, {'source_path': 'hardware/ArcDice.kicad_sch', 'bytes': 85359, 'sha256': '388bb0410c3372c2331c84b44ba8a45e10c4b34206a3b28b65cb90057129e4de', 'git_blob_sha1': 'aa3407c4d469eac8323872f13dcec2d980ceb7b3', 'repository': 'VorosEgyes/ArcDice', 'commit': '5908d99db1ef98b5996b380c75e5aee8bb8caaa6', 'mode': '100644', 'destination': 'arcdice/hardware/ArcDice.kicad_sch', 'raw_url': 'https://raw.githubusercontent.com/VorosEgyes/ArcDice/5908d99db1ef98b5996b380c75e5aee8bb8caaa6/hardware/ArcDice.kicad_sch', 'rights_basis': 'Root MIT notice, Miklos Mod 2024, and exact README retained. README declares MIT but has no separate hardware-scope sentence. Embedded MyFootprints:TP4056-Module origin and optional model rights/closure remain unqualified; no raw board/assets publication or models/libraries/firmware download.'}], 'directories': ['hardware'], 'board_path': 'hardware/ArcDice.kicad_pcb', 'output_prefix': 'arcdice-demo-', 'default_output': '.data/arcdice-demo-001', 'source_subdirectory': 'project', 'receipt_path': 'result.json', 'file_count': 5, 'bytes': 595341, 'max_requests': 5, 'network_byte_cap': 595346, 'max_single_response_bytes': 488061, 'wall_budget_seconds': 300, 'cpu_budget_seconds': 300, 'request_wall_seconds': 30, 'output_byte_cap': 2097152, 'source_entries_cap': 6, 'rights': 'Root MIT notice, Miklos Mod 2024, and exact README retained. README declares MIT but has no separate hardware-scope sentence. Embedded MyFootprints:TP4056-Module origin and optional model rights/closure remain unqualified; no raw board/assets publication or models/libraries/firmware download.', 'native_packet_notice_copies': {'hardware/_licenses/creator/LICENSE': 'LICENSE', 'hardware/_licenses/creator/README.md': 'README.md'}, 'native_packet_files': 7, 'native_packet_bytes': 599338, 'development_exposed': True, 'independent_ancestry_established': False, 'native_validation_performed_by_fetch': False, 'raw_assets_public': False, 'warnings': ['Same already exposed ArcDice source, not an additional independent circuit/family.', 'Fetch performs no native routing, schematic, electrical or physical qualification.', 'Root MIT/README retained; README has no separate hardware-scope sentence.', 'MyFootprints:TP4056-Module origin/local library and eight optional models (two absolute paths) remain unclosed.', 'No scripts/firmware/models/libraries/images/engines downloaded; original Source bytes/hierarchy never normalized.']}

def fixed_profile(profile_id='led'):
    if profile_id=='arcdice':return copy.deepcopy(ARC_PROFILE)
    if profile_id!='led':raise ValueError('unknown fixed public source profile')
    return {'profile_id':'led','rows':copy.deepcopy(ROWS),'directories':[],'bytes':161071,
            'network_byte_cap':NETWORK_BYTES,'output_prefix':'led-demo-','default_output':'.data/led-demo-001',
            'native_packet_notice_copies':{},'native_packet_files':0,'native_packet_bytes':0}

def destination(root,name,*,profile_id='led'):
    root=Path(root).absolute();relative=shared.safe(name);prefix=fixed_profile(profile_id)['output_prefix']
    if len(relative.parts)!=2 or relative.parts[0]!='.data' or not re.fullmatch(re.escape(prefix)+r'[a-z0-9][a-z0-9-]{0,47}',relative.parts[1]):
        raise ValueError('fresh .data/'+prefix+'NAME directory required')
    return shared.contained(root,root/relative)

def verify_project(path,*,profile_id='led',native_packet=False):
    """Read-only fixed original source verifier, independent of research cache."""
    cfg=fixed_profile(profile_id)
    if type(native_packet) is not bool or native_packet and profile_id!='arcdice':raise ValueError('unsupported notice-packet request')
    path=Path(path).absolute();shared.contained(path,path)
    rows=cfg['rows'];expected={r['source_path']:{'bytes':r['bytes'],'sha256':r['sha256']} for r in rows};directories=list(cfg['directories'])
    copies=cfg['native_packet_notice_copies'] if native_packet else {}
    for name,origin in copies.items():expected[name]=dict(expected[origin])
    if copies:directories+=['hardware/_licenses','hardware/_licenses/creator']
    before=shared.inventory(path,cap=OUTPUT_BYTES)
    if before['files']!=expected or before['directories']!=directories:raise ValueError('exact five original LED project files required' if profile_id=='led' else 'exact fixed original source/notice project required')
    for row in rows:shared.payload(row,shared.bounded(path/shared.safe(row['source_path'])))
    for name,origin in copies.items():
        row=next(r for r in rows if r['source_path']==origin);shared.payload(row,shared.bounded(path/shared.safe(name)))
    shared.inventory(path,before,cap=OUTPUT_BYTES)
    return {'schema':1,'verified':True,'project':str(path),'repository':rows[0]['repository'],
        'source_commit':rows[0]['commit'],'file_count':len(expected),'bytes':sum(x['bytes'] for x in expected.values()),
        'files':expected,'native_accepted':False}

class OwnedFile:
    """Guard delayed exclusive transport creation with an owned parent descriptor."""
    def __init__(self,path,owned,directory_fd):self.path=path;self.owned=owned;self.directory_fd=directory_fd
    @contextmanager
    def open(self,*args,**kwargs):
        if args!=('xb',) or kwargs:raise ValueError('exclusive binary response creation required')
        self.owned();fd=os.open(self.path.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|getattr(os,'O_CLOEXEC',0),0o600,dir_fd=self.directory_fd)
        try:
            self.owned();opened=os.fstat(fd)
            if not stat.S_ISREG(opened.st_mode):raise ValueError('regular response file required')
            with os.fdopen(fd,'wb',closefd=False) as stream:
                yield stream;stream.flush();self.owned()
            named=os.stat(self.path.name,dir_fd=self.directory_fd,follow_symlinks=False)
            if (named.st_dev,named.st_ino)!=(opened.st_dev,opened.st_ino):raise ValueError('response file replaced')
        finally:os.close(fd)
    def exists(self):
        self.owned()
        try:os.stat(self.path.name,dir_fd=self.directory_fd,follow_symlinks=False);return True
        except FileNotFoundError:return False

def fetch_demo(name,*,profile_id='led',fetch=False,root=ROOT,transport=shared.fetch_one,started=None,cpu_started=None):
    started=time.monotonic() if started is None else started;cpu_started=cpu() if cpu_started is None else cpu_started
    cfg=fixed_profile(profile_id);root=Path(root).absolute();out=destination(root,name,profile_id=profile_id);rows=cfg['rows'];network_cap=cfg['network_byte_cap'];planned=cfg['bytes'];nested=profile_id=='arcdice'
    if out.exists():raise ValueError('destination already exists; preserve earlier attempts')
    if fetch is not True:
        return {'schema':1,'action':'plan_only','destination':str(out),'source_commit':rows[0]['commit'],
            'planned_files':5,'planned_bytes':planned,'network_requests':0,'native_accepted':False,
            'command':'scripts/fetch_led_demo.py --project '+profile_id+' --fetch --output '+name}
    extra=ARC_MATERIAL if nested else ()
    def material():return {n:shared.sha(shared.bounded(shared.contained(root,root/n))) for n in (*MATERIAL,*extra)}
    witness=material();owner={};project_owner={};native_owner={};response_owner={};completed={};requests=[];received={};raw_fd=None
    def owned():
        h.owned_destination(owner)
        for scope in (project_owner,native_owner,response_owner):
            if scope.get('created'):h.owned_destination(scope)
        if raw_fd is not None:
            identity=os.fstat(raw_fd);scope=response_owner if nested else project_owner
            if (identity.st_dev,identity.st_ino)!=scope['directory_identity']:raise ValueError('owned response parent descriptor differs')
        return out
    def remaining():
        left=min(SECONDS-(time.monotonic()-started),SECONDS-(cpu()-cpu_started))
        if left<=0:raise TimeoutError('whole LED demo acquisition wall/CPU budget exhausted')
        return left
    shared.contained(root,out.parent);out.parent.mkdir(exist_ok=True);shared.contained(root,out.parent);out.mkdir();h.capture_destination(owner,out);project=out/'project'
    raw_root=out/'responses' if nested else project;raw_root.mkdir();h.capture_destination(response_owner if nested else project_owner,raw_root)
    raw_fd=os.open(raw_root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|getattr(os,'O_CLOEXEC',0))
    try:owned()
    except BaseException:os.close(raw_fd);raw_fd=None;raise
    record={'schema':1,'kind':'fixed_public_arcdice_source_acquisition' if nested else 'fixed_public_led_source_acquisition','status':'running','accepted':False,
        'native_accepted':False,'physical_electrical_validation':False,'routing_support':'unqualified',
        'destination':str(out),'project':str(project),'repository':rows[0]['repository'],'source_commit':rows[0]['commit'],
        'source_profile':'fixed five-file public ArcDice selection' if nested else 'licensed_acquisition_v7 fixed five-file public LED selection',
        'runtime_sha256':witness,'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,
        'max_requests':5,'network_byte_cap':network_cap,'output_byte_cap':OUTPUT_BYTES,
        'planned_files':5,'planned_bytes':planned,'requests':requests,'files':[],
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
    if nested:record.update(warnings=cfg['warnings'],native_project=str(out/'native-project'),native_packet_prepared=False,native_packet_hashes=None)
    def exact_source():
        if nested:
            if not project_owner.get('created') or not native_owner.get('created'):return False
            verify_project(project,profile_id=profile_id);verified=verify_project(out/'native-project',profile_id=profile_id,native_packet=True)
            if verified['files']!=record['native_packet_hashes']:raise ValueError('native notice packet differs')
            return True
        return len(completed)==5
    def scan():return shared.inventory(owned(),cap=OUTPUT_BYTES)
    def stable():
        owned();remaining()
        if material()!=witness:raise ValueError('acquisition implementation changed during execution')
        actual=scan()['files'];allowed={r['artifact'] for r in requests}|set(completed)|{'result.json','result.json.partial'}
        if nested:
            # Preserve legitimate partial owned copies on failure without claiming completeness.
            allowed|={'project/'+r['source_path'] for r in rows}|{'native-project/'+r['source_path'] for r in rows}|{'native-project/'+n for n in cfg['native_packet_notice_copies']}
        if record['status'] in {'invalidated','failed','cancelled'}:
            allowed|={n for n in actual if re.fullmatch(r'(?:invalidated-result|interrupted-result)-[0-9a-f]{32}\.json',n)}
        if set(actual)-allowed:raise ValueError('unexpected output member')
        for n,info in completed.items():
            if actual.get(n)!=info:raise ValueError('completed source file changed: '+n)
        if record['status']=='acquired_unqualified':
            if not exact_source():raise ValueError('complete source population required')
            verify_project(project,profile_id=profile_id)
        remaining();owned()
    def account():
        owned();actual=scan();record.update(wall_seconds=time.monotonic()-started,total_cpu_seconds=cpu()-cpu_started,output_bytes=actual['bytes'],
          new_network_requests=len(requests),received_bytes=sum(x.get('received_bytes',0) for x in requests))
        record['source_files_exact']=exact_source() and all(actual['files'].get(n)==info for n,info in completed.items())
        record['within_budget']=record['wall_seconds']<=SECONDS and record['total_cpu_seconds']<=SECONDS and actual['bytes']<=OUTPUT_BYTES and len(requests)<=5 and record['received_bytes']<=network_cap
        if not record['within_budget'] or record['status']=='acquired_unqualified' and not record['source_files_exact']:record.update(status='failed',accepted=False)
    try:
        stable()
        for index,row in enumerate(rows):
            stable();artifact=('responses/'+str(index+1).zfill(2)+'.payload') if nested else 'project/'+row['source_path'];req={'index':index,'source_path':row['source_path'],'artifact':artifact};requests.append(req)
            allowance=network_cap-sum(r.get('received_bytes',0) for r in requests)
            raw=transport(row,req,OwnedFile(out/artifact,owned,raw_fd),allowance,remaining)
            owned();remaining()
            if sum(r.get('received_bytes',0) for r in requests)>network_cap:raise ValueError('network byte cap exceeded')
            info=shared.payload(row,raw)
            if shared.bounded(out/artifact)!=raw or req.get('response_sha256')!=shared.sha(raw):raise ValueError('response artifact/returned payload differ')
            completed[artifact]=info;received[row['source_path']]=raw;record['files'].append({**row,**info});stable()
        if nested:
            from experiments.placement_handoff_native_v1.driver import copy_bytes
            owned();project_owner.update(copy_bytes(received,project,expected_parent_owner=owner));owned()
            packet=dict(received)
            for name,origin in cfg['native_packet_notice_copies'].items():packet[name]=received[origin]
            native_owner.update(copy_bytes(packet,out/'native-project',expected_parent_owner=owner));owned()
            for prefix,values in [('project',received),('native-project',packet)]:
                for name,raw in values.items():completed[prefix+'/'+name]={'bytes':len(raw),'sha256':shared.sha(raw)}
            record.update(native_packet_prepared=True,native_packet_hashes=verify_project(out/'native-project',profile_id=profile_id,native_packet=True)['files'])
        record['status']='acquired_unqualified'
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',first_failure=type(exc).__name__+': '+str(exc))
    finally:
        if raw_fd is not None:os.close(raw_fd);raw_fd=None
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
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--fetch',action='store_true');parser.add_argument('--project',choices=('led','arcdice'),default='led');parser.add_argument('--output');args=parser.parse_args();args.output=args.output or fixed_profile(args.project)['default_output']
    try:
        with shared.cancellation(),shared.alarm(SECONDS):record=fetch_demo(args.output,profile_id=args.project,fetch=args.fetch,started=START,cpu_started=CPU_START)
    except (Exception,KeyboardInterrupt) as exc:
        print(json.dumps({'status':'failed','reason':type(exc).__name__+': '+str(exc),'accepted':False}));return 2
    print(json.dumps({k:record[k] for k in ('action','status','destination','project','planned_files','planned_bytes','new_network_requests','received_bytes','wall_seconds','total_cpu_seconds','source_files_exact','within_budget') if k in record}));return 0 if record.get('action')=='plan_only' or record.get('status')=='acquired_unqualified' and record.get('within_budget') and record.get('source_files_exact') else 2
if __name__=='__main__':raise SystemExit(main())
