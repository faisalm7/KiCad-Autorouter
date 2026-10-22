"""Prepare three fresh GUI092 roles only after all eleven fresh058 Native proofs.

DRAFT: refuse until the companion records actual completed current058 pins.
Run only after lead review and with the Native lane idle. This executes no board
worker or GUI: one bounded no-network child prepares the existing isolated
launcher. Native readers replay retained proofs; preparation is not GUI support.
A late refusal may retain a partial session; never reuse or delete it here.
The actual058 manifest is pinned after the completed build, never guessed.
Optional BROWSER override is per-launch metadata; it never changes global defaults.
"""
from pathlib import Path
import datetime,json,os,resource,shutil,sys,time
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
ADMIN=Path(__file__).resolve().parents[1]
RUNTIME=ADMIN/'.runs/runtime-directory-058/runtime'
HEAD='8f5e96b88dd22cd25919bb71ce47711612994efa'
MANIFEST='4f923e053577eb7b7f0425dee6a90be34075641495b4ac2a359ccb1a759f2c74'
DRAFT=ADMIN/'.runs/prepare-runtime058-gui092.draft.json'
draft=json.loads(DRAFT.read_text())
if (draft.get('schema')!=1 or draft.get('state')!='RESOLVED_CURRENT058_EVIDENCE'
        or draft.get('source_head')!=HEAD or draft.get('runtime_manifest_sha256')!=MANIFEST
        or draft.get('runtime')!='.runs/runtime-directory-058/runtime'
        or draft['native']['base']!='.runs/runtime058-native-qualification-001'
        or draft['derived_from']['path']!='.runs/prepare-runtime057-gui090.py'):
    raise SystemExit('GUI092 draft unresolved: lead must bind actual completed current058 evidence before execution.')
for group in ('invalid','IR'):
    for field in ('base','child_receipt','controller'):
        if type(draft[group][field]) is not str or not draft[group][field]:
            raise SystemExit('GUI092 unresolved current058 path: '+group+'.'+field)
required_digests=[*draft['known_sha256'].values(),draft['native']['batch_result_sha256']]
for group in ('invalid','IR'):
    required_digests.extend(draft[group][field] for field in
        ('protocol_sha256','enclosure_result_sha256','enclosure_process_sha256','child_sha256','controller_sha256'))
if any(type(value) is not str or len(value)!=64 or any(c not in '0123456789abcdef' for c in value) for value in required_digests):
    raise SystemExit('GUI092 draft has unresolved SHA-256 pins; completed current058 evidence is required.')
# Prospective control population, not historical proof or unknown future hashes.
# Protocol bytes must match the separately frozen eleven-case population.
CASES=(('via-high-whole2Cu','whole_board_unlocked_routing',1,'route','standard',90,[0,0,6,0],'.runs/native7-npth-keepout-owned-source-001/source/owned1007-transport.kicad_pcb'),
       ('via-high-partial2Cu','partial_completion',4,'route','standard',90,[0,0,0,0],'.runs/native7-source-all-alias-controls-001/source/owned1007-transport.kicad_pcb'),
       ('via-high-whole4Cu','whole_board_unlocked_routing',10,'route','standard',120,[0,0,6,0],'.runs/runtime-directory-019/source-matching/owned-four-copper-forced-inner.kicad_pcb'),
       ('via-high-partial4Cu','partial_completion',10,'route','standard',120,[0,0,6,0],'.runs/runtime-directory-019/source-matching/owned-four-copper-forced-inner.kicad_pcb'),
       ('ordinary-npth2Cu','whole_board_unlocked_routing',1,'route','standard',90,[0,0,6,0],'.runs/native7-npth-keepout-owned-source-001/source/owned1007-transport.kicad_pcb'),
       ('improve-pour-only','whole_board_unlocked_routing',1,'improve','tuned',90,[0,0,6,0],'.runs/native7-improve-rule-area-controls-001/pour-only/owned1007-transport.kicad_pcb'),
       ('improve-fractional','whole_board_unlocked_routing',1,'improve','tuned',90,[0,0,6,0],'.runs/native7-fractional-export-controls-001/positive/source/owned1007-transport.kicad_pcb'),
       ('improve-floor2Cu','whole_board_unlocked_routing',1,'improve','tuned',90,[0,0,6,0],'.runs/default-floor-owned-controls-001/source-2Cu/owned-default-floor-2cu.kicad_pcb'),
       ('ordinary-alias2Cu','partial_completion',4,'route','standard',90,[0,0,0,0],'.runs/native7-source-all-alias-controls-001/source/owned1007-transport.kicad_pcb'),
       ('ordinary-whole4Cu','whole_board_unlocked_routing',10,'route','standard',120,[0,0,6,0],'.runs/runtime-directory-019/source-matching/owned-four-copper-forced-inner.kicad_pcb'),
       ('ordinary-hierarchy2Cu','whole_board_unlocked_routing',0,'route','standard',90,[0,0,0,0],'.runs/hierarchy-native-controls-001/source/owned_hierarchy_native.kicad_pcb'))
