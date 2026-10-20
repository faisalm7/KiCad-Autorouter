"""Prepare ONLY the ordinary GUI087 role for the installed-existing050 root.

Requires its completed fresh doctor/six-stage Native delivery and matching outer
custody. No GUI, routing or Native process is run by preparation; the sole child
prepares the existing isolated launcher. Same Mac/base Python/external tools.
"""
from pathlib import Path
import datetime, json, os, re, shutil, sys, time
START=time.monotonic()
ADMIN=Path(__file__).resolve().parents[1]
RUNTIME=ADMIN/'.runs/runtime050 fresh install 001'
ORIGINAL=ADMIN/'.runs/runtime-directory-050/runtime'
QUALIFICATION=ADMIN/'.runs/runtime050-install-existing-qualification-001'
HEAD='aa0072c6b3d8090de2603e5ecb42a95968fb873b'
ORIGINAL_MANIFEST='c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8'
SETTINGS_SHA='a73292826f5de5a992d4d04ec85ced90ecac269556f72b35180f610e79866a65'
SOURCE=ADMIN/'.runs/task-copper-fixed-alias-native-004/source/owned1007-transport.kicad_pcb'
assert Path(sys.executable).absolute()==RUNTIME/'.venv/bin/python'
assert Path(sys.prefix).resolve()==RUNTIME/'.venv' and sys.prefix!=sys.base_prefix
assert sys.version_info[:3]==(3,11,9) and sys.base_prefix=='/Users/faisal/.pyenv/versions/3.11.9'
sys.path.insert(0,str(RUNTIME));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,handoff as h
from autorouter import provenance as pv,preferences as pref,placement_clearance as pc,sexpr as sx
from autorouter.runner import run
assert c.ROOT==RUNTIME and c.NATIVE_VERSION=='10.0.7'
SELF=Path(__file__).absolute();SELF_SHA=p.sha(SELF)
assert SELF==ADMIN/'.runs/prepare-runtime050-install-existing-gui087.py'
TEMPLATE=ADMIN/'.runs/prepare-runtime042-gui081.py'
assert p.sha(TEMPLATE)=='7dd09d1e4706bd272436736d699a91adc1aa18d8344d7a6d2377f30db77cfc45'
protocol=QUALIFICATION/'protocol.json';outer_path=QUALIFICATION/'enclosure/result.json'
parent_path=RUNTIME/'.runs/clean-env-partial-delivery-001/result.json'
plan=f.read_json(protocol);outer=f.read_json(outer_path);parent=f.read_json(parent_path)
manifest=RUNTIME/pv.MANIFEST;manifest_pin=p.sha(manifest)
assert type(plan.get('schema'))is int and plan['schema']==1
assert plan['kind']=='runtime050-install-existing-clean-environment-v1'
assert plan['runtime']==str(RUNTIME) and plan['source_head']==HEAD
assert type(plan['runtime_manifest_sha256'])is str and re.fullmatch('[0-9a-f]{64}',plan['runtime_manifest_sha256'])
assert plan['runtime_manifest_sha256']==manifest_pin and plan['output']==str(parent_path.parent)
assert outer['passed']is True and outer['status']=='completed' and outer['accepted']is False
assert outer['actual_GUI']is False and outer['protocol_sha256']==p.sha(protocol)
assert outer['child_receipt']==str(parent_path) and outer['child_sha256']==p.sha(parent_path)
process=outer['process']
assert process['status']=='success' and process['exit_code']==0
assert process['cleanup_complete']is True and process['log_truncated']is False
assert max(outer['complete_wall_seconds'],outer['complete_full_CPU_seconds'])<=300
assert parent['kind']==plan['kind'] and parent['status']=='completed'
assert parent['controls_passed']is True and parent['workflow_delivered']is True
assert parent['accepted']is False and parent['production_admitted']is False and parent['actual_GUI']is False
assert parent['runtime']==str(RUNTIME) and parent['source_head']==HEAD
assert parent['runtime_manifest_sha256']==manifest_pin and parent['protocol_sha256']==p.sha(protocol)
assert parent['controller_sha256']==plan['controller_sha256'] and p.sha(Path(plan['controller']))==plan['controller_sha256']
assert parent['Native_counts']==[0,0,0,0] and all(type(v)is int for v in parent['Native_counts'])
assert type(parent['protected_routes'])is int and parent['protected_routes']==4
assert parent['all_four_original_routes_preserved']is True
assert parent['source']==plan['source']==str(SOURCE) and parent['source_hashes']==plan['source_hashes']
assert parent['original_runtime']==str(ORIGINAL) and parent['original_manifest_sha256']==ORIGINAL_MANIFEST
assert parent['installation_record_is_authoritative']is False
assert parent['installation_record_sha256']==plan['installation_record_sha256']
completed_material=outer['completed_material']
assert f.evidence_inventory(parent_path.parent)==completed_material
original_record=f.read_json(ORIGINAL/pv.MANIFEST)
implementation={name:pin for name,pin in original_record['immutable_files_sha256'].items() if name.startswith('autorouter/')}
original_identity=pv._runtime_identity(ORIGINAL,implementation)
assert original_identity['manifest_sha256']==ORIGINAL_MANIFEST and original_identity['git_head']==HEAD
assert f.read_json(manifest)=={**original_record,'root':str(RUNTIME)}
tools=p.tool_manifest()
assert pv._runtime_identity(RUNTIME,implementation)==tools['source_provenance']
assert tools==parent['tools']==plan['tools'] and tools['git_head']==HEAD and tools['kicad']=='10.0.7'
assert tools['source_provenance']['manifest_sha256']==manifest_pin
assert tools['implementation_sha256']['autorouter/gui.py']=='93963f6a68d3269050298b6a2d374ffbfa18a86315c2ee30cb9cf02d7caf709e'
assert tools['implementation_sha256']['autorouter/pipeline.py']=='7f3d1c20f063f5aa6d55fddcb8896ecdc9c0de6f8a0f51d0faf49a3feebf542e'
settings=pref.validate(dict(pref.DEFAULTS,scope='partial_completion',seconds=90))
assert parent['settings']==plan['settings']==settings
assert p.sha(QUALIFICATION/'settings.json')==plan['settings_sha256']==SETTINGS_SHA
assert pref.load(QUALIFICATION/'settings.json').parsed==settings
hashes=plan['source_hashes']
assert len(hashes)==4 and pc.inventory(SOURCE.parent)==hashes
assert hashes[SOURCE.name]=='62cb74bf329f3eb259b595881a24ef2ac320b930ca738f732461ca38831f0128'
workspace=h.real_path(parent['workspace'])
assert workspace.parent==parent_path.parent/'workflow' and workspace.name.startswith('autorouter-gui-')
route_path=workspace/'route/result.json';export_path=workspace/'export/export.json'
assert p.sha(route_path)==parent['route_receipt_sha256'] and p.sha(export_path)==parent['export_receipt_sha256']
route=f.read_json(route_path);exported=f.read_json(export_path)
assert route['accepted']is True and route['status']=='routing_accepted' and exported['export_accepted']is True
assert route['source']==str(SOURCE) and exported['inputs']['source']==str(SOURCE)
assert exported['inputs']['receipt']==str(route_path) and exported['inputs']['receipt_sha256']==p.sha(route_path)
assert exported['original_geometry_and_routing_unchanged']is True
assert route['candidate_sha256']==exported['candidate_sha256']==parent['candidate_sha256']
assert route['scope']=='partial_completion' and route['engine_profile']=='standard' and route['adapter']=='both'
assert route['scoring_variant']is None and route['budget_seconds']==route['cpu_budget_seconds']==90
assert exported['budget_seconds']==90 and route['metrics']['copper_layers']==2
original=sx.read(SOURCE);protected=p.routes(original);assert len(protected)==4
for data in (route,exported):
    assert data['source_hashes']==hashes and data['tools']==tools
    assert data['schematic_parity']=='checked by final native DRC'
    assert [data['native'][key] for key in ('opens','blocking','warnings','exclusions')]==[0,0,0,0]
    candidate=h.real_path(data['candidate']);p.verify_candidate_files(candidate,hashes,data['candidate_sha256'])
    tree=sx.read(candidate)
    assert p.immutable(tree)==p.immutable(original) and all(item in p.routes(tree) for item in protected)
