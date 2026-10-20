"""Prepare two fresh GUI084 source roles after their own completed Native proofs.

Run only after lead review and with the Native lane idle. This executes no board
worker or GUI: one bounded no-network child prepares the existing isolated
launcher. Native readers replay retained proofs; preparation is not GUI support.
A late refusal may retain a partial session; never reuse or delete it here.
"""
from pathlib import Path
import datetime,json,os,resource,shutil,sys,time
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
ADMIN=Path(__file__).resolve().parents[1]
RUNTIME=ADMIN/'.runs/runtime-directory-048/runtime'
HEAD='e49a8d7c5f1423c9a82241e5ab58592cd5f119ac'
MANIFEST='97b4d212270c1fda57a8b151910e2f42ba81bc64828ffefda2fc4de4e2651693'
CASES=(('ordinary-alias2Cu','2396bd26e8a3b47a015c7632c0489fa06156fcd4772dc15328d28eaf71221e4d','partial_completion',4,'route','standard',[0,0,0,0]),
       ('improve-fractional','d6abd71a4af3b904d4e1e2023ed6cfe1d5dbae2045f354cc75ce8af0f15efa96','whole_board_unlocked_routing',1,'improve','tuned',[0,0,6,0]))
assert Path(sys.executable).absolute()==RUNTIME/'.venv/bin/python' and Path(sys.prefix).resolve()==RUNTIME/'.venv'
assert sys.prefix!=sys.base_prefix
sys.path.insert(0,str(RUNTIME));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,provenance as pv,preferences as pref
from autorouter import floor_route as f,handoff as h,placement_clearance as pc,review_export as ex,sexpr as sx,local_settings as local,strategy
from autorouter.gui import child_environment
from autorouter.runner import run
assert c.ROOT==RUNTIME and c.NATIVE_VERSION=='10.0.7'
SELF=h.real_path(Path(__file__).absolute());assert SELF==ADMIN/'.runs/prepare-runtime048-gui084.py'
prerequisites={}
def pin(path):
    path=h.real_path(path);prerequisites[str(path)]=p.sha(path);return f.read_json(path)
def process_ok(row):
    assert row['status']=='success' and row['exit_code']==0
    assert row['cleanup_complete'] is True and row['log_truncated'] is False