assert Path(sys.executable).absolute()==RUNTIME/'.venv/bin/python' and Path(sys.prefix).resolve()==RUNTIME/'.venv'
assert sys.prefix!=sys.base_prefix
sys.path.insert(0,str(RUNTIME));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,provenance as pv,preferences as pref
from autorouter import floor_route as f,handoff as h,placement_clearance as pc,review_export as ex,sexpr as sx,local_settings as local,strategy
from autorouter.gui import child_environment
from autorouter.runner import run
assert c.ROOT==RUNTIME and c.NATIVE_VERSION=='10.0.7'
SELF=h.real_path(Path(__file__).absolute());assert SELF==ADMIN/'.runs/prepare-runtime058-gui092.py'
prerequisites={}
def pin(path,expected=None):
    path=h.real_path(path);digest=p.sha(path)
    if expected is not None:assert digest==expected
    prerequisites[str(path)]=digest;return f.read_json(path)
def process_ok(row):
    assert row['status']=='success' and row['exit_code']==0
    assert row['cleanup_complete'] is True and row['log_truncated'] is False
assert f.canonical(pin(DRAFT))==f.canonical(draft)
original_preparer=ADMIN/'.runs/prepare-runtime057-gui090.py'
assert p.sha(original_preparer)==draft['derived_from']['sha256']
prerequisites[str(original_preparer)]=draft['derived_from']['sha256']
manifest=RUNTIME/pv.MANIFEST;assert p.sha(manifest)==MANIFEST
prerequisites[str(manifest)]=MANIFEST;prerequisites[str(SELF)]=p.sha(SELF)
tools=p.tool_manifest()
assert tools['git_head']==HEAD and tools['kicad']=='10.0.7'
assert tools['source_provenance']['manifest_sha256']==MANIFEST
assert tools['source_provenance']['native_version']=='10.0.7'
full=pin(ADMIN/'.runs/full-integration-209/execution.json',draft['known_sha256']['full209_execution']);full_plan=pin(ADMIN/'.runs/full-integration-209/protocol.json',draft['known_sha256']['full209_protocol'])
assert full['passed'] is True and full['sources_unchanged'] is True;process_ok(full['process'])
assert full_plan['tools']['git_head']==HEAD
for name,digest in tools['implementation_sha256'].items():assert full_plan['source_sha256'][name]==digest
prepared=pin(RUNTIME.parent/'preparation.json',draft['known_sha256']['runtime_preparation'])
assert prepared['prepared'] is True and prepared['source_head']==HEAD and prepared['runtime']==str(RUNTIME)
assert prepared['manifest_sha256']==MANIFEST and prepared['recipe']['source_provenance']==tools['source_provenance']
assert prepared['full209_execution_sha256']==prerequisites[str(ADMIN/'.runs/full-integration-209/execution.json')]
venv=pin(RUNTIME.parent/'venv-process.json',draft['known_sha256']['venv_process']);process_ok(venv)
assert prerequisites[str(RUNTIME.parent/'venv-process.json')]==prepared['venv_process_sha256']
base=ADMIN/'.runs/runtime058-native-qualification-001'
frozen=pin(base/'frozen.json',draft['known_sha256']['native_frozen'])
assert frozen['schema']==1 and frozen['source_head']==HEAD and frozen['runtime_manifest_sha256']==MANIFEST
assert type(frozen['protocols']) is list and len(frozen['protocols'])==11
frozen_rows={row['case']:row for row in frozen['protocols']}
assert [row['case'] for row in frozen['protocols']]==[row[0] for row in CASES]
assert len(frozen_rows)==11
freezer=ADMIN/'.runs/freeze-runtime058-native-qualification-001.py'
assert p.sha(freezer)==frozen['controller_sha256']==draft['known_sha256']['native_freezer'];prerequisites[str(freezer)]=frozen['controller_sha256']
batch=pin(base/'batch-result.json',draft['native']['batch_result_sha256']);dispatcher=ADMIN/'.runs/qualify-runtime058-native-batch-001.py'
assert batch['passed'] is True and [row['case'] for row in batch['rows']]==[row[0] for row in CASES]
assert all(row['passed'] is True for row in batch['rows']) and batch['frozen_sha256']==p.sha(base/'frozen.json')
assert max(batch['wall_seconds'],batch['full_CPU_seconds'])<=frozen['whole_batch_seconds']==900
assert p.sha(dispatcher)==batch['controller_sha256']==draft['known_sha256']['native_dispatcher'];prerequisites[str(dispatcher)]=batch['controller_sha256']
doctor=pin(base/'doctor.json',draft['known_sha256']['native_doctor']);doctor_process=pin(base/'doctor-process.json',draft['known_sha256']['native_doctor_process']);process_ok(doctor_process)
assert doctor['ready'] is True and doctor['workspace']==str(RUNTIME)
assert doctor['checks']['runtime_provenance']=={'verified':True,'identity':tools['source_provenance']}
assert doctor_process['argv']==[*f.SANDBOX,str(RUNTIME/'.venv/bin/python'),'-B','-m','autorouter','doctor']
batch_rows={row['case']:row for row in batch['rows']};assert len(batch_rows)==11
positives={};packets=[];pairs=[]
for label,scope,protected_count,method,profile,seconds,expected_counts,source_name in CASES:
    folder=base/label;protocol=folder/'protocol.json';protocol_sha=p.sha(protocol)
    assert frozen_rows[label]['protocol']==str(protocol) and frozen_rows[label]['protocol_sha256']==protocol_sha
    assert frozen_rows[label]['method']==method
    plan=pin(protocol);completed=pin(folder/'execution.json',batch_rows[label]['execution_sha256']);settings_path=folder/'settings.json'
    scoring='via_high' if label.startswith('via-high-') else None
    settings=pref.validate(dict(pref.DEFAULTS,scope=scope,seconds=seconds,profile=profile,adapter='both',
        guidance='native',layers='source_all',scoring_preference=scoring))
    assert plan['schema']==1 and plan['kind']=='runtime058-six-stage-route-or-improve-CLI'
    assert plan['case']==label and plan['method']==method
    assert plan['runtime']==str(RUNTIME) and plan['source_head']==HEAD and plan['runtime_manifest_sha256']==MANIFEST
    assert plan['tools']==tools and plan['settings']==settings and plan['budgets']=={'route':seconds,'export':seconds}
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
    assert source==ADMIN/source_name and pc.inventory(source.parent)==hashes
    assert all(source.with_suffix(suffix).name in hashes for suffix in ('.kicad_pcb','.kicad_pro','.kicad_sch'))
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
    else:assert route['scoring_variant']==scoring
    assert route['budget_seconds']==route['cpu_budget_seconds']==exported['budget_seconds']==exported['cpu_budget_seconds']==seconds
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


