"""Retain completed fresh-root050 CLI delivery; GUI087 preparation only. No Native/readers."""
from pathlib import Path
import ast,datetime,hashlib,json,os,resource,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
START=time.monotonic();CPU0=resource.getrusage(resource.RUSAGE_SELF)
HEAD='aa0072c6b3d8090de2603e5ecb42a95968fb873b'
OLD='c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8'
NEW='8fdf819606e2345b932139f1c16c330825fd8634caef1b611b5e105b97be22a4'
PROTOCOL='493cfb303c7f6b90d1c13f5195c8e487ce54ca7719619a76c3065960ff2f43a7'
runtime=ROOT/'.runs/runtime050 fresh install 001';original=ROOT/'.runs/runtime-directory-050/runtime'
base=ROOT/'.runs/runtime050-install-existing-qualification-001';out=runtime/'.runs/clean-env-partial-delivery-001'
session=runtime/'.runs/gui-session087';notes=ROOT/'evidence/runtime050-install-existing-001-notes'
output=ROOT/'evidence/runtime050-install-existing-001.json'
assert not os.path.lexists(notes) and not os.path.lexists(output)
refs={};files=[];material=[];total=0;queue=[];omitted=[]
shared=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
own=ROOT/'.runs/curate-gui-runtime042-081-recovery-deliveries-001.py'
for path,pin,names in [(shared,'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',['retain','cost']),
 (own,'340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',['read','own_final'])]:
    assert p.sha(path)==pin
    funcs=[n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert [n.name for n in funcs]==names
    exec(compile(ast.Module(body=funcs,type_ignores=[]),str(path),'exec'),globals())
real_retain=retain
# Reuse only the explicit current050 Native packet's bounded retained index.
dep=ROOT/'evidence/runtime050-native-milestone-002.json'
assert p.sha(dep)=='1d0d2019d5505f1fad0134cc2163b3337ce227e1b8d841c8c3c8a81e21a94934'
dep_data=read(dep);assert dep_data['source_head']==HEAD and dep_data['runtime_manifest_sha256']==OLD
index_ref=dep_data['files_index'];assert p.sha(ROOT/index_ref['path'])==index_ref['sha256']
old_index=read(ROOT/index_ref['path'])
for row in old_index['files']:refs.setdefault(row['sha256'],row['path'])
for row in old_index['material']:refs.setdefault(row['sha256'],row['retained'])
def retain(path,name):
    path=Path(path);assert ROOT in path.parents and path.is_file() and not path.is_symlink()
    queue.append((path,Path(name)))
plan=read(base/'protocol.json');outer=read(base/'enclosure/result.json');prep=read(base/'preparation.json')
result=read(out/'result.json');workflow=read(out/'workflow/result.json');cli=Path(result['workspace'])
review_path=ROOT/'.runs/runtime050-install-existing-source-review-001.json'
assert p.sha(review_path)=='900b64c409687e69b24d685461210e6b96b7d7ebb958225da1bffdf4bbf4c937'
review=read(review_path);correction=review['closed_initial_accounting_finding']
assert p.sha(base/'protocol.json')==PROTOCOL==correction['final_protocol_sha256']
assert p.sha(base/'pre-dispatch-protocol-001-original.json')==correction['initial_protocol_sha256']
assert correction['predispatch_correction_observed']is True
assert plan['runtime']==str(runtime) and plan['source_head']==HEAD and plan['runtime_manifest_sha256']==NEW
assert plan['original_manifest_sha256']==OLD and plan['output']==str(out)
assert p.sha(runtime/'runtime-distribution.json')==NEW and p.sha(original/'runtime-distribution.json')==OLD
old=read(original/'runtime-distribution.json');assert read(runtime/'runtime-distribution.json')==dict(old,root=str(runtime))
immutable=old['immutable_files_sha256']
def frozen_inputs():
    assert all(p.sha(runtime/name)==pin and p.sha(original/name)==pin for name,pin in immutable.items())
    for key in ('controller','outer_controller_path','driver_path','enclosure_path','installer_path','installation_record_path',
                'query_preparation_path','query_process_path','tools_defaults_path','settings_path'):
        pin_key={'outer_controller_path':'outer_controller_sha256','driver_path':'driver_sha256','enclosure_path':'enclosure_sha256',
          'installer_path':'installer_sha256','installation_record_path':'installation_record_sha256',
          'query_preparation_path':'query_preparation_sha256','query_process_path':'query_process_sha256',
          'tools_defaults_path':'tools_defaults_sha256','settings_path':'settings_sha256'}.get(key,'controller_sha256')
        assert p.sha(Path(plan[key]))==plan[pin_key]
    assert io.inventory(Path(plan['source']).parent)==plan['source_hashes']
    assert f.evidence_inventory(out)==outer['completed_material']
frozen_inputs()
assert prep['setup_completed']is True and prep['immutable_maps_unchanged']is True and prep['immutable_files']==len(immutable)
assert prep['source_head']==HEAD and prep['source_manifest_sha256']==OLD and prep['runtime_manifest_sha256']==NEW
assert outer['passed']is True and outer['status']=='completed' and outer['accepted']is False and outer['actual_GUI']is False
assert outer['protocol_sha256']==result['protocol_sha256']==PROTOCOL
assert outer['child_receipt']==str(out/'result.json') and outer['child_sha256']==p.sha(out/'result.json')
assert result['controls_passed']is True and result['workflow_delivered']is True and result['status']=='completed'
assert result['accepted']is False and result['production_admitted']is False and result['actual_GUI']is False
assert result['source_head']==HEAD and result['runtime_manifest_sha256']==NEW
assert result['doctor']['ready']is True and result['Native_counts']==[0,0,0,0]
assert result['protected_routes']==4 and result['all_four_original_routes_preserved']is True
assert result['installation_record_is_authoritative']is False
assert cli.parent==out/'workflow' and cli.name=='autorouter-gui-5d281e2acd35411eaab95e7eee4b7014'
assert workflow['workflow_delivered']is True and workflow['actual_GUI']is False
assert workflow['settings']==plan['settings']==result['settings'] and workflow['source_hashes']==result['source_hashes']==plan['source_hashes']
assert workflow['tools']==result['tools']==plan['tools']
assert [row['stage'] for row in workflow['processes']]==['preview','route','review','choice','export','verify_export']
for row in workflow['processes']:
    q=row['process'];assert q['exit_code']==0 and q['cancel_requested']is False and q['log_truncated']is False
    assert p.sha(out/'workflow'/(row['stage']+'.log'))==row['log_sha256']
for row in result['processes']+prep['processes']:
    q=row['process'];assert q['status']=='success' and q['exit_code']==0 and q['cleanup_complete']is True and q['log_truncated']is False
    assert p.sha(Path(q['log']))==row['log_sha256']
assert outer['process']['status']=='success' and outer['process']['exit_code']==0 and outer['process']['cleanup_complete']is True
assert outer['process']['log_truncated']is False
hashes=plan['source_hashes'];proofs={}
for label,receipt,folder in [('route',cli/'route/result.json',cli/'route'),('export',cli/'export/export.json',cli/'export/validation')]:
    data=read(receipt);assert data['source_hashes']==hashes and data['tools']==plan['tools']
    assert data['schematic_parity']=='checked by final native DRC'
    assert [data['native'][k] for k in ('opens','blocking','warnings','exclusions')]==[0,0,0,0]
    assert len(data['native']['ignored_checks'])==2
    assert all(s['cleanup_complete']is True and s['log_truncated']is False for s in data['steps'])
    final=own_final(data,folder,folder,hashes,data['candidate'])
    audit=read(folder/'final-netclass-audit.json');native_map=read(folder/'final-netclasses.json')
    assert audit['candidate_sha256']==data['candidate_sha256']==native_map['board_sha256']
    assert audit['project_sha256']==hashes[Path(plan['source']).with_suffix('.kicad_pro').name]==native_map['project_sha256']
    assert audit['native_map_file_sha256']==p.sha(folder/'final-netclasses.json')
    assert native_map['source']==data['candidate'] and native_map['board_saved']is False
    proofs[label]=dict(receipt_sha256=p.sha(receipt),candidate_sha256=data['candidate_sha256'],own_final=final,
        Native_counts=[0,0,0,0],ignored_checks=data['native']['ignored_checks'],
        default_audit_sha256=p.sha(folder/'final-netclass-audit.json'),default_map_sha256=p.sha(folder/'final-netclasses.json'))
route=read(cli/'route/result.json');export=read(cli/'export/export.json');choice=read(cli/'choice/choice.json')
assert route['accepted']is True and route['invariants_unchanged']is True and len(route['protected_route_import']['matches'])==4
assert export['export_accepted']is True and export['applied']is False and export['original_geometry_and_routing_unchanged']is True
assert export['inputs']['source']==route['source']==plan['source']
assert export['inputs']['receipt_sha256']==proofs['route']['receipt_sha256']==result['route_receipt_sha256']
assert proofs['export']['receipt_sha256']==result['export_receipt_sha256']
assert proofs['route']['candidate_sha256']==proofs['export']['candidate_sha256']==result['candidate_sha256']
assert choice['choice']=='accept' and choice['applied']is False and choice['human_pcb_approval_observed']is False
assert choice['receipt_sha256']==proofs['route']['receipt_sha256']
assert p.sha(cli/'route/default-targets.json')==route['default_target_transport']['sha256']
prepared_path=session/'prepared-state.json';required_path=session/'protocol-required-001.json'
assert p.sha(prepared_path)=='f8776f10cdc34552c3ab53bef470d5678bd5bfb10c7711ab0edbc2d6bc8cebf6'
assert p.sha(required_path)=='3fcf3c8028e353af75732f431ce63f9636bb51d5bbd94fbde915cac1dba1f52e'
prepared=read(prepared_path);required=read(required_path)
assert prepared['source_head']==HEAD and prepared['runtime_manifest_sha256']==NEW and prepared['tools']==plan['tools']
assert prepared['state']==required['state']=='PREPARED_ONLY_NOT_EXECUTED'
assert prepared['actual_GUI_qualified']is False and required['actual_GUI_qualified']is False
assert prepared['Native_qualification_provided_by_preparation']is False
assert prepared['original_source']==plan['source'] and prepared['source_hashes']==hashes
# Only these two frozen GUI files are read/retained. No live GUI087 session or launcher inventory.
for path in sorted(base.rglob('*')):
    if path.is_file():retain(path,Path('qualification')/path.relative_to(base))
# This is the completed CLI subtree only, never a runtime/archive census.
closed_inventory=io.inventory(out,max_bytes=64*1024**2)
excluded_dirs={'home','tmp','code','kicad-config','kicad-cache','kicad-documents','__pycache__'}
for name,pin in closed_inventory.items():
    path=out/name;parts=set(Path(name).parts)
    keep=path.suffix.lower() in {'.json','.log','.kicad_prl'} and not parts&excluded_dirs
    # Full geometric padless/obstacle observations stay local; their bound digests remain in raw receipts/inventories.
    keep=keep and path.name not in {'task.alias-export.json','obstacles.json'}
    if keep:retain(path,Path('CLI-proof')/name)
    else:omitted.append(dict(original=str(path.relative_to(ROOT)),bytes=path.stat().st_size,sha256=pin,
        reason='CAD/DSN/SES/plots, geometric observation, captured code, environment/preferences/cache omitted; raw Mac-only.'))
for path,name in [(runtime/'runtime-distribution.json','new-runtime-distribution.json'),
 (original/'runtime-distribution.json','original-runtime-distribution.json'),(runtime/'.venv/pyvenv.cfg','pyvenv.cfg'),
 (Path(plan['installation_record_path']),'install-existing-runtime-001.json'),(prepared_path,'GUI087-prepared-state.json'),
 (required_path,'GUI087-protocol-required-001.json')]:retain(path,Path('installation')/name)
controllers=['install-existing-runtime050-prepare-001.py','install-existing-runtime050-prepare-001.log',
 'install-existing-runtime050-prepare-001-time.log','qualify-runtime050-install-existing-environment-001.py',
 'run-runtime050-install-existing-environment-001.py','runtime050-install-existing-source-review-001.json',
 'prepare-runtime050-install-existing-gui087.py','prepare-runtime050-install-existing-gui087.log',
 'prepare-runtime050-install-existing-gui087-time.log','prepare-runtime050-install-existing-gui087-002.py',
 'prepare-runtime050-install-existing-gui087-002.log','prepare-runtime050-install-existing-gui087-002-time.log']
for name in controllers:retain(ROOT/'.runs'/name,Path('retained-run')/name)
for key in ('driver_path','enclosure_path','installer_path'):retain(Path(plan[key]),Path('controllers')/Path(plan[key]).name)
for path in (shared,own,Path(__file__),ROOT/'LICENSE'):retain(path,Path('curation-source')/path.name)
timings=dict(setup=cost(ROOT/'.runs/install-existing-runtime050-prepare-001-time.log'),
 CLI_complete=cost(base/'outer-time.log'),GUI_preparation_failed001=cost(ROOT/'.runs/prepare-runtime050-install-existing-gui087-time.log'),
 GUI_preparation_corrected002=cost(ROOT/'.runs/prepare-runtime050-install-existing-gui087-002-time.log'))
assert timings==dict(setup=dict(wall_seconds=1.61,CPU_seconds=.89),CLI_complete=dict(wall_seconds=39.10,CPU_seconds=33.94),
 GUI_preparation_failed001=dict(wall_seconds=.35,CPU_seconds=.32),GUI_preparation_corrected002=dict(wall_seconds=1.08,CPU_seconds=.88))
assert correction['correct_setup_complete_external']['time_log_sha256']==p.sha(ROOT/'.runs/install-existing-runtime050-prepare-001-time.log')
known=set(refs);expected={};new_bytes=0;new_files=0
for path,name in queue:
    raw=io.read_bytes(path,4*1024**2);assert b'\0'not in raw;raw.decode('utf8');sha=hashlib.sha256(raw).hexdigest()
    expected[str(path)]=(len(raw),sha)
    if sha not in known:known.add(sha);new_bytes+=len(raw);new_files+=1
assert new_bytes<16*1024**2-32768 and new_files<1997,(new_bytes,new_files)
frozen_inputs();notes.mkdir(mode=0o700)
for path,name in queue:
    assert (path.stat().st_size,p.sha(path))==expected[str(path)];real_retain(path,name)
scope='''Fresh-root050 CLI installation on the same Mac/user/base Python3.11.9 and existing pinned external KiCad/Java dependencies. Original and fresh manifests differ only in root, with all54 immutable file pins unchanged. New venv --copies --without-pip and minimal PATH/fresh HOME/TMP were used. The non-authoritative installation record does not itself confer acceptance.\n\nActual fresh doctor and six-stage partial90/export90 CLI delivery have their own final Route/export Native0/0/0/0, two ignored checks, full-schematic/refill/original-rule and four-original-route protection proofs. Source is the preserved owned padless-alias four-route fixture, not a new renamed-layer control or new family. Curation reads existing bytes and shared static own_final only; no Native, production acceptance reader, GUI or engine rerun. Field/PRL evidence is retained exactly as present; no separate field-worker result is invented.\n\nGUI087 corrected preparation is PREPARED_ONLY. First preparation failed on a stale GUI-code pin before routing; both numbered attempts and complete costs are retained. Only frozen prepared-state/protocol bytes are included. File-dialog access remained pending at this cutoff; no live087 job/launcher/session material or actual GUI outcome is included.\n\nComplete external CLI39.10wall/33.94CPU is separate from setup1.61/.89 and GUI preparation failed001 .35/.32 plus corrected0021.08/.88. Parent/nested process samples overlap and are not added. Predispatch prose correction and original protocol are preserved. Authoring/review and any interactive time are unknown additional, not zero. Curation complete external cost is separately recorded in its time log, not the pre-exit sample.\n\nOwned metadata/log/PRL and controller sources only; no CAD, DSN, SES, geometry observation, plots, ZIP, downloaded engines/binaries, venv/cache/preferences payload. Omitted raw has exact hashes. This packet is essential proof, not a complete backup; new raw is Mac-only outside010 and restoration capacity remains blocked. No cleanOS/new-account/standalone/dependency-relocation, complete GUI/product, Windows, comparative quality/performance, human/electrical/physical or release claim.\n'''
review_facts=dict(schema=1,kind='runtime050-install-existing-retained-metadata-review-v1',human_review=False,
 reviewer='AI curator static readback; not an independent author review or fresh Native run',findings=[],
 own_route_export_bound=True,source_hashes_unchanged=True,immutable_map_root_only_change=True,
 full_schematic_flag=True,protected_route_matches=4,Native_counts=[0,0,0,0],ignored_checks=route['native']['ignored_checks'],
 GUI087='PREPARED_ONLY; no actual GUI outcome included',retained_source_review_sha256=p.sha(review_path),
 old_protocol_sha256=p.sha(base/'pre-dispatch-protocol-001-original.json'),protocol_sha256=PROTOCOL)
for name,raw in [('SCOPE.md',scope.encode()),('metadata-review.json',(json.dumps(review_facts,indent=2,sort_keys=True)+'\n').encode())]:
    path=notes/name;path.open('xb').write(raw);sha=hashlib.sha256(raw).hexdigest();total+=len(raw)
    files.append(dict(path=str(path.relative_to(ROOT)),bytes=len(raw),sha256=sha))
    material.append(dict(original='authored:'+name,retained=str(path.relative_to(ROOT)),bytes=len(raw),sha256=sha))
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material,omitted_payloads=omitted))
u=resource.getrusage(resource.RUSAGE_SELF)
summary=dict(schema=1,kind='runtime050-install-existing-actual-Native-CLI-prepared-GUI-only-v1',
 recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,production_admitted=False,
 project_complete=False,workflow_CLI=True,workflow_delivered=True,actual_GUI=False,full_GUI_claim=False,
 broad_claims=False,human_review=False,source_head=HEAD,runtime=str(runtime),runtime_manifest_sha256=NEW,
 original_runtime=str(original),original_runtime_manifest_sha256=OLD,immutable_files=len(immutable),
 immutable_map_build_lock_version_unchanged=True,source=plan['source'],source_hashes=hashes,
 fixture_scope='Preserved owned padless-alias/four-route partial2Cu, not a new renamed-layer control.',
 Native=dict(doctor_ready=True,six_stage_delivery=True,counts=[0,0,0,0],protected_routes=4,proofs=proofs,
  protocol_sha256=PROTOCOL,parent_sha256=p.sha(out/'result.json'),outer_sha256=p.sha(base/'enclosure/result.json')),
 GUI087=dict(state='PREPARED_ONLY_NOT_EXECUTED',actual_GUI=False,prepared_sha256=p.sha(prepared_path),
  protocol_required_sha256=p.sha(required_path),access_at_cutoff='File-dialog access pending; no actual GUI outcome retained.'),
 installation_record_is_authoritative=False,source_review_sha256=p.sha(review_path),
 predispatch_accounting_correction=correction,complete_external_costs=timings,
 nested_samples=dict(outer_wall_seconds=outer['complete_wall_seconds'],outer_full_CPU_seconds=outer['complete_full_CPU_seconds'],
  parent_wall_seconds=result['sampled_wall_seconds'],parent_full_CPU_seconds=result['sampled_full_CPU_seconds'],
  overlaps_complete_external=True,do_not_add=True),
 accounting='CLI complete external, setup and two GUI-preparation attempts are separate; nested samples overlap. Unmetered authoring/review/interactive costs unknown, not zero.',
 dependencies=[dict(path=str(dep.relative_to(ROOT)),sha256=p.sha(dep),files_index=index_ref)],
 source_rights='Project-owned GPL fixture/code; original source and immutable provenance retained by exact current050 Native dependency.',
 scope='Same Mac/user/basePython3.11.9/external tools and fresh HOME/TMP only; no standalone/cleanOS/account/quality/fullGUI/platform claim.',
 backup_scope='Essential text proof; omitted raw Mac-only outside010, not a full backup; restoration-capacity gate unchanged.',
 retention=dict(max_file_bytes=4*1024**2,max_packet_payload_bytes=16*1024**2,max_new_files=2000,
  new_files=len(files),new_bytes=total,material_rows=len(material),omitted_rows=len(omitted),preflight_complete=True),
 curation_sample=dict(wall_seconds=time.monotonic()-START,CPU_seconds=u.ru_utime+u.ru_stime-CPU0.ru_utime-CPU0.ru_stime,
  complete_external_required=True,external_time_log='.runs/curate-runtime050-install-existing-001-time.log'),
 files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index)))
assert total<16*1024**2 and len(files)<2000
p.save_json(output,summary)
frozen_inputs()
assert p.sha(prepared_path)==summary['GUI087']['prepared_sha256'] and p.sha(required_path)==summary['GUI087']['protocol_required_sha256']
for row in material:
    raw=io.read_bytes(ROOT/row['retained'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
print(json.dumps(dict(packet=str(output.relative_to(ROOT)),sha256=p.sha(output),index_sha256=p.sha(index),
 new_files=len(files),new_bytes=total,material_rows=len(material),omitted_rows=len(omitted))))