manifest=RUNTIME/pv.MANIFEST;assert p.sha(manifest)==MANIFEST
prerequisites[str(manifest)]=MANIFEST;prerequisites[str(SELF)]=p.sha(SELF)
tools=p.tool_manifest()
assert tools['git_head']==HEAD and tools['kicad']=='10.0.7'
assert tools['source_provenance']['manifest_sha256']==MANIFEST
assert tools['source_provenance']['native_version']=='10.0.7'
full=pin(ADMIN/'.runs/full-integration-197/execution.json');full_plan=pin(ADMIN/'.runs/full-integration-197/protocol.json')
assert full['passed'] is True and full['sources_unchanged'] is True;process_ok(full['process'])
assert full_plan['tools']['git_head']==HEAD
for name,digest in tools['implementation_sha256'].items():assert full_plan['source_sha256'][name]==digest
prepared=pin(RUNTIME.parent/'preparation.json')
assert prepared['prepared'] is True and prepared['source_head']==HEAD and prepared['runtime']==str(RUNTIME)
assert prepared['manifest_sha256']==MANIFEST and prepared['recipe']['source_provenance']==tools['source_provenance']
assert prepared['full197_execution_sha256']==prerequisites[str(ADMIN/'.runs/full-integration-197/execution.json')]
venv=pin(RUNTIME.parent/'venv-process.json');process_ok(venv)
assert prerequisites[str(RUNTIME.parent/'venv-process.json')]==prepared['venv_process_sha256']
base=ADMIN/'.runs/runtime048-native-qualification-001'
doctor=pin(base/'doctor.json');doctor_process=pin(base/'doctor-process.json');process_ok(doctor_process)
assert doctor['ready'] is True and doctor['workspace']==str(RUNTIME)
assert doctor['checks']['runtime_provenance']=={'verified':True,'identity':tools['source_provenance']}
assert doctor_process['argv']==[*f.SANDBOX,str(RUNTIME/'.venv/bin/python'),'-B','-m','autorouter','doctor']
positives={};packets=[];pairs=[]
for label,protocol_sha,scope,protected_count,method,profile,expected_counts in CASES:
    folder=base/label;protocol=folder/'protocol.json';assert p.sha(protocol)==protocol_sha
    plan=pin(protocol);completed=pin(folder/'execution.json');settings_path=folder/'settings.json'
    settings=pref.validate(dict(pref.DEFAULTS,scope=scope,seconds=90,profile=profile,adapter='both',
        guidance='native',layers='source_all',scoring_preference=None))
    assert plan['schema']==1 and plan['kind']=='runtime048-six-stage-route-or-improve-CLI'
    assert plan['case']==label and plan['method']==method
    assert plan['runtime']==str(RUNTIME) and plan['source_head']==HEAD and plan['runtime_manifest_sha256']==MANIFEST
    assert plan['tools']==tools and plan['settings']==settings and plan['budgets']=={'route':90,'export':90}
    assert plan['expected_protected_count']==protected_count and p.sha(settings_path)==plan['settings_sha256']
    assert f.read_json(settings_path)==settings;prerequisites[str(settings_path)]=plan['settings_sha256']
    for path,key in ((ADMIN/'scripts/qualify_runtime_workflow.py','driver_sha256'),(ADMIN/'.runs/enclose-runtime044-workflow-001.py','enclosure_sha256')):
        assert p.sha(path)==plan[key];prerequisites[str(path)]=plan[key]
    output=RUNTIME/'.runs'/(label+'-001');assert plan['output']==str(output)
    assert completed['controls_passed'] is True and completed['workflow_delivered'] is True and completed['error'] is None
    assert completed['protocol_sha256']==protocol_sha and max(completed['complete_wall_seconds'],completed['complete_full_CPU_seconds'])<=240
    process_ok(completed['process'])
    child_path=output/'result.json';assert completed['child_receipt']==str(child_path) and completed['child_sha256']==p.sha(child_path)
    child=pin(child_path);source=h.real_path(plan['source']);hashes=plan['source_hashes']
    assert len(hashes)==4 and pc.inventory(source.parent)==hashes
    assert child['status']=='completed' and child['workflow_delivered'] is True and child['accepted'] is False
    assert child['actual_GUI'] is False and child['human_review'] is False and child['method']==method
    assert child['source']==str(source) and child['source_hashes']==hashes and child['tools']==tools and child['settings']==settings
    assert child['settings_path']==str(settings_path) and child['settings_sha256']==plan['settings_sha256']
    assert child['driver_sha256']==plan['driver_sha256']
    assert [r['stage'] for r in child['processes']]==['preview','route','review','choice','export','verify_export']
    for row in child['processes']:
        assert row['process']['exit_code']==0 and row['process']['cancel_requested'] is False and row['process']['log_truncated'] is False
        assert p.sha(output/(row['stage']+'.log'))==row['log_sha256']
    workspace=h.real_path(child['workspace']);assert workspace.parent==output and workspace.name.startswith('autorouter-gui-')
    route_path=workspace/'route/result.json';export_path=workspace/'export/export.json'
    route=pin(route_path);exported=pin(export_path)
    with p.validation_readback_session():
        checked=p.check_result(route_path);checked_export=ex.check_export(export_path)
    assert checked['current'] is True and checked['applied'] is False
    assert checked_export['current'] is True and checked_export['export_accepted'] is True and checked_export['applied'] is False
    assert route['accepted'] is True and route['status']=='routing_accepted' and exported['export_accepted'] is True
    assert route['scope']==scope and route['engine_profile']==profile and route['adapter']=='both'
    if method=='improve':
        assert route.get('scoring_variant') is None and route.get('incumbent_scoring_variant') is None
    else:assert route['scoring_variant'] is None
    assert route['budget_seconds']==route['cpu_budget_seconds']==exported['budget_seconds']==90
    assert exported['inputs']['source']==str(source) and exported['inputs']['receipt']==str(route_path)
    assert exported['inputs']['receipt_sha256']==p.sha(route_path) and exported['original_geometry_and_routing_unchanged'] is True
    original=sx.read(source);protected=p.protected_for_record(route,original);assert len(protected)==protected_count
    counts=[route['native'][key] for key in ('opens','blocking','warnings','exclusions')]
    assert counts==[exported['native'][key] for key in ('opens','blocking','warnings','exclusions')]==completed['Native_counts']
    assert all(type(n)is int and n>=0 for n in counts) and counts==expected_counts and completed['protected_count']==protected_count
    if plan['expected_counts'] is None:assert plan['warning_policy']=='retain_all_native_findings' and counts[3]==plan['expected_exclusions']
    else:assert counts==plan['expected_counts']
    for data,candidate in ((route,workspace/'route/candidate'/source.name),(exported,workspace/'export/validation/candidate'/source.name)):
        assert data['candidate']==str(candidate) and data['tools']==tools and data['source_hashes']==hashes
        assert data['schematic_parity']=='checked by final native DRC';p.verify_candidate_files(candidate,hashes,data['candidate_sha256'])
        tree=sx.read(candidate);assert p.immutable(tree)==p.immutable(original) and all(item in p.routes(tree) for item in protected)
    assert route['candidate_sha256']==exported['candidate_sha256']==child['candidate_sha256']
    if method=='improve':
        assert route['strategy']=='native_validated_zone_net_pruning' and route['pruning_preferences']['effective']==settings
        packets.extend(strategy.native7_packets(route_path.parent,route))
    else:
        assert route.get('strategy') is None and route['routing_preferences']['effective']==settings
        packets.append((route_path.parent,route))
    packets.append((workspace/'export/validation',exported))
    preview=pin(workspace/'review/review.json')['preview'];plot=workspace/'review/plot-work'
    for step in preview['steps']:
        assert step['cwd']==str(plot);process=f.process_check(plot,preview,step['name'],step['argv'])
        pairs.append((plot,f.read_json(plot/(step['name']+'-input-binding.json')),process))
    positives[label]=dict(source=str(source),source_hashes=hashes,method=method,settings=settings,settings_sha256=plan['settings_sha256'],
        output=str(output),material=pc.inventory(output,max_bytes=256*1024**2,max_files=8000,max_entries=16000),
        Native_counts=counts,protected_count=protected_count,candidate_sha256=child['candidate_sha256'])