# Additional completed current-runtime gates. These are retained proof replays,
# not another Native experiment or GUI role transfer.
invalid_base=h.real_path(ADMIN/draft['invalid']['base']);assert invalid_base.is_relative_to(ADMIN/'.runs')
invalid_plan=pin(invalid_base/'protocol.json',draft['invalid']['protocol_sha256']);invalid_outer=pin(invalid_base/'enclosure/result.json',draft['invalid']['enclosure_result_sha256'])
process_ok(invalid_outer['process']);assert invalid_outer['process']==pin(invalid_base/'enclosure/process.json',draft['invalid']['enclosure_process_sha256'])
assert invalid_outer['passed'] is True and invalid_outer['status']=='completed'
assert invalid_outer['protocol_sha256']==prerequisites[str(invalid_base/'protocol.json')]
assert invalid_plan['source_head']==HEAD and invalid_plan['runtime']==str(RUNTIME)
assert invalid_plan['runtime_manifest_sha256']==MANIFEST and invalid_plan['expected_scoring']=='via_high'
invalid_path=h.real_path(invalid_outer['child_receipt']);assert invalid_path==h.real_path(ADMIN/draft['invalid']['child_receipt'])
invalid=pin(invalid_path,draft['invalid']['child_sha256'])
assert invalid_path==Path(invalid_plan['output'])/'result.json' and p.sha(invalid_path)==invalid_outer['child_sha256']
assert invalid['control_passed'] is True and invalid['status']=='completed' and invalid['accepted'] is False
assert invalid['source_head']==HEAD and invalid['runtime_manifest_sha256']==MANIFEST and invalid['tools']==tools
assert invalid['protocol_sha256']==p.sha(invalid_base/'protocol.json')
assert h.real_path(invalid_plan['controller'])==h.real_path(ADMIN/draft['invalid']['controller'])
assert invalid['controller_sha256']==invalid_plan['controller_sha256']==p.sha(Path(invalid_plan['controller']))==draft['invalid']['controller_sha256']
prerequisites[str(h.real_path(invalid_plan['controller']))]=invalid['controller_sha256']
assert invalid['positive_sha256']==prerequisites[invalid['positive_receipt']]
assert [row['case'] for row in invalid['cases']]==['short','protected-width','hole-clearance']
assert all(row['passed'] is True for row in invalid['cases'])
for row in invalid['cases']:packets.append((invalid_path.parent/row['case'],{'steps':row['steps']}))
invalid_material=f.evidence_inventory(invalid_path.parent)
assert invalid_material==invalid_outer['completed_evidence']
ir_base=h.real_path(ADMIN/draft['IR']['base']);assert ir_base.is_relative_to(ADMIN/'.runs')
ir_plan=pin(ir_base/'protocol.json',draft['IR']['protocol_sha256']);ir_outer=pin(ir_base/'enclosure/result.json',draft['IR']['enclosure_result_sha256'])
process_ok(ir_outer['process']);assert ir_outer['process']==pin(ir_base/'enclosure/process.json',draft['IR']['enclosure_process_sha256'])
assert ir_outer['passed'] is True and ir_outer['status']=='completed'
assert ir_outer['protocol_sha256']==prerequisites[str(ir_base/'protocol.json')]
assert ir_plan['source_head']==HEAD and ir_plan['runtime']==str(RUNTIME) and ir_plan['runtime_manifest_sha256']==MANIFEST
assert ir_plan['tools']==tools and ir_plan['arm']=='Cimprove'
ir_path=h.real_path(ir_outer['child_receipt']);assert ir_path==h.real_path(ADMIN/draft['IR']['child_receipt'])
ir=pin(ir_path,draft['IR']['child_sha256'])
assert ir_path==Path(ir_plan['output'])/'result.json' and p.sha(ir_path)==ir_outer['child_sha256']
assert ir['status']=='completed' and ir['controls_passed'] is True and ir['attempt_qualified'] is True
assert ir['workflow_delivered'] is True and ir['outcome']=='validated_delivery' and ir['actual_GUI'] is False
assert ir['runtime']==str(RUNTIME) and ir['source_head']==HEAD and ir['runtime_manifest_sha256']==MANIFEST and ir['tools']==tools
assert ir['source_hashes']==ir_plan['source_hashes']==pc.inventory(Path(ir_plan['source']).parent)
assert ir['protocol_sha256']==p.sha(ir_base/'protocol.json') and ir['controller_sha256']==ir_plan['controller_sha256']
assert h.real_path(ir_plan['controller'])==h.real_path(ADMIN/draft['IR']['controller'])
assert p.sha(Path(ir_plan['controller']))==ir['controller_sha256']==draft['IR']['controller_sha256']
prerequisites[str(h.real_path(ir_plan['controller']))]=ir['controller_sha256']
ir_route_path=h.real_path(ir['selected_route_receipt']);ir_route=pin(ir_route_path)
ir_export_path=h.real_path(ir['export_receipt']);ir_export=pin(ir_export_path)
assert ir_path.parent in ir_route_path.parents and ir_path.parent in ir_export_path.parents
assert p.sha(ir_route_path)==ir['selected_route_sha256'] and p.sha(ir_export_path)==ir['export_sha256']
assert ir_route['accepted'] is True and ir_export['export_accepted'] is True
assert ir_route['source_hashes']==ir_export['source_hashes']==ir_plan['source_hashes']
assert ir_route['tools']==ir_export['tools']==tools and ir_route['pruning_preferences']['effective']['scoring_preference'] is None
assert ir_route['candidate_sha256']==ir_export['candidate_sha256']==ir['candidate_sha256']
packets.extend(strategy.native7_packets(ir_route_path.parent,ir_route));packets.append((ir_export_path.parent/'validation',ir_export))
ir_material=f.evidence_inventory(ir_path.parent)
assert ir_material==ir_outer['completed_evidence']==ir['completed_evidence']
supporting_proofs=dict(invalid_current=dict(enclosure_sha256=p.sha(invalid_base/'enclosure/result.json'),child_sha256=p.sha(invalid_path),control_passed=True),
    IR_delivery=dict(enclosure_sha256=p.sha(ir_base/'enclosure/result.json'),child_sha256=p.sha(ir_path),workflow_delivered=True))

