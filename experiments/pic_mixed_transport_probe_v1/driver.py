"""ROOT-only mixed-class prerequisite. Reuses retained bounded IO/publication and native mapping."""
import argparse,fcntl,os,subprocess,sys,time
from contextlib import contextmanager
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'autorouter/runner.py').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'experiments/custom_pad_area_probe_v1'))
from experiments.custom_pad_area_probe_v1 import driver as base
sys.path.insert(0,str(ROOT/'experiments/pic_custom_observer_v1'))
from experiments.pic_custom_observer_v1 import driver as original,mapping
from autorouter import runner,placement_clearance as io,sexpr as sx,floor_route as floor
sys.path.insert(0,str(HERE))
import transport
from experiments.pic_mixed_transport_probe_v1.worker import OBSERVATION_SCOPE,observation_reference

SECONDS=180.0;LIMIT=64*1024**2
HELPERS=('driver.py','worker.py','transport.py','MixedClassProbe.java','test_draft.py','PROTOCOL.json','README.md','LOCAL_CLEARANCE_PROTOCOL.json','test_local_transport.py','SES_PROTOCOL.json','ses_checks.py','ses_native.py','test_ses.py','SES_NATIVE_PROTOCOL.json','SES_FINISH_PROTOCOL.json','SELECTIVE_PROTOCOL.json','SelectiveAreaProbe.java','selective.py','test_selective.py','ROUTING_PROTOCOL.json','SelectiveRoutingProbe.java','routing_input.py','test_routing_input.py','routing_checks.py','routing_native.py','test_routing.py','ROUTING_NATIVE_PROTOCOL.json','ADAPTER_PROTOCOL.json','routing_adapter.py','test_routing_adapter.py','ExactPointWitness.java')
REUSE=('experiments/custom_pad_area_probe_v1/driver.py','experiments/custom_pad_area_probe_v1/derive.py',
    'experiments/custom_pad_area_probe_v1/checks.py','experiments/custom_pad_area_probe_v1/AreaContactProbe.java',
    'experiments/pic_custom_observer_v1/driver.py','experiments/pic_custom_observer_v1/worker.py','experiments/pic_custom_observer_v1/mapping.py')

def inventory(path):return io.inventory(path,max_bytes=LIMIT,max_files=2000,max_entries=4000)
def source_paths():return [HERE/n for n in HELPERS]+[ROOT/n for n in REUSE]+list(sorted((ROOT/'autorouter').glob('*.py')))+[ROOT/'toolchain.lock.json',ROOT/'data/sources.json']
def runtime(protocol):
    cached=None;cached_ses=None;cached_positive=None;cached_local=None;cached_selective=None;cached_routing=None
    if protocol.get('mode') in ('local250','local250-ses','local250-ses-cached','local250-ses-finish','local250-selective','local250-routing','local250-routing-native','local250-routing-adapter'):
        if protocol.get('reuse_native')!='.runs/pic-mixed-transport-probe-005':raise ValueError('fixed cached-native source required')
        # The larger cached scan precedes the protected current-material reads.
        # Late changes during that scan must appear in the returned witness.
        cached=inventory(ROOT/protocol['reuse_native'])
    if protocol.get('mode') in ('local250-ses-cached','local250-ses-finish'):
        if protocol.get('reuse_ses')!='.runs/pic-custom-ses-roundtrip-001':raise ValueError('fixed cached SES source required')
        cached_ses=inventory(ROOT/protocol['reuse_ses'])
    if protocol.get('mode')=='local250-ses-finish':
        if protocol.get('reuse_positive')!='.runs/pic-custom-ses-native-001':raise ValueError('fixed cached positive source required')
        cached_positive=inventory(ROOT/protocol['reuse_positive'])
    if protocol.get('mode') in ('local250-selective','local250-routing','local250-routing-native','local250-routing-adapter'):
        if protocol.get('reuse_local')!='.runs/pic-local-clearance-transport-001':raise ValueError('fixed local basis required')
        cached_local=inventory(ROOT/protocol['reuse_local'])
    if protocol.get('mode') in ('local250-routing','local250-routing-native','local250-routing-adapter'):
        if protocol.get('reuse_selective')!='.runs/pic-selective-area-observation-002':raise ValueError('fixed selective prerequisite required')
        cached_selective=inventory(ROOT/protocol['reuse_selective'])
    if protocol.get('mode')=='local250-routing-native':
        if protocol.get('reuse_routing')!='.runs/pic-selective-routing-001':raise ValueError('fixed failed routing source required')
        cached_routing=inventory(ROOT/protocol['reuse_routing'])
    git=base.head_witness()
    tools={name:base.content(Path(row['path']) if Path(row['path']).is_absolute() else ROOT/row['path'],row['bytes'],digest=True) for name,row in protocol['tools'].items()}
    sources={str(p.relative_to(ROOT)):base.content(p,2*1024**2,digest=True) for p in source_paths()}
    basis={name:base.content(ROOT/name,row['bytes'],digest=True) for name,row in protocol['basis'].items()}
    original_hashes,total=original.source_binding()
    result={'git':git,'tools':tools,'sources':sources,'basis':basis,'original':original_hashes,'original_bytes':total}
    if cached is not None:result['cached_native_inventory']=cached
    if cached_ses is not None:result['cached_ses_inventory']=cached_ses
    if cached_positive is not None:result['cached_positive_inventory']=cached_positive
    if cached_local is not None:result['cached_local_inventory']=cached_local
    if cached_selective is not None:result['cached_selective_inventory']=cached_selective
    if cached_routing is not None:result['cached_routing_inventory']=cached_routing
    return result

