"""DRAFT ONLY: prepare the fresh057-root ordinary GUI091 role after review.

Use the installed root's Python, with the GUI090/Native worker idle. One existing
ordinary CLI route/export proof pair is replayed read-only; no eleven-case/IR
replay, solver, Native worker or GUI is started. The sole bounded no-network
child runs the unchanged install_gui --output writer. Retain any partial failure.
Actual new-root preview/review/acknowledged intent/fresh export/checked opening
and complete external preparation costs remain required. Same Mac/base Python/
external dependency paths; no cleanOS, standalone or transferred GUI authority.
"""
from pathlib import Path
import datetime,json,os,resource,shutil,sys,time
START=time.monotonic()
def cpu():return sum(row.ru_utime+row.ru_stime for row in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ADMIN=Path(__file__).resolve().parents[1]
RUNTIME=ADMIN/'.runs/runtime057 fresh install 001'
ORIGINAL=ADMIN/'.runs/runtime-directory-057/runtime'
QUALIFICATION=ADMIN/'.runs/runtime057-install-existing-qualification-001'
CASE=QUALIFICATION/'ordinary-alias2Cu';OUTPUT=RUNTIME/'.runs/ordinary-alias2Cu-001'
WORK=OUTPUT/'autorouter-gui-7c385b3a104247d18857fca349cab3aa'
SOURCE=ADMIN/'.runs/native7-source-all-alias-controls-001/source/owned1007-transport.kicad_pcb'
HEAD='ac1a48c3b25b2217e0f8252e0e6da21905f144a4'
MANIFEST='b1d7066dff94e331f967afa89a4c0b3e2cfa10067324c3216996b31476898c51'
ORIGINAL_MANIFEST='9c667b15b916fc18fadec6dcbd6e0f9710a0c4cc6daeb36fc616f111ef03722e'
SETTINGS_SHA='a73292826f5de5a992d4d04ec85ced90ecac269556f72b35180f610e79866a65'
CANDIDATE='7327b94e81653b0830a349e22230d1da562cb76eebb8042c96bb6eb460b424f5'
TEMPLATE=ADMIN/'.runs/prepare-runtime050-install-existing-gui087-002.py'
PUBLIC=ADMIN/'evidence/runtime057-install-existing-001.json'
assert Path(sys.executable).absolute()==RUNTIME/'.venv/bin/python'
assert Path(sys.prefix).resolve()==RUNTIME/'.venv' and sys.prefix!=sys.base_prefix
assert sys.version_info[:3]==(3,11,9) and sys.base_prefix=='/Users/faisal/.pyenv/versions/3.11.9'
sys.path.insert(0,str(RUNTIME));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,handoff as h
from autorouter import provenance as pv,preferences as pref,placement_clearance as pc,review_export as ex,local_settings as local
from autorouter.gui import child_environment
from autorouter.runner import run
from scripts import install_gui as installer
assert c.ROOT==RUNTIME and c.NATIVE_VERSION=='10.0.7'
assert Path(installer.__file__).resolve()==RUNTIME/'scripts/install_gui.py'
SELF=h.real_path(Path(__file__).absolute());assert SELF==ADMIN/'.runs/prepare-runtime057-install-existing-gui091.py'
SELF_SHA=p.sha(SELF)
route_path=WORK/'route/result.json';export_path=WORK/'export/export.json';child_path=OUTPUT/'result.json'
prerequisites={
    TEMPLATE:'8ff73a154b805c3d5fc933ab18d78d02fdc53b6fc4d789e923ea3c8352571ee7',
    PUBLIC:'9d87a27e8a6329698b80e2e6f905361f40cb2391b70f9a54d7cf0f2917e6d006',
    RUNTIME/pv.MANIFEST:MANIFEST,ORIGINAL/pv.MANIFEST:ORIGINAL_MANIFEST,
    QUALIFICATION/'preparation.json':'64a555603f104f670e53459d05c72f2a86385ff79223adeef6bb7340f32f1d9b',
    QUALIFICATION/'doctor.json':'85673d8e3e11da01e1c7a9fa1a8d959ab4647fa42a4070d23174c8cd1823fc2d',
    QUALIFICATION/'doctor-process.json':'1ca8908b772766990bd5ef158b389bf1d944061766303a6d2869e4a4dfb86dd3',
    CASE/'protocol.json':'ff0da6afe89b1209ce8b6c5c75254e84b742840f69276b3415f8375b9fb5cec4',
    CASE/'execution.json':'06349c56ecaebe2079bd8a64baf7747d3eff8ed818d24040a85d166b470958cc',
    CASE/'settings.json':SETTINGS_SHA,
    child_path:'09ed05a34b49354b3e14de93c12470c524398294ceb5bce06151cab9a006727c',
    route_path:'cddc8f84c707a4b576eb0527967da3838218053ba26414005fa2a4253bc633ef',
    export_path:'7f93ca3968443139d82bcfc8f2ee9aa97050bc7e203f55cad4dd68e353e21685',
    RUNTIME/'scripts/install_gui.py':'0a7c487951c1641e4e790105939394bc3c430612a6cfe7376bd62f5acd67f56f',
    RUNTIME/'scripts/prepare_gui_plugin.py':'dfa0580e0ef88791601053922ba164eedadad8a9fd9a3d8935e6a75e4017798a',
    SELF:SELF_SHA}
for path,pin in prerequisites.items():assert p.sha(h.real_path(path))==pin,str(path)
plan=f.read_json(CASE/'protocol.json');execution=f.read_json(CASE/'execution.json');child=f.read_json(child_path)
prepared=f.read_json(QUALIFICATION/'preparation.json');published=f.read_json(PUBLIC)
original_record=f.read_json(ORIGINAL/pv.MANIFEST);manifest=f.read_json(RUNTIME/pv.MANIFEST)
assert len(original_record['immutable_files_sha256'])==54 and manifest=={**original_record,'root':str(RUNTIME)}
implementation={name:pin for name,pin in original_record['immutable_files_sha256'].items() if name.startswith('autorouter/')}
original_identity=pv._runtime_identity(ORIGINAL,implementation);tools=p.tool_manifest()
assert original_identity['git_head']==HEAD and original_identity['manifest_sha256']==ORIGINAL_MANIFEST
assert pv._runtime_identity(RUNTIME,implementation)==tools['source_provenance']
assert tools==plan['tools']==child['tools'] and tools['git_head']==HEAD and tools['kicad']=='10.0.7'
assert tools['source_provenance']['manifest_sha256']==MANIFEST
assert prepared['runtime']==str(RUNTIME) and prepared['source_head']==HEAD and prepared['runtime_manifest_sha256']==MANIFEST
assert prepared['source_runtime']==str(ORIGINAL) and prepared['source_manifest_sha256']==ORIGINAL_MANIFEST
assert prepared['immutable_maps_build_source_engine_unchanged'] is True and prepared['immutable_files']==54
assert prepared['installation_record_is_authoritative'] is False and prepared['doctor_ready'] is True
for name,pin in prepared['prerequisite_sha256'].items():
    path=h.real_path(name);assert p.sha(path)==pin;prerequisites[path]=pin
assert [row['protocol_sha256'] for row in prepared['protocols'] if row['case']=='ordinary-alias2Cu']==[prerequisites[CASE/'protocol.json']]
doctor=f.read_json(QUALIFICATION/'doctor.json');doctor_process=f.read_json(QUALIFICATION/'doctor-process.json')
assert doctor['ready'] is True and doctor['workspace']==str(RUNTIME)
assert doctor['checks']['runtime_provenance']==dict(verified=True,identity=tools['source_provenance'])
assert doctor_process['status']=='success' and doctor_process['exit_code']==0 and doctor_process['cleanup_complete'] is True and doctor_process['log_truncated'] is False
settings=pref.validate(dict(pref.DEFAULTS,scope='partial_completion',seconds=90))
assert plan['schema']==1 and plan['kind']=='runtime057-six-stage-route-or-improve-CLI' and plan['case']=='ordinary-alias2Cu' and plan['method']=='route'
assert plan['runtime']==str(RUNTIME) and plan['source_head']==HEAD and plan['runtime_manifest_sha256']==MANIFEST and plan['output']==str(OUTPUT)
assert plan['source']==str(SOURCE) and plan['settings']==child['settings']==settings==pref.load(CASE/'settings.json').parsed
assert plan['settings_sha256']==child['settings_sha256']==SETTINGS_SHA and child['settings_path']==str(CASE/'settings.json')
assert plan['budgets']==dict(route=90,export=90) and plan['expected_counts']==[0,0,0,0] and plan['expected_protected_count']==4
assert execution['controls_passed'] is True and execution['workflow_delivered'] is True and execution['error'] is None
assert execution['protocol_sha256']==prerequisites[CASE/'protocol.json'] and execution['child_receipt']==str(child_path) and execution['child_sha256']==prerequisites[child_path]
assert max(execution['complete_wall_seconds'],execution['complete_full_CPU_seconds'])<=240
assert execution['process']['status']=='success' and execution['process']['exit_code']==0 and execution['process']['cleanup_complete'] is True and execution['process']['log_truncated'] is False
assert child['status']=='completed' and child['workflow_delivered'] is True and child['accepted'] is False and child['actual_GUI'] is False and child['human_review'] is False
assert child['method']=='route' and child['source']==str(SOURCE) and child['workspace']==str(WORK)
assert [row['stage'] for row in child['processes']]==['preview','route','review','choice','export','verify_export']
hashes=plan['source_hashes'];assert len(hashes)==4 and child['source_hashes']==hashes and pc.inventory(SOURCE.parent)==hashes
assert hashes[SOURCE.name]=='72ea130a31ae15ecad765bb08fa00ebf0b20a399f6fe733f72fedc68c0b2a77a'
route=f.read_json(route_path);exported=f.read_json(export_path)
assert route['accepted'] is True and route['scope']=='partial_completion' and route['engine_profile']=='standard' and route['adapter']=='both' and route['scoring_variant'] is None
assert route['routing_preferences']['effective']==settings and route['budget_seconds']==route['cpu_budget_seconds']==exported['budget_seconds']==exported['cpu_budget_seconds']==90
assert route['candidate_sha256']==exported['candidate_sha256']==child['candidate_sha256']==CANDIDATE
assert execution['Native_counts']==[0,0,0,0] and execution['protected_count']==4
assert route['source']==exported['inputs']['source']==str(SOURCE) and exported['inputs']['receipt']==str(route_path) and exported['inputs']['receipt_sha256']==prerequisites[route_path]
for data in (route,exported):
    assert data['source_hashes']==hashes and data['tools']==tools and data['schematic_parity']=='checked by final native DRC'
    assert [data['native'][key] for key in ('opens','blocking','warnings','exclusions')]==[0,0,0,0]
assert len(p.protected_for_record(route,p.sx.read(SOURCE)))==4
public_rows=[row for row in published['rows'] if row['case']=='ordinary-alias2Cu'];assert len(public_rows)==1
public_row=public_rows[0]
assert published['source_head']==HEAD and published['runtime_manifest_sha256']==MANIFEST and published['installation_record_is_authoritative'] is False
assert public_row['Native_counts']==[0,0,0,0] and public_row['protected_count']==4 and public_row['candidate_sha256']==CANDIDATE
assert public_row['own_final']['route']['receipt_sha256']==prerequisites[route_path] and public_row['own_final']['export']['receipt_sha256']==prerequisites[export_path]
# Only this ordinary proof pair is replayed. Capture its bounded material first.
proof_material=f.evidence_inventory(OUTPUT);proof_owners={}
for folder in (OUTPUT,WORK,route_path.parent,export_path.parent):
    owner={};h.capture_destination(owner,h.real_path(folder));proof_owners[folder]=owner
with p.validation_readback_session():
    checked=p.check_result(route_path);checked_export=ex.check_export(export_path)
assert checked['current'] is True and checked['applied'] is False
assert checked_export['current'] is True and checked_export['export_accepted'] is True and checked_export['applied'] is False
def fresh():
    assert time.monotonic()-START<90 and cpu()-CPU0<90
    for path,pin in prerequisites.items():assert p.sha(path)==pin,str(path)
    assert p.tool_manifest()==tools and pc.inventory(SOURCE.parent)==hashes
    assert f.evidence_inventory(OUTPUT)==proof_material
    for folder,owner in proof_owners.items():assert h.owned_destination(owner)==folder
    for relative in proof_material:
        if Path(relative).suffix=='.kicad_prl':assert local.check_current_metadata(OUTPUT/relative)
    for name,module in tuple(sys.modules.items()):
        if name.split('.')[0]=='autorouter' and getattr(module,'__file__',None):assert Path(module.__file__).resolve().is_relative_to(RUNTIME),name
fresh();assert shutil.disk_usage(ADMIN).free>2*1024**3
session=RUNTIME/'.runs/gui-session091';launcher=RUNTIME/'.runs/gui-launcher091'
for path in (session,launcher):assert h.real_path(path,existing=False)==path and not os.path.lexists(path)
session.mkdir(mode=0o700);owner={};h.capture_destination(owner,session)
for name in ('project','inspection'):
    shutil.copytree(SOURCE.parent,session/name);assert pc.inventory(session/name)==hashes
(session/'jobs').mkdir(mode=0o700);p.save_json(session/'route-settings.json',settings)
assert p.sha(session/'route-settings.json')==SETTINGS_SHA
required=dict(schema=1,state='PREPARED_ONLY_NOT_EXECUTED',runtime=str(RUNTIME),source_head=HEAD,runtime_manifest_sha256=MANIFEST,
    method='route',settings=settings,source=str(session/'project'/SOURCE.name),source_hashes=hashes,
    required_observation='Actual fresh-root GUI091 launcher/toolbar and fresh preview, ordinary partial90 Route, rendered F/B review, close review project, explicit acknowledged Accept, fresh Native export90/check and checked KiCad PCB opening; own final fullSCH/original/protected4 proof required. Preserve pre-editor export. No prior GUI role transfer.',
    actual_GUI_qualified=False,Native_qualification_provided_by_preparation=False,
    scope='One ordinary installed-path functional role on the same Mac/basePython/external tools; no cleanOS/standalone/all-combination or quality qualification.')
p.save_json(session/'protocol-required-001.json',required);required_pin=p.sha(session/'protocol-required-001.json')
fresh()
process=run([*f.SANDBOX,str(RUNTIME/'.venv/bin/python'),'-B',str(RUNTIME/'scripts/install_gui.py'),'--output',str(launcher)],
    cwd=session,env=child_environment(),log=session/'prepare-launcher.log',timeout=min(30,90-max(time.monotonic()-START,cpu()-CPU0)),
    max_log_bytes=512*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=1024**3)
p.save_json(session/'prepare-launcher-process.json',process)
assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False
install=f.read_json(launcher/'install.json')
assert install['root']==str(launcher) and install['checkout']==str(RUNTIME) and install['tools']==tools and install['installed_globally'] is False and install['standalone'] is False
assert install['installer_sha256']==installer.installer_pins() and set(install['immutable_files'])==installer.IMMUTABLE_FILES
for relative,pin in install['immutable_files'].items():assert installer.digest(local.canonical(launcher/relative))==pin
launcher_hashes=pc.inventory(launcher,max_bytes=16*1024**2,max_files=100,max_entries=200)
def prepared_fresh():
    fresh();assert h.owned_destination(owner)==session
    for name in ('project','inspection'):
        assert pc.inventory(session/name)==hashes
        assert local.check_current_metadata(session/name/SOURCE.with_suffix('.kicad_prl').name)
    assert p.sha(session/'route-settings.json')==SETTINGS_SHA and p.sha(session/'protocol-required-001.json')==required_pin
    assert pc.inventory(launcher,max_bytes=16*1024**2,max_files=100,max_entries=200)==launcher_hashes
prepared_fresh()
record=dict(schema=1,state='PREPARED_ONLY_NOT_EXECUTED',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    runtime=str(RUNTIME),source_head=HEAD,runtime_manifest_sha256=MANIFEST,tools=tools,controller_sha256=SELF_SHA,
    template=dict(path=str(TEMPLATE),sha256=prerequisites[TEMPLATE]),source=str(session/'project'/SOURCE.name),original_source=str(SOURCE),source_hashes=hashes,
    inspection=str(session/'inspection'/SOURCE.with_suffix('.kicad_pro').name),method='route',settings=settings,
    settings_path=str(session/'route-settings.json'),settings_sha256=SETTINGS_SHA,jobs=str(session/'jobs'),launcher=str(launcher/'Launch Autorouter.command'),launcher_hashes=launcher_hashes,
    protocol_required=str(session/'protocol-required-001.json'),protocol_required_sha256=required_pin,
    ordinary_CLI_prerequisite=dict(protocol=str(CASE/'protocol.json'),protocol_sha256=prerequisites[CASE/'protocol.json'],execution=str(CASE/'execution.json'),execution_sha256=prerequisites[CASE/'execution.json'],child=str(child_path),child_sha256=prerequisites[child_path],route=str(route_path),route_sha256=prerequisites[route_path],export=str(export_path),export_sha256=prerequisites[export_path],Native_counts=[0,0,0,0],protected_routes=4,candidate_sha256=CANDIDATE,scope='Current shared-reader replay of one completed fresh-root CLI prerequisite; not a Native rerun or GUI qualification.'),
    public_installation_evidence=dict(path=str(PUBLIC),sha256=prerequisites[PUBLIC]),installation_record_is_authoritative=False,
    prerequisites_sha256={str(path):pin for path,pin in prerequisites.items()},optional_launch_environment={'BROWSER':'/usr/bin/open -a "Microsoft Edge" %s'},
    sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0,external_complete_exit_required=True,preparation_wall_full_CPU_cap_seconds=90,
    actual_GUI_qualified=False,Native_executed=False,project_complete=False,
    scope='Fresh057-root GUI091 setup only: original owned source/inspection copies, ordinary partial90 default-score preset and existing isolated launcher. No board solve or GUI launch; no eleven-case/IR replay. Same Mac/account/basePython3.11.9/pinned external dependency paths; no cleanOS, standalone, independent-user, all-combination, human/electrical, quality or release claim. Actual new-root GUI workflow and external complete preparation exit remain required; a late refusal retains partial non-authoritative output.')
p.save_json(session/'prepared-state.json',record);record_pin=p.sha(session/'prepared-state.json')
prepared_fresh();assert p.sha(session/'prepared-state.json')==record_pin
print(json.dumps(dict(prepared_state=str(session/'prepared-state.json'),sha256=record_pin,actual_GUI_qualified=False,Native_executed=False)))