def fresh():
    assert p.tool_manifest()==tools and p.sha(manifest)==MANIFEST
    for path,digest in prerequisites.items():assert p.sha(Path(path))==digest
    for item in positives.values():
        assert pc.inventory(Path(item['source']).parent)==item['source_hashes']
        assert pc.inventory(Path(item['output']),max_bytes=256*1024**2,max_files=8000,max_entries=16000)==item['material']
    for name,module in tuple(sys.modules.items()):
        if name.split('.')[0]=='autorouter' and getattr(module,'__file__',None):assert Path(module.__file__).resolve().is_relative_to(RUNTIME),name
    assert time.monotonic()-START<90 and cpu()-CPU0<90
fresh();assert shutil.disk_usage(ADMIN).free>2*1024**3
session=RUNTIME/'.runs/gui-session084';launcher=RUNTIME/'.runs/gui-launcher084'
for path in (session,launcher):assert h.real_path(path,existing=False)==path and not os.path.lexists(path)
session.mkdir(mode=0o700);owner={};h.capture_destination(owner,session)
roles={}
for label,project,inspection,settings_name in (('ordinary-alias2Cu','project','inspection','route-settings.json'),('improve-fractional','fractional-project','fractional-inspection','fractional-settings.json')):
    item=positives[label];source=Path(item['source'])
    for name in (project,inspection):
        shutil.copytree(source.parent,session/name);assert pc.inventory(session/name)==item['source_hashes']
    shutil.copyfile(base/label/'settings.json',session/settings_name)
    assert p.sha(session/settings_name)==item['settings_sha256']
    roles[label]=dict(source=str(session/project/source.name),inspection=str(session/inspection/source.with_suffix('.kicad_pro').name),
        original_source=str(source),source_hashes=item['source_hashes'],method=item['method'],
        description=('Ordinary partial90 corrected-standard alias-layer source, protected4' if item['method']=='route' else
            'Optional whole Improve90 tuned incumbent/pruning/final-reserve method, protected1; six retained Native warnings'),
        settings=item['settings'],settings_path=str(session/settings_name),settings_sha256=item['settings_sha256'])