def verify_clearance_rows(observed,context,notes):
    if type(observed) is not list or len(observed)!=247:raise ValueError('clearance terminal census differs')
    rows={r['uuid']:r for r in observed}
    if len(rows)!=247 or set(rows)!=set(notes['source_pads_identity']):raise ValueError('clearance terminal census differs')
    nets={r['name']:r for r in context['nets']}
    if len(nets)!=len(context['nets']):raise ValueError('duplicate native context net')
    for uid,row in rows.items():
        if any(row[k]!=notes['source_pads_identity'][uid][k] for k in ('reference','number','net')):raise ValueError('clearance terminal identity differs')
        metadata=row.get('class_metadata',{})
        if (metadata.get('source')!='BOARD.GetNetsByName -> NETINFO_ITEM.GetNetClassSlow'
                or metadata.get('meaning')!='Net metadata class preference; not a pad-local, own-clearance, or pairwise rule result.'):
            raise ValueError('clearance class metadata origin differs')
        if row['net']:
            net=nets.get(row['net'])
            if (net is None or metadata.get('status')!='observed' or type(row.get('netcode')) is not int
                    or type(row.get('class_clearance_nm')) is not int or type(row.get('netclass')) is not str
                    or row['netcode']!=net['netcode'] or row['netclass']!=net['class']
                    or row['class_clearance_nm']!=net['clearance_nm']):
                raise ValueError('assigned class metadata differs from same-board context')
        elif (metadata.get('status')!='unavailable_netless' or type(row.get('netcode')) is not int or row['netcode']!=0
                or row.get('netclass') is not None or row.get('class_clearance_nm') is not None):
            raise ValueError('netless class metadata must remain unavailable')

def verify_load_observations(custom,saved,context,notes):
    observations=[]
    for stage in ('before_export','after_export'):
        clear=saved[stage]
        reference=custom['observation_'+stage]['clearance_observation']
        if (set(clear)!={'scope','initialization_qualified','pairwise_rules_qualified','drc_report_executed','api_types','rows'}
                or clear['scope']!=OBSERVATION_SCOPE or any(clear[k] is not False for k in ('initialization_qualified','pairwise_rules_qualified','drc_report_executed'))
                or type(clear['api_types']) is not list or reference!=observation_reference(clear)
                or any(reference[k] is not False for k in ('initialization_qualified','pairwise_rules_qualified','drc_report_executed'))):
            raise ValueError('load-only observation scope/binding differs')
        verify_clearance_rows(clear['rows'],context,notes);observations.append(clear)
    if set(saved)!={'before_export','after_export'} or observations[0]!=observations[1]:
        raise ValueError('export changed clearance observations')
    return observations[0]

def verify_native(out,source_hashes,notes):
    context=base.decode(base.content(out/'context.json',2*1024**2));custom=base.decode(base.content(out/'custom.json',4*1024**2));raw=base.content(out/'native.dsn',1024**2)
    board=out/'observe-input'/original.SOURCE.name
    floor.context_binding(context,board,source_hashes,'export',base.sha(raw))
    for key in ('context_schema','native_version','units','mode','source','board_sha256','project_sha256','dsn_sha256','input_hashes_before','input_hashes_after'):
        if custom.get(key)!=context.get(key):raise ValueError('same-load custom/context binding differs')
    if custom.get('floor_context_sha256')!=base.sha(base.content(out/'context.json')):raise ValueError('custom context digest differs')
    mapping.floor_identity(context,notes,base.decode(base.content(board.with_suffix('.kicad_pro'))))
    rows=mapping.custom_identity(custom,context,notes)
    clear=verify_load_observations(custom,base.decode(base.content(out/'clearance-observation.json',2*1024**2)),context,notes)
    derived,expected=transport.derive(raw,context,custom,notes)
    return derived,expected,{'initialization_qualified':False,'drc_report_executed':False,'pairwise_rules_qualified':False,
        'scope':OBSERVATION_SCOPE,
        'local_optional_observations_supported':all(x['status']=='observed' for r in clear['rows'] for x in (r['pad_local'],r['footprint_local'],r['pad_override'])),
        'custom_pad_own_clearance':[{k:r[k] for k in ('uuid','net','netcode','netclass','class_clearance_nm','class_metadata','net_metadata_return_types','pad_net_return_types','own','pad_local','footprint_local','pad_override')} for r in clear['rows'] if r['uuid'] in {p['uuid'] for p in rows}]}