def fresh():
    assert p.tool_manifest()==tools and p.sha(manifest)==MANIFEST
    for path,digest in prerequisites.items():assert p.sha(Path(path))==digest
    for item in positives.values():
        assert pc.inventory(Path(item['source']).parent)==item['source_hashes']
        assert pc.inventory(Path(item['output']),max_bytes=256*1024**2,max_files=8000,max_entries=16000)==item['material']
    assert f.evidence_inventory(invalid_path.parent)==invalid_material
    assert f.evidence_inventory(ir_path.parent)==ir_material
    assert pc.inventory(Path(ir_plan['source']).parent)==ir_plan['source_hashes']
    for name,module in tuple(sys.modules.items()):
        if name.split('.')[0]=='autorouter' and getattr(module,'__file__',None):assert Path(module.__file__).resolve().is_relative_to(RUNTIME),name
    assert time.monotonic()-START<90 and cpu()-CPU0<90
assert len(positives)==11
fresh();assert shutil.disk_usage(ADMIN).free>2*1024**3
session=RUNTIME/'.runs/gui-session092';launcher=RUNTIME/'.runs/gui-launcher092'
for path in (session,launcher):assert h.real_path(path,existing=False)==path and not os.path.lexists(path)
session.mkdir(mode=0o700);owner={};h.capture_destination(owner,session)
roles={}
for label,project,inspection,settings_name in (('ordinary-alias2Cu','project','inspection','route-settings.json'),('via-high-partial2Cu','via-high-project','via-high-inspection','via-high-settings.json'),('improve-fractional','fractional-project','fractional-inspection','fractional-settings.json')):
    item=positives[label];source=Path(item['source'])
    for name in (project,inspection):
        shutil.copytree(source.parent,session/name);assert pc.inventory(session/name)==item['source_hashes']
    shutil.copyfile(base/label/'settings.json',session/settings_name)
    assert p.sha(session/settings_name)==item['settings_sha256']
    roles[label]=dict(source=str(session/project/source.name),inspection=str(session/inspection/source.with_suffix('.kicad_pro').name),
        original_source=str(source),source_hashes=item['source_hashes'],method=item['method'],
        description={'ordinary-alias2Cu':'Ordinary partial90 corrected-standard alias-layer source, protected4; default via cost',
            'via-high-partial2Cu':'Explicit partial90 standard higher-via-cost preference on the original alias-layer source, protected4; no fewer-via or quality promise',
            'improve-fractional':'Optional whole Improve90 tuned incumbent/pruning/final-reserve method, protected1; default via cost and six retained Native warnings'}[label],
        settings=item['settings'],settings_path=str(session/settings_name),settings_sha256=item['settings_sha256'])