(session/'jobs').mkdir(mode=0o700)
required=dict(schema=1,state='PREPARED_ONLY_NOT_EXECUTED',runtime=str(RUNTIME),source_head=HEAD,runtime_manifest_sha256=MANIFEST,
    roles=roles,actual_GUI_qualified=False,required_observations='Fresh toolbar ordinary alias partial90/standard and separate explicit Improve fractional whole-method90/tuned roles. Each requires rendered F/B review, explicit acknowledged intent, fresh export90 and checked opening; own Native/fullSCH/original/protected4 or1. Improve budget includes incumbent/trials/25s return reserve; no score override. No prior GUI role transfer or actual GUI observation is inferred from preparation.')
p.save_json(session/'protocol-required-001.json',required)
process=run([*f.SANDBOX,str(RUNTIME/'.venv/bin/python'),'-B',str(RUNTIME/'scripts/install_gui.py'),'--output',str(launcher)],
    cwd=session,env=child_environment(),log=session/'prepare-launcher.log',timeout=min(30,90-(time.monotonic()-START)),
    max_log_bytes=512*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=1024**3)
p.save_json(session/'prepare-launcher-process.json',process);process_ok(process)
install=f.read_json(launcher/'install.json');assert install['checkout']==str(RUNTIME) and install['tools']==tools
assert install['installed_globally'] is False and install['standalone'] is False
launcher_hashes=pc.inventory(launcher,max_bytes=16*1024**2,max_files=100,max_entries=200)
record=dict(schema=1,state='PREPARED_ONLY_NOT_EXECUTED',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    runtime=str(RUNTIME),source_head=HEAD,runtime_manifest_sha256=MANIFEST,tools=tools,roles=roles,
    source=roles['ordinary-alias2Cu']['source'],inspection=roles['ordinary-alias2Cu']['inspection'],settings=roles['ordinary-alias2Cu']['settings'],
    settings_path=roles['ordinary-alias2Cu']['settings_path'],settings_sha256=roles['ordinary-alias2Cu']['settings_sha256'],
    jobs=str(session/'jobs'),launcher=str(launcher/'Launch Autorouter.command'),launcher_hashes=launcher_hashes,
    native_prerequisites={label:{key:value for key,value in item.items() if key!='material'} for label,item in positives.items()},
    prerequisite_sha256=prerequisites,protocol_required_sha256=p.sha(session/'protocol-required-001.json'),
    sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0,external_complete_exit_required=True,
    actual_GUI_qualified=False,Native_executed=False,project_complete=False,
    scope='Preparation only from two fresh six-stage Native route/improve prerequisites; original source copies, not candidates. Same Mac/account/base Python/external dependencies. No cleanOS/standalone/Windows/quality/human/electrical claim. Actual GUI roles remain unperformed; a late refusal can retain this non-authoritative preparation record.')
p.save_json(session/'prepared-state.json',record);record_pin=p.sha(session/'prepared-state.json')
assert h.owned_destination(owner)==session;fresh()
for role in roles.values():
    for key in ('source','inspection'):assert pc.inventory(Path(role[key]).parent)==role['source_hashes']
    assert p.sha(Path(role['settings_path']))==role['settings_sha256']
assert pc.inventory(launcher,max_bytes=16*1024**2,max_files=100,max_entries=200)==launcher_hashes
assert p.sha(session/'protocol-required-001.json')==record['protocol_required_sha256'] and p.sha(session/'prepared-state.json')==record_pin
local.check_final_events(packets,c.CLI,pairs=pairs)
assert time.monotonic()-START<90 and cpu()-CPU0<90
print(json.dumps(dict(prepared_state=str(session/'prepared-state.json'),sha256=record_pin,actual_GUI_qualified=False,Native_executed=False)))