@contextmanager
def pending_candidate(out,path,frozen,mutable_files,capture):
    # Exactly one fresh working PCB is intentionally refilled by the shared
    # validator. Everything else remains frozen at each stage; final or failed
    # bytes are sealed when this synchronous operation exits.
    expected_path=out/'routing-native/candidate'/original.SOURCE.name
    if path!=expected_path or path.exists() or mutable_files:raise ValueError('unexpected mutable candidate path')
    relative=str(path.relative_to(out))
    if relative in frozen:raise ValueError('cannot unfreeze prior evidence')
    mutable_files.add(relative)
    try:yield
    finally:
        mutable_files.remove(relative);capture()

def experiment(out,*,started=None,cpu_started=None,local_clearance=False,ses_roundtrip=False,native_from_ses=False,finish_native=False,selective_obstacles=False,routing_probe=False,cancel_routing=False,native_from_routing=False,adapter_proposal=False):
    if HERE.relative_to(ROOT).as_posix()!='experiments/pic_mixed_transport_probe_v1':raise ValueError('promote and commit reviewed helper before execution')
    start=time.monotonic() if started is None else started;cpu0=base.cpu() if cpu_started is None else cpu_started;out=base.real(out)
    if out.parent!=ROOT/'.runs' or out.exists():raise ValueError('fresh direct .runs output required')
    if selective_obstacles and (local_clearance or ses_roundtrip or native_from_ses or finish_native):raise ValueError('selective mode cannot be combined with other modes')
    if native_from_routing and (routing_probe or cancel_routing):raise ValueError('native continuation cannot combine routing/cancel modes')
    if adapter_proposal and (routing_probe or native_from_routing or cancel_routing):raise ValueError('adapter proposal mode must stand alone')
    routing_probe=routing_probe or native_from_routing or adapter_proposal
    if routing_probe and (local_clearance or ses_roundtrip or native_from_ses or finish_native or selective_obstacles):raise ValueError('routing mode must stand alone')
    if cancel_routing and not routing_probe:raise ValueError('cancel control requires routing mode')
    native_from_ses=native_from_ses or finish_native
    ses_roundtrip=ses_roundtrip or native_from_ses
    local_clearance=local_clearance or ses_roundtrip or selective_obstacles or routing_probe
    protocol=base.decode(base.content(HERE/('ADAPTER_PROTOCOL.json' if adapter_proposal else 'ROUTING_NATIVE_PROTOCOL.json' if native_from_routing else 'ROUTING_PROTOCOL.json' if routing_probe else 'SELECTIVE_PROTOCOL.json' if selective_obstacles else 'SES_FINISH_PROTOCOL.json' if finish_native else 'SES_NATIVE_PROTOCOL.json' if native_from_ses else 'SES_PROTOCOL.json' if ses_roundtrip else 'LOCAL_CLEARANCE_PROTOCOL.json' if local_clearance else 'PROTOCOL.json')));record={'schema':1,'status':'preparing','observations_complete':False,
        'routing_accepted':False,'custom_pad_support_qualified':False,'mixed_clearance_equivalence_qualified':False,
        'routing_executed':False,'ses_executed':False,'native_process_executed':False,'import_process_executed':False,
        'steps':[],'wall_budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,
        'max_output_bytes':LIMIT,'accounting_point':'Stored totals precede final publication checks; acceptance caps include them.',
        'cpu_enforcement':'Measured self plus waited children, acceptance cap; not hard CPU preemption.'}
    def remaining():
        left=min(SECONDS-(time.monotonic()-start),SECONDS-(base.cpu()-cpu0))
        if left<=0:raise TimeoutError('shared wall/full CPU cap exceeded')
        return left
    def account():record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=base.cpu()-cpu0)
    out.mkdir();before=None;frozen={};mutable_files=set()
    def capture():
        for name,digest in inventory(out).items():
            if name in mutable_files:continue
            if name in frozen and frozen[name]!=digest:raise ValueError('completed evidence changed before capture')
            frozen[name]=digest
    def stable():
        actual=inventory(out)
        if any(actual.get(k)!=v for k,v in frozen.items()):raise ValueError('retained evidence changed')
        if before is not None and runtime(protocol)!=before:raise ValueError('source/helper/tool/API/HEAD changed')
        actual=inventory(out)
        if any(actual.get(k)!=v for k,v in frozen.items()):raise ValueError('retained evidence changed after runtime sampling')
        remaining()
    try:
        if (type(protocol['schema']) is not int or protocol['schema']!=1
                or base.canonical(protocol['limits'])!=base.canonical({'wall_seconds':180,'full_cpu_seconds':180,'output_bytes':LIMIT,'java_heap':'256m'})
                or base.canonical(protocol['cases'])!=base.canonical([False] if selective_obstacles or routing_probe else [False,True])):raise ValueError('fixed prospective protocol differs')
        if Path(sys.executable).resolve()!=Path(protocol['tools']['python']['path']):raise ValueError('invoking Python differs')
        before=runtime(protocol)
        if before['tools']!={k:{x:v[x] for x in ('bytes','sha256')} for k,v in protocol['tools'].items()} or before['basis']!=protocol['basis']:raise ValueError('pinned tools/basis differ')
        for relative,pin in before['sources'].items():
            raw=base.content(ROOT/relative,2*1024**2)
            blob=subprocess.run(['git','show',before['git']['head']+':'+relative],cwd=ROOT,capture_output=True,check=True,timeout=min(3,remaining())).stdout
            if blob!=raw or base.sha(raw)!=pin['sha256']:raise ValueError('commit exact helper/core before execution')
            target=out/'code'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        for name in ('observe-input','classes','home','tmp'): (out/name).mkdir()
        for name,digest in before['original'].items():
            raw=base.content(original.SOURCE.parent/name,2*1024**2)
            if base.sha(raw)!=digest:raise ValueError('source changed during copy')
            target=out/'observe-input'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        if inventory(out/'observe-input')!=before['original']:raise ValueError('complete input copy differs')
        base.write(out/'runtime.json',before);capture();record['runtime']=before
        notes=mapping.source_notes(sx.parse(base.content(out/'observe-input'/original.SOURCE.name).decode()),base.decode(base.content(out/'observe-input'/original.SOURCE.with_suffix('.kicad_pro').name)))
        env={'HOME':str(out/'home'),'TMPDIR':str(out/'tmp'),'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'}
        def step(name,argv,cap,*,allowed=(0,),cwd=None,env_override=None):
            stable();result=runner.run(argv,cwd=cwd or out,log=out/(name+'.log'),timeout=min(cap,remaining()),env=env_override or env,max_log_bytes=1024**2,max_workdir_bytes=LIMIT,max_group_rss_bytes=2*1024**3)
            if name=='native-observe' or name.startswith('ses-'):record['native_process_executed']=type(result.get('pid')) is int
            if name=='import':record['import_process_executed']=type(result.get('pid')) is int
            record['steps'].append({'name':name,**result});base.write(out/(name+'-process.json'),result);capture()
            if routing_probe and name=='import' and (out/'observations.json').is_file():
                partial=base.decode(base.content(out/'observations.json',16*1024**2))
                record['routing_executed']=partial.get('routing_executed') is True
                record['ses_executed']=partial.get('ses_executed') is True
            if result['status']=='cancelled':raise KeyboardInterrupt('owned worker cancelled')
            if result['status'] not in ('success','nonzero_exit') or result['exit_code'] not in allowed or result.get('cleanup_complete') is not True:raise ValueError(name+' failed; raw artifacts retained')
            stable();return result
        code=out/'code'/str(HERE.relative_to(ROOT));tools=protocol['tools']
        if local_clearance:
            if protocol.get('mode')!=('local250-routing-adapter' if adapter_proposal else 'local250-routing-native' if native_from_routing else 'local250-routing' if routing_probe else 'local250-selective' if selective_obstacles else 'local250-ses-finish' if finish_native else 'local250-ses-cached' if native_from_ses else 'local250-ses' if ses_roundtrip else 'local250'):raise ValueError('local-clearance protocol mode differs')
            cached=ROOT/protocol['reuse_native'];old=base.decode(base.content(cached/'summary.json'))
            if (old.get('status')!='failed' or old.get('error')!='ValueError: engine original class/width differs'
                    or old['runtime']['original']!=before['original']
                    or any(before['cached_native_inventory'].get(k)!=v for k,v in old['frozen_evidence'].items())
                    or inventory(cached/'observe-input')!=before['original']):raise ValueError('cached failed run/native material differs')
            derived,expected,native=verify_native(cached,before['original'],notes)
            if derived!=base.content(cached/'mixed.dsn'):raise ValueError('cached DSN changed under current derivation')
            record['local_basis']=transport.local_override_basis(base.decode(base.content(cached/'clearance-observation.json',2*1024**2)),base.decode(base.content(original.SOURCE.with_suffix('.kicad_pro'))))
            record['native_reuse']={'run':protocol['reuse_native'],'summary_sha256':base.sha(base.content(cached/'summary.json')),
                'git_head':old['runtime']['git']['head'],'original_status':old['status'],'new_native_execution':False,
                'prior_run_wall_seconds':old['wall_seconds'],'prior_run_total_cpu_seconds':old['total_cpu_seconds'],
                'scope':'Existing005 native observation/export reused; original failed checker receipt unchanged. Fresh native SES stages, if requested, are separately recorded.'}
            (out/'cached-native').mkdir()
            for name in ('context.json','custom.json','clearance-observation.json','native.dsn','summary.json'):
                (out/'cached-native'/name).write_bytes(base.content(cached/name,4*1024**2))
            capture()
        else:
            step('native-observe',[*base.SANDBOX,tools['native_python']['path'],str(code/'worker.py'),str(out/'observe-input'/original.SOURCE.name),str(out/'context.json'),str(out/'native.dsn'),str(out/'custom.json'),str(out/'clearance-observation.json')],60)
            derived,expected,native=verify_native(out,before['original'],notes)
        record['native']=native
        (out/'mixed.dsn').write_bytes(derived);base.write(out/'expectations.json',expected);capture()
        if selective_obstacles or routing_probe:
            cached=ROOT/protocol['reuse_local'];old=base.decode(base.content(cached/'summary.json'))
            if (old.get('status')!='completed' or old.get('observations_complete') is not True
                    or old['runtime']['original']!=before['original'] or any(before['tools'].get(k)!=v for k,v in old['runtime']['tools'].items())
                    or any(before['cached_local_inventory'].get(k)!=v for k,v in old['frozen_evidence'].items())
                    or inventory(cached/'observe-input')!=before['original']
                    or base.content(cached/'mixed.dsn')!=derived or base.decode(base.content(cached/'expectations.json'))!=expected
                    or [(r['name'],r['status'],r['exit_code'],r.get('cleanup_complete')) for r in old['steps']]!=[('compile','success',0,True),('import','success',0,True)]):
                raise ValueError('cached actual local basis differs')
            baseline=base.content(cached/'observations.json',16*1024**2)
            (out/'local-basis-observations.json').write_bytes(baseline)
            local_binding={'run':protocol['reuse_local'],'summary_sha256':base.sha(base.content(cached/'summary.json')),
                'git_head':old['runtime']['git']['head'],'prior_run_wall_seconds':old['wall_seconds'],
                'prior_run_total_cpu_seconds':old['total_cpu_seconds'],'scope':'Revalidated actual local250 baseline; no old JVM/native repeated. One fresh selective observation.'}
            capture()
        if routing_probe:
            from experiments.pic_mixed_transport_probe_v1 import selective,routing_input
            cached=ROOT/protocol['reuse_selective'];prior=base.decode(base.content(cached/'summary.json'))
            if (prior.get('status')!='completed' or prior.get('observations_complete') is not True
                    or prior['runtime']['original']!=before['original']
                    or any(before['tools'].get(k)!=v for k,v in prior['runtime']['tools'].items())
                    or any(before['cached_selective_inventory'].get(k)!=v for k,v in prior['frozen_evidence'].items())
                    or inventory(cached/'observe-input')!=before['original']
                    or base.content(cached/'mixed.dsn')!=derived or base.decode(base.content(cached/'expectations.json'))!=expected
                    or [(r['name'],r['status'],r['exit_code'],r.get('cleanup_complete')) for r in prior['steps']]!=[('compile','success',0,True),('import','success',0,True)]):
                raise ValueError('actual selective prerequisite binding differs')
            retained_selective=base.decode(base.content(cached/'observations.json',16*1024**2))
            selective.compare(retained_selective,expected,base.decode(baseline))
            base.write(out/'selective-basis-observations.json',retained_selective)
            context=base.decode(base.content(out/'cached-native/context.json',2*1024**2))
            unrouted,removal=routing_input.derive(derived,expected,base.content(out/'observe-input'/original.SOURCE.name),context)
            routing_input.verify(derived,expected,base.content(out/'observe-input'/original.SOURCE.name),context,unrouted,removal)
            (out/'unrouted.dsn').write_bytes(unrouted);base.write(out/'removal-ledger.json',removal)
            if adapter_proposal:
                from experiments.pic_mixed_transport_probe_v1 import routing_adapter
                stripped=unrouted;(out/'stripped-unrouted.dsn').write_bytes(stripped)
                adapted=routing_adapter.apply(out/'unrouted.dsn',context)
                unrouted=base.content(out/'unrouted.dsn')
                routing_adapter.verify(stripped,unrouted,context,adapted)
                record['routing_adapter']=adapted;base.write(out/'routing-adapter.json',adapted)
            route_expected=dict(expected,derived_dsn_sha256=base.sha(unrouted));base.write(out/'routing-expectations.json',route_expected)
            record['local_reuse']=local_binding
            record['selective_reuse']={'run':protocol['reuse_selective'],'summary_sha256':base.sha(base.content(cached/'summary.json')),
                'git_head':prior['runtime']['git']['head'],'prior_run_wall_seconds':prior['wall_seconds'],
                'prior_run_total_cpu_seconds':prior['total_cpu_seconds'],'scope':'Passing retained representation prerequisite; no repeated engine/native.'}
            capture()
        if native_from_routing:
            cached=ROOT/protocol['reuse_routing'];prior_routing=base.decode(base.content(cached/'summary.json'))
            if (prior_routing.get('status')!='failed' or prior_routing.get('error')!='ValueError: exact integer engine point required'
                    or prior_routing.get('routing_executed') is not True or prior_routing.get('ses_executed') is not True
                    or prior_routing['runtime']['original']!=before['original'] or prior_routing['runtime']['tools']!=before['tools']
                    or any(before['cached_routing_inventory'].get(k)!=v for k,v in prior_routing['frozen_evidence'].items())
                    or inventory(cached/'observe-input')!=before['original']
                    or base.content(cached/'mixed.dsn')!=derived or base.content(cached/'unrouted.dsn')!=unrouted
                    or base.decode(base.content(cached/'expectations.json'))!=expected
                    or base.decode(base.content(cached/'routing-expectations.json'))!=route_expected
                    or base.decode(base.content(cached/'removal-ledger.json'))!=removal
                    or [(r['name'],r['status'],r['exit_code'],r.get('cleanup_complete')) for r in prior_routing['steps']]!=[('compile','success',0,True),('import','success',0,True)]):
                raise ValueError('cached failed routing provenance differs')
            for name in ('MixedClassProbe.java','SelectiveAreaProbe.java','SelectiveRoutingProbe.java'):
                key=str(HERE.relative_to(ROOT)/name)
                if prior_routing['runtime']['sources'][key]!=before['sources'][key]:raise ValueError('cached executed Java source differs')
            key='experiments/custom_pad_area_probe_v1/AreaContactProbe.java'
            if prior_routing['runtime']['sources'][key]!=before['sources'][key]:raise ValueError('cached Java support source differs')
            for name in ('observations.json','prepared.json','raw.ses'):(out/name).write_bytes(base.content(cached/name,16*1024**2))
            base.write(out/'cached-routing-summary.json',prior_routing)
            record['routing_reuse']={'run':protocol['reuse_routing'],'summary_sha256':base.sha(base.content(cached/'summary.json')),
                'git_head':prior_routing['runtime']['git']['head'],'original_error':prior_routing['error'],
                'prior_run_wall_seconds':prior_routing['wall_seconds'],'prior_run_total_cpu_seconds':prior_routing['total_cpu_seconds'],
                'new_routing_execution':False,'new_ses_writer_execution':False,'scope':'Native diagnosis of saved generated proposal. Failed exact-coordinate obligation remains unqualified; never routing acceptance.'}
            capture()
        jar=str(ROOT/tools['jar']['path'])
        if native_from_ses:
            cached=ROOT/protocol['reuse_ses'];prior_run=base.decode(base.content(cached/'summary.json'))
            if (prior_run.get('status')!='failed' or prior_run.get('error')!='ValueError: engine route shape metadata differs'
                    or prior_run['runtime']['original']!=before['original'] or prior_run['runtime']['tools']!=before['tools']
                    or any(before['cached_ses_inventory'].get(k)!=v for k,v in prior_run['frozen_evidence'].items())
                    or inventory(cached/'observe-input')!=before['original']
                    or base.content(cached/'mixed.dsn')!=derived or base.decode(base.content(cached/'expectations.json'))!=expected
                    or prior_run['runtime']['sources'][str(HERE.relative_to(ROOT)/'MixedClassProbe.java')]!=before['sources'][str(HERE.relative_to(ROOT)/'MixedClassProbe.java')]
                    or [(r['name'],r['status'],r['exit_code'],r.get('cleanup_complete')) for r in prior_run['steps']]!=[('compile','success',0,True),('import','success',0,True)]):
                raise ValueError('cached actual writer source/process/evidence differs')
            for name in ('observations.json','raw.ses'):(out/name).write_bytes(base.content(cached/name,16*1024**2))
            record['ses_reuse']={'run':protocol['reuse_ses'],'summary_sha256':base.sha(base.content(cached/'summary.json')),
                'git_head':prior_run['runtime']['git']['head'],'original_status':prior_run['status'],
                'prior_run_wall_seconds':prior_run['wall_seconds'],'prior_run_total_cpu_seconds':prior_run['total_cpu_seconds'],
                'new_writer_execution':False,'scope':'Reuse completed actual writer output after a strict checker correction; original failed receipt retained. Fresh native stages only.'}
            capture()
        elif not native_from_routing:
            step('compile',[*base.SANDBOX,tools['javac']['path'],'-J-Xmx256m','-J-Duser.home='+env['HOME'],'-proc:none','-classpath',jar,'-d',str(out/'classes'),str(code/'MixedClassProbe.java'),str(code/'ExactPointWitness.java'),str(out/'code/experiments/custom_pad_area_probe_v1/AreaContactProbe.java'),*([str(code/'SelectiveAreaProbe.java')] if selective_obstacles or routing_probe else []),*([str(code/'SelectiveRoutingProbe.java')] if routing_probe else [])],30)
            step('import',[*base.SANDBOX,tools['java']['path'],'-Xmx256m','-Djava.awt.headless=true','-Duser.home='+env['HOME'],'-Djava.io.tmpdir='+env['TMPDIR'],'-cp',str(out/'classes')+os.pathsep+jar,'SelectiveRoutingProbe' if routing_probe else 'SelectiveAreaProbe' if selective_obstacles else 'MixedClassProbe',str(out/('unrouted.dsn' if routing_probe else 'mixed.dsn')),str(out/'observations.json'),*(['adapter-route' if adapter_proposal else 'cancel' if cancel_routing else 'route'] if routing_probe else ['local250-ses' if ses_roundtrip else 'local250'] if local_clearance and not selective_obstacles else [])],90 if routing_probe else 60)
        observed=base.decode(base.content(out/'observations.json',16*1024**2))
        if routing_probe:
            from experiments.pic_mixed_transport_probe_v1 import routing_checks,routing_native,ses_checks
            record['routing_executed']=observed.get('routing_executed') is True and not native_from_routing
            record['ses_executed']=observed.get('ses_executed') is True and not native_from_routing
            if observed.get('cancel_before_routing') is not cancel_routing:raise ValueError('observed cancellation mode differs from requested action')
            if native_from_routing:
                try:routing_checks.compare(observed,route_expected,retained_selective)
                except ValueError as exc:
                    if str(exc)!='exact integer engine point required':raise
                    record['retained_routing_failure']='ValueError: '+str(exc)
                else:raise ValueError('expected retained strict geometry failure absent')
                record['routing_comparison']=routing_checks.compare(observed,route_expected,retained_selective,native_diagnostic=True)
            elif adapter_proposal:
                try:routing_checks.compare(observed,route_expected,retained_selective,adapter_receipt=record['routing_adapter'])
                except ValueError as exc:
                    if str(exc)!='exact integer engine point required':raise
                    record['strict_geometry_error']='ValueError: '+str(exc)
                record['routing_comparison']=routing_checks.compare(observed,route_expected,retained_selective,native_diagnostic=True,adapter_receipt=record['routing_adapter'])
            else:
                record['routing_comparison']=routing_checks.compare(observed,route_expected,retained_selective)
            raw=base.content(out/'raw.ses',ses_checks.MAX_SES);writer=observed['writer']['ses']
            if writer!={'executed':True,'returned':True,'closed':True,'bytes':len(raw),'sha256':base.sha(raw),'path':'raw.ses','write_completed':True,'stream_accepted_bytes':len(raw)}:
                raise ValueError('generated SES writer binding differs')
            # The shared native task recipe has zero ordinary routes and unchanged source intent.
            task=routing_native.task_copy(out/'observe-input'/original.SOURCE.name,out/'task-project')
            if native_from_routing or adapter_proposal:
                _,survival=ses_checks.audit(raw,unrouted,route_expected,sx.parse(base.content(task).decode()),generated=True,proposal_only=True)
                survival.update(generated_engine_to_ses_exact=False,retained_routing_failure=record.get('retained_routing_failure'),
                    adapter_proposal_only=adapter_proposal,strict_geometry_error=record.get('strict_geometry_error'),
                    scope='Structurally checked new routing proposal for native diagnosis only; exact engine geometry remains unqualified.')
            else:
                _,survival=ses_checks.audit(raw,unrouted,route_expected,sx.parse(base.content(task).decode()),observed['final_geometry'],generated=True)
            record['generated_transport']=survival;capture()
            if cancel_routing:
                record.update(status='completed',observations_complete=True,cancel_control=True)
            else:
                native_routing=routing_native.execute(out,out/'observe-input'/original.SOURCE.name,route_expected,survival,remaining,step,env,capture,record,lambda path:pending_candidate(out,path,frozen,mutable_files,capture),diagnostic_only=native_from_routing or adapter_proposal)
                record.update(status='completed' if native_routing['completed'] else 'observed-incomplete',observations_complete=native_routing['completed'])
        elif selective_obstacles:
            from experiments.pic_mixed_transport_probe_v1 import selective
            comparison=selective.compare(observed,expected,base.decode(baseline))
            record.update(status='completed',observations_complete=True,selective_comparison=comparison,
                local_reuse=local_binding)
            capture()
        elif ses_roundtrip:
            import copy
            from experiments.pic_mixed_transport_probe_v1 import ses_checks,ses_native
            record['ses_executed']=observed.get('ses_executed') is True
            if len(observed.get('cases',[]))==2:
                record['writer']=observed['cases'][1].get('ses')
            if observed.get('ses_executed') is not True:raise ValueError('SES writer did not complete')
            prior=copy.deepcopy(observed);prior['ses_executed']=False
            comparisons=transport.validate_local(prior,expected)
            if not all(r['observed'] for r in comparisons):raise ValueError('SES input local state incomplete')
            for case in observed['cases']:
                if case['route_geometry_before_local']!=case['route_geometry']:raise ValueError('local clearance changed ordinary routing geometry')
                ses_checks.geometry_check(case['route_geometry'],case['state'])
            row=observed['cases'][1];writer=row['ses'];raw=base.content(out/'raw.ses',ses_checks.MAX_SES)
            if (writer!={'executed':True,'returned':True,'closed':True,'bytes':len(raw),'sha256':base.sha(raw),'path':'raw.ses','write_completed':True,'stream_accepted_bytes':len(raw)}
                    or row['state']!=row['state_after_ses'] or row['route_geometry']!=row['route_geometry_after_ses']):
                raise ValueError('SES writer binding or unchanged engine state differs')
            tree,survival=ses_checks.audit(raw,derived,expected,sx.parse(base.content(out/'observe-input'/original.SOURCE.name).decode()),row['route_geometry'])
            record.update(ses_executed=True,writer=writer,ses_transport=survival,case_comparison=comparisons);capture()
            # A safely parsed retained-route mismatch may still receive diagnostic
            # native DRC; no reconstructed candidate can pass that failed obligation.
            reuse=None
            if finish_native:
                cached=ROOT/protocol['reuse_positive']
                if base.content(cached/'raw.ses')!=raw:raise ValueError('cached positive SES differs')
                reuse=ses_native.cached_positive(cached,before,before['cached_positive_inventory'])
            native_ses=ses_native.execute(out,out/'observe-input'/original.SOURCE.name,tree,expected,survival,remaining,step,env,capture,record,reuse=reuse)
            record.update(status='completed' if native_ses['completed'] else 'observed-incomplete',observations_complete=native_ses['completed'])
        else:
            comparisons=(transport.validate_local(observed,expected) if local_clearance else transport.validate(observed,expected))
            record.update(status='completed',observations_complete=all(r['observed'] for r in comparisons),case_comparison=comparisons)
            if not record['observations_complete']:record['status']='observed-incomplete'
    except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',error=type(exc).__name__+': '+str(exc))
    record['frozen_evidence']=frozen
    return base.publish(out,record,stable,account,remaining)