(session/'jobs').mkdir(mode=0o700)
required=dict(schema=1,state='PREPARED_ONLY_NOT_EXECUTED',runtime=str(RUNTIME),source_head=HEAD,runtime_manifest_sha256=MANIFEST,
    roles=roles,actual_GUI_qualified=False,required_observations='Fresh toolbar ordinary alias partial90/standard/default-score, explicit higher-via-cost alias partial90/standard, and separate Improve fractional whole-method90/tuned/default-score roles. Each requires rendered F/B review, explicit acknowledged intent, fresh export90 and checked opening; own Native/fullSCH/original/protected4,4 or1. Via preference changes search costs only, not source constraints or a guarantee of fewer vias. Improve budget includes incumbent/trials/25s return reserve; no score override. No prior GUI role transfer or actual GUI observation is inferred from preparation.')
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
    optional_launch_environment={'BROWSER':'/usr/bin/open -a "Microsoft Edge" %s'},
    browser_scope='Optional per-launch environment only; no global browser change or Chrome launch. Actual Edge rendering still requires observation.',
    native_prerequisites={label:{key:value for key,value in item.items() if key!='material'} for label,item in positives.items()},
    prerequisite_sha256=prerequisites,supporting_completed_current_proofs=supporting_proofs,protocol_required_sha256=p.sha(session/'protocol-required-001.json'),
    sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0,external_complete_exit_required=True,
    actual_GUI_qualified=False,Native_executed=False,project_complete=False,
    scope='Preparation only after all eleven fresh058 six-stage Native prerequisites, successful current IR delivery and current invalid controls. Three GUI roles use original source copies, not candidates; no prior GUI transfer or fewer-via/electrical promise. Same Mac/account/base Python/external dependencies. No cleanOS/standalone/Windows/quality/human/electrical claim. Actual GUI roles remain unperformed; a late refusal can retain this non-authoritative preparation record.')
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