prerequisites={str(path):p.sha(path) for path in (protocol,outer_path,parent_path,route_path,export_path,
    manifest,ORIGINAL/pv.MANIFEST,TEMPLATE,QUALIFICATION/'settings.json',QUALIFICATION/'preparation.json')}
for name in ('installation_record','installer','query_preparation','tools_defaults','query_process'):
    path=h.real_path(plan[name+'_path']);assert p.sha(path)==plan[name+'_sha256']
    prerequisites[str(path)]=plan[name+'_sha256']
assert h.real_path(SOURCE)==SOURCE and shutil.disk_usage(ADMIN).free>2*1024**3
session=RUNTIME/'.runs/gui-session087';launcher=RUNTIME/'.runs/gui-launcher087'
for path in (session,launcher):
    assert h.real_path(path,existing=False)==path and not os.path.lexists(path)
session.mkdir(mode=0o700);owner={};h.capture_destination(owner,session)
for name in ('project','inspection'):
    shutil.copytree(SOURCE.parent,session/name)
    assert pc.inventory(session/name)==hashes
(session/'jobs').mkdir(mode=0o700)
p.save_json(session/'route-settings.json',settings)
assert p.sha(session/'route-settings.json')==SETTINGS_SHA
required=dict(schema=1,state='PREPARED_ONLY_NOT_EXECUTED',source_head=HEAD,
    runtime=str(RUNTIME),runtime_manifest_sha256=manifest_pin,method='route',settings=settings,
    source=str(session/'project'/SOURCE.name),source_hashes=hashes,
    required_observation='Actual new-root isolated launcher/toolbar, partial90 Route, rendered review, explicit acknowledged intent, fresh export90 and checked opening. Own fullSCH/original/protected4 proof mandatory. No historical GUI role transfer.',
    actual_GUI_qualified=False,Native_qualification_provided_by_preparation=False,
    scope='One owned ordinary installation-path functional role only; no recovery/alias/hierarchy/cancel/freshness population or general product/quality qualification.')