def main(argv=None):
    started=time.monotonic();cpu_started=base.cpu()
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-probe',action='store_true');parser.add_argument('--output',type=Path,required=True);parser.add_argument('--local-clearance',action='store_true');parser.add_argument('--ses-roundtrip',action='store_true');parser.add_argument('--native-from-ses',action='store_true');parser.add_argument('--finish-native',action='store_true');parser.add_argument('--selective-obstacles',action='store_true');parser.add_argument('--routing-probe',action='store_true');parser.add_argument('--cancel-routing',action='store_true');parser.add_argument('--native-from-routing',action='store_true');parser.add_argument('--adapter-proposal',action='store_true');args=parser.parse_args(argv)
    if not args.run_probe:parser.error('--run-probe required')
    with base.cancellation(),base.real(ROOT/'.runs/quality-experiment.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);result=experiment(args.output,started=started,cpu_started=cpu_started,local_clearance=args.local_clearance,ses_roundtrip=args.ses_roundtrip,native_from_ses=args.native_from_ses,finish_native=args.finish_native,selective_obstacles=args.selective_obstacles,routing_probe=args.routing_probe,cancel_routing=args.cancel_routing,native_from_routing=args.native_from_routing,adapter_proposal=args.adapter_proposal)
    print(base.canonical({k:result.get(k) for k in ('status','observations_complete','wall_seconds','total_cpu_seconds')}).decode(),end='')
    return 0 if result['observations_complete'] else 1

if __name__=='__main__':raise SystemExit(main())