p.save_json(session/'protocol-required-001.json',required)
env={key:value for key,value in os.environ.items() if key not in ('PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN')}
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
process=run([*f.SANDBOX,str(RUNTIME/'.venv/bin/python'),'-B',str(RUNTIME/'scripts/install_gui.py'),
    '--output',str(launcher)],cwd=session,env=env,log=session/'prepare-launcher.log',timeout=30,
    max_log_bytes=512*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=1024**3)
p.save_json(session/'prepare-launcher-process.json',process)
assert process['status']=='success' and process['exit_code']==0
assert process['cleanup_complete']is True and process['log_truncated']is False
assert h.owned_destination(owner)==session and p.sha(SELF)==SELF_SHA
assert pv._runtime_identity(ORIGINAL,implementation)==original_identity
assert f.read_json(manifest)=={**original_record,'root':str(RUNTIME)} and p.sha(manifest)==manifest_pin
assert p.tool_manifest()==tools and pc.inventory(SOURCE.parent)==hashes
assert f.evidence_inventory(parent_path.parent)==completed_material
for path,pin in prerequisites.items():assert p.sha(Path(path))==pin
for name in ('project','inspection'):assert pc.inventory(session/name)==hashes
for name,module in tuple(sys.modules.items()):
    if name.split('.')[0]=='autorouter' and getattr(module,'__file__',None):
        assert Path(module.__file__).resolve().is_relative_to(RUNTIME),name
record=dict(schema=1,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    state='PREPARED_ONLY_NOT_EXECUTED',runtime=str(RUNTIME),source_head=HEAD,
    runtime_manifest_sha256=manifest_pin,tools=tools,controller_sha256=SELF_SHA,
    template=dict(path=str(TEMPLATE),sha256=p.sha(TEMPLATE)),
    source=str(session/'project'/SOURCE.name),original_source=str(SOURCE),source_hashes=hashes,
    inspection=str(session/'inspection'/SOURCE.with_suffix('.kicad_pro').name),
    settings=settings,settings_path=str(session/'route-settings.json'),settings_sha256=SETTINGS_SHA,
    jobs=str(session/'jobs'),launcher=str(launcher/'Launch Autorouter.command'),
    protocol_required=str(session/'protocol-required-001.json'),protocol_required_sha256=p.sha(session/'protocol-required-001.json'),
    parent_qualification=dict(receipt=str(parent_path),sha256=p.sha(parent_path),
        outer_receipt=str(outer_path),outer_sha256=p.sha(outer_path),controls_passed=True,
        workflow_delivered=True,Native_counts=parent['Native_counts'],protected_routes=parent['protected_routes'],
        own_final_full_schematic_proof=True,candidate_sha256=parent['candidate_sha256'],
        scope='Completed fresh new-root CLI prerequisite; not actual GUI qualification.'),
    installation_record_sha256=plan['installation_record_sha256'],installation_record_is_authoritative=False,
    prerequisites_sha256=prerequisites,preparation_wall_seconds_before_publication=time.monotonic()-START,
    actual_GUI_qualified=False,Native_qualification_provided_by_preparation=False,project_complete=False,
    scope='Prepared new-root050/087 ordinary partial90 inspection and isolated launcher only. Copies are original owned source, never routed candidates. Same Mac/base Python/pinned external tools; no freshOS, dependency relocation, standalone, broad GUI/quality/human claim. Actual GUI and complete external preparation costs remain required.')
p.save_json(session/'prepared-state.json',record)
print(json.dumps(record))
